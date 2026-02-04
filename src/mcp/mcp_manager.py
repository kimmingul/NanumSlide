"""MCP 매니저 모듈

여러 MCP 서버의 연결을 관리하고 클라이언트를 제공하는 매니저 클래스입니다.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING
import asyncio
import logging

from .mcp_client import MCPClient, MCPServerConfig

if TYPE_CHECKING:
    from .powerpoint_mcp import PowerPointMCPClient
    from .web_search_mcp import WebSearchMCPClient

logger = logging.getLogger(__name__)


class MCPManager:
    """MCP 서버 관리자

    MCP 서버들의 연결을 관리하고 각 서버에 대한 전용 클라이언트를 제공합니다.

    Attributes:
        config_path: MCP 설정 파일 경로
    """

    def __init__(self, config_path: str = "mcp.json"):
        """MCPManager 초기화

        Args:
            config_path: MCP 설정 파일 경로 (기본값: "mcp.json")
        """
        self.config_path = Path(config_path)
        self._clients: Dict[str, MCPClient] = {}
        self._config: Optional[Dict] = None

        # 전용 클라이언트
        self._powerpoint: Optional["PowerPointMCPClient"] = None
        self._web_search: Optional["WebSearchMCPClient"] = None

    def load_config(self) -> Dict:
        """설정 파일 로드

        MCP 설정 파일을 로드합니다. 파일이 없으면 빈 설정을 반환합니다.

        Returns:
            MCP 설정 딕셔너리
        """
        if self._config is None:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            else:
                logger.warning(f"MCP config file not found: {self.config_path}")
                self._config = {"mcpServers": {}}
        return self._config

    async def connect_all(self) -> None:
        """모든 MCP 서버 연결

        설정 파일에 정의된 모든 MCP 서버에 연결합니다.
        """
        config = self.load_config()

        for name, server_config in config.get("mcpServers", {}).items():
            await self.connect_server(name, server_config)

    async def connect_server(
        self,
        name: str,
        server_config: Dict
    ) -> bool:
        """특정 MCP 서버 연결

        Args:
            name: 서버 이름
            server_config: 서버 설정 딕셔너리

        Returns:
            연결 성공 여부
        """
        try:
            # 환경 변수 치환
            env = self._resolve_env_vars(server_config.get("env", {}))

            config = MCPServerConfig(
                name=name,
                command=server_config["command"],
                args=server_config.get("args", []),
                env=env
            )

            client = MCPClient(config)
            connected = await client.connect()

            if connected:
                self._clients[name] = client

                # PowerPoint 전용 클라이언트 초기화
                if name == "powerpoint":
                    from .powerpoint_mcp import PowerPointMCPClient
                    self._powerpoint = PowerPointMCPClient(client)

                # Web Search 전용 클라이언트 초기화
                if name == "web-search":
                    from .web_search_mcp import WebSearchMCPClient
                    self._web_search = WebSearchMCPClient(client)

                logger.info(f"Successfully connected to MCP server: {name}")
                return True

            logger.warning(f"Failed to connect to MCP server: {name}")
            return False

        except Exception as e:
            logger.error(f"Failed to connect server '{name}': {e}")
            return False

    async def disconnect_all(self) -> None:
        """모든 MCP 서버 연결 해제

        모든 연결된 MCP 서버와의 연결을 해제합니다.
        """
        for name, client in self._clients.items():
            try:
                await client.disconnect()
                logger.info(f"Disconnected from MCP server: {name}")
            except Exception as e:
                logger.error(f"Error disconnecting from server '{name}': {e}")

        self._clients.clear()
        self._powerpoint = None
        self._web_search = None

    async def disconnect_server(self, name: str) -> bool:
        """특정 MCP 서버 연결 해제

        Args:
            name: 서버 이름

        Returns:
            연결 해제 성공 여부
        """
        if name in self._clients:
            try:
                await self._clients[name].disconnect()
                del self._clients[name]

                if name == "powerpoint":
                    self._powerpoint = None
                if name == "web-search":
                    self._web_search = None

                logger.info(f"Disconnected from MCP server: {name}")
                return True
            except Exception as e:
                logger.error(f"Error disconnecting from server '{name}': {e}")
                return False
        return False

    def get_client(self, name: str) -> Optional[MCPClient]:
        """MCP 클라이언트 조회

        Args:
            name: 서버 이름

        Returns:
            MCPClient 인스턴스 또는 None
        """
        return self._clients.get(name)

    @property
    def powerpoint(self) -> Optional["PowerPointMCPClient"]:
        """PowerPoint 클라이언트

        Returns:
            PowerPointMCPClient 인스턴스 또는 None
        """
        return self._powerpoint

    @property
    def web_search(self) -> Optional["WebSearchMCPClient"]:
        """Web Search 클라이언트

        Returns:
            WebSearchMCPClient 인스턴스 또는 None
        """
        return self._web_search

    def is_connected(self, name: str) -> bool:
        """서버 연결 상태 확인

        Args:
            name: 서버 이름

        Returns:
            연결 여부
        """
        return name in self._clients and self._clients[name].is_connected

    def get_connected_servers(self) -> list[str]:
        """연결된 서버 목록 조회

        Returns:
            연결된 서버 이름 리스트
        """
        return [name for name, client in self._clients.items() if client.is_connected]

    def _resolve_env_vars(self, env: Dict[str, str]) -> Dict[str, str]:
        """환경 변수 치환

        ${VAR_NAME} 형식의 값을 실제 환경 변수 값으로 치환합니다.

        Args:
            env: 환경 변수 딕셔너리

        Returns:
            치환된 환경 변수 딕셔너리
        """
        resolved = {}

        for key, value in env.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_name = value[2:-1]
                resolved[key] = os.environ.get(env_name, "")
            else:
                resolved[key] = value

        return resolved

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입

        모든 MCP 서버에 연결합니다.
        """
        await self.connect_all()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료

        모든 MCP 서버 연결을 해제합니다.
        """
        await self.disconnect_all()
