# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L2017-L2240 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #9  lines=223  compile=OK
# kind: fragment  ident: frag_L02017.py
# edits: none. Header comment is the only addition.
# ======================
"""
测试验证：CMAWSE v1.2 精简核心模块严格一致性
执行：pytest tests/test_minimal_core.py
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
    VerbalIntent,
)
from cmawse.core.ledger import EventLedger, LedgerIntegrityViolation
from cmawse.core.committer import StateCommitter, CommitTransactionError
from cmawse.core.arbiter import CausalArbiter, ArbiterConfiguration


@pytest.fixture
def clean_world() -> GlobalWorldState:
    """纯粹的数学物理空间快照，不携带任何剧情色彩"""
    return GlobalWorldState(
        tick=1,
        timestamp="2024-01-01T00:00:00",
        environment=PhysicalEnvironmentSnapshot(
            temperature=20.0,
            observation_pressure=0.5,
            micro_entropy_variable=0.8848
        ),
        actors={
            "agent_1": ActorSnapshot(
                position=Vector3D(x=0.0, y=0.0, z=0.0),
                somatic=SomaticState(energy_pool=50.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            ),
            "agent_2": ActorSnapshot(
                position=Vector3D(x=1.5, y=0.0, z=0.0),
                somatic=SomaticState(energy_pool=50.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            )
        }
    )


def test_zero_event_cycle(clean_world: GlobalWorldState):
    """验证公理 4：零事件轮 (SILENT_PASS) 属于系统最高优先级合法状态"""
    arbiter = CausalArbiter()
    proposals = [
        ActionProposal(agent_id="agent_1", tick=1, is_silent_pass=True),
        ActionProposal(agent_id="agent_2", tick=1, is_silent_pass=True)
    ]
    event = arbiter.arbitrate_tick(
        tick=1,
        timestamp="2024-01-01T00:00:01",
        proposals=proposals,
        world_state=clean_world
    )
    assert event.causal_status == "QUIET_CYCLE"
    assert len(event.state_patches) == 0
    assert len(event.resolved_kinematics) == 2


def test_spatial_gate_hard_rejection(clean_world: GlobalWorldState):
    """验证公理 2：超距动作绝不形成因果，距离超出阈值立即被拒绝"""
    config = ArbiterConfiguration(contact_distance_limit=1.0)
    arbiter = CausalArbiter(config=config)

    # 物理距离为 1.5m，阈值限制为 1.0m
    proposal = ActionProposal(
        agent_id="agent_1",
        tick=1,
        kinematics=KinematicIntent(
            target_id="agent_2",
            applied_force=10.0,
            effective_mass=70.0,
            is_contact_action=True,
            action_type="GRASP"
        )
    )

    event = arbiter.arbitrate_tick(
        tick=1,
        timestamp="2024-01-01T00:00:01",
        proposals=[proposal],
        world_state=clean_world
    )

    assert len(event.state_patches) == 0
    assert event.resolved_kinematics[0]["status"] == "SPATIAL_COLLISION_INVALID"


def test_energy_barrier_interception(clean_world: GlobalWorldState):
    """验证公理 3：做功阶梯能耗势垒拦截，动能匮乏强制无法做功"""
    # 调高阻尼权重使得 ΔE 显著放大
    config = ArbiterConfiguration(gamma_obs=100.0)
    arbiter = CausalArbiter(config=config)

    # agent_1 仅有 10.0 单位能量池
    starved_world = clean_world.model_copy(
        update={
            "actors": {
                **clean_world.actors,
                "agent_1": clean_world.actors["agent_1"].model_copy(
                    update={"somatic": SomaticState(energy_pool=10.0)}
                )
            }
        }
    )

    proposal = ActionProposal(
        agent_id="agent_1",
        tick=1,
        kinematics=KinematicIntent(
            target_id="agent_2",
            applied_force=20.0,
            effective_mass=60.0,
            is_contact_action=True,
            action_type="PUSH"
        )
    )

    event = arbiter.arbitrate_tick(
        tick=1,
        timestamp="2024-01-01T00:00:01",
        proposals=[proposal],
        world_state=starved_world
    )

    assert event.resolved_kinematics[0]["status"] == "ENERGY_BARRIER_UNMET"
    # 仅产出 load 增加的 patch，核心做功不发生
    assert len(event.state_patches) == 1
    assert "/somatic/load" in event.state_patches[0].path


def test_deadlock_consumes_world_entropy(clean_world: GlobalWorldState):
    """验证死锁对称性破缺：Arbiter 绝不凭空发明事实，必须消费 World Plane 显式注入的环境熵"""
    arbiter = CausalArbiter()
    p1 = ActionProposal(
        agent_id="agent_1",
        tick=1,
        kinematics=KinematicIntent(
            target_id="agent_2",
            applied_force=30.0,
            effective_mass=60.0,
            action_type="STRIKE"
        )
    )
    p2 = ActionProposal(
        agent_id="agent_2",
        tick=1,
        kinematics=KinematicIntent(
            target_id="agent_1",
            applied_force=30.5,  # 差值 0.5 < epsilon(2.0)
            effective_mass=60.0,
            action_type="BLOCK"
        )
    )

    event = arbiter.arbitrate_tick(
        tick=1,
        timestamp="2024-01-01T00:00:01",
        proposals=[p1, p2],
        world_state=clean_world
    )

    record = event.resolved_kinematics[0]
    assert record["status"] == "KINEMATIC_DEADLOCK_RESOLVED_BY_ENTROPY"
    assert record["consumed_entropy"] == clean_world.environment.micro_entropy_variable


def test_ledger_and_committer_strict_sovereignty(clean_world: GlobalWorldState):
    """验证主权原则：Ledger 历史不可篡改，Committer 发生异常完全回滚"""
    ledger = EventLedger()
    arbiter = CausalArbiter()

    p = ActionProposal(
        agent_id="agent_1",
        tick=1,
        verbal=VerbalIntent(content="Test emission", intensity_db=50.0),
        kinematics=KinematicIntent(
            applied_force=5.0,
            effective_mass=50.0,
            is_contact_action=False,
            action_type="STEP"
        )
    )

    event = arbiter.arbitrate_tick(
        tick=1,
        timestamp="2024-01-01T00:00:01",
        proposals=[p],
        world_state=clean_world
    )

    # 1. 事实入账
    ledger.append(event)
    assert len(ledger) == 1

    # 时序倒流断言
    with pytest.raises(LedgerIntegrityViolation):
        ledger.append(event.model_copy(update={"tick_index": 0}))

    # 2. Committer 原子生效
    new_state = StateCommitter.apply_transaction(clean_world, event.state_patches, next_tick=2)
    assert new_state.tick == 2
    assert new_state.actors["agent_1"].somatic.energy_pool < 50.0

    # 3. 注入脏 Patch 检验零污染回滚
    poison_patch = RFC6902Patch(op="replace", path="/non_existent_scope/value", value=123)
    with pytest.raises(CommitTransactionError):
        StateCommitter.apply_transaction(new_state, [poison_patch])

    # 确认原状态未受任何污染
    assert new_state.tick == 2
