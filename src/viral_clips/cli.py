"""
Command Line Interface for Viral Clips AI.
Provides direct access to pipeline stages for testing, debugging, batch processing, and serving.
"""

import json
import sys
from pathlib import Path
from typing import Optional
import click
from loguru import logger

from viral_clips.core.ffmpeg_utils import check_nvenc_support, find_binary
from viral_clips.core.media_probe import probe_media
from viral_clips.db.database import create_project, get_project_clips
from viral_clips.exceptions import ViralClipsError
from viral_clips.services.pipeline_service import _sync_pipeline_runner, create_job


@click.group()
def main():
    """Viral Clips AI - Video processing pipeline CLI."""
    pass


@main.command()
def env_check():
    """Check system environment, FFmpeg binaries, and GPU acceleration."""
    click.echo("=== Viral Clips AI - Environment Diagnosis ===")

    ffmpeg = find_binary("ffmpeg")
    ffprobe = find_binary("ffprobe")

    click.echo(f"FFmpeg binary:  {ffmpeg or 'NOT FOUND (Required)'}")
    click.echo(f"FFprobe binary: {ffprobe or 'NOT FOUND (Required)'}")

    if ffmpeg:
        nvenc = check_nvenc_support()
        click.echo(f"NVIDIA NVENC support: {'AVAILABLE (Hardware acceleration active)' if nvenc else 'NOT AVAILABLE (Using CPU)'}")
    else:
        click.echo("NVIDIA NVENC support: N/A")


@main.command()
@click.argument("video_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", type=click.Path(dir_okay=False), help="Path to save probe.json artifact")
@click.option("--allow-no-audio", is_flag=True, default=False, help="Allow video without audio stream")
def probe(video_path: str, output: Optional[str], allow_no_audio: bool):
    """Validate and inspect a media file, generating a versioned probe artifact."""
    try:
        click.echo(f"Probing media: {video_path} ...")
        result = probe_media(video_path, allow_missing_audio=allow_no_audio)

        v = result["primary_video"]
        a = result.get("primary_audio")

        click.echo("OK: Media file is valid.")
        click.echo(f"  Duration:   {result['duration_s']}s")
        click.echo(f"  Resolution: {v['width']}x{v['height']} ({v['fps']} fps)")
        click.echo(f"  Video Codec:{v['codec']}")
        if a:
            click.echo(f"  Audio:      {a['codec']} ({a['sample_rate']} Hz, {a['channels']} ch)")
        else:
            click.echo("  Audio:      None")

        if output:
            out_p = Path(output)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            click.echo(f"Saved artifact to: {out_p.resolve()}")
        else:
            click.echo("\n" + json.dumps(result, indent=2, ensure_ascii=False))

    except ViralClipsError as e:
        click.secho(f"Error [{e.code}]: {e.message}", fg="red", err=True)
        if e.details:
            click.secho(f"Details: {json.dumps(e.details, indent=2)}", fg="yellow", err=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"Unexpected error: {e}", fg="red", err=True)
        sys.exit(1)


@main.command()
@click.argument("video_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--clips", "-c", default=5, type=int, help="Number of clips to generate (3/5/10)")
@click.option("--framing", "-f", default="active_speaker", type=click.Choice(["active_speaker", "blurred_background", "center_crop"]))
@click.option("--subtitles", "-s", default="bold_karaoke", type=click.Choice(["bold_karaoke", "minimalist", "hormozi_pop"]))
@click.option("--language", "-l", default="auto", help="Audio language (auto/ru/en)")
@click.option("--output-dir", "-o", default="./storage/cli_output", help="Destination folder for clips")
@click.option("--debug", is_flag=True, default=False, help="Print detailed diagnostic provenance summary")
def process(video_path: str, clips: int, framing: str, subtitles: str, language: str, output_dir: str, debug: bool):
    """Run full End-to-End pipeline on a video file directly from CLI."""
    click.secho(f"=== Starting E2E Pipeline for: {video_path} ===", fg="cyan", bold=True)
    v_path = Path(video_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    project = create_project(name=f"CLI - {v_path.name}", language=language, desired_clip_count=clips)
    p_id = project["id"]
    job = create_job(project_id=p_id, job_type="cli_pipeline")
    j_id = job["id"]

    try:
        _sync_pipeline_runner(
            job_id=j_id,
            project_id=p_id,
            video_path=v_path,
            output_dir=out_dir,
            clip_count=clips,
            min_duration_s=20.0,
            max_duration_s=75.0,
            framing=framing,
            subtitle_preset=subtitles,
            language=language,
        )

        rendered_clips = get_project_clips(p_id)
        click.secho(f"\n[SUCCESS] Generated {len(rendered_clips)} clips in {out_dir}:", fg="green", bold=True)
        for idx, c in enumerate(rendered_clips):
            dur = round((c['end_ms'] - c['start_ms']) / 1000)
            score = c.get('final_score', 8.5)
            click.echo(f"  #{idx+1} [Score: {score}/10] ({dur}s) -> {c.get('video_path')}")

        if debug:
            click.secho("\n=== Pipeline Diagnostic Summary (--debug) ===", fg="yellow", bold=True)
            t_file = out_dir / "transcript.json"
            r_file = out_dir / "ranking.json"
            c_file = out_dir / "candidates.json"

            t_data = json.loads(t_file.read_text(encoding="utf-8")) if t_file.exists() else {}
            r_data = json.loads(r_file.read_text(encoding="utf-8")) if r_file.exists() else {}
            c_data = json.loads(c_file.read_text(encoding="utf-8")) if c_file.exists() else {}

            from viral_clips.config import settings

            click.echo(f"ASR ............... {t_data.get('provider', settings.asr_provider)} {t_data.get('model', settings.whisper_model)}")
            click.echo(f"Language .......... {t_data.get('detected_language', language)} (prob: {t_data.get('language_probability', 1.0)})")
            click.echo(f"Words ............. {t_data.get('total_words', len(t_data.get('words', [])))}\n")

            click.echo(f"Candidates ........ {c_data.get('total_generated', len(c_data.get('candidates', [])))}")
            click.echo(f"Pre-ranked ........ {c_data.get('total_scored', len(c_data.get('candidates', [])))}\n")

            click.echo(f"LLM ................ {r_data.get('provider', settings.llm_provider)}")
            click.echo(f"Model .............. {r_data.get('model', getattr(settings, 'ollama_model', 'qwen2.5:7b'))}")
            if r_data.get("fallback_used"):
                click.secho("Fallback ........... HEURISTIC FALLBACK WAS USED", fg="red", bold=True)
            else:
                click.echo("Fallback ........... disabled (real LLM)")
            click.echo(f"\nSelected clips ..... {len(rendered_clips)}\n")

            click.echo(f"Face tracking ...... {'enabled' if framing == 'active_speaker' else 'disabled'}")
            click.echo(f"Dynamic crop ....... {'enabled' if framing == 'active_speaker' else 'disabled'}\n")

            click.echo(f"Renderer ........... {'h264_nvenc' if settings.use_nvenc else 'libx264'}\n")
            click.echo("Output:")
            click.echo(f"  {out_dir}")

    except Exception as e:
        click.secho(f"\n[FAILED] Pipeline error: {e}", fg="red", err=True)
        sys.exit(1)


@main.command()
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8000, type=int, help="Port to listen on")
def server(host: str, port: int):
    """Start the FastAPI backend and Modern Web UI Studio server."""
    import uvicorn
    click.secho(f"=== Starting Viral Clips Studio at http://{host}:{port} ===", fg="green", bold=True)
    uvicorn.run("viral_clips.api.app:app", host=host, port=port, reload=False)


@main.command()
@click.option("--dest", default="backups", help="Target backup directory")
def backup(dest: str):
    """Create disaster-recovery snapshot with checksums."""
    from viral_clips.core.security import BackupManager
    click.echo(f"Creating snapshot in '{dest}'...")
    target = BackupManager.create_backup(dest_backup_dir=dest)
    click.secho(f"✓ Backup snapshot successfully created at: {target}", fg="green", bold=True)


@main.command()
@click.option("--max-age", default=14, type=int, help="Purge artifacts older than N days")
def cleanup(max_age: int):
    """Execute storage lifecycle cleanup on temporary files and expired runs."""
    from viral_clips.core.storage import StorageLifecycleManager
    click.echo(f"Running lifecycle cleanup (max_age={max_age}d)...")
    mgr = StorageLifecycleManager()
    res = mgr.enforce_retention_policy(max_age_days=max_age)
    click.secho(f"✓ Cleaned {res['deleted_projects']} expired project(s), reclaimed {res['reclaimed_bytes']} bytes.", fg="green", bold=True)


@main.command()
@click.argument("project_id")
def evaluate(project_id: str):
    """Phase 10: Run beta quality benchmark scorecard for a project."""
    from viral_clips.db.database import get_candidates
    from viral_clips.core.evaluation import GoldenBenchmarkRunner
    candidates = get_candidates(project_id)
    if not candidates:
        click.secho(f"No candidates found for project {project_id}", fg="red")
        return
    results = GoldenBenchmarkRunner.run_benchmark_suite(candidates)
    click.secho(f"\n=== Quality Benchmark Report for Project {project_id[:8]} ===", fg="cyan", bold=True)
    click.echo(f"Total Evaluated: {results['total_candidates_evaluated']}")
    click.echo(f"Publishable:     {results['publishable_candidates']} ({results['publishable_ratio']:.1%})")
    click.echo(f"Avg Score:       {results['average_viral_score']}/100")


if __name__ == "__main__":
    main()
