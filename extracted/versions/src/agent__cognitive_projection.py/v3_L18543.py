# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L18543-L18820 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #91  lines=277  compile=OK
# kind: module  ident: agent/cognitive_projection.py  version: 3/7
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.1
模块：agent/cognitive_projection.py
职责：认知输入投影层 (Cognitive Input Projection Layer)。
建立显式白名单 DTO，杜绝 model_dump() 字段透传，消除 is_physically_feasible 真值泄露，
实现候选集规范化排序 (Canonicalization) 与快照哈希绑定。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field

from cmawse.agent.affordance import CandidateAffordance
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.intent import SubjectiveIntent
from cmawse.agent.representation import SubjectiveRepresentation
from cmawse.cognitive.memory import SubjectiveMemoryTrace
from cmawse.cognitive.rumor import RumorPacket


# ============================================================================
# 显式白名单 DTO (Strict Whitelist DTOs, extra="forbid")
# ============================================================================

class ProjectedCandidateDTO(BaseModel):
    """投影至大模型视界的可供性通道描述（只读、无内部地址、无物理真值泄露）"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    channel_id: str
    action_type: str
    actuator: str
    target_id: Optional[str] = None
    target_surface: str
    action_attribute: str
    narrative_status: str
    estimated_metabolic_joules: float


class ProjectedRepresentationDTO(BaseModel):
    """主观表征显式白名单 DTO"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    situation_type: str
    dominant_strain: str
    action_capacity_horizon: str
    confinement_mode: str
    salient_interface_ids: List[str]
    interpersonal_climate: str
    memory_resonance_refs: List[str]
    narrative_coherence_strain: str


class ProjectedCognitiveStateDTO(BaseModel):
    """内部心智状态显式白名单 DTO"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    active_concerns: List[Dict[str, Any]]
    interpersonal_expectations: Dict[str, Dict[str, Any]]
    learned_interface_resistance: Dict[str, Dict[str, Any]]
    deliberative_stance: str
    spatial_uncertainty: str
    relational_uncertainty: str


class ProjectedIntentDTO(BaseModel):
    """主观意向显式白名单 DTO"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_id: str
    origin_concern: str
    intended_transition: str
    urgency_mode: str
    scope: str
    persistence_ticks: int


class ProjectedMemoryDTO(BaseModel):
    """记忆显式白名单 DTO"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_ref: str
    recorded_tick: int
    subjective_rationalization: str
    salience_tags: List[str]


class ProjectedRumorDTO(BaseModel):
    """传闻显式白名单 DTO"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    origin_event_id: str
    hop_count: int
    gist: str


class ProjectedSomaticDTO(BaseModel):
    """生理状态显式白名单 DTO"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    energy_pool: float
    pain: float
    load: float


class ProjectedSocialDTO(BaseModel):
    """社交状态显式白名单 DTO"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    rank: int
    surveillance_load: float


class CognitiveMindContext(BaseModel):
    """
    大模型认知审议的唯一合法输入载荷（Strict Whitelist Payload）。
    完全通过显式 DTO 组装，严禁透传未经定义的内部字段。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_id: str
    tick: int
    candidate_set_hash: str
    subjective_representation: ProjectedRepresentationDTO
    internal_cognitive_state: ProjectedCognitiveStateDTO
    subjective_intents: List[ProjectedIntentDTO]
    available_candidates: List[ProjectedCandidateDTO]
    recalled_memories: List[ProjectedMemoryDTO]
    received_rumors: List[ProjectedRumorDTO]
    somatic_summary: ProjectedSomaticDTO
    social_summary: ProjectedSocialDTO


class CognitiveProjection:
    """认知输入投影器"""

    @classmethod
    def compute_candidate_set_hash(cls, candidates: List[CandidateAffordance]) -> str:
        """计算候选集的规范化哈希指纹（与输入列表顺序完全无关）"""
        sorted_ids = sorted(c.channel_id for c in candidates)
        raw_str = "|".join(sorted_ids)
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]

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
        # 1. 候选集规范化展示排序 (Canonicalization: 按 channel_id 稳定升序排列，消除顺序偏见)
        # 注意：此处只影响投影呈现顺序，严禁用于候选选择
        sorted_candidates = sorted(candidates, key=lambda c: c.channel_id)
        candidate_set_hash = cls.compute_candidate_set_hash(sorted_candidates)

        projected_candidates: List[ProjectedCandidateDTO] = []
        for c in sorted_candidates:
            projected_candidates.append(
                ProjectedCandidateDTO(
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

        # 2. 显式装配表征 DTO (禁止 model_dump 盲目透传)
        projected_rep = ProjectedRepresentationDTO(
            situation_type=rep.situation_type.value,
            dominant_strain=rep.somatic_appraisal.dominant_strain.value,
            action_capacity_horizon=rep.somatic_appraisal.action_capacity_horizon,
            confinement_mode=rep.spatial_appraisal.confinement_mode.value,
            salient_interface_ids=sorted(list(rep.spatial_appraisal.salient_interface_ids)),
            interpersonal_climate=rep.relational_appraisal.interpersonal_climate.value,
            memory_resonance_refs=list(rep.relational_appraisal.memory_resonance_refs),
            narrative_coherence_strain=rep.narrative_coherence_strain.value
        )

        # 3. 显式装配内部状态 DTO
        projected_state = ProjectedCognitiveStateDTO(
            active_concerns=[
                {
                    "domain": c.concern_domain.value,
                    "tension": c.underlying_unresolved_tension,
                    "intensity": c.felt_intensity.value
                }
                for c in state.active_concerns
            ],
            interpersonal_expectations={
                k: {
                    "stance": v.perceived_stance.value,
                    "debt": v.relational_debt.value,
                    "residue": v.recent_interaction_residue
                }
                for k, v in state.interpersonal_expectations.items()
            },
            learned_interface_resistance={
                k: {
                    "resistance": v.get("resistance_level", "UNKNOWN"),
                    "learned_tick": v.get("learned_tick", 0)
                }
                for k, v in state.learned_interface_resistance.items()
            },
            deliberative_stance=state.deliberative_stance.value,
            spatial_uncertainty=state.cognitive_uncertainty.spatial_uncertainty.value,
            relational_uncertainty=state.cognitive_uncertainty.relational_uncertainty.value
        )

        # 4. 显式装配意向 DTO
        projected_intents = [
            ProjectedIntentDTO(
                intent_id=i.intent_id,
                origin_concern=i.origin_concern.value,
                intended_transition=i.intended_transition.value,
                urgency_mode=i.urgency_mode.value,
                scope=i.scope.value,
                persistence_ticks=i.persistence_ticks
            )
            for i in intents
        ]

        # 5. 显式装配记忆与传闻 DTO
        projected_memories = [
            ProjectedMemoryDTO(
                event_ref=m.event_ref,
                recorded_tick=m.recorded_tick,
                subjective_rationalization=m.subjective_rationalization,
                salience_tags=list(m.salience_tags)
            )
            for m in memories
        ]

        projected_rumors = [
            ProjectedRumorDTO(
                origin_event_id=r.origin_event_id,
                hop_count=r.hop_count,
                gist=r.gist
            )
            for r in rumors
        ]

        # 6. 显式装配生理与社交概要
        projected_somatic = ProjectedSomaticDTO(
            energy_pool=ctx.somatic.energy_pool,
            pain=ctx.somatic.pain,
            load=ctx.somatic.load
        )

        projected_social = ProjectedSocialDTO(
            rank=ctx.social.rank,
            surveillance_load=ctx.social.surveillance_load
        )

        return CognitiveMindContext(
            agent_id=ctx.agent_id,
            tick=ctx.tick,
            candidate_set_hash=candidate_set_hash,
            subjective_representation=projected_rep,
            internal_cognitive_state=projected_state,
            subjective_intents=projected_intents,
            available_candidates=projected_candidates,
            recalled_memories=projected_memories,
            received_rumors=projected_rumors,
            somatic_summary=projected_somatic,
            social_summary=projected_social
        )
