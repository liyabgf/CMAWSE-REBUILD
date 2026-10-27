# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L3715-L3891 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #22  lines=176  compile=OK
# kind: module  ident: runtime/orchestrator.py  version: 2/4
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：runtime/orchestrator.py
职责：调度总线。严格执行事务时序与目击隔离。
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
from cmawse.world.bus import PublicRealityBus, PrivateHorizon
from cmawse.agent.base import AgentEntity
from cmawse.cognitive.memory import MemorySystem
from cmawse.cognitive.rumor import RumorEngine


class NarrativePotentialModifier(BaseModel):
    model_config = ConfigDict(frozen=True)

    delta_temp: float = 0.0
    delta_observation_pressure: float = 0.0
    injected_micro_entropy: Optional[float] = None


class RuntimeCycleResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    tick: int
    event: VerifiedEventEntry
    state: GlobalWorldState


class CMAWSERuntime:
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
        current_tick = self._state.tick + 1
        current_time = f"TICK_TIME_{current_tick:06d}"

        # --------------------------------------------------------------------
        # STEP 1: 【势场与环境物理核算】
        # --------------------------------------------------------------------
        pot_mod = self._narrative_fn(current_tick, self._ledger)
        interim_env = PhysicalEnvironmentSnapshot(
            temperature=self._state.environment.temperature + pot_mod.delta_temp,
            observation_pressure=max(0.0, min(1.0, self._state.environment.observation_pressure + pot_mod.delta_observation_pressure)),
            friction_coefficient=self._state.environment.friction_coefficient,
            micro_entropy_variable=(
                pot_mod.injected_micro_entropy
                if pot_mod.injected_micro_entropy is not None
                else self._state.environment.micro_entropy_variable
            ),
            properties=self._state.environment.properties
        )
        world_for_tick = self._state.model_copy(update={"environment": interim_env})

        # --------------------------------------------------------------------
        # STEP 2: 【公共现实总线局域广播】
        # --------------------------------------------------------------------
        for aid, agent in self._agents.items():
            if aid in world_for_tick.actors:
                snap = world_for_tick.actors[aid]
                agent.sync_internal_states(snap.somatic, snap.social, snap.self_narrative)

        horizons = self._bus.generate_horizons(world_for_tick)

        # --------------------------------------------------------------------
        # STEP 3: 【多主体沙盒并行推演】(Memory -> Drive -> Proposal 闭环)
        # --------------------------------------------------------------------
        proposals: List[ActionProposal] = []
        for aid, agent in self._agents.items():
            horizon = horizons.get(aid)
            if not horizon:
                continue

            # 基于局部视觉/声学检索私有记忆
            cues = list(horizon.visible_actors.keys())
            mem_store = self._memory.get_or_create_store(aid)
            recalled = mem_store.retrieve_by_cues(cues)

            # 驱动提案生成
            prop = agent.generate_proposal(
                tick=current_tick,
                horizon=horizon,
                recalled_memories=recalled
            )
            proposals.append(prop)

        # --------------------------------------------------------------------
        # STEP 4: 【因果阻尼仲裁法庭审判】
        # --------------------------------------------------------------------
        verified_event = self._arbiter.arbitrate_tick(
            tick=current_tick,
            timestamp=current_time,
            proposals=proposals,
            world_state=world_for_tick
        )

        # --------------------------------------------------------------------
        # 事务性关键修复：状态演进先行检验 (Staging Verification)
        # --------------------------------------------------------------------
        # 在事实入账前，验证补丁是否能完全无痛原子应用
        staged_new_state = StateCommitter.apply_transaction(
            base_state=world_for_tick,
            patches=verified_event.state_patches,
            next_tick=current_tick,
            next_timestamp=current_time
        )

        # --------------------------------------------------------------------
        # STEP 5: 【事实主权账本锁定】(通过检验后方可入账)
        # --------------------------------------------------------------------
        self._ledger.append(verified_event)
        self._state = staged_new_state

        # --------------------------------------------------------------------
        # STEP 6: 【衍生系统隔离回写】(严格限制 Witness)
        # --------------------------------------------------------------------
        witness_ids = self._bus.filter_witnesses(verified_event, horizons)
        witness_horizons: Dict[str, PrivateHorizon] = {
            wid: horizons[wid] for wid in witness_ids if wid in horizons
        }

        # Branch B: 仅对真实在场目击者沉降记忆
        self._memory.settle_event_for_witnesses(verified_event, witness_horizons)

        # Branch C: 仅由真实目击者在社交拓扑播种初始传闻
        for wid in witness_ids:
            self._rumor.seed_witness_rumor(wid, verified_event)
        self._rumor.step_propagation()

        # --------------------------------------------------------------------
        # STEP 7 & 8: 外部观察 Hooks
        # --------------------------------------------------------------------
        if self._rendering_fn:
            self._rendering_fn(self._state, verified_event)

        return RuntimeCycleResult(
            tick=current_tick,
            event=verified_event,
            state=self._state
        )
