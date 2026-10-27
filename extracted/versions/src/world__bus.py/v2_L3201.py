# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L3201-L3356 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #18  lines=155  compile=OK
# kind: module  ident: world/bus.py  version: 2/3
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：world/bus.py
职责：World Plane 空间计算与 Public Reality Bus。
落实视界物理防火墙，提供零全知泄露的目击者资格裁决。
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol
from pydantic import BaseModel, ConfigDict, Field

from cmawse.core.schema import (
    GlobalWorldState,
    PhysicalEnvironmentSnapshot,
    Vector3D,
    VerifiedEventEntry,
)


class PrivateHorizon(BaseModel):
    """主体私有物理视界切片"""
    model_config = ConfigDict(frozen=True)

    agent_id: str
    tick: int
    self_position: Vector3D
    local_environment: PhysicalEnvironmentSnapshot
    visible_actors: Dict[str, Vector3D] = Field(default_factory=dict)
    audible_emissions: List[Dict[str, Any]] = Field(default_factory=list)


class SpatialOcclusionPolicy(Protocol):
    def is_visible(self, source: Vector3D, target: Vector3D, env: PhysicalEnvironmentSnapshot) -> bool:
        ...

    def calculate_audible_db(self, emitter_pos: Vector3D, receiver_pos: Vector3D, source_db: float) -> float:
        ...


class DefaultSpatialPolicy:
    def __init__(self, visual_range_limit: float = 15.0, hearing_threshold_db: float = 20.0):
        self._visual_range_limit = visual_range_limit
        self._hearing_threshold_db = hearing_threshold_db

    def is_visible(self, source: Vector3D, target: Vector3D, env: PhysicalEnvironmentSnapshot) -> bool:
        return source.distance_to(target) <= self._visual_range_limit

    def calculate_audible_db(self, emitter_pos: Vector3D, receiver_pos: Vector3D, source_db: float) -> float:
        dist = max(1.0, emitter_pos.distance_to(receiver_pos))
        return max(0.0, source_db - 20.0 * (dist ** 0.5))


class PublicRealityBus:
    """公共现实广播总线"""

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
                horizons[agent_id] = PrivateHorizon(
                    agent_id=agent_id,
                    tick=world_state.tick,
                    self_position=snapshot.position,
                    local_environment=world_state.environment
                )
                continue

            visible_actors: Dict[str, Vector3D] = {}
            for other_id, other_snapshot in world_state.actors.items():
                if other_id == agent_id:
                    continue
                if self._spatial.is_visible(snapshot.position, other_snapshot.position, world_state.environment):
                    visible_actors[other_id] = other_snapshot.position

            audible_list: List[Dict[str, Any]] = []
            for em in emissions:
                speaker_id = em.get("speaker_id")
                if not speaker_id or speaker_id not in world_state.actors:
                    continue
                speaker_pos = world_state.actors[speaker_id].position
                received_db = self._spatial.calculate_audible_db(
                    speaker_pos, snapshot.position, em.get("intensity_db", 60.0)
                )
                if received_db > 20.0:
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

    def filter_witnesses(
        self,
        event: VerifiedEventEntry,
        horizons: Dict[str, PrivateHorizon]
    ) -> List[str]:
        """
        严格依据物理可及性裁决目击资格：
        1. 动作发起方或目标方必定在场；
        2. 视界内目睹了相关主体物理位移；
        3. 接收到了相关发声事件。
        """
        witnesses: set[str] = set()

        # 提取事件涉及的物理核心主体
        involved_actors: set[str] = set()
        for k in event.resolved_kinematics:
            if "agent_id" in k:
                involved_actors.add(k["agent_id"])
            if "target_id" in k:
                involved_actors.add(k["target_id"])
            if "actors" in k:
                involved_actors.update(k["actors"])

        for speaker in event.acoustic_emissions:
            if "speaker_id" in speaker:
                involved_actors.add(speaker["speaker_id"])

        for aid, horizon in horizons.items():
            # 规则 1: 自身直接参与
            if aid in involved_actors:
                witnesses.add(aid)
                continue

            # 规则 2: 视野中包含任何核心当事人
            if any(target in horizon.visible_actors for target in involved_actors):
                witnesses.add(aid)
                continue

            # 规则 3: 耳闻声学信号
            if any(em["speaker_id"] in involved_actors for em in horizon.audible_emissions):
                witnesses.add(aid)
                continue

        return list(witnesses)
