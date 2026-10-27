# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L2423-L2568 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #11  lines=145  compile=OK
# kind: module  ident: agent/base.py  version: 1/4
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：agent/base.py
职责：分布式 Agent 认知沙盒基类与提案发生器。
基于 Somatic/Social/Self-Narrative 内驱变量运转。
决策模型由协议完全解耦注入（支持规则模型与可插拔 LLM 适配器），强制支持 ACTION: SILENT_PASS。
"""

from __future__ import annotations

from typing import Any, Dict, Protocol
from pydantic import BaseModel, ConfigDict, Field

from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    SelfNarrativeState,
    SocialState,
    SomaticState,
)
from cmawse.world.bus import PrivateHorizon


class DecisionPolicy(Protocol):
    """
    可注入的 Agent 决策策略协议。
    既可以是可插拔的本地 LLM (如 Ollama Qwen-2.5-14B) 适配器，
    也可以是形式化状态机或规则动力学模型。
    """
    def evaluate(
        self,
        agent_id: str,
        tick: int,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState,
        horizon: PrivateHorizon,
        memory_cues: Dict[str, Any]
    ) -> ActionProposal:
        ...


class LivingInertiaPolicy:
    """
    默认高阻尼惰性决策策略（遵循做功阶梯公理 3 与零事件轮公理 4）：
    内驱张力低于临界势垒时，强制输出 SILENT_PASS，绝不反向表演戏剧冲突。
    """

    def __init__(self, action_threshold: float = 30.0):
        self._action_threshold = action_threshold

    def evaluate(
        self,
        agent_id: str,
        tick: int,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState,
        horizon: PrivateHorizon,
        memory_cues: Dict[str, Any]
    ) -> ActionProposal:
        # 计算内部张力 (Tension)：由躯体负荷、规制压力和认知失调耦合构成
        internal_tension = (
            somatic.load * 0.4
            + social.surveillance_load * 30.0
            + self_narrative.dissonance * 0.3
        )

        # 惰性过滤：张力不足，直接静默
        if internal_tension < self._action_threshold:
            return ActionProposal(
                agent_id=agent_id,
                tick=tick,
                stage=ActionStage.TOPIC,
                is_silent_pass=True
            )

        # 超过阈值仅作为示例提议（具体行为由具体注入策略接管）
        return ActionProposal(
            agent_id=agent_id,
            tick=tick,
            stage=ActionStage.COMMITMENT,
            is_silent_pass=True  # 默认保底依旧安全挂起
        )


class AgentEntity:
    """
    Agent 认知实体：独立、沙盒化、无直接写权限。
    仅依据自身私有数据产生 ActionProposal。
    """

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
        self._policy = decision_policy or LivingInertiaPolicy()

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
        """从已生效的 GlobalWorldState 快照中同步物理身体状态（单向同步）"""
        self._somatic = somatic
        self._social = social
        self._self_narrative = self_narrative

    def generate_proposal(
        self,
        tick: int,
        horizon: PrivateHorizon,
        memory_cues: Dict[str, Any] | None = None
    ) -> ActionProposal:
        """主权受限的动作提议入口：无权直接生效，仅提交 Proposal"""
        return self._policy.evaluate(
            agent_id=self.agent_id,
            tick=tick,
            somatic=self._somatic,
            social=self._social,
            self_narrative=self._self_narrative,
            horizon=horizon,
            memory_cues=memory_cues or {}
        )
