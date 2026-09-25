"""
Smart 9:16 Reframe & Dynamic Face Tracking Engine.
Detects faces using neural YuNet / Haar cascade, calculates dead-zone smoothed crop trajectory,
and generates reusable 'crop_plan.json' artifacts and FFmpeg filtergraphs.
Supports active_speaker (with dynamic trajectory), blurred_background, center_crop, and split_screen presets.
Compatible with OpenCV 4.x and modern OpenCV 5.x.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np
from loguru import logger

from viral_clips.config import settings
from viral_clips.exceptions import ViralClipsError

SCHEMA_VERSION = "1.0.0"

# Model asset paths
YUNET_MODEL_PATH = Path(__file__).parent / "assets" / "face_detection_yunet_2023mar.onnx"
HAAR_MODEL_PATH = Path(__file__).parent / "assets" / "haarcascade_frontalface_default.xml"

_yunet_detector = None


def get_face_detector(frame_width: int, frame_height: int):
    """Initializes or reconfigures cached YuNet neural face detector."""
    global _yunet_detector
    if hasattr(cv2, "FaceDetectorYN_create") and YUNET_MODEL_PATH.exists():
        try:
            if _yunet_detector is None:
                _yunet_detector = cv2.FaceDetectorYN_create(
                    str(YUNET_MODEL_PATH),
                    "",
                    (frame_width, frame_height),
                    score_threshold=0.6,
                    nms_threshold=0.3,
                    top_k=5,
                )
            else:
                _yunet_detector.setInputSize((frame_width, frame_height))
            return _yunet_detector
        except Exception as e:
            logger.debug(f"YuNet creation failed: {e}")
    return None


def detect_faces_in_frame(frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Detects verified human faces in a single BGR frame.
    Uses OpenCV YuNet neural network with strict confidence filtering.
    Falls back to Haar Cascade if YuNet is unavailable.
    Returns list of (x, y, w, h). Completely free of false-positive color heuristics.
    """
    h, w = frame.shape[:2]

    # 1. Try OpenCV 5 / YuNet neural detector
    detector = get_face_detector(w, h)
    if detector is not None:
        try:
            _, faces = detector.detect(frame)
            if faces is not None and len(faces) > 0:
                results = []
                for f in faces:
                    fx, fy, fw, fh = int(f[0]), int(f[1]), int(f[2]), int(f[3])
                    confidence = float(f[14]) if len(f) > 14 else 1.0
                    # Validate geometric bounds and confidence
                    if confidence >= 0.60 and fw >= 30 and fh >= 30:
                        aspect_ratio = fw / max(1, fh)
                        if 0.5 <= aspect_ratio <= 1.8:
                            results.append((max(0, fx), max(0, fy), min(w - fx, fw), min(h - fy, fh)))
                if results:
                    return results
        except Exception as e:
            logger.debug(f"YuNet inference error: {e}")

    # 2. Try OpenCV Haar Cascade if available
    if hasattr(cv2, "CascadeClassifier") and HAAR_MODEL_PATH.exists():
        try:
            cascade = cv2.CascadeClassifier(str(HAAR_MODEL_PATH))
            if not cascade.empty():
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                raw_faces = cascade.detectMultiScale(
                    gray, scaleFactor=1.15, minNeighbors=5, minSize=(40, 40)
                )
                valid = []
                for (x, y, fw, fh) in raw_faces:
                    aspect = fw / max(1, fh)
                    if 0.6 <= aspect <= 1.5:
                        valid.append((int(x), int(y), int(fw), int(fh)))
                return valid
        except Exception as e:
            logger.debug(f"Haar cascade detection error: {e}")

    # No faces detected; never guess with color masks
    return []


def analyze_video_framing(
    video_path: Union[str, Path],
    clip_start_s: float,
    clip_end_s: float,
    sample_interval_s: float = 0.25,
) -> Dict[str, Any]:
    """
    Samples frames across the clip window to locate speakers, build a dynamic
    dead-zone smoothed trajectory, and detect multi-speaker split-screen opportunities.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.warning(f"Could not open video {video_path} with OpenCV. Falling back to center crop.")
        return {
            "face_detected": False,
            "face_visible_ratio": 0.0,
            "source_width": 1920,
            "source_height": 1080,
            "target_crop_width": 607,
            "target_crop_height": 1080,
            "crop_x": 656,
            "crop_y": 0,
            "average_x_ratio": 0.5,
            "trajectory": [],
            "multi_speaker_detected": False,
            "speaker_clusters": [],
        }

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080)

    # Target 9:16 crop width
    target_crop_w = int(height * (9.0 / 16.0))
    max_x = max(0, width - target_crop_w)

    sample_step_frames = max(1, int(fps * sample_interval_s))
    start_frame = int(clip_start_s * fps)
    end_frame = int(clip_end_s * fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame = start_frame

    samples: List[Dict[str, Any]] = []
    detected_centers_x: List[int] = []
    two_face_counts = 0
    prev_frame_gray = None

    while current_frame <= end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp_s = round(current_frame / fps, 2)
        faces = detect_faces_in_frame(frame)

        # Detect scene cut via frame difference
        small_gray = cv2.cvtColor(cv2.resize(frame, (64, 36)), cv2.COLOR_BGR2GRAY)
        is_scene_cut = False
        if prev_frame_gray is not None:
            diff = float(np.mean(np.abs(small_gray.astype(float) - prev_frame_gray.astype(float))))
            if diff > 38.0:
                is_scene_cut = True
        prev_frame_gray = small_gray

        if len(faces) >= 2:
            two_face_counts += 1

        primary_face = None
        if faces:
            # Sort by bounding box area descending
            faces.sort(key=lambda f: f[2] * f[3], reverse=True)
            primary_face = faces[0]
            cx = primary_face[0] + primary_face[2] // 2
            detected_centers_x.append(cx)
        else:
            cx = None

        samples.append({
            "timestamp_s": timestamp_s,
            "faces_count": len(faces),
            "primary_center_x": cx,
            "faces": faces,
            "is_scene_cut": is_scene_cut,
        })

        current_frame += sample_step_frames
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

    cap.release()

    total_samples = len(samples)
    faces_detected_count = len(detected_centers_x)
    face_detected = faces_detected_count > 0
    face_visible_ratio = round(faces_detected_count / max(1, total_samples), 3)
    multi_speaker_detected = (two_face_counts / max(1, total_samples)) >= 0.40

    # Dynamic Dead-Zone Trajectory Smoothing with Scene Reset
    dead_zone_ratio = getattr(settings, "crop_dead_zone_ratio", 0.12)
    smooth_alpha = getattr(settings, "crop_smoothing_alpha", 0.20)
    dead_zone_width = int(width * dead_zone_ratio)

    current_camera_center = width / 2.0
    trajectory = []

    if face_detected:
        initial_median = float(np.median(detected_centers_x))
        current_camera_center = initial_median

    for smp in samples:
        t_s = smp["timestamp_s"]
        target_cx = smp["primary_center_x"]
        is_cut = smp.get("is_scene_cut", False)

        if target_cx is not None:
            if is_cut:
                # Scene cut: instant reset without lagging EMA
                current_camera_center = float(target_cx)
            else:
                # Check dead-zone
                delta = target_cx - current_camera_center
                if abs(delta) > (dead_zone_width / 2.0):
                    adjustment = delta - np.sign(delta) * (dead_zone_width / 2.0)
                    current_camera_center += smooth_alpha * adjustment

        # Calculate bounding crop_x
        computed_crop_x = int(current_camera_center - (target_crop_w / 2.0))
        clamped_crop_x = max(0, min(max_x, computed_crop_x))

        trajectory.append({
            "time": t_s,
            "time_s": t_s,
            "center_x": round(current_camera_center, 1),
            "smooth_center_x": round(current_camera_center, 1),
            "target_center_x": target_cx,
            "crop_x": clamped_crop_x,
            "scene_cut": is_cut,
        })

    # Overall representative crop_x
    if face_detected:
        final_median_x = float(np.median(detected_centers_x))
        rep_crop_x = int(final_median_x - (target_crop_w // 2))
        rep_crop_x = max(0, min(max_x, rep_crop_x))
        avg_x_ratio = round(final_median_x / width, 3)
    else:
        rep_crop_x = max(0, (width - target_crop_w) // 2)
        avg_x_ratio = 0.5

    return {
        "face_detected": face_detected,
        "face_visible_ratio": face_visible_ratio,
        "source_width": width,
        "source_height": height,
        "target_crop_width": target_crop_w,
        "target_crop_height": height,
        "crop_x": rep_crop_x,
        "crop_y": 0,
        "average_x_ratio": avg_x_ratio,
        "trajectory": trajectory,
        "multi_speaker_detected": multi_speaker_detected,
    }


def simplify_trajectory_points(points: List[Tuple[float, int]], max_points: int = 25) -> List[Tuple[float, int]]:
    """
    Simplifies trajectory keypoints to prevent FFmpeg AST parser stack overflow.
    Merges stationary plateaus and simplifies collinear segments to at most max_points.
    """
    if len(points) <= 2:
        return points

    deduped: List[Tuple[float, int]] = [points[0]]
    for i in range(1, len(points) - 1):
        prev_t, prev_x = deduped[-1]
        cur_t, cur_x = points[i]
        next_t, next_x = points[i + 1]
        if cur_x != prev_x or cur_x != next_x:
            deduped.append((cur_t, cur_x))
    deduped.append(points[-1])

    if len(deduped) <= max_points:
        return deduped

    def point_line_dist(pt: Tuple[float, int], p1: Tuple[float, int], p2: Tuple[float, int]) -> float:
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        norm = (dx**2 + dy**2)**0.5
        if norm == 0:
            return ((pt[0] - p1[0])**2 + (pt[1] - p1[1])**2)**0.5
        return abs(dy * pt[0] - dx * pt[1] + p2[0] * p1[1] - p2[1] * p1[0]) / norm

    def rdp(pts: List[Tuple[float, int]], epsilon: float) -> List[Tuple[float, int]]:
        if len(pts) <= 2:
            return pts
        dists = [point_line_dist(p, pts[0], pts[-1]) for p in pts]
        max_idx = int(np.argmax(dists))
        max_dist = dists[max_idx]
        if max_dist > epsilon:
            left = rdp(pts[:max_idx + 1], epsilon)
            right = rdp(pts[max_idx:], epsilon)
            return left[:-1] + right
        else:
            return [pts[0], pts[-1]]

    simplified = deduped
    eps = 1.0
    while len(simplified) > max_points and eps < 100.0:
        simplified = rdp(deduped, eps)
        eps += 2.0

    if len(simplified) > max_points:
        indices = np.linspace(0, len(simplified) - 1, max_points, dtype=int)
        simplified = [simplified[i] for i in indices]

    return simplified


def build_dynamic_crop_expression(
    trajectory: List[Dict[str, Any]],
    clip_start_s: float = 0.0,
    default_x: int = 0,
    max_x: int = 1920,
) -> str:
    """
    Builds an analytical FFmpeg mathematical expression for crop x coordinate.
    Uses nested lerp intervals for fluid, continuous frame-by-frame camera motion.
    Simplifies keypoints to remain strictly within FFmpeg AST depth limits.
    """
    if not trajectory or len(trajectory) < 2:
        return str(default_x)

    points: List[Tuple[float, int]] = []
    for pt in trajectory:
        t_val = pt.get("timestamp_s") if "timestamp_s" in pt else (pt.get("time_s") if "time_s" in pt else pt.get("time", 0.0))
        t_rel = max(0.0, float(t_val) - clip_start_s)
        cx = int(pt.get("crop_x", default_x))
        clamped = max(0, min(max_x, cx))
        points.append((round(t_rel, 2), clamped))

    if not points:
        return str(default_x)

    # Simplify trajectory to max 25 piecewise nodes
    points = simplify_trajectory_points(points, max_points=25)

    # If all positions are identical, keep static constant
    all_x = [p[1] for p in points]
    if min(all_x) == max(all_x):
        return str(all_x[0])

    # Construct nested piecewise linear interpolation
    last_t, last_x = points[-1]
    expr = str(last_x)

    for i in range(len(points) - 2, -1, -1):
        t_cur, x_cur = points[i]
        t_next, x_next = points[i + 1]
        dt = max(0.01, t_next - t_cur)
        if x_cur == x_next:
            interp = str(x_cur)
        else:
            interp = f"lerp({x_cur},{x_next},(t-{t_cur:.2f})/{dt:.2f})"
        expr = f"if(lt(t,{t_next:.2f}),{interp},{expr})"

    return expr


def generate_crop_plan(
    video_path: Union[str, Path],
    clip_start_ms: int,
    clip_end_ms: int,
    preset: str = "active_speaker",
    output_plan_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Produces a 'crop_plan.json' artifact defining how 16:9 input is mapped to 9:16.
    Supports dynamic trajectory and split-screen layout when multiple speakers are present.
    """
    clip_start_s = clip_start_ms / 1000.0
    clip_end_s = clip_end_ms / 1000.0

    analysis = analyze_video_framing(video_path, clip_start_s, clip_end_s)

    dynamic_crop_expr = str(analysis["crop_x"])

    # Determine filtergraph expression based on preset and analysis
    if preset == "split_screen" or (preset == "active_speaker" and analysis.get("multi_speaker_detected")):
        # Vertical split screen: top speaker + bottom speaker
        filter_expr = (
            "[0:v]crop=iw/2:ih:0:0,scale=1080:960[top];"
            "[0:v]crop=iw/2:ih:iw/2:0,scale=1080:960[bot];"
            "[top][bot]vstack[base]"
        )
        resolved_mode = "split_screen"
    elif preset == "blurred_background" or (preset == "active_speaker" and not analysis["face_detected"]):
        filter_expr = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
            "[0:v]scale=1080:-2[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2[base]"
        )
        resolved_mode = "blurred_background"
    elif preset == "center_crop":
        filter_expr = "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920[base]"
        resolved_mode = "center_crop"
    else:
        # Dynamic face tracking with actual FFmpeg trajectory execution
        max_x = max(0, analysis["source_width"] - analysis["target_crop_width"])
        dynamic_crop_expr = build_dynamic_crop_expression(
            analysis.get("trajectory", []),
            clip_start_s=clip_start_s,
            default_x=analysis["crop_x"],
            max_x=max_x,
        )
        filter_expr = f"crop=ih*9/16:ih:x='{dynamic_crop_expr}':y=0,scale=1080:1920[base]"
        resolved_mode = "dynamic_face_tracking"

    plan = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "preset_requested": preset,
        "mode": resolved_mode,
        "mode_resolved": resolved_mode,
        "source_width": analysis["source_width"],
        "source_height": analysis["source_height"],
        "clip_start_ms": clip_start_ms,
        "clip_end_ms": clip_end_ms,
        "face_detected": analysis["face_detected"],
        "face_visible_ratio": analysis["face_visible_ratio"],
        "multi_speaker_detected": analysis.get("multi_speaker_detected", False),
        "crop_coordinates": {
            "x": analysis["crop_x"],
            "y": analysis["crop_y"],
            "width": analysis["target_crop_width"],
            "height": analysis["target_crop_height"],
        },
        "target_resolution": {"width": 1080, "height": 1920},
        "dynamic_crop_expr": dynamic_crop_expr,
        "trajectory": analysis.get("trajectory", []),
        "ffmpeg_filtergraph_base": filter_expr,
    }

    if output_plan_path:
        out_p = Path(output_plan_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        logger.success(f"Saved crop plan: {out_p.name} (mode: {resolved_mode}, face_ratio: {plan['face_visible_ratio']})")

    return plan

