import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import KIMI_API_KEY, KIMI_BASE_URL, KIMI_MODEL
from app.services.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


class KimiProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or KIMI_API_KEY
        self.base_url = (base_url or KIMI_BASE_URL).rstrip("/")
        self.model = model or KIMI_MODEL

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _chat(self, messages: List[Dict[str, str]], temperature: float = 0.0) -> str:
        if not self.is_available():
            raise RuntimeError("Kimi API key not configured")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.exception("Kimi API call failed")
            raise RuntimeError(f"Kimi API call failed: {exc}") from exc

    def extract_biomarkers(
        self,
        report_text: str,
        biomarker_dictionary: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        dict_text = json.dumps(biomarker_dictionary, ensure_ascii=False, indent=2)
        system_prompt = (
            "你是一名医学信息提取助手。请从体检报告文本中提取指标，并严格按 JSON 数组返回。"
            "每个元素字段：original_name（原文名称）、original_value（数值字符串）、"
            "original_unit（原文单位）、confidence（0-1 置信度）。"
            "只返回 JSON，不要其他解释。"
        )
        user_prompt = (
            f"可用指标标准库：\n{dict_text}\n\n"
            f"体检报告文本：\n{report_text[:12000]}\n\n"
            "请提取所有匹配指标标准库的体检指标。"
        )
        content = self._chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        return self._parse_json_array(content)

    def analyze_trend(
        self,
        biomarker_name: str,
        unit: str,
        reference_low: Optional[float],
        reference_high: Optional[float],
        trend_points: List[Dict[str, Any]],
    ) -> str:
        ref_text = ""
        if reference_low is not None and reference_high is not None:
            ref_text = f"参考范围：{reference_low}-{reference_high} {unit}。"
        elif reference_high is not None:
            ref_text = f"参考上限：{reference_high} {unit}。"
        elif reference_low is not None:
            ref_text = f"参考下限：{reference_low} {unit}。"

        points_text = "\n".join(
            f"- {p['report_date']}: {p['value']} {unit} (状态：{p.get('status', '未知')})"
            for p in trend_points
        )

        system_prompt = (
            "你是一名健康数据分析助手。请基于用户体检指标历史数据，给出趋势描述和可能的健康提示。"
            "要求：1）只描述数据变化趋势；2）不给出确诊；3）建议咨询专业医生。"
            "回答控制在 300 字以内。"
        )
        user_prompt = (
            f"指标：{biomarker_name}\n"
            f"单位：{unit}\n"
            f"{ref_text}\n"
            f"历史数据：\n{points_text}\n\n"
            "请总结趋势并给出健康关注建议。"
        )
        return self._chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

    @staticmethod
    def _parse_json_array(content: str) -> List[Dict[str, Any]]:
        text = content.strip()
        if text.startswith("```"):
            # remove markdown code fence
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "biomarkers" in data:
                return data["biomarkers"]
            return []
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON: %s", text[:200])
            return []
