"""休息调度服务：管理"工作—休息"节奏的计时与状态机。

状态机：
    WORKING  → 计时累计工作时间，到达间隔后进入 BREAK_READY
    BREAK_READY → 触发提醒，等待用户确认（或自动开始）→ BREAKING
    BREAKING → 休息倒计时，结束后回到 WORKING
"""
from __future__ import annotations

import datetime as dt
from enum import Enum

from PySide6.QtCore import QObject, QTimer, Signal


class BreakState(Enum):
    IDLE = "idle"            # 未启用
    WORKING = "working"      # 工作中
    READY = "ready"          # 该休息了，等待确认
    BREAKING = "breaking"    # 休息中


class BreakService(QObject):
    """休息节奏调度器。"""

    tick = Signal(int, str)          # (剩余秒数, 状态值)
    break_ready = Signal()           # 该休息了
    break_started = Signal(int)      # 休息开始，参数为休息秒数
    break_finished = Signal(str)     # 休息结束，参数为原因 ok/skip

    def __init__(self, conf, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.conf = conf
        self.state = BreakState.IDLE
        self._work_elapsed = 0        # 已工作时间（秒）
        self._break_remaining = 0     # 休息剩余（秒）
        self._paused = False

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)

    # ------------------------------------------------------------------
    @property
    def interval_seconds(self) -> int:
        return int(self.conf.get("break_interval_min", 45)) * 60

    @property
    def duration_seconds(self) -> int:
        return int(self.conf.get("break_duration_sec", 300))

    def _in_work_window(self) -> bool:
        win = self.conf.get("break_work_windows", {"start": 8, "end": 22})
        hour = dt.datetime.now().hour
        return int(win.get("start", 0)) <= hour < int(win.get("end", 24))

    # ------------------------------------------------------------------
    def start(self) -> None:
        if not self.conf.get("break_enabled", True):
            self.state = BreakState.IDLE
            return
        self.state = BreakState.WORKING
        self._work_elapsed = 0
        self._paused = False
        self._timer.start()
        self._emit_tick()

    def stop(self) -> None:
        self._timer.stop()
        self.state = BreakState.IDLE
        self._emit_tick()

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def reset(self) -> None:
        """重置工作时间累计（例如用户手动开始新的一轮）。"""
        self._work_elapsed = 0
        if self.state in (BreakState.IDLE,):
            self.start()
        elif self.state == BreakState.READY:
            self.state = BreakState.WORKING
        self._emit_tick()

    def snooze(self) -> None:
        """推迟休息。"""
        minutes = int(self.conf.get("break_snooze_min", 5))
        self.state = BreakState.WORKING
        self._work_elapsed = max(0, self.interval_seconds - minutes * 60)
        self._emit_tick()

    # ------------------------------------------------------------------
    def start_break_now(self, manual: bool = True) -> None:
        """立即进入休息。"""
        self._break_remaining = self.duration_seconds
        self.state = BreakState.BREAKING
        if not self._timer.isActive():
            self._timer.start()
        self.break_started.emit(self._break_remaining)
        self._emit_tick()

    def finish_break(self, reason: str = "ok") -> None:
        """结束休息。"""
        self.state = BreakState.WORKING
        self._work_elapsed = 0
        self.break_finished.emit(reason)
        self._emit_tick()

    # ------------------------------------------------------------------
    def _on_tick(self) -> None:
        if self._paused:
            return
        if self.state == BreakState.WORKING:
            if self._in_work_window():
                self._work_elapsed += 1
            if self._work_elapsed >= self.interval_seconds:
                self._enter_ready()
        elif self.state == BreakState.BREAKING:
            self._break_remaining -= 1
            if self._break_remaining <= 0:
                self.finish_break("ok")
        self._emit_tick()

    def _enter_ready(self) -> None:
        self.state = BreakState.READY
        if self.conf.get("break_auto_start", False):
            self.start_break_now(manual=False)
        else:
            self.break_ready.emit()

    def _emit_tick(self) -> None:
        if self.state == BreakState.WORKING:
            remaining = max(0, self.interval_seconds - self._work_elapsed)
        elif self.state == BreakState.BREAKING:
            remaining = max(0, self._break_remaining)
        else:
            remaining = self.interval_seconds
        self.tick.emit(remaining, self.state.value)

    # ------------------------------------------------------------------
    def progress_percent(self) -> int:
        """当前工作进度百分比。"""
        if self.state == BreakState.BREAKING:
            total = max(1, self.duration_seconds)
            return int((total - self._break_remaining) / total * 100)
        total = max(1, self.interval_seconds)
        return int(min(100, self._work_elapsed / total * 100))

    @staticmethod
    def format_hms(seconds: int) -> str:
        seconds = max(0, int(seconds))
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
