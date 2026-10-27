# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L13734-L13823 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #55  lines=89  compile=OK
# kind: module  ident: agent/selector.py  version: latest of 2 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 2
模块：agent/selector.py
职责：定性消歧选择器（Qualitative Disambiguation Selector）。
严禁行为树、严禁短路优先级分发、严禁 utility 打分，允许自主收敛至 SILENT_PASS。
"""

from __future__ import annotations

from typing import List, Optional
from cmawse.agent.affordance import (
    ActionAttribute,
    CandidateAffordance,
    NarrativeValence,
)
from cmawse.agent.context import SubjectContext


class SubjectiveSelector:
    """定性消歧选择器"""

    @classmethod
    def select(
        cls,
        ctx: SubjectContext,
        candidates: List[CandidateAffordance]
    ) -> Optional[CandidateAffordance]:
        # 1. 物理不可行性硬过滤（物理事实的一票否决权）
        feasible_pool = [a for a in candidates if a.is_physically_feasible]
        if not feasible_pool:
            return None

        # --------------------------------------------------------------------
        # 2. 具身行动连续性与挫败反思 (Action Continuity & Failure Feedback)
        # 若上一动作在特定客体上受挫，主动抑制在该客体上的相同通道
        # --------------------------------------------------------------------
        non_frustrated = [
            a for a in feasible_pool
            if not (ctx.last_action_failed and a.target_id == ctx.last_failed_target and a.action_attribute == ActionAttribute.MECHANICAL_INTERACTION)
        ]
        if not non_frustrated:
            return None

        # --------------------------------------------------------------------
        # 3. 焦点对齐与定性意图消歧 (Focus Alignment & Intentional Gating)
        # --------------------------------------------------------------------
        # 情境 A: 视界内存在直接可见的在场他人摩擦
        if ctx.horizon.visible_actors and "INTERPERSONAL_EXPOSURE" in ctx.activations:
            # 提取人际相关通道
            interpersonal_set = [
                a for a in non_frustrated
                if a.action_attribute in (ActionAttribute.INTERPERSONAL_ASSERTION, ActionAttribute.INTERPERSONAL_DE_ESCALATION)
            ]
            if interpersonal_set:
                # 寻找与自身叙事姿态完全一致的通道
                aligned = [a for a in interpersonal_set if a.narrative_status == NarrativeValence.SUPPORTED]
                if aligned:
                    # 确定性对齐首个焦点客体，但绝不执行全类别覆盖
                    return aligned[0]

                # 允许悲剧性违背：当受挫或威胁严重时，容忍 VIOLATING 通道执行
                if "SOMATIC_THREAT" in ctx.activations:
                    violating = [a for a in interpersonal_set if a.narrative_status == NarrativeValence.VIOLATING]
                    if violating:
                        return violating[0]

        # 情境 B: 感知到明确的空间物理结构交互界面（门体/装置）
        structural_set = [
            a for a in non_frustrated
            if a.action_attribute in (ActionAttribute.MECHANICAL_INTERACTION, ActionAttribute.LOCOMOTION)
            and a.target_id is not None
        ]
        if structural_set:
            return structural_set[0]

        # --------------------------------------------------------------------
        # 4. 常态平稳环境：自主静止观察（SILENT_PASS）与低强度维持并存
        # 绝无强迫行走，若无明确动能动员需求，自然收敛为姿态维持或观察（返回 None 触发静默）
        # --------------------------------------------------------------------
        if not ctx.activations:
            # 外部世界完全平静，身体处于稳态：返回 None，即保持 SILENT_PASS
            return None

        # 仅有轻微内部维持通道可选时，选择姿态维持
        resting_set = [a for a in non_frustrated if a.action_attribute == ActionAttribute.REST_STILLNESS]
        if resting_set:
            return resting_set[0]

        return None
