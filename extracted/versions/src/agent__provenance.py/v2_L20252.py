# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L20252-L20313 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #98  lines=61  compile=OK
# kind: module  ident: agent/provenance.py  version: 2/4
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.1.1
模块：agent/provenance.py
职责：纯旁路决策出处信封 (Decision Provenance Envelope)。
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field

from cmawse.agent.cognitive_projection import CognitiveProjection


class DecisionProvenanceEnvelope(BaseModel):
    """纯遥测审计出处信封"""
    model_config = ConfigDict(extra="forbid", frozen=True)

    agent_id: str
    tick: int
    candidate_set_hash: str
    projection_hash: str
    model_name: str
    decision_status: str
    selected_candidate_id: Optional[str] = None
    silent_mode: Optional[str] = None
    is_boundary_valid: bool
    rejection_reason: Optional[str] = None
    reason_telemetry: Optional[str] = Field(default=None)

    @classmethod
    def create(
        cls,
        agent_id: str,
        tick: int,
        candidate_set_hash: str,
        projection_payload: Dict[str, Any],
        model_name: str,
        decision_status: str,
        is_boundary_valid: bool,
        selected_candidate_id: Optional[str] = None,
        silent_mode: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        reason_telemetry: Optional[str] = None
    ) -> DecisionProvenanceEnvelope:
        proj_hash = CognitiveProjection.compute_projection_hash(projection_payload)

        return cls(
            agent_id=agent_id,
            tick=tick,
            candidate_set_hash=candidate_set_hash,
            projection_hash=proj_hash,
            model_name=model_name,
            decision_status=decision_status,
            selected_candidate_id=selected_candidate_id,
            silent_mode=silent_mode,
            is_boundary_valid=is_boundary_valid,
            rejection_reason=rejection_reason,
            reason_telemetry=reason_telemetry
        )
