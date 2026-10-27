# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L16884-L17011 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #82  lines=127  compile=OK
# kind: module  ident: agent/cognitive_projection.py  version: 1/7
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.0
模块：agent/cognitive_projection.py
职责：认知输入投影层 (Cognitive Input Projection Layer)。
严格单向降维：World Reality -> Perception -> Agent Cognition。
确保全局世界未见事实、隐藏NPC、未来规划与世界状态完全无法渗透入认知上下文。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from cmawse.agent.affordance import CandidateAffordance
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.intent import SubjectiveIntent
from cmawse.agent.representation import SubjectiveRepresentation
from cmawse.cognitive.memory import SubjectiveMemoryTrace
from cmawse.cognitive.rumor import RumorPacket


class ProjectedCandidate(BaseModel):
    """投影至大模型视界的可供性通道描述（只读、无内部地址泄露）"""
    model_config = ConfigDict(frozen=True)

    channel_id: str
    action_type: str
    actuator: str
    target_id: Optional[str] = None
    target_surface: str
    action_attribute: str
    narrative_status: str
    estimated_metabolic_joules: float


class CognitiveMindContext(BaseModel):
    """
    大语言模型认知审议的唯一合法输入载荷（Strict Whitelist Payload）。
    绝对不包含 GlobalWorldState、不包含未感知实体、不包含隐式决策答案。
    """
    model_config = ConfigDict(frozen=True)

    agent_id: str
    tick: int
    subjective_representation: Dict[str, Any]
    internal_cognitive_state: Dict[str, Any]
    subjective_intents: List[Dict[str, Any]]
    available_candidates: List[ProjectedCandidate]
    recalled_memories: List[Dict[str, Any]]
    received_rumors: List[Dict[str, Any]]
    somatic_summary: Dict[str, Any]
    social_summary: Dict[str, Any]


class CognitiveProjection:
    """认知输入安全投影器"""

    @classmethod
    def project(
        cls,
        ctx: SubjectContext,
        state: InternalCognitiveState,
        rep: SubjectiveRepresentation,
        intents: List[SubjectiveIntent],
        candidates: List[CandidateAffordance],
        memories: List[SubjectiveMemoryTrace],
        rumors: List[RumorPacket]
    ) -> CognitiveMindContext:
        # 1. 投影客观候选集（只暴露通道 ID 与物理/叙事属性，不暴露内部私有对象）
        projected_candidates: List[ProjectedCandidate] = []
        for c in candidates:
            if not c.is_physically_feasible:
                continue
            projected_candidates.append(
                ProjectedCandidate(
                    channel_id=c.channel_id,
                    action_type=c.action_type,
                    actuator=c.actuator.value,
                    target_id=c.target_id,
                    target_surface=c.target_surface.value,
                    action_attribute=c.action_attribute.value,
                    narrative_status=c.narrative_status.value,
                    estimated_metabolic_joules=c.estimated_metabolic_joules
                )
            )

        # 2. 投影记忆与传闻（仅限在场相关与主体私有）
        projected_memories = [
            {
                "event_ref": m.event_ref,
                "recorded_tick": m.recorded_tick,
                "subjective_rationalization": m.subjective_rationalization,
                "salience_tags": m.salience_tags
            }
            for m in memories
        ]

        projected_rumors = [
            {
                "origin_event_id": r.origin_event_id,
                "hop_count": r.hop_count,
                "gist": r.gist
            }
            for r in rumors
        ]

        # 3. 投影内部心智状态与主观意向（序列化为纯数据字典）
        return CognitiveMindContext(
            agent_id=ctx.agent_id,
            tick=ctx.tick,
            subjective_representation=rep.model_dump(),
            internal_cognitive_state=state.model_dump(),
            subjective_intents=[i.model_dump() for i in intents],
            available_candidates=projected_candidates,
            recalled_memories=projected_memories,
            received_rumors=projected_rumors,
            somatic_summary={
                "energy_pool": ctx.somatic.energy_pool,
                "pain": ctx.somatic.pain,
                "load": ctx.somatic.load
            },
            social_summary={
                "rank": ctx.social.rank,
                "surveillance_load": ctx.social.surveillance_load
            }
        )
