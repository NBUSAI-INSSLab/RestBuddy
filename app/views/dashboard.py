"""今日总览页：问候、实时时钟、今日任务醒目提醒、休息节奏。"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ..database import Task
from ..icons import icon
from ..services.break_service import BreakService, BreakState
from ..theme import palette
from ..widgets.common import Card, StatCard
from ..widgets.task_card import TaskCard


class DashboardView(QWidget):
    """首页总览。"""

    tasks_changed = Signal()
    start_break_requested = Signal()
    snooze_requested = Signal()

    def __init__(self, repo, break_service: BreakService, conf,
                 theme: str = "light", parent=None) -> None:
        super().__init__(parent)
        self.repo = repo
        self.break_service = break_service
        self.conf = conf
        self._theme = theme
        self._build()

        self._clock = QTimer(self)
        self._clock.setInterval(1000)
        self._clock.timeout.connect(self._update_clock)
        self._clock.start()

        self.break_service.tick.connect(self._on_break_tick)
        self._update_clock()
        self.refresh()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        c = palette(self._theme)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(4, 4, 12, 12)
        root.setSpacing(16)

        # ---- 问候 + 时钟 ----
        greet = QFrame()
        greet.setObjectName("Card")
        gl = QHBoxLayout(greet)
        gl.setContentsMargins(22, 18, 22, 18)
        left = QVBoxLayout()
        left.setSpacing(4)
        self.lb_greet = QLabel("你好")
        self.lb_greet.setObjectName("H1")
        self.lb_date = QLabel("")
        self.lb_date.setObjectName("Muted")
        left.addWidget(self.lb_greet)
        left.addWidget(self.lb_date)
        left.addStretch(1)
        gl.addLayout(left, 1)

        self.lb_clock = QLabel("--:--:--")
        self.lb_clock.setObjectName("Clock")
        self.lb_clock.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        gl.addWidget(self.lb_clock)
        root.addWidget(greet)

        # ---- 指标卡 ----
        stats = QHBoxLayout()
        stats.setSpacing(14)
        self.card_tasks = StatCard("今日任务", "0/0", self._theme,
                                   self._icon_label("calendar"), "项")
        self.card_rate = StatCard("完成率", "0", self._theme,
                                  self._icon_label("target"), "%")
        self.card_break = StatCard("距下次休息", "--:--", self._theme,
                                   self._icon_label("coffee"))
        self.card_streak = StatCard("今日已休息", "0", self._theme,
                                    self._icon_label("leaf"), "次")
        for card in (self.card_tasks, self.card_rate,
                     self.card_break, self.card_streak):
            stats.addWidget(card, 1)
        root.addLayout(stats)

        # ---- 主体两栏 ----
        cols = QHBoxLayout()
        cols.setSpacing(16)

        # 左：今日任务
        self.task_card = Card("今日任务", self._theme, subtitle="")
        add_row = QHBoxLayout()
        self.ed_quick = QLineEdit()
        self.ed_quick.setPlaceholderText("快速添加今日任务，按回车确认…")
        self.ed_quick.returnPressed.connect(self._quick_add)
        btn_add = QPushButton("添加")
        btn_add.setObjectName("Primary")
        btn_add.clicked.connect(self._quick_add)
        add_row.addWidget(self.ed_quick, 1)
        add_row.addWidget(btn_add)
        self.task_card.add_layout(add_row)

        self.task_container = QWidget()
        self.task_list_layout = QVBoxLayout(self.task_container)
        self.task_list_layout.setContentsMargins(0, 0, 4, 0)
        self.task_list_layout.setSpacing(8)
        self.task_card.add(self.task_container)
        self.task_card.body.addStretch(1)
        cols.addWidget(self.task_card, 3)

        # 右：休息节奏
        right = QVBoxLayout()
        right.setSpacing(16)

        rest = Card("休息节奏", self._theme)
        self.pb_rest = QProgressBar()
        self.pb_rest.setRange(0, 100)
        self.pb_rest.setValue(0)
        self.pb_rest.setTextVisible(False)
        rest.add(self.pb_rest)
        self.lb_rest_state = QLabel("工作中 · 距离下次休息还有 --:--")
        self.lb_rest_state.setObjectName("Muted")
        rest.add(self.lb_rest_state)

        rb = QHBoxLayout()
        rb.setSpacing(10)
        self.btn_break_now = QPushButton("立即休息")
        self.btn_break_now.setObjectName("Primary")
        self.btn_break_now.clicked.connect(self.start_break_requested.emit)
        self.btn_snooze = QPushButton("推迟 5 分钟")
        self.btn_snooze.clicked.connect(self.snooze_requested.emit)
        rb.addWidget(self.btn_break_now, 1)
        rb.addWidget(self.btn_snooze, 1)
        rest.add_layout(rb)
        right.addWidget(rest)

        tip = Card("休息小贴士", self._theme)
        self.lb_tip = QLabel("")
        self.lb_tip.setWordWrap(True)
        self.lb_tip.setObjectName("Muted")
        tip.add(self.lb_tip)
        right.addWidget(tip)
        right.addStretch(1)

        col_right = QWidget()
        col_right.setLayout(right)
        col_right.setMinimumWidth(280)
        cols.addWidget(col_right, 2)
        root.addLayout(cols)
        root.addStretch(1)

        self._rotate_tip()

    def _icon_label(self, name: str) -> QLabel:
        c = palette(self._theme)
        lb = QLabel()
        lb.setPixmap(icon(name, c["primary"], 40).pixmap(22, 22))
        return lb

    # ------------------------------------------------------------------
    def _update_clock(self) -> None:
        now = dt.datetime.now()
        self.lb_clock.setText(now.strftime("%H:%M:%S"))
        hour = now.hour
        if hour < 6:
            greet = "夜深了"
        elif hour < 9:
            greet = "早上好"
        elif hour < 12:
            greet = "上午好"
        elif hour < 14:
            greet = "中午好"
        elif hour < 18:
            greet = "下午好"
        elif hour < 23:
            greet = "晚上好"
        else:
            greet = "夜深了"
        self.lb_greet.setText(f"{greet}，江老师")
        week = "一二三四五六日"[now.weekday()]
        self.lb_date.setText(
            f"{now.year} 年 {now.month} 月 {now.day} 日 · 星期{week}"
        )

    def _rotate_tip(self) -> None:
        tips = [
            "每工作 45 分钟休息 5 分钟，能让专注力保持在较高水平。",
            "休息时看向 6 米以外的远处，可以缓解视疲劳。",
            "喝水、起身走动，比继续硬撑更能提高效率。",
            "把大任务拆成 25 分钟的小块，更容易启动。",
            "睡前 1 小时远离屏幕，有助于提升睡眠质量。",
        ]
        import random
        self.lb_tip.setText(random.choice(tips))
        QTimer.singleShot(30000, self._rotate_tip)

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        today = dt.date.today().isoformat()
        tasks = self.repo.today(today)
        done = sum(1 for t in tasks if t.done)
        total = len(tasks)
        self.card_tasks.set_value(f"{done}/{total}", f"共 {total} 项，已完成 {done} 项")
        rate = int(done / total * 100) if total else 0
        self.card_rate.set_value(str(rate), "今日完成进度")
        self.task_card.header_set_subtitle = None
        self._rebuild_tasks(tasks)

    def _rebuild_tasks(self, tasks: list[Task]) -> None:
        # 清空
        while self.task_list_layout.count():
            item = self.task_list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not tasks:
            empty = QLabel("今天还没有任务，在上方输入框快速添加吧 🍃")
            empty.setObjectName("Muted")
            empty.setAlignment(Qt.AlignCenter)
            empty.setMinimumHeight(90)
            self.task_list_layout.addWidget(empty)
            return

        for t in tasks[:50]:
            card = TaskCard(t, self._theme, compact=True)
            card.toggled.connect(self._on_toggle)
            self.task_list_layout.addWidget(card)

    def _on_toggle(self, task_id: int) -> None:
        if task_id and task_id > 0:
            self.repo.toggle_done(task_id)
            self.tasks_changed.emit()
            self.refresh()

    def _quick_add(self) -> None:
        text = self.ed_quick.text().strip()
        if not text:
            return
        task = Task(title=text, date=dt.date.today().isoformat(), priority=1)
        self.repo.add(task)
        self.ed_quick.clear()
        self.tasks_changed.emit()
        self.refresh()

    # ------------------------------------------------------------------
    def _on_break_tick(self, remaining: int, state: str) -> None:
        self.lb_rest_state.setText(
            f"工作中 · 距离下次休息还有 {BreakService.format_hms(remaining)}"
            if state == BreakState.WORKING.value else
            (f"该休息了！" if state == BreakState.READY.value else
             f"休息中 · 还剩 {BreakService.format_hms(remaining)}"
             if state == BreakState.BREAKING.value else "休息功能已关闭")
        )
        if self.break_service.state == BreakState.BREAKING:
            self.pb_rest.setValue(self.break_service.progress_percent())
        else:
            self.pb_rest.setValue(self.break_service.progress_percent())
        self.card_break.set_value(BreakService.format_hms(remaining))

    def set_break_count(self, count: int) -> None:
        self.card_streak.set_value(str(count), "今日已完成休息")
