# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L7689-L7693 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #35  lines=4  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L07689.py
# edits: none. Header comment is the only addition.
# ======================
  class SelfNarrativeState(BaseModel):
      defense_rigidity: float = Field(default=50.0)
      dissonance: float = Field(default=0.0)
      constants: Dict[str, str] = Field(default_factory=dict)
  