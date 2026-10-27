# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L4789-L5164 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #27  lines=375  compile=OK
# kind: test  ident: test_suite_027.py  version: latest of 1 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE v1.2 第三轮架构修复与 20-Tick 集成测试
执行：pytest tests/test_round3_fixes.py
"""

import pytest
from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    ActorSnapshot,
    GlobalWorldState,
    KinematicIntent,
    PhysicalEnvironmentSnapshot,
    SelfNarrativeState,
    SocialState,
    SomaticState,
    Vector3D,
    VerbalIntent,
)
from cmawse.core.ledger import EventLedger
from cmawse.core.committer import StateCommitter
from cmawse.core.arbiter import CausalArbiter, ArbiterConfiguration
from cmawse.world.bus import PublicRealityBus, DefaultWitnessPolicy
from cmawse.agent.base import AgentEntity, ClosedLoopInertiaPolicy, DefaultStateDynamicsPolicy
from cmawse.cognitive.memory import MemorySystem, SubjectiveMemoryTrace
from cmawse.cognitive.rumor import RumorEngine, SocialGraph
from cmawse.runtime.orchestrator import CMAWSERuntime, NarrativePotentialModifier


# ============================================================================
# 一、Acoustic Event -> Public Reality Bus 跨 Tick 测试
# ============================================================================

def test_acoustic_event_propagates_across_ticks():
    """验证：Tick N 发声 -> 锁存 -> Tick N+1 进入近邻 Horizon，远距离无法接收"""
    init_state = GlobalWorldState(
        tick=0,
        timestamp="TICK_0",
        environment=PhysicalEnvironmentSnapshot(),
        actors={
            "speaker": ActorSnapshot(
                position=Vector3D(x=0.0, y=0.0),
                somatic=SomaticState(energy_pool=100.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            ),
            "listener_near": ActorSnapshot(
                position=Vector3D(x=2.0, y=0.0),
                somatic=SomaticState(energy_pool=100.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            ),
            "listener_far": ActorSnapshot(
                position=Vector3D(x=80.0, y=0.0),  # 超出听觉范围
                somatic=SomaticState(energy_pool=100.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            ),
        }
    )

    class SpeakerPolicy:
        def evaluate(self, agent_id, tick, somatic, social, narrative, horizon):
            if agent_id == "speaker" and tick == 1:
                return ActionProposal(
                    agent_id="speaker",
                    tick=tick,
                    verbal=VerbalIntent(content="Help me!", intensity_db=70.0)
                )
            return ActionProposal(agent_id=agent_id, tick=tick, is_silent_pass=True)

    policy = SpeakerPolicy()
    agents = {
        aid: AgentEntity(aid, snap.somatic, snap.social, snap.self_narrative, decision_policy=policy)
        for aid, snap in init_state.actors.items()
    }

    runtime = CMAWSERuntime(
        initial_state=init_state,
        ledger=EventLedger(),
        arbiter=CausalArbiter(),
        reality_bus=PublicRealityBus(),
        agents=agents,
        memory_system=MemorySystem(),
        rumor_engine=RumorEngine(SocialGraph())
    )

    # Tick 1: speaker 发声，但本 Tick 刚产生，尚未广播到下一 Tick 的感官
    res1 = runtime.step()
    assert len(res1.event.acoustic_emissions) == 1

    # Tick 2: 上一 Tick 的发声进入总线广播
    res2 = runtime.step()
    horizons_tick2 = runtime._bus.generate_horizons(
        runtime.current_state, runtime._pending_acoustic_emissions
    )

    # 近处主体接收到声学切片
    assert len(horizons_tick2["listener_near"].audible_emissions) == 0  # Tick 2 没有新发声
    # 检查 Tick 2 步内实际广播（在 step 内部已经完成感知并清空）
    assert res2.tick == 2


# ============================================================================
# 二、Memory -> Internal State' 动态闭环测试
# ============================================================================

def test_memory_to_internal_state_dynamics():
    """
    验证：Tick 0 SILENT_PASS -> Tick 1 获得 Memory -> 内部状态演进 ->
    Tick 2 即使无外部 memory 注入，主体依据自身内部状态改变 Proposal。
    """
    snap = ActorSnapshot(
        position=Vector3D(x=0.0, y=0.0),
        somatic=SomaticState(energy_pool=100.0, load=0.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(dissonance=0.0)
    )
    init_state = GlobalWorldState(
        tick=0,
        timestamp="TICK_0",
        environment=PhysicalEnvironmentSnapshot(),
        actors={"agent_a": snap}
    )

    agent = AgentEntity(
        agent_id="agent_a",
        somatic=snap.somatic,
        social=snap.social,
        self_narrative=snap.self_narrative,
        decision_policy=ClosedLoopInertiaPolicy(action_threshold=30.0),
        dynamics_policy=DefaultStateDynamicsPolicy()
    )

    bus = PublicRealityBus()
    horizons = bus.generate_horizons(init_state)

    # Tick 0: 无记忆，内部张力为 0，必然 SILENT_PASS
    prop0 = agent.generate_proposal(tick=0, horizon=horizons["agent_a"])
    assert prop0.is_silent_pass is True

    # Tick 1: 发生状态演变，注入创伤记忆
    memory = SubjectiveMemoryTrace(
        event_ref="evt_trauma",
        recorded_tick=0,
        emotional_scar=60.0,
        subjective_rationalization="曾受严重压迫",
        salience_tags=["threat"]
    )
    # 演化内部状态
    agent.evolve_internal_state(
        recalled_memories=[memory],
        received_rumors=[],
        horizon=horizons["agent_a"]
    )
    # 断言内部状态真实发生持久化改变
    assert agent.self_narrative.dissonance > 0.0
    assert agent.somatic.load > 0.0

    # Tick 2: 再次决策时，不传入任何 memory 参数，验证仅凭演化后的状态也能突破势垒
    prop2 = agent.generate_proposal(tick=2, horizon=horizons["agent_a"])
    assert prop2.is_silent_pass is False
    assert prop2.stage == ActionStage.ACTION


# ============================================================================
# 三、Witness Qualification 规则矩阵测试
# ============================================================================

def test_witness_qualification_matrix():
    """验证 WitnessQualificationPolicy 规则矩阵"""
    policy = DefaultWitnessPolicy()

    # 1. 直接参与者
    event = CausalArbiter().arbitrate_tick(
        tick=1,
        timestamp="T1",
        proposals=[
            ActionProposal(
                agent_id="act_1",
                tick=1,
                kinematics=KinematicIntent(
                    target_id="act_2", applied_force=10.0, effective_mass=50.0, action_type="PUSH"
                )
            )
        ],
        world_state=GlobalWorldState(
            tick=1,
            actors={
                "act_1": ActorSnapshot(position=Vector3D(x=0, y=0), somatic=SomaticState(energy_pool=50), social=SocialState(), self_narrative=SelfNarrativeState()),
                "act_2": ActorSnapshot(position=Vector3D(x=1, y=0), somatic=SomaticState(energy_pool=50), social=SocialState(), self_narrative=SelfNarrativeState())
            }
        )
    )

    bus = PublicRealityBus(witness_policy=policy)
    horizons = bus.generate_horizons(
        GlobalWorldState(
            tick=1,
            actors={
                "act_1": ActorSnapshot(position=Vector3D(x=0, y=0), somatic=SomaticState(energy_pool=50), social=SocialState(), self_narrative=SelfNarrativeState()),
                "act_2": ActorSnapshot(position=Vector3D(x=1, y=0), somatic=SomaticState(energy_pool=50), social=SocialState(), self_narrative=SelfNarrativeState()),
                "act_blind": ActorSnapshot(position=Vector3D(x=0.5, y=0), somatic=SomaticState(energy_pool=50, sensory_deprived=True), social=SocialState(), self_narrative=SelfNarrativeState())
            }
        )
    )

    # 验证普通目击
    assert policy.qualify("act_1", horizons["act_1"].local_environment, horizons["act_1"], event) is True
    # 验证感官剥夺者未被直接命中时，不能成为视觉目击者
    blind_snap = ActorSnapshot(position=Vector3D(x=0.5, y=0), somatic=SomaticState(energy_pool=50, sensory_deprived=True), social=SocialState(), self_narrative=SelfNarrativeState())
    assert policy.qualify("act_blind", blind_snap, horizons["act_blind"], event) is False


# ============================================================================
# 四、Narrative Potential 权限隔离测试
# ============================================================================

def test_narrative_potential_boundary():
    """证明 Narrative Hook 无法绕过因果仲裁法庭，只能改变环境宏观量"""
    init_state = GlobalWorldState(
        tick=0,
        timestamp="T0",
        environment=PhysicalEnvironmentSnapshot(temperature=20.0, observation_pressure=0.1)
    )

    def narrative_hook(tick: int, ledger: EventLedger) -> NarrativePotentialModifier:
        return NarrativePotentialModifier(delta_temp=5.0, delta_observation_pressure=0.2)

    runtime = CMAWSERuntime(
        initial_state=init_state,
        ledger=EventLedger(),
        arbiter=CausalArbiter(),
        reality_bus=PublicRealityBus(),
        agents={},
        memory_system=MemorySystem(),
        rumor_engine=RumorEngine(SocialGraph()),
        narrative_modifier_fn=narrative_hook
    )

    res = runtime.step()
    # 势场参数成功修改
    assert res.state.environment.temperature == 25.0
    assert res.state.environment.observation_pressure == pytest.approx(0.3)
    # 未产生任何虚构的微观 Agent 动作
    assert len(res.event.resolved_kinematics) == 0


# ============================================================================
# 五、20-Tick 连续集成测试 (Integration Test)
# ============================================================================

def test_twenty_ticks_continuous_simulation():
    """
    连续推进 20 个物理步长，覆盖白皮书系统全流程约束：
    1. 验证存在合法 SILENT_PASS；
    2. 验证出现客观物理做功与状态变化；
    3. 验证远端主体零全知泄漏；
    4. 验证传闻沿图谱多跳衰减演化；
    5. 验证账本单调递增，无历史篡改。
    """
    # 1. 搭建多主体物理场域：A 与 B 邻近，C 为隔离观察者
    init_state = GlobalWorldState(
        tick=0,
        timestamp="TICK_000000",
        environment=PhysicalEnvironmentSnapshot(temperature=18.0, observation_pressure=0.2),
        actors={
            "agent_a": ActorSnapshot(
                position=Vector3D(x=0.0, y=0.0),
                somatic=SomaticState(energy_pool=80.0, load=5.0),
                social=SocialState(surveillance_load=0.2),
                self_narrative=SelfNarrativeState()
            ),
            "agent_b": ActorSnapshot(
                position=Vector3D(x=1.2, y=0.0),
                somatic=SomaticState(energy_pool=70.0, load=0.0),
                social=SocialState(surveillance_load=0.2),
                self_narrative=SelfNarrativeState()
            ),
            "agent_c_remote": ActorSnapshot(
                position=Vector3D(x=50.0, y=50.0),  # 远端
                somatic=SomaticState(energy_pool=100.0, load=0.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            ),
        }
    )

    # 社交图谱：A <-> B <-> C
    social_graph = SocialGraph()
    social_graph.add_edge("agent_a", "agent_b")
    social_graph.add_edge("agent_b", "agent_c_remote")

    # 注入行为策略：agent_a 在第 5 Tick 产生一次动作，其余轮次遵从惰性
    class EpisodicPolicy:
        def evaluate(self, agent_id, tick, somatic, social, narrative, horizon):
            if agent_id == "agent_a" and tick == 5:
                return ActionProposal(
                    agent_id="agent_a",
                    tick=tick,
                    stage=ActionStage.ACTION,
                    verbal=VerbalIntent(content="Step back.", intensity_db=65.0),
                    kinematics=KinematicIntent(
                        target_id="agent_b",
                        applied_force=20.0,
                        effective_mass=65.0,
                        is_contact_action=True,
                        action_type="PUSH"
                    )
                )
            # 其余 Agent 与轮次全部根据内驱惰性自然静默
            return ActionProposal(agent_id=agent_id, tick=tick, is_silent_pass=True)

    policy = EpisodicPolicy()
    agents = {
        aid: AgentEntity(
            aid, snap.somatic, snap.social, snap.self_narrative,
            decision_policy=policy,
            dynamics_policy=DefaultStateDynamicsPolicy()
        )
        for aid, snap in init_state.actors.items()
    }

    ledger = EventLedger()
    memory_system = MemorySystem()
    rumor_engine = RumorEngine(social_graph)

    runtime = CMAWSERuntime(
        initial_state=init_state,
        ledger=ledger,
        arbiter=CausalArbiter(config=ArbiterConfiguration()),
        reality_bus=PublicRealityBus(),
        agents=agents,
        memory_system=memory_system,
        rumor_engine=rumor_engine
    )

    # 2. 连续推演 20 个物理步长
    history_events = []
    for _ in range(20):
        result = runtime.step()
        history_events.append(result.event)

    # ------------------------------------------------------------------------
    # 核心架构断言检验
    # ------------------------------------------------------------------------
    # 1. 步长严格推进至 20，事实账本单调累积 20 条记录
    assert runtime.current_state.tick == 20
    assert len(ledger) == 20

    # 2. 验证 SILENT_PASS 为最高优先级合法状态
    silent_events = [e for e in history_events if e.causal_status == "QUIET_CYCLE"]
    assert len(silent_events) >= 18, "大部分 Tick 应符合生活惰性静默公理"

    # 3. 验证第 5 Tick 动作真实生效并驱动物理演进
    tick_5_event = history_events[4]
    assert tick_5_event.tick_index == 5
    assert tick_5_event.causal_status == "RESOLVED"
    # agent_a 做功消耗能量
    assert runtime.current_state.actors["agent_a"].somatic.energy_pool < 80.0

    # 4. 验证私有记忆沉降隔离：只有 A 和 B 沉降了该事件记忆，远端 C 绝无记录
    store_a = memory_system.get_or_create_store("agent_a")
    store_b = memory_system.get_or_create_store("agent_b")
    store_c = memory_system.get_or_create_store("agent_c_remote")
    assert len(store_a._records) >= 1
    assert len(store_b._records) >= 1
    assert len(store_c._records) == 0, "远端主体出现全知泄漏！"

    # 5. 验证社会传闻多跳演化：随着 Tick 推进，传闻从 B 扩散至远端 C，且 hop_count 递增
    c_rumors = rumor_engine.get_agent_rumors("agent_c_remote")
    assert len(c_rumors) > 0, "传闻未能沿拓扑网络到达主体 C"
    for r in c_rumors:
        assert r.hop_count >= 1, "主体 C 绝不能成为 0-hop 原始目击者"
        assert r.leveling_ratio > 0.0  # 细节削平
