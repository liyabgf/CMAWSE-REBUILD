# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L17642-L17654 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #86  lines=12  compile=OK
# kind: fragment  ident: frag_L17642.py
# edits: none. Header comment is the only addition.
# ======================
class CognitiveMind(Protocol):
    def deliberate(
        self,
        ctx: SubjectContext,
        state: InternalCognitiveState,
        rep: SubjectiveRepresentation,
        intents: List[SubjectiveIntent],
        candidates: List[CandidateAffordance],
        memories: List[SubjectiveMemoryTrace],
        rumors: List[RumorPacket]
    ) -> MindDecision:
        ...
