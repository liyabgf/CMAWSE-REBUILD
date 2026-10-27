# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L2290-L2415 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #10  lines=125  compile=OK
# kind: module  ident: world/bus.py  version: 1/3
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：world/bus.py
职责：World Plane 空间计算与 Public Reality Bus (公共现实广播总线)。
严格执行视界物理防火墙：依据空间距离、声学衰减与遮挡计算各 Agent 的私有物理视界（Private Horizon）。
严禁向 Agent 泄露全局状态或他人私有数据。
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol
from pydantic import BaseModel, ConfigDict, Field

from cmawse.core.schema import (
    GlobalWorldState,
    PhysicalEnvironmentSnapshot,
    Vector3D,
)


class PrivateHorizon(BaseModel):
    """主体在当前 Tick 的合法私有物理视界切片（只读）"""
    model_config = ConfigDict(frozen=True)

    agent_id: str
    tick: int
    self_position: Vector3D
    local_environment: PhysicalEnvironmentSnapshot
    visible_actors: Dict[str, Vector3D] = Field(
        default_factory=dict,
        description="视野内可观测到的其他在场主体坐标"
    )
    audible_emissions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="经空间声学衰减后可被感官接收的声学切片"
    )


class SpatialOcclusionPolicy(Protocol):
    """可注入的空间遮挡与感知衰减算法协议"""
    def is_visible(self, source: Vector3D, target: Vector3D, env: PhysicalEnvironmentSnapshot) -> bool:
        ...

    def calculate_audible_db(self, emitter_pos: Vector3D, receiver_pos: Vector3D, source_db: float) -> float:
        ...


class DefaultSpatialPolicy:
    """默认空间物理计算策略（无遮挡欧几里得简单衰减，可注入替换）"""

    def __init__(self, visual_range_limit: float = 15.0, hearing_threshold_db: float = 20.0):
        self._visual_range_limit = visual_range_limit
        self._hearing_threshold_db = hearing_threshold_db

    def is_visible(self, source: Vector3D, target: Vector3D, env: PhysicalEnvironmentSnapshot) -> bool:
        dist = source.distance_to(target)
        return dist <= self._visual_range_limit

    def calculate_audible_db(self, emitter_pos: Vector3D, receiver_pos: Vector3D, source_db: float) -> float:
        dist = max(1.0, emitter_pos.distance_to(receiver_pos))
        # 距离平方反比简易声学损耗: dB - 20 * log10(r)
        attenuation = 20.0 * (dist ** 0.5)  # 简易阻尼标定
        return max(0.0, source_db - attenuation)


class PublicRealityBus:
    """公共现实广播总线：剥离全局全知信息，分发私有视界"""

    def __init__(self, spatial_policy: SpatialOcclusionPolicy | None = None) -> None:
        self._spatial = spatial_policy or DefaultSpatialPolicy()

    def generate_horizons(
        self,
        world_state: GlobalWorldState,
        unattenuated_emissions: List[Dict[str, Any]] | None = None
    ) -> Dict[str, PrivateHorizon]:
        emissions = unattenuated_emissions or []
        horizons: Dict[str, PrivateHorizon] = {}

        for agent_id, snapshot in world_state.actors.items():
            if snapshot.somatic.sensory_deprived:
                # 感官剥夺：视界被完全抹去
                horizons[agent_id] = PrivateHorizon(
                    agent_id=agent_id,
                    tick=world_state.tick,
                    self_position=snapshot.position,
                    local_environment=world_state.environment
                )
                continue

            # 1. 视界内其他可见主体过滤
            visible_actors: Dict[str, Vector3D] = {}
            for other_id, other_snapshot in world_state.actors.items():
                if other_id == agent_id:
                    continue
                if self._spatial.is_visible(snapshot.position, other_snapshot.position, world_state.environment):
                    visible_actors[other_id] = other_snapshot.position

            # 2. 声学可及性计算过滤
            audible_list: List[Dict[str, Any]] = []
            for em in emissions:
                speaker_id = em.get("speaker_id")
                if not speaker_id or speaker_id not in world_state.actors:
                    continue
                speaker_pos = world_state.actors[speaker_id].position
                received_db = self._spatial.calculate_audible_db(
                    speaker_pos, snapshot.position, em.get("intensity_db", 60.0)
                )
                if received_db > 20.0:  # 高于听觉底噪阈值
                    audible_list.append({
                        "speaker_id": speaker_id,
                        "content": em.get("content"),
                        "received_intensity_db": received_db
                    })

            horizons[agent_id] = PrivateHorizon(
                agent_id=agent_id,
                tick=world_state.tick,
                self_position=snapshot.position,
                local_environment=world_state.environment,
                visible_actors=visible_actors,
                audible_emissions=audible_list
            )

        return horizons
