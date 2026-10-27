# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L13406-L13519 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #53  lines=113  compile=OK
# kind: module  ident: agent/context.py  version: latest of 2 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 2
模块：agent/context.py
职责：装配纯净的 SubjectContext。
严格从 PrivateHorizon 提取真实存在的客体与物理特征，严禁凭空捏造不存在的世界实体。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field

from cmawse.core.schema import (
    ActorSnapshot,
    SelfNarrativeState,
    SocialState,
    SomaticState,
    Vector3D,
)
from cmawse.world.bus import PrivateHorizon
from cmawse.cognitive.memory import SubjectiveMemoryTrace
from cmawse.cognitive.rumor import RumorPacket


class PerceivedSpatialObject(BaseModel):
    """主体通过局部感官实际感知到的客观空间物理客体"""
    model_config = ConfigDict(frozen=True)

    object_id: str
    object_type: str  # 例: "DOOR", "OBSTACLE", "TOOL", "CONTAINER"
    position: Vector3D
    is_passable: bool = False
    is_interactive: bool = True
    properties: Dict[str, Any] = Field(default_factory=dict)


class SubjectContext(BaseModel):
    """主体私有局部现实（严格限制在视界与私有内存内）"""
    model_config = ConfigDict(frozen=True)

    agent_id: str
    tick: int
    somatic: SomaticState
    social: SocialState
    self_narrative: SelfNarrativeState
    horizon: PrivateHorizon
    recalled_memories: List[SubjectiveMemoryTrace] = Field(default_factory=list)
    received_rumors: List[RumorPacket] = Field(default_factory=list)
    perceived_objects: List[PerceivedSpatialObject] = Field(default_factory=list)
    activations: Set[str] = Field(default_factory=set)
    last_action_failed: bool = Field(default=False)
    last_failed_target: Optional[str] = Field(default=None)

    @classmethod
    def assemble(
        cls,
        agent_id: str,
        tick: int,
        somatic: SomaticState,
        social: SocialState,
        self_narrative: SelfNarrativeState,
        horizon: PrivateHorizon,
        recalled_memories: List[SubjectiveMemoryTrace],
        received_rumors: List[RumorPacket],
        last_action_failed: bool = False,
        last_failed_target: Optional[str] = None
    ) -> SubjectContext:
        # 1. 严格从局部环境属性中提取客观存在的物理客体，无则为空
        perceived_objects: List[PerceivedSpatialObject] = []
        raw_features = horizon.local_environment.properties.get("spatial_features", [])
        for feat in raw_features:
            pos_dict = feat.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})
            obj_pos = Vector3D(x=pos_dict.get("x", 0.0), y=pos_dict.get("y", 0.0), z=pos_dict.get("z", 0.0))
            # 仅能感知距离视界半径内的实体
            if horizon.self_position.distance_to(obj_pos) <= 15.0:
                perceived_objects.append(
                    PerceivedSpatialObject(
                        object_id=feat.get("id", "unknown_object"),
                        object_type=feat.get("type", "GENERIC_SURFACE"),
                        position=obj_pos,
                        is_passable=feat.get("is_passable", False),
                        is_interactive=feat.get("is_interactive", True),
                        properties=feat.get("properties", {})
                    )
                )

        # 2. 提取共存的定性情境显著性标记（非标量、非优先级）
        activations: Set[str] = set()
        if somatic.pain > 40.0 or somatic.sensory_deprived:
            activations.add("SOMATIC_THREAT")
        if somatic.energy_pool < 25.0 or somatic.load > 60.0:
            activations.add("SOMATIC_FATIGUE")
        if horizon.visible_actors or horizon.audible_emissions:
            activations.add("INTERPERSONAL_EXPOSURE")
        if any(not obj.is_passable for obj in perceived_objects):
            activations.add("SPATIAL_BARRIER_PRESENT")
        if recalled_memories:
            activations.add("MEMORY_SALIENT")

        return cls(
            agent_id=agent_id,
            tick=tick,
            somatic=somatic,
            social=social,
            self_narrative=self_narrative,
            horizon=horizon,
            recalled_memories=recalled_memories,
            received_rumors=received_rumors,
            perceived_objects=perceived_objects,
            activations=activations,
            last_action_failed=last_action_failed,
            last_failed_target=last_failed_target
        )
