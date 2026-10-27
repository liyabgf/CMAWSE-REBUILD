# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L155-L378 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #0  lines=223  compile=OK
# kind: module  ident: core/schema.py  version: 1/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）
模块：schema.py
职责：全局核心数据契约、四态解耦协议与类型系统规范。
"""

from __future__ import annotations

import enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# 枚举与基础常量
# ============================================================================

class ActionStage(str, enum.Enum):
    """做功阶梯公理：行为意图的五阶递进"""
    TOPIC = "Topic"              # 动念/言语萌芽
    INTENT = "Intent"            # 确立行动意图
    PLAN = "Plan"                # 形成运动规划
    COMMITMENT = "Commitment"    # 调动身体能量承诺
    ACTION = "Action"            # 克服阻尼跨越势垒做功


class AcousticSignature(str, enum.Enum):
    """声学特征标记"""
    WHISPER = "WHISPER"
    MUTTER = "MUTTER"
    CONVERSATIONAL = "CONVERSATIONAL"
    LOW_PITCH_HEAVY_BREATH = "LOW_PITCH_HEAVY_BREATH"
    STRANGLED_HIGH_PITCH = "STRANGLED_HIGH_PITCH"
    SHOUT = "SHOUT"


# ============================================================================
# Agent 内驱变量三元组 (非任务型架构核心)
# ============================================================================

class SomaticState(BaseModel):
    """动物性生理状态：直接影响做功阶梯克服能耗势垒的能力"""
    model_config = ConfigDict(frozen=True)

    fatigue: float = Field(default=0.0, ge=0.0, le=100.0, description="疲劳度 0-100")
    pain: float = Field(default=0.0, ge=0.0, le=100.0, description="躯体疼痛 0-100")
    sensory_overload: bool = Field(default=False, description="感官是否过载")
    hunger: float = Field(default=0.0, ge=0.0, le=100.0, description="饥饿值 0-100")
    adrenaline: float = Field(default=10.0, ge=0.0, le=100.0, description="肾上腺素水平")


class SocialState(BaseModel):
    """社会性状态：表征角色在社交场域中感受到的制度与规训压力"""
    model_config = ConfigDict(frozen=True)

    status_hierarchy: int = Field(default=0, description="相对阶层位阶（数字越大地位越高）")
    perceived_surveillance: float = Field(default=0.0, ge=0.0, le=100.0, description="被注视感/规制压力")
    shame: float = Field(default=0.0, ge=0.0, le=100.0, description="羞耻度/社交防御")


class SelfNarrativeState(BaseModel):
    """自洽性状态：角色维持自身叙事稳定的心理防御参数"""
    model_config = ConfigDict(frozen=True)

    core_belief: str = Field(description="核心不可动摇的自我认知信念")
    denial_level: float = Field(default=0.0, ge=0.0, le=100.0, description="对冲突事实的否认指数")
    cognitive_dissonance: float = Field(default=0.0, ge=0.0, le=100.0, description="认知失调张力")


# ============================================================================
# 空间与物理环境模型
# ============================================================================

class Coordinate3D(BaseModel):
    """三维欧几里得坐标（单位：米）"""
    model_config = ConfigDict(frozen=True)

    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: Coordinate3D) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2) ** 0.5


class SpatialFieldParams(BaseModel):
    """物理场域参数 (P/O 阻尼模型)"""
    model_config = ConfigDict(frozen=True)

    privacy_level: float = Field(default=1.0, ge=0.0, le=1.0, description="P: 私密性 (0公开/被注视 -> 1绝对私密)")
    observation_pressure: float = Field(default=0.0, ge=0.0, le=1.0, description="O: 规制压力 (0无规训 -> 1高压注视)")
    ambient_temp: float = Field(default=20.0, description="环境摄氏度")
    lighting_lux: float = Field(default=300.0, ge=0.0, description="照度 (勒克斯)")


# ============================================================================
# Proposal 系统：Agent 意图提议 (无直接写权限)
# ============================================================================

class KinematicVector(BaseModel):
    """微观物理动作意图动力学向量"""
    model_config = ConfigDict(frozen=True)

    target_agent_id: Optional[str] = None
    target_object_id: Optional[str] = None
    target_coordinate: Optional[Coordinate3D] = None
    force_magnitude: float = Field(default=1.0, ge=0.0, le=100.0, description="投入做功力道 (牛顿/标量标定)")
    mass_kg: float = Field(default=65.0, gt=0.0, description="施动主体物理质量 (kg)")
    action_description: str = Field(description="拟执行微观物理动作的客观描述")


class VerbalEmission(BaseModel):
    """拟言语发声"""
    model_config = ConfigDict(frozen=True)

    text: str
    acoustic: AcousticSignature = AcousticSignature.CONVERSATIONAL


class ActionProposal(BaseModel):
    """
    主体行为提案。
    在提交至 Causal Arbiter 前仅为可能发生的意图，不构成世界事实。
    """
    model_config = ConfigDict(frozen=True)

    agent_id: str
    tick: int
    stage: ActionStage = ActionStage.ACTION
    is_silent_pass: bool = Field(default=False, description="是否主动选择静默/挂起 (最高合法状态)")
    kinematics: Optional[KinematicVector] = None
    verbal: Optional[VerbalEmission] = None
    intended_preconditions: List[str] = Field(default_factory=list, description="该动作期望成立的前提")


# ============================================================================
# RFC 6902 JSON Patch 协议
# ============================================================================

class RFC6902Patch(BaseModel):
    """严格符合 RFC 6902 的原子状态修补协议"""
    model_config = ConfigDict(frozen=True)

    op: Literal["add", "remove", "replace", "move", "copy", "test"]
    path: str
    value: Optional[Any] = None
    from_path: Optional[str] = Field(default=None, alias="from")

    @field_validator("path")
    @classmethod
    def validate_json_pointer(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError(f"RFC 6902 路径必须以 '/' 开头: {v}")
        return v


# ============================================================================
# Event Ledger: 事实主权账本原子数据结构
# ============================================================================

class DialogueRecord(BaseModel):
    """已经实际发声并在空间中传播的对白记录"""
    model_config = ConfigDict(frozen=True)

    speaker: str
    phonetics: str
    acoustic_signature: AcousticSignature


class VerifiedEventEntry(BaseModel):
    """
    系统唯一事实源 (Single Source of Truth) 条目。
    一旦落槌进入 Event Ledger，具有单调递增、只读、不可撤销性。
    小说渲染、记忆重构、传闻演化皆为此条目的下游投影。
    """
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(description="全局唯一事实序列号 (例如: evt_20240101_0001)")
    tick_index: int = Field(ge=0, description="物理推进步长绝对索引")
    timestamp: str = Field(description="世界时钟物理时间字符串 (ISO 8601 或标准业务时间)")
    verified_physical_facts: List[str] = Field(
        default_factory=list,
        description="因果仲裁法庭确认生效的客观物理事实（白描、力学与位移）"
    )
    dialogue_emissions: List[DialogueRecord] = Field(
        default_factory=list,
        description="实际散逸至空间总线的对话切片"
    )
    state_patches: List[RFC6902Patch] = Field(
        default_factory=list,
        description="本事实对物理世界造成的确定性原子 RFC 6902 补丁集"
    )


# ============================================================================
# Global World State: 物理快照 (由 Committer 唯一维护)
# ============================================================================

class ActorPhysicalSnapshot(BaseModel):
    """在场主体的物理镜像"""
    model_config = ConfigDict(frozen=True)

    agent_id: str
    coordinate: Coordinate3D
    somatic: SomaticState
    social: SocialState
    self_narrative: SelfNarrativeState
    inventory: List[str] = Field(default_factory=list)


class GlobalWorldState(BaseModel):
    """
    全局物理场域当前快照。
    严禁任何组件直接原地突变，必须经由 State Committer 原子提交。
    """
    model_config = ConfigDict(frozen=True)

    tick: int = 0
    timestamp: str = "2024-01-01T08:00:00"
    spatial_params: SpatialFieldParams = Field(default_factory=SpatialFieldParams)
    actors: Dict[str, ActorPhysicalSnapshot] = Field(default_factory=dict)
    objects: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    world_flags: Dict[str, Any] = Field(default_factory=dict)
