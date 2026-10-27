# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L7664-L7668 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #34  lines=4  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L07664.py
# edits: none. Header comment is the only addition.
# ======================
  class SocialState(BaseModel):
      rank: int = Field(default=0)
      surveillance_load: float = Field(default=0.0, ge=0.0, le=1.0)
      variables: Dict[str, float] = Field(default_factory=dict)
  