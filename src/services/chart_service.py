"""Chart Service for NanumSlide.

Provides chart generation functionality for presentations,
supporting various chart types and data visualization needs.
"""

import base64
import io
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple, Union

import structlog

logger = structlog.get_logger(__name__)


class ChartType(Enum):
    """Supported chart types."""
    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    FUNNEL = "funnel"
    GAUGE = "gauge"


@dataclass
class ChartDataSeries:
    """A data series for a chart."""
    name: str
    values: List[Union[int, float]]
    color: Optional[str] = None


@dataclass
class ChartData:
    """Data structure for chart generation."""
    labels: List[str]
    series: List[ChartDataSeries]
    title: Optional[str] = None
    subtitle: Optional[str] = None
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None


@dataclass
class ChartStyle:
    """Style configuration for charts."""
    colors: List[str] = field(default_factory=lambda: [
        "#3498db", "#e74c3c", "#2ecc71", "#f39c12",
        "#9b59b6", "#1abc9c", "#e67e22", "#34495e"
    ])
    background_color: str = "transparent"
    font_family: str = "Pretendard, sans-serif"
    font_size: int = 12
    title_font_size: int = 16
    show_legend: bool = True
    show_grid: bool = True
    animation: bool = False
    border_radius: int = 0


@dataclass
class ChartOutput:
    """Output from chart generation."""
    image_data: bytes
    format: str = "png"
    width: int = 800
    height: int = 600
    chart_type: ChartType = ChartType.BAR
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_base64(self) -> str:
        """Convert image data to base64 string."""
        return base64.b64encode(self.image_data).decode("utf-8")

    def to_data_uri(self) -> str:
        """Convert to data URI for embedding."""
        b64 = self.to_base64()
        return f"data:image/{self.format};base64,{b64}"


class ChartService:
    """Service for generating charts."""

    def __init__(self, default_style: Optional[ChartStyle] = None):
        self.default_style = default_style or ChartStyle()
        self._matplotlib_available = self._check_matplotlib()

    def _check_matplotlib(self) -> bool:
        """Check if matplotlib is available."""
        try:
            import matplotlib
            matplotlib.use("Agg")  # Use non-interactive backend
            return True
        except ImportError:
            logger.warning("matplotlib not available, chart generation limited")
            return False

    def generate_chart(
        self,
        chart_type: ChartType,
        data: ChartData,
        style: Optional[ChartStyle] = None,
        width: int = 800,
        height: int = 600,
        format: str = "png"
    ) -> Optional[ChartOutput]:
        """Generate a chart image."""
        if not self._matplotlib_available:
            logger.error("matplotlib required for chart generation")
            return None

        style = style or self.default_style

        try:
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
            import numpy as np

            # Create figure
            fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)

            if style.background_color != "transparent":
                fig.patch.set_facecolor(style.background_color)
                ax.set_facecolor(style.background_color)
            else:
                fig.patch.set_alpha(0)
                ax.set_facecolor("none")

            # Generate chart based on type
            if chart_type == ChartType.BAR:
                self._draw_bar_chart(ax, data, style)
            elif chart_type == ChartType.HORIZONTAL_BAR:
                self._draw_horizontal_bar_chart(ax, data, style)
            elif chart_type == ChartType.LINE:
                self._draw_line_chart(ax, data, style)
            elif chart_type == ChartType.PIE:
                self._draw_pie_chart(ax, data, style)
            elif chart_type == ChartType.DONUT:
                self._draw_donut_chart(ax, data, style)
            elif chart_type == ChartType.AREA:
                self._draw_area_chart(ax, data, style)
            elif chart_type == ChartType.SCATTER:
                self._draw_scatter_chart(ax, data, style)
            elif chart_type == ChartType.RADAR:
                self._draw_radar_chart(fig, data, style)
            else:
                self._draw_bar_chart(ax, data, style)

            # Add title
            if data.title:
                ax.set_title(
                    data.title,
                    fontsize=style.title_font_size,
                    fontweight="bold",
                    pad=20
                )

            # Add axis labels
            if data.x_axis_label and chart_type not in [ChartType.PIE, ChartType.DONUT, ChartType.RADAR]:
                ax.set_xlabel(data.x_axis_label, fontsize=style.font_size)
            if data.y_axis_label and chart_type not in [ChartType.PIE, ChartType.DONUT, ChartType.RADAR]:
                ax.set_ylabel(data.y_axis_label, fontsize=style.font_size)

            # Grid
            if style.show_grid and chart_type not in [ChartType.PIE, ChartType.DONUT, ChartType.RADAR]:
                ax.grid(True, alpha=0.3, linestyle="--")

            # Legend
            if style.show_legend and len(data.series) > 1:
                ax.legend(loc="best", framealpha=0.9)

            plt.tight_layout()

            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(
                buf,
                format=format,
                dpi=100,
                bbox_inches="tight",
                transparent=(style.background_color == "transparent")
            )
            buf.seek(0)
            image_data = buf.read()
            plt.close(fig)

            return ChartOutput(
                image_data=image_data,
                format=format,
                width=width,
                height=height,
                chart_type=chart_type,
                metadata={"title": data.title}
            )

        except Exception as e:
            logger.error("Chart generation failed", error=str(e), chart_type=chart_type.value)
            return None

    def _draw_bar_chart(self, ax, data: ChartData, style: ChartStyle):
        import numpy as np
        x = np.arange(len(data.labels))
        width = 0.8 / len(data.series)

        for i, series in enumerate(data.series):
            color = series.color or style.colors[i % len(style.colors)]
            offset = (i - len(data.series) / 2 + 0.5) * width
            ax.bar(x + offset, series.values, width, label=series.name, color=color)

        ax.set_xticks(x)
        ax.set_xticklabels(data.labels, fontsize=style.font_size)

    def _draw_horizontal_bar_chart(self, ax, data: ChartData, style: ChartStyle):
        import numpy as np
        y = np.arange(len(data.labels))
        height = 0.8 / len(data.series)

        for i, series in enumerate(data.series):
            color = series.color or style.colors[i % len(style.colors)]
            offset = (i - len(data.series) / 2 + 0.5) * height
            ax.barh(y + offset, series.values, height, label=series.name, color=color)

        ax.set_yticks(y)
        ax.set_yticklabels(data.labels, fontsize=style.font_size)

    def _draw_line_chart(self, ax, data: ChartData, style: ChartStyle):
        for i, series in enumerate(data.series):
            color = series.color or style.colors[i % len(style.colors)]
            ax.plot(data.labels, series.values, marker="o", label=series.name, color=color)

        ax.tick_params(axis="x", rotation=45)

    def _draw_area_chart(self, ax, data: ChartData, style: ChartStyle):
        import numpy as np
        x = np.arange(len(data.labels))

        for i, series in enumerate(data.series):
            color = series.color or style.colors[i % len(style.colors)]
            ax.fill_between(x, series.values, alpha=0.4, color=color, label=series.name)
            ax.plot(x, series.values, color=color)

        ax.set_xticks(x)
        ax.set_xticklabels(data.labels, fontsize=style.font_size)

    def _draw_pie_chart(self, ax, data: ChartData, style: ChartStyle):
        if data.series:
            values = data.series[0].values
            colors = [style.colors[i % len(style.colors)] for i in range(len(values))]
            ax.pie(
                values,
                labels=data.labels,
                colors=colors,
                autopct="%1.1f%%",
                startangle=90
            )
            ax.axis("equal")

    def _draw_donut_chart(self, ax, data: ChartData, style: ChartStyle):
        if data.series:
            values = data.series[0].values
            colors = [style.colors[i % len(style.colors)] for i in range(len(values))]
            wedges, texts, autotexts = ax.pie(
                values,
                labels=data.labels,
                colors=colors,
                autopct="%1.1f%%",
                startangle=90,
                wedgeprops={"width": 0.5}
            )
            ax.axis("equal")

    def _draw_scatter_chart(self, ax, data: ChartData, style: ChartStyle):
        for i, series in enumerate(data.series):
            color = series.color or style.colors[i % len(style.colors)]
            # Assuming values are [x, y] pairs or using index as x
            if len(series.values) > 0:
                x_vals = list(range(len(series.values)))
                ax.scatter(x_vals, series.values, label=series.name, color=color, s=50)

    def _draw_radar_chart(self, fig, data: ChartData, style: ChartStyle):
        import numpy as np

        # Clear current axes and create polar projection
        fig.clear()
        ax = fig.add_subplot(111, polar=True)

        num_vars = len(data.labels)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]  # Complete the loop

        for i, series in enumerate(data.series):
            color = series.color or style.colors[i % len(style.colors)]
            values = series.values + series.values[:1]  # Complete the loop
            ax.plot(angles, values, "o-", linewidth=2, label=series.name, color=color)
            ax.fill(angles, values, alpha=0.25, color=color)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(data.labels, fontsize=style.font_size)

        if style.show_legend and len(data.series) > 1:
            ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))


def generate_chart(
    chart_type: Union[ChartType, str],
    labels: List[str],
    values: List[Union[int, float]],
    series_name: str = "Data",
    title: Optional[str] = None,
    **kwargs
) -> Optional[ChartOutput]:
    """Convenience function to generate a simple chart."""
    if isinstance(chart_type, str):
        chart_type = ChartType(chart_type)

    data = ChartData(
        labels=labels,
        series=[ChartDataSeries(name=series_name, values=values)],
        title=title
    )

    service = ChartService()
    return service.generate_chart(chart_type, data, **kwargs)


def generate_comparison_chart(
    labels: List[str],
    datasets: Dict[str, List[Union[int, float]]],
    chart_type: ChartType = ChartType.BAR,
    title: Optional[str] = None,
    **kwargs
) -> Optional[ChartOutput]:
    """Generate a comparison chart with multiple data series."""
    series = [
        ChartDataSeries(name=name, values=values)
        for name, values in datasets.items()
    ]

    data = ChartData(labels=labels, series=series, title=title)
    service = ChartService()
    return service.generate_chart(chart_type, data, **kwargs)
