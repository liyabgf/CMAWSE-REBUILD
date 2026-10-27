# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L21193-L21276 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #102  lines=83  compile=FAIL:84:unterminated string literal (detected at line 84
# kind: module  ident: agent/llm_boundary.py  version: 5/5
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.1.2
模块：agent/llm_boundary.py
职责：实现严格的纯 JSON 边界防御、TOCTOU 快照身份断言与重复 channel_id 拒止。
清理冗余 catch-all 异常捕获，禁止伪造任何 reason 字符串。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cmawse.agent.affordance import CandidateAffordance
from cmawse.agent.cognitive_projection import CognitiveProjection, ProjectedCandidateDTO
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
        valid_candidates: List[CandidateAffordance] | List[ProjectedCandidateDTO] | Tuple[ProjectedCandidateDTO, ...],
        expected_candidate_set_hash: Optional[str] = None
    ) -> BoundaryValidationResult:
        # 1. 候选快照身份与重复 channel_id 核验
        try:
            actual_snapshot_hash = CognitiveProjection.compute_candidate_snapshot_hash(valid_candidates)
        except ValueError as err:
            return BoundaryValidationResult(
                is_valid=False,
                decision=MindDecision(
                    status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                    telemetry_reason=f"Candidate snapshot contains duplicates: {str(err)}"
                ),
                rejection_reason="DUPLICATE_CHANNEL_ID_IN_SNAPSHOT"
            )

        if expected_candidate_set_hash is not None and actual_snapshot_hash != expected_candidate_set_hash:
            return BoundaryValidationResult(
                is_valid=False,
                decision=MindDecision(
                    status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                    telemetry_reason=f"Candidate snapshot hash mismatch: expected {expected_candidate_set_hash}, got {actual_snapshot_hash}"
                ),
                rejection_reason="CANDIDATE_SNAPSHOT_MISMATCH"
            )

        valid_channel_ids: Set[str] = {c.channel_id for c in valid_candidates}

        # 2. 严格纯 JSON 解析（明确异常集合）
        try:
            if isinstance(raw_response, str):
                cleaned_str = raw_response.strip()
                if cleaned_str.startswith("