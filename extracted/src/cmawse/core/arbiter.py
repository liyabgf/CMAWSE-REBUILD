# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L1726-L2008 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #8  lines=282  compile=OK
# kind: module  ident: core/arbiter.py  version: latest of 2 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：core/arbiter.py
职责：Causal Arbiter (因果阻尼与动力学仲裁法庭)。
纯粹由因果公理驱动的 Proposal -> VerifiedEvent 仲裁器。
切除一切自然语言文学修饰，所有物理参数与经验权重完全支持注入。
严禁自行编造未在世界状态中存在的物理事实。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    GlobalWorldState,
    RFC6902Patch,
    VerifiedEventEntry,
)


class ArbiterConfiguration(BaseModel):
    """
    因果法庭参数注入配置。
    所有力学势垒常数完全参数化，拒绝引擎内部硬编码。
    """
    model_config = ConfigDict(frozen=True)

    alpha_mass: float = Field(default=0.05, description="质量阻尼系数")
    beta_temp: float = Field(default=0.15, description="温度阻尼系数")
    gamma_obs: float = Field(default=25.0, description="规制观察压力阻尼系数")
    collision_deadlock_threshold: float = Field(default=2.0, description="对撞死锁标量公差 epsilon")
    contact_distance_limit: float = Field(default=2.0, description="接触性动作最大空间物理欧氏间距")


class CausalArbiter:
    """
    因果阻尼与动力学仲裁器。
    严禁直接修改传入的任何状态对象。
    """

    def __init__(
        self,
        config: Optional[ArbiterConfiguration] = None,
        event_id_factory: Optional[Callable[[int], str]] = None
    ) -> None:
        self._config = config or ArbiterConfiguration()
        self._event_id_factory = event_id_factory or (lambda tick: f"evt_{tick:08d}")

    def arbitrate_tick(
        self,
        tick: int,
        timestamp: str,
        proposals: List[ActionProposal],
        world_state: GlobalWorldState
    ) -> VerifiedEventEntry:
        """
        因果仲裁主流水线：
        1. 过滤与分离 SILENT_PASS 提案；
        2. 空间距离与物理几何门禁断言；
        3. 做功阶梯能耗势垒 (ΔE) 校验；
        4. 动力学对撞分析与环境微观熵仲裁；
        5. 构造输出确定性事实条目与对应 RFC 6902 状态补丁。
        """
        state_patches: List[RFC6902Patch] = []
        resolved_kinematics: List[Dict[str, Any]] = []
        acoustic_emissions: List[Dict[str, Any]] = []

        # --------------------------------------------------------------------
        # 1. 分离言语通道与静默轮
        # --------------------------------------------------------------------
        active_kinematics: List[ActionProposal] = []

        for prop in proposals:
            if prop.is_silent_pass:
                resolved_kinematics.append({
                    "agent_id": prop.agent_id,
                    "status": "SILENT_PASS_CONFIRMED"
                })
                continue

            # 言语发声检查
            if prop.verbal:
                speaker = world_state.actors.get(prop.agent_id)
                if speaker and not speaker.somatic.sensory_deprived:
                    acoustic_emissions.append({
                        "speaker_id": prop.agent_id,
                        "content": prop.verbal.content,
                        "intensity_db": prop.verbal.intensity_db
                    })

            if prop.kinematics is not None and prop.stage == ActionStage.ACTION:
                active_kinematics.append(prop)

        # 全场静默或无动作提议
        if not active_kinematics:
            return VerifiedEventEntry(
                event_id=self._event_id_factory(tick),
                tick_index=tick,
                timestamp=timestamp,
                causal_status="QUIET_CYCLE",
                resolved_kinematics=resolved_kinematics,
                acoustic_emissions=acoustic_emissions,
                state_patches=state_patches
            )

        # --------------------------------------------------------------------
        # 2. 空间物理几何门禁 (Spatial Causal Gate)
        # --------------------------------------------------------------------
        geometrically_valid: List[ActionProposal] = []

        for prop in active_kinematics:
            assert prop.kinematics is not None
            source_actor = world_state.actors.get(prop.agent_id)
            if not source_actor:
                resolved_kinematics.append({
                    "agent_id": prop.agent_id,
                    "status": "REJECTED_ACTOR_NOT_FOUND"
                })
                continue

            if prop.kinematics.is_contact_action and prop.kinematics.target_id:
                target_actor = world_state.actors.get(prop.kinematics.target_id)
                if not target_actor:
                    resolved_kinematics.append({
                        "agent_id": prop.agent_id,
                        "status": "REJECTED_TARGET_NOT_FOUND",
                        "target_id": prop.kinematics.target_id
                    })
                    continue

                # 距离计算
                dist = source_actor.position.distance_to(target_actor.position)
                if dist > self._config.contact_distance_limit:
                    resolved_kinematics.append({
                        "agent_id": prop.agent_id,
                        "status": "SPATIAL_COLLISION_INVALID",
                        "measured_distance": dist,
                        "threshold": self._config.contact_distance_limit
                    })
                    continue

            geometrically_valid.append(prop)

        # --------------------------------------------------------------------
        # 3. 做功阶梯能耗势垒 (ΔE) 拦截
        # --------------------------------------------------------------------
        energy_cleared: List[ActionProposal] = []

        for prop in geometrically_valid:
            assert prop.kinematics is not None
            source_actor = world_state.actors[prop.agent_id]

            # 计算环境即时势垒: ΔE = α·Mass + β·(100 - Temp) + γ·ObsPressure
            temp_penalty = max(0.0, 100.0 - world_state.environment.temperature)
            delta_e = (
                self._config.alpha_mass * prop.kinematics.effective_mass
                + self._config.beta_temp * temp_penalty
                + self._config.gamma_obs * world_state.environment.observation_pressure
            )

            # 主体可用做功能量校验
            if source_actor.somatic.energy_pool < delta_e:
                resolved_kinematics.append({
                    "agent_id": prop.agent_id,
                    "status": "ENERGY_BARRIER_UNMET",
                    "required_delta_e": delta_e,
                    "available_pool": source_actor.somatic.energy_pool
                })
                # 生理损耗但动作不生效
                state_patches.append(
                    RFC6902Patch(
                        op="replace",
                        path=f"/actors/{prop.agent_id}/somatic/load",
                        value=source_actor.somatic.load + 1.0
                    )
                )
            else:
                energy_cleared.append(prop)

        # --------------------------------------------------------------------
        # 4. 动力学对撞分析与微观环境熵采样 (Coupling Engine)
        # --------------------------------------------------------------------
        # 双主体相互作用动力学仲裁
        if len(energy_cleared) == 2:
            p1, p2 = energy_cleared[0], energy_cleared[1]
            assert p1.kinematics is not None and p2.kinematics is not None

            # 彼此互为目标，判定为对抗性动能对撞
            if (p1.kinematics.target_id == p2.agent_id and
                    p2.kinematics.target_id == p1.agent_id):
                force_diff = abs(p1.kinematics.applied_force - p2.kinematics.applied_force)

                if force_diff < self._config.collision_deadlock_threshold:
                    # 形成临界死锁，消费 World Plane 注入的微观物理扰动熵
                    entropy_val = world_state.environment.micro_entropy_variable
                    resolved_kinematics.append({
                        "status": "KINEMATIC_DEADLOCK_RESOLVED_BY_ENTROPY",
                        "actors": [p1.agent_id, p2.agent_id],
                        "force_difference": force_diff,
                        "consumed_entropy": entropy_val
                    })
                    for p in (p1, p2):
                        actor_snap = world_state.actors[p.agent_id]
                        # 双方能耗扣减，动作滑脱
                        state_patches.append(
                            RFC6902Patch(
                                op="replace",
                                path=f"/actors/{p.agent_id}/somatic/energy_pool",
                                value=max(0.0, actor_snap.somatic.energy_pool - 2.0)
                            )
                        )
                else:
                    # 力道大者压制胜出
                    winner = p1 if p1.kinematics.applied_force > p2.kinematics.applied_force else p2
                    loser = p2 if winner == p1 else p1
                    assert winner.kinematics is not None
                    resolved_kinematics.append({
                        "status": "KINEMATIC_OPPOSITION_DECIDED",
                        "winner_id": winner.agent_id,
                        "loser_id": loser.agent_id,
                        "executed_action": winner.kinematics.action_type
                    })
                    # 胜者扣能，败者承受破坏
                    w_actor = world_state.actors[winner.agent_id]
                    l_actor = world_state.actors[loser.agent_id]
                    state_patches.append(
                        RFC6902Patch(
                            op="replace",
                            path=f"/actors/{winner.agent_id}/somatic/energy_pool",
                            value=max(0.0, w_actor.somatic.energy_pool - 5.0)
                        )
                    )
                    state_patches.append(
                        RFC6902Patch(
                            op="replace",
                            path=f"/actors/{loser.agent_id}/somatic/integrity",
                            value=max(0.0, l_actor.somatic.integrity - 10.0)
                        )
                    )
            else:
                for p in energy_cleared:
                    self._resolve_single_action(p, world_state, resolved_kinematics, state_patches)
        else:
            for p in energy_cleared:
                self._resolve_single_action(p, world_state, resolved_kinematics, state_patches)

        return VerifiedEventEntry(
            event_id=self._event_id_factory(tick),
            tick_index=tick,
            timestamp=timestamp,
            causal_status="RESOLVED",
            resolved_kinematics=resolved_kinematics,
            acoustic_emissions=acoustic_emissions,
            state_patches=state_patches
        )

    def _resolve_single_action(
        self,
        prop: ActionProposal,
        world_state: GlobalWorldState,
        resolved_list: List[Dict[str, Any]],
        patches: List[RFC6902Patch]
    ) -> None:
        """单主体无对撞物理动作结算"""
        assert prop.kinematics is not None
        actor = world_state.actors[prop.agent_id]
        resolved_list.append({
            "agent_id": prop.agent_id,
            "status": "ACTION_EXECUTED",
            "action_type": prop.kinematics.action_type
        })
        # 扣除做功能量
        patches.append(
            RFC6902Patch(
                op="replace",
                path=f"/actors/{prop.agent_id}/somatic/energy_pool",
                value=max(0.0, actor.somatic.energy_pool - 3.0)
            )
        )
