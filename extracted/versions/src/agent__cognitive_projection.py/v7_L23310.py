# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L23310-L23677 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #110  lines=367  compile=OK
# kind: module  ident: agent/cognitive_projection.py  version: 7/7
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.1.5
模块：agent/cognitive_projection.py
职责：认知输入投影与不可变快照绑定。
强制实现全载荷递归不可变性（Frozen DTOs & Tuple 容器）；
严格执行主体可见引用过滤，并确保 Candidate Snapshot Hash 严格绑定过滤后快照。
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
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
    """不可变规范化候选快照 DTO（无内部真值泄漏）"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    channel_id: str
    action_type: str
    actuator: str
    target_id: Optional[str] = None
    target_surface: str
    action_attribute: str
    narrative_status: str
    estimated_metabolic_joules: float


class ProjectedConcernDTO(BaseModel):
    """不可变关切状态条目"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    domain: str
    tension: str
    intensity: str


class ProjectedInterpersonalExpectationDTO(BaseModel):
    """不可变人际预期条目"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    target_actor_id: str
    stance: str
    debt: str
    residue: str


class ProjectedInterfaceResistanceDTO(BaseModel):
    """不可变物理界面阻抗经验条目"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    interface_ref: str
    resistance_level: str
    learned_tick: int


class ProjectedRepresentationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    situation_type: str
    dominant_strain: str
    action_capacity_horizon: str
    confinement_mode: str
    salient_interface_ids: Tuple[str, ...]
    interpersonal_climate: str
    memory_resonance_refs: Tuple[str, ...]
    narrative_coherence_strain: str


class ProjectedCognitiveStateDTO(BaseModel):
    """真正递归不可变认知状态 DTO"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    active_concerns: Tuple[ProjectedConcernDTO, ...]
    interpersonal_expectations: Tuple[ProjectedInterpersonalExpectationDTO, ...]
    learned_interface_resistance: Tuple[ProjectedInterfaceResistanceDTO, ...]
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
    salience_tags: Tuple[str, ...]


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
    全字段递归不可变性保证（Frozen Pydantic DTOs + Tuple 集合）。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_id: str
    tick: int
    candidate_set_hash: str
    subjective_representation: ProjectedRepresentationDTO
    internal_cognitive_state: ProjectedCognitiveStateDTO
    subjective_intents: Tuple[ProjectedIntentDTO, ...]
    available_candidates: Tuple[ProjectedCandidateDTO, ...]
    recalled_memories: Tuple[ProjectedMemoryDTO, ...]
    received_rumors: Tuple[ProjectedRumorDTO, ...]
    somatic_summary: ProjectedSomaticDTO
    social_summary: ProjectedSocialDTO


class CognitiveProjection:
    """认知输入投影与快照哈希引擎"""

    @classmethod
    def compute_candidate_snapshot_hash(
        cls,
        candidates: List[CandidateAffordance] | List[ProjectedCandidateDTO] | Tuple[ProjectedCandidateDTO, ...] | Tuple[CandidateAffordance, ...]
    ) -> str:
        """
        计算候选集快照的 Canonical SHA-256 哈希值 (128-bit truncated)。
        保证严格输入检查与排列无关性。
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
        canonical_json = json.dumps(raw_list, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
        normalized_str = unicodedata.normalize('NFC', canonical_json)
        return hashlib.sha256(normalized_str.encode("utf-8")).hexdigest()[:32]

    @classmethod
    def compute_projection_hash(cls, payload: Dict[str, Any]) -> str:
        """计算完整 CognitiveMindContext 载荷的 Canonical SHA-256 指纹"""
        canonical_json = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
        normalized_str = unicodedata.normalize('NFC', canonical_json)
        return hashlib.sha256(normalized_str.encode("utf-8")).hexdigest()[:32]

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
        # 0. 提取主体视界内可感知的公开实体引用白名单
        visible_references: Set[str] = set(ctx.horizon.visible_actors.keys())
        for obj in ctx.perceived_interfaces:
            visible_references.add(obj.entity_id)

        # 1. 原始候选唯一性前置校验 (Duplicate channel_id Guard)
        seen_raw_ids: Set[str] = set()
        for c in candidates:
            if c.channel_id in seen_raw_ids:
                raise ValueError(f"Duplicate channel_id detected in raw candidates: '{c.channel_id}'")
            seen_raw_ids.add(c.channel_id)

        # 2. 主体可见引用过滤与规范 DTO 构造 (Subject-Visible Reference Filtering)
        filtered_dtos: List[ProjectedCandidateDTO] = []
        for c in candidates:
            # 严格红线：若 target_id 存在且未在主体视界可见白名单中，则过滤该候选
            if c.target_id is not None and c.target_id not in visible_references:
                continue

            if isinstance(c, ProjectedCandidateDTO):
                filtered_dtos.append(c)
            else:
                filtered_dtos.append(
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

        # 3. 规范排序并生成最终不可变快照 (Canonical Sorting & Immutable Tuple)
        sorted_candidates: Tuple[ProjectedCandidateDTO, ...] = tuple(
            sorted(filtered_dtos, key=lambda x: x.channel_id)
        )

        # 4. 关键：对最终确定的 available_candidates 快照计算唯一的 candidate_set_hash
        candidate_set_hash = cls.compute_candidate_snapshot_hash(sorted_candidates)

        # 5. 递归构建不可变投影 DTO
        projected_rep = ProjectedRepresentationDTO(
            situation_type=rep.situation_type.value,
            dominant_strain=rep.somatic_appraisal.dominant_strain.value,
            action_capacity_horizon=rep.somatic_appraisal.action_capacity_horizon,
            confinement_mode=rep.spatial_appraisal.confinement_mode.value,
            salient_interface_ids=tuple(sorted(list(rep.spatial_appraisal.salient_interface_ids))),
            interpersonal_climate=rep.relational_appraisal.interpersonal_climate.value,
            memory_resonance_refs=tuple(rep.relational_appraisal.memory_resonance_refs),
            narrative_coherence_strain=rep.narrative_coherence_strain.value
        )

        projected_concerns = tuple([
            ProjectedConcernDTO(
                domain=c.concern_domain.value,
                tension=c.underlying_unresolved_tension,
                intensity=c.felt_intensity.value
            )
            for c in state.active_concerns
        ])

        projected_interpersonal = tuple([
            ProjectedInterpersonalExpectationDTO(
                target_actor_id=k,
                stance=v.perceived_stance.value,
                debt=v.relational_debt.value,
                residue=v.recent_interaction_residue
            )
            for k, v in sorted(state.interpersonal_expectations.items(), key=lambda x: x[0])
            if k in visible_references
        ])

        # 对 learned_interface_resistance 进行语义审计与引用过滤：
        # 若 interface_ref 为特定实体标识符（包含下划线或以实体 ID 命名）且不在可见白名单内，则剔除
        projected_resistance = tuple([
            ProjectedInterfaceResistanceDTO(
                interface_ref=k,
                resistance_level=v.get("resistance_level", "UNKNOWN"),
                learned_tick=v.get("learned_tick", 0)
            )
            for k, v in sorted(state.learned_interface_resistance.items(), key=lambda x: x[0])
            if (not k.startswith("entity_") and not k.startswith("obj_")) or k in visible_references
        ])

        projected_state = ProjectedCognitiveStateDTO(
            active_concerns=projected_concerns,
            interpersonal_expectations=projected_interpersonal,
            learned_interface_resistance=projected_resistance,
            deliberative_stance=state.deliberative_stance.value,
            spatial_uncertainty=state.cognitive_uncertainty.spatial_uncertainty.value,
            relational_uncertainty=state.cognitive_uncertainty.relational_uncertainty.value
        )

        projected_intents = tuple([
            ProjectedIntentDTO(
                intent_id=i.intent_id,
                origin_concern=i.origin_concern.value,
                intended_transition=i.intended_transition.value,
                urgency_mode=i.urgency_mode.value,
                scope=i.scope.value,
                persistence_ticks=i.persistence_ticks
            )
            for i in intents
        ])

        projected_memories = tuple([
            ProjectedMemoryDTO(
                event_ref=m.event_ref,
                recorded_tick=m.recorded_tick,
                subjective_rationalization=m.subjective_rationalization,
                salience_tags=tuple(m.salience_tags)
            )
            for m in memories
        ])

        projected_rumors = tuple([
            ProjectedRumorDTO(
                origin_event_id=r.origin_event_id,
                hop_count=r.hop_count,
                gist=r.gist
            )
            for r in rumors
        ])

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
            available_candidates=sorted_candidates,
            recalled_memories=projected_memories,
            received_rumors=projected_rumors,
            somatic_summary=projected_somatic,
            social_summary=projected_social
        )
