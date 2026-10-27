# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L10570-L10761 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #40  lines=191  compile=OK
# kind: module  ident: agent/generator.py  version: 1/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 2
模块：agent/generator.py
职责：可供性连续剪裁生发生态引擎（Affordance Generator）。
严格遵循：空间投影 -> 身体能力 -> 场域制度 -> 叙事定性。
唯有物理/具身可行性拥有否决权，社会与叙事仅赋予定性标签。
"""

from __future__ import annotations

from typing import List
from cmawse.agent.affordance import (
    ActionAttribute,
    ActuatorType,
    AffordancePreconditions,
    CandidateAffordance,
    NarrativeValence,
    SurfaceType,
)
from cmawse.agent.context import SubjectContext, SituationalActivation
from cmawse.core.schema import Vector3D


class AffordanceGenerator:
    """具身可供性连续剪裁生发引擎"""

    @classmethod
    def generate(cls, ctx: SubjectContext) -> List[CandidateAffordance]:
        candidates: List[CandidateAffordance] = []

        # ====================================================================
        # 步骤 1: 空间几何接触面投影 (Physical Interface Projection)
        # ====================================================================
        # 1.1 常态身体基础通道：姿态维持与节能休息
        candidates.append(
            CandidateAffordance(
                channel_id="AFF_MAINTAIN_POSTURE",
                action_type="MAINTAIN_POSTURE",
                actuator=ActuatorType.TORSO,
                target_surface=SurfaceType.FREE_SPACE,
                preconditions=AffordancePreconditions(requires_load_bearing=False, requires_free_path=False),
                action_attribute=ActionAttribute.REST_STILLNESS,
                estimated_metabolic_joules=1.0,
                is_physically_feasible=True
            )
        )

        # 1.2 开阔空间移动通道
        candidates.append(
            CandidateAffordance(
                channel_id="AFF_LOCOMOTION_WALK",
                action_type="LOCOMOTION_WALK",
                actuator=ActuatorType.DUAL_LEGS,
                target_surface=SurfaceType.GROUND_SURFACE,
                spatial_vector=Vector3D(x=1.0, y=0.0, z=0.0),
                preconditions=AffordancePreconditions(requires_load_bearing=True, requires_free_path=True),
                action_attribute=ActionAttribute.LOCOMOTION,
                estimated_metabolic_joules=10.0,
                is_physically_feasible=True
            )
        )

        # 1.3 局部空间阻隔与门体交互通道
        if SituationalActivation.SPATIAL_BLOCKAGE in ctx.activations:
            candidates.append(
                CandidateAffordance(
                    channel_id="AFF_DOOR_SHAKE",
                    action_type="INTERACT_DOOR_SHAKE",
                    actuator=ActuatorType.DUAL_HANDS,
                    target_id="door_structure",
                    target_surface=SurfaceType.RIGID_HANDLE,
                    preconditions=AffordancePreconditions(requires_load_bearing=False, requires_contact=True),
                    action_attribute=ActionAttribute.MECHANICAL_INTERACTION,
                    estimated_metabolic_joules=15.0,
                    is_physically_feasible=True
                )
            )
            candidates.append(
                CandidateAffordance(
                    channel_id="AFF_SEARCH_TOOL",
                    action_type="SEARCH_TOOL",
                    actuator=ActuatorType.EYES_HEAD,
                    target_surface=SurfaceType.FREE_SPACE,
                    preconditions=AffordancePreconditions(requires_load_bearing=False, requires_free_path=False),
                    action_attribute=ActionAttribute.SOMATIC_MAINTENANCE,
                    estimated_metabolic_joules=5.0,
                    is_physically_feasible=True
                )
            )

        # 1.4 在场他人人际交互通道
        if ctx.horizon.visible_actors:
            nearest_id, nearest_pos = next(iter(ctx.horizon.visible_actors.items()))
            dist = ctx.horizon.self_position.distance_to(nearest_pos)

            # 对峙/发声通道
            candidates.append(
                CandidateAffordance(
                    channel_id=f"AFF_ASSERT_POSTURE_{nearest_id}",
                    action_type="ASSERT_POSTURE",
                    actuator=ActuatorType.VOCAL_TRACT,
                    target_id=nearest_id,
                    target_surface=SurfaceType.AGENT_BODY,
                    preconditions=AffordancePreconditions(requires_load_bearing=False, requires_free_path=False),
                    action_attribute=ActionAttribute.INTERPERSONAL_ASSERTION,
                    estimated_metabolic_joules=3.0,
                    is_physically_feasible=True
                )
            )
            # 退避通道
            candidates.append(
                CandidateAffordance(
                    channel_id=f"AFF_RETREAT_STEP_{nearest_id}",
                    action_type="RETREAT_STEP",
                    actuator=ActuatorType.DUAL_LEGS,
                    target_id=nearest_id,
                    target_surface=SurfaceType.GROUND_SURFACE,
                    spatial_vector=Vector3D(x=-1.0, y=0.0, z=0.0),
                    preconditions=AffordancePreconditions(requires_load_bearing=True, requires_free_path=True),
                    action_attribute=ActionAttribute.INTERPERSONAL_DE_ESCALATION,
                    estimated_metabolic_joules=8.0,
                    is_physically_feasible=True
                )
            )

        # ====================================================================
        # 步骤 2: 具身与空间能力剪裁 (Somatic & Spatial Feasibility)
        # 唯有此处有权将 is_physically_feasible 置为 False
        # ====================================================================
        refined_candidates: List[CandidateAffordance] = []
        is_load_bearing_capable = (ctx.somatic.pain < 60.0) and not (ctx.somatic.variables.get("fracture", 0.0) > 0.0)

        for aff in candidates:
            feasible = True
            # 双下肢承重检验
            if aff.preconditions.requires_load_bearing and not is_load_bearing_capable:
                feasible = False

            # 空间受阻时，向前的通行位移被物理否定
            if SituationalActivation.SPATIAL_BLOCKAGE in ctx.activations and aff.action_type == "LOCOMOTION_WALK":
                feasible = False

            # 若不可行，保留但标记物理不可执行
            if not feasible:
                aff = aff.model_copy(update={"is_physically_feasible": False})

            refined_candidates.append(aff)

        # 身体断裂时分发低位移替代通道
        if not is_load_bearing_capable:
            refined_candidates.append(
                CandidateAffordance(
                    channel_id="AFF_PRONE_CRAWL",
                    action_type="PRONE_CRAWL",
                    actuator=ActuatorType.DUAL_HANDS,
                    target_surface=SurfaceType.GROUND_SURFACE,
                    spatial_vector=Vector3D(x=0.2, y=0.0, z=0.0),
                    preconditions=AffordancePreconditions(requires_load_bearing=False, requires_free_path=True),
                    action_attribute=ActionAttribute.LOCOMOTION,
                    estimated_metabolic_joules=12.0,
                    is_physically_feasible=True
                )
            )

        # ====================================================================
        # 步骤 3: 叙事语义与意义标记 (Self-Narrative Inscription)
        # 绝不删除动作，仅标注 SUPPORTED / TENSIONED / VIOLATING
        # ====================================================================
        final_candidates: List[CandidateAffordance] = []
        core_belief = ctx.self_narrative.constants.get("core_belief", "")

        for aff in refined_candidates:
            valence = NarrativeValence.SUPPORTED

            # 尊严/硬汉型角色：退避为 VIOLATING，对峙为 SUPPORTED
            if "寸步不让" in core_belief or "体面" in core_belief or "绝不示弱" in core_belief:
                if aff.action_attribute == ActionAttribute.INTERPERSONAL_DE_ESCALATION:
                    valence = NarrativeValence.VIOLATING
                elif aff.action_attribute == ActionAttribute.INTERPERSONAL_ASSERTION:
                    valence = NarrativeValence.SUPPORTED

            # 避险/实用型角色：退避为 SUPPORTED，对峙硬刚为 TENSIONED
            elif "好汉不吃眼前亏" in core_belief or "生存第一" in core_belief or "自保" in core_belief:
                if aff.action_attribute == ActionAttribute.INTERPERSONAL_DE_ESCALATION:
                    valence = NarrativeValence.SUPPORTED
                elif aff.action_attribute == ActionAttribute.INTERPERSONAL_ASSERTION:
                    valence = NarrativeValence.TENSIONED

            final_candidates.append(aff.model_copy(update={"narrative_status": valence}))

        return final_candidates
