# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L18826-L18888 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #92  lines=62  compile=FAIL:63:unterminated string literal (detected at line 63
# kind: module  ident: agent/llm_boundary.py  version: 3/5
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.1
模块：agent/llm_boundary.py
职责：严格纯 JSON 边界防御校验器 (Strict JSON Boundary Validator)。
彻底切除字符串切片提取，严格要求整体为单一合法 JSON Object，
拦截重复键 (Duplicate Keys)、非对象标量/数组、未知字段 (extra='forbid') 与模型幻觉。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cmawse.agent.affordance import CandidateAffordance
from cmawse.agent.deliberation import CognitiveSilentMode, MindDecision, MindDecisionStatus


class RawLLMOutputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: MindDecisionStatus
    candidate_id: Optional[str] = None
    silent_mode: Optional[CognitiveSilentMode] = None
    reason: Optional[str] = Field(default=None)


class BoundaryValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    is_valid: bool
    decision: MindDecision
    rejection_reason: Optional[str] = None


def _strict_no_duplicate_keys_hook(pairs: List[tuple[str, Any]]) -> Dict[str, Any]:
    """检测 JSON 字典中是否存在重复键攻击"""
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key detected: '{key}'")
        result[key] = value
    return result


class LLMBoundaryValidator:
    """大模型认知边界严格防御校验器"""

    @classmethod
    def validate_and_sanitize(
        cls,
        raw_response: str | Dict[str, Any],
        valid_candidates: List[CandidateAffordance],
        expected_candidate_set_hash: Optional[str] = None
    ) -> BoundaryValidationResult:
        valid_channel_ids: Set[str] = {c.channel_id for c in valid_candidates}

        # 1. 严格纯 JSON 格式解析（严禁 index("{") 字符串截取，必须整体自洽）
        try:
            if isinstance(raw_response, str):
                cleaned_str = raw_response.strip()
                # 拒止任何带 Markdown 标记或前后包装文本的内容
                if cleaned_str.startswith("