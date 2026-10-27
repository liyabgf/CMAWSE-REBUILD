# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L3614-L3706 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #21  lines=92  compile=OK
# kind: module  ident: cognitive/rumor.py  version: 2/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：cognitive/rumor.py
职责：离场社会传闻网络。传播三律参数完全参数化。
"""

from __future__ import annotations

import copy
from typing import Dict, List, Protocol, Set
from pydantic import BaseModel, ConfigDict

from cmawse.core.schema import VerifiedEventEntry


class RumorPacket(BaseModel):
    model_config = ConfigDict(frozen=True)

    origin_event_id: str
    hop_count: int = 0
    leveling_ratio: float = 0.0
    sharpened_polarity: float = 0.0
    assimilated_bias: str = ""
    gist: str


class RumorEvolutionPolicy(Protocol):
    def evolve(self, packet: RumorPacket, transmitter: str, receiver: str) -> RumorPacket | None:
        ...


class DefaultRumorPolicy:
    def __init__(self, max_hops: int = 3, leveling_step: float = 0.25, sharpening_step: float = 0.2):
        self._max_hops = max_hops
        self._leveling_step = leveling_step
        self._sharpening_step = sharpening_step

    def evolve(self, packet: RumorPacket, transmitter: str, receiver: str) -> RumorPacket | None:
        if packet.hop_count >= self._max_hops:
            return None
        return RumorPacket(
            origin_event_id=packet.origin_event_id,
            hop_count=packet.hop_count + 1,
            leveling_ratio=min(1.0, packet.leveling_ratio + self._leveling_step),
            sharpened_polarity=min(1.0, packet.sharpened_polarity + self._sharpening_step),
            assimilated_bias=f"Bias_{receiver}",
            gist=f"[Hop {packet.hop_count + 1} via {transmitter}] {packet.gist}"
        )


class SocialGraph:
    def __init__(self) -> None:
        self._adj: Dict[str, Set[str]] = {}

    def add_edge(self, u: str, v: str) -> None:
        self._adj.setdefault(u, set()).add(v)
        self._adj.setdefault(v, set()).add(u)

    def get_neighbors(self, node: str) -> Set[str]:
        return self._adj.get(node, set())


class RumorEngine:
    def __init__(self, social_graph: SocialGraph, policy: RumorEvolutionPolicy | None = None) -> None:
        self._graph = social_graph
        self._policy = policy or DefaultRumorPolicy()
        self._agent_beliefs: Dict[str, List[RumorPacket]] = {}

    def seed_witness_rumor(self, witness_id: str, event: VerifiedEventEntry) -> None:
        """必须由物理目击者触发播种"""
        initial_packet = RumorPacket(
            origin_event_id=event.event_id,
            hop_count=0,
            gist=f"Event {event.event_id}:{event.causal_status}"
        )
        self._agent_beliefs.setdefault(witness_id, []).append(initial_packet)

    def step_propagation(self) -> None:
        new_beliefs: Dict[str, List[RumorPacket]] = copy.deepcopy(self._agent_beliefs)

        for source_agent, packets in self._agent_beliefs.items():
            neighbors = self._graph.get_neighbors(source_agent)
            for packet in packets:
                for neighbor in neighbors:
                    mutated = self._policy.evolve(packet, source_agent, neighbor)
                    if mutated:
                        new_beliefs.setdefault(neighbor, []).append(mutated)

        self._agent_beliefs = new_beliefs

    def get_agent_rumors(self, agent_id: str) -> List[RumorPacket]:
        return copy.deepcopy(self._agent_beliefs.get(agent_id, []))
