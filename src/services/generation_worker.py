"""AI 생성 작업 워커 (백그라운드 스레드)"""

import asyncio
from typing import Optional

from PySide6.QtCore import QThread, Signal

from src.core.presentation import Presentation
from src.services.presentation_generator import PresentationGenerator
from src.services.llm_client import create_llm_client_for_model


class GenerationWorker(QThread):
    """프레젠테이션 생성 워커 스레드"""

    # 시그널 정의
    progress = Signal(str, int)  # (메시지, 퍼센트)
    finished = Signal(object)    # Presentation 객체
    error = Signal(str)          # 에러 메시지

    def __init__(
        self,
        prompt: str,
        slide_count: int = 8,
        language: str = "한국어",
        template: str = "기본",
        model: str = "GPT-4o",
        reference_content: str = "",
    ):
        super().__init__()
        self.prompt = prompt
        self.slide_count = slide_count
        self.language = language
        self.template = template
        self.model = model
        self.reference_content = reference_content
        self._is_cancelled = False

    def cancel(self):
        """생성 취소"""
        self._is_cancelled = True

    def run(self):
        """워커 실행"""
        try:
            # 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 프레젠테이션 생성
                presentation = loop.run_until_complete(self._generate())

                if not self._is_cancelled:
                    self.finished.emit(presentation)
            finally:
                loop.close()

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))

    async def _generate(self) -> Presentation:
        """프레젠테이션 생성 (비동기)"""
        try:
            # UI에서 선택한 모델로 클라이언트 생성
            llm_client = create_llm_client_for_model(self.model)
            generator = PresentationGenerator(llm_client)

            # 진행률 콜백 설정
            def on_progress(message: str, percent: int):
                if not self._is_cancelled:
                    self.progress.emit(message, percent)

            generator.set_progress_callback(on_progress)

            # 생성 실행
            presentation = await generator.generate(
                topic=self.prompt,
                slide_count=self.slide_count,
                language=self.language,
                template=self.template,
                reference_content=self.reference_content,
            )

            return presentation

        except Exception as e:
            raise Exception(f"프레젠테이션 생성 실패: {e}")


class MockGenerationWorker(QThread):
    """테스트용 목업 생성 워커 (API 없이 테스트)"""

    progress = Signal(str, int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        prompt: str,
        slide_count: int = 8,
        language: str = "한국어",
        template: str = "기본",
        model: str = "GPT-4o",
    ):
        super().__init__()
        self.prompt = prompt
        self.slide_count = slide_count
        self.language = language
        self.template = template
        self.model = model
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        """목업 데이터 생성"""
        import time
        from src.core.presentation import Presentation, Slide, SlideLayoutType
        import uuid

        try:
            # 진행률 시뮬레이션
            self.progress.emit("개요 생성 중...", 10)
            time.sleep(0.5)

            if self._is_cancelled:
                return

            self.progress.emit("슬라이드 구성 중...", 30)
            time.sleep(0.5)

            # 목업 프레젠테이션 생성
            presentation = Presentation(
                id=str(uuid.uuid4()),
                title=self.prompt,
                language=self.language,
                prompt=self.prompt,
            )

            # 슬라이드 생성
            slides_data = [
                {
                    "title": self.prompt,
                    "layout": SlideLayoutType.TITLE,
                    "subtitle": f"생성일: {time.strftime('%Y-%m-%d')}",
                    "content": "",
                },
                {
                    "title": "목차",
                    "layout": SlideLayoutType.BULLET_POINTS,
                    "bullet_points": ["소개", "주요 내용", "세부 사항", "결론"],
                },
                {
                    "title": "소개",
                    "layout": SlideLayoutType.TITLE_CONTENT,
                    "content": f"{self.prompt}에 대한 소개입니다. 이 프레젠테이션에서는 주요 개념과 핵심 내용을 다룹니다.",
                },
                {
                    "title": "주요 내용",
                    "layout": SlideLayoutType.BULLET_POINTS,
                    "bullet_points": [
                        "첫 번째 핵심 포인트",
                        "두 번째 핵심 포인트",
                        "세 번째 핵심 포인트",
                    ],
                },
                {
                    "title": "세부 사항",
                    "layout": SlideLayoutType.TITLE_CONTENT,
                    "content": "여기에 더 자세한 내용이 들어갑니다. 구체적인 예시와 데이터를 포함할 수 있습니다.",
                },
                {
                    "title": "결론",
                    "layout": SlideLayoutType.BULLET_POINTS,
                    "bullet_points": [
                        "핵심 내용 요약",
                        "향후 계획",
                        "Q&A",
                    ],
                },
                {
                    "title": "감사합니다",
                    "layout": SlideLayoutType.TITLE,
                    "subtitle": "질문이 있으시면 말씀해 주세요",
                },
            ]

            for i, data in enumerate(slides_data[: self.slide_count]):
                if self._is_cancelled:
                    return

                progress = 30 + int((i + 1) / min(len(slides_data), self.slide_count) * 60)
                self.progress.emit(f"슬라이드 {i + 1} 생성 중...", progress)
                time.sleep(0.3)

                slide = Slide(
                    id=f"slide_{i + 1}",
                    title=data.get("title", ""),
                    layout=data.get("layout", SlideLayoutType.TITLE_CONTENT),
                    subtitle=data.get("subtitle", ""),
                    content=data.get("content", ""),
                    bullet_points=data.get("bullet_points", []),
                )
                presentation.add_slide(slide)

            self.progress.emit("완료", 100)
            time.sleep(0.2)

            if not self._is_cancelled:
                self.finished.emit(presentation)

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))
