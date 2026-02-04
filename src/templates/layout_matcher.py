"""레이아웃 매칭 모듈

슬라이드 콘텐츠를 분석하여 최적의 레이아웃을 선택합니다.
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass

from .layout_types import Layout, LayoutType, LayoutCategory, DEFAULT_LAYOUTS

if TYPE_CHECKING:
    from ..core.presentation import Slide


@dataclass
class ContentAnalysis:
    """콘텐츠 분석 결과

    슬라이드 콘텐츠의 특성을 분석한 결과를 담습니다.
    """
    has_title: bool
    has_subtitle: bool
    has_body_text: bool
    has_bullet_points: bool
    bullet_count: int
    has_image: bool
    has_chart: bool
    has_quote: bool
    text_length: int
    is_comparison: bool
    is_timeline: bool
    word_count: int = 0
    has_statistics: bool = False
    is_team_content: bool = False
    is_contact_content: bool = False

    @property
    def is_text_heavy(self) -> bool:
        """텍스트가 많은지 확인"""
        return self.text_length > 300 or self.word_count > 50

    @property
    def is_bullet_heavy(self) -> bool:
        """글머리 기호가 많은지 확인"""
        return self.bullet_count > 4

    @property
    def needs_visual_balance(self) -> bool:
        """시각적 균형이 필요한지 확인"""
        return self.has_image or self.has_chart

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "has_title": self.has_title,
            "has_subtitle": self.has_subtitle,
            "has_body_text": self.has_body_text,
            "has_bullet_points": self.has_bullet_points,
            "bullet_count": self.bullet_count,
            "has_image": self.has_image,
            "has_chart": self.has_chart,
            "has_quote": self.has_quote,
            "text_length": self.text_length,
            "is_comparison": self.is_comparison,
            "is_timeline": self.is_timeline,
            "word_count": self.word_count,
            "has_statistics": self.has_statistics,
            "is_team_content": self.is_team_content,
            "is_contact_content": self.is_contact_content
        }


class LayoutMatcher:
    """콘텐츠에 최적화된 레이아웃 매칭

    슬라이드 콘텐츠를 분석하고 가장 적합한 레이아웃을 선택합니다.
    """

    def __init__(self, layouts: Optional[Dict[str, Layout]] = None):
        """초기화

        Args:
            layouts: 사용 가능한 레이아웃 딕셔너리
        """
        self.layouts = layouts or {}
        self._layout_cache: Dict[str, LayoutType] = {}

    def match(
        self,
        content: Any,
        slide_index: int,
        total_slides: int,
        previous_layout: Optional[LayoutType] = None
    ) -> LayoutType:
        """콘텐츠에 맞는 레이아웃 선택

        Args:
            content: 슬라이드 콘텐츠 (SlideContent 또는 Slide)
            slide_index: 슬라이드 인덱스 (0부터 시작)
            total_slides: 전체 슬라이드 수
            previous_layout: 이전 슬라이드의 레이아웃

        Returns:
            선택된 레이아웃 타입
        """
        # 콘텐츠 분석
        analysis = self._analyze_content(content)

        # 슬라이드 위치에 따른 특수 처리
        if slide_index == 0:
            return self._match_title_slide(analysis)

        if slide_index == total_slides - 1:
            return self._match_ending_slide(analysis)

        # 콘텐츠 기반 매칭
        matched = self._match_by_content(analysis)

        # 다양성 확보 (연속 동일 레이아웃 방지)
        if matched == previous_layout:
            matched = self._get_alternative(matched, analysis)

        return matched

    def _analyze_content(self, content: Any) -> ContentAnalysis:
        """콘텐츠 분석

        Args:
            content: 분석할 콘텐츠

        Returns:
            ContentAnalysis 객체
        """
        # 콘텐츠 속성 추출 (다양한 객체 타입 지원)
        title = getattr(content, 'title', '') or ''
        subtitle = getattr(content, 'subtitle', '') or ''
        body_content = getattr(content, 'content', '') or ''
        bullet_points = getattr(content, 'bullet_points', []) or []
        image_url = getattr(content, 'image_url', None)
        chart_data = getattr(content, 'chart_data', None)

        # 텍스트 분석
        full_text = f"{title} {subtitle} {body_content}"
        word_count = len(full_text.split())

        return ContentAnalysis(
            has_title=bool(title),
            has_subtitle=bool(subtitle),
            has_body_text=bool(body_content),
            has_bullet_points=len(bullet_points) > 0,
            bullet_count=len(bullet_points),
            has_image=bool(image_url),
            has_chart=bool(chart_data),
            has_quote=self._is_quote(body_content),
            text_length=len(body_content) if body_content else 0,
            is_comparison=self._is_comparison(title, body_content),
            is_timeline=self._is_timeline(title, body_content),
            word_count=word_count,
            has_statistics=self._has_statistics(body_content, bullet_points),
            is_team_content=self._is_team_content(title),
            is_contact_content=self._is_contact_content(title)
        )

    def _match_title_slide(self, analysis: ContentAnalysis) -> LayoutType:
        """제목 슬라이드 레이아웃 선택

        Args:
            analysis: 콘텐츠 분석 결과

        Returns:
            레이아웃 타입
        """
        if analysis.has_image:
            return LayoutType.TITLE_IMAGE_BG
        if analysis.has_subtitle:
            return LayoutType.TITLE_WITH_SUBTITLE
        return LayoutType.TITLE_CENTERED

    def _match_ending_slide(self, analysis: ContentAnalysis) -> LayoutType:
        """마지막 슬라이드 레이아웃 선택

        Args:
            analysis: 콘텐츠 분석 결과

        Returns:
            레이아웃 타입
        """
        if analysis.has_quote:
            return LayoutType.QUOTE
        if analysis.is_contact_content:
            return LayoutType.CONTACT
        return LayoutType.CONTACT

    def _match_by_content(self, analysis: ContentAnalysis) -> LayoutType:
        """콘텐츠 기반 레이아웃 선택

        Args:
            analysis: 콘텐츠 분석 결과

        Returns:
            레이아웃 타입
        """
        # 팀 소개 콘텐츠
        if analysis.is_team_content:
            return LayoutType.TEAM_GRID

        # 차트가 있는 경우
        if analysis.has_chart:
            return LayoutType.CHART_CENTERED

        # 인용문인 경우
        if analysis.has_quote:
            return LayoutType.QUOTE

        # 비교 콘텐츠
        if analysis.is_comparison:
            return LayoutType.COMPARISON

        # 타임라인
        if analysis.is_timeline:
            return LayoutType.TIMELINE

        # 통계 데이터
        if analysis.has_statistics:
            return LayoutType.STATISTICS

        # 이미지가 있는 경우
        if analysis.has_image:
            if analysis.text_length > 200:
                return LayoutType.IMAGE_LEFT
            else:
                return LayoutType.IMAGE_FULL

        # 글머리 기호가 많은 경우
        if analysis.bullet_count > 4:
            return LayoutType.TWO_COLUMN

        # 글머리 기호가 있는 경우
        if analysis.has_bullet_points:
            return LayoutType.BULLET_POINTS

        # 긴 텍스트
        if analysis.text_length > 300:
            return LayoutType.TWO_COLUMN

        # 기본
        return LayoutType.SINGLE_COLUMN

    def _get_alternative(
        self,
        current: LayoutType,
        analysis: ContentAnalysis
    ) -> LayoutType:
        """대체 레이아웃 선택

        연속으로 동일한 레이아웃이 선택되지 않도록 대안을 제공합니다.

        Args:
            current: 현재 선택된 레이아웃
            analysis: 콘텐츠 분석 결과

        Returns:
            대체 레이아웃 타입
        """
        alternatives = {
            LayoutType.SINGLE_COLUMN: LayoutType.BULLET_POINTS,
            LayoutType.BULLET_POINTS: LayoutType.SINGLE_COLUMN,
            LayoutType.TWO_COLUMN: LayoutType.IMAGE_RIGHT,
            LayoutType.IMAGE_LEFT: LayoutType.IMAGE_RIGHT,
            LayoutType.IMAGE_RIGHT: LayoutType.IMAGE_LEFT,
            LayoutType.CHART_CENTERED: LayoutType.STATISTICS,
            LayoutType.STATISTICS: LayoutType.CHART_CENTERED,
        }
        return alternatives.get(current, current)

    def _is_quote(self, text: Optional[str]) -> bool:
        """인용문 여부 확인

        Args:
            text: 확인할 텍스트

        Returns:
            인용문이면 True
        """
        if not text:
            return False
        text_stripped = text.strip()
        quote_markers = ['"', '"', '"', '「', '『', "'"]
        return any(text_stripped.startswith(marker) for marker in quote_markers) or '명언' in text

    def _is_comparison(self, title: str, content: str) -> bool:
        """비교 콘텐츠 여부 확인

        Args:
            title: 제목
            content: 본문 내용

        Returns:
            비교 콘텐츠면 True
        """
        keywords = ['vs', 'VS', '비교', '차이', '대비', 'before', 'after', '장단점', '비용 비교']
        combined = (title or '') + ' ' + (content or '')
        return any(kw in combined for kw in keywords)

    def _is_timeline(self, title: str, content: str) -> bool:
        """타임라인 콘텐츠 여부 확인

        Args:
            title: 제목
            content: 본문 내용

        Returns:
            타임라인 콘텐츠면 True
        """
        keywords = ['연혁', '역사', '단계', 'step', '과정', '타임라인', 'timeline', '로드맵', 'roadmap']
        combined = ((title or '') + ' ' + (content or '')).lower()
        return any(kw.lower() in combined for kw in keywords)

    def _has_statistics(self, content: str, bullet_points: List[str]) -> bool:
        """통계 데이터 여부 확인

        Args:
            content: 본문 내용
            bullet_points: 글머리 기호 목록

        Returns:
            통계 데이터가 있으면 True
        """
        # 숫자와 퍼센트 패턴 확인
        import re
        stat_pattern = r'\d+(?:\.\d+)?(?:%|명|개|원|달러|\$|억|만)'
        combined = (content or '') + ' '.join(bullet_points or [])
        matches = re.findall(stat_pattern, combined)
        return len(matches) >= 2

    def _is_team_content(self, title: str) -> bool:
        """팀 소개 콘텐츠 여부 확인

        Args:
            title: 제목

        Returns:
            팀 소개 콘텐츠면 True
        """
        keywords = ['팀', 'team', '구성원', '멤버', 'member', '조직', '인력', '담당자']
        title_lower = (title or '').lower()
        return any(kw.lower() in title_lower for kw in keywords)

    def _is_contact_content(self, title: str) -> bool:
        """연락처 콘텐츠 여부 확인

        Args:
            title: 제목

        Returns:
            연락처 콘텐츠면 True
        """
        keywords = ['연락처', 'contact', '문의', 'q&a', '감사', 'thank', '마무리', '끝']
        title_lower = (title or '').lower()
        return any(kw.lower() in title_lower for kw in keywords)

    def get_layout(self, layout_type: LayoutType) -> Layout:
        """레이아웃 정의 조회

        Args:
            layout_type: 레이아웃 타입

        Returns:
            Layout 객체
        """
        layout_id = layout_type.value

        # 캐시된 레이아웃 확인
        if layout_id in self.layouts:
            return self.layouts[layout_id]

        # 기본 레이아웃에서 조회
        if layout_type in DEFAULT_LAYOUTS:
            return DEFAULT_LAYOUTS[layout_type]

        # 기본 단일 열 레이아웃 반환
        return DEFAULT_LAYOUTS[LayoutType.SINGLE_COLUMN]

    def analyze_presentation(
        self,
        slides: List[Any]
    ) -> List[ContentAnalysis]:
        """전체 프레젠테이션 분석

        Args:
            slides: 슬라이드 목록

        Returns:
            각 슬라이드의 ContentAnalysis 목록
        """
        return [self._analyze_content(slide) for slide in slides]

    def suggest_layouts(
        self,
        slides: List[Any],
        ensure_variety: bool = True
    ) -> List[LayoutType]:
        """전체 프레젠테이션의 레이아웃 제안

        Args:
            slides: 슬라이드 목록
            ensure_variety: 다양성 보장 여부

        Returns:
            각 슬라이드의 추천 레이아웃 목록
        """
        suggested = []
        total = len(slides)

        for i, slide in enumerate(slides):
            previous = suggested[-1] if suggested else None
            layout = self.match(slide, i, total, previous)

            # 다양성 확보: 3개 연속 동일 레이아웃 방지
            if ensure_variety and len(suggested) >= 2:
                if suggested[-1] == suggested[-2] == layout:
                    analysis = self._analyze_content(slide)
                    layout = self._get_alternative(layout, analysis)

            suggested.append(layout)

        return suggested


def create_layout_matcher(custom_layouts: Optional[Dict[str, Layout]] = None) -> LayoutMatcher:
    """레이아웃 매처 생성

    Args:
        custom_layouts: 사용자 정의 레이아웃

    Returns:
        LayoutMatcher 인스턴스
    """
    layouts = dict(DEFAULT_LAYOUTS)
    if custom_layouts:
        layouts.update(custom_layouts)

    return LayoutMatcher(layouts)
