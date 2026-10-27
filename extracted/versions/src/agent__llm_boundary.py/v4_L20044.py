# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L20044-L20117 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #97  lines=73  compile=FAIL:74:unterminated string literal (detected at line 74
# kind: module  ident: agent/llm_boundary.py  version: 4/5
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.1.1
模块：agent/llm_boundary.py
职责：实现 Candidate Snapshot Identity 绑定核验与纯 JSON 边界防御。
切除 "LLM Deliberated" 假理由，缺失 reason 则保持 None，断言快照哈希一致性。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set
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
        valid_candidates: List[CandidateAffordance] | List[ProjectedCandidateDTO],
        expected_candidate_set_hash: Optional[str] = None
    ) -> BoundaryValidationResult:
        # 1. 候选快照身份核验 (Snapshot Identity Verification)
        if expected_candidate_set_hash is not None:
            actual_snapshot_hash = CognitiveProjection.compute_candidate_snapshot_hash(valid_candidates)
            if actual_snapshot_hash != expected_candidate_set_hash:
                return BoundaryValidationResult(
                    is_valid=False,
                    decision=MindDecision(
                        status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                        telemetry_reason=f"Candidate snapshot hash mismatch: expected {expected_candidate_set_hash}, got {actual_snapshot_hash}"
                    ),
                    rejection_reason="CANDIDATE_SNAPSHOT_MISMATCH"
                )

        valid_channel_ids: Set[str] = {c.channel_id for c in valid_candidates}

        # 2. 严格纯 JSON 解析
        try:
            if isinstance(raw_response, str):
                cleaned_str = raw_response.strip()
                if cleaned_str.startswith("