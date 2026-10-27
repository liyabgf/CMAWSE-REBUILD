# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L7636-L7642 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #33  lines=6  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L07636.py
# edits: none. Header comment is the only addition.
# ======================
  class SomaticState(BaseModel):
      energy_pool: float = Field(..., ge=0.0)
      integrity: float = Field(default=100.0)
      load: float = Field(default=0.0)
      sensory_deprived: bool = Field(default=False)
      variables: Dict[str, float] = Field(default_factory=dict)
  