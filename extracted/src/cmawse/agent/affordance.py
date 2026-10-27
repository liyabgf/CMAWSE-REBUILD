# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L10363-L10450 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #38  lines=87  compile=OK
# kind: module  ident: agent/affordance.py  version: latest of 1 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 2
模块：agent/affordance.py
职责：定义 Action Affordance 语义载体与具身通道契约。
严禁标量化，严禁使用全局通用动作枚举，强制具身部位与接触表面对齐。
"""

from __future__ import annotations

import enum
from typing import Any, Dict, Optional, Set
from pydantic import BaseModel, ConfigDict, Field

from cmawse.core.schema import Vector3D


class ActuatorType(str, enum.Enum):
    """具身执行器官/身体部位"""
    DUAL_LEGS = "DUAL_LEGS"
    RIGHT_LEG = "RIGHT_LEG"
    LEFT_LEG = "LEFT_LEG"
    DUAL_HANDS = "DUAL_HANDS"
    RIGHT_HAND = "RIGHT_HAND"
    LEFT_HAND = "LEFT_HAND"
    TORSO = "TORSO"
    VOCAL_TRACT = "VOCAL_TRACT"
    EYES_HEAD = "EYES_HEAD"


class SurfaceType(str, enum.Enum):
    """受力/接触目标客体表面"""
    FREE_SPACE = "FREE_SPACE"
    RIGID_DOOR_SURFACE = "RIGID_DOOR_SURFACE"
    RIGID_HANDLE = "RIGID_HANDLE"
    OBSTACLE_SURFACE = "OBSTACLE_SURFACE"
    GROUND_SURFACE = "GROUND_SURFACE"
    AGENT_BODY = "AGENT_BODY"
    TOOL_SURFACE = "TOOL_SURFACE"


class NarrativeValence(str, enum.Enum):
    """行动对核心自我认同的定性语义标记"""
    SUPPORTED = "SUPPORTED"
    TENSIONED = "TENSIONED"
    VIOLATING = "VIOLATING"


class ActionAttribute(str, enum.Enum):
    """行动质性情境分类"""
    REFLEX_PROTECTION = "REFLEX_PROTECTION"
    LOCOMOTION = "LOCOMOTION"
    MECHANICAL_INTERACTION = "MECHANICAL_INTERACTION"
    INTERPERSONAL_ASSERTION = "INTERPERSONAL_ASSERTION"
    INTERPERSONAL_DE_ESCALATION = "INTERPERSONAL_DE_ESCALATION"
    SOMATIC_MAINTENANCE = "SOMATIC_MAINTENANCE"
    REST_STILLNESS = "REST_STILLNESS"


class AffordancePreconditions(BaseModel):
    """动作成立的定性前提矩阵"""
    model_config = ConfigDict(frozen=True)

    requires_load_bearing: bool = False
    requires_free_path: bool = True
    requires_contact: bool = False
    max_reach_distance: float = 2.0
    required_tool: Optional[str] = None


class CandidateAffordance(BaseModel):
    """
    具体的具身可供性通道（Action Affordance）。
    绝非动作字符串，而是主体与环境界面形成的潜在动能/信号通路。
    """
    model_config = ConfigDict(frozen=True)

    channel_id: str = Field(description="通道全局语义唯一标识")
    action_type: str = Field(description="具身力学动作名 (如: LOCOMOTION_WALK, DOOR_PUSH)")
    actuator: ActuatorType = Field(description="调用的身体器官")
    target_id: Optional[str] = Field(default=None, description="目标客体或主体 ID")
    target_surface: SurfaceType = Field(description="接触的目标表面")
    spatial_vector: Vector3D = Field(default_factory=lambda: Vector3D(x=0.0, y=0.0, z=0.0))
    preconditions: AffordancePreconditions = Field(default_factory=AffordancePreconditions)
    narrative_status: NarrativeValence = Field(default=NarrativeValence.SUPPORTED)
    action_attribute: ActionAttribute = Field(default=ActionAttribute.LOCOMOTION)
    estimated_metabolic_joules: float = Field(default=5.0, ge=0.0)
    is_physically_feasible: bool = Field(default=True, description="唯一具有否决权的物理/身体可行性标记")
