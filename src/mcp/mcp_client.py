"""MCP 클라이언트 모듈

MCP(Model Context Protocol) 서버와의 통신을 담당하는 기본 클라이언트 클래스입니다.
JSON-RPC over stdio를 사용하여 MCP 서버와 통신합니다.
"""

import asyncio
import json
import subprocess
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """MCP 서버 설정

    Attributes:
        name: 서버 이름
        command: 실행 명령어 (예: "npx")
        args: 명령어 인자 리스트
        env: 환경 변수 딕셔너리
    """
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]


@dataclass
class MCPToolInfo:
    """MCP 도구 정보

    Attributes:
        name: 도구 이름
        description: 도구 설명
        parameters: 입력 파라미터 스키마
    """
    name: str
    description: str
    parameters: Dict[str, Any]


class MCPError(Exception):
    """MCP 에러

    MCP 서버에서 반환된 에러를 나타냅니다.

    Attributes:
        message: 에러 메시지
        code: 에러 코드
    """
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return f"MCPError({self.code}): {self.message}"


class MCPClient:
    """MCP 클라이언트

    MCP 서버와의 통신을 관리하는 클라이언트 클래스입니다.
    JSON-RPC 프로토콜을 사용하여 MCP 서버와 통신합니다.

    Attributes:
        config: MCP 서버 설정
    """

    def __init__(self, config: MCPServerConfig):
        """MCPClient 초기화

        Args:
            config: MCP 서버 설정
        """
        self.config = config
        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._connected = False
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._connected

    async def connect(self) -> bool:
        """MCP 서버 연결

        MCP 서버 프로세스를 시작하고 초기화 핸드셰이크를 수행합니다.

        Returns:
            연결 성공 여부
        """
        try:
            # 환경 변수 설정
            env = os.environ.copy()
            env.update(self.config.env)

            self._process = subprocess.Popen(
                [self.config.command] + self.config.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1
            )

            # 초기화 핸드셰이크
            init_response = await self._send_request("initialize", {
                "protocolVersion": "0.1.0",
                "clientInfo": {
                    "name": "NanumSlide",
                    "version": "1.0.0"
                }
            })

            if init_response.get("result"):
                self._connected = True
                logger.info(f"MCP server '{self.config.name}' connected")
                return True

            logger.warning(f"MCP server '{self.config.name}' initialization failed")
            return False

        except FileNotFoundError as e:
            logger.error(f"MCP server command not found: {self.config.command}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect MCP server '{self.config.name}': {e}")
            return False

    async def disconnect(self) -> None:
        """MCP 서버 연결 해제

        MCP 서버 프로세스를 종료합니다.
        """
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            finally:
                self._process = None
                self._connected = False
                logger.info(f"MCP server '{self.config.name}' disconnected")

    async def list_tools(self) -> List[MCPToolInfo]:
        """사용 가능한 도구 목록 조회

        MCP 서버에서 사용 가능한 모든 도구의 목록을 조회합니다.

        Returns:
            MCPToolInfo 객체 리스트

        Raises:
            RuntimeError: 연결되지 않은 경우
        """
        if not self._connected:
            raise RuntimeError("MCP client not connected")

        response = await self._send_request("tools/list", {})

        tools = []
        for tool in response.get("result", {}).get("tools", []):
            tools.append(MCPToolInfo(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=tool.get("inputSchema", {})
            ))

        return tools

    async def call_tool(
        self,
        server: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """도구 호출

        MCP 서버의 도구를 호출합니다.

        Args:
            server: 서버 이름 (현재는 사용되지 않음, 향후 멀티 서버 지원용)
            tool_name: 호출할 도구 이름
            arguments: 도구에 전달할 인자

        Returns:
            도구 실행 결과

        Raises:
            RuntimeError: 연결되지 않은 경우
            MCPError: 도구 호출 중 에러 발생 시
        """
        if not self._connected:
            raise RuntimeError("MCP client not connected")

        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        if "error" in response:
            raise MCPError(
                response["error"].get("message", "Unknown error"),
                response["error"].get("code", -1)
            )

        return response.get("result", {})

    async def _send_request(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """JSON-RPC 요청 전송

        MCP 서버에 JSON-RPC 요청을 보내고 응답을 받습니다.

        Args:
            method: RPC 메서드 이름
            params: 메서드 파라미터

        Returns:
            서버 응답

        Raises:
            RuntimeError: 프로세스가 실행중이지 않은 경우
        """
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise RuntimeError("MCP process not running")

        async with self._lock:
            self._request_id += 1

            request = {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": method,
                "params": params
            }

            request_str = json.dumps(request) + "\n"

            # 비동기 쓰기/읽기를 위해 별도 스레드에서 실행
            loop = asyncio.get_event_loop()

            def write_and_read():
                self._process.stdin.write(request_str)
                self._process.stdin.flush()
                response_str = self._process.stdout.readline()
                return response_str

            response_str = await loop.run_in_executor(None, write_and_read)

            if not response_str:
                return {"error": {"code": -1, "message": "Empty response from server"}}

            return json.loads(response_str)

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.disconnect()
