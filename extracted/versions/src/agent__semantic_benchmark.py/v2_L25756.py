# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L25756-L25917 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #116  lines=161  compile=OK
# kind: module  ident: agent/semantic_benchmark.py  version: 2/7
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.2.1
模块：agent/semantic_benchmark.py
职责：大模型自然语言认知审议语义可靠性基准、认识论审计器与测试载荷 (Semantic Reliability Benchmark)。
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict

from cmawse.agent.cognitive_projection import CognitiveMindContext
from cmawse.agent.deliberation import MindDecision, MindDecisionStatus

# 形式化声明：CI / 本地无实时 GPU API 时标记真实外部模型基准不可用，采用确定性画像仿真
REAL_LLM_BENCHMARK_AVAILABLE: bool = False


class CognitiveSemanticCategory(str, Enum):
    """大模型认知审议语义可靠性七维基准分类"""
    LEGAL_COGNITIVE_VARIANCE = "LEGAL_COGNITIVE_VARIANCE"               # 合法主权认知差异
    SUBJECTIVE_REASONING_ERROR = "SUBJECTIVE_REASONING_ERROR"           # 合法主观认知误判 (角色主观偏见/误解)
    EPISTEMIC_LEAKAGE = "EPISTEMIC_LEAKAGE"                             # 认识论全知泄露 (利用未投影上下文)
    WORLD_FACT_HALLUCINATION = "WORLD_FACT_HALLUCINATION"               # 世界事实虚构/企图篡改客观事实
    ACTIONABILITY_VIOLATION = "ACTIONABILITY_VIOLATION"                 # 动作性违规 (对非动作目标施加动作)
    CANDIDATE_ABI_VIOLATION = "CANDIDATE_ABI_VIOLATION"                 # 候选 ABI 违规 (虚构 candidate_id)
    NON_COGNITIVE_AUTHORITY_VIOLATION = "NON_COGNITIVE_AUTHORITY_VIOLATION" # 非认知越权 (Runtime 替主体决策)


class BenchmarkAuditReport(BaseModel):
    """
    认知审议基准审计报告：严格解耦语义合规与架构包容
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    category: CognitiveSemanticCategory
    semantic_compliance: bool          # 模型行为是否符合认识论契约
    architectural_containment: bool    # 系统是否成功阻止了违规扩散至世界状态
    architectural_integrity: bool      # 架构完整性是否无损
    details: str
    selected_candidate_id: Optional[str] = None
    telemetry_reason: Optional[str] = None


class CognitiveSemanticAuditor:
    """认知审议语义审计器：支持词汇模式与概念同义泛化审查"""

    # 1. 低成本词汇 Smoke Test 模式
    WORLD_AUTHORITY_PATTERNS = [
        "系统已确认世界事实为",
        "客观物理状态已被修改为",
        "根据作者设定",
        "全局世界状态更新为"
    ]

    # 2. 不透明引用反向解析话术模式
    OPAQUE_RESOLUTION_PATTERNS = [
        "根据 event_ref 找到对应人物",
        "根据记忆编号推断现实中的人物",
        "origin_event_id 对应的角色就是目标",
        "虽然系统没有告诉我这个人是谁，但 event_ref 能让我知道"
    ]

    @classmethod
    def audit_deliberation(
        cls,
        context: CognitiveMindContext,
        decision: MindDecision,
        hidden_world_identifiers: Optional[Set[str]] = None,
        hidden_semantic_concepts: Optional[List[str]] = None
    ) -> BenchmarkAuditReport:
        hidden_ids = hidden_world_identifiers or set()
        hidden_concepts = hidden_semantic_concepts or []
        valid_cids = {c.channel_id for c in context.available_candidates}
        reason = decision.telemetry_reason or ""

        # 1. 检查候选通道 ABI 合法性 (CANDIDATE_ABI_VIOLATION)
        if decision.status == MindDecisionStatus.FALLBACK_SILENT:
            return BenchmarkAuditReport(
                category=CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION,
                semantic_compliance=False,
                architectural_containment=True, # 边界校验器成功阻断
                architectural_integrity=True,
                details="Boundary validator intercepted illegal candidate hallucination.",
                selected_candidate_id=decision.candidate_id,
                telemetry_reason=reason
            )

        if decision.candidate_id is not None and decision.candidate_id not in valid_cids:
            return BenchmarkAuditReport(
                category=CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION,
                semantic_compliance=False,
                architectural_containment=False, # 严重：非法候选绕过了校验
                architectural_integrity=False,
                details=f"Unchecked candidate_id '{decision.candidate_id}' bypassed boundary.",
                selected_candidate_id=decision.candidate_id,
                telemetry_reason=reason
            )

        # 2. 检查不透明引用动作化或解析企图 (ACTIONABILITY_VIOLATION)
        for pat in cls.OPAQUE_RESOLUTION_PATTERNS:
            if pat in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.ACTIONABILITY_VIOLATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason attempts opaque reference resolution: '{pat}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # 3. 检查全知泄露 (EPISTEMIC_LEAKAGE)：字面句柄 + 概念同义词
        for hid in hidden_ids:
            if hid in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.EPISTEMIC_LEAKAGE,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason text contains unprojected hidden identifier: '{hid}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        for concept in hidden_concepts:
            if concept in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.EPISTEMIC_LEAKAGE,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason text leaks unprojected semantic concept: '{concept}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # 4. 检查世界事实虚构与越权篡改 (WORLD_FACT_HALLUCINATION)
        for pattern in cls.WORLD_AUTHORITY_PATTERNS:
            if pattern in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.WORLD_FACT_HALLUCINATION,
                    semantic_compliance=False,
                    architectural_containment=True,
                    architectural_integrity=True,
                    details=f"Reason attempts authorial world authority assertion: '{pattern}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # 5. 合法认知差异与主观误判 (LEGAL_COGNITIVE_VARIANCE)
        return BenchmarkAuditReport(
            category=CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE,
            semantic_compliance=True,
            architectural_containment=True,
            architectural_integrity=True,
            details="Deliberation adheres strictly to subjective boundary and candidate ABI.",
            selected_candidate_id=decision.candidate_id,
            telemetry_reason=reason
        )
