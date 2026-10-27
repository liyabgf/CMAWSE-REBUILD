# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L19091-L19326 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #94  lines=235  compile=OK
# kind: module  ident: agent/llm_adapter.py  version: 3/6
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.1
模块：agent/llm_adapter.py
职责：LLM 认知适配器与确定性 Mock。接入快照一致性、出处信封与幂等性 Fail-Closed 保护。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from cmawse.agent.affordance import CandidateAffordance
from cmawse.agent.cognitive_projection import CognitiveMindContext, CognitiveProjection
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import (
    CognitiveMind,
    CognitiveSilentMode,
    MindDecision,
    MindDecisionStatus,
)
from cmawse.agent.intent import SubjectiveIntent
from cmawse.agent.llm_boundary import LLMBoundaryValidator
from cmawse.agent.provenance import DecisionProvenanceEnvelope
from cmawse.agent.representation import SubjectiveRepresentation
from cmawse.cognitive.memory import SubjectiveMemoryTrace
from cmawse.cognitive.rumor import RumorPacket


SYSTEM_PROMPT = """你是一个在客观物理世界中运行的主体心智认知审议模型。
你不是世界模拟器，不是物理引擎，不是叙事作者，不是行动执行器。
你的唯一职责：基于主体当前的主观具身情境、内部认知状态、主观意向愿景与感官可及的候选行动，决定主体是否形成行动承诺。

【绝对安全红线】
1. 你只能选择传入列表中客观存在的 candidate_id；
2. 严禁创造任何候选列表中不存在的行动、目标或工具；
3. 严禁修改物理力道、位移参数或环境属性；
4. 若决定不行动，必须返回 COGNITIVE_SILENT 并明确指定 silent_mode；
5. 若处于不可调和的心智撕扯，必须返回 UNRESOLVED_COGNITION。

【输出格式要求】
必须且只能返回单个合法纯 JSON 对象，严禁 Markdown 代码块包装，严禁前后附带任何自然语言：
{
  "status": "SELECTED" | "COGNITIVE_SILENT" | "UNRESOLVED_COGNITION",
  "candidate_id": "AFF_XXX" (仅在 SELECTED 时提供，否则为 null),
  "silent_mode": "OBSERVATIONAL_STANCE" | "PASSIVE_CONSERVATION" | "SUPPRESSED_INHIBITION" (仅在 COGNITIVE_SILENT 时必须提供，否则为 null),
  "reason": "主观审议简要理由"
}
"""


class LLMCognitiveAdapter:
    """基于外部 LLM API 的认知适配器"""

    def __init__(
        self,
        model_name: str = "qwen2.5:14b",
        endpoint_url: str = "http://localhost:11434/api/generate",
        timeout_seconds: float = 5.0,
        custom_http_caller: Optional[Callable[[str, Dict[str, Any]], str]] = None
    ) -> None:
        self.model_name = model_name
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds
        self._caller = custom_http_caller or self._default_ollama_caller
        self.last_provenance: Optional[DecisionProvenanceEnvelope] = None

    def deliberate(
        self,
        ctx: SubjectContext,
        state: InternalCognitiveState,
        rep: SubjectiveRepresentation,
        intents: List[SubjectiveIntent],
        candidates: List[CandidateAffordance],
        memories: List[SubjectiveMemoryTrace],
        rumors: List[RumorPacket]
    ) -> MindDecision:
        # 1. 建立不可变候选集快照与规范投影
        projected_context = CognitiveProjection.project(
            ctx=ctx,
            state=state,
            rep=rep,
            intents=intents,
            candidates=candidates,
            memories=memories,
            rumors=rumors
        )

        user_prompt = f"""【主体当前局域认知上下文】
{json.dumps(projected_context.model_dump(), ensure_ascii=False, indent=2)}

请审议上述处境与可选通道，输出你的决策 JSON："""

        # 2. 单步幂等性调用（调用失败立即 Fail-Closed）
        try:
            raw_text = self._caller(user_prompt, {"model": self.model_name})
        except Exception as err:
            decision = MindDecision(
                status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                telemetry_reason=f"LLM transport failure: {str(err)}"
            )
            self.last_provenance = DecisionProvenanceEnvelope.create(
                agent_id=ctx.agent_id,
                tick=ctx.tick,
                candidate_set_hash=projected_context.candidate_set_hash,
                projection_payload=projected_context.model_dump(),
                model_name=self.model_name,
                decision_status=decision.status.value,
                is_boundary_valid=False,
                rejection_reason=f"TRANSPORT_ERROR: {str(err)}"
            )
            return decision

        # 3. 严格边界防御校验（绑定候选集哈希快照）
        validation_result = LLMBoundaryValidator.validate_and_sanitize(
            raw_response=raw_text,
            valid_candidates=candidates,
            expected_candidate_set_hash=projected_context.candidate_set_hash
        )

        # 4. 记录纯旁路出处信封
        self.last_provenance = DecisionProvenanceEnvelope.create(
            agent_id=ctx.agent_id,
            tick=ctx.tick,
            candidate_set_hash=projected_context.candidate_set_hash,
            projection_payload=projected_context.model_dump(),
            model_name=self.model_name,
            decision_status=validation_result.decision.status.value,
            selected_candidate_id=validation_result.decision.candidate_id,
            silent_mode=validation_result.decision.silent_mode.value if validation_result.decision.silent_mode else None,
            is_boundary_valid=validation_result.is_valid,
            rejection_reason=validation_result.rejection_reason,
            reason_telemetry=validation_result.decision.telemetry_reason
        )

        return validation_result.decision

    def _default_ollama_caller(self, prompt: str, config: Dict[str, Any]) -> str:
        req_data = {
            "model": config.get("model", self.model_name),
            "system": SYSTEM_PROMPT,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "top_p": 0.8
            }
        }
        encoded_data = json.dumps(req_data).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint_url,
            data=encoded_data,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
            res_raw = response.read().decode("utf-8")
            res_json = json.loads(res_raw)
            return res_json.get("response", "{}")


class DeterministicMockCognitiveMind:
    """确定性认知审议 Mock 驱动（带出处追踪与快照绑定）"""

    def __init__(
        self,
        fixed_candidate_id: Optional[str] = None,
        fixed_silent_mode: Optional[CognitiveSilentMode] = None,
        fixed_decision_handler: Optional[Callable[[CognitiveMindContext], str | Dict[str, Any]]] = None
    ) -> None:
        self.fixed_candidate_id = fixed_candidate_id
        self.fixed_silent_mode = fixed_silent_mode
        self._handler = fixed_decision_handler
        self.last_provenance: Optional[DecisionProvenanceEnvelope] = None

    def deliberate(
        self,
        ctx: SubjectContext,
        state: InternalCognitiveState,
        rep: SubjectiveRepresentation,
        intents: List[SubjectiveIntent],
        candidates: List[CandidateAffordance],
        memories: List[SubjectiveMemoryTrace],
        rumors: List[RumorPacket]
    ) -> MindDecision:
        projected = CognitiveProjection.project(ctx, state, rep, intents, candidates, memories, rumors)

        if self._handler:
            raw_output = self._handler(projected)
        elif self.fixed_candidate_id is not None:
            raw_output = {
                "status": "SELECTED",
                "candidate_id": self.fixed_candidate_id,
                "silent_mode": None,
                "reason": "Mock explicit candidate selection"
            }
        elif self.fixed_silent_mode is not None:
            raw_output = {
                "status": "COGNITIVE_SILENT",
                "candidate_id": None,
                "silent_mode": self.fixed_silent_mode.value,
                "reason": "Mock explicit silent selection"
            }
        else:
            raw_output = {
                "status": "UNRESOLVED_COGNITION",
                "candidate_id": None,
                "silent_mode": None,
                "reason": "Mock unguided deliberation yields unresolved cognitive state"
            }

        validation = LLMBoundaryValidator.validate_and_sanitize(
            raw_response=raw_output,
            valid_candidates=candidates,
            expected_candidate_set_hash=projected.candidate_set_hash
        )

        self.last_provenance = DecisionProvenanceEnvelope.create(
            agent_id=ctx.agent_id,
            tick=ctx.tick,
            candidate_set_hash=projected.candidate_set_hash,
            projection_payload=projected.model_dump(),
            model_name="mock_deterministic",
            decision_status=validation.decision.status.value,
            selected_candidate_id=validation.decision.candidate_id,
            silent_mode=validation.decision.silent_mode.value if validation.decision.silent_mode else None,
            is_boundary_valid=validation.is_valid,
            rejection_reason=validation.rejection_reason,
            reason_telemetry=validation.decision.telemetry_reason
        )

        return validation.decision
