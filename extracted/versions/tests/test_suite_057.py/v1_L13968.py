# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L13968-L14258 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #57  lines=290  compile=OK
# kind: test  ident: test_suite_057.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 2 - Action Affordance Architecture 语义纯正性验证
执行：pytest tests/test_phase2_affordance.py
"""

import pytest
from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    ActorSnapshot,
    GlobalWorldState,
    PhysicalEnvironmentSnapshot,
    SelfNarrativeState,
    SocialState,
    SomaticState,
    Vector3D,
)
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import (
    ActuatorType,
    CandidateAffordance,
    NarrativeValence,
    SurfaceType,
)
from cmawse.agent.context import SubjectContext
from cmawse.agent.generator import AffordanceGenerator
from cmawse.agent.selector import SubjectiveSelector
from cmawse.agent.base import AgentEntity


# ============================================================================
# Test A: 空间客体客观存在性断言 (Space Divergence)
# ============================================================================
def test_space_divergence_object_presence():
    """验证：视界内真实存在门客体时生发门通道；无门时绝对不能凭空捏造门通道"""
    # 场景 1: 环境中真实存在门物理客体
    env_with_door = PhysicalEnvironmentSnapshot(
        properties={
            "spatial_features": [
                {
                    "id": "door_north_01",
                    "type": "DOOR",
                    "position": {"x": 1.0, "y": 0.0, "z": 0.0},
                    "is_passable": True
                }
            ]
        }
    )
    horizon_with_door = PrivateHorizon(
        agent_id="agent_a",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=env_with_door
    )
    ctx_with_door = SubjectContext.assemble(
        agent_id="agent_a",
        tick=1,
        somatic=SomaticState(energy_pool=80.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
        horizon=horizon_with_door,
        recalled_memories=[],
        received_rumors=[]
    )
    affs_with_door = AffordanceGenerator.generate(ctx_with_door)

    # 断言 1: 真实感知到门时，存在以该门为 target_id 的具身通道
    door_aff = next((a for a in affs_with_door if a.target_id == "door_north_01"), None)
    assert door_aff is not None
    assert door_aff.target_surface == SurfaceType.RIGID_HANDLE

    # 场景 2: 环境中空无一物（开阔平地）
    env_empty = PhysicalEnvironmentSnapshot(properties={"spatial_features": []})
    horizon_empty = PrivateHorizon(
        agent_id="agent_a",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=env_empty
    )
    ctx_empty = SubjectContext.assemble(
        agent_id="agent_a",
        tick=1,
        somatic=SomaticState(energy_pool=80.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
        horizon=horizon_empty,
        recalled_memories=[],
        received_rumors=[]
    )
    affs_empty = AffordanceGenerator.generate(ctx_empty)

    # 核心红线断言：无门时，绝对禁止凭空产生任何门或把手的 target_id
    assert not any("door" in a.channel_id.lower() for a in affs_empty)
    assert not any(a.target_surface == SurfaceType.RIGID_HANDLE for a in affs_empty)


# ============================================================================
# Test B: 具身能力边界断言 (Somatic Divergence)
# ============================================================================
def test_somatic_divergence_load_bearing_failure():
    """验证：当下肢骨折失能时，所有要求承重的通道在物理上被否定，涌现非承重匍匐通道"""
    horizon = PrivateHorizon(
        agent_id="agent_somatic",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot()
    )

    # Case: 严重骨折（无法承重）
    ctx_fractured = SubjectContext.assemble(
        agent_id="agent_somatic",
        tick=1,
        somatic=SomaticState(energy_pool=80.0, variables={"fracture": 1.0}),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
        horizon=horizon,
        recalled_memories=[],
        received_rumors=[]
    )
    affs = AffordanceGenerator.generate(ctx_fractured)

    # 断言：双足承重位移物理不可行，但双臂拉动匍匐可行
    walk_aff = next(a for a in affs if a.action_type == "LOCOMOTION_WALK")
    crawl_aff = next(a for a in affs if a.action_type == "PRONE_CRAWL")

    assert walk_aff.is_physically_feasible is False
    assert crawl_aff.is_physically_feasible is True
    assert crawl_aff.actuator == ActuatorType.DUAL_HANDS


# ============================================================================
# Test C: 叙事定性结构分叉断言 (Narrative Interpretation Divergence)
# ============================================================================
def test_narrative_interpretation_divergence_non_preset():
    """验证：同一在场他人，不同自洽姿态赋予同一物理通道完全不同的定性标签，无硬编码剧情"""
    horizon = PrivateHorizon(
        agent_id="subject",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(),
        visible_actors={"stranger_01": Vector3D(x=1.5, y=0.0)}
    )

    # 对抗型认同
    ctx_defiant = SubjectContext.assemble(
        agent_id="subject",
        tick=1,
        somatic=SomaticState(energy_pool=80.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(constants={"relational_posture": "DEFIANT"}),
        horizon=horizon,
        recalled_memories=[],
        received_rumors=[]
    )
    affs_defiant = AffordanceGenerator.generate(ctx_defiant)

    # 顺从/避险型认同
    ctx_accommodating = SubjectContext.assemble(
        agent_id="subject",
        tick=1,
        somatic=SomaticState(energy_pool=80.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(constants={"relational_posture": "ACCOMMODATING"}),
        horizon=horizon,
        recalled_memories=[],
        received_rumors=[]
    )
    affs_accommodating = AffordanceGenerator.generate(ctx_accommodating)

    # 提取相同的后退通道
    retreat_defiant = next(a for a in affs_defiant if a.action_type == "RETREAT_STEP")
    retreat_accommodating = next(a for a in affs_accommodating if a.action_type == "RETREAT_STEP")

    # 结构断言：同一通道被赋予了完全相反的定性价值标记，且不预设具体动作答案
    assert retreat_defiant.narrative_status == NarrativeValence.VIOLATING
    assert retreat_accommodating.narrative_status == NarrativeValence.SUPPORTED


# ============================================================================
# Test D: 失败行动反馈断言 (Continuity & Failure Feedback)
# ============================================================================
def test_failure_feedback_channel_inhibition():
    """验证：上一 Tick 在特定客体上受挫的事实，抑制继续选择该目标相同通道"""
    env = PhysicalEnvironmentSnapshot(
        properties={
            "spatial_features": [
                {"id": "door_block", "type": "DOOR", "position": {"x": 1.0, "y": 0.0, "z": 0.0}}
            ]
        }
    )
    horizon = PrivateHorizon(
        agent_id="agent_retry",
        tick=2,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=env
    )

    # 记录上一动作为在 door_block 上的机械操作受挫
    ctx_frustrated = SubjectContext.assemble(
        agent_id="agent_retry",
        tick=2,
        somatic=SomaticState(energy_pool=80.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
        horizon=horizon,
        recalled_memories=[],
        received_rumors=[],
        last_action_failed=True,
        last_failed_target="door_block"
    )

    affs = AffordanceGenerator.generate(ctx_frustrated)
    selected = SubjectiveSelector.select(ctx_frustrated, affs)

    # 断言：由于受挫反馈，选择器拒绝再次执行已受挫的 door_block 机械交互
    if selected is not None:
        assert not (selected.target_id == "door_block" and selected.action_type == "INTERACT_DOOR_MANIPULATE")


# ============================================================================
# Test E: 法庭做功耗能闭环不变性断言 (Causal Arbiter Pipeline)
# ============================================================================
def test_arbiter_metabolic_commitment_intact():
    """验证：做功承诺完全交由法庭落槌扣减，Agent 自身无直接写状态权限"""
    from cmawse.core.arbiter import CausalArbiter
    from cmawse.core.committer import StateCommitter

    arbiter = CausalArbiter()
    agent = AgentEntity(
        agent_id="pusher",
        somatic=SomaticState(energy_pool=60.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState()
    )
    horizon = PrivateHorizon(
        agent_id="pusher",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot()
    )

    proposal = agent.generate_proposal(tick=1, horizon=horizon)

    # 初始状态未被 Agent 篡改
    assert agent.somatic.energy_pool == 60.0

    world_state = GlobalWorldState(
        tick=1,
        timestamp="T1",
        actors={
            "pusher": ActorSnapshot(
                position=Vector3D(x=0.0, y=0.0),
                somatic=SomaticState(energy_pool=60.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            )
        }
    )

    # 经由 Arbiter 判定并由 Committer 提交
    verified = arbiter.arbitrate_tick(tick=1, timestamp="T1", proposals=[proposal], world_state=world_state)
    if verified.state_patches:
        new_state = StateCommitter.apply_transaction(world_state, verified.state_patches)
        # 能耗由法庭仲裁真实扣减
        assert new_state.actors["pusher"].somatic.energy_pool < 60.0


# ============================================================================
# Test F: 常态自发静默断言 (Ordinary Silence)
# ============================================================================
def test_ordinary_normative_silence():
    """验证：和平常态无刺激无危机时，系统稳定自主收敛至 SILENT_PASS，绝无强制行动"""
    peaceful_agent = AgentEntity(
        agent_id="monk",
        somatic=SomaticState(energy_pool=90.0, load=0.0, pain=0.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
    )
    # 完全平静的空旷开阔环境，无激活标记
    peaceful_horizon = PrivateHorizon(
        agent_id="monk",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []})
    )

    prop = peaceful_agent.generate_proposal(tick=1, horizon=peaceful_horizon)

    # 核心断言：平稳世界自然呈现合法的静止状态，不被算法强迫行走
    assert prop.is_silent_pass is True
