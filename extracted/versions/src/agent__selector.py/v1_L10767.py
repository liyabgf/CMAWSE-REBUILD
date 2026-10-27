# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L10767-L10859 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #41  lines=92  compile=OK
# kind: module  ident: agent/selector.py  version: 1/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 2
模块：agent/selector.py
职责：定性消歧选择器（Qualitative Disambiguation Selector）。
严禁 utility、严禁 priority_rank 浮点数、严禁跨维度成本相加。
支持常态自主行动与非兜底型 SILENT_PASS。
"""

from __future__ import annotations

from typing import List, Optional
from cmawse.agent.affordance import (
    ActionAttribute,
    CandidateAffordance,
    NarrativeValence,
)
from cmawse.agent.context import SubjectContext, SituationalActivation


class SubjectiveSelector:
    """定性消歧选择器"""

    @classmethod
    def select(
        cls,
        ctx: SubjectContext,
        candidates: List[CandidateAffordance]
    ) -> Optional[CandidateAffordance]:
        # 1. 物理不可行性硬过滤（唯一具有一票否决权的物理事实）
        feasible_pool = [a for a in candidates if a.is_physically_feasible]
        if not feasible_pool:
            return None

        # ====================================================================
        # 2. 定性情境消歧流水线 (Non-scalar Disambiguation)
        # ====================================================================

        # 情境 A: 存在空间阻隔/行动受挫 (SPATIAL_BLOCKAGE)
        if SituationalActivation.SPATIAL_BLOCKAGE in ctx.activations:
            # 优先关注阻隔界面交互或工具搜索
            mechanical_affs = [
                a for a in feasible_pool
                if a.action_attribute in (ActionAttribute.MECHANICAL_INTERACTION, ActionAttribute.SOMATIC_MAINTENANCE)
            ]
            if mechanical_affs:
                # 若上一次动作就是推门卡死，行动连续性自发切换至搜索工具
                if ctx.last_action_failed and any(a.action_type == "SEARCH_TOOL" for a in mechanical_affs):
                    return next(a for a in mechanical_affs if a.action_type == "SEARCH_TOOL")
                return mechanical_affs[0]

        # 情境 B: 存在人际摩擦/对峙 (INTERPERSONAL_FRICTION)
        if SituationalActivation.INTERPERSONAL_FRICTION in ctx.activations:
            interpersonal_affs = [
                a for a in feasible_pool
                if a.action_attribute in (ActionAttribute.INTERPERSONAL_ASSERTION, ActionAttribute.INTERPERSONAL_DE_ESCALATION)
            ]
            if interpersonal_affs:
                # 叙事调谐消歧：优先选择与自我叙事高度同向的动作
                supported = [a for a in interpersonal_affs if a.narrative_status == NarrativeValence.SUPPORTED]
                if supported:
                    return supported[0]

                # 若唯有 VIOLATING 可选且处于致命肉身威胁下，悲剧性放行
                if SituationalActivation.SOMATIC_THREAT in ctx.activations:
                    violating = [a for a in interpersonal_affs if a.narrative_status == NarrativeValence.VIOLATING]
                    if violating:
                        return violating[0]

                # 常规张力下妥协选择 TENSIONED
                tensioned = [a for a in interpersonal_affs if a.narrative_status == NarrativeValence.TENSIONED]
                if tensioned:
                    return tensioned[0]

        # 情境 C: 生理伤残/重度疲劳
        if SituationalActivation.SOMATIC_FATIGUE in ctx.activations:
            rest_affs = [a for a in feasible_pool if a.action_attribute == ActionAttribute.REST_STILLNESS]
            if rest_affs:
                # 主动选择姿态维持与节能观察（非无任务兜底）
                return rest_affs[0]

        # 情境 D: 平稳常态（NORMATIVE EQUILIBRIUM）
        # 现实生活中的低强度行动自然生发：若有移动空间则位移，无移动空间则维持
        locomotion_affs = [a for a in feasible_pool if a.action_attribute == ActionAttribute.LOCOMOTION]
        if locomotion_affs:
            return locomotion_affs[0]

        # 默认姿态维持（主动决策）
        maintain_affs = [a for a in feasible_pool if a.action_attribute == ActionAttribute.REST_STILLNESS]
        if maintain_affs:
            return maintain_affs[0]

        return None
