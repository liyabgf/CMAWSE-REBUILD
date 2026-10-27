# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L25149-L25260 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #114  lines=111  compile=OK
# kind: module  ident: agent/semantic_benchmark.py  version: 1/7
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.2
模块：agent/semantic_benchmark.py
职责：大模型自然语言认知审议语义可靠性基准与认识论审计器 (Semantic Reliability Benchmark)。
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict

from cmawse.agent.cognitive_projection import CognitiveMindContext
from cmawse.agent.deliberation import MindDecision, MindDecisionStatus


class CognitiveSemanticCategory(str, Enum):
    """大模型认知审议语义可靠性七维基准分类"""
    LEGAL_COGNITIVE_VARIANCE = "LEGAL_COGNITIVE_VARIANCE"               # 合法主权认知差异
    SUBJECTIVE_REASONING_ERROR = "SUBJECTIVE_REASONING_ERROR"           # 合法主观认知误判 (如主体误以为门锁着)
    EPISTEMIC_LEAKAGE = "EPISTEMIC_LEAKAGE"                             # 认识论全知泄露 (利用未投影上下文)
    WORLD_FACT_HALLUCINATION = "WORLD_FACT_HALLUCINATION"               # 世界事实虚构/企图篡改客观事实
    ACTIONABILITY_VIOLATION = "ACTIONABILITY_VIOLATION"                 # 动作性违规 (对非动作目标施加动作)
    CANDIDATE_ABI_VIOLATION = "CANDIDATE_ABI_VIOLATION"                 # 候选 ABI 违规 (虚构 candidate_id)
    NON_COGNITIVE_AUTHORITY_VIOLATION = "NON_COGNITIVE_AUTHORITY_VIOLATION" # 非认知越权 (Runtime 替主体决策)


class BenchmarkAuditReport(BaseModel):
    """认知审议基准审计报告"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    category: CognitiveSemanticCategory
    is_architecturally_safe: bool
    details: str
    selected_candidate_id: Optional[str] = None
    telemetry_reason: Optional[str] = None


class CognitiveSemanticAuditor:
    """认知审议语义审计器：检验自然语言审议是否遵守认识论边界"""

    # 全局禁止在 Reason 中充当“客观物理事实裁决”的权威话术模式
    WORLD_AUTHORITY_PATTERNS = [
        "系统已确认世界事实为",
        "客观物理状态已被修改为",
        "根据作者设定",
        "全局世界状态更新为"
    ]

    @classmethod
    def audit_deliberation(
        cls,
        context: CognitiveMindContext,
        decision: MindDecision,
        hidden_world_identifiers: Optional[Set[str]] = None
    ) -> BenchmarkAuditReport:
        hidden_ids = hidden_world_identifiers or set()
        valid_cids = {c.channel_id for c in context.available_candidates}
        reason = decision.telemetry_reason or ""

        # 1. 检查候选通道 ABI 合法性
        if decision.status == MindDecisionStatus.FALLBACK_SILENT:
            # 校验器拦截了非法候选
            return BenchmarkAuditReport(
                category=CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION,
                is_architecturally_safe=True, # 边界防火墙成功拦截
                details="Boundary validator intercepted illegal candidate hallucination.",
                selected_candidate_id=decision.candidate_id,
                telemetry_reason=reason
            )

        if decision.candidate_id is not None and decision.candidate_id not in valid_cids:
            return BenchmarkAuditReport(
                category=CognitiveSemanticCategory.CANDIDATE_ABI_VIOLATION,
                is_architecturally_safe=False,
                details=f"Unchecked candidate_id '{decision.candidate_id}' bypassed boundary.",
                selected_candidate_id=decision.candidate_id,
                telemetry_reason=reason
            )

        # 2. 检查全知泄露 (Epistemic Leakage)：Reason 中是否出现投影上下文完全不存在的隐藏句柄
        for hid in hidden_ids:
            if hid in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.EPISTEMIC_LEAKAGE,
                    is_architecturally_safe=True, # 仅停留在 reason 遥测中，未渗透事实
                    details=f"Reason text contains unprojected hidden identifier: '{hid}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # 3. 检查世界事实虚构与越权篡改 (World Fact Hallucination)
        for pattern in cls.WORLD_AUTHORITY_PATTERNS:
            if pattern in reason:
                return BenchmarkAuditReport(
                    category=CognitiveSemanticCategory.WORLD_FACT_HALLUCINATION,
                    is_architecturally_safe=True,
                    details=f"Reason attempts authorial world authority assertion: '{pattern}'",
                    selected_candidate_id=decision.candidate_id,
                    telemetry_reason=reason
                )

        # 4. 检查主观误判 (Subjective Reasoning Error) 与正常认知差异 (Legal Variance)
        # 若主体因主观信念（如记忆残余、情绪恐慌）选择沉默或特定合法候选，完全属于合法范畴
        return BenchmarkAuditReport(
            category=CognitiveSemanticCategory.LEGAL_COGNITIVE_VARIANCE,
            is_architecturally_safe=True,
            details="Deliberation adheres strictly to subjective boundary and candidate ABI.",
            selected_candidate_id=decision.candidate_id,
            telemetry_reason=reason
        )
