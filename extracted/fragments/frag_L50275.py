# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L50275-L50352 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #140  lines=77  compile=OK
# kind: fragment  ident: frag_L50275.py
# edits: none. Header comment is the only addition.
# ======================
"""
CMAWSE-Core: 最小可运行因果运行时架构
仅包含状态机、物理约束、不可变账本与严格白名单边界。
"""
from __future__ import annotations
import copy
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# ============================================================================
# 1. 核心状态与不可变结构
# ============================================================================

class ActionExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    IMPEDED_ENERGY = "IMPEDED_ENERGY"         # 动能未跨越环境势垒
    IMPEDED_GEOMETRY = "IMPEDED_GEOMETRY"     # 几何碰撞或距离不满足
    REJECTED_INVALID_ID = "REJECTED_INVALID_ID" # 虚构或非法通道ID
    SILENT_PASS = "SILENT_PASS"               # 主动静默

@dataclass(frozen=True)
class Position2D:
    x: float
    y: float

    def distance_to(self, other: Position2D) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

@dataclass(frozen=True)
class AffordanceChannel:
    channel_id: str
    target_object_id: str
    action_verb: str
    base_metabolic_cost: float

@dataclass(frozen=True)
class ObservationSlice:
    tick: int
    agent_id: str
    self_position: Position2D
    self_energy: float
    visible_objects: Dict[str, Position2D]
    available_channels: Tuple[AffordanceChannel, ...]

@dataclass(frozen=True)
class ActionProposal:
    agent_id: str
    tick: int
    selected_channel_id: Optional[str]
    telemetry_reason: str = ""

@dataclass(frozen=True)
class EventEntry:
    event_id: str
    tick: int
    initiator_id: str
    channel_id: Optional[str]
    status: ActionExecutionStatus
    applied_patches: Tuple[Dict[str, Any], ...]
    telemetry_reason: str

# ============================================================================
# 2. 全局世界状态容器 (仅允许通过原子操作更新)
# ============================================================================

@dataclass(frozen=True)
class GlobalWorldState:
    tick: int
    agent_positions: Dict[str, Position2D]
    agent_energies: Dict[str, float]
    object_positions: Dict[str, Position2D]
    # 核心物理隐变量 (对 Agent 完全不可见)
    latent_friction_map: Dict[str, float]  # object_id -> friction coefficient
    latent_interventions: Dict[str, Any]   # 外部强制覆盖表
