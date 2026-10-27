# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L50777-L50783 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #142  lines=6  compile=OK
# kind: fragment  ident: frag_L50777.py
# edits: none. Header comment is the only addition.
# ======================
# 致命缺陷：Runtime 内部直接计算了特定力学逻辑
latent_friction = self._state.latent_friction_map.get(target_obj, 1.0)
required_energy = chosen_channel.base_metabolic_cost * latent_friction
available_energy = staged_energies[prop.agent_id]
if available_energy < required_energy:
    ...
