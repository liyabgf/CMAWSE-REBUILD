# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L1254-L1445 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #5  lines=191  compile=OK
# kind: module  ident: core/schema.py  version: 2/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：core/schema.py
职责：全局核心数据契约、四态解耦模型与运行时基础类型系统。
严禁包含具体角色、具体剧情与文学渲染层描述。
"""

from __future__ import annotations

import enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# 1. 做功阶梯公理模型 (Axiom 3)
# ============================================================================

class ActionStage(str, enum.Enum):
    """做功阶梯：动念至物理做功的五阶不可跳跃状态"""
    TOPIC = "Topic"              # 动念 / 语义共现
    INTENT = "Intent"            # 确立行动意向
    PLAN = "Plan"                # 形成运动规划
    COMMITMENT = "Commitment"    # 调动身体能量与生理承诺
    ACTION = "Action"            # 克服阻尼跨越势垒做功


# ============================================================================
# 2. Agent 内驱状态三元组（通用容器，非任务目标）
# ============================================================================

class SomaticState(BaseModel):
    """动物性生理状态通用张量"""
    model_config = ConfigDict(frozen=True)

    energy_pool: float = Field(..., ge=0.0, description="可用代谢总能量池")
    integrity: float = Field(default=100.0, ge=0.0, le=100.0, description="躯体物理完整度")
    load: float = Field(default=0.0, ge=0.0, description="生理/神经瞬时负荷")
    sensory_deprived: bool = Field(default=False, description="感官是否被物理剥夺")
    variables: Dict[str, float] = Field(default_factory=dict, description="可扩展生理微观变量")


class SocialState(BaseModel):
    """社会性规训与场域张量"""
    model_config = ConfigDict(frozen=True)

    rank: int = Field(default=0, description="形式阶层等级")
    surveillance_load: float = Field(default=0.0, ge=0.0, le=1.0, description="被观察与规训压力")
    variables: Dict[str, float] = Field(default_factory=dict, description="可扩展社会结构变量")


class SelfNarrativeState(BaseModel):
    """自洽性心理防御状态"""
    model_config = ConfigDict(frozen=True)

    defense_rigidity: float = Field(default=50.0, ge=0.0, le=100.0, description="认知防御刚性")
    dissonance: float = Field(default=0.0, ge=0.0, le=100.0, description="失调紧张度")
    constants: Dict[str, str] = Field(default_factory=dict, description="核心自我锚定常量")


# ============================================================================
# 3. 空间与物理环境底层模型
# ============================================================================

class Vector3D(BaseModel):
    """连续空间欧氏几何向量"""
    model_config = ConfigDict(frozen=True)

    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: Vector3D) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2) ** 0.5


class PhysicalEnvironmentSnapshot(BaseModel):
    """World Plane 提供的环境宏观与微观物理量（只读）"""
    model_config = ConfigDict(frozen=True)

    temperature: float = 20.0
    observation_pressure: float = Field(default=0.0, ge=0.0, le=1.0)
    friction_coefficient: float = Field(default=0.6, ge=0.0, le=1.0)
    micro_entropy_variable: float = Field(default=0.0, description="微观扰动熵采样值")
    properties: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 4. Proposal 系统 (Agent 唯一允许产出的行为意图，非事实)
# ============================================================================

class KinematicIntent(BaseModel):
    """物理动作力学诉求"""
    model_config = ConfigDict(frozen=True)

    target_id: Optional[str] = None
    applied_force: float = Field(ge=0.0, description="施加做功力道 (N)")
    effective_mass: float = Field(gt=0.0, description="动量等效质量 (kg)")
    intended_trajectory: Optional[Vector3D] = None
    is_contact_action: bool = True
    action_type: str


class VerbalIntent(BaseModel):
    """言语动作诉求"""
    model_config = ConfigDict(frozen=True)

    content: str
    intensity_db: float = Field(default=60.0, ge=0.0, description="分贝强度")


class ActionProposal(BaseModel):
    """
    主体行为提案。
    零事件轮合法性公理：is_silent_pass 为 True 时，为最高优先级合法状态。
    """
    model_config = ConfigDict(frozen=True)

    agent_id: str
    tick: int
    stage: ActionStage = ActionStage.ACTION
    is_silent_pass: bool = False
    kinematics: Optional[KinematicIntent] = None
    verbal: Optional[VerbalIntent] = None


# ============================================================================
# 5. RFC 6902 状态补丁协议
# ============================================================================

class RFC6902Patch(BaseModel):
    """RFC 6902 JSON Patch 纯操作契约"""
    model_config = ConfigDict(frozen=True)

    op: Literal["add", "remove", "replace", "move", "copy", "test"]
    path: str
    value: Optional[Any] = None
    from_path: Optional[str] = Field(default=None, alias="from")

    @field_validator("path")
    @classmethod
    def must_be_valid_json_pointer(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError(f"RFC 6902 Path 必须以 '/' 开头: {v}")
        return v


# ============================================================================
# 6. Event Ledger 核心事实协议 (唯一不可逆事实源)
# ============================================================================

class VerifiedEventEntry(BaseModel):
    """
    经 Arbiter 仲裁后落槌的客观事实条目。
    不包含渲染修辞，仅保留确定性的力学结果、声学物理发生及原子状态补丁。
    """
    model_config = ConfigDict(frozen=True)

    event_id: str
    tick_index: int
    timestamp: str
    causal_status: str = Field(description="仲裁因果判定码，如 SUCCESS, IMPEDED, DROPPED, DEADLOCK")
    resolved_kinematics: List[Dict[str, Any]] = Field(default_factory=list)
    acoustic_emissions: List[Dict[str, Any]] = Field(default_factory=list)
    state_patches: List[RFC6902Patch] = Field(default_factory=list)


# ============================================================================
# 7. Global World State 物理快照契约
# ============================================================================

class ActorSnapshot(BaseModel):
    """主体在物理世界的快照映射"""
    model_config = ConfigDict(frozen=True)

    position: Vector3D
    somatic: SomaticState
    social: SocialState
    self_narrative: SelfNarrativeState
    bound_objects: Dict[str, Any] = Field(default_factory=dict)


class GlobalWorldState(BaseModel):
    """全局世界状态快照 (由 Committer 唯一原子维护)"""
    model_config = ConfigDict(frozen=True)

    tick: int = 0
    timestamp: str = ""
    environment: PhysicalEnvironmentSnapshot = Field(default_factory=PhysicalEnvironmentSnapshot)
    actors: Dict[str, ActorSnapshot] = Field(default_factory=dict)
    objects: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
