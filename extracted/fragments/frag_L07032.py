# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L7032-L7044 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #30  lines=12  compile=FAIL:1:unexpected indent
# kind: fragment  ident: frag_L07032.py
# edits: none. Header comment is the only addition.
# ======================
    return ActionProposal(
        ...,
        stage=ActionStage.ACTION,
        is_silent_pass=False,
        kinematics=KinematicIntent(
            target_id=target_candidate,
            applied_force=...,
            effective_mass=60.0,
            is_contact_action=False,
            action_type="POSTURE_SHIFT"  # 核心动作类型直接硬编码
        )
    )
    