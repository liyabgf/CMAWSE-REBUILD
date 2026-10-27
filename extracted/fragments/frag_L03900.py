# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L3900-L4102 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #23  lines=202  compile=OK
# kind: fragment  ident: frag_L03900.py
# edits: none. Header comment is the only addition.
# ======================
"""
测试验证：第二轮架构审计缺陷的针对性回归测试
执行：pytest tests/test_audit_constraints.py
"""

import pytest
from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    ActorSnapshot,
    GlobalWorldState,
    KinematicIntent,
    PhysicalEnvironmentSnapshot,
    RFC6902Patch,
    SelfNarrativeState,
    SocialState,
    SomaticState,
    Vector3D,
    VerifiedEventEntry,
)
from cmawse.core.ledger import EventLedger
from cmawse.core.committer import CommitTransactionError
from cmawse.core.arbiter import CausalArbiter
from cmawse.world.bus import PublicRealityBus
from cmawse.agent.base import AgentEntity, ClosedLoopInertiaPolicy
from cmawse.cognitive.memory import MemorySystem, SubjectiveMemoryTrace
from cmawse.cognitive.rumor import RumorEngine, SocialGraph
from cmawse.runtime.orchestrator import CMAWSERuntime


@pytest.fixture
def isolated_world() -> GlobalWorldState:
    """构建空间隔离场景：A 与 B 相邻，C 远在 100 米之外"""
    return GlobalWorldState(
        tick=0,
        timestamp="TICK_0",
        environment=PhysicalEnvironmentSnapshot(),
        actors={
            "agent_a": ActorSnapshot(
                position=Vector3D(x=0.0, y=0.0),
                somatic=SomaticState(energy_pool=100.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            ),
            "agent_b": ActorSnapshot(
                position=Vector3D(x=1.0, y=0.0),
                somatic=SomaticState(energy_pool=100.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            ),
            "agent_c_remote": ActorSnapshot(
                position=Vector3D(x=100.0, y=100.0),  # 远超感知阈值
                somatic=SomaticState(energy_pool=100.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            ),
        }
    )


def test_no_omniscience_leak_for_remote_agent(isolated_world: GlobalWorldState):
    """
    证明约束 1：未在场且不可感知的 Agent 绝不会产生客观事实记忆，
    也绝不能作为 Witness 播种传闻（彻底阻断全知穿帮）。
    """
    ledger = EventLedger()
    arbiter = CausalArbiter()
    bus = PublicRealityBus()
    memory_system = MemorySystem()
    social_graph = SocialGraph()
    social_graph.add_edge("agent_b", "agent_c_remote")
    rumor_engine = RumorEngine(social_graph)

    agents = {
        aid: AgentEntity(aid, snap.somatic, snap.social, snap.self_narrative)
        for aid, snap in isolated_world.actors.items()
    }

    runtime = CMAWSERuntime(
        initial_state=isolated_world,
        ledger=ledger,
        arbiter=arbiter,
        reality_bus=bus,
        agents=agents,
        memory_system=memory_system,
        rumor_engine=rumor_engine
    )

    # 构造一次由 A 对 B 的主动肢体动作
    class LocalActionPolicy:
        def evaluate(self, agent_id, tick, somatic, social, self_narrative, horizon, recalled):
            if agent_id == "agent_a":
                return ActionProposal(
                    agent_id="agent_a",
                    tick=tick,
                    kinematics=KinematicIntent(
                        target_id="agent_b",
                        applied_force=10.0,
                        effective_mass=60.0,
                        is_contact_action=True,
                        action_type="TOUCH"
                    )
                )
            return ActionProposal(agent_id=agent_id, tick=tick, is_silent_pass=True)

    runtime._agents["agent_a"]._policy = LocalActionPolicy()

    # 推进物理步长
    res = runtime.step()

    # 断言：事件实际发生
    assert len(ledger) == 1

    # 核心断言：在场目击者 (A, B) 沉降了记忆
    assert len(memory_system.get_or_create_store("agent_a")._records) == 1
    assert len(memory_system.get_or_create_store("agent_b")._records) == 1

    # 核心断言：远端未在场者 (C) 的私有记忆库必须完全为空！
    assert len(memory_system.get_or_create_store("agent_c_remote")._records) == 0

    # 核心断言：远端主体 C 不能直接持有 0-hop 的 Witness 传闻
    remote_rumors = rumor_engine.get_agent_rumors("agent_c_remote")
    for r in remote_rumors:
        assert r.hop_count > 0, "远端主体绝不能凭空成为原始目击者 (0-hop)"


def test_transactional_consistency_on_bad_patch(isolated_world: GlobalWorldState):
    """
    证明约束 2：若状态补丁存在非法路径，整个物理推进事务崩溃，
    Event Ledger 严禁追加任何条目（保持绝对事务一致性）。
    """
    ledger = EventLedger()
    bus = PublicRealityBus()
    memory_system = MemorySystem()
    rumor_engine = RumorEngine(SocialGraph())
    agents = {
        aid: AgentEntity(aid, snap.somatic, snap.social, snap.self_narrative)
        for aid, snap in isolated_world.actors.items()
    }

    # 构造一个故障仲裁器：输出带破坏性路径的 Patch
    class PoisonedArbiter(CausalArbiter):
        def arbitrate_tick(self, tick, timestamp, proposals, world_state):
            return VerifiedEventEntry(
                event_id=f"evt_poisoned_{tick}",
                tick_index=tick,
                timestamp=timestamp,
                causal_status="POISON_TEST",
                state_patches=[
                    RFC6902Patch(op="replace", path="/non_existent_field/corrupt", value=999)
                ]
            )

    runtime = CMAWSERuntime(
        initial_state=isolated_world,
        ledger=ledger,
        arbiter=PoisonedArbiter(),
        reality_bus=bus,
        agents=agents,
        memory_system=memory_system,
        rumor_engine=rumor_engine
    )

    # 推进应因补丁非法而抛出 CommitTransactionError
    with pytest.raises(CommitTransactionError):
        runtime.step()

    # 核心断言：账本不可逆主权未受污染，长度依然为 0
    assert len(ledger) == 0
    assert runtime.current_state.tick == 0


def test_closed_loop_memory_to_proposal(isolated_world: GlobalWorldState):
    """
    证明约束 3：Memory -> Tension -> ActionProposal 真实闭环。
    平稳状态下主体原本静默，植入创伤记忆后再次感应目标，张力被点燃进而产生主动行为。
    """
    bus = PublicRealityBus()
    policy = ClosedLoopInertiaPolicy(action_threshold=30.0)
    agent = AgentEntity("agent_a", isolated_world.actors["agent_a"].somatic, isolated_world.actors["agent_a"].social, isolated_world.actors["agent_a"].self_narrative, policy)

    horizons = bus.generate_horizons(isolated_world)
    horizon_a = horizons["agent_a"]

    # 1. 无记忆召回时：张力未达标，输出 SILENT_PASS
    proposal_inert = agent.generate_proposal(tick=1, horizon=horizon_a, recalled_memories=[])
    assert proposal_inert.is_silent_pass is True

    # 2. 模拟过去沉降的一条高创伤记忆
    traumatic_memory = SubjectiveMemoryTrace(
        event_ref="evt_past_trauma",
        recorded_tick=0,
        emotional_scar=35.0,  # 带来 35.0 * 1.5 = 52.5 的额外内在张力
        subjective_rationalization="曾在此坐标遭受严重挤压",
        salience_tags=["agent_b"]
    )

    # 3. 伴随记忆唤醒：张力突破阈值，闭环激活，产出主动防御/回避提案
    proposal_active = agent.generate_proposal(tick=2, horizon=horizon_a, recalled_memories=[traumatic_memory])
    assert proposal_active.is_silent_pass is False
    assert proposal_active.stage == ActionStage.ACTION
    assert proposal_active.kinematics.action_type == "EVADE_OR_DEFEND"
