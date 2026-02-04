"""MCP Configuration Manager.

MCP 설정을 관리하고 저장/로드하는 모듈입니다.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any

import structlog

logger = structlog.get_logger(__name__)

# 설정 파일 경로
CONFIG_FILE = Path.home() / ".nanumslide" / "mcp_config.json"


@dataclass
class MCPServiceConfig:
    """개별 MCP 서비스 설정"""
    enabled: bool = False
    connected: bool = False
    api_key: Optional[str] = None
    server_url: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPConfig:
    """전체 MCP 설정"""
    # PowerPoint MCP
    powerpoint: MCPServiceConfig = field(default_factory=lambda: MCPServiceConfig(
        enabled=False,
        options={"features": ["charts", "smartart", "animations", "transitions"]}
    ))

    # 웹 검색 MCP
    web_search: MCPServiceConfig = field(default_factory=lambda: MCPServiceConfig(
        enabled=True,  # 기본 활성화 (DuckDuckGo는 무료)
        options={"provider": "duckduckgo", "max_results": 10}
    ))

    # 이미지 생성 MCP
    image_generation: MCPServiceConfig = field(default_factory=lambda: MCPServiceConfig(
        enabled=False,
        options={"provider": "dalle3", "size": "1024x1024"}
    ))

    # 글로벌 설정
    auto_connect: bool = True
    verbose_logging: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            "powerpoint": asdict(self.powerpoint),
            "web_search": asdict(self.web_search),
            "image_generation": asdict(self.image_generation),
            "auto_connect": self.auto_connect,
            "verbose_logging": self.verbose_logging,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPConfig":
        """딕셔너리에서 설정 로드"""
        config = cls()

        if "powerpoint" in data:
            config.powerpoint = MCPServiceConfig(**data["powerpoint"])
        if "web_search" in data:
            config.web_search = MCPServiceConfig(**data["web_search"])
        if "image_generation" in data:
            config.image_generation = MCPServiceConfig(**data["image_generation"])

        config.auto_connect = data.get("auto_connect", True)
        config.verbose_logging = data.get("verbose_logging", False)

        return config


class MCPConfigManager:
    """MCP 설정 관리자"""

    _instance: Optional["MCPConfigManager"] = None
    _config: MCPConfig

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = MCPConfig()
            cls._instance._load()
        return cls._instance

    def _load(self):
        """설정 파일에서 로드"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = MCPConfig.from_dict(data)
                logger.info("MCP config loaded", path=str(CONFIG_FILE))
            except Exception as e:
                logger.error("Failed to load MCP config", error=str(e))
                self._config = MCPConfig()
        else:
            self._config = MCPConfig()

    def save(self):
        """설정을 파일에 저장"""
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info("MCP config saved", path=str(CONFIG_FILE))
        except Exception as e:
            logger.error("Failed to save MCP config", error=str(e))

    @property
    def config(self) -> MCPConfig:
        """현재 설정 반환"""
        return self._config

    def update_service(self, service_name: str, **kwargs):
        """서비스 설정 업데이트"""
        if hasattr(self._config, service_name):
            service_config = getattr(self._config, service_name)
            for key, value in kwargs.items():
                if hasattr(service_config, key):
                    setattr(service_config, key, value)
            self.save()

    def is_service_enabled(self, service_name: str) -> bool:
        """서비스 활성화 여부 확인"""
        if hasattr(self._config, service_name):
            return getattr(self._config, service_name).enabled
        return False

    def set_service_enabled(self, service_name: str, enabled: bool):
        """서비스 활성화/비활성화"""
        self.update_service(service_name, enabled=enabled)

    def set_service_connected(self, service_name: str, connected: bool):
        """서비스 연결 상태 설정"""
        if hasattr(self._config, service_name):
            getattr(self._config, service_name).connected = connected


def get_mcp_config() -> MCPConfig:
    """현재 MCP 설정 반환"""
    return MCPConfigManager().config


def get_mcp_config_manager() -> MCPConfigManager:
    """MCP 설정 관리자 반환"""
    return MCPConfigManager()
