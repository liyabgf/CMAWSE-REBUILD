# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L18099-L18273 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #89  lines=174  compile=OK
# kind: module  ident: agent/llm_boundary.py  version: 2/5
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.0.1 Patch
模块：agent/llm_boundary.py
修复：严格执行 Fail-Closed。若返回 COGNITIVE_SILENT 且 silent_mode 为空，
严禁自动注入默认 OBSERVATIONAL_STANCE，直接拒止为 SYSTEM_FAILURE_SILENT。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cmawse.agent.affordance import CandidateAffordance
from cmawse.agent.deliberation import CognitiveSilentMode, MindDecision, MindDecisionStatus


class RawLLMOutputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: MindDecisionStatus
    candidate_id: Optional[str] = None
    silent_mode: Optional[CognitiveSilentMode] = None
    reason: Optional[str] = Field(default=None)


class BoundaryValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    is_valid: bool
    decision: MindDecision
    rejection_reason: Optional[str] = None


class LLMBoundaryValidator:
    """大模型认知边界严格防御校验器"""

    @classmethod
    def validate_and_sanitize(
        cls,
        raw_response: str | Dict[str, Any],
        valid_candidates: List[CandidateAffordance]
    ) -> BoundaryValidationResult:
        valid_channel_ids: Set[str] = {c.channel_id for c in valid_candidates if c.is_physically_feasible}

        try:
            if isinstance(raw_response, str):
                cleaned_str = raw_response.strip()
                if "{" in cleaned_str and "}" in cleaned_str:
                    start = cleaned_str.index("{")
                    end = cleaned_str.rindex("}") + 1
                    cleaned_str = cleaned_str[start:end]
                parsed_dict = json.loads(cleaned_str)
            else:
                parsed_dict = raw_response

            parsed_payload = RawLLMOutputSchema.model_validate(parsed_dict)
        except (json.JSONDecodeError, ValidationError, Exception) as err:
            return BoundaryValidationResult(
                is_valid=False,
                decision=MindDecision(
                    status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                    telemetry_reason=f"Schema or JSON decode failure: {str(err)}"
                ),
                rejection_reason=f"INVALID_PAYLOAD_SCHEMA: {str(err)}"
            )

        status = parsed_payload.status
        cid = parsed_payload.candidate_id
        smode = parsed_payload.silent_mode
        reason_text = parsed_payload.reason or "LLM Deliberated"

        # 1. SELECTED 校验
        if status == MindDecisionStatus.SELECTED:
            if not cid:
                return BoundaryValidationResult(
                    is_valid=False,
                    decision=MindDecision(
                        status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                        telemetry_reason="SELECTED status requires non-null candidate_id"
                    ),
                    rejection_reason="MISSING_CANDIDATE_ID_ON_SELECTED"
                )

            if cid not in valid_channel_ids:
                return BoundaryValidationResult(
                    is_valid=False,
                    decision=MindDecision(
                        status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                        telemetry_reason=f"Hallucinated or infeasible candidate_id: '{cid}'"
                    ),
                    rejection_reason=f"CANDIDATE_HALLUCINATION_REJECTED: '{cid}' not in valid set"
                )

            if smode is not None:
                return BoundaryValidationResult(
                    is_valid=False,
                    decision=MindDecision(
                        status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                        telemetry_reason="SELECTED status cannot contain silent_mode"
                    ),
                    rejection_reason="CONFLICTING_SILENT_MODE_ON_SELECTED"
                )

            return BoundaryValidationResult(
                is_valid=True,
                decision=MindDecision(
                    status=MindDecisionStatus.SELECTED,
                    candidate_id=cid,
                    telemetry_reason=reason_text
                )
            )

        # 2. COGNITIVE_SILENT 校验（严格 Fail-Closed）
        elif status == MindDecisionStatus.COGNITIVE_SILENT:
            if cid is not None:
                return BoundaryValidationResult(
                    is_valid=False,
                    decision=MindDecision(
                        status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                        telemetry_reason="COGNITIVE_SILENT cannot have candidate_id"
                    ),
                    rejection_reason="UNEXPECTED_CANDIDATE_ID_ON_SILENT"
                )

            # 严禁 Validator 自动替模型补充默认模式，缺失一律 Fail-Closed 拒止
            if smode is None:
                return BoundaryValidationResult(
                    is_valid=False,
                    decision=MindDecision(
                        status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                        telemetry_reason="COGNITIVE_SILENT requires explicit non-null silent_mode"
                    ),
                    rejection_reason="MISSING_SILENT_MODE_ON_COGNITIVE_SILENT"
                )

            return BoundaryValidationResult(
                is_valid=True,
                decision=MindDecision(
                    status=MindDecisionStatus.COGNITIVE_SILENT,
                    silent_mode=smode,
                    telemetry_reason=reason_text
                )
            )

        # 3. UNRESOLVED_COGNITION 校验
        elif status == MindDecisionStatus.UNRESOLVED_COGNITION:
            if cid is not None or smode is not None:
                return BoundaryValidationResult(
                    is_valid=False,
                    decision=MindDecision(
                        status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                        telemetry_reason="UNRESOLVED_COGNITION must not contain candidate_id or silent_mode"
                    ),
                    rejection_reason="INVALID_UNRESOLVED_PAYLOAD"
                )

            return BoundaryValidationResult(
                is_valid=True,
                decision=MindDecision(
                    status=MindDecisionStatus.UNRESOLVED_COGNITION,
                    telemetry_reason=reason_text
                )
            )

        # 4. 未知状态兜底
        return BoundaryValidationResult(
            is_valid=False,
            decision=MindDecision(
                status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                telemetry_reason="Unknown status state"
            ),
            rejection_reason="UNKNOWN_STATUS"
        )
