"""템플릿 로더 모듈

템플릿 인덱스 및 개별 템플릿을 로드하고 관리합니다.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TemplateInfo:
    """템플릿 정보

    템플릿의 메타데이터를 담는 클래스입니다.
    """
    id: str
    name: str
    name_ko: str
    category: str
    description: str
    tags: List[str]
    thumbnail_path: str
    slides_count: int
    color_schemes: List[str]
    best_for: List[str]
    popularity: int
    created_at: str = ""
    updated_at: str = ""

    def matches_query(self, query: str) -> int:
        """검색어와의 매칭 점수 계산

        Args:
            query: 검색어

        Returns:
            매칭 점수 (0이면 매칭되지 않음)
        """
        query_lower = query.lower()
        score = 0

        # 이름 매칭
        if query_lower in self.name.lower():
            score += 10
        if query_lower in self.name_ko:
            score += 10

        # 태그 매칭
        for tag in self.tags:
            if query_lower in tag.lower():
                score += 5

        # 설명 매칭
        if query_lower in self.description.lower():
            score += 3

        # best_for 매칭
        for bf in self.best_for:
            if query_lower in bf:
                score += 7

        return score

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "name_ko": self.name_ko,
            "category": self.category,
            "description": self.description,
            "tags": self.tags,
            "thumbnail": self.thumbnail_path,
            "slides_count": self.slides_count,
            "color_schemes": self.color_schemes,
            "best_for": self.best_for,
            "popularity": self.popularity,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class CategoryInfo:
    """카테고리 정보"""
    id: str
    name: str
    name_ko: str
    icon: str
    description: str

    @classmethod
    def from_dict(cls, data: Dict) -> "CategoryInfo":
        """딕셔너리에서 생성"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            name_ko=data.get("name_ko", ""),
            icon=data.get("icon", ""),
            description=data.get("description", "")
        )


class TemplateLoader:
    """템플릿 로더

    템플릿 인덱스와 개별 템플릿 파일을 로드합니다.
    """

    def __init__(self, templates_dir: str = "templates"):
        """초기화

        Args:
            templates_dir: 템플릿 디렉토리 경로
        """
        self.templates_dir = Path(templates_dir)
        self._index: Optional[Dict] = None
        self._templates: Dict[str, Dict] = {}
        self._categories: List[CategoryInfo] = []

    def load_index(self) -> Dict:
        """템플릿 인덱스 로드

        Returns:
            인덱스 딕셔너리
        """
        if self._index is None:
            index_path = self.templates_dir / "index.json"
            if index_path.exists():
                with open(index_path, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
            else:
                self._index = {"templates": [], "categories": []}
        return self._index

    def list_templates(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "popularity"
    ) -> List[TemplateInfo]:
        """템플릿 목록 조회

        Args:
            category: 카테고리 필터 (None이면 전체)
            tags: 태그 필터 목록
            sort_by: 정렬 기준 (popularity, name, created_at)

        Returns:
            TemplateInfo 목록
        """
        index = self.load_index()
        templates = []

        for t in index.get("templates", []):
            # 카테고리 필터
            if category and t.get("category") != category:
                continue

            # 태그 필터
            if tags:
                template_tags = t.get("tags", [])
                if not any(tag in template_tags for tag in tags):
                    continue

            templates.append(TemplateInfo(
                id=t["id"],
                name=t["name"],
                name_ko=t.get("name_ko", t["name"]),
                category=t["category"],
                description=t.get("description", ""),
                tags=t.get("tags", []),
                thumbnail_path=t.get("thumbnail", ""),
                slides_count=t.get("slides_count", 10),
                color_schemes=t.get("color_schemes", []),
                best_for=t.get("best_for", []),
                popularity=t.get("popularity", 0),
                created_at=t.get("created_at", ""),
                updated_at=t.get("updated_at", "")
            ))

        # 정렬
        if sort_by == "popularity":
            templates.sort(key=lambda x: x.popularity, reverse=True)
        elif sort_by == "name":
            templates.sort(key=lambda x: x.name)
        elif sort_by == "created_at":
            templates.sort(key=lambda x: x.created_at, reverse=True)

        return templates

    def get_template(self, template_id: str) -> Optional[Dict]:
        """템플릿 상세 정보 로드

        Args:
            template_id: 템플릿 ID

        Returns:
            템플릿 정의 딕셔너리 또는 None
        """
        if template_id in self._templates:
            return self._templates[template_id]

        # 인덱스에서 템플릿 찾기
        index = self.load_index()
        template_meta = None
        for t in index.get("templates", []):
            if t["id"] == template_id:
                template_meta = t
                break

        if not template_meta:
            return None

        # 템플릿 정의 파일 로드
        category = template_meta["category"]
        template_path = self.templates_dir / category / template_id / "template.json"

        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                self._templates[template_id] = template_data
                return template_data

        return None

    def get_template_info(self, template_id: str) -> Optional[TemplateInfo]:
        """템플릿 정보 조회

        Args:
            template_id: 템플릿 ID

        Returns:
            TemplateInfo 또는 None
        """
        index = self.load_index()
        for t in index.get("templates", []):
            if t["id"] == template_id:
                return TemplateInfo(
                    id=t["id"],
                    name=t["name"],
                    name_ko=t.get("name_ko", t["name"]),
                    category=t["category"],
                    description=t.get("description", ""),
                    tags=t.get("tags", []),
                    thumbnail_path=t.get("thumbnail", ""),
                    slides_count=t.get("slides_count", 10),
                    color_schemes=t.get("color_schemes", []),
                    best_for=t.get("best_for", []),
                    popularity=t.get("popularity", 0),
                    created_at=t.get("created_at", ""),
                    updated_at=t.get("updated_at", "")
                )
        return None

    def get_categories(self) -> List[CategoryInfo]:
        """카테고리 목록 조회

        Returns:
            CategoryInfo 목록
        """
        if self._categories:
            return self._categories

        index = self.load_index()
        self._categories = [
            CategoryInfo.from_dict(c) for c in index.get("categories", [])
        ]
        return self._categories

    def get_category(self, category_id: str) -> Optional[CategoryInfo]:
        """특정 카테고리 조회

        Args:
            category_id: 카테고리 ID

        Returns:
            CategoryInfo 또는 None
        """
        categories = self.get_categories()
        for cat in categories:
            if cat.id == category_id:
                return cat
        return None

    def get_master_pptx_path(self, template_id: str) -> Optional[Path]:
        """마스터 PPTX 파일 경로

        Args:
            template_id: 템플릿 ID

        Returns:
            마스터 PPTX 경로 또는 None
        """
        template = self.get_template(template_id)
        if not template:
            return None

        category = template.get("metadata", {}).get("category", "")
        master_file = template.get("assets", {}).get("master_pptx", "master.pptx")

        path = self.templates_dir / category / template_id / master_file
        return path if path.exists() else None

    def get_thumbnail_path(self, template_id: str) -> Optional[Path]:
        """썸네일 이미지 경로

        Args:
            template_id: 템플릿 ID

        Returns:
            썸네일 경로 또는 None
        """
        info = self.get_template_info(template_id)
        if info and info.thumbnail_path:
            path = self.templates_dir / info.thumbnail_path
            return path if path.exists() else None
        return None

    def search_templates(
        self,
        query: str,
        limit: int = 10
    ) -> List[TemplateInfo]:
        """템플릿 검색

        Args:
            query: 검색어
            limit: 최대 결과 수

        Returns:
            검색 결과 TemplateInfo 목록
        """
        templates = self.list_templates()
        scored_templates = []

        for t in templates:
            score = t.matches_query(query)
            if score > 0:
                scored_templates.append((t, score))

        # 점수순 정렬
        scored_templates.sort(key=lambda x: x[1], reverse=True)

        return [t for t, _ in scored_templates[:limit]]

    def get_templates_by_purpose(self, purpose: str) -> List[TemplateInfo]:
        """목적에 맞는 템플릿 검색

        Args:
            purpose: 프레젠테이션 목적

        Returns:
            적합한 템플릿 목록
        """
        templates = self.list_templates()
        matched = []

        purpose_lower = purpose.lower()
        for t in templates:
            for bf in t.best_for:
                if purpose_lower in bf.lower():
                    matched.append(t)
                    break

        if not matched:
            # 폴백: 검색 결과 반환
            return self.search_templates(purpose)

        return matched

    def reload_index(self) -> None:
        """인덱스 다시 로드"""
        self._index = None
        self._templates.clear()
        self._categories.clear()
        self.load_index()

    def template_exists(self, template_id: str) -> bool:
        """템플릿 존재 여부 확인

        Args:
            template_id: 템플릿 ID

        Returns:
            존재하면 True
        """
        index = self.load_index()
        for t in index.get("templates", []):
            if t["id"] == template_id:
                return True
        return False

    def get_color_schemes_for_template(self, template_id: str) -> List[str]:
        """템플릿에서 사용 가능한 색상 스키마 목록

        Args:
            template_id: 템플릿 ID

        Returns:
            색상 스키마 이름 목록
        """
        template = self.get_template(template_id)
        if template:
            design = template.get("design", {})
            color_schemes = design.get("color_schemes", {})
            return list(color_schemes.keys())

        # 인덱스에서 색상 스키마 목록 가져오기
        info = self.get_template_info(template_id)
        if info:
            return info.color_schemes

        return []

    def get_recommended_slides(self, template_id: str) -> List[Dict]:
        """템플릿의 추천 슬라이드 구조

        Args:
            template_id: 템플릿 ID

        Returns:
            추천 슬라이드 목록
        """
        template = self.get_template(template_id)
        if template:
            structure = template.get("structure", {})
            return structure.get("recommended_slides", [])
        return []
