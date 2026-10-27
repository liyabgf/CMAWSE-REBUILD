# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L10865-L10947 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #42  lines=82  compile=OK
# kind: module  ident: agent/ladder.py  version: 1/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 2
模块：agent/ladder.py
职责：做功阶梯推进器 (Five-Stage Work Ladder)。
Affordance -> Intent -> Plan -> Commitment -> ActionProposal。
Agent 平面全程只读，Commitment 仅保存计划参数，实际能耗下发交由 Arbiter。
"""

from __future__ import annotations

from typing import Optional
from cmawse.agent.affordance import CandidateAffordance, SurfaceType
from cmawse.agent.context import SubjectContext
from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    KinematicIntent,
    Vector3D,
    VerbalIntent,
)


class FiveStageWorkLadder:
    """五阶段做功阶梯推进器"""

    @classmethod
    def escalate_to_proposal(
        cls,
        ctx: SubjectContext,
        affordance: Optional[CandidateAffordance]
    ) -> ActionProposal:
        # 若未选定通道，合法塌陷为静默观察
        if affordance is None:
            return ActionProposal(
                agent_id=ctx.agent_id,
                tick=ctx.tick,
                stage=ActionStage.TOPIC,
                is_silent_pass=True
            )

        # --------------------------------------------------------------------
        # 阶梯 2: Intent (意向确立)
        # --------------------------------------------------------------------
        # 阶梯 3: Plan (运动学规划)
        # --------------------------------------------------------------------
        applied_force = 15.0
        if affordance.action_type in ("LOCOMOTION_WALK", "RETREAT_STEP"):
            applied_force = 25.0
        elif affordance.action_type in ("INTERACT_DOOR_SHAKE", "ASSERT_POSTURE"):
            applied_force = 35.0
        elif affordance.action_type == "PRONE_CRAWL":
            applied_force = 10.0

        # --------------------------------------------------------------------
        # 阶梯 4: Commitment (动能动员承诺声明，不修改 Agent 自身状态)
        # --------------------------------------------------------------------
        is_contact = (affordance.target_surface != SurfaceType.FREE_SPACE)

        kinematics = KinematicIntent(
            target_id=affordance.target_id,
            applied_force=applied_force,
            effective_mass=65.0,
            intended_trajectory=affordance.spatial_vector,
            is_contact_action=is_contact,
            action_type=affordance.action_type
        )

        verbal = None
        if affordance.action_type == "ASSERT_POSTURE":
            verbal = VerbalIntent(content="退后！别靠过来！", intensity_db=70.0)

        # --------------------------------------------------------------------
        # 阶梯 5: ActionProposal (正式物理提案提交)
        # --------------------------------------------------------------------
        return ActionProposal(
            agent_id=ctx.agent_id,
            tick=ctx.tick,
            stage=ActionStage.ACTION,
            is_silent_pass=False,
            kinematics=kinematics,
            verbal=verbal
        )
