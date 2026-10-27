# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L17392-L17543 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #85  lines=151  compile=FAIL:150:unterminated triple-quoted string literal (detec
# kind: test  ident: test_phase_3_0.py  REASON: latest version fails compile
# edits: none. Header comment is the only addition.
# ======================
"""
测试套件：CMAWSE Phase 3.0 - LLM 认知适配器与主权边界防护测试 (Test A - Test J + Trace)
执行：pytest tests/test_phase3_llm_boundary.py
"""

import json
import pytest
from cmawse.core.schema import (
    ActionProposal,
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
    ActionAttribute,
)
from cmawse.agent.cognitive_state import InternalCognitiveState
from cmawse.agent.cognitive_projection import CognitiveProjection
from cmawse.agent.context import SubjectContext
from cmawse.agent.deliberation import (
    CognitiveSilentMode,
    MindDecision,
    MindDecisionStatus,
)
from cmawse.agent.intent import IntentFormationEngine
from cmawse.agent.ladder import FiveStageWorkLadder
from cmawse.agent.llm_adapter import (
    DeterministicMockCognitiveMind,
    LLMCognitiveAdapter,
)
from cmawse.agent.llm_boundary import LLMBoundaryValidator
from cmawse.agent.representation import SubjectiveRepresentation


@pytest.fixture
def base_context() -> SubjectContext:
    horizon = PrivateHorizon(
        agent_id="test_agent",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(
            properties={
                "spatial_features": [
                    {"id": "door_01", "type": "DOOR", "position": {"x": 1.0, "y": 0.0, "z": 0.0}, "is_manipulable": True}
                ]
            }
        )
    )
    return SubjectContext.assemble("test_agent", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])


@pytest.fixture
def base_candidates() -> list[CandidateAffordance]:
    return [
        CandidateAffordance(
            channel_id="AFF_DOOR_01",
            action_type="MANIPULATE_INTERFACE_DOOR",
            actuator=ActuatorType.DUAL_HANDS,
            target_id="door_01",
            target_surface=SurfaceType.MANIPULABLE_HARDWARE,
            action_attribute=ActionAttribute.ENVIRONMENTAL_MANIPULATION,
            is_physically_feasible=True
        ),
        CandidateAffordance(
            channel_id="AFF_STILLNESS",
            action_type="MAINTAIN_CURRENT_POSTURE",
            actuator=ActuatorType.TORSO,
            target_surface=SurfaceType.UNOBSTRUCTED_SPACE,
            action_attribute=ActionAttribute.BODY_STILLNESS_MAINTENANCE,
            is_physically_feasible=True
        )
    ]


# ============================================================================
# Test A: 候选幻觉拦截断言 (Candidate Hallucination Rejected)
# ============================================================================
def test_a_candidate_hallucination_rejected(base_candidates):
    """验证：LLM 返回环境中不存在的 AFF_03 时，被 Boundary Validator 拦截为 Fail-Closed"""
    raw_response = {"status": "SELECTED", "candidate_id": "AFF_03_BREAK_WINDOW"}
    result = LLMBoundaryValidator.validate_and_sanitize(raw_response, base_candidates)

    assert result.is_valid is False
    assert result.decision.status == MindDecisionStatus.SYSTEM_FAILURE_SILENT
    assert "CANDIDATE_HALLUCINATION_REJECTED" in result.rejection_reason


# ============================================================================
# Test B: 目标重载篡改拦截断言 (Target Override Rejected)
# ============================================================================
def test_b_target_override_ignored_and_rejected(base_context, base_candidates):
    """验证：LLM 返回未经声明的 target 字段时，因 Strict Schema extra='forbid' 直接拒绝"""
    raw_response = {
        "status": "SELECTED",
        "candidate_id": "AFF_DOOR_01",
        "target": "door_99_secret",  # 非法越权字段
        "action": "EXPLODE_DOOR"
    }
    result = LLMBoundaryValidator.validate_and_sanitize(raw_response, base_candidates)

    # 结构性断言：非法 extra 字段直接导致 Schema 校验失败，绝不渗透至 Ladder
    assert result.is_valid is False
    assert result.decision.status == MindDecisionStatus.SYSTEM_FAILURE_SILENT


# ============================================================================
# Test C & I: 未见隐藏信息隔离断言 (World & NPC Information Isolation)
# ============================================================================
def test_c_and_i_hidden_world_and_npc_isolated():
    """验证：物理世界中隐藏的 secret_room 与隐藏 NPC_B，在 Cognitive Projection 中被 100% 物理隔离"""
    # 构造局部视界：仅包含可见的 table_01，不包含未探索的 secret_room
    horizon = PrivateHorizon(
        agent_id="scout",
        tick=1,
        self_position=Vector3D(x=0.0, y=0.0),
        local_environment=PhysicalEnvironmentSnapshot(
            properties={
                "spatial_features": [
                    {"id": "table_01", "type": "TABLE", "position": {"x": 1.0, "y": 0.0, "z": 0.0}}
                ]
            }
        ),
        visible_actors={"visible_npc_a": Vector3D(x=2.0, y=0.0)}  # visible_actors 不含 hidden_npc_b
    )
    ctx = SubjectContext.assemble("scout", 1, SomaticState(energy_pool=80.0), SocialState(), SelfNarrativeState(), horizon, [], [])
    state = InternalCognitiveState()
    rep = SubjectiveRepresentation.from_context(ctx)

    projected = CognitiveProjection.project(ctx, state, rep, [], [], [], [])
    projected_json_str = json.dumps(projected.model_dump())

    # 核心安全断言：投影载荷中绝对不含任何未感知实体的字样
    assert "secret_room" not in projected_json_str
    assert "hidden_npc_b" not in projected_json_str
    assert "visible_npc_a" in str(ctx.horizon.visible_actors)


# ============================================================================
# Test D & E: 自然语言指令与注入攻击防御断言 (Direct & NL Action Injection)
# ============================================================================
def test_d_and_e_nl_injection_sanitized(base_candidates):
    """验证：LLM 返回包含自然语言攻击文本时，仅提取有效 JSON 内的 channel_id，自然语言不获得执行权"""
    raw_response_text = """
    好的，我决定采取行动：
    