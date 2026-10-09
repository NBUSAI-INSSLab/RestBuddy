"""任务日历页：日历 + 选中日期的任务列表。"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QColor, QTextCharFormat
from PySide6.QtWidgets import (
    QCalendarWidget, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from ..database import Task
from ..icons import icon
from ..theme import palette
from ..widgets.common import Card
from ..widgets.task_card import TaskCard
from ..widgets.task_dialog import TaskDialog


class CalendarView(QWidget):
    """任务日历。"""

    tasks_changed = Signal()

    def __init__(self, repo, conf, theme: str = "light", parent=None) -> None:
        super().__init__(parent)
        self.repo = repo
        self.conf = conf
        self._theme = theme
        self._build()
        self.refresh()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        c = palette(self._theme)
        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 12, 12)
        root.setSpacing(16)

        # 左：日历
        cal_card = Card("任务日历", self._theme, subtitle="")
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        self.calendar.setFirstDayOfWeek(Qt.Monday)
        self.calendar.setMinimumHeight(320)
        self.calendar.selectionChanged.connect(self._on_date_selected)
        self.calendar.currentPageChanged.connect(self._on_page_changed)
        self.calendar.clicked.connect(self._on_date_selected)
        cal_card.add(self.calendar)

        nav = QHBoxLayout()
        btn_today = QPushButton("回到今天")
        btn_today.clicked.connect(self._goto_today)
        btn_new = QPushButton("新建任务")
        btn_new.setObjectName("Primary")
        btn_new.clicked.connect(self._new_task)
        nav.addWidget(btn_today)
        nav.addStretch(1)
        nav.addWidget(btn_new)
        cal_card.add_layout(nav)

        left = QWidget()
        left.setLayout(QVBoxLayout())
        left.layout().setContentsMargins(0, 0, 0, 0)
        left.layout().addWidget(cal_card)
        left.setMinimumWidth(360)
        left.setMaximumWidth(420)
        root.addWidget(left)

        # 右：任务列表
        self.list_card = Card("", self._theme, subtitle="")
        self.lb_title = QLabel("今天")
        self.lb_title.setObjectName("H2")
        self.list_card.add_header_widget(self.lb_title)
        self.lb_count = QLabel("")
        self.lb_count.setObjectName("Muted")
        self.list_card.add_header_widget(self.lb_count)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 8, 0)
        self.list_layout.setSpacing(8)
        scroll.setWidget(self.container)
        self.list_card.add(scroll, 1)
        root.addWidget(self.list_card, 1)

        self._selected = dt.date.today()

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        self._highlight()
        self._load_date(self._selected)

    def _highlight(self) -> None:
        """在日历上标记有任务的日期。"""
        c = palette(self._theme)
        # 清除既有格式
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())

        year = self.calendar.yearShown()
        month = self.calendar.monthShown()
        counts = self.repo.dates_with_tasks(year, month)
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(c["primary_soft"]))
        fmt.setForeground(QColor(c["primary"]))
        fmt.setFontWeight(700)
        for date_str in counts:
            qd = QDate.fromString(date_str, "yyyy-MM-dd")
            if qd.isValid():
                self.calendar.setDateTextFormat(qd, fmt)

        today_fmt = QTextCharFormat()
        today_fmt.setForeground(QColor(c["danger"]))
        today_fmt.setFontWeight(800)
        self.calendar.setDateTextFormat(QDate.currentDate(), today_fmt)

    def _on_page_changed(self, _y, _m) -> None:
        self._highlight()

    def _on_date_selected(self) -> None:
        qd = self.calendar.selectedDate()
        self._selected = dt.date(qd.year(), qd.month(), qd.day())
        self._load_date(self._selected)

    def _goto_today(self) -> None:
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.showToday()
        self._on_date_selected()

    def _load_date(self, date: dt.date) -> None:
        date_str = date.isoformat()
        tasks = self.repo.by_date(date_str)
        week = "一二三四五六日"[date.weekday()]
        today = dt.date.today()
        prefix = "今天 · " if date == today else ""
        self.lb_title.setText(f"{prefix}{date.month} 月 {date.day} 日 星期{week}")
        done = sum(1 for t in tasks if t.done)
        self.lb_count.setText(f"{done}/{len(tasks)} 已完成")

        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not tasks:
            empty = QLabel("这一天还没有任务")
            empty.setObjectName("Muted")
            empty.setAlignment(Qt.AlignCenter)
            empty.setMinimumHeight(120)
            self.list_layout.addWidget(empty)
        else:
            for t in tasks:
                card = TaskCard(t, self._theme)
                card.toggled.connect(self._on_toggle)
                card.edit_requested.connect(self._edit_task)
                card.delete_requested.connect(self._delete_task)
                self.list_layout.addWidget(card)
        self.list_layout.addStretch(1)

    # ------------------------------------------------------------------
    def _on_toggle(self, task_id: int) -> None:
        if task_id and task_id > 0:
            self.repo.toggle_done(task_id)
            self.tasks_changed.emit()
            self.refresh()

    def _new_task(self) -> None:
        dlg = TaskDialog(None, self._theme, default_date=self._selected, parent=self)
        if dlg.exec() == TaskDialog.Accepted:
            self.repo.add(dlg.task)
            self.tasks_changed.emit()
            self.refresh()

    def _edit_task(self, task: Task) -> None:
        dlg = TaskDialog(task, self._theme, parent=self)
        result = dlg.exec()
        if result == 2:      # 删除
            if task.id is not None:
                self.repo.delete(task.id)
            self.tasks_changed.emit()
            self.refresh()
        elif result == TaskDialog.Accepted:
            self.repo.update(dlg.task)
            self.tasks_changed.emit()
            self.refresh()

    def _delete_task(self, task: Task) -> None:
        if task.id is not None:
            self.repo.delete(task.id)
            self.tasks_changed.emit()
            self.refresh()
