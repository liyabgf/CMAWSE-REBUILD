# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L475-L661 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #2  lines=186  compile=OK
# kind: module  ident: committer.py  version: latest of 1 (selected by latest source line)
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）
模块：committer.py
职责：State Committer (全局状态单点提交器)。
纯 Python 原生实现 RFC 6902 JSON Patch 规格规范，确保全局物理状态单点原子提交与回滚。
"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, List

from cmawse.core.schema import GlobalWorldState, RFC6902Patch


class PatchApplicationError(Exception):
    """RFC 6902 Patch 应用异常"""
    pass


class StateCommitter:
    """
    全系统唯一拥有 Global World State 写主权的实体。
    任何外部平面只允许通过传入 RFC6902Patch 补丁集请求原子演进。
    """

    @classmethod
    def apply_patches(
        cls,
        current_state: GlobalWorldState,
        patches: List[RFC6902Patch]
    ) -> GlobalWorldState:
        """
        原子应用补丁集。
        若任何一个 Patch 失败，必须立即抛出异常中断，不产生部分修改脏数据。
        """
        # 1. 序列化当前快照为纯字典结构作为暂存沙盒
        state_dict = current_state.model_dump()
        staged_dict = copy.deepcopy(state_dict)

        # 2. 逐条执行 RFC 6902 算子
        for idx, patch in enumerate(patches):
            try:
                cls._apply_single_patch(staged_dict, patch)
            except Exception as exc:
                raise PatchApplicationError(
                    f"原子提交在第 {idx} 号 Patch 失败: [{patch.op} -> {patch.path}]. "
                    f"原因: {str(exc)}. 全局状态已阻断回滚。"
                ) from exc

        # 3. 校验并重新构建全新的不可变 GlobalWorldState
        return GlobalWorldState.model_validate(staged_dict)

    # ========================================================================
    # RFC 6902 内部实现引擎
    # ========================================================================

    @staticmethod
    def _parse_pointer(path: str) -> List[str]:
        """将 RFC 6901 JSON Pointer 转换为键路径数组"""
        if not path:
            return []
        tokens = path.split("/")[1:]
        # RFC 6901 转义字符解析 (~1 -> /, ~0 -> ~)
        return [t.replace("~1", "/").replace("~0", "~") for t in tokens]

    @classmethod
    def _resolve_target(
        cls,
        data: Dict[str, Any],
        tokens: List[str],
        create_missing: bool = False
    ) -> tuple[Any, str | int]:
        """沿着 JSON Pointer 定位目标父节点与最终 Key/Index"""
        if not tokens:
            raise PatchApplicationError("指向根节点的指针不可作为叶子节点修改")

        curr: Any = data
        for token in tokens[:-1]:
            if isinstance(curr, dict):
                if token not in curr:
                    if create_missing:
                        curr[token] = {}
                    else:
                        raise KeyError(f"未找到属性节点: {token}")
                curr = curr[token]
            elif isinstance(curr, list):
                if not re.match(r"^\d+$", token):
                    raise IndexError(f"数组非法索引: {token}")
                idx = int(token)
                if idx < 0 or idx >= len(curr):
                    raise IndexError(f"数组索引越界: {idx}")
                curr = curr[idx]
            else:
                raise TypeError(f"无法在标量节点深入寻址: {type(curr)}")

        last_token = tokens[-1]
        final_key: str | int = last_token
        if isinstance(curr, list) and last_token != "-":
            if not re.match(r"^\d+$", last_token):
                raise IndexError(f"数组非法索引: {last_token}")
            final_key = int(last_token)

        return curr, final_key

    @classmethod
    def _apply_single_patch(cls, doc: Dict[str, Any], patch: RFC6902Patch) -> None:
        tokens = cls._parse_pointer(patch.path)
        op = patch.op

        if op == "add":
            parent, key = cls._resolve_target(doc, tokens, create_missing=True)
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
            parent, key = cls._resolve_target(doc, tokens)
            if isinstance(parent, list):
                assert isinstance(key, int)
                if key < 0 or key >= len(parent):
                    raise IndexError(f"数组删除索引越界: {key}")
                parent.pop(key)
            elif isinstance(parent, dict):
                assert isinstance(key, str)
                if key not in parent:
                    raise KeyError(f"属性不存在: {key}")
                del parent[key]

        elif op == "replace":
            parent, key = cls._resolve_target(doc, tokens)
            if isinstance(parent, list):
                assert isinstance(key, int)
                if key < 0 or key >= len(parent):
                    raise IndexError(f"数组替换索引越界: {key}")
                parent[key] = patch.value
            elif isinstance(parent, dict):
                assert isinstance(key, str)
                if key not in parent:
                    raise KeyError(f"属性不存在，无法执行 replace: {key}")
                parent[key] = patch.value

        elif op == "test":
            parent, key = cls._resolve_target(doc, tokens)
            actual_val = parent[key] if isinstance(parent, (dict, list)) else None
            if actual_val != patch.value:
                raise PatchApplicationError(
                    f"Test 断言失败: 路径 {patch.path} 期望值为 {patch.value}，实际为 {actual_val}"
                )

        elif op in ("move", "copy"):
            if not patch.from_path:
                raise PatchApplicationError(f"操作 {op} 缺少 'from' 路径")
            from_tokens = cls._parse_pointer(patch.from_path)
            from_parent, from_key = cls._resolve_target(doc, from_tokens)
            value_to_move = from_parent[from_key]

            if op == "move":
                if isinstance(from_parent, list):
                    assert isinstance(from_key, int)
                    from_parent.pop(from_key)
                else:
                    assert isinstance(from_key, str)
                    del from_parent[from_key]

            # 插入到新位置
            parent, key = cls._resolve_target(doc, tokens, create_missing=True)
            if isinstance(parent, list):
                if key == "-":
                    parent.append(copy.deepcopy(value_to_move))
                else:
                    assert isinstance(key, int)
                    parent.insert(key, copy.deepcopy(value_to_move))
            elif isinstance(parent, dict):
                assert isinstance(key, str)
                parent[key] = copy.deepcopy(value_to_move)

        else:
            raise PatchApplicationError(f"未知的 RFC 6902 操作符: {op}")
