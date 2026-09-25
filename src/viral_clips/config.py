"""
Application configuration management.
Implements strict security boundaries:
- Loads from environment variables / .env
- Secret keys are never exposed in logs or string representations
- Validates operational limits and hardware concurrency
"""

from pathlib import Path
from typing import Literal, Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_env: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"

    # Hardware & Video Engine
    # Per 03_ARCHITECTURE.md: Concurrency default 1 on RTX 4060 8GB
    gpu_worker_concurrency: int = Field(default=1, ge=1, le=4)
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    use_nvenc: bool = True

    # Media Validation & Security Limits (07_SECURITY_PERFORMANCE.md)
    max_source_duration_minutes: int = Field(default=180, description="Max allowed video length")
    max_video_width: int = Field(default=3840, description="Max video width in pixels")
    max_video_height: int = Field(default=2160, description="Max video height in pixels")
    max_video_fps: int = Field(default=60, description="Max video frames per second")
    max_file_size_bytes: int = Field(
        default=10 * 1024 * 1024 * 1024,  # 10 GB
        description="Max raw file upload size in bytes",
    )
    max_video_streams: int = 1
    max_audio_streams: int = 4
    max_clips_per_run: int = 10

    # ASR (Transcription)
    asr_provider: str = "faster_whisper"
    whisper_model: str = "small"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"

    # LLM Settings (Highlight & Rerank)
    llm_provider: Literal["ollama", "gemini", "openai"] = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"
    gemini_model: str = "gemini-2.5-flash"
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: Optional[SecretStr] = None
    openai_api_key: Optional[SecretStr] = None
    groq_api_key: Optional[SecretStr] = None
    allow_heuristic_llm_fallback: bool = Field(default=False, description="Strictly prohibit silent heuristic fallback unless True")

    # Clip & Framing Settings
    clip_min_duration_seconds: int = 20
    clip_max_duration_seconds: int = 90
    crop_dead_zone_ratio: float = 0.12
    crop_smoothing_alpha: float = 0.20

    # Storage Settings
    storage_provider: Literal["local", "r2"] = "local"
    storage_local_dir: Path = Path("./storage")
    storage_temp_dir: Path = Path("./temp")

    # Cloudflare R2 Settings (Production)
    r2_account_id: Optional[str] = None
    r2_access_key_id: Optional[str] = None
    r2_secret_access_key: Optional[SecretStr] = None
    r2_bucket_name: Optional[str] = None
    r2_public_url_prefix: Optional[str] = None

    # Database & Queue
    database_url: str = "sqlite:///./storage/viral_clips.db"
    redis_url: str = "redis://localhost:6379/0"

    # Security & Execution Boundaries
    allow_test_fixtures: bool = Field(default=False, description="Strictly allow synthetic test fixtures only in test suite")
    google_drive_credentials_json: Optional[str] = None
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"])

    def get_gemini_key(self) -> Optional[str]:
        return self.gemini_api_key.get_secret_value() if self.gemini_api_key else None

    def get_openai_key(self) -> Optional[str]:
        return self.openai_api_key.get_secret_value() if self.openai_api_key else None

    def get_groq_key(self) -> Optional[str]:
        return self.groq_api_key.get_secret_value() if self.groq_api_key else None


# Singleton instance
settings = Settings()
