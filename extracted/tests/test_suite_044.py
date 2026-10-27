# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L11089-L11372 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #44  lines=283  compile=OK
# kind: test  ident: test_suite_044.py  version: latest of 1 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 2 - Action Affordance Architecture 结构性分叉验证
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
from cmawse.world.bus import PrivateHorizon, PublicRealityBus
from cmawse.agent.affordance import (
    ActuatorType,
    CandidateAffordance,
    NarrativeValence,
    SurfaceType,
)
from cmawse.agent.context import SubjectContext, SituationalActivation
from cmawse.agent.generator import AffordanceGenerator
from cmawse.agent.selector import SubjectiveSelector
from cmawse.agent.ladder import FiveStageWorkLadder
from cmawse.agent.base import AgentEntity


# ============================================================================
# Test A: 空间拓扑分叉断言 (Space Divergence)
# ============================================================================
def test_space_divergence_door_open_vs_locked():
    """验证：完全相同的主体面对虚掩门与死锁门，物理可供性通道发生结构性突变"""
    horizon_base = PrivateHorizon(
        agent_id="agent_a",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot()
    )

    # Case 1: 门虚掩 / 通畅开阔
    ctx_open = SubjectContext.assemble(
        agent_id="agent_a",
        tick=1,
        somatic=SomaticState(energy_pool=80.0, load=0.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
        horizon=horizon_base,
        recalled_memories=[],
        received_rumors=[],
        last_action_failed=False
    )
    affs_open = AffordanceGenerator.generate(ctx_open)

    # 断言 1: 畅通时，必有可执行的位移通道
    walk_channel = next((a for a in affs_open if a.action_type == "LOCOMOTION_WALK"), None)
    assert walk_channel is not None
    assert walk_channel.is_physically_feasible is True

    # Case 2: 空间阻断 / 门体死锁 (上一动作为推门失败)
    ctx_locked = SubjectContext.assemble(
        agent_id="agent_a",
        tick=2,
        somatic=SomaticState(energy_pool=80.0, load=0.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
        horizon=horizon_base,
        recalled_memories=[],
        received_rumors=[],
        last_action_failed=True,
        last_action_type="INTERACT_DOOR_PUSH"
    )
    affs_locked = AffordanceGenerator.generate(ctx_locked)

    # 断言 2: 阻断时，直行位移被物理否定，结构性涌现摇晃把手与搜索工具通道
    locked_walk = next((a for a in affs_locked if a.action_type == "LOCOMOTION_WALK"), None)
    assert locked_walk.is_physically_feasible is False

    shake_channel = next((a for a in affs_locked if a.action_type == "INTERACT_DOOR_SHAKE"), None)
    tool_channel = next((a for a in affs_locked if a.action_type == "SEARCH_TOOL"), None)
    assert shake_channel is not None and shake_channel.is_physically_feasible is True
    assert tool_channel is not None and tool_channel.is_physically_feasible is True


# ============================================================================
# Test B: 具身动力学分叉断言 (Somatic Divergence)
# ============================================================================
def test_somatic_divergence_healthy_vs_fractured():
    """验证：双下肢完好 vs 骨折伤残，位移通道的 Actuator 发生质的替换"""
    horizon = PrivateHorizon(
        agent_id="agent_somatic",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot()
    )

    # Case 1: 健康下肢
    ctx_healthy = SubjectContext.assemble(
        agent_id="agent_somatic",
        tick=1,
        somatic=SomaticState(energy_pool=90.0, pain=0.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
        horizon=horizon,
        recalled_memories=[],
        received_rumors=[]
    )
    affs_healthy = AffordanceGenerator.generate(ctx_healthy)
    walk_aff = next(a for a in affs_healthy if a.action_type == "LOCOMOTION_WALK")
    assert walk_aff.is_physically_feasible is True
    assert walk_aff.actuator == ActuatorType.DUAL_LEGS

    # Case 2: 严重骨折失能
    ctx_fractured = SubjectContext.assemble(
        agent_id="agent_somatic",
        tick=1,
        somatic=SomaticState(energy_pool=90.0, pain=80.0, variables={"fracture": 1.0}),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
        horizon=horizon,
        recalled_memories=[],
        received_rumors=[]
    )
    affs_fractured = AffordanceGenerator.generate(ctx_fractured)

    # 断言：双下肢行走物理不可行，分发出双臂拉动的匍匐通道
    walk_infeasible = next(a for a in affs_fractured if a.action_type == "LOCOMOTION_WALK")
    assert walk_infeasible.is_physically_feasible is False

    crawl_aff = next((a for a in affs_fractured if a.action_type == "PRONE_CRAWL"), None)
    assert crawl_aff is not None
    assert crawl_aff.is_physically_feasible is True
    assert crawl_aff.actuator == ActuatorType.DUAL_HANDS


# ============================================================================
# Test C: 主体叙事与意义分叉断言 (Narrative Interpretation Divergence)
# ============================================================================
def test_narrative_interpretation_divergence():
    """验证：同一逼近挑衅者现实，面对尊严型与避险型主体，叙事定性相反且提议矢量对立"""
    horizon = PrivateHorizon(
        agent_id="subject",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(),
        visible_actors={"opponent": Vector3D(x=1.5, y=0.0)}
    )

    # Agent A: 尊严至上
    agent_a = AgentEntity(
        agent_id="agent_a",
        somatic=SomaticState(energy_pool=80.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(constants={"core_belief": "我是街坊长辈，寸步不让"}),
    )
    prop_a = agent_a.generate_proposal(tick=1, horizon=horizon)

    # Agent B: 避险第一
    agent_b = AgentEntity(
        agent_id="agent_b",
        somatic=SomaticState(energy_pool=80.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(constants={"core_belief": "好汉不吃眼前亏，生存第一"}),
    )
    prop_b = agent_b.generate_proposal(tick=1, horizon=horizon)

    # 结构性断言：双方提议均合法成立，但力学与动作属性形成定性对立
    assert prop_a.is_silent_pass is False
    assert prop_a.kinematics.action_type == "ASSERT_POSTURE"
    assert prop_a.verbal is not None  # Agent A 选择正向发声喝止

    assert prop_b.is_silent_pass is False
    assert prop_b.kinematics.action_type == "RETREAT_STEP"
    assert prop_b.kinematics.intended_trajectory.x < 0.0  # Agent B 选择背向退避


# ============================================================================
# Test D: 行动连续性与反馈分叉断言 (Continuity Divergence)
# ============================================================================
def test_continuity_and_failure_feedback_divergence():
    """验证：连续动作惯性推进 vs 遭遇撞墙失败后自发切换动作通道"""
    agent = AgentEntity(
        agent_id="agent_worker",
        somatic=SomaticState(energy_pool=80.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
    )
    horizon = PrivateHorizon(
        agent_id="agent_worker",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot()
    )

    # 1. 首次遭遇门体阻断
    agent.record_action_feedback(failed=True, action_type="INTERACT_DOOR_PUSH")
    prop_retry = agent.generate_proposal(tick=2, horizon=horizon)

    # 断言：上一次推门失败，本轮通道自动消歧并切换至搜索工具或摇晃，不再无脑重复推门
    assert prop_retry.is_silent_pass is False
    assert prop_retry.kinematics.action_type in ("SEARCH_TOOL", "INTERACT_DOOR_SHAKE")


# ============================================================================
# Test E: 失败动作的物理耗能因果闭环验证 (Failed Action Causal Loop)
# ============================================================================
def test_failed_action_somatic_exhaustion_pipeline():
    """验证：推死锁门虽未位移，但身体真实做功产出能量损耗，并经由 Committer 生效"""
    from cmawse.core.arbiter import CausalArbiter
    from cmawse.core.committer import StateCommitter

    arbiter = CausalArbiter()
    agent_entity = AgentEntity(
        agent_id="pusher",
        somatic=SomaticState(energy_pool=50.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState()
    )
    horizon = PrivateHorizon(
        agent_id="pusher",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot()
    )

    # 生成摇晃门体提案
    agent_entity.record_action_feedback(failed=True, action_type="DOOR_BLOCK")
    prop = agent_entity.generate_proposal(tick=1, horizon=horizon)

    world_state = GlobalWorldState(
        tick=1,
        timestamp="T1",
        actors={
            "pusher": ActorSnapshot(
                position=Vector3D(x=0.0, y=0.0),
                somatic=SomaticState(energy_pool=50.0),
                social=SocialState(),
                self_narrative=SelfNarrativeState()
            )
        }
    )

    # Arbiter 仲裁该物理动作
    verified_event = arbiter.arbitrate_tick(
        tick=1,
        timestamp="T1",
        proposals=[prop],
        world_state=world_state
    )

    # 断言：法庭确认做功发生，生成能量扣除 Patch
    assert len(verified_event.state_patches) > 0
    new_state = StateCommitter.apply_transaction(world_state, verified_event.state_patches)
    assert new_state.actors["pusher"].somatic.energy_pool < 50.0


# ============================================================================
# Test F: 常态无任务自主低强度生活行动断言 (No-Task Ordinary Life)
# ============================================================================
def test_no_task_ordinary_life_spontaneous_action():
    """验证：完全无危机、无外部任务的和平常态下，Agent 自发生发低强度日常位移/维持行动，绝不退化为死寂"""
    peaceful_agent = AgentEntity(
        agent_id="peaceful_citizen",
        somatic=SomaticState(energy_pool=100.0, load=0.0, pain=0.0),
        social=SocialState(),
        self_narrative=SelfNarrativeState(),
    )
    peaceful_horizon = PrivateHorizon(
        agent_id="peaceful_citizen",
        tick=1,
        self_position=Vector3D(x=5.0, y=5.0),
        local_environment=PhysicalEnvironmentSnapshot(temperature=20.0, observation_pressure=0.0)
    )

    prop = peaceful_agent.generate_proposal(tick=1, horizon=peaceful_horizon)

    # 断言：在平稳开阔环境中，主体自主产生微量步态位移，而不是系统默认的 SILENT_PASS 瘫痪
    assert prop.is_silent_pass is False
    assert prop.kinematics.action_type in ("LOCOMOTION_WALK", "MAINTAIN_POSTURE")
    assert prop.kinematics.applied_force > 0.0
