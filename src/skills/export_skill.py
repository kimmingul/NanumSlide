# src/skills/export_skill.py

from typing import Dict, Any, Optional
from pathlib import Path

from .base_skill import (
    BaseSkill, SkillMetadata, SkillCategory,
    SkillParameter, SkillInput, SkillOutput
)


class ExportSkill(BaseSkill):
    """내보내기 스킬 - 다양한 형식으로 내보내기"""

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="export",
            display_name="내보내기",
            description="프레젠테이션을 PPTX, PDF, 이미지 등 다양한 형식으로 내보냅니다.",
            category=SkillCategory.EXPORT,
            command="/export",
            parameters=[
                SkillParameter(
                    name="format",
                    type=str,
                    description="출력 형식",
                    required=False,
                    default="pptx",
                    choices=["pptx", "pdf", "png", "html"]
                ),
                SkillParameter(
                    name="output_path",
                    type=str,
                    description="출력 경로",
                    required=False
                ),
                SkillParameter(
                    name="quality",
                    type=str,
                    description="출력 품질",
                    required=False,
                    default="high",
                    choices=["low", "medium", "high"]
                ),
                SkillParameter(
                    name="include_notes",
                    type=bool,
                    description="발표자 노트 포함 여부",
                    required=False,
                    default=True
                ),
            ],
            examples=[
                '/export --format pptx',
                '/export --format pdf --output_path ./output/presentation.pdf',
                '/export --format png --quality high',
            ],
            requires=["outline"],
            produces=["exported_file"]
        )

    async def execute(self, input: SkillInput) -> SkillOutput:
        """내보내기 실행"""
        format = input.parameters.get("format", "pptx")
        output_path = input.parameters.get("output_path")
        quality = input.parameters.get("quality", "high")
        include_notes = input.parameters.get("include_notes", True)

        # 프레젠테이션 가져오기
        presentation = None
        if input.context:
            presentation = input.context.presentation

        if not presentation:
            return SkillOutput(
                success=False,
                data=None,
                error="내보낼 프레젠테이션이 없습니다"
            )

        # 출력 경로 결정
        if not output_path:
            output_path = self._generate_output_path(presentation, format)

        # 형식별 내보내기
        try:
            if format == "pptx":
                result = await self._export_pptx(
                    presentation, output_path, include_notes
                )
            elif format == "pdf":
                result = await self._export_pdf(
                    presentation, output_path, quality
                )
            elif format == "png":
                result = await self._export_images(
                    presentation, output_path, quality
                )
            elif format == "html":
                result = await self._export_html(
                    presentation, output_path
                )
            else:
                return SkillOutput(
                    success=False,
                    data=None,
                    error=f"지원하지 않는 형식: {format}"
                )

            return SkillOutput(
                success=True,
                data={
                    "format": format,
                    "output_path": result,
                    "file_size": self._get_file_size(result)
                },
                metadata={"quality": quality}
            )

        except Exception as e:
            return SkillOutput(
                success=False,
                data=None,
                error=str(e)
            )

    async def _export_pptx(
        self,
        presentation: Any,
        output_path: str,
        include_notes: bool
    ) -> str:
        """PPTX 내보내기"""
        from ..core.export.pptx_exporter import PptxExporter

        exporter = PptxExporter()
        exporter.export(presentation, output_path, include_notes=include_notes)

        return output_path

    async def _export_pdf(
        self,
        presentation: Any,
        output_path: str,
        quality: str
    ) -> str:
        """PDF 내보내기"""
        # PDF 내보내기 구현
        # 향후 PDF 내보내기 기능 추가 시 구현
        return output_path

    async def _export_images(
        self,
        presentation: Any,
        output_path: str,
        quality: str
    ) -> str:
        """이미지 내보내기"""
        # 이미지 내보내기 구현
        # 향후 이미지 내보내기 기능 추가 시 구현
        return output_path

    async def _export_html(
        self,
        presentation: Any,
        output_path: str
    ) -> str:
        """HTML 내보내기"""
        # HTML 내보내기 구현
        # 향후 HTML 내보내기 기능 추가 시 구현
        return output_path

    def _generate_output_path(self, presentation: Any, format: str) -> str:
        """출력 경로 생성"""
        title = getattr(presentation, 'title', 'presentation')
        if isinstance(presentation, dict):
            title = presentation.get('title', 'presentation')
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        return f"./output/{safe_title}.{format}"

    def _get_file_size(self, path: str) -> int:
        """파일 크기 조회"""
        try:
            return Path(path).stat().st_size
        except:
            return 0
