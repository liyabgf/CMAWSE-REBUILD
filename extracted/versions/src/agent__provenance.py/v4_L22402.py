# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L22402-L22487 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #107  lines=85  compile=OK
# kind: module  ident: agent/provenance.py  version: 4/4
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2 - Phase 3.1.3
模块：agent/provenance.py
职责：出处信封 (Decision Provenance Envelope)。
绑定 system_prompt_hash, schema_version, endpoint_identity, sampling_config_digest, raw_response_hash。
纯旁路遥测隔离。
"""

from __future__ import annotations

import hashlib
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
    endpoint_identity: str
    system_prompt_version: str
    system_prompt_hash: str
    schema_version: str
    sampling_config_digest: Optional[str] = None
    raw_response_hash: Optional[str] = None
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
        endpoint_identity: str = "local_direct",
        system_prompt_hash: str = "none",
        sampling_config_digest: Optional[str] = None,
        raw_response: Optional[str] = None,
        selected_candidate_id: Optional[str] = None,
        silent_mode: Optional[str] = None,
        rejection_reason: Optional[str] = None,
        reason_telemetry: Optional[str] = None,
        system_prompt_version: str = "v1.0",
        schema_version: str = "v1.0"
    ) -> DecisionProvenanceEnvelope:
        proj_hash = CognitiveProjection.compute_projection_hash(projection_payload)
        resp_hash = None
        if raw_response is not None:
            resp_hash = hashlib.sha256(raw_response.encode("utf-8")).hexdigest()[:32]

        return cls(
            agent_id=agent_id,
            tick=tick,
            candidate_set_hash=candidate_set_hash,
            projection_hash=proj_hash,
            model_name=model_name,
            endpoint_identity=endpoint_identity,
            system_prompt_version=system_prompt_version,
            system_prompt_hash=system_prompt_hash,
            schema_version=schema_version,
            sampling_config_digest=sampling_config_digest,
            raw_response_hash=resp_hash,
            decision_status=decision_status,
            selected_candidate_id=selected_candidate_id,
            silent_mode=silent_mode,
            is_boundary_valid=is_boundary_valid,
            rejection_reason=rejection_reason,
            reason_telemetry=reason_telemetry
        )
