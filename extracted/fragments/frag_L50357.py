# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L50357-L50550 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #141  lines=193  compile=OK
# kind: fragment  ident: frag_L50357.py
# edits: none. Header comment is the only addition.
# ======================
class CausalLedger:
    """不可篡改事实主权账本"""
    def __init__(self) -> None:
        self._entries: List[EventEntry] = []
        self._sealed_hashes: List[str] = []

    def append(self, entry: EventEntry) -> None:
        serialized = f"{entry.event_id}|{entry.tick}|{entry.initiator_id}|{entry.status.value}"
        entry_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self._entries.append(entry)
        self._sealed_hashes.append(entry_hash)

    def get_history(self) -> List[EventEntry]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


class MinimalCMAWSERuntime:
    """
    最小 CMAWSE 调度器：严格执行 6 步因果闭环事务
    """
    def __init__(
        self,
        initial_state: GlobalWorldState,
        ledger: Optional[CausalLedger] = None,
        vision_range: float = 5.0
    ) -> None:
        self._state: GlobalWorldState = initial_state
        self._ledger: CausalLedger = ledger or CausalLedger()
        self._vision_range: float = vision_range

    @property
    def current_state(self) -> GlobalWorldState:
        return self._state

    @property
    def ledger(self) -> CausalLedger:
        return self._ledger

    # ------------------------------------------------------------------------
    # STEP 1: 物理视界切片生成 (Observation Projection)
    # ------------------------------------------------------------------------
    def generate_observation(self, agent_id: str) -> ObservationSlice:
        agent_pos = self._state.agent_positions[agent_id]
        agent_energy = self._state.agent_energies[agent_id]

        # 1. 距离过滤 (剔除超距物体)
        visible_objs = {
            obj_id: pos
            for obj_id, pos in self._state.object_positions.items()
            if agent_pos.distance_to(pos) <= self._vision_range
        }

        # 2. 生成客观物理通道 (仅基于几何近邻与体能)
        channels: List[AffordanceChannel] = []
        for obj_id, obj_pos in visible_objs.items():
            if agent_pos.distance_to(obj_pos) <= 2.0: # 接触操作阈值
                channels.append(
                    AffordanceChannel(
                        channel_id=f"act_interact_{obj_id}",
                        target_object_id=obj_id,
                        action_verb="INTERACT",
                        base_metabolic_cost=10.0
                    )
                )

        return ObservationSlice(
            tick=self._state.tick,
            agent_id=agent_id,
            self_position=agent_pos,
            self_energy=agent_energy,
            visible_objects=visible_objs,
            available_channels=tuple(channels)
        )

    # ------------------------------------------------------------------------
    # STEP 2 ~ 5: 物理仲裁、事务试算与原子生效
    # ------------------------------------------------------------------------
    def step(self, proposals: List[ActionProposal]) -> List[EventEntry]:
        current_tick = self._state.tick
        next_tick = current_tick + 1
        
        # 预备暂存容器 (Staging Area)
        staged_positions = dict(self._state.agent_positions)
        staged_energies = dict(self._state.agent_energies)
        produced_events: List[EventEntry] = []

        for prop in proposals:
            obs = self.generate_observation(prop.agent_id)
            valid_cids = {c.channel_id: c for c in obs.available_channels}

            # 判决 0: 主动静默轮
            if prop.selected_channel_id is None:
                entry = EventEntry(
                    event_id=f"evt_{current_tick}_{prop.agent_id}_silent",
                    tick=current_tick,
                    initiator_id=prop.agent_id,
                    channel_id=None,
                    status=ActionExecutionStatus.SILENT_PASS,
                    applied_patches=(),
                    telemetry_reason=prop.telemetry_reason
                )
                produced_events.append(entry)
                continue

            # 判决 1: 非法/虚构 candidate_id 拦截 (Fail-Closed)
            if prop.selected_channel_id not in valid_cids:
                entry = EventEntry(
                    event_id=f"evt_{current_tick}_{prop.agent_id}_err",
                    tick=current_tick,
                    initiator_id=prop.agent_id,
                    channel_id=prop.selected_channel_id,
                    status=ActionExecutionStatus.REJECTED_INVALID_ID,
                    applied_patches=(),
                    telemetry_reason=prop.telemetry_reason
                )
                produced_events.append(entry)
                continue

            # 判决 2: 物理能耗势垒核算 (结合隐变量与当前代谢)
            chosen_channel = valid_cids[prop.selected_channel_id]
            target_obj = chosen_channel.target_object_id
            
            # 从隐变量图层获取该物体的真实物理阻力 (Agent 无法直接读取)
            latent_friction = self._state.latent_friction_map.get(target_obj, 1.0)
            required_energy = chosen_channel.base_metabolic_cost * latent_friction

            available_energy = staged_energies[prop.agent_id]

            if available_energy < required_energy:
                # 动能不足以跨越势垒：扣除惩罚损耗，动作受阻
                staged_energies[prop.agent_id] = max(0.0, available_energy - 2.0)
                entry = EventEntry(
                    event_id=f"evt_{current_tick}_{prop.agent_id}_imp",
                    tick=current_tick,
                    initiator_id=prop.agent_id,
                    channel_id=prop.selected_channel_id,
                    status=ActionExecutionStatus.IMPEDED_ENERGY,
                    applied_patches=(
                        {"op": "replace", "path": f"agent_energies/{prop.agent_id}", "value": staged_energies[prop.agent_id]},
                    ),
                    telemetry_reason=prop.telemetry_reason
                )
            else:
                # 成功做功：扣除完整能耗，物理事实成立
                staged_energies[prop.agent_id] = available_energy - required_energy
                entry = EventEntry(
                    event_id=f"evt_{current_tick}_{prop.agent_id}_succ",
                    tick=current_tick,
                    initiator_id=prop.agent_id,
                    channel_id=prop.selected_channel_id,
                    status=ActionExecutionStatus.SUCCESS,
                    applied_patches=(
                        {"op": "replace", "path": f"agent_energies/{prop.agent_id}", "value": staged_energies[prop.agent_id]},
                    ),
                    telemetry_reason=prop.telemetry_reason
                )

            produced_events.append(entry)

        # STEP 5: 原子提交 (Commit) 与账本追加
        for ev in produced_events:
            self._ledger.append(ev)

        # 生成全新不可变世界快照
        self._state = GlobalWorldState(
            tick=next_tick,
            agent_positions=staged_positions,
            agent_energies=staged_energies,
            object_positions=self._state.object_positions,
            latent_friction_map=self._state.latent_friction_map,
            latent_interventions=self._state.latent_interventions
        )

        return produced_events

    # ------------------------------------------------------------------------
    # STEP 6: 外生因果干预接口 (do-calculus)
    # ------------------------------------------------------------------------
    def apply_intervention(self, target_object_id: str, new_friction: float) -> None:
        """强制改写世界物理隐变量，不通知模型"""
        new_map = dict(self._state.latent_friction_map)
        new_map[target_object_id] = new_friction
        self._state = GlobalWorldState(
            tick=self._state.tick,
            agent_positions=self._state.agent_positions,
            agent_energies=self._state.agent_energies,
            object_positions=self._state.object_positions,
            latent_friction_map=new_map,
            latent_interventions=self._state.latent_interventions
        )
