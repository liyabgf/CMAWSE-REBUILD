# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L31183-L31394 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #130  lines=211  compile=OK
# kind: module  ident: agent/nl_adapter.py  version: latest of 1 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.3.0
模块：agent/nl_adapter.py
职责：自然语言心智适配器接口、严格模型输出解析器与认知出处记录。

【架构防火墙契约 (Architectural Firewall Contract)】
1. 零自动修复：
   - 解析器绝不自动选择首尾候选、唯一候选或根据意图/理由反向推断候选。
   - 畸变、重复键、非法格式严格抛出异常或降阶，绝不猜测意图。
2. 越权直达边界：
   - LLM 虚构的 candidate_id 原样保留并传递至 MindDecision，由 Boundary Validator 进行拦截并降阶。
   - 解析器绝不自行“洗白”或“纠偏”非法候选。
3. 认知出处只读：
   - Provenance 仅供事后审计与重放，无世界状态写权限。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from cmawse.agent.cognitive_projection import CognitiveMindContext
from cmawse.agent.deliberation import (
    CognitiveMind,
    CognitiveSilentMode,
    MindDecision,
    MindDecisionStatus,
)
from cmawse.agent.provenance import DecisionProvenanceEnvelope


class LLMParseError(Exception):
    """LLM 原始文本解析失败（语法畸变、键重复、字段非法等）"""
    pass


class StrictLLMOutputParser:
    """
    严格 LLM 输出解析器：
    仅接受严格符合 Schema 的标准 JSON，绝不执行任何启发式纠偏。
    """

    ALLOWED_STATUSES = {s.value for s in MindDecisionStatus}
    ALLOWED_SILENT_MODES = {m.value for m in CognitiveSilentMode}

    @classmethod
    def parse_raw_response(cls, raw_text: str) -> MindDecision:
        """
        严格解析大模型输出文本。
        反模式防御：
        - 拒绝重复键 (Duplicate Keys)
        - 拒绝多余字段 (Extra Fields)
        - 拒绝未知状态枚举
        - 绝不自动选择候选或自愈
        """
        # 1. 严格 JSON 解析，检测重复键
        def _dict_without_duplicates(pairs):
            d = {}
            for k, v in pairs:
                if k in d:
                    raise LLMParseError(f"Duplicate key detected in LLM response: {k}")
                d[k] = v
            return d

        try:
            data = json.loads(raw_text, object_pairs_hook=_dict_without_duplicates)
        except Exception as e:
            raise LLMParseError(f"Malformed JSON in LLM raw output: {str(e)}") from e

        if not isinstance(data, dict):
            raise LLMParseError("LLM response root must be a JSON object.")

        # 2. 严格字段白名单校验 (禁止额外字段)
        allowed_keys = {"status", "candidate_id", "silent_mode", "reason"}
        extra_keys = set(data.keys()) - allowed_keys
        if extra_keys:
            raise LLMParseError(f"Extra forbidden fields in LLM response: {extra_keys}")

        status_str = data.get("status")
        if status_str not in cls.ALLOWED_STATUSES:
            raise LLMParseError(f"Illegal or missing status: {status_str}")

        status = MindDecisionStatus(status_str)
        candidate_id = data.get("candidate_id")
        silent_mode_str = data.get("silent_mode")
        reason = data.get("reason")

        if silent_mode_str is not None:
            if silent_mode_str not in cls.ALLOWED_SILENT_MODES:
                raise LLMParseError(f"Illegal silent_mode: {silent_mode_str}")
            silent_mode = CognitiveSilentMode(silent_mode_str)
        else:
            silent_mode = None

        # 3. 构造决策包 (注意：不对 candidate_id 的合法性在此进行自动纠偏，原样抛给 Boundary)
        return MindDecision(
            status=status,
            candidate_id=candidate_id,
            silent_mode=silent_mode,
            telemetry_reason=reason
        )


class NaturalLanguageCognitiveAdapter(CognitiveMind):
    """
    自然语言认知适配器（测试仿真驱动）
    职责：
    1. 接收 CognitiveMindContext，渲染为只读 Prompt；
    2. 调用可插拔的 model_caller (Mock/Real)；
    3. 通过 StrictLLMOutputParser 解析输出；
    4. 产生不可篡改的 DecisionProvenanceEnvelope。
    """

    def __init__(
        self,
        adapter_identifier: str = "adapter_v1_strict",
        model_identifier: str = "mock_deterministic_llm",
        sampling_config: Optional[Dict[str, Any]] = None,
        raw_model_caller: Optional[Callable[[str], str]] = None
    ) -> None:
        self.adapter_identifier = adapter_identifier
        self.model_identifier = model_identifier
        self.sampling_config = sampling_config or {"temperature": 0.0}
        self.raw_model_caller = raw_model_caller or (lambda prompt: '{"status": "FALLBACK_SILENT"}')
        self._last_provenance: Optional[DecisionProvenanceEnvelope] = None

    @property
    def last_provenance(self) -> Optional[DecisionProvenanceEnvelope]:
        return self._last_provenance

    def render_prompt(self, context: CognitiveMindContext) -> str:
        """
        认知投影严格序列化：
        保证唯有 CognitiveMindContext 中的数据会被渲染进 Prompt。
        隐蔽世界实体、未投影上下文均无法被包含。
        """
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
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def deliberate(self, context: CognitiveMindContext) -> MindDecision:
        """
        心智审议执行主干：
        严格遵循 Prompt -> Raw Output -> Parser -> MindDecision -> Provenance。
        绝不直接修改世界状态，绝不越过 Boundary。
        """
        prompt = self.render_prompt(context)
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        snapshot_hash = context.snapshot_hash

        # 1. 模拟调用模型
        raw_output = self.raw_model_caller(prompt)
        raw_hash = hashlib.sha256(raw_output.encode("utf-8")).hexdigest()

        # 2. 严格解析
        parse_rejection: Optional[str] = None
        try:
            decision = StrictLLMOutputParser.parse_raw_response(raw_output)
        except LLMParseError as err:
            parse_rejection = f"LLM_PARSE_ERROR: {str(err)}"
            decision = MindDecision(
                status=MindDecisionStatus.FALLBACK_SILENT,
                candidate_id=None,
                silent_mode=CognitiveSilentMode.INHIBITED_STASIS,
                telemetry_reason=parse_rejection
            )

        # 3. 记录出处信封 (不可篡改审计证据)
        self._last_provenance = DecisionProvenanceEnvelope(
            agent_id=context.agent_id,
            tick=context.tick,
            source_candidates_snapshot_hash=snapshot_hash,
            system_prompt_snapshot_hash=prompt_hash,
            model_identifier=self.model_identifier,
            rejection_reason=parse_rejection,
            reason_telemetry=decision.telemetry_reason
        )

        return decision
