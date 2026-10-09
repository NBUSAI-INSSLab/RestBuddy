"""当日任务醒目提醒弹窗（启动时 / 定时触发）。"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from ..database import Task
from ..icons import icon
from ..theme import palette


class TodayReminderDialog(QDialog):
    """以醒目卡片形式展示当天任务。"""

    snooze_requested = Signal(int)      # 稍后提醒（分钟）

    def __init__(self, tasks: list[Task], theme: str = "light", parent=None) -> None:
        super().__init__(parent)
        self.tasks = tasks
        self._theme = theme
        self.setObjectName("ReminderDialog")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(False)
        self.setFixedWidth(460)
        self._build()
        self._center()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        c = palette(self._theme)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        card = QFrame()
        card.setObjectName("ReminderCard")
        card.setStyleSheet(
            f"#ReminderCard{{background:{c['surface']};border:1px solid {c['border']};"
            f"border-radius:18px;}}"
        )
        outer.addWidget(card)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(12)

        # 顶部标题
        head = QHBoxLayout()
        bell = QLabel()
        bell.setPixmap(icon("bell", c["warning"], 56).pixmap(28, 28))
        head.addWidget(bell)
        col = QVBoxLayout()
        col.setSpacing(1)
        title = QLabel("今日任务提醒")
        title.setStyleSheet(f"font-size:18px;font-weight:700;color:{c['text']};")
        col.addWidget(title)
        today = dt.date.today()
        sub = QLabel(f"{today.strftime('%Y 年 %m 月 %d 日')} · 星期{'一二三四五六日'[today.weekday()]}")
        sub.setStyleSheet(f"font-size:12px;color:{c['text_muted']};")
        col.addWidget(sub)
        head.addLayout(col)
        head.addStretch(1)

        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.done)
        badge = QLabel(f"{done}/{total}")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(70, 46)
        badge.setStyleSheet(
            f"background:{c['primary_soft']};color:{c['primary']};"
            f"border-radius:12px;font-size:20px;font-weight:700;"
        )
        head.addWidget(badge)
        lay.addLayout(head)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{c['border']};")
        lay.addWidget(line)

        if not self.tasks:
            empty = QLabel("今天还没有安排任务，享受轻松的一天吧 🍃")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color:{c['text_muted']};font-size:14px;padding:26px 0;")
            lay.addWidget(empty)
        else:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setMaximumHeight(320)
            container = QWidget()
            v = QVBoxLayout(container)
            v.setContentsMargins(0, 0, 6, 0)
            v.setSpacing(8)
            # 未完成的排前面
            ordered = sorted(self.tasks, key=lambda t: (t.done, -t.priority))
            for t in ordered[:12]:
                v.addWidget(self._row(t))
            v.addStretch(1)
            scroll.setWidget(container)
            lay.addWidget(scroll)

        # 底部按钮
        btns = QHBoxLayout()
        btns.addStretch(1)
        btn_snooze = QPushButton("稍后提醒")
        btn_snooze.setObjectName("Ghost")
        btn_snooze.clicked.connect(self._on_snooze)
        btn_ok = QPushButton("开始今天")
        btn_ok.setObjectName("Primary")
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_snooze)
        btns.addWidget(btn_ok)
        lay.addLayout(btns)

    def _row(self, t: Task) -> QWidget:
        c = palette(self._theme)
        f = QFrame()
        f.setStyleSheet(
            f"background:{c['surface_alt']};border:1px solid {c['border']};"
            f"border-radius:10px;"
        )
        h = QHBoxLayout(f)
        h.setContentsMargins(12, 9, 12, 9)
        h.setSpacing(10)

        dot = QFrame()
        dot.setFixedSize(8, 8)
        color = c["success"] if t.done else t.priority_color
        dot.setStyleSheet(f"background:{color};border-radius:4px;")
        h.addWidget(dot)

        col = QVBoxLayout()
        col.setSpacing(1)
        lb = QLabel(t.title)
        deco = "text-decoration:line-through;" if t.done else ""
        lb.setStyleSheet(
            f"font-size:14px;font-weight:{'400' if t.done else '600'};"
            f"color:{c['text_muted'] if t.done else c['text']};{deco}"
        )
        lb.setWordWrap(True)
        col.addWidget(lb)
        meta_bits = [x for x in [t.time, t.category] if x]
        if meta_bits:
            m = QLabel(" · ".join(meta_bits))
            m.setStyleSheet(f"font-size:12px;color:{c['text_muted']};")
            col.addWidget(m)
        h.addLayout(col, 1)

        tag = QLabel(t.priority_label)
        tag.setStyleSheet(
            f"color:#ffffff;background:{t.priority_color};border-radius:8px;"
            f"padding:2px 8px;font-size:11px;"
        )
        h.addWidget(tag)
        return f

    # ------------------------------------------------------------------
    def _on_snooze(self) -> None:
        self.snooze_requested.emit(10)
        self.accept()

    def _center(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.adjustSize()
        x = geo.center().x() - self.width() // 2
        y = geo.top() + 90
        self.move(x, y)
