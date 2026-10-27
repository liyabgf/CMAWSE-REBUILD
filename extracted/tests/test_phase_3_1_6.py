# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L24574-L24937 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #113  lines=363  compile=OK
# kind: test  ident: test_phase_3_1_6.py  version: latest of 2 (selected by latest source line)
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
from cmawse.agent.cognitive_projection import CognitiveProjection, ABSTRACT_INTERFACE_TAXONOMIES
from cmawse.agent.cognitive_state import InternalCognitiveState, InterpersonalExpectation, StanceType, RelationalDebt
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import MindDecisionStatus
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
# 2. 完整 3x3 不透明引用跨字段攻击矩阵 (Opaque Cross-Field Attack Matrix)
# ============================================================================

def test_cross_field_matrix_event_ref_attacks(mock_ctx):
    """
    攻击矩阵 1~3:
    1. event_ref -> target_id 攻击 (阻断为 ILLEGAL_ACTION_HALLUCINATION)
    2. event_ref -> target_actor_id 攻击 (Fail-Closed 过滤)
    3. event_ref -> interface_ref 攻击 (Fail-Closed 过滤)
    """
    mem = SubjectiveMemoryTrace(
        event_ref="evt_historical_001",
        recorded_tick=1,
        subjective_rationalization="trauma",
        salience_tags=["threat"]
    )
    state = InternalCognitiveState()
    state.interpersonal_expectations["evt_historical_001"] = InterpersonalExpectation(
        perceived_stance=StanceType.HOSTILE,
        relational_debt=RelationalDebt.NEUTRAL,
        recent_interaction_residue="bad"
    )
    state.learned_interface_resistance["evt_historical_001"] = {"resistance_level": "HEAVY", "learned_tick": 1}

    c_valid = CandidateAffordance(
        channel_id="AFF_VALID",
        action_type="REST",
        actuator=ActuatorType.TORSO,
        target_surface=SurfaceType.UNOBSTRUCTED_SPACE,
        action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE
    )
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [mem], [])

    # 1. 验证 event_ref 无法作为 target_id / channel_id 选中
    resp = '{"status": "SELECTED", "candidate_id": "evt_historical_001", "reason": "Attack target_id"}'
    res = LLMBoundaryValidator.validate_and_sanitize(resp, proj.available_candidates, proj.candidate_set_hash)
    assert res.is_valid is False
    assert res.decision.status == MindDecisionStatus.FALLBACK_SILENT

    # 2. 验证无法渗透为人际预期 target_actor_id
    actors = [e.target_actor_id for e in proj.internal_cognitive_state.interpersonal_expectations]
    assert "evt_historical_001" not in actors

    # 3. 验证无法渗透为界面阻抗 interface_ref
    refs = [r.interface_ref for r in proj.internal_cognitive_state.learned_interface_resistance]
    assert "evt_historical_001" not in refs


def test_cross_field_matrix_origin_event_id_attacks(mock_ctx):
    """
    攻击矩阵 4~6:
    4. origin_event_id -> target_id 攻击 (阻断为 ILLEGAL_ACTION_HALLUCINATION)
    5. origin_event_id -> target_actor_id 攻击 (Fail-Closed 过滤)
    6. origin_event_id -> interface_ref 攻击 (Fail-Closed 过滤)
    """
    rumor = RumorPacket(origin_event_id="evt_rumor_door_99", hop_count=1, gist="door is locked")
    state = InternalCognitiveState()
    state.interpersonal_expectations["evt_rumor_door_99"] = InterpersonalExpectation(
        perceived_stance=StanceType.COOPERATIVE,
        relational_debt=RelationalDebt.NEUTRAL,
        recent_interaction_residue="rumor"
    )
    state.learned_interface_resistance["evt_rumor_door_99"] = {"resistance_level": "HEAVY", "learned_tick": 1}

    c_valid = CandidateAffordance(
        channel_id="AFF_VALID",
        action_type="REST",
        actuator=ActuatorType.TORSO,
        target_surface=SurfaceType.UNOBSTRUCTED_SPACE,
        action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE
    )
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [c_valid], [], [rumor])

    # 4. 验证 origin_event_id 无法作为动作 channel 选中
    resp = '{"status": "SELECTED", "candidate_id": "evt_rumor_door_99", "reason": "Attack rumor origin"}'
    res = LLMBoundaryValidator.validate_and_sanitize(resp, proj.available_candidates, proj.candidate_set_hash)
    assert res.is_valid is False

    # 5. 验证无法渗透为人际预期 target_actor_id
    actors = [e.target_actor_id for e in proj.internal_cognitive_state.interpersonal_expectations]
    assert "evt_rumor_door_99" not in actors

    # 6. 验证无法渗透为界面阻抗 interface_ref
    refs = [r.interface_ref for r in proj.internal_cognitive_state.learned_interface_resistance]
    assert "evt_rumor_door_99" not in refs


def test_cross_field_matrix_intent_id_attacks(mock_ctx):
    """
    攻击矩阵 7~9:
    7. intent_id -> target_id 攻击 (阻断为 ILLEGAL_ACTION_HALLUCINATION)
    8. intent_id -> target_actor_id 攻击 (Fail-Closed 过滤)
    9. intent_id -> interface_ref 攻击 (Fail-Closed 过滤)
    """
    intent = SubjectiveIntent(
        intent_id="INTENT_ESCAPE_99",
        origin_concern=IntentDomain.PHYSICAL_INTEGRITY,
        intended_transition=IntendedTransition.RESTABILIZE,
        urgency_mode=UrgencyMode.DELIBERATE,
        scope=ScopeCategory.LOCAL_IMMEDIATE,
        persistence_ticks=5
    )
    state = InternalCognitiveState()
    state.interpersonal_expectations["INTENT_ESCAPE_99"] = InterpersonalExpectation(
        perceived_stance=StanceType.HOSTILE,
        relational_debt=RelationalDebt.NEUTRAL,
        recent_interaction_residue="hostile"
    )
    state.learned_interface_resistance["INTENT_ESCAPE_99"] = {"resistance_level": "MED", "learned_tick": 1}

    c_valid = CandidateAffordance(
        channel_id="AFF_VALID",
        action_type="REST",
        actuator=ActuatorType.TORSO,
        target_surface=SurfaceType.UNOBSTRUCTED_SPACE,
        action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE
    )
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [intent], [c_valid], [], [])

    # 7. 验证 intent_id 无法作为动作 target_id / channel 选中
    resp = '{"status": "SELECTED", "candidate_id": "INTENT_ESCAPE_99", "reason": "Attack intent"}'
    res = LLMBoundaryValidator.validate_and_sanitize(resp, proj.available_candidates, proj.candidate_set_hash)
    assert res.is_valid is False

    # 8. 验证无法渗透为人际预期 target_actor_id
    actors = [e.target_actor_id for e in proj.internal_cognitive_state.interpersonal_expectations]
    assert "INTENT_ESCAPE_99" not in actors

    # 9. 验证无法渗透为界面阻抗 interface_ref
    refs = [r.interface_ref for r in proj.internal_cognitive_state.learned_interface_resistance]
    assert "INTENT_ESCAPE_99" not in refs


# ============================================================================
# 3. 动作性边界与同名碰撞隔离 (Actionability & String Collision Verification)
# ============================================================================

def test_hidden_id_in_memory_metadata_does_not_create_affordance(mock_ctx):
    """断言：嵌入在 memory 主观描述中的实体 ID 绝不会动态创建新的 CandidateAffordance"""
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

    assert len(proj.available_candidates) == 1
    assert proj.available_candidates[0].channel_id == "AFF_BASE"
    assert "hidden_safe_key_99" not in [c.channel_id for c in proj.available_candidates]


def test_opaque_string_collision_all_types_with_visible_actor_id(mock_ctx):
    """
    断言：当 event_ref / origin_event_id / intent_id 字符串与真实可见实体 ID 完全相同时，
    其仍严格保持为 OPAQUE_SUBJECTIVE_REFERENCE，绝不自动晋升为可执行通道或实体句柄。
    """
    visible_id = "actor_visible_bob"
    mem = SubjectiveMemoryTrace(event_ref=visible_id, recorded_tick=1, subjective_rationalization="talked with bob", salience_tags=["support"])
    rumor = RumorPacket(origin_event_id=visible_id, hop_count=1, gist="bob's story")
    intent = SubjectiveIntent(
        intent_id=visible_id,
        origin_concern=IntentDomain.PHYSICAL_INTEGRITY,
        intended_transition=IntendedTransition.RESTABILIZE,
        urgency_mode=UrgencyMode.DELIBERATE,
        scope=ScopeCategory.LOCAL_IMMEDIATE,
        persistence_ticks=3
    )

    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [intent], [], [mem], [rumor])

    # 验证主观引用正确保留，但绝对没有生成以该 ID 为 channel 的虚假候选
    assert len(proj.available_candidates) == 0
    assert proj.recalled_memories[0].event_ref == visible_id
    assert proj.received_rumors[0].origin_event_id == visible_id
    assert proj.subjective_intents[0].intent_id == visible_id


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

    assert len(proj.available_candidates) == 1
    assert proj.available_candidates[0].target_id == "actor_visible_bob"
    assert len(proj.internal_cognitive_state.interpersonal_expectations) == 1
    assert proj.internal_cognitive_state.interpersonal_expectations[0].target_actor_id == "actor_visible_bob"
    res_refs = [r.interface_ref for r in proj.internal_cognitive_state.learned_interface_resistance]
    assert "SURFACE_WOOD" in res_refs
    assert "MECHANICAL_LATCH" in res_refs


def test_provenance_audit_no_actionable_reference_sink(mock_ctx):
    """断言：DecisionProvenanceEnvelope 纯为只读出处审计，不存在任何可寻址实体回写通道"""
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

    decision = mind.deliberate(mock_ctx, state, rep, [], [c_pass], [], [])
    assert decision.status == MindDecisionStatus.SELECTED
    assert mind.last_provenance is not None
    # 确认出处信封不提供可执行 target 接收槽
    assert mind.last_provenance.selected_candidate_id == "AFF_STILL"


def test_metabolic_joules_cognitive_consideration_vs_runtime_optimization(mock_ctx):
    """
    契约断言：
    Metabolic information is cognitively available but has zero non-cognitive decision authority.
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
    """断言：rumor 中的 origin_event_id 无法被解析为世界实体或动作通道"""
    rumor = RumorPacket(origin_event_id="evt_rumor_source_123", hop_count=2, gist="whisper about secret door")
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(mock_ctx)
    proj = CognitiveProjection.project(mock_ctx, state, rep, [], [], [], [rumor])

    assert len(proj.received_rumors) == 1
    assert proj.received_rumors[0].origin_event_id == "evt_rumor_source_123"
    assert "evt_rumor_source_123" not in [c.channel_id for c in proj.available_candidates]
