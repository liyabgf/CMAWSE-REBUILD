# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L7052-L7057 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #31  lines=5  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L07052.py
# edits: none. Header comment is the only addition.
# ======================
    delta_e = (
        self._config.alpha_mass * prop.kinematics.effective_mass
        + self._config.beta_temp * temp_penalty
        + self._config.gamma_obs * world_state.environment.observation_pressure
    )
    