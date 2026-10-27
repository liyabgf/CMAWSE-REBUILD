# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L1452-L1527 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #6  lines=75  compile=OK
# kind: module  ident: core/ledger.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）v1.2
模块：core/ledger.py
职责：Event Ledger 事实主权账本。
严格实现 Append-Only、线程安全、单调递增的事实持久化与只读切片检索。
严禁进行物理仲裁或直接突变业务状态。
"""

from __future__ import annotations

import copy
import threading
from typing import List, Optional

from cmawse.core.schema import VerifiedEventEntry


class LedgerIntegrityViolation(Exception):
    """事实账本完整性校验违例（阻止历史篡改或因果时序倒流）"""
    pass


class EventLedger:
    """系统最高事实主权账本容器"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: List[VerifiedEventEntry] = []
        self._registered_ids: set[str] = set()
        self._latest_tick: int = -1

    def append(self, entry: VerifiedEventEntry) -> None:
        """
        单调递增追加合法事实。
        """
        with self._lock:
            if entry.event_id in self._registered_ids:
                raise LedgerIntegrityViolation(
                    f"主权冲突：事件 ID '{entry.event_id}' 已经持久化，严禁篡改已生效历史。"
                )

            if entry.tick_index < self._latest_tick:
                raise LedgerIntegrityViolation(
                    f"因果逆流违例：当前提交事件 Tick ({entry.tick_index}) 小于 "
                    f"账本最高历史 Tick ({self._latest_tick})。"
                )

            self._entries.append(entry)
            self._registered_ids.add(entry.event_id)
            self._latest_tick = entry.tick_index

    def get_latest_entry(self) -> Optional[VerifiedEventEntry]:
        """获取最后一次落槌的事实（深度复制，防止只读视图穿透）"""
        with self._lock:
            if not self._entries:
                return None
            return copy.deepcopy(self._entries[-1])

    def query_slice(self, from_tick: int, to_tick: int) -> List[VerifiedEventEntry]:
        """时间区间事实切片检索"""
        with self._lock:
            matched = [
                e for e in self._entries
                if from_tick <= e.tick_index <= to_tick
            ]
            return copy.deepcopy(matched)

    def dump_immutable_history(self) -> List[VerifiedEventEntry]:
        """导出全量事实历史快照"""
        with self._lock:
            return copy.deepcopy(self._entries)

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
