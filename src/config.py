"""애플리케이션 설정 관리"""

import os
from pathlib import Path
from typing import Optional
from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """LLM 프로바이더 열거형"""
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class ImageProvider(str, Enum):
    """이미지 프로바이더 열거형"""
    PEXELS = "pexels"
    PIXABAY = "pixabay"
    DALLE = "dall-e-3"
    DISABLED = "disabled"


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM 설정
    llm_provider: LLMProvider = Field(default=LLMProvider.OPENAI, alias="LLM_PROVIDER")

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")

    # Google
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    google_model: str = Field(default="gemini-2.0-flash", alias="GOOGLE_MODEL")

    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", alias="ANTHROPIC_MODEL")

    # Ollama
    ollama_url: str = Field(default="http://localhost:11434", alias="OLLAMA_URL")
    ollama_model: str = Field(default="llama3.2", alias="OLLAMA_MODEL")

    # 이미지 프로바이더
    image_provider: ImageProvider = Field(default=ImageProvider.DALLE, alias="IMAGE_PROVIDER")
    pexels_api_key: Optional[str] = Field(default=None, alias="PEXELS_API_KEY")
    pixabay_api_key: Optional[str] = Field(default=None, alias="PIXABAY_API_KEY")

    def get_current_model(self) -> str:
        """현재 설정된 LLM 모델명 반환"""
        match self.llm_provider:
            case LLMProvider.OPENAI:
                return self.openai_model
            case LLMProvider.GOOGLE:
                return self.google_model
            case LLMProvider.ANTHROPIC:
                return self.anthropic_model
            case LLMProvider.OLLAMA:
                return self.ollama_model

    def get_api_key(self) -> Optional[str]:
        """현재 프로바이더의 API 키 반환"""
        match self.llm_provider:
            case LLMProvider.OPENAI:
                return self.openai_api_key
            case LLMProvider.GOOGLE:
                return self.google_api_key
            case LLMProvider.ANTHROPIC:
                return self.anthropic_api_key
            case LLMProvider.OLLAMA:
                return None  # Ollama는 API 키 불필요


# 앱 데이터 디렉토리
def get_app_data_dir() -> Path:
    """애플리케이션 데이터 디렉토리 경로 반환"""
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"

    app_dir = base / "NanumSlide"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_temp_dir() -> Path:
    """임시 디렉토리 경로 반환"""
    temp_dir = get_app_data_dir() / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_cache_dir() -> Path:
    """캐시 디렉토리 경로 반환"""
    cache_dir = get_app_data_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


# 전역 설정 인스턴스
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """설정 인스턴스 반환 (싱글톤)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """설정 다시 로드"""
    global _settings
    _settings = Settings()
    return _settings
