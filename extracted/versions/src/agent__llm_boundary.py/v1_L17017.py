# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L17017-L17197 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #83  lines=180  compile=OK
# kind: module  ident: agent/llm_boundary.py  version: 1/5
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.0
模块：agent/llm_boundary.py
职责：LLM 输出边界校验器 (LLM Boundary Validator)。
严格执行 Fail-Closed 策略。
确立不变量：LLM 绝不能创造候选、不能创造实体、不能修改物理参数、不能通过自然语言越权。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cmawse.agent.affordance import CandidateAffordance
from cmawse.agent.deliberation import CognitiveSilentMode, MindDecision, MindDecisionStatus


class RawLLMOutputSchema(BaseModel):
    """大模型返回的严格 JSON 结构定义"""
    model_config = ConfigDict(extra="forbid")  # 严禁任何未声明字段 (如 action, target, force 等)

    status: MindDecisionStatus
    candidate_id: Optional[str] = None
    silent_mode: Optional[CognitiveSilentMode] = None
    reason: Optional[str] = Field(default=None, description="旁路遥测解释，不参与任何因果决策")


class BoundaryValidationResult(BaseModel):
    """边界校验结果报告"""
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
        """
        全量边界合规检验：
        1. JSON 格式与 Strict Schema 校验；
        2. candidate_id 存在性与 Candidate Set 精确匹配（禁止模糊匹配与幻觉创建）；
        3. 状态与字段的语义互斥断言；
        4. 任何异常一律 Fail-Closed 降阶为 SYSTEM_FAILURE_SILENT。
        """
        valid_channel_ids: Set[str] = {c.channel_id for c in valid_candidates if c.is_physically_feasible}

        # 1. 基础解析与 Schema 校验
        try:
            if isinstance(raw_response, str):
                # 提取首个有效 JSON 块，防止模型输出自然语言包装
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

        # 2. SELECTED 状态强约束校验
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

            # 核心权限防御：必须严格等于候选集内的 ID，严禁幻觉创造与模糊推测
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

        # 3. COGNITIVE_SILENT 状态强约束校验
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

            if not smode:
                # 默认赋予客观审议观察姿态
                smode = CognitiveSilentMode.OBSERVATIONAL_STANCE

            return BoundaryValidationResult(
                is_valid=True,
                decision=MindDecision(
                    status=MindDecisionStatus.COGNITIVE_SILENT,
                    silent_mode=smode,
                    telemetry_reason=reason_text
                )
            )

        # 4. UNRESOLVED_COGNITION 状态强约束校验
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

        # 5. 其他异常兜底
        return BoundaryValidationResult(
            is_valid=False,
            decision=MindDecision(
                status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                telemetry_reason="Unknown status state"
            ),
            rejection_reason="UNKNOWN_STATUS"
        )
