# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L2774-L2962 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #14  lines=188  compile=OK
# kind: module  ident: runtime/orchestrator.py  version: 1/4
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：runtime/orchestrator.py
职责：Single-Tick Execution Pipeline 调度总线。
严格实现白皮书单步时钟循环调度规程 (STEP 1 至 STEP 8)，串联所有平面，维护数据主权。
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

from cmawse.core.schema import (
    ActionProposal,
    GlobalWorldState,
    PhysicalEnvironmentSnapshot,
    VerifiedEventEntry,
)
from cmawse.core.ledger import EventLedger
from cmawse.core.committer import StateCommitter
from cmawse.core.arbiter import CausalArbiter
from cmawse.world.bus import PublicRealityBus
from cmawse.agent.base import AgentEntity
from cmawse.cognitive.memory import MemorySystem
from cmawse.cognitive.rumor import RumorEngine


class NarrativePotentialModifier(BaseModel):
    """叙事平面可注入的引力势场偏置算子（控制论调节，非微观操纵）"""
    model_config = ConfigDict(frozen=True)

    delta_temp: float = 0.0
    delta_observation_pressure: float = 0.0
    injected_micro_entropy: Optional[float] = None


class RuntimeCycleResult(BaseModel):
    """单步执行结果报告（去主权数据交付物）"""
    model_config = ConfigDict(frozen=True)

    tick: int
    event: VerifiedEventEntry
    state: GlobalWorldState


class CMAWSERuntime:
    """CMAWSE 单步因果推进总控运行时"""

    def __init__(
        self,
        initial_state: GlobalWorldState,
        ledger: EventLedger,
        arbiter: CausalArbiter,
        reality_bus: PublicRealityBus,
        agents: Dict[str, AgentEntity],
        memory_system: MemorySystem,
        rumor_engine: RumorEngine,
        narrative_modifier_fn: Optional[Callable[[int, EventLedger], NarrativePotentialModifier]] = None,
        rendering_observer_fn: Optional[Callable[[GlobalWorldState, VerifiedEventEntry], None]] = None
    ) -> None:
        self._state = initial_state
        self._ledger = ledger
        self._arbiter = arbiter
        self._bus = reality_bus
        self._agents = agents
        self._memory = memory_system
        self._rumor = rumor_engine
        self._narrative_fn = narrative_modifier_fn or (lambda tick, l: NarrativePotentialModifier())
        self._rendering_fn = rendering_observer_fn

    @property
    def current_state(self) -> GlobalWorldState:
        return self._state

    def step(self) -> RuntimeCycleResult:
        """
        单步时钟循环不可分割事务：
        Step 1: 势场与环境物理核算
        Step 2: 公共现实总线局域广播
        Step 3: 多主体沙盒并行推演
        Step 4: 因果阻尼仲裁法庭审判
        Step 5: 事实主权账本锁定
        Step 6: 衍生系统并发回写 (State, Memory, Rumor)
        Step 7: 控制论大纲自愈对账 (Hook)
        Step 8: 去主权化文学渲染与脱水 (Hook)
        """
        current_tick = self._state.tick + 1
        current_time = f"TICK_TIME_{current_tick:06d}"

        # --------------------------------------------------------------------
        # STEP 1: 【势场与环境物理核算】(Narrative Plane -> World Plane)
        # --------------------------------------------------------------------
        pot_mod = self._narrative_fn(current_tick, self._ledger)
        new_temp = self._state.environment.temperature + pot_mod.delta_temp
        new_obs = max(0.0, min(1.0, self._state.environment.observation_pressure + pot_mod.delta_observation_pressure))
        new_entropy = pot_mod.injected_micro_entropy if pot_mod.injected_micro_entropy is not None else self._state.environment.micro_entropy_variable

        interim_env = PhysicalEnvironmentSnapshot(
            temperature=new_temp,
            observation_pressure=new_obs,
            friction_coefficient=self._state.environment.friction_coefficient,
            micro_entropy_variable=new_entropy,
            properties=self._state.environment.properties
        )
        world_for_tick = self._state.model_copy(update={"environment": interim_env})

        # --------------------------------------------------------------------
        # STEP 2: 【公共现实总线局域广播】(Public-Reality-Bus)
        # --------------------------------------------------------------------
        # 同步各沙盒身体状态镜像
        for aid, agent in self._agents.items():
            if aid in world_for_tick.actors:
                snap = world_for_tick.actors[aid]
                agent.sync_internal_states(snap.somatic, snap.social, snap.self_narrative)

        horizons = self._bus.generate_horizons(world_for_tick)

        # --------------------------------------------------------------------
        # STEP 3: 【多主体沙盒推演】(Distributed-Agent-Pool)
        # --------------------------------------------------------------------
        proposals: List[ActionProposal] = []
        for aid, agent in self._agents.items():
            horizon = horizons.get(aid)
            if not horizon:
                continue
            # 检索主体私有记忆线索
            cues = list(horizon.visible_actors.keys())
            mem_store = self._memory.get_or_create_store(aid)
            recalled = mem_store.retrieve_by_cues(cues)
            prop = agent.generate_proposal(
                tick=current_tick,
                horizon=horizon,
                memory_cues={"recalled_traces": recalled}
            )
            proposals.append(prop)

        # --------------------------------------------------------------------
        # STEP 4: 【因果阻尼仲裁法庭审判】(Causal-Arbiter-Core)
        # --------------------------------------------------------------------
        verified_event = self._arbiter.arbitrate_tick(
            tick=current_tick,
            timestamp=current_time,
            proposals=proposals,
            world_state=world_for_tick
        )

        # --------------------------------------------------------------------
        # STEP 5: 【事实主权账本锁定】(Event-Ledger-Store)
        # --------------------------------------------------------------------
        self._ledger.append(verified_event)

        # --------------------------------------------------------------------
        # STEP 6: 【衍生系统并发回写】
        # --------------------------------------------------------------------
        # Branch A: 全局物理状态原子更新
        updated_state = StateCommitter.apply_transaction(
            base_state=world_for_tick,
            patches=verified_event.state_patches,
            next_tick=current_tick,
            next_timestamp=current_time
        )
        self._state = updated_state

        # Branch B: 主体私有记忆沉降
        involved_actors = list(self._agents.keys())
        self._memory.settle_event(verified_event, involved_actors)

        # Branch C: 社会传闻演化与异步扩散
        for aid in involved_actors:
            self._rumor.inject_witness_event(aid, verified_event)
        self._rumor.step_propagation()

        # --------------------------------------------------------------------
        # STEP 7: 【控制论大纲自愈监测】 (Narrative Monitor 对账)
        # --------------------------------------------------------------------
        # 外部监控通过传入的 narrative_modifier_fn 闭环，历史已落槌不可篡改

        # --------------------------------------------------------------------
        # STEP 8: 【去主权化文学渲染与脱水】 (Rendering Hook)
        # --------------------------------------------------------------------
        if self._rendering_fn:
            self._rendering_fn(self._state, verified_event)

        return RuntimeCycleResult(
            tick=current_tick,
            event=verified_event,
            state=self._state
        )
