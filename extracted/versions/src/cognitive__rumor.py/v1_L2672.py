# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L2672-L2766 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #13  lines=94  compile=OK
# kind: module  ident: cognitive/rumor.py  version: 1/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：cognitive/rumor.py
职责：离场社会传闻网络 (What They Heard)。
脱离现场的事实沿社交拓扑传播，实现社会学三律：削平、磨尖、同化。
"""

from __future__ import annotations

import copy
import random
from typing import Dict, List, Set
from pydantic import BaseModel, ConfigDict, Field

from cmawse.core.schema import VerifiedEventEntry


class RumorPacket(BaseModel):
    """在社交网络中流转的传闻数据包"""
    model_config = ConfigDict(frozen=True)

    origin_event_id: str
    hop_count: int = 0
    leveling_ratio: float = 0.0  # 削平率：丢失前置物理因果细节
    sharpened_polarity: float = 0.0  # 磨尖度：极化动词刺激性
    assimilated_bias: str = ""  # 同化偏见标签
    gist: str


class SocialGraph:
    """社交关系拓扑图（邻接表）"""

    def __init__(self) -> None:
        self._adj: Dict[str, Set[str]] = {}

    def add_edge(self, u: str, v: str) -> None:
        self._adj.setdefault(u, set()).add(v)
        self._adj.setdefault(v, set()).add(u)

    def get_neighbors(self, node: str) -> Set[str]:
        return self._adj.get(node, set())


class RumorEngine:
    """社会传闻引擎：独立于物理现实的异步谣变网络"""

    def __init__(self, social_graph: SocialGraph, seed: int | None = None) -> None:
        self._graph = social_graph
        self._rumors_in_transit: List[RumorPacket] = []
        self._agent_beliefs: Dict[str, List[RumorPacket]] = {}
        self._rng = random.Random(seed)

    def inject_witness_event(self, witness_id: str, event: VerifiedEventEntry) -> None:
        """目击者将原始物理事实注入为初始传闻包"""
        raw_packet = RumorPacket(
            origin_event_id=event.event_id,
            hop_count=0,
            leveling_ratio=0.0,
            sharpened_polarity=0.1,
            gist=f"Event {event.event_id} verified with status {event.causal_status}"
        )
        self._agent_beliefs.setdefault(witness_id, []).append(raw_packet)

    def step_propagation(self) -> None:
        """
        单步传播：沿社交边多跳扩散，执行三律：
        1. 削平 (Leveling): 提高削平率
        2. 磨尖 (Sharpening): 放大极化动能
        3. 同化 (Assimilation): 注入群体先入为主的偏见
        """
        new_beliefs: Dict[str, List[RumorPacket]] = copy.deepcopy(self._agent_beliefs)

        for source_agent, packets in self._agent_beliefs.items():
            neighbors = self._graph.get_neighbors(source_agent)
            for packet in packets:
                if packet.hop_count >= 3:  # 3跳后能量衰竭
                    continue

                for neighbor in neighbors:
                    # 社会三律演化
                    mutated_packet = RumorPacket(
                        origin_event_id=packet.origin_event_id,
                        hop_count=packet.hop_count + 1,
                        leveling_ratio=min(1.0, packet.leveling_ratio + 0.3),  # 削平细节
                        sharpened_polarity=min(1.0, packet.sharpened_polarity + 0.25),  # 磨尖动词
                        assimilated_bias=f"ClassBias_{neighbor}",  # 同化
                        gist=f"[Distorted hop {packet.hop_count + 1}] {packet.gist}"
                    )
                    new_beliefs.setdefault(neighbor, []).append(mutated_packet)

        self._agent_beliefs = new_beliefs

    def get_agent_rumors(self, agent_id: str) -> List[RumorPacket]:
        return copy.deepcopy(self._agent_beliefs.get(agent_id, []))
