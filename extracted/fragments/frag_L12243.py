# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L12243-L12257 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #45  lines=14  compile=FAIL:2:unexpected indent
# kind: fragment  ident: frag_L12243.py
# edits: none. Header comment is the only addition.
# ======================
  # context.py
  if last_action_failed or (last_action_type and "DOOR" in last_action_type):
      activations.add(SituationalActivation.SPATIAL_BLOCKAGE)

  # generator.py
  if SituationalActivation.SPATIAL_BLOCKAGE in ctx.activations:
      candidates.append(CandidateAffordance(
          channel_id="AFF_DOOR_SHAKE",
          action_type="INTERACT_DOOR_SHAKE",
          actuator=ActuatorType.DUAL_HANDS,
          target_id="door_structure",  # 凭空发明的物理实体
          target_surface=SurfaceType.RIGID_HANDLE,  # 凭空发明的物理表面
          ...
      ))
  