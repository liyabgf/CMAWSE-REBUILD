# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L32338-L32807 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #132  lines=469  compile=OK
# kind: module  ident: agent/nl_contract.py  version: 2/3
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.3.2
模块：agent/nl_contract.py
职责：候选规范化排序、递归不可变 DTO、正交失败层级与严格 Schema 跨字段校验。

【核心主权与因果契约 (Sovereign & Causal Contract)】
1. Canonical Candidate Ordering:
   Prompt 序列化前，候选集强制按照稳定 channel_id 升序排序，杜绝基于效用、打分、能耗的排序。
2. Recursive Immutability:
   PromptEnvelope 与 ModelResponse 内的所有嵌套数据树通过 MappingProxyType 与 tuple 实现深层冻结。
3. Orthogonal Failure Hierarchy:
   PROVIDER_FAILURE | MODEL_EMPTY_OUTPUT | MALFORMED_MODEL_OUTPUT | SCHEMA_VIOLATION | VALID_MODEL_OUTPUT。
4. Parser Schema Cross-Field Contract:
   Parser 负责跨字段类型与状态强校验，绝对不负责 candidate_id 在世界中的存在性校验。
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field

from cmawse.agent.cognitive_projection import CognitiveMindContext
from cmawse.agent.deliberation import (
    CognitiveMind,
    CognitiveSilentMode,
    MindDecision,
    MindDecisionStatus,
)
from cmawse.agent.provenance import DecisionProvenanceEnvelope


def _deep_freeze(val: Any) -> Any:
    """递归将 dict 转换为只读 MappingProxyType，将 list/set 转换为 tuple"""
    if isinstance(val, dict):
        return MappingProxyType({k: _deep_freeze(v) for k, v in val.items()})
    elif isinstance(val, (list, tuple, set)):
        return tuple(_deep_freeze(v) for v in val)
    return val


def canonical_serialize(obj: Any) -> str:
    """确定性规范化 JSON 序列化（消除格式与键排序非确定性）"""
    def _to_json_compatible(item: Any) -> Any:
        if isinstance(item, (dict, MappingProxyType)):
            return {k: _to_json_compatible(v) for k, v in sorted(item.items(), key=lambda x: str(x[0]))}
        elif isinstance(item, (list, tuple, set)):
            return [_to_json_compatible(v) for v in item]
        return item

    normalized = _to_json_compatible(obj)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class ParserOutcome(str, Enum):
    """解析器与前置调用执行结果分类（五态正交）"""
    VALID_MODEL_OUTPUT = "VALID_MODEL_OUTPUT"         # 语法与 Schema 合法
    MALFORMED_MODEL_OUTPUT = "MALFORMED_MODEL_OUTPUT" # JSON 语法畸变、重复键
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"             # 语法合法但跨字段结构非法
    MODEL_EMPTY_OUTPUT = "MODEL_EMPTY_OUTPUT"         # 模型返回空文本
    PROVIDER_FAILURE = "PROVIDER_FAILURE"             # 供应商级故障（超时、断连）


class ProviderErrorCode(str, Enum):
    """供应商层故障枚举"""
    TIMEOUT = "TIMEOUT"
    CONNECTION_FAILURE = "CONNECTION_FAILURE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"


class CanonicalCandidateEntry(BaseModel):
    """规范化候选动作 DTO（不可变）"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    channel_id: str
    action_type: str
    actuator: str
    estimated_metabolic_joules: float


class PromptEnvelope(BaseModel):
    """
    不可变 Prompt 请求信封（深层冻结）
    """
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    system_prompt: str
    projected_context_payload: Any  # Deep-frozen MappingProxyType
    schema_contract: Any            # Deep-frozen MappingProxyType
    model_identifier: str
    sampling_config: Any            # Deep-frozen MappingProxyType
    deterministic_hash: str
    canonical_candidates: Tuple[CanonicalCandidateEntry, ...]

    @classmethod
    def create(
        cls,
        system_prompt: str,
        context: CognitiveMindContext,
        schema_contract: Dict[str, Any],
        model_identifier: str,
        sampling_config: Dict[str, Any]
    ) -> PromptEnvelope:
        # 1. 候选规范化排序：严格依从 channel_id 字符字典序，严禁基于任何语义/能耗/效用排序
        sorted_candidates = tuple(
            CanonicalCandidateEntry(
                channel_id=c.channel_id,
                action_type=c.action_type,
                actuator=c.actuator.value,
                estimated_metabolic_joules=c.estimated_metabolic_joules
            )
            for c in sorted(context.available_candidates, key=lambda x: x.channel_id)
        )

        # 2. 构造规范化投影上下文
        payload_dict = {
            "agent_id": context.agent_id,
            "tick": context.tick,
            "somatic": {
                "energy_pool": context.somatic.energy_pool,
                "fatigue": context.somatic.fatigue,
                "sensory_overload": context.somatic.sensory_overload
            },
            "available_candidates": [c.model_dump() for c in sorted_candidates],
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

        # 3. 递归不可变深层冻结
        frozen_payload = _deep_freeze(payload_dict)
        frozen_schema = _deep_freeze(schema_contract)
        frozen_sampling = _deep_freeze(sampling_config)

        # 4. 规范化确定性哈希
        raw_to_hash = {
            "system_prompt": system_prompt,
            "context": frozen_payload,
            "schema": frozen_schema,
            "model": model_identifier,
            "sampling": frozen_sampling
        }
        serialized = canonical_serialize(raw_to_hash)
        h = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return cls(
            system_prompt=system_prompt,
            projected_context_payload=frozen_payload,
            schema_contract=frozen_schema,
            model_identifier=model_identifier,
            sampling_config=frozen_sampling,
            deterministic_hash=h,
            canonical_candidates=sorted_candidates
        )


class ModelResponse(BaseModel):
    """
    不可变模型响应 DTO（深层冻结）
    """
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    raw_text: str
    provider_identifier: str
    model_identifier: str
    response_metadata: Any  # Deep-frozen MappingProxyType
    raw_response_hash: str
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
        frozen_meta = _deep_freeze(response_metadata or {})
        return cls(
            raw_text=raw_text,
            provider_identifier=provider_identifier,
            model_identifier=model_identifier,
            response_metadata=frozen_meta,
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
        frozen_meta = _deep_freeze({"error_details": details})
        return cls(
            raw_text="",
            provider_identifier=provider_identifier,
            model_identifier=model_identifier,
            response_metadata=frozen_meta,
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
    严格模型输出解析器：
    执行纯语法与跨字段 Schema 约束验证，绝对不负责 candidate_id 在物理世界中的存在性。
    """

    ALLOWED_STATUSES = {s.value for s in MindDecisionStatus}
    ALLOWED_SILENT_MODES = {m.value for m in CognitiveSilentMode}

    @classmethod
    def parse(cls, response: ModelResponse) -> tuple[MindDecision, ParserOutcome, Optional[str]]:
        # 1. 检查 Provider 级别故障
        if response.error_code is not None:
            return (
                MindDecision(
                    status=MindDecisionStatus.FALLBACK_SILENT,
                    candidate_id=None,
                    silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                    telemetry_reason=f"PROVIDER_FAILURE: {response.error_code.value}"
                ),
                ParserOutcome.PROVIDER_FAILURE,
                f"Provider failed with {response.error_code.value}"
            )

        # 2. 检查空输出故障
        raw_text = response.raw_text
        if raw_text is None or not raw_text.strip():
            return (
                MindDecision(
                    status=MindDecisionStatus.FALLBACK_SILENT,
                    candidate_id=None,
                    silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                    telemetry_reason="MODEL_EMPTY_OUTPUT: Received empty text from model"
                ),
                ParserOutcome.MODEL_EMPTY_OUTPUT,
                "Model returned empty text or whitespace"
            )

        # 3. 语法解析：检测重复键与 JSON 畸变
        def _dict_without_duplicates(pairs):
            d = {}
            for k, v in pairs:
                if k in d:
                    raise ValueError(f"Duplicate key detected: {k}")
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
                    telemetry_reason=f"MALFORMED_MODEL_OUTPUT: {str(e)}"
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

        # 4. 字段白名单检查（禁止多余字段）
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

        if reason is not None and not isinstance(reason, str):
            return (
                MindDecision(
                    status=MindDecisionStatus.FALLBACK_SILENT,
                    candidate_id=None,
                    silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                    telemetry_reason="SCHEMA_VIOLATION: reason must be string or null"
                ),
                ParserOutcome.SCHEMA_VIOLATION,
                "reason field must be a string or null"
            )

        # 5. 跨字段状态契约强校验 (Cross-Field Schema Validation)
        if status == MindDecisionStatus.SELECTED:
            if not isinstance(candidate_id, str) or not candidate_id.strip():
                return (
                    MindDecision(
                        status=MindDecisionStatus.FALLBACK_SILENT,
                        candidate_id=None,
                        silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                        telemetry_reason="SCHEMA_VIOLATION: SELECTED requires non-empty string candidate_id"
                    ),
                    ParserOutcome.SCHEMA_VIOLATION,
                    "SELECTED status requires string candidate_id"
                )
        elif status in (MindDecisionStatus.COGNITIVE_SILENT, MindDecisionStatus.UNRESOLVED_COGNITION, MindDecisionStatus.FALLBACK_SILENT):
            if candidate_id is not None:
                return (
                    MindDecision(
                        status=MindDecisionStatus.FALLBACK_SILENT,
                        candidate_id=None,
                        silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                        telemetry_reason=f"SCHEMA_VIOLATION: {status.value} forbids candidate_id"
                    ),
                    ParserOutcome.SCHEMA_VIOLATION,
                    f"{status.value} forbids candidate_id"
                )

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

        # 语法与 Schema 验证通过（注意：虚构 candidate_id 此处依然合法，交给 Boundary 处理）
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
    供应商中立认知适配器（Phase 3.3.2 闭环加固版本）
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

        # 完整出处元数据构建（真实绑定所有字段）
        self._last_provenance = DecisionProvenanceEnvelope(
            agent_id=context.agent_id,
            tick=context.tick,
            source_candidates_snapshot_hash=context.snapshot_hash,
            system_prompt_snapshot_hash=prompt_req.deterministic_hash,
            model_identifier=self.model_interface.model_identifier,
            provider_identifier=response.provider_identifier,
            raw_response_hash=response.raw_response_hash,
            parser_outcome=outcome.value,
            rejection_reason=rejection_reason,
            reason_telemetry=decision.telemetry_reason
        )

        return decision
