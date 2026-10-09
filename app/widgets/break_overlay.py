"""全屏休息覆盖层：休息时铺满屏幕，播放音乐并引导放松呼吸。"""
from __future__ import annotations

import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFont, QGuiApplication, QLinearGradient, QPainter, QPen,
)
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from ..icons import icon
from ..theme import palette

REST_TIPS = [
    "远眺 20 米外的地方，让睫状肌松弛下来",
    "站起来活动一下颈肩，慢慢转动脖子",
    "喝一杯温水，给身体补充水分",
    "闭上眼睛，深呼吸 5 次，让思绪放空",
    "揉搓双手至微热，轻敷在双眼上",
    "手腕顺时针、逆时针各转 10 圈",
    "把肩膀向上耸起到耳朵旁，保持 5 秒再放下",
    "看看窗外的绿植，让眼睛休息一会儿",
]


class CountdownRing(QWidget):
    """环形倒计时，中心显示剩余时间。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.progress = 1.0          # 1.0 → 0.0
        self.text = "--:--"
        self.subtitle = "休息中"
        self.color1 = QColor("#3ad3b1")
        self.color2 = QColor("#5b9cf0")

    def set_colors(self, color1: str, color2: str) -> None:
        self.color1 = QColor(color1)
        self.color2 = QColor(color2)
        self.update()

    def set_progress(self, value: float) -> None:
        self.progress = max(0.0, min(1.0, value))
        self.update()

    def set_text(self, text: str) -> None:
        self.text = text
        self.update()

    def set_subtitle(self, text: str) -> None:
        self.subtitle = text
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        side = min(w, h) - 24
        rect = QRectF((w - side) / 2, (h - side) / 2, side, side)

        # 轨道
        pen = QPen(QColor(255, 255, 255, 40))
        pen.setWidth(14)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)

        # 进度弧
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0, self.color1)
        grad.setColorAt(1, self.color2)
        pen = QPen(QBrush(grad), 14)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        span = int(-self.progress * 360 * 16)
        p.drawArc(rect, 90 * 16, span)

        # 中心文字
        p.setPen(QColor("#ffffff"))
        f = QFont("Microsoft YaHei UI", 40, QFont.Bold)
        p.setFont(f)
        p.drawText(rect, Qt.AlignCenter, self.text)

        p.setPen(QColor(255, 255, 255, 150))
        f2 = QFont("Microsoft YaHei UI", 12)
        p.setFont(f2)
        sub_rect = QRectF(rect.left(), rect.center().y() + 44,
                          rect.width(), 30)
        p.drawText(sub_rect, Qt.AlignHCenter | Qt.AlignTop, self.subtitle)
        p.end()


class BreathingCircle(QWidget):
    """呼吸引导圆：4 秒吸气、4 秒呼气循环，配合文字提示。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self._phase = 0.0
        self.color1 = QColor(58, 211, 177, 120)
        self.color2 = QColor(91, 156, 240, 120)
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._step)
        self._timer.start()

    def set_colors(self, color1: str, color2: str) -> None:
        c1, c2 = QColor(color1), QColor(color2)
        c1.setAlpha(120)
        c2.setAlpha(120)
        self.color1, self.color2 = c1, c2
        self.update()

    def _step(self) -> None:
        self._phase += 0.033
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        # 8 秒一个循环
        t = (self._phase % 8.0) / 8.0
        scale = 0.72 + 0.28 * math.sin(t * 2 * math.pi - math.pi / 2) * 0.5 + 0.14

        base = min(w, h) * 0.32
        r = base * scale
        grad = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
        grad.setColorAt(0, self.color1)
        grad.setColorAt(1, self.color2)
        p.setBrush(QBrush(grad))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), r, r)

        inner = r * 0.55
        p.setBrush(QColor(255, 255, 255, 30))
        p.drawEllipse(QPointF(cx, cy), inner, inner)

        label = "吸 气" if t < 0.5 else "呼 气"
        p.setPen(QColor(255, 255, 255, 220))
        f = QFont("Microsoft YaHei UI", 20, QFont.DemiBold)
        p.setFont(f)
        p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, label)
        p.end()


class BreakOverlay(QWidget):
    """全屏休息界面。

    信号：
        finished(str)  - 休息结束，参数为原因（ok / skip）
        snooze_requested - 请求推迟
    """

    finished = Signal(str)
    snooze_requested = Signal()

    def __init__(self, music_player, theme: str = "dark", parent=None) -> None:
        super().__init__(parent)
        self.music = music_player
        self._theme = theme
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint | Qt.BypassWindowManagerHint)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowTitle("休息一下")
        self._strict = False
        self._remaining = 0
        self._total = 1
        self._muted = False
        self._build()
        self._apply_style()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 46, 60, 46)
        root.setSpacing(6)

        # 顶部
        top = QHBoxLayout()
        self.lb_hello = QLabel("休息一下，让眼睛和大脑都放松")
        self.lb_hello.setStyleSheet("color:rgba(255,255,255,0.92);font-size:20px;font-weight:700;")
        top.addWidget(self.lb_hello)
        top.addStretch(1)
        self.lb_round = QLabel("")
        self.lb_round.setStyleSheet("color:rgba(255,255,255,0.5);font-size:13px;")
        top.addWidget(self.lb_round)
        root.addLayout(top)

        self.lb_music = QLabel("")
        self.lb_music.setStyleSheet("color:rgba(255,255,255,0.45);font-size:12px;")
        root.addWidget(self.lb_music)

        # 中部
        mid = QHBoxLayout()
        mid.setSpacing(40)
        mid.addStretch(1)
        self.ring = CountdownRing()
        self.ring.setFixedSize(340, 340)
        mid.addWidget(self.ring)
        self.breath = BreathingCircle()
        self.breath.setFixedSize(240, 240)
        mid.addWidget(self.breath)
        mid.addStretch(1)
        root.addLayout(mid, 1)

        # 提示
        self.lb_tip = QLabel(random.choice(REST_TIPS))
        self.lb_tip.setAlignment(Qt.AlignCenter)
        self.lb_tip.setStyleSheet("color:rgba(255,255,255,0.72);font-size:15px;")
        root.addWidget(self.lb_tip)

        # 底部按钮
        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_mute = QPushButton("静音")
        self.btn_mute.setObjectName("OverlayBtn")
        self.btn_mute.clicked.connect(self._toggle_mute)
        self.btn_snooze = QPushButton("休息 5 分钟后再继续")
        self.btn_snooze.setObjectName("OverlayBtn")
        self.btn_snooze.clicked.connect(self._on_snooze)
        self.btn_end = QPushButton("结束休息")
        self.btn_end.setObjectName("OverlayBtnPrimary")
        self.btn_end.clicked.connect(lambda: self._finish("skip"))
        btns.addWidget(self.btn_mute)
        btns.addWidget(self.btn_snooze)
        btns.addWidget(self.btn_end)
        btns.addStretch(1)
        root.addLayout(btns)

    def _apply_style(self) -> None:
        """按当前配色方案刷新休息层配色。"""
        c = palette(self._theme)
        self.ring.set_colors(c["ov_accent1"], c["ov_accent2"])
        self.breath.set_colors(c["ov_accent1"], c["ov_accent2"])
        self.setStyleSheet(
            f"QPushButton#OverlayBtn{{background:rgba(255,255,255,0.10);"
            f"border:1px solid rgba(255,255,255,0.24);color:#ffffff;"
            f"border-radius:11px;padding:11px 26px;font-size:14px;}}"
            f"QPushButton#OverlayBtn:hover{{background:rgba(255,255,255,0.22);}}"
            f"QPushButton#OverlayBtnPrimary{{background:{c['ov_primary']};border:none;"
            f"color:{c['ov_primary_text']};border-radius:11px;padding:11px 30px;"
            f"font-size:14px;font-weight:700;}}"
            f"QPushButton#OverlayBtnPrimary:hover{{background:{c['ov_primary_hover']};}}"
        )
        self.update()

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self._apply_style()
        self.lb_hello.setStyleSheet("color:rgba(255,255,255,0.94);"
                                    "font-size:20px;font-weight:700;")
        self.lb_tip.setStyleSheet("color:rgba(255,255,255,0.74);font-size:15px;")

    # ------------------------------------------------------------------
    def paintEvent(self, _event) -> None:
        c = palette(self._theme)
        p = QPainter(self)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.0, QColor(c["ov_bg"]))
        grad.setColorAt(0.5, QColor(c["ov_bg2"]))
        grad.setColorAt(1.0, QColor(c["ov_bg3"]))
        p.fillRect(self.rect(), grad)
        # 柔光圆
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(c["ov_glow1"]))
        p.drawEllipse(QPointF(self.width() * 0.22, self.height() * 0.25), 260, 260)
        p.setBrush(QColor(c["ov_glow2"]))
        p.drawEllipse(QPointF(self.width() * 0.82, self.height() * 0.78), 300, 300)
        p.end()

    # ------------------------------------------------------------------
    def begin(self, duration_sec: int, strict: bool = False,
              round_no: int = 0) -> None:
        self._total = max(1, duration_sec)
        self._remaining = duration_sec
        self._strict = strict
        self.btn_snooze.setVisible(not strict)
        self.btn_end.setVisible(not strict)
        self.lb_round.setText(f"第 {round_no} 次休息" if round_no else "")
        self.lb_tip.setText(random.choice(REST_TIPS))
        self.ring.set_progress(1.0)
        self.ring.set_text(self._fmt(self._remaining))
        self.ring.set_subtitle("休息倒计时")

        # 铺满主屏
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.geometry())
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

        # 音乐
        self._muted = False
        self.btn_mute.setText("静音")
        if self.music is not None and getattr(self.music, "available", False):
            if self.music.playlist:
                self.music.play()
                self.lb_music.setText("♪ 正在播放休息音乐")
            else:
                self.lb_music.setText("未设置休息音乐，可在「定时休息」中添加")
        else:
            self.lb_music.setText("当前环境未启用音频播放")

    def update_countdown(self, remaining: int) -> None:
        self._remaining = remaining
        self.ring.set_text(self._fmt(remaining))
        self.ring.set_progress(remaining / self._total)

    @staticmethod
    def _fmt(sec: int) -> str:
        sec = max(0, int(sec))
        m, s = divmod(sec, 60)
        return f"{m:02d}:{s:02d}"

    # ------------------------------------------------------------------
    def _toggle_mute(self) -> None:
        self._muted = not self._muted
        if self.music is not None and getattr(self.music, "available", False):
            if self._muted:
                self.music.pause()
            else:
                self.music.resume()
        self.btn_mute.setText("取消静音" if self._muted else "静音")

    def _on_snooze(self) -> None:
        self.close_overlay()
        self.snooze_requested.emit()

    def _finish(self, reason: str) -> None:
        if self._strict and reason == "skip":
            return
        self.close_overlay()
        self.finished.emit(reason)

    def close_overlay(self) -> None:
        if self.music is not None and getattr(self.music, "available", False):
            self.music.stop()
        self.hide()

    def closeEvent(self, event) -> None:
        if self._strict:
            event.ignore()
            return
        super().closeEvent(event)
