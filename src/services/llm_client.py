"""LLM 클라이언트 - 다양한 AI 모델 지원"""

import re
from typing import AsyncGenerator, Optional
from abc import ABC, abstractmethod

from openai import OpenAI
from anthropic import Anthropic, AsyncAnthropic

from src.config import get_settings, LLMProvider


# 캐시된 모델 목록 (프로바이더별)
_cached_models: dict[str, list[str]] = {
    "openai": [],
    "anthropic": [],
}


def _extract_version(model_name: str) -> tuple[float, str]:
    """모델명에서 버전 번호 추출 (정렬용)"""
    # 숫자 패턴 찾기 (예: gpt-4, gpt-4o, claude-3.5, o1 등)
    patterns = [
        r'(\d+\.?\d*)',  # 일반 숫자
    ]

    for pattern in patterns:
        match = re.search(pattern, model_name)
        if match:
            try:
                version = float(match.group(1))
                return (version, model_name)
            except ValueError:
                pass

    return (0.0, model_name)


def _sort_models_by_newest(models: list[str]) -> list[str]:
    """모델 목록을 최신순으로 정렬"""
    # 버전 번호로 내림차순 정렬
    return sorted(models, key=_extract_version, reverse=True)


def fetch_openai_models(api_key: str) -> tuple[bool, str, list[str]]:
    """OpenAI API에서 사용 가능한 모델 목록 가져오기"""
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()

        # GPT-5.2만 필터링
        chat_models = []
        for m in models.data:
            model_id = m.id.lower()

            # GPT-5.2 모델만 포함
            if 'gpt-5' in model_id:
                chat_models.append(m.id)

        # 최신순 정렬
        sorted_models = _sort_models_by_newest(chat_models)

        # 캐시 업데이트
        _cached_models["openai"] = sorted_models

        return True, f"✓ 유효한 키입니다. {len(sorted_models)}개 모델 사용 가능", sorted_models
    except Exception as e:
        error_str = str(e)
        if "invalid" in error_str.lower() or "auth" in error_str.lower():
            return False, "✗ API 키가 유효하지 않습니다.", []
        return False, f"✗ 연결 오류: {error_str[:100]}", []


def fetch_anthropic_models(api_key: str) -> tuple[bool, str, list[str]]:
    """Anthropic API 키 검증 및 사용 가능한 모델 목록 반환"""
    # Anthropic은 모델 목록 API가 없으므로 알려진 모델들을 직접 테스트
    known_models = [
        "claude-opus-4-5-20251101",
        "claude-sonnet-4-20251101",
        "claude-3-7-sonnet-20250219",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]

    try:
        client = Anthropic(api_key=api_key)

        # 키 검증을 위해 간단한 요청
        available_models = []

        # 가장 저렴한 모델로 키 검증
        try:
            client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "hi"}],
            )
            # 키가 유효하면 모든 알려진 모델 사용 가능으로 표시
            available_models = known_models
        except Exception as e:
            if "model" in str(e).lower():
                # 모델 관련 오류면 다른 모델 시도
                available_models = known_models
            else:
                raise e

        # 최신순 정렬
        sorted_models = _sort_models_by_newest(available_models)

        # 캐시 업데이트
        _cached_models["anthropic"] = sorted_models

        return True, f"✓ 유효한 키입니다. {len(sorted_models)}개 모델 사용 가능", sorted_models
    except Exception as e:
        error_str = str(e)
        if "authentication" in error_str.lower() or "api key" in error_str.lower():
            return False, "✗ API 키가 유효하지 않습니다.", []
        if "invalid" in error_str.lower():
            return False, "✗ API 키가 유효하지 않습니다.", []
        return False, f"✗ 연결 오류: {error_str[:100]}", []


def get_cached_models(provider: str) -> list[str]:
    """캐시된 모델 목록 반환"""
    return _cached_models.get(provider, [])


def get_all_available_models() -> list[tuple[str, str]]:
    """모든 사용 가능한 모델 목록 반환 (프로바이더, 모델명) 튜플 리스트"""
    settings = get_settings()
    models = []

    # 캐시된 모델이 없으면 API에서 가져오기 시도
    if settings.openai_api_key and not _cached_models["openai"]:
        fetch_openai_models(settings.openai_api_key)

    if settings.anthropic_api_key and not _cached_models["anthropic"]:
        fetch_anthropic_models(settings.anthropic_api_key)

    # OpenAI 모델
    for model in _cached_models["openai"]:
        models.append(("openai", model))

    # Anthropic 모델
    for model in _cached_models["anthropic"]:
        models.append(("anthropic", model))

    return models


def get_available_models() -> list[str]:
    """UI 표시용 모델 목록 반환 (프로바이더 포함)"""
    settings = get_settings()
    models = []

    # 캐시된 모델이 없으면 API에서 가져오기 시도
    if settings.openai_api_key:
        if not _cached_models["openai"]:
            fetch_openai_models(settings.openai_api_key)
        for model in _cached_models["openai"]:
            models.append(f"[OpenAI] {model}")

    if settings.anthropic_api_key:
        if not _cached_models["anthropic"]:
            fetch_anthropic_models(settings.anthropic_api_key)
        for model in _cached_models["anthropic"]:
            models.append(f"[Anthropic] {model}")

    # 캐시된 모델이 하나도 없으면 기본 메시지
    if not models:
        models.append("(설정에서 API 키를 입력하세요)")

    return models


def parse_model_selection(display_name: str) -> tuple[str, str]:
    """UI 표시명에서 (프로바이더, 모델명) 반환"""
    if display_name.startswith("[OpenAI] "):
        return ("openai", display_name.replace("[OpenAI] ", ""))
    elif display_name.startswith("[Anthropic] "):
        return ("anthropic", display_name.replace("[Anthropic] ", ""))
    else:
        # 기본값
        return ("openai", "gpt-4o")


class BaseLLMClient(ABC):
    """LLM 클라이언트 기본 클래스"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> str:
        """텍스트 생성"""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        """스트리밍 텍스트 생성"""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> dict:
        """구조화된 JSON 응답 생성"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI 클라이언트 (GPT-5.2 Responses API 전용)"""

    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> str:
        """Responses API를 사용한 텍스트 생성"""
        import asyncio

        # 시스템 프롬프트와 사용자 프롬프트 결합
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        def sync_call():
            response = self.client.responses.create(
                model=self.model,
                input=full_prompt,
            )
            return response.output_text or ""

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_call)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        """Responses API 스트리밍 (미지원 시 일반 응답)"""
        # Responses API는 스트리밍 지원 여부 확인 필요
        # 현재는 일반 응답으로 대체
        result = await self.generate(prompt, system_prompt, max_tokens)
        yield result

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> dict:
        """Responses API를 사용한 구조화된 JSON 응답 생성"""
        import json
        import re
        import asyncio

        # 시스템 프롬프트와 사용자 프롬프트 결합
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # 1차 시도: Responses API with JSON schema
        def sync_call_with_schema():
            response = self.client.responses.create(
                model=self.model,
                input=full_prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "response",
                        "schema": response_schema,
                    }
                },
            )
            return response.output_text or "{}"

        try:
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, sync_call_with_schema)
            return json.loads(content)
        except Exception as e:
            print(f"Responses API JSON schema 실패: {e}")

        # 2차 시도: 일반 텍스트 응답에서 JSON 추출
        def sync_call_text():
            response = self.client.responses.create(
                model=self.model,
                input=full_prompt + "\n\n반드시 JSON 형식으로만 응답해주세요. 다른 텍스트 없이 JSON만 출력하세요.",
            )
            return response.output_text or ""

        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, sync_call_text)

        # JSON 블록 추출
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            return json.loads(json_match.group(1))

        json_match = re.search(r'(\{[\s\S]*\})', text)
        if json_match:
            return json.loads(json_match.group(1))

        raise ValueError(f"JSON 파싱 실패: {text[:200]}")


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude 클라이언트"""

    def __init__(self, api_key: str, model: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> dict:
        import json
        import re

        # 1차 시도: 도구 사용 강제
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
                tools=[
                    {
                        "name": "create_presentation",
                        "description": "프레젠테이션 데이터를 생성합니다",
                        "input_schema": response_schema,
                    }
                ],
                tool_choice={"type": "tool", "name": "create_presentation"},
            )

            for content in response.content:
                if content.type == "tool_use":
                    return content.input
        except Exception:
            pass  # 도구 사용 실패 시 텍스트 응답으로 대체

        # 2차 시도: 일반 텍스트에서 JSON 추출
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt + "\n\n반드시 JSON 형식으로만 응답해주세요."}],
        )

        text = response.content[0].text if response.content else ""

        # JSON 블록 추출
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            return json.loads(json_match.group(1))

        json_match = re.search(r'(\{[\s\S]*\})', text)
        if json_match:
            return json.loads(json_match.group(1))

        raise ValueError(f"JSON 파싱 실패: {text[:200]}")


class OllamaClient(BaseLLMClient):
    """Ollama 클라이언트 (OpenAI 호환 API 사용)"""

    def __init__(self, base_url: str, model: str):
        self.client = AsyncOpenAI(
            base_url=f"{base_url}/v1",
            api_key="ollama",
        )
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_structured(
        self,
        prompt: str,
        response_schema: dict,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> dict:
        import json

        # Ollama는 JSON 모드로 요청
        enhanced_prompt = f"{prompt}\n\nJSON 형식으로 응답해주세요."

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": enhanced_prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)


def create_llm_client() -> BaseLLMClient:
    """설정에 따른 LLM 클라이언트 생성"""
    settings = get_settings()

    match settings.llm_provider:
        case LLMProvider.OPENAI:
            if not settings.openai_api_key:
                raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
            return OpenAIClient(settings.openai_api_key, settings.openai_model)

        case LLMProvider.ANTHROPIC:
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API 키가 설정되지 않았습니다.")
            return AnthropicClient(settings.anthropic_api_key, settings.anthropic_model)

        case LLMProvider.GOOGLE:
            # Google은 별도 구현 필요
            raise NotImplementedError("Google Gemini는 아직 구현되지 않았습니다.")

        case LLMProvider.OLLAMA:
            return OllamaClient(settings.ollama_url, settings.ollama_model)

        case _:
            raise ValueError(f"지원하지 않는 LLM 프로바이더: {settings.llm_provider}")


def create_llm_client_for_model(model_display_name: str) -> BaseLLMClient:
    """UI에서 선택한 모델명으로 LLM 클라이언트 생성"""
    settings = get_settings()
    provider, model_name = parse_model_selection(model_display_name)

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.\n설정에서 API 키를 입력해주세요.")
        return OpenAIClient(settings.openai_api_key, model_name)

    elif provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API 키가 설정되지 않았습니다.\n설정에서 API 키를 입력해주세요.")
        return AnthropicClient(settings.anthropic_api_key, model_name)

    else:
        raise ValueError(f"지원하지 않는 프로바이더: {provider}")
