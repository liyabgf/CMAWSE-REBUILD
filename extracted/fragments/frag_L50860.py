# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L50860-L50926 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #143  lines=66  compile=OK
# kind: fragment  ident: frag_L50860.py
# edits: none. Header comment is the only addition.
# ======================
# 真正领域中立的 CMAWSE-Core 核心契约接口

from typing import Protocol, TypeVar, Generic, Optional, Tuple, List, Dict, Any

StateT = TypeVar("StateT")         # 抽象世界状态
ObsT = TypeVar("ObsT")             # 抽象私有视界
ActionT = TypeVar("ActionT")       # 抽象动作意图
EventT = TypeVar("EventT")         # 抽象仲裁后事实

class TransitionModel(Protocol[StateT, ActionT, EventT]):
    """领域物理学接口：由特定业务/世界注入，Runtime 本身完全不理解其内部物理意义"""
    def project_observation(self, state: StateT, agent_id: str) -> ObsT:
        ...
    def validate_action(self, state: StateT, agent_id: str, action: ActionT) -> bool:
        ...
    def apply_transition(self, state: StateT, actions: Dict[str, ActionT]) -> Tuple[StateT, EventT]:
        ...

class CausalLedger(Protocol[EventT]):
    """因果事实账本：单调追加，只读暴露"""
    def append(self, event: EventT) -> None:
        ...
    def get_history(self) -> List[EventT]:
        ...

class CMAWSEKernel(Generic[StateT, ObsT, ActionT, EventT]):
    """
    真正最小的运行时：只控制调用时序、不可变性与信息单向流动。
    对摩擦力、能量、心理学、社会学等具体领域语义 100% 解耦。
    """
    def __init__(
        self,
        initial_state: StateT,
        transition_model: TransitionModel[StateT, ActionT, EventT],
        ledger: CausalLedger[EventT]
    ) -> None:
        self._state: StateT = initial_state
        self._model: TransitionModel[StateT, ActionT, EventT] = transition_model
        self._ledger: CausalLedger[EventT] = ledger

    def tick(self, agent_actions: Dict[str, ActionT]) -> EventT:
        # 1. 刚性安全校验：过滤非法动作
        sanitized_actions: Dict[str, ActionT] = {}
        for aid, act in agent_actions.items():
            if self._model.validate_action(self._state, aid, act):
                sanitized_actions[aid] = act
            else:
                # 非法提案直接丢弃，严禁进入世界转换
                pass

        # 2. 状态转移交由可插拔物理学模型执行
        next_state, verified_event = self._model.apply_transition(self._state, sanitized_actions)

        # 3. 事实入账与状态切结
        self._ledger.append(verified_event)
        self._state = next_state

        return verified_event

    def observe(self, agent_id: str) -> ObsT:
        """只读私有投影入口"""
        return self._model.project_observation(self._state, agent_id)

    def intervene(self, state_override: StateT) -> None:
        """外生干预：直接重置内部状态，不经任何 Agent 同意"""
        self._state = state_override
