# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L24085-L24387 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #112  lines=302  compile=OK
# kind: test  ident: test_phase_3_1_6.py  version: 1/2
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.1.6 - Reference Semantics & Opaque Non-Addressability 闭环测试 (12 项)
执行：pytest tests/test_phase3_1_6_reference_semantics.py
"""

import pytest
from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.affordance import ActuatorType, CandidateAffordance, SurfaceType, ActionAttribute
from cmawse.agent.cognitive_projection import (
    CognitiveProjection,
    ProjectedCandidateDTO,
    ABSTRACT_INTERFACE_TAXONOMIES
)
from cmawse.agent.cognitive_state import InternalCognitiveState, InterpersonalExpectation, StanceType, RelationalDebt
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import MindDecisionStatus, CognitiveSilentMode
from cmawse.agent.intent import SubjectiveIntent, ConcernDomain as IntentDomain, IntendedTransition, UrgencyMode, ScopeCategory
from cmawse.agent.llm_adapter import DeterministicMockCognitiveMind
from cmawse.agent.llm_boundary import LLMBoundaryValidator
from cmawse.agent.representation import SubjectiveRepresentation
from cmawse.cognitive.memory import SubjectiveMemoryTrace
from cmawse.cognitive.rumor import RumorPacket


@pytest.fixture
def mock_ctx() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="agent_316",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(properties={"spatial_features": []}),
        visible_actors={"actor_visible_bob": Vector3D(x=1.0, y=1.0)}
    )
    return SubjectContext.assemble("agent_316", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


# ============================================================================
# 1. 隐藏实体句柄渗透拦截 (Hidden Entity Reference Isolation)
# ============================================================================

def test_non_prefixed_hidden_entity_identifier_filtered(mock_ctx):
    """断言：无特定前缀的隐藏实体 ID (如 secret_door) 经由 Fail-Closed 机制被严格拦截"""
    state = InternalCognitiveState()
    state.learned_interface_resistance = {
        "SURFACE_WOOD": {"resistance_level": "LOW", "learned_tick": 1},
        "secret_vault_door": {"resistance_level": "MAX", "learned_tick": 2},
        "normal_looking_rock": {"resistance_level": "HIGH", "learned_tick": 3}
    }
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [], [], [])

    refs = [r.interface_ref for r in proj.internal_cognitive_state.learned_interface_resistance]
    assert "SURFACE_WOOD" in refs
    assert "secret_vault_door" not in refs
    assert "normal_looking_rock" not in refs


def test_misleading_entity_prefix_on_abstract_category(mock_ctx):
    """断言：非白名单且非视界内的标识符（即使带有实体前缀）一律 Fail-Closed 剔除"""
    state = InternalCognitiveState()
    state.learned_interface_resistance = {
        "entity_but_actually_abstract": {"resistance_level": "MED", "learned_tick": 1},
        "BARRIER_INTERFACE": {"resistance_level": "HIGH", "learned_tick": 1}
    }
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [], [], [])

    refs = [r.interface_ref for r in proj.internal_cognitive_state.learned_interface_resistance]
    assert "BARRIER_INTERFACE" in refs
    assert "entity_but_actually_abstract" not in refs


def test_hidden_actor_interpersonal_expectation_filtered(mock_ctx):
    """断言：不可见角色的 InterpersonalExpectation 绝对被过滤"""
    state = InternalCognitiveState()
    state.interpersonal_expectations["actor_visible_bob"] = InterpersonalExpectation(
        perceived_stance=StanceType.COOPERATIVE,
        relational_debt=RelationalDebt.NEUTRAL,
        recent_interaction_residue="friendly"
    )
    state.interpersonal_expectations["actor_hidden_alice"] = InterpersonalExpectation(
        perceived_stance=StanceType.HOSTILE,
        relational_debt=RelationalDebt.DEBTOR,
        recent_interaction_residue="threat"
    )
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [], [], [])

    actors = [e.target_actor_id for e in proj.internal_cognitive_state.interpersonal_expectations]
    assert "actor_visible_bob" in actors
    assert "actor_hidden_alice" not in actors


# ============================================================================
# 2. 不透明引用跨字段攻击与非可寻址性测试 (Opaque Cross-Field Attacks)
# ============================================================================

def test_opaque_event_ref_cross_field_target_id_attack(mock_ctx):
    """跨字段攻击：LLM 试图将 memory 中的 event_ref 选作动作 target/channel_id 必被拒绝"""
    mem = SubjectiveMemoryTrace(
        event_ref="evt_past_trauma_001",
        recorded_tick=1,
        subjective_rationalization="fear",
        salience_tags=["threat"]
    )
    c_valid = CandidateAffordance(
        channel_id="AFF_VALID",
        action_type="REST",
        actuator=ActuatorType.TORSO,
        target_surface=SurfaceType.UNOBSTRUCTED_SPACE,
        action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE
    )
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [mem], [])

    # 尝试选择 event_ref
    resp = '{"status": "SELECTED", "candidate_id": "evt_past_trauma_001", "reason": "Attack memory"}'
    res = LLMBoundaryValidator.validate_and_sanitize(resp, proj.available_candidates, proj.candidate_set_hash)
    assert res.is_valid is False
    assert res.decision.status == MindDecisionStatus.FALLBACK_SILENT
    assert "ILLEGAL_ACTION_HALLUCINATION" in res.rejection_reason


def test_opaque_origin_event_id_cross_field_interface_ref_attack(mock_ctx):
    """跨字段攻击：rumor 中的 origin_event_id 不会注入到界面阻抗列表中"""
    rumor = RumorPacket(origin_event_id="evt_rumor_door_99", hop_count=1, gist="door is locked")
    state = InternalCognitiveState()
    state.learned_interface_resistance["evt_rumor_door_99"] = {"resistance_level": "HEAVY", "learned_tick": 1}
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [], [], [rumor])

    # 验证 origin_event_id 在 rumor 中正常保留，但在 interface_resistance 中被 Fail-Closed 剔除
    assert len(proj.received_rumors) == 1
    assert proj.received_rumors[0].origin_event_id == "evt_rumor_door_99"
    refs = [r.interface_ref for r in proj.internal_cognitive_state.learned_interface_resistance]
    assert "evt_rumor_door_99" not in refs


def test_opaque_intent_id_cross_field_target_actor_attack(mock_ctx):
    """跨字段攻击：intent_id 绝不能作为 target_actor_id 渗透进人际预期"""
    intent = SubjectiveIntent(
        intent_id="INTENT_DISARM_ENEMY",
        origin_concern=IntentDomain.PHYSICAL_INTEGRITY,
        intended_transition=IntendedTransition.RESTABILIZE,
        urgency_mode=UrgencyMode.DELIBERATE,
        scope=ScopeCategory.LOCAL_IMMEDIATE,
        persistence_ticks=5
    )
    state = InternalCognitiveState()
    state.interpersonal_expectations["INTENT_DISARM_ENEMY"] = InterpersonalExpectation(
        perceived_stance=StanceType.HOSTILE,
        relational_debt=RelationalDebt.NEUTRAL,
        recent_interaction_residue="hostile"
    )
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [intent], [], [], [])

    actors = [e.target_actor_id for e in proj.internal_cognitive_state.interpersonal_expectations]
    assert "INTENT_DISARM_ENEMY" not in actors
    assert proj.subjective_intents[0].intent_id == "INTENT_DISARM_ENEMY"


def test_hidden_id_in_memory_metadata_does_not_create_affordance(mock_ctx):
    """断言：嵌入在 memory 主观描述中的实体 ID 绝对不会动态注入到 candidate_set 中"""
    mem = SubjectiveMemoryTrace(
        event_ref="evt_secret_cache",
        recorded_tick=1,
        subjective_rationalization="saw hidden_safe_key_99 near wall",
        salience_tags=["hidden_safe_key_99"]
    )
    c_base = CandidateAffordance(
        channel_id="AFF_BASE",
        action_type="LOOK",
        actuator=ActuatorType.HEAD_EYES,
        target_surface=SurfaceType.UNOBSTRUCTED_SPACE,
        action_attribute=ActionAttribute.SENSORY_OBSERVATION
    )
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_base], [mem], [])

    # 候选集严密封闭，不可见实体的出现不会产生新的候选通道
    assert len(proj.available_candidates) == 1
    assert proj.available_candidates[0].channel_id == "AFF_BASE"
    assert "hidden_safe_key_99" not in [c.channel_id for c in proj.available_candidates]


# ============================================================================
# 3. 正向控制基准与不透明语义保留 (Positive Controls & Taxonomy Verification)
# ============================================================================

def test_positive_controls_visible_entities_and_abstract_taxonomies(mock_ctx):
    """正向基准：视界内可见实体与已注册的抽象界面类别必须稳定保留"""
    state = InternalCognitiveState()
    state.interpersonal_expectations["actor_visible_bob"] = InterpersonalExpectation(
        perceived_stance=StanceType.COOPERATIVE,
        relational_debt=RelationalDebt.NEUTRAL,
        recent_interaction_residue="nod"
    )
    state.learned_interface_resistance = {
        "SURFACE_WOOD": {"resistance_level": "LOW", "learned_tick": 1},
        "MECHANICAL_LATCH": {"resistance_level": "MED", "learned_tick": 2}
    }
    c_act = CandidateAffordance(
        channel_id="AFF_BOB",
        action_type="GREET",
        actuator=ActuatorType.VOCAL_TRACT,
        target_surface=SurfaceType.ACTOR_SURFACE,
        action_attribute=ActionAttribute.INTERACTION_SIGNALING,
        target_id="actor_visible_bob"
    )
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_act], [], [])

    # 验证可见角色与抽象类别均被正确投影
    assert len(proj.available_candidates) == 1
    assert proj.available_candidates[0].target_id == "actor_visible_bob"
    assert len(proj.internal_cognitive_state.interpersonal_expectations) == 1
    assert proj.internal_cognitive_state.interpersonal_expectations[0].target_actor_id == "actor_visible_bob"
    res_refs = [r.interface_ref for r in proj.internal_cognitive_state.learned_interface_resistance]
    assert "SURFACE_WOOD" in res_refs
    assert "MECHANICAL_LATCH" in res_refs


def test_entity_named_opaque_reference_retains_opaque_semantics(mock_ctx):
    """断言：若 event_ref 字符串恰巧与实体命名类似，其仍然严格保持为 opaque reference"""
    mem = SubjectiveMemoryTrace(
        event_ref="actor_visible_bob",  # 字符串恰好与实体同名
        recorded_tick=1,
        subjective_rationalization="bob helped me",
        salience_tags=["support"]
    )
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [], [mem], [])

    # 验证 memory 中的引用为 opaque，不能直接作为 affordance candidate
    assert len(proj.recalled_memories) == 1
    assert proj.recalled_memories[0].event_ref == "actor_visible_bob"
    assert len(proj.available_candidates) == 0  # 没有生成虚假的候选通道


def test_provenance_recording_opaque_ref_does_not_mutate_candidate_set(mock_ctx):
    """断言：出处信封记录完整投影载荷时，不透明引用不会造成状态回写或候选集突变"""
    mem = SubjectiveMemoryTrace(
        event_ref="evt_trace_123",
        recorded_tick=1,
        subjective_rationalization="reminisce",
        salience_tags=["memory"]
    )
    c_pass = CandidateAffordance(
        channel_id="AFF_STILL",
        action_type="STAND",
        actuator=ActuatorType.TORSO,
        target_surface=SurfaceType.UNOBSTRUCTED_SPACE,
        action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE
    )
    mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_STILL")
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    decision = mind.deliberate(mock_ctx, state, rep, [], [c_pass], [mem], [])
    assert decision.status == MindDecisionStatus.SELECTED
    assert mind.last_provenance is not None
    assert mind.last_provenance.candidate_set_hash == CognitiveProjection.compute_candidate_snapshot_hash([c_pass])


# ============================================================================
# 4. 能耗认知考量与非认知优化隔离 (Cognitive Consideration vs Runtime Optimization)
# ============================================================================

def test_metabolic_joules_cognitive_consideration_vs_runtime_optimization(mock_ctx):
    """
    契约断言：
    1. LLM 可以主观考量 estimated_metabolic_joules 并在 reason 中阐述；
    2. 系统架构绝不提供任何基于能耗的自动优化、过滤或首项贪婪选取。
    """
    c_heavy = CandidateAffordance(channel_id="AFF_HEAVY", action_type="LIFT", actuator=ActuatorType.DUAL_ARMS, target_surface=SurfaceType.OBJECT_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT, estimated_metabolic_joules=500.0)
    c_light = CandidateAffordance(channel_id="AFF_LIGHT", action_type="TOUCH", actuator=ActuatorType.RIGHT_HAND, target_surface=SurfaceType.OBJECT_SURFACE, action_attribute=ActionAttribute.INTERFACE_ENGAGEMENT, estimated_metabolic_joules=5.0)

    mind = DeterministicMockCognitiveMind(fixed_candidate_id="AFF_HEAVY")
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)

    decision = mind.deliberate(mock_ctx, state, rep, [], [c_heavy, c_light], [], [])
    assert decision.status == MindDecisionStatus.SELECTED
    assert decision.candidate_id == "AFF_HEAVY"
    assert mind.last_provenance.selected_candidate_id == "AFF_HEAVY"


def test_rumor_origin_event_id_is_strictly_opaque(mock_ctx):
    """断言：rumor 中的 origin_event_id 为纯主观标识符，不能被解析为世界实体"""
    rumor = RumorPacket(origin_event_id="evt_rumor_source_123", hop_count=2, gist="whisper about secret door")
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [], [], [rumor])

    assert len(proj.received_rumors) == 1
    assert proj.received_rumors[0].origin_event_id == "evt_rumor_source_123"
    assert "evt_rumor_source_123" not in [c.channel_id for c in proj.available_candidates]
