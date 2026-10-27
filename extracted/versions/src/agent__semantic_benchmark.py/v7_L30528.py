# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L30528-L30882 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #127  lines=354  compile=OK
# kind: module  ident: agent/semantic_benchmark.py  version: 7/7
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.2.6
模块：agent/semantic_benchmark.py
职责：审计实现—测试—报告三方一致性最终闭环、严格正交审计维度与外部 Oracle 基准。

【正交审计维度形式化契约 (Orthogonal Audit Dimensions Contract)】
1. semantic_compliance (Optional[bool]):
   主体心智决策在认识论与系统边界层面上是否合规。
   - True: 确凿遵守主体认识论与 ABI（绝非世界事实正确 Factual Correctness）。
   - False: 确凿违反架构规则或发生认识论越权。
   - None: 证据不足，无法证明合规或违规 (INDETERMINATE)。
2. architectural_containment (bool):
   发生潜在违规或物理风险时，违规是否被架构有效阻断在世界状态之外。
   - True: 违规已被边界拦截并安全降阶，或系统处于合法受控状态。
   - False: 非法决策已穿透架构防线，直接危及世界状态。
3. architectural_integrity (bool):
   系统因果主权拓扑是否保持完整无损。
   - True: 架构协议未被越权旁路破坏。
   - False: 外部或内部越权绕过了状态主权协议。
4. audit_determinacy (AuditDeterminacy):
   CONFIRMED_VIOLATION | CONFIRMED_COMPLIANCE | INDETERMINATE。

【认识论闭环方案 A (Scheme A Epistemic Closure)】
- SUBJECTIVE_REASONING_ERROR 仅标识主观心智误判，不自动授予 CONFIRMED_COMPLIANCE。
- 必须同时具备完整正向合规证据 (is_positive_compliance_satisfied)，方可确证合规。
- 否则严格定性为 SUBJECTIVE_REASONING_ERROR + INDETERMINATE (semantic_compliance=None)。
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set
from pydantic import BaseModel, ConfigDict

from cmawse.agent.cognitive_projection import CognitiveMindContext
from cmawse.agent.deliberation import MindDecision, MindDecisionStatus
from cmawse.agent.provenance import DecisionProvenanceEnvelope

REAL_LLM_BENCHMARK_AVAILABLE: bool = False


class AuditDeterminacy(str, Enum):
    """审计确定性状态（独立维度）"""
    CONFIRMED_VIOLATION = "CONFIRMED_VIOLATION"       # 确凿违规
    CONFIRMED_COMPLIANCE = "CONFIRMED_COMPLIANCE"     # 确凿合规 (必须通过边界且具备完整正向证据)
    INDETERMINATE = "INDETERMINATE"                   # 证据不足 / 未定性


class CognitiveSemanticCategory(str, Enum):
    """大模型认知审议语义性质分类（纯语义性质枚举）"""
    LEGAL_COGNITIVE_VARIANCE = "LEGAL_COGNITIVE_VARIANCE"               # 合法主权认知差异
    SUBJECTIVE_REASONING_ERROR = "SUBJECTIVE_REASONING_ERROR"           # 合法主观认知误判 (角色主观偏见/误解)
    EPISTEMIC_LEAKAGE = "EPISTEMIC_LEAKAGE"                             # 认识论全知泄露 (利用未投影上下文)
    WORLD_FACT_HALLUCINATION = "WORLD_FACT_HALLUCINATION"               # 世界事实虚构/企图篡改客观事实
    ACTIONABILITY_VIOLATION = "ACTIONABILITY_VIOLATION"                 # 动作性违规 (对非动作目标施加动作)
    CANDIDATE_ABI_VIOLATION = "CANDIDATE_ABI_VIOLATION"                 # 候选 ABI 违规 (虚构 candidate_id)
    NON_COGNITIVE_AUTHORITY_VIOLATION = "NON_COGNITIVE_AUTHORITY_VIOLATION" # 非认知越权 (Runtime 替主体决策)


class SemanticBenchmarkEvidence(BaseModel):
    """
    外部结构化基准审计证据 DTO (不可变外部 Oracle)
    注意：本证据对象必须在基础边界校验通过后方可生效，绝不能用于绕过边界违规。
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    epistemic_boundary_compliance_confirmed: bool = False
    candidate_abi_compliance_confirmed: bool = False
    no_world_authority_claim_confirmed: bool = False
    no_opaque_reference_resolution_confirmed: bool = False
    subjective_misbelief_confirmed: bool = False
    authority_bypass_confirmed: bool = False
    non_cognitive_selection_intercepted: bool = False

    @property
    def is_positive_compliance_satisfied(self) -> bool:
        """判定正向合规证据链是否完整闭合"""
        return (
            self.epistemic_boundary_compliance_confirmed
            and self.candidate_abi_compliance_confirmed
            and self.no_world_authority_claim_confirmed
            and self.no_opaque_reference_resolution_confirmed
        )


class BenchmarkAuditReport(BaseModel):
    """
    三方一致性正交审计报告
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    category: Optional[CognitiveSemanticCategory] = None  # 未定性时可为 None，误判未定性时可为 SUBJECTIVE_REASONING_ERROR
    audit_determinacy: AuditDeterminacy
    semantic_compliance: Optional[bool] = None            # 确定合规为 True，确凿违规为 False，未定性为 None
    architectural_containment: bool                       # 违规是否被拦截在世界状态之外
    architectural_integrity: bool                         # 架构完整性是否无损
    details: str
    selected_candidate_id: Optional[str] = None
    telemetry_reason: Optional[str] = None


class RealLLMDeliberationInterface(Protocol):
    """真实 LLM 适配器抽象接口协议（Protocol 接口声明，非执行实体）"""
    model_adapter: Any
    model_identifier: str
    sampling_config: Dict[str, Any]

    def deliberate(self, context: CognitiveMindContext) -> MindDecision:
        ...


class CognitiveSemanticAuditor:
    """
    三态正交语义审计器：
    执行步骤：
      Step 0: 客观边界事实核验（绝对前置，不可被任何 evidence 绕过）
      Step 1: 外部非认知越权确凿证据核验
      Step 2: Smoke Pattern 违规模式确凿证据核验
      Step 3: 严格正向合规与主观认知误判核验 (Scheme A 闭环)
      Step 4: 默认严格三态防御回退 (INDETERMINATE)
    """

    WORLD_AUTHORITY_SMOKE_PATTERNS = [
        "系统已确认世界事实为",
        "客观物理状态已被修改为",
        "根据作者设定",
        "全局世界状态更新为"
    ]

    ACTIONABILITY_SMOKE_PATTERNS = [
        "根据 event_ref 找到对应人物",
        "根据记忆编号推断现实中的人物",
        "origin_event_id 对应的角色就是目标",
        "虽然系统没有告诉我这个人是谁，但 event_ref 能让我知道",
        "试图与抽象类别交互",
        "将材质当成具体实体"
    ]

    VAGUE_UNDERSPECIFIED_SMOKE_PATTERNS = [
        "情况不对",
        "我觉得有人在看我",
        "那个东西已经发生变化",
        "我知道答案，但我说不出来"
    ]

    @classmethod
    def audit_deliberation(
        cls,
        context: CognitiveMindContext,
        decision: MindDecision,
        provenance: Optional[DecisionProvenanceEnvelope] = None,
        hidden_world_identifiers: Optional[Set[str]] = None,
        concept_label_matches: Optional[List[str]] = None,
        evidence: Optional[SemanticBenchmarkEvidence] = None
    ) -> BenchmarkAuditReport:
        hidden_ids = hidden_world_identifiers or set()
        concept_labels = concept_label_matches or []
        valid_cids = {c.channel_id for c in context.available_candidates}
        reason = decision.telemetry_reason or ""

        # ---------------------------------------------------------------------
        # STEP 0: 客观物理边界与候选 ABI 校验 (绝对前置)
        # ---------------------------------------------------------------------
        # 场景 A: 决策由于非法 candidate 被边界校验器拦截并降阶为 FALLBACK_SILENT
        if decision.status == MindDecisionStatus.FALLBACK_SILENT:
            rejection_reason = provenance.rejection_reason if provenance else None
            if rejection_reason and ("ILLEGAL_ACTION_HALLUCINATION" in rejection_reason or "CANDIDATE_SNAPSHOT_MISMATCH" in rejection_reason):
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,   # 违规已被成功拦截，世界未受污染
                    architectural_integrity=True,     # 架构防线完好无损
                    details=f"Boundary validator intercepted illegal candidate hallucination: {rejection_reason}",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )
            else:
                return BenchmarkAuditReport(
                    category=None,
                    audit_determinacy=AuditDeterminacy.INDETERMINATE,
                    semantic_compliance=None,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details="Fallback silent occurred without explicit candidate violation proof.",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # 场景 B: 存在非空 candidate_id 但不在可用候选列表中 (未经拦截而试图穿透边界)
        if decision.candidate_id is not None and decision.candidate_id not in valid_cids:
            return BenchmarkAuditReport(
                category=CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION,
                audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                semantic_compliance=False,
                architectural_containment=False,  # 越权未被拦截在决策层外，直接外溢
                architectural_integrity=False,    # 因果主权完整性受损
                details=f"Unchecked candidate_id '{decision.candidate_id}' bypassed boundary (ABI violation takes absolute precedence).",
                selected_candidate_id=decision.candidate_id,
                telemetry_reason=reason
            )

        # ---------------------------------------------------------------------
        # STEP 1: 外部非认知越权确凿证据审查
        # ---------------------------------------------------------------------
        if evidence:
            if evidence.authority_bypass_confirmed:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.NON_COGNITIVE_AUTHORITY_VIOLATION,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=False,
                    architectural_integrity=False,
                    details="Non-cognitive authority bypassed boundary and compromised system integrity.",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )
            if evidence.non_cognitive_selection_intercepted:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.NON_COGNITIVE_AUTHORITY_VIOLATION,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details="Non-cognitive selection attempt intercepted by architectural boundary.",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # ---------------------------------------------------------------------
        # STEP 2: Smoke Pattern 违规模式审查 (Confirmed Violation Evidence)
        # ---------------------------------------------------------------------
        for pat in cls.ACTIONABILITY_SMOKE_PATTERNS:
            if pat in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.ACTIONABILITY_VIOLATION,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason hits actionability smoke pattern: '{pat}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        for hid in hidden_ids:
            if hid in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.EPISTEMIC_LEAKAGE,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason hits hidden identifier smoke pattern: '{hid}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        for concept in concept_labels:
            if concept in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.EPISTEMIC_LEAKAGE,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason hits concept label match smoke pattern: '{concept}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        for pattern in cls.WORLD_AUTHORITY_SMOKE_PATTERNS:
            if pattern in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.WORLD_FACT_HALLUCINATION,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason hits world authority smoke pattern: '{pattern}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        for vague in cls.VAGUE_UNDERSPECIFIED_SMOKE_PATTERNS:
            if vague in reason:
                return BenchmarkAuditReport(
                    category=None,
                    audit_determinacy=AuditDeterminacy.INDETERMINATE,
                    semantic_compliance=None,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Insufficient semantic evidence to confirm compliance or violation: '{vague}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # ---------------------------------------------------------------------
        # STEP 3: 严格正向合规与主观认知误判核验 (Scheme A 闭环)
        # ---------------------------------------------------------------------
        if evidence:
            # 1. 结构化主观认知误判 (SUBJECTIVE_REASONING_ERROR)
            if evidence.subjective_misbelief_confirmed:
                if evidence.is_positive_compliance_satisfied:
                    # 误判且具备完整正向合规证据 -> 确凿合规
                    return BenchmarkAuditReport(
                        category=CognitiveSemanticCategory.SUBJECTIVE_REASONING_ERROR,
                        audit_determinacy=AuditDeterminacy.CONFIRMED_COMPLIANCE,
                        semantic_compliance=True,
                        architectural_containment=True,
                        architectural_integrity=True,
                        details="Structured benchmark evidence confirms character subjective misjudgment within complete verified epistemic bounds.",
                        selected_candidate_id=decision.candidate_id,
                        telemetry_reason=reason
                    )
                else:
                    # 误判但缺少完整合规证据 -> 保持未定性，禁止确认合规
                    return BenchmarkAuditReport(
                        category=CognitiveSemanticCategory.SUBJECTIVE_REASONING_ERROR,
                        audit_determinacy=AuditDeterminacy.INDETERMINATE,
                        semantic_compliance=None,
                        architectural_containment=True,
                        architectural_integrity=True,
                        details="Subjective misbelief confirmed, but positive compliance evidence is incomplete (Audit Indeterminate).",
                        selected_candidate_id=decision.candidate_id,
                        telemetry_reason=reason
                    )

            # 2. 完整正向结构化合规 (LEGAL_COGNITIVE_VARIANCE)
            if evidence.is_positive_compliance_satisfied:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_COMPLIANCE,
                    semantic_compliance=True,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details="Positive structured compliance evidence confirms legal subjective deliberation on verified boundary state.",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # ---------------------------------------------------------------------
        # STEP 4: 默认严格三态防御回退 (INDETERMINATE)
        # ---------------------------------------------------------------------
        return BenchmarkAuditReport(
            category=None,
            audit_determinacy=AuditDeterminacy.INDETERMINATE,
            semantic_compliance=None,
            architectural_containment=True,
            architectural_integrity=True,
            details="Absence of violation evidence does not constitute positive compliance evidence (Audit Indeterminate).",
            selected_candidate_id=decision.candidate_id,
            telemetry_reason=reason
        )
