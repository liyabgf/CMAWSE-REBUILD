# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L1534-L1719 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #7  lines=185  compile=OK
# kind: module  ident: core/committer.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：core/committer.py
职责：State Committer (全局状态单点提交器)。
基于 RFC 6902 纯函数式状态演进。保证原子生效与失败完全零污染回滚。
"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, List

from cmawse.core.schema import GlobalWorldState, RFC6902Patch


class CommitTransactionError(Exception):
    """原子事务提交失败异常"""
    pass


class StateCommitter:
    """全系统唯一拥有 Global World State 状态演进写权限的执行体"""

    @classmethod
    def apply_transaction(
        cls,
        base_state: GlobalWorldState,
        patches: List[RFC6902Patch],
        next_tick: Optional[int] = None,
        next_timestamp: Optional[str] = None
    ) -> GlobalWorldState:
        """
        原子事务：将一组 RFC 6902 补丁完全作用于当前快照，返回新快照。
        若任何一个 Patch 触发断言或越界，立即中断抛出异常，base_state 丝毫不变。
        """
        # 1. 深度拷贝转化为裸字典沙盒
        raw_data: Dict[str, Any] = base_state.model_dump()
        sandbox = copy.deepcopy(raw_data)

        # 2. 逐条执行操作
        for step_idx, patch in enumerate(patches):
            try:
                cls._execute_patch_operation(sandbox, patch)
            except Exception as err:
                raise CommitTransactionError(
                    f"提交在补丁 #{step_idx} [{patch.op} -> {patch.path}] 失败: {str(err)}. "
                    f"事务整体撤销。"
                ) from err

        # 3. 推进状态元数据
        if next_tick is not None:
            sandbox["tick"] = next_tick
        if next_timestamp is not None:
            sandbox["timestamp"] = next_timestamp

        # 4. 强类型模型重新验证（防非法破坏契约结构）
        return GlobalWorldState.model_validate(sandbox)

    # ------------------------------------------------------------------------
    # RFC 6902 指针解析与底层操作
    # ------------------------------------------------------------------------

    @staticmethod
    def _parse_pointer(path: str) -> List[str]:
        if not path:
            return []
        tokens = path.split("/")[1:]
        return [t.replace("~1", "/").replace("~0", "~") for t in tokens]

    @classmethod
    def _navigate_to_parent(
        cls,
        doc: Dict[str, Any],
        tokens: List[str],
        allow_autovivify: bool = False
    ) -> tuple[Any, str | int]:
        if not tokens:
            raise CommitTransactionError("指向根节点的 JSON Pointer 不可作为叶子节点修改")

        current: Any = doc
        for token in tokens[:-1]:
            if isinstance(current, dict):
                if token not in current:
                    if allow_autovivify:
                        current[token] = {}
                    else:
                        raise KeyError(f"路径片段不存在: '{token}'")
                current = current[token]
            elif isinstance(current, list):
                if not re.match(r"^\d+$", token):
                    raise IndexError(f"数组索引必须为无符号整数: '{token}'")
                idx = int(token)
                if idx < 0 or idx >= len(current):
                    raise IndexError(f"数组寻址越界: {idx}")
                current = current[idx]
            else:
                raise TypeError(f"标量节点无法作为容器深入访问: {type(current)}")

        last_token = tokens[-1]
        final_key: str | int = last_token
        if isinstance(current, list) and last_token != "-":
            if not re.match(r"^\d+$", last_token):
                raise IndexError(f"数组索引格式错误: '{last_token}'")
            final_key = int(last_token)

        return current, final_key

    @classmethod
    def _execute_patch_operation(cls, doc: Dict[str, Any], patch: RFC6902Patch) -> None:
        tokens = cls._parse_pointer(patch.path)
        op = patch.op

        if op == "add":
            parent, key = cls._navigate_to_parent(doc, tokens, allow_autovivify=True)
            if isinstance(parent, list):
                if key == "-":
                    parent.append(patch.value)
                else:
                    assert isinstance(key, int)
                    parent.insert(key, patch.value)
            elif isinstance(parent, dict):
                assert isinstance(key, str)
                parent[key] = patch.value

        elif op == "remove":
            parent, key = cls._navigate_to_parent(doc, tokens)
            if isinstance(parent, list):
                assert isinstance(key, int)
                if key < 0 or key >= len(parent):
                    raise IndexError(f"删除索引超出数组界限: {key}")
                parent.pop(key)
            elif isinstance(parent, dict):
                assert isinstance(key, str)
                if key not in parent:
                    raise KeyError(f"待删除属性键不存在: '{key}'")
                del parent[key]

        elif op == "replace":
            parent, key = cls._navigate_to_parent(doc, tokens)
            if isinstance(parent, list):
                assert isinstance(key, int)
                if key < 0 or key >= len(parent):
                    raise IndexError(f"替换索引超出数组界限: {key}")
                parent[key] = patch.value
            elif isinstance(parent, dict):
                assert isinstance(key, str)
                if key not in parent:
                    raise KeyError(f"待替换目标键不存在: '{key}'")
                parent[key] = patch.value

        elif op == "test":
            parent, key = cls._navigate_to_parent(doc, tokens)
            actual = parent[key] if isinstance(parent, (dict, list)) else None
            if actual != patch.value:
                raise CommitTransactionError(
                    f"RFC 6902 test 断言不匹配：路径 '{patch.path}' 期望值 {patch.value}, 实际值 {actual}"
                )

        elif op in ("move", "copy"):
            if not patch.from_path:
                raise CommitTransactionError(f"操作符 '{op}' 必须指定 'from' 路径")
            from_tokens = cls._parse_pointer(patch.from_path)
            from_parent, from_key = cls._navigate_to_parent(doc, from_tokens)
            source_val = from_parent[from_key]

            if op == "move":
                if isinstance(from_parent, list):
                    assert isinstance(from_key, int)
                    from_parent.pop(from_key)
                else:
                    assert isinstance(from_key, str)
                    del from_parent[from_key]

            parent, key = cls._navigate_to_parent(doc, tokens, allow_autovivify=True)
            copied_val = copy.deepcopy(source_val)
            if isinstance(parent, list):
                if key == "-":
                    parent.append(copied_val)
                else:
                    assert isinstance(key, int)
                    parent.insert(key, copied_val)
            elif isinstance(parent, dict):
                assert isinstance(key, str)
                parent[key] = copied_val
