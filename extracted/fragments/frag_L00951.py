# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L951-L1160 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #4  lines=209  compile=OK
# kind: fragment  ident: frag_L00951.py
# edits: none. Header comment is the only addition.
# ======================
"""
测试：Phase 1 四个核心模块的闭环与主权约束验证
执行：pytest tests/test_phase1_pipeline.py
"""

import pytest
from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    AcousticSignature,
    ActorPhysicalSnapshot,
    Coordinate3D,
    GlobalWorldState,
    KinematicVector,
    RFC6902Patch,
    SelfNarrativeState,
    SocialState,
    SomaticState,
    SpatialFieldParams,
    VerbalEmission,
)
from cmawse.core.ledger import EventLedger, LedgerIntegrityError
from cmawse.core.committer import StateCommitter, PatchApplicationError
from cmawse.core.arbiter import CausalArbiter


@pytest.fixture
def initial_world_state() -> GlobalWorldState:
    """初始化一个标准的双主体封闭物理场域快照"""
    actor_a = ActorPhysicalSnapshot(
        agent_id="li_yang",
        coordinate=Coordinate3D(x=1.0, y=1.0, z=0.0),
        somatic=SomaticState(fatigue=10.0, pain=0.0, adrenaline=30.0),
        social=SocialState(status_hierarchy=2, perceived_surveillance=0.8),
        self_narrative=SelfNarrativeState(core_belief="必须保持绝对掌控"),
        inventory=["towel"]
    )
    actor_b = ActorPhysicalSnapshot(
        agent_id="wang_wenxu",
        coordinate=Coordinate3D(x=2.0, y=1.0, z=0.0),  # 距离 li_yang 1.0米
        somatic=SomaticState(fatigue=60.0, pain=20.0, adrenaline=15.0),
        social=SocialState(status_hierarchy=1, perceived_surveillance=0.9),
        self_narrative=SelfNarrativeState(core_belief="绝不能显露软弱"),
        inventory=[]
    )
    return GlobalWorldState(
        tick=420,
        timestamp="2024-08-19T03:45:00",
        spatial_params=SpatialFieldParams(
            privacy_level=0.2,
            observation_pressure=0.8,
            ambient_temp=12.0
        ),
        actors={"li_yang": actor_a, "wang_wenxu": actor_b}
    )


def test_spatial_gate_and_energy_barrier(initial_world_state: GlobalWorldState):
    """验证因果门禁：超距动作被直接驳回，低动能动作被阻尼降阶"""
    arbiter = CausalArbiter(random_seed=42)

    # 1. 构造一个在 5 米开外的远距离主体
    far_actor = ActorPhysicalSnapshot(
        agent_id="stranger",
        coordinate=Coordinate3D(x=10.0, y=10.0, z=0.0),
        somatic=SomaticState(fatigue=0.0, adrenaline=50.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(core_belief="观察者")
    )
    state = initial_world_state.model_copy(
        update={"actors": {**initial_world_state.actors, "stranger": far_actor}}
    )

    # stranger 尝试攻击 li_yang（距离远超 3 米）
    proposal_far = ActionProposal(
        agent_id="stranger",
        tick=421,
        kinematics=KinematicVector(
            target_agent_id="li_yang",
            force_magnitude=30.0,
            action_description="试图挥拳打击对方下颌"
        )
    )

    # wang_wenxu (高疲劳度+高环境规制阻尼) 尝试反抗，但动能不足
    proposal_tired = ActionProposal(
        agent_id="wang_wenxu",
        tick=421,
        kinematics=KinematicVector(
            target_agent_id="li_yang",
            force_magnitude=10.0,
            action_description="试图猛烈推开对方肩膀"
        )
    )

    event = arbiter.arbitrate(
        tick_index=421,
        timestamp="2024-08-19T03:45:01",
        proposals=[proposal_far, proposal_tired],
        world_state=state
    )

    # 断言：超距动作被驳回，低动能被降阶为微动作
    facts_joined = "\n".join(event.verified_physical_facts)
    assert "超出阈值 3.0m" in facts_joined
    assert "动作降阶：指尖仅产生微弱颤动" in facts_joined


def test_deadlock_environmental_roll(initial_world_state: GlobalWorldState):
    """验证动力学死锁：两主体力道相近进入临界阈值时，自动抽取环境随机熵打破平衡"""
    arbiter = CausalArbiter(random_seed=123)

    # 双方势均力敌对抗
    proposal_a = ActionProposal(
        agent_id="li_yang",
        tick=421,
        kinematics=KinematicVector(
            target_agent_id="wang_wenxu",
            force_magnitude=20.0,
            action_description="逼近压制对方双腿"
        )
    )
    proposal_b = ActionProposal(
        agent_id="wang_wenxu",
        tick=421,
        kinematics=KinematicVector(
            target_agent_id="li_yang",
            force_magnitude=20.5,  # 差值 0.5 < epsilon (2.0)
            action_description="蹬腿抗拒对方接触"
        )
    )

    event = arbiter.arbitrate(
        tick_index=421,
        timestamp="2024-08-19T03:45:01",
        proposals=[proposal_a, proposal_b],
        world_state=initial_world_state
    )

    facts_joined = "\n".join(event.verified_physical_facts)
    assert "对称死锁" in facts_joined
    assert "法庭引入环境熵打破平衡" in facts_joined
    assert len(event.state_patches) > 0


def test_full_pipeline_ledger_and_committer(initial_world_state: GlobalWorldState):
    """全流水线闭环：Proposal -> Arbiter -> VerifiedEvent -> Ledger -> Committer -> 新 State"""
    ledger = EventLedger()
    arbiter = CausalArbiter(random_seed=999)

    # 产生有效言语与单向动作提案
    prop_speak = ActionProposal(
        agent_id="li_yang",
        tick=421,
        verbal=VerbalEmission(text="把腿收一下。", acoustic=AcousticSignature.LOW_PITCH_HEAVY_BREATH),
        kinematics=KinematicVector(
            target_agent_id="wang_wenxu",
            force_magnitude=35.0,
            action_description="递出毛巾，悬空停滞于对方右膝20cm处"
        )
    )
    # 对方选择挂起 (SILENT_PASS)
    prop_silent = ActionProposal(
        agent_id="wang_wenxu",
        tick=421,
        is_silent_pass=True
    )

    # 1. 仲裁出唯一合法事实
    event = arbiter.arbitrate(
        tick_index=421,
        timestamp="2024-08-19T03:45:01",
        proposals=[prop_speak, prop_silent],
        world_state=initial_world_state
    )

    assert len(event.dialogue_emissions) == 1
    assert event.dialogue_emissions[0].phonetics == "把腿收一下。"
    assert len(event.state_patches) > 0

    # 2. 事实主权账本持久化生效
    ledger.append(event)
    assert ledger.count() == 1

    # 事实账本主权断言：严禁时序倒流
    with pytest.raises(LedgerIntegrityError):
        invalid_retro_event = event.model_copy(update={"tick_index": 400})
        ledger.append(invalid_retro_event)

    # 3. State Committer 执行原子 RFC 6902 状态提交
    new_world_state = StateCommitter.apply_patches(initial_world_state, event.state_patches)

    # 断言：li_yang 的疲劳度发生确定性更新，原状态对象完全未被就地突变
    assert new_world_state.actors["li_yang"].somatic.fatigue > initial_world_state.actors["li_yang"].somatic.fatigue
    assert initial_world_state.actors["li_yang"].somatic.fatigue == 10.0


def test_committer_atomic_rollback(initial_world_state: GlobalWorldState):
    """测试 State Committer 的原子回滚特性：当补丁中出现非法路径时，完全拒绝修改"""
    invalid_patches = [
        RFC6902Patch(op="replace", path="/actors/li_yang/somatic/fatigue", value=50.0),
        RFC6902Patch(op="replace", path="/non_existent_scope/invalid_key", value=999.0)  # 致命非法路径
    ]

    with pytest.raises(PatchApplicationError):
        StateCommitter.apply_patches(initial_world_state, invalid_patches)

    # 验证原状态未受任何污染
    assert initial_world_state.actors["li_yang"].somatic.fatigue == 10.0
