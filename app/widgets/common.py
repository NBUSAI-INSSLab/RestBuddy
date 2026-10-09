"""通用 UI 组件：卡片容器、区块标题等。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ..theme import palette


class Card(QFrame):
    """带标题的圆角卡片容器。"""

    def __init__(self, title: str = "", theme: str = "light",
                 subtitle: str = "", parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        self.setObjectName("Card")
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(18, 16, 18, 16)
        self._root.setSpacing(12)

        if title:
            head = QHBoxLayout()
            head.setSpacing(8)
            lb = QLabel(title)
            lb.setObjectName("CardTitle")
            head.addWidget(lb)
            if subtitle:
                sub = QLabel(subtitle)
                sub.setObjectName("Muted")
                head.addWidget(sub)
            head.addStretch(1)
            self.header = head
            self._root.addLayout(head)
        else:
            self.header = None

        self.body = QVBoxLayout()
        self.body.setSpacing(10)
        self._root.addLayout(self.body)

    def add_header_widget(self, widget: QWidget) -> None:
        if self.header is not None:
            self.header.addWidget(widget)

    def add(self, widget: QWidget, stretch: int = 0) -> None:
        self.body.addWidget(widget, stretch)

    def add_layout(self, layout) -> None:
        self.body.addLayout(layout)


class StatCard(Card):
    """指标卡片：大数字 + 说明。"""

    def __init__(self, label: str, value: str, theme: str = "light",
                 icon_widget: QWidget | None = None, unit: str = "",
                 parent=None) -> None:
        super().__init__("", theme, parent=parent)
        self._theme = theme
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._root.setContentsMargins(16, 14, 16, 14)
        self._root.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(6)
        self.lb_label = QLabel(label)
        self.lb_label.setObjectName("Muted")
        top.addWidget(self.lb_label)
        top.addStretch(1)
        if icon_widget is not None:
            top.addWidget(icon_widget)
        self.body.addLayout(top)

        row = QHBoxLayout()
        row.setSpacing(4)
        self.lb_value = QLabel(value)
        self.lb_value.setObjectName("BigNumber")
        row.addWidget(self.lb_value)
        if unit:
            self.lb_unit = QLabel(unit)
            self.lb_unit.setObjectName("Muted")
            self.lb_unit.setAlignment(Qt.AlignBottom)
            row.addWidget(self.lb_unit)
        row.addStretch(1)
        self.body.addLayout(row)

        self.lb_sub = QLabel("")
        self.lb_sub.setObjectName("Muted")
        self.body.addWidget(self.lb_sub)

    def set_value(self, value: str, sub: str = "") -> None:
        self.lb_value.setText(value)
        if sub:
            self.lb_sub.setText(sub)


def divider(theme: str) -> QFrame:
    c = palette(theme)
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background:{c['border']};")
    return line


def section_title(text: str, theme: str = "light") -> QLabel:
    lb = QLabel(text)
    lb.setObjectName("H2")
    return lb
