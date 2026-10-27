# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L5337-L5473 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #28  lines=136  compile=OK
# kind: module  ident: cognitive/memory.py  version: latest of 3 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：cognitive/memory.py
职责：主体私有主观记忆系统。强化主体间性：同一客观事件经由不同主体的生理/心理滤镜，
折射出截然不同的创伤深度、标签与主观合理化。
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Protocol
from pydantic import BaseModel, ConfigDict, Field
from cmawse.core.schema import ActorSnapshot, VerifiedEventEntry
from cmawse.world.bus import PrivateHorizon


class SubjectiveMemoryTrace(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_ref: str
    recorded_tick: int
    observer_id: str
    emotional_scar: float = Field(default=0.0, ge=0.0, le=100.0)
    subjective_rationalization: str
    salience_tags: List[str] = Field(default_factory=list)


class MemoryRefractionPolicy(Protocol):
    def refract(
        self,
        agent_id: str,
        actor_snapshot: ActorSnapshot,
        event: VerifiedEventEntry,
        horizon: PrivateHorizon
    ) -> tuple[float, str, List[str]]:
        ...


class DefaultRefractionPolicy:
    """
    符合白皮书公理 5 的主观折射策略：
    客观事实唯一，主观折射多元。同一动作在不同主体的信念刚性与失调度过滤下产生异质记忆。
    """
    def refract(
        self,
        agent_id: str,
        actor_snapshot: ActorSnapshot,
        event: VerifiedEventEntry,
        horizon: PrivateHorizon
    ) -> tuple[float, str, List[str]]:
        is_direct_actor = any(
            k.get("agent_id") == agent_id or k.get("target_id") == agent_id
            for k in event.resolved_kinematics
        )
        
        # 1. 创伤深度依据主体的心理承受力与失调基线异质放大
        base_scar = 20.0 if is_direct_actor else 6.0
        # 认知失调越高、被监视压力越大，记忆创伤感越剧烈
        emotional_scar = min(
            100.0,
            base_scar * (1.0 + actor_snapshot.self_narrative.dissonance * 0.02)
            + actor_snapshot.social.surveillance_load * 10.0
        )

        # 2. 主观合理化受 core_belief 偏置影响
        belief = actor_snapshot.self_narrative.constants.get("core_belief", "自保")
        dist = 0.0
        if horizon.visible_actors:
            first_target = next(iter(horizon.visible_actors.values()))
            dist = horizon.self_position.distance_to(first_target)

        rationalization = (
            f"[{agent_id}|信念:{belief}] 在距离约 {dist:.1f}m 处目睹 {event.event_id}。"
            f"主观判定：{'威胁逼近，必须防卫' if emotional_scar > 15.0 else '常规场域扰动'}。"
        )

        # 3. 提取主体偏置关注的标签
        tags = [event.causal_status, f"scar_{int(emotional_scar)}"]
        if is_direct_actor:
            tags.append("DIRECT_INVOLVED")
        for k in event.resolved_kinematics:
            if "action_type" in k:
                tags.append(k["action_type"])

        return emotional_scar, rationalization, tags


class MemoryStore:
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self._records: List[SubjectiveMemoryTrace] = []

    def append_trace(self, trace: SubjectiveMemoryTrace) -> None:
        self._records.append(trace)

    def retrieve_by_cues(self, cues: List[str], limit: int = 3) -> List[SubjectiveMemoryTrace]:
        cues_set = set(cues)
        matched = [r for r in self._records if cues_set.intersection(set(r.salience_tags))]
        matched.sort(key=lambda x: (x.emotional_scar, x.recorded_tick), reverse=True)
        return copy.deepcopy(matched[:limit])

    def dump_all(self) -> List[SubjectiveMemoryTrace]:
        return copy.deepcopy(self._records)


class MemorySystem:
    def __init__(self, policy: MemoryRefractionPolicy | None = None) -> None:
        self._stores: Dict[str, MemoryStore] = {}
        self._policy = policy or DefaultRefractionPolicy()

    def get_or_create_store(self, agent_id: str) -> MemoryStore:
        if agent_id not in self._stores:
            self._stores[agent_id] = MemoryStore(agent_id)
        return self._stores[agent_id]

    def settle_event_for_witnesses(
        self,
        event: VerifiedEventEntry,
        witness_horizons: Dict[str, PrivateHorizon],
        actor_snapshots: Dict[str, ActorSnapshot]
    ) -> None:
        """只针对法定目击者沉降主观记忆，严格结合其私有生理/心理快照进行折射"""
        for aid, horizon in witness_horizons.items():
            snapshot = actor_snapshots.get(aid)
            if not snapshot:
                continue
            scar, rationalization, tags = self._policy.refract(aid, snapshot, event, horizon)
            trace = SubjectiveMemoryTrace(
                event_ref=event.event_id,
                recorded_tick=event.tick_index,
                observer_id=aid,
                emotional_scar=scar,
                subjective_rationalization=rationalization,
                salience_tags=tags
            )
            self.get_or_create_store(aid).append_trace(trace)
