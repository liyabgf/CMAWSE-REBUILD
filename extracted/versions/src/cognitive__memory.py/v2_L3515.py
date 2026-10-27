# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L3515-L3610 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #20  lines=95  compile=OK
# kind: module  ident: cognitive/memory.py  version: 2/3
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：cognitive/memory.py
职责：基于视界感知的主体私有记忆沉降与线索召回，规则完全支持注入。
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Protocol
from pydantic import BaseModel, ConfigDict, Field
from cmawse.core.schema import VerifiedEventEntry
from cmawse.world.bus import PrivateHorizon


class SubjectiveMemoryTrace(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_ref: str
    recorded_tick: int
    emotional_scar: float = Field(default=0.0, ge=0.0, le=100.0)
    subjective_rationalization: str
    salience_tags: List[str] = Field(default_factory=list)


class MemoryRefractionPolicy(Protocol):
    """可注入的主观折射策略"""
    def refract(
        self,
        agent_id: str,
        event: VerifiedEventEntry,
        horizon: PrivateHorizon
    ) -> tuple[float, str, List[str]]:
        ...


class DefaultRefractionPolicy:
    """默认折射实现：仅依据感官实际接收的数据生成有色记忆"""
    def refract(
        self,
        agent_id: str,
        event: VerifiedEventEntry,
        horizon: PrivateHorizon
    ) -> tuple[float, str, List[str]]:
        is_direct_actor = any(
            k.get("agent_id") == agent_id or k.get("target_id") == agent_id
            for k in event.resolved_kinematics
        )
        scar = 25.0 if is_direct_actor and "DEADLOCK" in event.causal_status else 5.0
        rationalization = f"Observed event {event.event_id} from position ({horizon.self_position.x}, {horizon.self_position.y})"
        tags = [event.causal_status] + list(horizon.visible_actors.keys())
        return scar, rationalization, tags


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
        witness_horizons: Dict[str, PrivateHorizon]
    ) -> None:
        """只针对有目击资格的 Agent 沉降记忆，杜绝未在场主体全知记忆生成"""
        for aid, horizon in witness_horizons.items():
            scar, rationalization, tags = self._policy.refract(aid, event, horizon)
            trace = SubjectiveMemoryTrace(
                event_ref=event.event_id,
                recorded_tick=event.tick_index,
                emotional_scar=scar,
                subjective_rationalization=rationalization,
                salience_tags=tags
            )
            self.get_or_create_store(aid).append_trace(trace)
