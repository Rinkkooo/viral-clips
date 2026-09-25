"""
Standardized application exceptions and error codes.
Aligned with Problem Details specification (RFC 7807) defined in 05_API.md.
"""

from typing import Any, Dict, Optional


class ViralClipsError(Exception):
    """Base application exception."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class MediaProbeError(ViralClipsError):
    """Raised when ffprobe fails to parse media or file is corrupted."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="MEDIA_PROBE_FAILED",
            message=message,
            status_code=422,
            details=details,
        )


class MediaLimitExceededError(ViralClipsError):
    """Raised when media exceeds allowed duration, dimensions, fps, or size."""

    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=code,
            message=message,
            status_code=400,
            details=details,
        )


class UnsupportedCodecError(ViralClipsError):
    """Raised when media uses an unsupported video or audio codec."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="UNSUPPORTED_CODEC",
            message=message,
            status_code=415,
            details=details,
        )


class MissingStreamError(ViralClipsError):
    """Raised when media lacks an audio or video stream."""

    def __init__(self, message: str, stream_type: str):
        super().__init__(
            code=f"MISSING_{stream_type.upper()}_STREAM",
            message=message,
            status_code=422,
            details={"required_stream": stream_type},
        )
