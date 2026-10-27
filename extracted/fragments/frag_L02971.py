# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L2971-L3103 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #15  lines=132  compile=OK
# kind: fragment  ident: frag_L02971.py
# edits: none. Header comment is the only addition.
# ======================
"""
测试验证：CMAWSE v1.2 运行时单步循环与全平面联动
执行：pytest tests/test_runtime_cycle.py
"""

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
from cmawse.core.arbiter import CausalArbiter, ArbiterConfiguration
from cmawse.world.bus import PublicRealityBus
from cmawse.agent.base import AgentEntity, DecisionPolicy
from cmawse.cognitive.memory import MemorySystem
from cmawse.cognitive.rumor import RumorEngine, SocialGraph
from cmawse.runtime.orchestrator import CMAWSERuntime, NarrativePotentialModifier


class CustomActivePolicy:
    """用于测试的主动型决策注入策略"""
    def evaluate(self, agent_id, tick, somatic, social, self_narrative, horizon, memory_cues):
        if agent_id == "actor_active":
            return ActionProposal(
                agent_id=agent_id,
                tick=tick,
                stage=ActionStage.ACTION,
                verbal=VerbalIntent(content="Stay where you are.", intensity_db=65.0),
                kinematics=KinematicIntent(
                    target_id="actor_passive",
                    applied_force=15.0,
                    effective_mass=60.0,
                    is_contact_action=False,
                    action_type="ADVANCE"
                )
            )
        # 默认静默挂起
        return ActionProposal(agent_id=agent_id, tick=tick, is_silent_pass=True)


def test_full_runtime_tick_cycle():
    # 1. 搭建稳定 ABI 核心
    ledger = EventLedger()
    arbiter = CausalArbiter(config=ArbiterConfiguration())
    bus = PublicRealityBus()
    memory_system = MemorySystem()

    # 社交图谱注入
    social_graph = SocialGraph()
    social_graph.add_edge("actor_active", "actor_passive")
    social_graph.add_edge("actor_passive", "actor_remote")
    rumor_engine = RumorEngine(social_graph, seed=42)

    # 2. 初始化世界状态
    init_state = GlobalWorldState(
        tick=0,
        timestamp="TICK_TIME_000000",
        environment=PhysicalEnvironmentSnapshot(temperature=22.0, observation_pressure=0.2),
        actors={
            "actor_active": ActorSnapshot(
                position=Vector3D(x=0.0, y=0.0),
                somatic=SomaticState(energy_pool=80.0),
                social=SocialState(surveillance_load=0.2),
                self_narrative=SelfNarrativeState()
            ),
            "actor_passive": ActorSnapshot(
                position=Vector3D(x=2.0, y=0.0),
                somatic=SomaticState(energy_pool=60.0),
                social=SocialState(surveillance_load=0.2),
                self_narrative=SelfNarrativeState()
            )
        }
    )

    # 3. 构造注入决策沙盒的 Agents
    policy = CustomActivePolicy()
    agents = {
        "actor_active": AgentEntity("actor_active", init_state.actors["actor_active"].somatic, init_state.actors["actor_active"].social, init_state.actors["actor_active"].self_narrative, policy),
        "actor_passive": AgentEntity("actor_passive", init_state.actors["actor_passive"].somatic, init_state.actors["actor_passive"].social, init_state.actors["actor_passive"].self_narrative, policy)
    }

    # 叙事控制平面：注入环境升温与规制压力微调
    def narrative_controller(tick: int, led: EventLedger) -> NarrativePotentialModifier:
        return NarrativePotentialModifier(delta_observation_pressure=0.1)

    # 4. 组装 CMAWSE 运行时
    runtime = CMAWSERuntime(
        initial_state=init_state,
        ledger=ledger,
        arbiter=arbiter,
        reality_bus=bus,
        agents=agents,
        memory_system=memory_system,
        rumor_engine=rumor_engine,
        narrative_modifier_fn=narrative_controller
    )

    # 执行物理 Tick 推进
    res = runtime.step()

    # --------------------------------------------------------------------
    # 断言：运行时完整因果闭环与主权契约
    # --------------------------------------------------------------------
    # 1. 时钟推进与事实落槌
    assert res.tick == 1
    assert len(ledger) == 1
    assert ledger.get_latest_entry().event_id == res.event.event_id

    # 2. 状态原子提交：actor_active 消耗能量，World State 成功演进
    assert res.state.tick == 1
    assert res.state.actors["actor_active"].somatic.energy_pool < 80.0
    assert res.state.environment.observation_pressure == pytest.approx(0.3)

    # 3. 记忆系统落沉
    mem_store = memory_system.get_or_create_store("actor_active")
    recalled = mem_store.retrieve_by_cues(["RESOLVED"])
    assert len(recalled) == 1
    assert recalled[0].event_ref == res.event.event_id

    # 4. 传闻扩散三律：actor_passive 目击并开始向社交网络节点扩散
    rumors_remote = rumor_engine.get_agent_rumors("actor_remote")
    assert len(rumors_remote) >= 1
    assert rumors_remote[0].hop_count == 1
    assert rumors_remote[0].leveling_ratio > 0.0  # 细节削平
