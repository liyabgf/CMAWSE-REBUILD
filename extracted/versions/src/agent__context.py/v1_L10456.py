# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L10456-L10564 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #39  lines=108  compile=OK
# kind: module  ident: agent/context.py  version: 1/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 2
模块：agent/context.py
职责：装配纯净的 SubjectContext，计算定性情境显著性激活（Situational Activations）。
绝对禁止越权读取 GlobalWorldState，绝对禁止浮点加权评分。
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


class SituationalActivation(str):
    """非互斥的定性情境显著性激活标签"""
    SOMATIC_THREAT = "SOMATIC_THREAT"
    SPATIAL_BLOCKAGE = "SPATIAL_BLOCKAGE"
    INTERPERSONAL_FRICTION = "INTERPERSONAL_FRICTION"
    SOMATIC_FATIGUE = "SOMATIC_FATIGUE"
    NARRATIVE_CHALLENGE = "NARRATIVE_CHALLENGE"


class SubjectContext(BaseModel):
    """
    主体私有局部现实（严格限制在视界与私有内存内）。
    """
    model_config = ConfigDict(frozen=True)

    agent_id: str
    tick: int
    somatic: SomaticState
    social: SocialState
    self_narrative: SelfNarrativeState
    horizon: PrivateHorizon
    recalled_memories: List[SubjectiveMemoryTrace] = Field(default_factory=list)
    received_rumors: List[RumorPacket] = Field(default_factory=list)
    activations: Set[str] = Field(default_factory=set)
    last_action_failed: bool = Field(default=False)
    last_action_type: Optional[str] = Field(default=None)

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
        last_action_type: Optional[str] = None
    ) -> SubjectContext:
        activations: Set[str] = set()

        # 1. 生理急性威胁检测
        if somatic.pain > 40.0 or somatic.sensory_deprived:
            activations.add(SituationalActivation.SOMATIC_THREAT)

        # 2. 空间阻断与挫败检测
        if last_action_failed or (last_action_type and "DOOR" in last_action_type):
            activations.add(SituationalActivation.SPATIAL_BLOCKAGE)

        # 3. 人际摩擦检测
        if horizon.visible_actors or horizon.audible_emissions:
            for em in horizon.audible_emissions:
                if em.get("received_intensity_db", 0.0) >= 65.0:
                    activations.add(SituationalActivation.INTERPERSONAL_FRICTION)
            if len(horizon.visible_actors) > 0:
                # 检查最近邻居是否逼近在 2 米内
                for other_pos in horizon.visible_actors.values():
                    if horizon.self_position.distance_to(other_pos) <= 2.0:
                        activations.add(SituationalActivation.INTERPERSONAL_FRICTION)

        # 4. 生理疲劳检测
        if somatic.energy_pool < 25.0 or somatic.load > 60.0:
            activations.add(SituationalActivation.SOMATIC_FATIGUE)

        # 5. 叙事挑战检测
        for m in recalled_memories:
            if m.emotional_scar > 20.0:
                activations.add(SituationalActivation.NARRATIVE_CHALLENGE)

        return cls(
            agent_id=agent_id,
            tick=tick,
            somatic=somatic,
            social=social,
            self_narrative=self_narrative,
            horizon=horizon,
            recalled_memories=recalled_memories,
            received_rumors=received_rumors,
            activations=activations,
            last_action_failed=last_action_failed,
            last_action_type=last_action_type
        )
