# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L13532-L13721 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #54  lines=189  compile=OK
# kind: module  ident: agent/generator.py  version: 2/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 2
模块：agent/generator.py
职责：可供性连续剪裁生成引擎。
严禁凭空捏造客体，所有接触界面必须源于真实感知到的空间实体或自身肉身表面。
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
from cmawse.agent.context import SubjectContext
from cmawse.core.schema import Vector3D


class AffordanceGenerator:
    """具身可供性连续剪裁生发引擎"""

    @classmethod
    def generate(cls, ctx: SubjectContext) -> List[CandidateAffordance]:
        candidates: List[CandidateAffordance] = []

        # --------------------------------------------------------------------
        # 1. 具身内部通道：姿态维持与节能休息（永远客观存在）
        # --------------------------------------------------------------------
        candidates.append(
            CandidateAffordance(
                channel_id=f"AFF_MAINTAIN_POSTURE_{ctx.agent_id}",
                action_type="MAINTAIN_POSTURE",
                actuator=ActuatorType.TORSO,
                target_surface=SurfaceType.FREE_SPACE,
                preconditions=AffordancePreconditions(requires_load_bearing=False, requires_free_path=False),
                action_attribute=ActionAttribute.REST_STILLNESS,
                estimated_metabolic_joules=1.0,
                is_physically_feasible=True
            )
        )

        # --------------------------------------------------------------------
        # 2. 地面与开阔连续空间可供性
        # --------------------------------------------------------------------
        candidates.append(
            CandidateAffordance(
                channel_id=f"AFF_LOCOMOTION_WALK_{ctx.agent_id}",
                action_type="LOCOMOTION_WALK",
                actuator=ActuatorType.DUAL_LEGS,
                target_surface=SurfaceType.GROUND_SURFACE,
                spatial_vector=Vector3D(x=1.0, y=0.0, z=0.0),
                preconditions=AffordancePreconditions(requires_load_bearing=True, requires_free_path=True),
                action_attribute=ActionAttribute.LOCOMOTION,
                estimated_metabolic_joules=8.0,
                is_physically_feasible=True
            )
        )

        # --------------------------------------------------------------------
        # 3. 真实感知到的客观空间物理客体可供性（无客体则绝对不生成通道）
        # --------------------------------------------------------------------
        for obj in ctx.perceived_objects:
            dist = ctx.horizon.self_position.distance_to(obj.position)
            if obj.object_type == "DOOR":
                # 无论开闭，门体提供物理把手交互界面
                candidates.append(
                    CandidateAffordance(
                        channel_id=f"AFF_INTERACT_DOOR_{obj.object_id}",
                        action_type="INTERACT_DOOR_MANIPULATE",
                        actuator=ActuatorType.DUAL_HANDS,
                        target_id=obj.object_id,
                        target_surface=SurfaceType.RIGID_HANDLE,
                        preconditions=AffordancePreconditions(
                            requires_load_bearing=False,
                            requires_contact=True,
                            max_reach_distance=2.0
                        ),
                        action_attribute=ActionAttribute.MECHANICAL_INTERACTION,
                        estimated_metabolic_joules=12.0,
                        is_physically_feasible=(dist <= 2.0)
                    )
                )
                # 仅当门处于开启可通行状态时，才存在跨门通道
                if obj.is_passable:
                    candidates.append(
                        CandidateAffordance(
                            channel_id=f"AFF_PASS_DOOR_{obj.object_id}",
                            action_type="PASS_THRESHOLD",
                            actuator=ActuatorType.DUAL_LEGS,
                            target_id=obj.object_id,
                            target_surface=SurfaceType.FREE_SPACE,
                            spatial_vector=Vector3D(x=obj.position.x - ctx.horizon.self_position.x, y=0.0, z=0.0),
                            preconditions=AffordancePreconditions(requires_load_bearing=True, requires_free_path=True),
                            action_attribute=ActionAttribute.LOCOMOTION,
                            estimated_metabolic_joules=10.0,
                            is_physically_feasible=True
                        )
                    )

        # --------------------------------------------------------------------
        # 4. 真实感知的在场他人人际交互通道
        # --------------------------------------------------------------------
        for actor_id, actor_pos in ctx.horizon.visible_actors.items():
            dist = ctx.horizon.self_position.distance_to(actor_pos)
            candidates.append(
                CandidateAffordance(
                    channel_id=f"AFF_INTERPERSONAL_ASSERT_{actor_id}",
                    action_type="ASSERT_POSTURE",
                    actuator=ActuatorType.VOCAL_TRACT,
                    target_id=actor_id,
                    target_surface=SurfaceType.AGENT_BODY,
                    preconditions=AffordancePreconditions(requires_load_bearing=False, requires_free_path=False),
                    action_attribute=ActionAttribute.INTERPERSONAL_ASSERTION,
                    estimated_metabolic_joules=4.0,
                    is_physically_feasible=True
                )
            )
            candidates.append(
                CandidateAffordance(
                    channel_id=f"AFF_INTERPERSONAL_RETREAT_{actor_id}",
                    action_type="RETREAT_STEP",
                    actuator=ActuatorType.DUAL_LEGS,
                    target_id=actor_id,
                    target_surface=SurfaceType.GROUND_SURFACE,
                    spatial_vector=Vector3D(x=-1.0, y=0.0, z=0.0),
                    preconditions=AffordancePreconditions(requires_load_bearing=True, requires_free_path=True),
                    action_attribute=ActionAttribute.INTERPERSONAL_DE_ESCALATION,
                    estimated_metabolic_joules=6.0,
                    is_physically_feasible=True
                )
            )

        # --------------------------------------------------------------------
        # 5. 具身能力剪裁：唯有物理力学失能能判定 is_physically_feasible = False
        # --------------------------------------------------------------------
        refined: List[CandidateAffordance] = []
        is_load_bearing_capable = not (ctx.somatic.variables.get("fracture", 0.0) > 0.0)

        for aff in candidates:
            feasible = aff.is_physically_feasible
            if aff.preconditions.requires_load_bearing and not is_load_bearing_capable:
                feasible = False
            refined.append(aff.model_copy(update={"is_physically_feasible": feasible}))

        # 若下肢失能，具身力学结构性衍生双臂匍匐通道
        if not is_load_bearing_capable:
            refined.append(
                CandidateAffordance(
                    channel_id=f"AFF_PRONE_CRAWL_{ctx.agent_id}",
                    action_type="PRONE_CRAWL",
                    actuator=ActuatorType.DUAL_HANDS,
                    target_surface=SurfaceType.GROUND_SURFACE,
                    spatial_vector=Vector3D(x=0.3, y=0.0, z=0.0),
                    preconditions=AffordancePreconditions(requires_load_bearing=False, requires_free_path=True),
                    action_attribute=ActionAttribute.LOCOMOTION,
                    estimated_metabolic_joules=12.0,
                    is_physically_feasible=True
                )
            )

        # --------------------------------------------------------------------
        # 6. 自我叙事定性标记 (Self-Narrative Meaning Inscription)
        # 严禁中文子串硬编码，基于主体的自洽取向结构进行关系定性
        # --------------------------------------------------------------------
        final_list: List[CandidateAffordance] = []
        posture = ctx.self_narrative.constants.get("relational_posture", "NEUTRAL")

        for aff in refined:
            valence = NarrativeValence.SUPPORTED
            if posture == "DEFIANT":
                # 对抗型主体：退让违背自我认同，对峙强化认同
                if aff.action_attribute == ActionAttribute.INTERPERSONAL_DE_ESCALATION:
                    valence = NarrativeValence.VIOLATING
                elif aff.action_attribute == ActionAttribute.INTERPERSONAL_ASSERTION:
                    valence = NarrativeValence.SUPPORTED
            elif posture == "ACCOMMODATING":
                # 顺从/避险型主体：退避符合自我认同，对峙激化矛盾构成紧张
                if aff.action_attribute == ActionAttribute.INTERPERSONAL_DE_ESCALATION:
                    valence = NarrativeValence.SUPPORTED
                elif aff.action_attribute == ActionAttribute.INTERPERSONAL_ASSERTION:
                    valence = NarrativeValence.TENSIONED

            final_list.append(aff.model_copy(update={"narrative_status": valence}))

        return final_list
