from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", env_file_encoding="utf-8")

    PROGRAM_ENTRYPOINT: str = Field(default="runner.py:main", description="Module:function or script path")
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] | str = [".xlsx"]
    JOB_TTL_MINUTES: int = 120
    OUTPUT_DIR_BASE: Path | str = Path("./data")
    FRONTEND_DIST_DIR: Path | None = None  # optional static mount

    # server
    HOST: str = "0.0.0.0"
    PORT: int = 8080

settings = Settings()

# Normalize values coming from env
if isinstance(settings.ALLOWED_EXTENSIONS, str):
    raw = settings.ALLOWED_EXTENSIONS
    parts = [p.strip() for p in raw.replace(";", ",").replace(" ", ",").split(",") if p.strip()]
    settings.ALLOWED_EXTENSIONS = [p if p.startswith(".") else f".{p}" for p in parts]

if isinstance(settings.OUTPUT_DIR_BASE, str):
    settings.OUTPUT_DIR_BASE = Path(settings.OUTPUT_DIR_BASE)

settings.OUTPUT_DIR_BASE.mkdir(parents=True, exist_ok=True)
