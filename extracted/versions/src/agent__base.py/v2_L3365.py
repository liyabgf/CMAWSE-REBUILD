# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L3365-L3507 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #19  lines=142  compile=OK
# kind: module  ident: agent/base.py  version: 2/4
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：agent/base.py
职责：实现 Memory -> Internal State Tension -> Proposal 的真实闭环。
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol
from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    KinematicIntent,
    SelfNarrativeState,
    SocialState,
    SomaticState,
)
from cmawse.world.bus import PrivateHorizon


class DecisionPolicy(Protocol):
    def evaluate(
        self,
        agent_id: str,
        tick: int,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState,
        horizon: PrivateHorizon,
        recalled_memories: List[Any]
    ) -> ActionProposal:
        ...


class ClosedLoopInertiaPolicy:
    """
    闭环高阻尼惰性决策策略：
    当召回创伤记忆时，直接放大心理张力与神经负荷，突破静默势垒产生抵抗性提案。
    """

    def __init__(self, action_threshold: float = 40.0):
        self._action_threshold = action_threshold

    def evaluate(
        self,
        agent_id: str,
        tick: int,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState,
        horizon: PrivateHorizon,
        recalled_memories: List[Any]
    ) -> ActionProposal:
        # 1. 记忆对内在张力的动力学加权
        memory_scar_weight = sum(getattr(m, "emotional_scar", 0.0) for m in recalled_memories)

        # 2. 耦合计算瞬时总心理-生理张力 (Total Tension)
        total_tension = (
            somatic.load * 0.3
            + social.surveillance_load * 20.0
            + self_narrative.dissonance * 0.2
            + memory_scar_weight * 1.5  # 记忆真实注入张力
        )

        # 3. 未突破势垒，绝对服从静默惰性
        if total_tension < self._action_threshold:
            return ActionProposal(
                agent_id=agent_id,
                tick=tick,
                stage=ActionStage.TOPIC,
                is_silent_pass=True
            )

        # 4. 突破势垒：在场有威胁目标时，尝试执行回避/防御性做功
        target_candidate = next(iter(horizon.visible_actors.keys()), None)
        return ActionProposal(
            agent_id=agent_id,
            tick=tick,
            stage=ActionStage.ACTION,
            is_silent_pass=False,
            kinematics=KinematicIntent(
                target_id=target_candidate,
                applied_force=min(total_tension, somatic.energy_pool * 0.5),
                effective_mass=60.0,
                is_contact_action=False,
                action_type="EVADE_OR_DEFEND"
            )
        )


class AgentEntity:
    def __init__(
        self,
        agent_id: str,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState,
        decision_policy: DecisionPolicy | None = None
    ) -> None:
        self.agent_id = agent_id
        self._somatic = somatic
        self._social = social
        self._self_narrative = self_narrative
        self._policy = decision_policy or ClosedLoopInertiaPolicy()

    @property
    def somatic(self) -> SomaticState:
        return self._somatic

    @property
    def social(self) -> SocialState:
        return self._social

    @property
    def self_narrative(self) -> SelfNarrativeState:
        return self._self_narrative

    def sync_internal_states(
        self,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState
    ) -> None:
        self._somatic = somatic
        self._social = social
        self._self_narrative = self_narrative

    def generate_proposal(
        self,
        tick: int,
        horizon: PrivateHorizon,
        recalled_memories: List[Any] | None = None
    ) -> ActionProposal:
        return self._policy.evaluate(
            agent_id=self.agent_id,
            tick=tick,
            somatic=self._somatic,
            social=self._social,
            self_narrative=self._self_narrative,
            horizon=horizon,
            recalled_memories=recalled_memories or []
        )
