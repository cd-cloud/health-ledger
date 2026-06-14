from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class LLMProvider(ABC):
    """LLM 提供商抽象，支持后续切换 OpenAI、Kimi、本地模型等。"""

    @abstractmethod
    def extract_biomarkers(
        self,
        report_text: str,
        biomarker_dictionary: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        从体检报告文本中提取结构化指标。

        返回列表，每个元素包含：
        - original_name: str
        - original_value: str
        - original_unit: str
        - confidence: float (0-1)
        """
        raise NotImplementedError

    @abstractmethod
    def analyze_trend(
        self,
        biomarker_name: str,
        unit: str,
        reference_low: Optional[float],
        reference_high: Optional[float],
        trend_points: List[Dict[str, Any]],
    ) -> str:
        """
        基于指标历史趋势生成 AI 分析摘要。

        trend_points 每个元素包含：report_date, value, status。
        返回字符串，必须在外层附加医疗免责声明。
        """
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """检查当前 provider 是否配置完整可用。"""
        raise NotImplementedError
