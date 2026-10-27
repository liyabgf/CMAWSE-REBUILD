# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L13834-L13955 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #56  lines=121  compile=OK
# kind: module  ident: agent/ladder.py  version: 2/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 2
模块：agent/ladder.py
职责：五阶段做功阶梯推进器 (Five-Stage Work Ladder)。
明确表达做功阶梯的具身参数具象化过程，坚守 Agent 零世界写权限边界。
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict
from cmawse.agent.affordance import CandidateAffordance, SurfaceType
from cmawse.agent.context import SubjectContext
from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    KinematicIntent,
    Vector3D,
    VerbalIntent,
)


class SubjectiveIntent(BaseModel):
    """阶梯 2: 确立的主观意图状态"""
    model_config = ConfigDict(frozen=True)
    target_id: Optional[str]
    intent_mode: str


class BodilyPlan(BaseModel):
    """阶梯 3: 运动学具身规划"""
    model_config = ConfigDict(frozen=True)
    actuator: str
    target_surface: str
    trajectory: Vector3D
    planned_force: float


class PledgedCommitment(BaseModel):
    """阶梯 4: 动能动员承诺契约（计划参数，非世界状态）"""
    model_config = ConfigDict(frozen=True)
    pledged_energy_joules: float
    is_committed: bool = True


class FiveStageWorkLadder:
    """做功阶梯形式化推进器"""

    @classmethod
    def escalate_to_proposal(
        cls,
        ctx: SubjectContext,
        affordance: Optional[CandidateAffordance]
    ) -> ActionProposal:
        # 未选定通道时，合法塌陷为静止观察 (SILENT_PASS)
        if affordance is None:
            return ActionProposal(
                agent_id=ctx.agent_id,
                tick=ctx.tick,
                stage=ActionStage.TOPIC,
                is_silent_pass=True
            )

        # --------------------------------------------------------------------
        # 阶梯 2: Intent (目标意向确立)
        # --------------------------------------------------------------------
        intent = SubjectiveIntent(
            target_id=affordance.target_id,
            intent_mode=affordance.action_attribute.value
        )

        # --------------------------------------------------------------------
        # 阶梯 3: Plan (运动学轨迹具象化)
        # --------------------------------------------------------------------
        planned_force = 10.0
        if affordance.action_type in ("LOCOMOTION_WALK", "RETREAT_STEP"):
            planned_force = 20.0
        elif affordance.action_type in ("INTERACT_DOOR_MANIPULATE", "ASSERT_POSTURE"):
            planned_force = 30.0

        plan = BodilyPlan(
            actuator=affordance.actuator.value,
            target_surface=affordance.target_surface.value,
            trajectory=affordance.spatial_vector,
            planned_force=planned_force
        )

        # --------------------------------------------------------------------
        # 阶梯 4: Commitment (动能动员承诺声明：只读声明，不改自身能量槽)
        # --------------------------------------------------------------------
        commitment = PledgedCommitment(
            pledged_energy_joules=affordance.estimated_metabolic_joules,
            is_committed=True
        )

        # --------------------------------------------------------------------
        # 阶梯 5: ActionProposal (正式物理提案组装提交)
        # --------------------------------------------------------------------
        is_contact = (affordance.target_surface != SurfaceType.FREE_SPACE)

        kinematics = KinematicIntent(
            target_id=intent.target_id,
            applied_force=plan.planned_force,
            effective_mass=65.0,
            intended_trajectory=plan.trajectory,
            is_contact_action=is_contact,
            action_type=affordance.action_type
        )

        verbal = None
        if affordance.action_type == "ASSERT_POSTURE":
            verbal = VerbalIntent(content="站住！别再靠近！", intensity_db=70.0)

        return ActionProposal(
            agent_id=ctx.agent_id,
            tick=ctx.tick,
            stage=ActionStage.ACTION,
            is_silent_pass=False,
            kinematics=kinematics,
            verbal=verbal
        )
