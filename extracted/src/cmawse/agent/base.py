# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L10953-L11083 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #43  lines=130  compile=OK
# kind: module  ident: agent/base.py  version: latest of 4 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 2
模块：agent/base.py
职责：Agent 宿主容器。全面拥抱 Phase 2 Affordance 架构，
彻底切除 total_tension 与硬编码 POSTURE_SHIFT。
保留历史类名符号以向下兼容既有测试导入。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from cmawse.agent.affordance import CandidateAffordance
from cmawse.agent.context import SubjectContext
from cmawse.agent.generator import AffordanceGenerator
from cmawse.agent.ladder import FiveStageWorkLadder
from cmawse.agent.selector import SubjectiveSelector
from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    SelfNarrativeState,
    SocialState,
    SomaticState,
)
from cmawse.world.bus import PrivateHorizon


class AgentEntity:
    """Agent 沙盒实体（Phase 2 完整合规实现）"""

    def __init__(
        self,
        agent_id: str,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState,
        decision_policy: Any = None,
        dynamics_policy: Any = None
    ) -> None:
        self.agent_id = agent_id
        self._somatic = somatic
        self._social = social
        self._self_narrative = self_narrative

        # 行为追踪与行动惯性记录
        self._last_action_failed = False
        self._last_action_type: Optional[str] = None
        self._recalled_memories: List[Any] = []
        self._received_rumors: List[Any] = []

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
        """物理世界事实落槌后，从 GlobalWorldState 单向同步生理状态"""
        self._somatic = somatic

    def record_action_feedback(self, failed: bool, action_type: Optional[str]) -> None:
        """记录上一次物理执行的因果反馈，影响下一 Tick 的行动连续性"""
        self._last_action_failed = failed
        self._last_action_type = action_type

    def evolve_internal_state(
        self,
        recalled_memories: List[Any],
        received_rumors: List[Any],
        horizon: PrivateHorizon
    ) -> None:
        """缓存认知输入，用于 SubjectContext 装配"""
        self._recalled_memories = list(recalled_memories)
        self._received_rumors = list(received_rumors)

    def generate_proposal(self, tick: int, horizon: PrivateHorizon) -> ActionProposal:
        """
        Phase 2 具身可供性决策流水线核心入口：
        Context -> Affordance Generation -> Selection -> Work Ladder -> ActionProposal
        """
        # 1. 装配 Subject Context
        ctx = SubjectContext.assemble(
            agent_id=self.agent_id,
            tick=tick,
            somatic=self._somatic,
            social=self._social,
            self_narrative=self._self_narrative,
            horizon=horizon,
            recalled_memories=self._recalled_memories,
            received_rumors=self._received_rumors,
            last_action_failed=self._last_action_failed,
            last_action_type=self._last_action_type
        )

        # 2. 具身可供性连续剪裁生成
        candidates = AffordanceGenerator.generate(ctx)

        # 3. 定性消歧选择
        selected = SubjectiveSelector.select(ctx, candidates)

        # 4. 做功阶梯推进至物理提交
        proposal = FiveStageWorkLadder.escalate_to_proposal(ctx, selected)

        # 记录本次计划动作类型
        if proposal.kinematics:
            self._last_action_type = proposal.kinematics.action_type
        else:
            self._last_action_type = None

        return proposal


# ============================================================================
# 向下兼容历史测试套件的接口重定向与适配层 (不含任何旧标量公式)
# ============================================================================

class ClosedLoopInertiaPolicy:
    """仅作为兼容历史符号导入的包装类"""
    def __init__(self, action_threshold: float = 35.0) -> None:
        pass


class DefaultStateDynamicsPolicy:
    """仅作为兼容历史符号导入的包装类"""
    pass
