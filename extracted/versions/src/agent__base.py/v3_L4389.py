# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L4389-L4582 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #25  lines=193  compile=OK
# kind: module  ident: agent/base.py  version: 3/4
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：agent/base.py
职责：分布式 Agent 认知沙盒基类，实现 Memory/Rumor -> Internal State' -> Proposal 的真实闭环演化。
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


class StateDynamicsPolicy(Protocol):
    """可注入的 Agent 内部状态动态演化策略"""
    def evolve(
        self,
        current_somatic: SomaticState,
        current_social: SocialState,
        current_narrative: SelfNarrativeState,
        recalled_memories: List[Any],
        received_rumors: List[Any],
        horizon: PrivateHorizon
    ) -> tuple[SomaticState, SocialState, SelfNarrativeState]:
        ...


class DefaultStateDynamicsPolicy:
    """
    默认内部状态演化动力学：
    记忆创伤直接累积为心理防御失调 (dissonance) 与生理负荷 (load)。
    """

    def evolve(
        self,
        current_somatic: SomaticState,
        current_social: SocialState,
        current_narrative: SelfNarrativeState,
        recalled_memories: List[Any],
        received_rumors: List[Any],
        horizon: PrivateHorizon
    ) -> tuple[SomaticState, SocialState, SelfNarrativeState]:
        # 1. 记忆对内在自洽状态的冲击
        total_scar = sum(getattr(m, "emotional_scar", 0.0) for m in recalled_memories)
        new_dissonance = min(100.0, current_narrative.dissonance + total_scar * 0.4)

        # 2. 社会传闻对被监视感与社交压力的冲击
        rumor_pressure = len(received_rumors) * 5.0
        new_surveillance = min(1.0, current_social.surveillance_load + rumor_pressure * 0.01)

        # 3. 生理负荷微调
        new_load = min(100.0, current_somatic.load + total_scar * 0.1)

        evolved_somatic = current_somatic.model_copy(update={"load": new_load})
        evolved_social = current_social.model_copy(update={"surveillance_load": new_surveillance})
        evolved_narrative = current_narrative.model_copy(update={"dissonance": new_dissonance})

        return evolved_somatic, evolved_social, evolved_narrative


class DecisionPolicy(Protocol):
    """纯粹基于当前自身内部状态与局部视界的决策协议"""
    def evaluate(
        self,
        agent_id: str,
        tick: int,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState,
        horizon: PrivateHorizon
    ) -> ActionProposal:
        ...


class ClosedLoopInertiaPolicy:
    """
    基于做功阶梯的高阻尼决策：
    仅根据 Agent 当下内部状态张力判断是否跨越做功势垒。
    """

    def __init__(self, action_threshold: float = 35.0):
        self._action_threshold = action_threshold

    def evaluate(
        self,
        agent_id: str,
        tick: int,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState,
        horizon: PrivateHorizon
    ) -> ActionProposal:
        # 张力完全来自已经沉淀到主体内部状态的真实物理与心理变量
        total_tension = (
            somatic.load * 0.4
            + social.surveillance_load * 25.0
            + self_narrative.dissonance * 0.8
        )

        # 势垒拦截
        if total_tension < self._action_threshold:
            return ActionProposal(
                agent_id=agent_id,
                tick=tick,
                stage=ActionStage.TOPIC,
                is_silent_pass=True
            )

        # 产生微观动作提案
        target_candidate = next(iter(horizon.visible_actors.keys()), None)
        return ActionProposal(
            agent_id=agent_id,
            tick=tick,
            stage=ActionStage.ACTION,
            is_silent_pass=False,
            kinematics=KinematicIntent(
                target_id=target_candidate,
                applied_force=min(total_tension, somatic.energy_pool * 0.4),
                effective_mass=60.0,
                is_contact_action=False,
                action_type="POSTURE_SHIFT"
            )
        )


class AgentEntity:
    """Agent 沙盒实体"""

    def __init__(
        self,
        agent_id: str,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState,
        decision_policy: DecisionPolicy | None = None,
        dynamics_policy: StateDynamicsPolicy | None = None
    ) -> None:
        self.agent_id = agent_id
        self._somatic = somatic
        self._social = social
        self._self_narrative = self_narrative
        self._decision_policy = decision_policy or ClosedLoopInertiaPolicy()
        self._dynamics_policy = dynamics_policy or DefaultStateDynamicsPolicy()

    @property
    def somatic(self) -> SomaticState:
        return self._somatic

    @property
    def social(self) -> SocialState:
        return self._social

    @property
    def self_narrative(self) -> SelfNarrativeState:
        return self._self_narrative

    def sync_physical_states(self, somatic: SomaticState) -> None:
        """从 GlobalWorldState 同步由物理客观裁决带来的躯体改变（如做功能量扣减）"""
        self._somatic = somatic

    def evolve_internal_state(
        self,
        recalled_memories: List[Any],
        received_rumors: List[Any],
        horizon: PrivateHorizon
    ) -> None:
        """认知输入演变为本地内部状态（沙盒内部状态演进）"""
        self._somatic, self._social, self._self_narrative = self._dynamics_policy.evolve(
            self._somatic,
            self._social,
            self._self_narrative,
            recalled_memories,
            received_rumors,
            horizon
        )

    def generate_proposal(self, tick: int, horizon: PrivateHorizon) -> ActionProposal:
        """仅凭演化后的内部状态与局部视界产生提案"""
        return self._decision_policy.evaluate(
            agent_id=self.agent_id,
            tick=tick,
            somatic=self._somatic,
            social=self._social,
            self_narrative=self._self_narrative,
            horizon=horizon
        )
