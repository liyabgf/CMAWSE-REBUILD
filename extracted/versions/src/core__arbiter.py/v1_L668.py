# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L668-L942 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #3  lines=274  compile=OK
# kind: module  ident: core/arbiter.py  version: 1/2
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）
模块：arbiter.py
职责：Causal Arbiter (因果阻尼与动力学仲裁法庭)。
负责终结 Agent 的行动幻想。根据空间前置条件、做功阶梯能耗势垒 (ΔE)、
动能矢量对撞与微观环境随机熵进行仲裁，输出不可篡改的唯一合法 VerifiedEventEntry。
"""

from __future__ import annotations

import random
from typing import List, Optional

from cmawse.core.schema import (
    ActionProposal,
    ActionStage,
    DialogueRecord,
    GlobalWorldState,
    RFC6902Patch,
    VerifiedEventEntry,
)


class CausalArbiter:
    """
    确定性动力学法庭。
    无状态仲裁执行层：输入多主体意图提案与当前世界物理环境，
    根据白皮书因果公理仲裁出唯一物理事实。
    """

    # 力学势垒经验参数 (白皮书 4.2 公式标定)
    ALPHA_MASS = 0.05
    BETA_TEMP = 0.15
    GAMMA_OBSERVATION = 25.0
    COLLISION_EPSILON = 2.0  # 死锁临界阈值

    def __init__(self, random_seed: Optional[int] = None) -> None:
        self._rng = random.Random(random_seed)

    def arbitrate(
        self,
        tick_index: int,
        timestamp: str,
        proposals: List[ActionProposal],
        world_state: GlobalWorldState
    ) -> VerifiedEventEntry:
        """
        单步仲裁核心管线：
        1. 过滤 SILENT_PASS 提案；
        2. 空间距离与物理可行性矩阵校验（剔除超距与空间穿透）；
        3. 做功阶梯能耗势垒 (ΔE) 审查（动能不足强行降阶）；
        4. 双主体意图对抗动能对撞与微观环境随机变量（Roll）采样；
        5. 构造确定性物理事实条目与对应 RFC 6902 Patches。
        """
        verified_facts: List[str] = []
        dialogue_emissions: List[DialogueRecord] = []
        state_patches: List[RFC6902Patch] = []

        # 1. 分离言语通道与微观物理动作提案
        active_kinematics: List[ActionProposal] = []
        for prop in proposals:
            # 优先处理言语通道（言语做功势垒极低，但在场主体必须具备有效生理意识）
            if prop.verbal and not prop.is_silent_pass:
                speaker_snap = world_state.actors.get(prop.agent_id)
                if speaker_snap and not speaker_snap.somatic.sensory_overload:
                    dialogue_emissions.append(
                        DialogueRecord(
                            speaker=prop.agent_id,
                            phonetics=prop.verbal.text,
                            acoustic_signature=prop.verbal.acoustic
                        )
                    )

            if prop.is_silent_pass or prop.kinematics is None:
                # 零事件轮合法性公理：角色选择静默、原地发呆为最高优先级合法状态
                continue
            active_kinematics.append(prop)

        # 2. 如果没有任何肢体物理提案，仅包含言语或全部静默
        if not active_kinematics:
            if not dialogue_emissions:
                verified_facts.append("全场保持静默，空气中的阻尼未被克服，无宏观物理位移发生。")
            event_id = f"evt_{tick_index:08d}_0001"
            return VerifiedEventEntry(
                event_id=event_id,
                tick_index=tick_index,
                timestamp=timestamp,
                verified_physical_facts=verified_facts,
                dialogue_emissions=dialogue_emissions,
                state_patches=state_patches
            )

        # 3. 空间前置条件断言 (Causal Gate)
        valid_proposals: List[ActionProposal] = []
        for prop in active_kinematics:
            assert prop.kinematics is not None
            source_actor = world_state.actors.get(prop.agent_id)
            if not source_actor:
                continue

            # 目标主体距离检查
            if prop.kinematics.target_agent_id:
                target_actor = world_state.actors.get(prop.kinematics.target_agent_id)
                if target_actor:
                    dist = source_actor.coordinate.distance_to(target_actor.coordinate)
                    # 白皮书规定：超过 3.0 米无法执行接触性肢体动作
                    if dist > 3.0:
                        verified_facts.append(
                            f"[{prop.agent_id}] 试图对 [{prop.kinematics.target_agent_id}] 执行接触动作，"
                            f"但物理间距为 {dist:.2f}m（超出阈值 3.0m），动作落空。"
                        )
                        continue

            valid_proposals.append(prop)

        # 4. 做功阶梯能耗势垒 (ΔE) 拦截
        survived_proposals: List[ActionProposal] = []
        for prop in valid_proposals:
            assert prop.kinematics is not None
            source_actor = world_state.actors[prop.agent_id]
            delta_e = self._calculate_energy_barrier(
                mass=prop.kinematics.mass_kg,
                ambient_temp=world_state.spatial_params.ambient_temp,
                obs_pressure=world_state.spatial_params.observation_pressure
            )

            # 主体可用动物性驱力计算：肾上腺素放大，疲劳与疼痛惩罚
            available_drive = (
                source_actor.somatic.adrenaline * 1.5
                - source_actor.somatic.fatigue * 0.8
                - source_actor.somatic.pain * 0.5
            )

            if available_drive < delta_e:
                # 势能不足，强行降阶为微弱代偿动作
                verified_facts.append(
                    f"[{prop.agent_id}] 动能不足以跨越阻尼势垒 (驱力 {available_drive:.1f} < 势垒 {delta_e:.1f})，"
                    f"动作降阶：指尖仅产生微弱颤动，未能形成有效做功。"
                )
                # 产生微量疲劳累积 Patch
                new_fatigue = min(100.0, source_actor.somatic.fatigue + 1.0)
                state_patches.append(
                    RFC6902Patch(
                        op="replace",
                        path=f"/actors/{prop.agent_id}/somatic/fatigue",
                        value=new_fatigue
                    )
                )
            else:
                survived_proposals.append(prop)

        # 5. 意图动能对抗与环境微观随机熵采样 (Coupling & Collision Engine)
        # 检验是否存在多主体对抗（以两两交互为例）
        if len(survived_proposals) >= 2:
            p1, p2 = survived_proposals[0], survived_proposals[1]
            assert p1.kinematics is not None and p2.kinematics is not None

            # 彼此互为目标，判定为动力学对撞
            if (p1.kinematics.target_agent_id == p2.agent_id and
                    p2.kinematics.target_agent_id == p1.agent_id):
                diff = abs(p1.kinematics.force_magnitude - p2.kinematics.force_magnitude)
                if diff < self.COLLISION_EPSILON:
                    # 死锁！从物理环境抽取微观随机变量打破对称性
                    roll = self._rng.choice(["地面湿滑受力打滑", "远处突发声响导致重心失衡", "衣料纤维撕扯悬空"])
                    verified_facts.append(
                        f"[{p1.agent_id}] 与 [{p2.agent_id}] 动作矢量形成对称死锁 (差值 {diff:.2f} < {self.COLLISION_EPSILON})。"
                        f"法庭引入环境熵打破平衡：因【{roll}】，双方动作同时侧滑悬空！"
                    )
                    # 双方增加疲劳与失衡
                    for p in (p1, p2):
                        actor_snap = world_state.actors[p.agent_id]
                        state_patches.append(
                            RFC6902Patch(
                                op="replace",
                                path=f"/actors/{p.agent_id}/somatic/fatigue",
                                value=min(100.0, actor_snap.somatic.fatigue + 4.0)
                            )
                        )
                else:
                    # 胜出者动作生效，受损者被迫位移
                    winner = p1 if p1.kinematics.force_magnitude > p2.kinematics.force_magnitude else p2
                    loser = p2 if winner == p1 else p1
                    verified_facts.append(
                        f"动力学动能对抗：[{winner.agent_id}] (力道 {winner.kinematics.force_magnitude:.1f}) 压制 "
                        f"[{loser.agent_id}] (力道 {loser.kinematics.force_magnitude:.1f})。"
                        f"实物动作生效：{winner.kinematics.action_description}。"
                    )
                    self._apply_successful_action_patches(winner, loser, world_state, state_patches)
            else:
                # 独立发生动作
                for p in survived_proposals:
                    verified_facts.append(f"[{p.agent_id}] 执行物理动作：{p.kinematics.action_description}")
                    self._apply_single_actor_patches(p, world_state, state_patches)
        elif len(survived_proposals) == 1:
            p = survived_proposals[0]
            assert p.kinematics is not None
            verified_facts.append(f"[{p.agent_id}] 执行物理动作：{p.kinematics.action_description}")
            self._apply_single_actor_patches(p, world_state, state_patches)

        # 6. 打包构建不可逆的唯一事实 entry
        event_id = f"evt_{tick_index:08d}_{self._rng.randint(1000, 9999)}"
        return VerifiedEventEntry(
            event_id=event_id,
            tick_index=tick_index,
            timestamp=timestamp,
            verified_physical_facts=verified_facts,
            dialogue_emissions=dialogue_emissions,
            state_patches=state_patches
        )

    def _calculate_energy_barrier(
        self,
        mass: float,
        ambient_temp: float,
        obs_pressure: float
    ) -> float:
        """白皮书公式：ΔE = α·Mass + β·(100 - Temp) + γ·SocialObservationPressure"""
        temp_factor = max(0.0, 100.0 - ambient_temp)
        return (
            self.ALPHA_MASS * mass
            + self.BETA_TEMP * temp_factor
            + self.GAMMA_OBSERVATION * obs_pressure
        )

    def _apply_successful_action_patches(
        self,
        winner: ActionProposal,
        loser: ActionProposal,
        world_state: GlobalWorldState,
        patches: List[RFC6902Patch]
    ) -> None:
        """对抗胜出后的状态补丁生成"""
        winner_actor = world_state.actors[winner.agent_id]
        loser_actor = world_state.actors[loser.agent_id]

        # 胜者消耗能量
        patches.append(
            RFC6902Patch(
                op="replace",
                path=f"/actors/{winner.agent_id}/somatic/fatigue",
                value=min(100.0, winner_actor.somatic.fatigue + 5.0)
            )
        )
        # 败者增加疼痛与失控
        patches.append(
            RFC6902Patch(
                op="replace",
                path=f"/actors/{loser.agent_id}/somatic/pain",
                value=min(100.0, loser_actor.somatic.pain + 8.0)
            )
        )
        patches.append(
            RFC6902Patch(
                op="replace",
                path=f"/actors/{loser.agent_id}/somatic/sensory_overload",
                value=True
            )
        )

    def _apply_single_actor_patches(
        self,
        proposal: ActionProposal,
        world_state: GlobalWorldState,
        patches: List[RFC6902Patch]
    ) -> None:
        """单人无对抗动作成功实施后的状态消耗"""
        actor = world_state.actors[proposal.agent_id]
        patches.append(
            RFC6902Patch(
                op="replace",
                path=f"/actors/{proposal.agent_id}/somatic/fatigue",
                value=min(100.0, actor.somatic.fatigue + 2.5)
            )
        )
