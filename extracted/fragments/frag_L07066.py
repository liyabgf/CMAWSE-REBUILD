# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L7066-L7069 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #32  lines=3  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L07066.py
# edits: none. Header comment is the only addition.
# ======================
    def is_visible(self, source: Vector3D, target: Vector3D, env: PhysicalEnvironmentSnapshot) -> bool:
        dist = source.distance_to(target)
        return dist <= self._visual_range_limit  # 纯欧氏距离切分，完全忽略 env
    