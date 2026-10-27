# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L4176-L4382 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #24  lines=206  compile=OK
# kind: module  ident: world/bus.py  version: latest of 3 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：world/bus.py
职责：World Plane 空间计算、公共现实广播总线与可注入目击资格仲裁。
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol
from pydantic import BaseModel, ConfigDict, Field

from cmawse.core.schema import (
    ActorSnapshot,
    GlobalWorldState,
    PhysicalEnvironmentSnapshot,
    Vector3D,
    VerifiedEventEntry,
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
        description="经空间声学衰减后在当前 Tick 可被接收的声学切片"
    )


class SpatialOcclusionPolicy(Protocol):
    """空间遮挡与声学感知衰减协议"""
    def is_visible(self, source: Vector3D, target: Vector3D, env: PhysicalEnvironmentSnapshot) -> bool:
        ...

    def calculate_audible_db(self, emitter_pos: Vector3D, receiver_pos: Vector3D, source_db: float) -> float:
        ...


class DefaultSpatialPolicy:
    """默认空间物理计算策略"""

    def __init__(self, visual_range_limit: float = 15.0, hearing_threshold_db: float = 20.0):
        self._visual_range_limit = visual_range_limit
        self._hearing_threshold_db = hearing_threshold_db

    def is_visible(self, source: Vector3D, target: Vector3D, env: PhysicalEnvironmentSnapshot) -> bool:
        return source.distance_to(target) <= self._visual_range_limit

    def calculate_audible_db(self, emitter_pos: Vector3D, receiver_pos: Vector3D, source_db: float) -> float:
        dist = max(1.0, emitter_pos.distance_to(receiver_pos))
        # 阻尼损耗：对数距离衰减
        attenuation = 20.0 * (dist ** 0.5)
        return max(0.0, source_db - attenuation)


class WitnessQualificationPolicy(Protocol):
    """可注入的目击认知资格判定协议（非 Core 公理）"""
    def qualify(
        self,
        agent_id: str,
        actor_snapshot: ActorSnapshot,
        horizon: PrivateHorizon,
        event: VerifiedEventEntry
    ) -> bool:
        ...


class DefaultWitnessPolicy:
    """默认物理目击仲裁规则：直接卷入、视线目睹或耳闻发声"""

    def qualify(
        self,
        agent_id: str,
        actor_snapshot: ActorSnapshot,
        horizon: PrivateHorizon,
        event: VerifiedEventEntry
    ) -> bool:
        # 感官剥夺者无法通过常规视觉/听觉成为目击者
        if actor_snapshot.somatic.sensory_deprived:
            # 仅当自身被力学直接命中时才获得体感感知
            return any(
                k.get("target_id") == agent_id or k.get("agent_id") == agent_id
                for k in event.resolved_kinematics
            )

        # 1. 直接力学参与者
        is_direct_actor = any(
            k.get("agent_id") == agent_id or k.get("target_id") == agent_id or agent_id in k.get("actors", [])
            for k in event.resolved_kinematics
        )
        if is_direct_actor:
            return True

        # 2. 视觉目睹：事件的动作主体在自身可见范围内
        involved_actors = set()
        for k in event.resolved_kinematics:
            if "agent_id" in k:
                involved_actors.add(k["agent_id"])
            if "target_id" in k:
                involved_actors.add(k["target_id"])
            if "actors" in k:
                involved_actors.update(k["actors"])

        if any(target in horizon.visible_actors for target in involved_actors):
            return True

        # 3. 听觉捕获：当前视界收到了来自事件参与方的声学信号
        speaker_ids = {em.get("speaker_id") for em in event.acoustic_emissions}
        if any(em.get("speaker_id") in speaker_ids for em in horizon.audible_emissions):
            return True

        return False


class PublicRealityBus:
    """公共现实广播总线"""

    def __init__(
        self,
        spatial_policy: SpatialOcclusionPolicy | None = None,
        witness_policy: WitnessQualificationPolicy | None = None
    ) -> None:
        self._spatial = spatial_policy or DefaultSpatialPolicy()
        self._witness_policy = witness_policy or DefaultWitnessPolicy()

    def generate_horizons(
        self,
        world_state: GlobalWorldState,
        previous_tick_emissions: List[Dict[str, Any]] | None = None
    ) -> Dict[str, PrivateHorizon]:
        """
        根据当前物理世界和上一 Tick 产生的声学事件生成各主体 PrivateHorizon。
        """
        emissions = previous_tick_emissions or []
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

            # 视觉视界
            visible_actors: Dict[str, Vector3D] = {}
            for other_id, other_snapshot in world_state.actors.items():
                if other_id == agent_id:
                    continue
                if self._spatial.is_visible(snapshot.position, other_snapshot.position, world_state.environment):
                    visible_actors[other_id] = other_snapshot.position

            # 声学视界：对上一 Tick 的发声计算到达分贝
            audible_list: List[Dict[str, Any]] = []
            for em in emissions:
                speaker_id = em.get("speaker_id")
                if not speaker_id or speaker_id not in world_state.actors:
                    continue
                speaker_pos = world_state.actors[speaker_id].position
                received_db = self._spatial.calculate_audible_db(
                    speaker_pos, snapshot.position, em.get("intensity_db", 60.0)
                )
                if received_db > 20.0:  # 大于听觉底噪阈值
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
        world_state: GlobalWorldState,
        horizons: Dict[str, PrivateHorizon]
    ) -> List[str]:
        """通过注入的 WitnessQualificationPolicy 确定合法目击者"""
        qualified = []
        for aid, horizon in horizons.items():
            actor_snap = world_state.actors.get(aid)
            if not actor_snap:
                continue
            if self._witness_policy.qualify(aid, actor_snap, horizon, event):
                qualified.append(aid)
        return qualified
