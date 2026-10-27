# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L31649-L32015 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #131  lines=366  compile=OK
# kind: module  ident: agent/nl_contract.py  version: 1/3
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.3.1
模块：agent/nl_contract.py
职责：Provider-Agnostic 模型接口契约、不可变 Prompt/Response DTO、严格解析状态机。

【因果与主权契约 (Sovereign Contract)】
1. 职责分离：
   - Parser 仅负责语法与输出 Schema 校验，不核验 candidate_id 存在性。
   - BoundaryValidator 负责因果边界核验。
2. 供应商故障零降阶自愈：
   - 遭遇超时、网络故障、空响应时，严禁代为选择任何动作，只能降阶为 FALLBACK_SILENT。
3. 不可变性：
   - PromptEnvelope, ModelResponse, DecisionProvenanceEnvelope 均为不可变 DTO。
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from pydantic import BaseModel, ConfigDict, Field

from cmawse.agent.cognitive_projection import CognitiveMindContext
from cmawse.agent.deliberation import (
    CognitiveMind,
    CognitiveSilentMode,
    MindDecision,
    MindDecisionStatus,
)
from cmawse.agent.provenance import DecisionProvenanceEnvelope


class ParserOutcome(str, Enum):
    """解析器执行结果分类"""
    VALID_MODEL_OUTPUT = "VALID_MODEL_OUTPUT"         # 语法合法，成功转换为 MindDecision
    MALFORMED_MODEL_OUTPUT = "MALFORMED_MODEL_OUTPUT" # JSON 畸变、解析失败
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"             # 语法合法但字段非法（重复键、多余键、缺少状态等）


class ProviderErrorCode(str, Enum):
    """供应商层故障枚举"""
    TIMEOUT = "TIMEOUT"
    CONNECTION_FAILURE = "CONNECTION_FAILURE"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"


class PromptEnvelope(BaseModel):
    """不可变 Prompt 请求信封"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    system_prompt: str
    projected_context_payload: Dict[str, Any]
    schema_contract: Dict[str, Any]
    model_identifier: str
    sampling_config: Dict[str, Any]
    deterministic_hash: str = Field(default="")

    @classmethod
    def create(
        cls,
        system_prompt: str,
        context: CognitiveMindContext,
        schema_contract: Dict[str, Any],
        model_identifier: str,
        sampling_config: Dict[str, Any]
    ) -> PromptEnvelope:
        # 严格只读序列化 CognitiveMindContext
        payload = {
            "agent_id": context.agent_id,
            "tick": context.tick,
            "somatic": {
                "energy_pool": context.somatic.energy_pool,
                "fatigue": context.somatic.fatigue,
                "sensory_overload": context.somatic.sensory_overload
            },
            "available_candidates": [
                {
                    "channel_id": c.channel_id,
                    "action_type": c.action_type,
                    "actuator": c.actuator.value,
                    "estimated_metabolic_joules": c.estimated_metabolic_joules
                }
                for c in context.available_candidates
            ],
            "projected_memories": [
                {
                    "event_ref": m.event_ref,
                    "subjective_rationalization": m.subjective_rationalization
                }
                for m in context.projected_memories
            ],
            "projected_rumors": [
                {
                    "rumor_id": r.rumor_id,
                    "content_summary": r.content_summary
                }
                for r in context.projected_rumors
            ]
        }
        serialized_for_hash = json.dumps(
            {"sys": system_prompt, "ctx": payload, "schema": schema_contract, "model": model_identifier, "sampling": sampling_config},
            sort_keys=True,
            ensure_ascii=False
        )
        h = hashlib.sha256(serialized_for_hash.encode("utf-8")).hexdigest()
        return cls(
            system_prompt=system_prompt,
            projected_context_payload=payload,
            schema_contract=schema_contract,
            model_identifier=model_identifier,
            sampling_config=sampling_config,
            deterministic_hash=h
        )


class ModelResponse(BaseModel):
    """不可变模型响应 DTO"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    raw_text: str
    provider_identifier: str
    model_identifier: str
    response_metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_response_hash: str = Field(default="")
    error_code: Optional[ProviderErrorCode] = None

    @classmethod
    def successful(
        cls,
        raw_text: str,
        provider_identifier: str,
        model_identifier: str,
        response_metadata: Optional[Dict[str, Any]] = None
    ) -> ModelResponse:
        h = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        return cls(
            raw_text=raw_text,
            provider_identifier=provider_identifier,
            model_identifier=model_identifier,
            response_metadata=response_metadata or {},
            raw_response_hash=h,
            error_code=None
        )

    @classmethod
    def failed(
        cls,
        error_code: ProviderErrorCode,
        provider_identifier: str,
        model_identifier: str,
        details: str = ""
    ) -> ModelResponse:
        return cls(
            raw_text="",
            provider_identifier=provider_identifier,
            model_identifier=model_identifier,
            response_metadata={"error_details": details},
            raw_response_hash="",
            error_code=error_code
        )


class LLMModelInterface(Protocol):
    """供应商中立模型调用抽象接口"""
    provider_identifier: str
    model_identifier: str
    sampling_config: Dict[str, Any]

    def invoke(self, request: PromptEnvelope) -> ModelResponse:
        ...


class StrictLLMOutputParserV2:
    """
    升级版严格模型输出解析器：
    执行语法与字段结构解析，严格区分语法违规与语义越界。
    """

    ALLOWED_STATUSES = {s.value for s in MindDecisionStatus}
    ALLOWED_SILENT_MODES = {m.value for m in CognitiveSilentMode}

    @classmethod
    def parse(cls, response: ModelResponse) -> tuple[MindDecision, ParserOutcome, Optional[str]]:
        if response.error_code is not None:
            return (
                MindDecision(
                    status=MindDecisionStatus.FALLBACK_SILENT,
                    candidate_id=None,
                    silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                    telemetry_reason=f"PROVIDER_FAILURE: {response.error_code.value}"
                ),
                ParserOutcome.MALFORMED_MODEL_OUTPUT,
                f"Provider failed with {response.error_code.value}"
            )

        raw_text = response.raw_text
        if not raw_text or not raw_text.strip():
            return (
                MindDecision(
                    status=MindDecisionStatus.FALLBACK_SILENT,
                    candidate_id=None,
                    silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                    telemetry_reason="EMPTY_MODEL_OUTPUT"
                ),
                ParserOutcome.MALFORMED_MODEL_OUTPUT,
                "Model returned empty text."
            )

        def _dict_without_duplicates(pairs):
            d = {}
            for k, v in pairs:
                if k in d:
                    raise ValueError(f"Duplicate key: {k}")
                d[k] = v
            return d

        try:
            data = json.loads(raw_text, object_pairs_hook=_dict_without_duplicates)
        except Exception as e:
            return (
                MindDecision(
                    status=MindDecisionStatus.FALLBACK_SILENT,
                    candidate_id=None,
                    silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                    telemetry_reason=f"MALFORMED_JSON: {str(e)}"
                ),
                ParserOutcome.MALFORMED_MODEL_OUTPUT,
                str(e)
            )

        if not isinstance(data, dict):
            return (
                MindDecision(
                    status=MindDecisionStatus.FALLBACK_SILENT,
                    candidate_id=None,
                    silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                    telemetry_reason="SCHEMA_VIOLATION: Root must be an object"
                ),
                ParserOutcome.SCHEMA_VIOLATION,
                "Root is not an object"
            )

        allowed_keys = {"status", "candidate_id", "silent_mode", "reason"}
        extra_keys = set(data.keys()) - allowed_keys
        if extra_keys:
            return (
                MindDecision(
                    status=MindDecisionStatus.FALLBACK_SILENT,
                    candidate_id=None,
                    silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                    telemetry_reason=f"SCHEMA_VIOLATION: Extra fields {extra_keys}"
                ),
                ParserOutcome.SCHEMA_VIOLATION,
                f"Extra fields: {extra_keys}"
            )

        status_str = data.get("status")
        if status_str not in cls.ALLOWED_STATUSES:
            return (
                MindDecision(
                    status=MindDecisionStatus.FALLBACK_SILENT,
                    candidate_id=None,
                    silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                    telemetry_reason=f"SCHEMA_VIOLATION: Invalid status {status_str}"
                ),
                ParserOutcome.SCHEMA_VIOLATION,
                f"Invalid status: {status_str}"
            )

        status = MindDecisionStatus(status_str)
        candidate_id = data.get("candidate_id")
        silent_mode_str = data.get("silent_mode")
        reason = data.get("reason")

        if silent_mode_str is not None:
            if silent_mode_str not in cls.ALLOWED_SILENT_MODES:
                return (
                    MindDecision(
                        status=MindDecisionStatus.FALLBACK_SILENT,
                        candidate_id=None,
                        silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                        telemetry_reason=f"SCHEMA_VIOLATION: Invalid silent_mode {silent_mode_str}"
                    ),
                    ParserOutcome.SCHEMA_VIOLATION,
                    f"Invalid silent_mode: {silent_mode_str}"
                )
            silent_mode = CognitiveSilentMode(silent_mode_str)
        else:
            silent_mode = None

        # 语法结构合法（注意：若 candidate_id 为非法虚构，此处依然判定为 VALID_MODEL_OUTPUT，交给 Boundary 裁决）
        return (
            MindDecision(
                status=status,
                candidate_id=candidate_id,
                silent_mode=silent_mode,
                telemetry_reason=reason
            ),
            ParserOutcome.VALID_MODEL_OUTPUT,
            None
        )


class ProviderAgnosticCognitiveAdapter(CognitiveMind):
    """
    供应商中立认知适配器
    """

    def __init__(
        self,
        model_interface: LLMModelInterface,
        system_prompt: str = "You are an embodied cognitive mind. Deliberate and output valid JSON."
    ) -> None:
        self.model_interface = model_interface
        self.system_prompt = system_prompt
        self._last_provenance: Optional[DecisionProvenanceEnvelope] = None
        self._last_parser_outcome: Optional[ParserOutcome] = None

    @property
    def last_provenance(self) -> Optional[DecisionProvenanceEnvelope]:
        return self._last_provenance

    @property
    def last_parser_outcome(self) -> Optional[ParserOutcome]:
        return self._last_parser_outcome

    def deliberate(self, context: CognitiveMindContext) -> MindDecision:
        schema_contract = {
            "type": "object",
            "required": ["status"],
            "properties": {
                "status": ["SELECTED", "COGNITIVE_SILENT", "UNRESOLVED_COGNITION", "FALLBACK_SILENT"],
                "candidate_id": "string or null",
                "silent_mode": "string or null",
                "reason": "string or null"
            }
        }
        prompt_req = PromptEnvelope.create(
            system_prompt=self.system_prompt,
            context=context,
            schema_contract=schema_contract,
            model_identifier=self.model_interface.model_identifier,
            sampling_config=self.model_interface.sampling_config
        )

        response = self.model_interface.invoke(prompt_req)
        decision, outcome, err_details = StrictLLMOutputParserV2.parse(response)
        self._last_parser_outcome = outcome

        rejection_reason = None
        if outcome != ParserOutcome.VALID_MODEL_OUTPUT:
            rejection_reason = f"{outcome.value}: {err_details}"

        self._last_provenance = DecisionProvenanceEnvelope(
            agent_id=context.agent_id,
            tick=context.tick,
            source_candidates_snapshot_hash=context.snapshot_hash,
            system_prompt_snapshot_hash=prompt_req.deterministic_hash,
            model_identifier=self.model_interface.model_identifier,
            rejection_reason=rejection_reason,
            reason_telemetry=decision.telemetry_reason
        )

        return decision
