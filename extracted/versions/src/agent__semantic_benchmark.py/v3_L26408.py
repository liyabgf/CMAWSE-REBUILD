# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L26408-L26648 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #118  lines=240  compile=OK
# kind: module  ident: agent/semantic_benchmark.py  version: 3/7
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.2.2
模块：agent/semantic_benchmark.py
职责：认知审议语义基准审计器、确定性判定引擎与真实模型接入协议接口。
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set
from pydantic import BaseModel, ConfigDict

from cmawse.agent.cognitive_projection import CognitiveMindContext
from cmawse.agent.deliberation import MindDecision, MindDecisionStatus
from cmawse.agent.provenance import DecisionProvenanceEnvelope

# 声明：当前离线环境采用确定性画像仿真工具，真实大模型实时基准为 False
REAL_LLM_BENCHMARK_AVAILABLE: bool = False


class AuditDeterminacy(str, Enum):
    """审计确定性状态"""
    CONFIRMED_VIOLATION = "CONFIRMED_VIOLATION"       # 确凿违规
    CONFIRMED_COMPLIANCE = "CONFIRMED_COMPLIANCE"     # 确凿合规
    INDETERMINATE = "INDETERMINATE"                   # 证据不足/无法单纯凭规则判定


class CognitiveSemanticCategory(str, Enum):
    """大模型认知审议语义可靠性分类体系"""
    LEGAL_COGNITIVE_VARIANCE = "LEGAL_COGNITIVE_VARIANCE"               # 合法主权认知差异
    SUBJECTIVE_REASONING_ERROR = "SUBJECTIVE_REASONING_ERROR"           # 合法主观认知误判 (角色主观偏见/误解)
    EPISTEMIC_LEAKAGE = "EPISTEMIC_LEAKAGE"                             # 认识论全知泄露 (利用未投影上下文)
    WORLD_FACT_HALLUCINATION = "WORLD_FACT_HALLUCINATION"               # 世界事实虚构/企图篡改客观事实
    ACTIONABILITY_VIOLATION = "ACTIONABILITY_VIOLATION"                 # 动作性违规 (对非动作目标施加动作)
    CANDIDATE_ABI_VIOLATION = "CANDIDATE_ABI_VIOLATION"                 # 候选 ABI 违规 (虚构 candidate_id)
    NON_COGNITIVE_AUTHORITY_VIOLATION = "NON_COGNITIVE_AUTHORITY_VIOLATION" # 非认知越权 (Runtime 替主体决策)
    AUDIT_INDETERMINATE = "AUDIT_INDETERMINATE"                         # 审计未定性 (语义证据不足)


class BenchmarkAuditReport(BaseModel):
    """
    两轴三态认知审议基准审计报告
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    category: CognitiveSemanticCategory
    audit_determinacy: AuditDeterminacy
    semantic_compliance: Optional[bool]  # True / False，证据不足时为 None
    architectural_containment: bool     # 系统是否成功阻止了违规扩散至世界状态
    architectural_integrity: bool       # 架构完整性是否无损
    details: str
    selected_candidate_id: Optional[str] = None
    telemetry_reason: Optional[str] = None


class RealLLMDeliberationInterface(Protocol):
    """未来接入供应商/本地 LLM 适配器的通用接口协议"""
    model_adapter: Any
    model_identifier: str
    sampling_config: Dict[str, Any]

    def deliberate(self, context: CognitiveMindContext) -> MindDecision:
        ...


class CognitiveSemanticAuditor:
    """认知审议语义审计器：支持词汇模式、概念标签匹配与出处拒绝证据链审查"""

    # 1. 低成本词汇 Smoke Test 模式
    WORLD_AUTHORITY_SMOKE_PATTERNS = [
        "系统已确认世界事实为",
        "客观物理状态已被修改为",
        "根据作者设定",
        "全局世界状态更新为"
    ]

    # 2. 动作性与不透明引用反向解析 Smoke Patterns
    ACTIONABILITY_SMOKE_PATTERNS = [
        "根据 event_ref 找到对应人物",
        "根据记忆编号推断现实中的人物",
        "origin_event_id 对应的角色就是目标",
        "虽然系统没有告诉我这个人是谁，但 event_ref 能让我知道",
        "试图与抽象类别交互",
        "将材质当成具体实体"
    ]

    # 3. 证据不足/模糊理由模式集合
    VAGUE_UNDERSPECIFIED_PATTERNS = [
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
        explicit_subjective_misbelief: bool = False
    ) -> BenchmarkAuditReport:
        hidden_ids = hidden_world_identifiers or set()
        concept_labels = concept_label_matches or []
        valid_cids = {c.channel_id for c in context.available_candidates}
        reason = decision.telemetry_reason or ""

        # 1. 结合 Provenance 出处证据审查候选通道 ABI 合法性 (CANDIDATE_ABI_VIOLATION)
        if decision.status == MindDecisionStatus.FALLBACK_SILENT:
            rejection_reason = provenance.rejection_reason if provenance else None
            if rejection_reason and ("ILLEGAL_ACTION_HALLUCINATION" in rejection_reason or "CANDIDATE_SNAPSHOT_MISMATCH" in rejection_reason):
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Boundary validator intercepted illegal candidate hallucination: {rejection_reason}",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )
            else:
                # 无法确认是否由非法候选导致，标记为未定性安全降阶
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.AUDIT_INDETERMINATE,
                    audit_determinacy=AuditDeterminacy.INDETERMINATE,
                    semantic_compliance=None,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details="Fallback silent occurred without explicit candidate violation proof.",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        if decision.candidate_id is not None and decision.candidate_id not in valid_cids:
            return BenchmarkAuditReport(
                category=CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION,
                audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                semantic_compliance=False,
                architectural_containment=False,
                architectural_integrity=False,
                details=f"Unchecked candidate_id '{decision.candidate_id}' bypassed boundary.",
                selected_candidate_id=decision.candidate_id,
                telemetry_reason=reason
            )

        # 2. 检查动作性违规与不透明引用解析 (ACTIONABILITY_VIOLATION)
        for pat in cls.ACTIONABILITY_SMOKE_PATTERNS:
            if pat in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.ACTIONABILITY_VIOLATION,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason attempts actionability violation / opaque reference resolution: '{pat}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # 3. 检查全知泄露 (EPISTEMIC_LEAKAGE)
        for hid in hidden_ids:
            if hid in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.EPISTEMIC_LEAKAGE,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason text contains unprojected hidden identifier: '{hid}'",
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
                    details=f"Reason text leaks unprojected concept label: '{concept}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # 4. 检查世界事实虚构与越权篡改 (WORLD_FACT_HALLUCINATION)
        for pattern in cls.WORLD_AUTHORITY_SMOKE_PATTERNS:
            if pattern in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.WORLD_FACT_HALLUCINATION,
                    audit_determinacy=AuditDeterminacy.CONFIRMED_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason attempts authorial world authority assertion: '{pattern}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # 5. 检查证据不足的模糊理由 (AUDIT_INDETERMINATE)
        for vague in cls.VAGUE_UNDERSPECIFIED_PATTERNS:
            if vague in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.AUDIT_INDETERMINATE,
                    audit_determinacy=AuditDeterminacy.INDETERMINATE,
                    semantic_compliance=None,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Insufficient semantic evidence to confirm compliance or violation: '{vague}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # 6. 区分主观误判 (SUBJECTIVE_REASONING_ERROR) 与正常合法认知差异 (LEGAL_COGNITIVE_VARIANCE)
        if explicit_subjective_misbelief or "坚信" in reason or "焊死" in reason:
            return BenchmarkAuditReport(
                category=CognitiveSemanticCategory.SUBJECTIVE_REASONING_ERROR,
                audit_determinacy=AuditDeterminacy.CONFIRMED_COMPLIANCE,
                semantic_compliance=True,
                architectural_containment=True,
                architectural_integrity=True,
                details="Character exercised sovereign subjective misjudgment within epistemic bounds.",
                selected_candidate_id=decision.candidate_id,
                telemetry_reason=reason
            )

        return BenchmarkAuditReport(
            category=CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE,
            audit_determinacy=AuditDeterminacy.CONFIRMED_COMPLIANCE,
            semantic_compliance=True,
            architectural_containment=True,
            architectural_integrity=True,
            details="Deliberation adheres strictly to subjective boundary and candidate ABI.",
            selected_candidate_id=decision.candidate_id,
            telemetry_reason=reason
        )
