# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L34207-L34221 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #134  lines=14  compile=OK
# kind: fragment  ident: frag_L34207.py
# edits: none. Header comment is the only addition.
# ======================
# 运行独立验证断言脚本
import hashlib, pytest
from cmawse.agent.nl_contract import (
    PromptEnvelope, ModelResponse, ProviderErrorCode,
    StrictLLMOutputParserV2, ParserOutcome,
    ProviderAgnosticCognitiveAdapter, canonical_serialize
)
from cmawse.agent.deliberation import MindDecisionStatus, CognitiveSilentMode
from cmawse.agent.cognitive_projection import CognitiveMindContext
from cmawse.core.schema import PhysicalEnvironmentSnapshot, SelfNarrativeState, SocialState, SomaticState, Vector3D
from cmawse.world.bus import PrivateHorizon
from cmawse.agent.context import SubjectContext
from cmawse.agent.affordance import CandidateAffordance, ActuatorType, SurfaceType, ActionAttribute
from cmawse.agent.validator import BoundaryValidator
