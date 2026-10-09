"""任务卡片小部件：单条任务的展示与快捷操作。"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)

from ..database import Task
from ..icons import icon
from ..theme import palette


class TaskCard(QFrame):
    """一条任务。点击复选框切换完成状态，右侧提供编辑/删除。"""

    toggled = Signal(int)
    edit_requested = Signal(object)
    delete_requested = Signal(object)

    def __init__(self, task: Task, theme: str = "light",
                 compact: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.task = task
        self._theme = theme
        self._compact = compact
        self.setObjectName("CardFlat")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._build()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        c = palette(self._theme)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 10, 8)
        lay.setSpacing(10)

        # 优先级色条
        bar = QFrame()
        bar.setFixedWidth(4)
        bar.setMinimumHeight(30)
        bar.setStyleSheet(
            f"background:{self.task.priority_color};border-radius:2px;"
        )
        lay.addWidget(bar)

        self.cb = QCheckBox()
        self.cb.setChecked(self.task.done)
        self.cb.setCursor(Qt.PointingHandCursor)
        self.cb.stateChanged.connect(lambda _s: self.toggled.emit(self.task.id or -1))
        lay.addWidget(self.cb)

        text = QVBoxLayout()
        text.setSpacing(2)
        text.setContentsMargins(0, 0, 0, 0)

        self.lb_title = QLabel(self.task.title)
        self.lb_title.setWordWrap(True)
        color = c["text_muted"] if self.task.done else c["text"]
        deco = "text-decoration: line-through;" if self.task.done else ""
        weight = "400" if self.task.done else "600"
        self.lb_title.setStyleSheet(
            f"color:{color};{deco}font-size:14px;font-weight:{weight};"
        )
        text.addWidget(self.lb_title)

        meta = self._meta_text()
        if meta:
            self.lb_meta = QLabel(meta)
            self.lb_meta.setObjectName("Muted")
            self.lb_meta.setStyleSheet(f"color:{c['text_muted']};font-size:12px;")
            text.addWidget(self.lb_meta)

        lay.addLayout(text, 1)

        if self.task.time:
            self.lb_time = QLabel(self.task.time)
            self.lb_time.setStyleSheet(
                f"color:{c['text_muted']};font-size:13px;font-weight:600;"
            )
            lay.addWidget(self.lb_time)

        if not self._compact:
            self.btn_edit = self._mk_btn("edit", c["text_muted"], "编辑")
            self.btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.task))
            self.btn_del = self._mk_btn("trash", c["danger"], "删除")
            self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self.task))
            lay.addWidget(self.btn_edit)
            lay.addWidget(self.btn_del)

    def _mk_btn(self, name: str, color: str, tip: str) -> QPushButton:
        b = QPushButton()
        b.setIcon(icon(name, color, 32))
        b.setFixedSize(28, 28)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:6px;}"
            "QPushButton:hover{background:rgba(128,128,128,0.18);}"
        )
        return b

    def _meta_text(self) -> str:
        parts = [f"{self.task.priority_label}优先", self.task.category]
        if self.task.notes:
            parts.append(self.task.notes)
        if self.task.remind_min and self.task.remind_min > 0:
            parts.append(f"提前{self.task.remind_min}分钟提醒")
        base = " · ".join(p for p in parts if p)
        if not self.task.done and self.task.date:
            today = dt.date.today().isoformat()
            if self.task.date < today:
                base = "已逾期 · " + base
        return base
