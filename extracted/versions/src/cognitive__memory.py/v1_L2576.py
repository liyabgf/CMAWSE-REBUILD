# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L2576-L2668 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #12  lines=92  compile=OK
# kind: module  ident: cognitive/memory.py  version: 1/3
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：cognitive/memory.py
职责：主体私有记忆系统 (What I Remember)。
事实沉降为有色记忆；记忆不占日常注意力，仅在遭遇特定切片时受情境唤醒并发生时间性重构。
"""

from __future__ import annotations

import copy
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from cmawse.core.schema import VerifiedEventEntry


class SubjectiveMemoryTrace(BaseModel):
    """主体私有主观记忆切片"""
    model_config = ConfigDict(frozen=True)

    event_ref: str
    recorded_tick: int
    emotional_scar: float = Field(default=0.0, ge=0.0, le=100.0)
    subjective_rationalization: str = Field(description="主体防御机制重构后的事后合理化描述")
    salience_tags: List[str] = Field(default_factory=list, description="检索唤醒线索标签")


class MemoryStore:
    """单个 Agent 独占的私有记忆库，严禁跨主体直接共享"""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self._records: List[SubjectiveMemoryTrace] = []

    def record_event_refraction(
        self,
        event: VerifiedEventEntry,
        emotional_scar: float,
        rationalization: str,
        tags: List[str]
    ) -> None:
        trace = SubjectiveMemoryTrace(
            event_ref=event.event_id,
            recorded_tick=event.tick_index,
            emotional_scar=emotional_scar,
            subjective_rationalization=rationalization,
            salience_tags=tags
        )
        self._records.append(trace)

    def retrieve_by_cues(self, cues: List[str], limit: int = 3) -> List[SubjectiveMemoryTrace]:
        """根据当前环境出现的线索即时唤醒，旧记忆平时不占注意力"""
        cues_set = set(cues)
        matched = [
            r for r in self._records
            if cues_set.intersection(set(r.salience_tags))
        ]
        # 按创伤程度与新鲜度降序排序唤醒
        matched.sort(key=lambda x: (x.emotional_scar, x.recorded_tick), reverse=True)
        return copy.deepcopy(matched[:limit])


class MemorySystem:
    """全局记忆管理分发平面（单向消费 Event Ledger）"""

    def __init__(self) -> None:
        self._stores: Dict[str, MemoryStore] = {}

    def get_or_create_store(self, agent_id: str) -> MemoryStore:
        if agent_id not in self._stores:
            self._stores[agent_id] = MemoryStore(agent_id)
        return self._stores[agent_id]

    def settle_event(
        self,
        event: VerifiedEventEntry,
        participating_agents: List[str],
        default_rationalization_fn: Optional[callable] = None
    ) -> None:
        """事件落槌后，异步触发在场主体的主观记忆沉淀"""
        for aid in participating_agents:
            store = self.get_or_create_store(aid)
            # 形式化重构
            desc = f"Subjective trace of {event.event_id} at tick {event.tick_index}"
            if default_rationalization_fn:
                desc = default_rationalization_fn(aid, event)
            store.record_event_refraction(
                event=event,
                emotional_scar=10.0 if "COLLISION" in event.causal_status else 0.0,
                rationalization=desc,
                tags=[event.causal_status]
            )
