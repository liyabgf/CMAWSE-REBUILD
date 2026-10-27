# ===== PROVENANCE =====
# status: RESTORED (verbatim extraction from conversation export)
# source: CMAWSE第一阶段.md @ L385-L468 (SHA-256 anchored, see manifests/SHA256SUMS.txt)
# block: python #1  lines=83  compile=OK
# kind: module  ident: ledger.py  version: 1/1
# edits: none. Header comment is the only addition.
# ======================
"""
约束驱动的复杂叙事仿真引擎（CMAWSE）
模块：ledger.py
职责：Event Ledger 事实主权账本。
严格实现 Append-Only、线程安全、单调递增的事实持久化与只读切片检索。
"""

from __future__ import annotations

import copy
import threading
from typing import List, Optional

from cmawse.core.schema import VerifiedEventEntry


class LedgerIntegrityError(Exception):
    """事实账本完整性校验违例异常"""
    pass


class EventLedger:
    """
    Event Ledger (最高事实主权账本)
    CMAWSE 第一公理执行载体：只读、单调递增、历史不可逆。
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: List[VerifiedEventEntry] = []
        self._event_ids: set[str] = set()
        self._last_tick: int = -1

    def append(self, entry: VerifiedEventEntry) -> None:
        """
        向账本单调追加新的已仲裁事实。
        执行严格的主权完整性断言：
        1. 事件 ID 全局唯一；
        2. Tick 严格单调不递减（支持同一 Tick 仲裁出批次事件，但不可倒流）；
        3. 数据结构一旦提交即加锁不可篡改。
        """
        with self._lock:
            if entry.event_id in self._event_ids:
                raise LedgerIntegrityError(
                    f"主权账本冲突：事件 ID '{entry.event_id}' 已经存在，严禁覆写历史事实。"
                )

            if entry.tick_index < self._last_tick:
                raise LedgerIntegrityError(
                    f"因果时序倒流违例：当前提交 Tick ({entry.tick_index}) 小于 "
                    f"账本最后生效 Tick ({self._last_tick})。"
                )

            # 追加写入
            self._entries.append(entry)
            self._event_ids.add(entry.event_id)
            self._last_tick = entry.tick_index

    def get_latest_event(self) -> Optional[VerifiedEventEntry]:
        """只读获取账本尾部最新生效事实"""
        with self._lock:
            if not self._entries:
                return None
            return copy.deepcopy(self._entries[-1])

    def get_events_after_tick(self, tick: int) -> List[VerifiedEventEntry]:
        """获取指定 Tick 之后生效的所有事实切片（只读副本）"""
        with self._lock:
            filtered = [e for e in self._entries if e.tick_index > tick]
            return copy.deepcopy(filtered)

    def get_full_immutable_history(self) -> List[VerifiedEventEntry]:
        """
        供 Narrative Monitor 等校验实体进行事实核对时获取完整历史切片。
        返回深度副本，杜绝外部突变内部状态。
        """
        with self._lock:
            return copy.deepcopy(self._entries)

    def count(self) -> int:
        """当前已登记的事实总数"""
        with self._lock:
            return len(self._entries)
