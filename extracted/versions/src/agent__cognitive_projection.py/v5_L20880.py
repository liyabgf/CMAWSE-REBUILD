# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L20880-L21187 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #101  lines=307  compile=OK
# kind: module  ident: agent/cognitive_projection.py  version: 5/7
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.1.2
模块：agent/cognitive_projection.py
职责：认知输入投影与不可变候选快照绑定。
强制使用 Tuple[ProjectedCandidateDTO, ...] 保证快照物理不可变性；
实施全属性 Canonical SHA-256 哈希，对重复 channel_id 执行 Fail-Closed 拒止。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict

from cmawse.agent.affordance import CandidateAffordance
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.context import SubjectContext
from cmawse.agent.intent import SubjectiveIntent
from cmawse.agent.representation import SubjectiveRepresentation
from cmawse.cognitive.memory import SubjectiveMemoryTrace
from cmawse.cognitive.rumor import RumorPacket


class ProjectedCandidateDTO(BaseModel):
    """不可变规范化候选快照 DTO"""
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
    model_config = ConfigDict(extra="forbid", frozen=True)

    active_concerns: List[Dict[str, Any]]
    interpersonal_expectations: Dict[str, Dict[str, Any]]
    learned_interface_resistance: Dict[str, Dict[str, Any]]
    deliberative_stance: str
    spatial_uncertainty: str
    relational_uncertainty: str


class ProjectedIntentDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_id: str
    origin_concern: str
    intended_transition: str
    urgency_mode: str
    scope: str
    persistence_ticks: int


class ProjectedMemoryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_ref: str
    recorded_tick: int
    subjective_rationalization: str
    salience_tags: List[str]


class ProjectedRumorDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    origin_event_id: str
    hop_count: int
    gist: str


class ProjectedSomaticDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    energy_pool: float
    pain: float
    load: float


class ProjectedSocialDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rank: int
    surveillance_load: float


class CognitiveMindContext(BaseModel):
    """
    大模型认知审议的唯一合法输入载荷。
    available_candidates 强制使用 Tuple 保障快照物理不可变性。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_id: str
    tick: int
    candidate_set_hash: str
    subjective_representation: ProjectedRepresentationDTO
    internal_cognitive_state: ProjectedCognitiveStateDTO
    subjective_intents: List[ProjectedIntentDTO]
    available_candidates: Tuple[ProjectedCandidateDTO, ...]
    recalled_memories: List[ProjectedMemoryDTO]
    received_rumors: List[ProjectedRumorDTO]
    somatic_summary: ProjectedSomaticDTO
    social_summary: ProjectedSocialDTO


class CognitiveProjection:
    """认知输入投影与快照哈希引擎"""

    @classmethod
    def compute_candidate_snapshot_hash(
        cls,
        candidates: List[CandidateAffordance] | List[ProjectedCandidateDTO] | Tuple[ProjectedCandidateDTO, ...]
    ) -> str:
        """
        计算候选集快照的 Canonical SHA-256 哈希值：
        1. 检查 channel_id 唯一性，若存在重复直接抛出 ValueError (Fail-Closed)；
        2. 转换为 ProjectedCandidateDTO；
        3. 按 channel_id 升序排列；
        4. 序列化为规范 JSON 字符串 (sort_keys=True, ensure_ascii=False, separators=(',', ':'))；
        5. 生成 SHA-256 (32 字符 hex 摘要)。
        """
        dtos: List[ProjectedCandidateDTO] = []
        seen_channel_ids: Set[str] = set()

        for c in candidates:
            cid = c.channel_id
            if cid in seen_channel_ids:
                raise ValueError(f"Duplicate channel_id detected in candidate snapshot: '{cid}'")
            seen_channel_ids.add(cid)

            if isinstance(c, ProjectedCandidateDTO):
                dtos.append(c)
            else:
                dtos.append(
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

        sorted_dtos = sorted(dtos, key=lambda x: x.channel_id)
        raw_list = [d.model_dump() for d in sorted_dtos]
        canonical_json = json.dumps(raw_list, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()[:32]

    @classmethod
    def compute_projection_hash(cls, payload: Dict[str, Any]) -> str:
        """计算完整 CognitiveMindContext 载荷的 Canonical SHA-256 指纹"""
        canonical_json = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()[:32]

    @classmethod
    def project(
        cls,
        ctx: SubjectContext,
        state: InternalCognitiveState,
        rep: SubjectiveRepresentation,
        intents: List[SubjectiveIntent],
        candidates: List[CandidateAffordance] | Tuple[CandidateAffordance, ...],
        memories: List[SubjectiveMemoryTrace],
        rumors: List[RumorPacket]
    ) -> CognitiveMindContext:
        # 1. 检查唯一性并计算规范哈希
        candidate_set_hash = cls.compute_candidate_snapshot_hash(list(candidates))

        # 2. 构造规范排序的不可变 Tuple 快照
        dtos: List[ProjectedCandidateDTO] = []
        for c in candidates:
            if isinstance(c, ProjectedCandidateDTO):
                dtos.append(c)
            else:
                dtos.append(
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
        immutable_sorted_candidates: Tuple[ProjectedCandidateDTO, ...] = tuple(sorted(dtos, key=lambda x: x.channel_id))

        # 3. 显式白名单组装各 DTO
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
            available_candidates=immutable_sorted_candidates,
            recalled_memories=projected_memories,
            received_rumors=projected_rumors,
            somatic_summary=projected_somatic,
            social_summary=projected_social
        )
