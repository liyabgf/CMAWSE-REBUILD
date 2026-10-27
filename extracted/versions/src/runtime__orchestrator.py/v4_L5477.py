# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L5477-L5682 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #29  lines=205  compile=OK
# kind: module  ident: runtime/orchestrator.py  version: 4/4
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：runtime/orchestrator.py
职责：运行时调度总线。
强化信息主权边界：构建 DepoweredRenderingView 彻底剥离私有状态。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from cmawse.core.schema import (
    ActionProposal,
    GlobalWorldState,
    PhysicalEnvironmentSnapshot,
    Vector3D,
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


class DepoweredRenderingView(BaseModel):
    """
    去主权化文学渲染视界切片。
    严格物理白名单隔离：仅允许感知空间几何与客观物理现象，
    严禁泄露 Agent 的 Somatic 能量底牌、Social 阶层与 Self-Narrative 私有秘密。
    """
    model_config = ConfigDict(frozen=True)

    tick: int
    timestamp: str
    ambient_temperature: float
    ambient_lighting_lux: float = 300.0
    observable_spatial_bodies: Dict[str, Vector3D] = Field(
        default_factory=dict,
        description="在场肉身的外部宏观几何坐标"
    )


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
        rendering_observer_fn: Optional[Callable[[DepoweredRenderingView, VerifiedEventEntry], None]] = None
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
        self._pending_acoustic_emissions: List[Dict[str, Any]] = []

    @property
    def current_state(self) -> GlobalWorldState:
        return self._state

    def step(self) -> RuntimeCycleResult:
        current_tick = self._state.tick + 1
        current_time = f"TICK_TIME_{current_tick:06d}"

        # --------------------------------------------------------------------
        # STEP 1: 【势场与环境物理核算】 (Narrative Plane -> World Plane)
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
        # STEP 2: 【公共现实总线局域广播】 (World Plane -> Public-Reality-Bus)
        # --------------------------------------------------------------------
        for aid, agent in self._agents.items():
            if aid in world_for_tick.actors:
                agent.sync_physical_states(world_for_tick.actors[aid].somatic)

        horizons = self._bus.generate_horizons(
            world_state=world_for_tick,
            previous_tick_emissions=self._pending_acoustic_emissions
        )

        # --------------------------------------------------------------------
        # STEP 3: 【多主体沙盒推演】 (Agent Plane)
        # --------------------------------------------------------------------
        proposals: List[ActionProposal] = []
        for aid, agent in self._agents.items():
            horizon = horizons.get(aid)
            if not horizon:
                continue

            cues = list(horizon.visible_actors.keys()) + [em.get("content", "") for em in horizon.audible_emissions]
            mem_store = self._memory.get_or_create_store(aid)
            recalled = mem_store.retrieve_by_cues(cues)
            received_rumors = self._rumor.get_agent_rumors(aid)

            # 内部状态动力学演进
            agent.evolve_internal_state(
                recalled_memories=recalled,
                received_rumors=received_rumors,
                horizon=horizon
            )

            # 提议生成
            prop = agent.generate_proposal(tick=current_tick, horizon=horizon)
            proposals.append(prop)

        # --------------------------------------------------------------------
        # STEP 4: 【因果阻尼仲裁法庭审判】 (Causal Plane)
        # --------------------------------------------------------------------
        verified_event = self._arbiter.arbitrate_tick(
            tick=current_tick,
            timestamp=current_time,
            proposals=proposals,
            world_state=world_for_tick
        )

        # --------------------------------------------------------------------
        # STEP 5: 【事务试算与事实账本锁定】 (Ledger & State Commit)
        # --------------------------------------------------------------------
        staged_new_state = StateCommitter.apply_transaction(
            base_state=world_for_tick,
            patches=verified_event.state_patches,
            next_tick=current_tick,
            next_timestamp=current_time
        )
        self._ledger.append(verified_event)
        self._state = staged_new_state

        # --------------------------------------------------------------------
        # STEP 6: 【衍生系统隔离回写】 (Cognitive Plane)
        # --------------------------------------------------------------------
        witness_ids = self._bus.filter_witnesses(verified_event, world_for_tick, horizons)
        witness_horizons: Dict[str, PrivateHorizon] = {
            wid: horizons[wid] for wid in witness_ids if wid in horizons
        }
        witness_snapshots = {wid: world_for_tick.actors[wid] for wid in witness_ids if wid in world_for_tick.actors}

        # 仅目击者沉降有色主观记忆并播种传闻
        self._memory.settle_event_for_witnesses(verified_event, witness_horizons, witness_snapshots)
        for wid in witness_ids:
            self._rumor.seed_witness_rumor(wid, verified_event)
        self._rumor.step_propagation()

        # 锁存声学切片
        self._pending_acoustic_emissions = list(verified_event.acoustic_emissions)

        # --------------------------------------------------------------------
        # STEP 7 & 8: 【去主权化文学渲染】 (Rendering Plane 防火墙隔离)
        # --------------------------------------------------------------------
        if self._rendering_fn:
            depowered_view = DepoweredRenderingView(
                tick=current_tick,
                timestamp=current_time,
                ambient_temperature=self._state.environment.temperature,
                observable_spatial_bodies={aid: snap.position for aid, snap in self._state.actors.items()}
            )
            self._rendering_fn(depowered_view, verified_event)

        return RuntimeCycleResult(
            tick=current_tick,
            event=verified_event,
            state=self._state
        )
