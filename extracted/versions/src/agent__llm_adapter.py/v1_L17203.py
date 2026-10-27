# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L17203-L17385 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #84  lines=182  compile=OK
# kind: module  ident: agent/llm_adapter.py  version: 1/6
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.0
模块：agent/llm_adapter.py
职责：实现 CognitiveMind 的真实外部 LLM 驱动适配器与确定性测试 Mock 驱动。
支持 Ollama HTTP API (Qwen-2.5-14B) 与各类 OpenAI 兼容接口。
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
4. 若认为当前代价过高、信息不足或需节能观察，必须返回 COGNITIVE_SILENT；
5. 若处于不可调和的心智撕扯，必须返回 UNRESOLVED_COGNITION。

【输出格式要求】
必须且只能返回符合以下 Schema 的单个纯 JSON 字典，严禁任何额外 Markdown 修饰：
{
  "status": "SELECTED" | "COGNITIVE_SILENT" | "UNRESOLVED_COGNITION",
  "candidate_id": "AFF_XXX" (仅在 SELECTED 时提供，否则为 null),
  "silent_mode": "OBSERVATIONAL_STANCE" | "PASSIVE_CONSERVATION" | "SUPPRESSED_INHIBITION" (仅在 COGNITIVE_SILENT 时提供，否则为 null),
  "reason": "主观审议简要理由 (不参与任何因果执行)"
}
"""


class LLMCognitiveAdapter:
    """基于真实外部大语言模型的认知适配器 (Ollama / OpenAI API 驱动)"""

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
        # 1. 安全投影（剥离全局未见信息）
        projected_context = CognitiveProjection.project(
            ctx=ctx,
            state=state,
            rep=rep,
            intents=intents,
            candidates=candidates,
            memories=memories,
            rumors=rumors
        )

        # 2. 构造提示词载荷
        user_prompt = f"""【主体当前局域认知上下文】
{json.dumps(projected_context.model_dump(), ensure_ascii=False, indent=2)}

请审议上述处境与可选通道，输出你的决策 JSON："""

        # 3. 调用大模型
        try:
            raw_text = self._caller(user_prompt, {"model": self.model_name})
        except Exception as err:
            return MindDecision(
                status=MindDecisionStatus.SYSTEM_FAILURE_SILENT,
                telemetry_reason=f"LLM call failed: {str(err)}"
            )

        # 4. 边界合规校验与清洗
        validation_result = LLMBoundaryValidator.validate_and_sanitize(
            raw_response=raw_text,
            valid_candidates=candidates
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
                "temperature": 0.3,
                "top_p": 0.85
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
    """
    确定性认知审议 Mock 驱动（用于架构、ABI 与对抗性单元测试，脱离外部 Ollama 依赖）。
    完全通过 MindDecision 协议驱动，支持注入可控的模拟输出。
    """

    def __init__(self, fixed_decision_handler: Optional[Callable[[CognitiveMindContext], str | Dict[str, Any]]] = None) -> None:
        self._handler = fixed_decision_handler or self._default_mock_logic

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
        raw_output = self._handler(projected)

        validation = LLMBoundaryValidator.validate_and_sanitize(
            raw_response=raw_output,
            valid_candidates=candidates
        )
        return validation.decision

    @staticmethod
    def _default_mock_logic(p_ctx: CognitiveMindContext) -> Dict[str, Any]:
        # 默认 Mock：若无候选返回静止，若有意向与匹配通道则返回首个有效 ID
        if not p_ctx.available_candidates:
            return {
                "status": "COGNITIVE_SILENT",
                "candidate_id": None,
                "silent_mode": "PASSIVE_CONSERVATION",
                "reason": "No actionable candidates in horizon"
            }

        return {
            "status": "SELECTED",
            "candidate_id": p_ctx.available_candidates[0].channel_id,
            "silent_mode": None,
            "reason": "Mock deterministic choice"
        }
