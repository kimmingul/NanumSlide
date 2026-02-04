# src/agents/base_agent.py
"""에이전트 기본 클래스 정의"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from enum import Enum
import asyncio

if TYPE_CHECKING:
    from src.services.llm_client import BaseLLMClient
    from .agent_context import AgentContext


class AgentStatus(Enum):
    """에이전트 상태"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


@dataclass
class AgentResult:
    """에이전트 실행 결과"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    tokens_used: int = 0


@dataclass
class AgentMessage:
    """에이전트 간 메시지"""
    from_agent: str
    to_agent: str
    message_type: str  # "request", "response", "notification"
    content: Any
    timestamp: float


class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""

    def __init__(
        self,
        name: str,
        llm_client: "BaseLLMClient",
        config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.llm_client = llm_client
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self._messages: List[AgentMessage] = []

    @abstractmethod
    async def run(self, context: "AgentContext") -> AgentResult:
        """에이전트 실행 - 하위 클래스에서 구현"""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """에이전트의 시스템 프롬프트 반환"""
        pass

    async def send_message(
        self,
        to_agent: str,
        message_type: str,
        content: Any
    ) -> None:
        """다른 에이전트에게 메시지 전송"""
        try:
            loop = asyncio.get_event_loop()
            timestamp = loop.time()
        except RuntimeError:
            import time
            timestamp = time.time()

        message = AgentMessage(
            from_agent=self.name,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            timestamp=timestamp
        )
        self._messages.append(message)

    def receive_messages(self) -> List[AgentMessage]:
        """수신된 메시지 조회"""
        received = [m for m in self._messages if m.to_agent == self.name]
        return received

    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_schema: Optional[Dict] = None
    ) -> str:
        """LLM 호출 래퍼"""
        system = system_prompt or self.get_system_prompt()

        if json_schema:
            result = await self.llm_client.generate_structured(
                prompt=prompt,
                system_prompt=system,
                response_schema=json_schema
            )
            # generate_structured returns dict, convert to string for consistency
            import json
            return json.dumps(result, ensure_ascii=False)
        else:
            return await self.llm_client.generate(
                prompt=prompt,
                system_prompt=system
            )

    def update_status(self, status: AgentStatus) -> None:
        """상태 업데이트"""
        self.status = status
