"""任务新增 / 编辑对话框。"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit,
    QTimeEdit, QVBoxLayout,
)

from ..database import Task
from ..icons import icon
from ..theme import palette

CATEGORIES = ["默认", "会议", "教学", "实验", "科研", "作业", "答辩",
              "报告", "沟通", "健康", "生活"]
PRIORITIES = [(0, "低"), (1, "中"), (2, "高")]


class TaskDialog(QDialog):
    """任务编辑对话框，接受后可通过 :attr:`task` 取回结果。"""

    def __init__(self, task: Task | None = None, theme: str = "light",
                 default_date: dt.date | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("编辑任务" if task else "新建任务")
        self.setModal(True)
        self.setMinimumWidth(430)
        self._theme = theme
        self.task = task or Task()
        self._is_new = task is None

        self._build_ui()
        self._load()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(14)

        title = QLabel("编辑任务" if not self._is_new else "新建任务")
        title.setObjectName("H2")
        root.addWidget(title)

        form = QFormLayout()
        form.setSpacing(11)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.ed_title = QLineEdit()
        self.ed_title.setPlaceholderText("要做什么？例如：批改操作系统实验报告")
        form.addRow("任务标题", self.ed_title)

        date_row = QHBoxLayout()
        self.ed_date = QDateEdit()
        self.ed_date.setCalendarPopup(True)
        self.ed_date.setDisplayFormat("yyyy-MM-dd")
        date_row.addWidget(self.ed_date, 1)
        date_row.addWidget(QLabel("时间"))
        self.cb_has_time = QCheckBox("指定")
        self.ed_time = QTimeEdit()
        self.ed_time.setDisplayFormat("HH:mm")
        self.ed_time.setEnabled(False)
        self.cb_has_time.toggled.connect(self.ed_time.setEnabled)
        date_row.addWidget(self.cb_has_time)
        date_row.addWidget(self.ed_time)
        form.addRow("日期", self._wrap(date_row))

        prio_row = QHBoxLayout()
        self.cb_priority = QComboBox()
        for val, label in PRIORITIES:
            self.cb_priority.addItem(f"{label}优先级", val)
        self.ed_category = QComboBox()
        self.ed_category.setEditable(True)
        self.ed_category.addItems(CATEGORIES)
        prio_row.addWidget(self.cb_priority, 1)
        prio_row.addWidget(self.ed_category, 1)
        form.addRow("优先级 / 类别", self._wrap(prio_row))

        self.sp_remind = QSpinBox()
        self.sp_remind.setRange(-1, 1440)
        self.sp_remind.setSuffix(" 分钟")
        self.sp_remind.setSpecialValueText("不提醒")
        form.addRow("提前提醒", self.sp_remind)

        self.ed_notes = QTextEdit()
        self.ed_notes.setPlaceholderText("补充说明（可选）")
        self.ed_notes.setFixedHeight(72)
        form.addRow("备注", self.ed_notes)

        root.addLayout(form)

        btns = QHBoxLayout()
        if not self._is_new:
            self.btn_delete = QPushButton("删除")
            self.btn_delete.setObjectName("Danger")
            self.btn_delete.setIcon(icon("trash", palette(self._theme)["danger"], 32))
            self.btn_delete.clicked.connect(self._on_delete)
            btns.addWidget(self.btn_delete)
        btns.addStretch(1)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok = QPushButton("保存")
        self.btn_ok.setObjectName("Primary")
        self.btn_ok.clicked.connect(self._on_accept)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)
        root.addLayout(btns)

        self._deleted = False

    @staticmethod
    def _wrap(layout) -> QFrame:
        f = QFrame()
        layout.setContentsMargins(0, 0, 0, 0)
        f.setLayout(layout)
        return f

    # ------------------------------------------------------------------
    def _load(self) -> None:
        t = self.task
        self.ed_title.setText(t.title)
        if t.date:
            d = QDate.fromString(t.date, "yyyy-MM-dd")
            self.ed_date.setDate(d if d.isValid() else QDate.currentDate())
        else:
            self.ed_date.setDate(QDate.currentDate())
        if t.time:
            self.cb_has_time.setChecked(True)
            tm = QTime.fromString(t.time, "HH:mm")
            if tm.isValid():
                self.ed_time.setTime(tm)
        else:
            self.ed_time.setTime(QTime(9, 0))
        idx = self.cb_priority.findData(t.priority)
        self.cb_priority.setCurrentIndex(max(0, idx))
        self.ed_category.setCurrentText(t.category or "默认")
        self.sp_remind.setValue(t.remind_min if t.remind_min is not None else 0)
        self.ed_notes.setPlainText(t.notes)

    def _on_accept(self) -> None:
        title = self.ed_title.text().strip()
        if not title:
            self.ed_title.setFocus()
            self.ed_title.setPlaceholderText("请填写任务标题")
            return
        self.task.title = title
        self.task.date = self.ed_date.date().toString("yyyy-MM-dd")
        self.task.time = (self.ed_time.time().toString("HH:mm")
                          if self.cb_has_time.isChecked() else "")
        self.task.priority = self.cb_priority.currentData()
        self.task.category = self.ed_category.currentText().strip() or "默认"
        self.task.remind_min = self.sp_remind.value()
        self.task.notes = self.ed_notes.toPlainText().strip()
        self.accept()

    def _on_delete(self) -> None:
        self._deleted = True
        self.done(2)  # 自定义结果码：删除
