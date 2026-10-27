# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L17974-L18093 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #88  lines=119  compile=OK
# kind: module  ident: agent/cognitive_projection.py  version: 2/7
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.0.1 Patch
模块：agent/cognitive_projection.py
修复：彻底切除内部的 candidate 物理可行性过滤逻辑。
Projection 仅负责数据降维投影，绝不拥有候选裁剪主权。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

from cmawse.agent.affordance import CandidateAffordance
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.intent import SubjectiveIntent
from cmawse.agent.representation import SubjectiveRepresentation
from cmawse.cognitive.memory import SubjectiveMemoryTrace
from cmawse.cognitive.rumor import RumorPacket


class ProjectedCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    channel_id: str
    action_type: str
    actuator: str
    target_id: Optional[str] = None
    target_surface: str
    action_attribute: str
    narrative_status: str
    estimated_metabolic_joules: float
    is_physically_feasible: bool


class CognitiveMindContext(BaseModel):
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
        # 严格无损投影传入的所有候选通道，绝不在投影层进行物理过滤或静默删除
        projected_candidates: List[ProjectedCandidate] = []
        for c in candidates:
            projected_candidates.append(
                ProjectedCandidate(
                    channel_id=c.channel_id,
                    action_type=c.action_type,
                    actuator=c.actuator.value,
                    target_id=c.target_id,
                    target_surface=c.target_surface.value,
                    action_attribute=c.action_attribute.value,
                    narrative_status=c.narrative_status.value,
                    estimated_metabolic_joules=c.estimated_metabolic_joules,
                    is_physically_feasible=c.is_physically_feasible
                )
            )

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
