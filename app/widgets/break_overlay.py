"""全屏休息覆盖层：休息时铺满屏幕，播放音乐、轮播图片内容并引导放松呼吸。

界面构成（自左向右、自上而下）：

    ┌ 品牌行 ──────────────────────────── 音乐状态 · 第 N 次休息 ┐
    ├ 细进度条 ────────────────────────────────────────────────┤
    │  ┌ 图片轮播卡（Ken Burns 推拉 + 交叉淡入淡出）┐ ┌ 倒计时卡 ┐│
    │  │  本地图片 / 内置放松内容卡 + 指示点        │ │ 倒计时环 ││
    │  │                                          │ │ 呼吸圆+贴士││
    │  └──────────────────────────────────────────┘ └──────────┘│
    ├ 结束前警示条（剩余 15 秒起出现，闪烁 + 跳动）──────────────┤
    └ 底部操作按钮 ────────────────────────────────────────────┘

进入警示状态时：倒计时环变为警示色并上下跳动，屏幕边缘出现呼吸式光边，
顶部弹出醒目警示条提示「准备回到工作」。
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetrics, QGuiApplication, QLinearGradient,
    QPainter, QPainterPath, QPen, QPixmap,
)
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from ..config import app_data_dir
from ..icons import icon
from ..theme import palette

# ---------------------------------------------------------------------
# 文案素材
# ---------------------------------------------------------------------
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

# 未放置图片时轮播的内置放松内容卡
CONTENT_CARDS: list[dict[str, str]] = [
    {
        "icon": "eye",
        "title": "20-20-20 护眼法则",
        "body": "每工作 20 分钟，抬头看 20 英尺（约 6 米）外的地方 20 秒，"
                "让长时间收缩的睫状肌重新松弛下来。",
    },
    {
        "icon": "wind",
        "title": "4-2-6 深呼吸",
        "body": "用鼻子吸气 4 秒，屏住 2 秒，再用嘴缓缓呼气 6 秒。"
                "重复 5 轮，心率会明显下降，人也跟着放松。",
    },
    {
        "icon": "leaf",
        "title": "颈肩舒展",
        "body": "坐直身体，双肩缓慢上提至耳侧保持 5 秒，再自然落下。"
                "重复 8 次，缓解伏案带来的僵硬与酸痛。",
    },
    {
        "icon": "coffee",
        "title": "补水提醒",
        "body": "喝一杯约 200 毫升的温水，小口慢饮。"
                "久坐时血液流动变慢，补水能帮助身体保持清醒。",
    },
    {
        "icon": "target",
        "title": "视线远近调节",
        "body": "把视线在「近处指尖—远处窗外」之间缓慢移动 10 次，"
                "可有效缓解眼干、眼涩与视疲劳。",
    },
    {
        "icon": "moon",
        "title": "放松节律",
        "body": "闭上眼睛 30 秒，把注意力放在呼吸的起伏上，"
                "让杂乱的思绪慢慢沉下去，为下一段工作留出余量。",
    },
]

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".tif", ".tiff"}
MAX_SLIDES = 200


def default_slides_dir() -> Path:
    """默认轮播图片目录：%APPDATA%/RestBuddy/slides（自动创建）。"""
    d = app_data_dir() / "slides"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return d


def scan_images(folder: str | Path) -> list[str]:
    """扫描目录下的图片文件（含一级子目录），按名称排序。"""
    p = Path(folder)
    if not p.is_dir():
        return []
    found: list[str] = []
    try:
        for f in sorted(p.rglob("*")):
            if len(found) >= MAX_SLIDES:
                break
            if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                found.append(str(f))
    except OSError:
        pass
    return found


# =====================================================================
# 基础组件
# =====================================================================
class GlassCard(QWidget):
    """休息层里的毛玻璃卡片容器（自绘圆角 + 描边，避免样式级联问题）。"""

    def __init__(self, radius: int = 22, parent=None) -> None:
        super().__init__(parent)
        self.radius = radius

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 16))
        p.drawRoundedRect(r, self.radius, self.radius)
        pen = QPen(QColor(255, 255, 255, 30))
        pen.setWidth(1)
        p.setBrush(Qt.NoBrush)
        p.setPen(pen)
        p.drawRoundedRect(r, self.radius, self.radius)
        p.end()


class ThinProgress(QWidget):
    """顶部细进度条，显示整段休息的时间进度。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(6)
        self.value = 1.0
        self.color1 = QColor("#3ad3b1")
        self.color2 = QColor("#5b9cf0")

    def set_colors(self, c1: str, c2: str) -> None:
        self.color1, self.color2 = QColor(c1), QColor(c2)
        self.update()

    def set_value(self, v: float) -> None:
        self.value = max(0.0, min(1.0, float(v)))
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect())
        rad = r.height() / 2
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 34))
        p.drawRoundedRect(r, rad, rad)
        if self.value <= 0:
            p.end()
            return
        fw = max(r.height(), r.width() * self.value)
        fill = QRectF(r.left(), r.top(), fw, r.height())
        grad = QLinearGradient(fill.topLeft(), fill.topRight())
        grad.setColorAt(0, self.color1)
        grad.setColorAt(1, self.color2)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(fill, rad, rad)
        p.end()


# =====================================================================
# 倒计时环
# =====================================================================
class CountdownRing(QWidget):
    """环形倒计时，中心显示剩余时间；警示状态下变警示色并上下跳动。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(260, 260)
        self.progress = 1.0          # 1.0 → 0.0
        self.text = "--:--"
        self.subtitle = "休息倒计时"
        self.color1 = QColor("#3ad3b1")
        self.color2 = QColor("#5b9cf0")
        self.warn_color = QColor("#ffb020")
        self.warning = False
        self._shake = QPointF(0.0, 0.0)
        self._scale = 1.0
        self._st = 0.0
        self._shake_timer = QTimer(self)
        self._shake_timer.setInterval(30)
        self._shake_timer.timeout.connect(self._step_shake)

    # ------------------------------------------------------------------
    def set_colors(self, color1: str, color2: str) -> None:
        self.color1, self.color2 = QColor(color1), QColor(color2)
        self.update()

    def set_warn_color(self, color: str) -> None:
        self.warn_color = QColor(color)
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

    # ------------------------------------------------------------------
    def set_warning(self, on: bool) -> None:
        """开关警示态：开启后环形变警示色并持续跳动。"""
        on = bool(on)
        if on == self.warning:
            return
        self.warning = on
        if on:
            self._st = 0.0
            self._shake_timer.start()
        else:
            self._shake_timer.stop()
            self._shake = QPointF(0.0, 0.0)
            self._scale = 1.0
        self.update()

    def _step_shake(self) -> None:
        self._st += 0.03
        # 左右轻晃 + 向上跳动 + 缩放脉冲，形成"跳动"观感
        dx = math.sin(self._st * 24) * 4.0
        dy = -abs(math.sin(self._st * 8.5)) * 9.0
        self._shake = QPointF(dx, dy)
        self._scale = 1.0 + 0.035 * abs(math.sin(self._st * 5.5))
        self.update()

    def stop_animation(self) -> None:
        self._shake_timer.stop()

    # ------------------------------------------------------------------
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        side = min(w, h) - 34
        rect = QRectF((w - side) / 2, (h - side) / 2, side, side)

        p.translate(self._shake)
        if abs(self._scale - 1.0) > 1e-4:
            p.translate(cx, cy)
            p.scale(self._scale, self._scale)
            p.translate(-cx, -cy)

        c1 = self.warn_color if self.warning else self.color1
        c2 = self.warn_color if self.warning else self.color2

        # 警示时背后加一圈柔光，强化"要注意了"的观感
        if self.warning:
            glow = QColor(c1)
            glow.setAlpha(48)
            p.setPen(Qt.NoPen)
            p.setBrush(glow)
            p.drawEllipse(rect.center(), rect.width() / 2 + 10,
                          rect.height() / 2 + 10)

        # 轨道
        pen = QPen(QColor(255, 255, 255, 40))
        pen.setWidth(14)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawArc(rect, 0, 360 * 16)

        # 进度弧
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        pen = QPen(QBrush(grad), 14)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 90 * 16, int(-self.progress * 360 * 16))

        # 中心文字
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Microsoft YaHei UI", 38, QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, self.text)

        p.setPen(QColor(255, 255, 255, 150))
        p.setFont(QFont("Microsoft YaHei UI", 11))
        sub_rect = QRectF(rect.left(), rect.center().y() + 40, rect.width(), 28)
        p.drawText(sub_rect, Qt.AlignHCenter | Qt.AlignTop, self.subtitle)
        p.end()


# =====================================================================
# 呼吸引导圆
# =====================================================================
class BreathingCircle(QWidget):
    """呼吸引导圆：8 秒一个「吸气—呼气」循环，尺寸自适应。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(88, 88)
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

    def set_active(self, on: bool) -> None:
        if on:
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()

    def _step(self) -> None:
        if not self.isVisible():
            return
        self._phase += 0.033
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        t = (self._phase % 8.0) / 8.0
        scale = 0.72 + 0.28 * math.sin(t * 2 * math.pi - math.pi / 2) * 0.5 + 0.14

        base = min(w, h) * 0.34
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

        if min(w, h) >= 96:      # 尺寸太小时省略文字，避免拥挤
            label = "吸 气" if t < 0.5 else "呼 气"
            p.setPen(QColor(255, 255, 255, 225))
            p.setFont(QFont("Microsoft YaHei UI",
                            max(11, int(min(w, h) * 0.115)), QFont.DemiBold))
            p.drawText(QRectF(0, 0, w, h), Qt.AlignCenter, label)
        p.end()


# =====================================================================
# 图片轮播
# =====================================================================
class MediaCarousel(QWidget):
    """休息页轮播：本地图片（Ken Burns 推拉 + 交叉淡入淡出）或内置放松内容卡。

    点击/空格可手动切换；无图片时自动改用内置内容卡，保证任何环境都有内容可看。
    """

    FADE_SEC = 0.9          # 交叉淡入淡出时长
    RADIUS = 16

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(320, 200)
        self.setCursor(Qt.PointingHandCursor)
        self._files: list[str] = []
        self._enabled = True
        self._index = 0
        self._elapsed = 0.0
        self._interval = 12.0
        self._fade = 1.0
        self._cache: dict[str, QPixmap | None] = {}
        self._accent1 = QColor("#3ad3b1")
        self._accent2 = QColor("#5b9cf0")
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._tick)

    # ------------------------------------------------------------------
    def set_colors(self, c1: str, c2: str) -> None:
        self._accent1, self._accent2 = QColor(c1), QColor(c2)
        self.update()

    def set_source(self, folder: str | Path, interval_sec: int = 12,
                   enabled: bool = True) -> None:
        """设置图片来源与轮播间隔。"""
        self._enabled = bool(enabled)
        self._files = scan_images(folder) if self._enabled else []
        self._interval = float(max(4, int(interval_sec or 12)))
        self._cache.clear()
        self._index = 0
        self._elapsed = 0.0
        self._fade = 1.0
        self.update()

    def set_active(self, on: bool) -> None:
        if on:
            if not self._timer.isActive():
                self._elapsed = 0.0
                self._timer.start()
        else:
            self._timer.stop()

    def next_slide(self) -> None:
        n = self._count()
        if n > 1:
            self._index = (self._index + 1) % n
        self._elapsed = 0.0
        self._fade = 1.0
        self.update()

    def using_images(self) -> bool:
        return bool(self._enabled and self._files)

    # ------------------------------------------------------------------
    def _count(self) -> int:
        return len(self._files) if self.using_images() else len(CONTENT_CARDS)

    def _tick(self) -> None:
        if not self.isVisible():
            return
        n = self._count()
        if n <= 1:
            self._fade = 1.0
            self.update()
            return
        self._elapsed += 0.04
        if self._elapsed >= self._interval:
            self._index = (self._index + 1) % n
            self._elapsed = 0.0
            self._fade = 1.0
        else:
            remain = self._interval - self._elapsed
            self._fade = 1.0 if remain >= self.FADE_SEC else max(
                0.0, remain / self.FADE_SEC)
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.next_slide()
        super().mousePressEvent(event)

    # ------------------------------------------------------------------
    def _pix(self, path: str):
        if path in self._cache:
            return self._cache[path]
        pm = QPixmap(path)
        if pm.isNull():
            self._cache[path] = None
            return None
        if max(pm.width(), pm.height()) > 1800:
            pm = pm.scaled(1800, 1800, Qt.KeepAspectRatio,
                           Qt.SmoothTransformation)
        if len(self._cache) > 10:
            self._cache.clear()
        self._cache[path] = pm
        return pm

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, self.RADIUS, self.RADIUS)
        p.setClipPath(path)

        n = self._count()
        cur = self._index % n if n else 0
        kb = min(1.0, self._elapsed / self._interval) if self._interval else 0.0

        if n and self._fade < 1.0 and n > 1:
            nxt = (cur + 1) % n
            self._paint_slide(p, r, nxt, 0.0)
            p.setOpacity(self._fade)
            self._paint_slide(p, r, cur, kb)
            p.setOpacity(1.0)
        elif n:
            self._paint_slide(p, r, cur, kb)

        p.setClipping(False)
        pen = QPen(QColor(255, 255, 255, 34))
        pen.setWidth(1)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(r, self.RADIUS, self.RADIUS)

        self._paint_badge(p, r)
        self._paint_dots(p, r)
        p.end()

    # ------------------------------------------------------------------
    def _paint_slide(self, p: QPainter, rect: QRectF, idx: int,
                     kb: float) -> None:
        if self.using_images():
            self._paint_image(p, rect, self._files[idx], kb)
        else:
            self._paint_card(p, rect, CONTENT_CARDS[idx], kb)

    def _paint_image(self, p: QPainter, rect: QRectF, path: str,
                     kb: float) -> None:
        pm = self._pix(path)
        p.fillRect(rect, QColor(10, 16, 22))
        if pm is not None and not pm.isNull():
            iw, ih = pm.width(), pm.height()
            zoom = 1.04 + 0.10 * kb                 # Ken Burns 缓慢推近
            base = max(rect.width() / iw, rect.height() / ih)
            w, h = iw * base * zoom, ih * base * zoom
            dx = (rect.width() - w) / 2 + math.sin(kb * math.pi) * 12
            dy = (rect.height() - h) / 2 + (1 - kb) * 12
            p.drawPixmap(
                QRectF(rect.left() + dx, rect.top() + dy, w, h),
                pm, QRectF(0, 0, iw, ih),
            )

        # 底部压暗，保证图注可读
        scrim = QLinearGradient(rect.left(), rect.bottom() - 96,
                                rect.left(), rect.bottom())
        scrim.setColorAt(0.0, QColor(0, 0, 0, 0))
        scrim.setColorAt(1.0, QColor(0, 0, 0, 165))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(scrim))
        p.drawRect(QRectF(rect.left(), rect.bottom() - 96, rect.width(), 96))

        caption = Path(path).stem
        caption = caption.replace("_", " ").replace("-", " ").strip()
        if caption:
            p.setPen(QColor(255, 255, 255, 232))
            p.setFont(QFont("Microsoft YaHei UI", 13, QFont.DemiBold))
            box = QRectF(rect.left() + 22, rect.bottom() - 58,
                         rect.width() - 104, 30)
            p.drawText(box, Qt.AlignLeft | Qt.AlignVCenter,
                       QFontMetrics(p.font()).elidedText(
                           caption, Qt.ElideRight, int(box.width())))

    def _paint_card(self, p: QPainter, rect: QRectF, card: dict,
                    kb: float) -> None:
        c1 = QColor(self._accent1).darker(430)
        c2 = QColor(self._accent2).darker(430)
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, c1)
        grad.setColorAt(1.0, c2)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRect(rect)

        # 柔光
        glow = QColor(self._accent1)
        glow.setAlpha(30)
        p.setBrush(glow)
        p.drawEllipse(QPointF(rect.left() + rect.width() * 0.82,
                              rect.top() + rect.height() * 0.16),
                      rect.width() * 0.30, rect.width() * 0.30)

        pad = 34.0
        box = 62.0
        max_w = rect.width() - pad * 2

        # 先量出正文实际高度，让整块内容在卡片内垂直居中
        title_font = QFont("Microsoft YaHei UI", 20, QFont.Bold)
        body_font = QFont("Microsoft YaHei UI", 13)
        tfm = QFontMetrics(title_font)
        bfm = QFontMetrics(body_font)
        title_h = tfm.height() + 4
        body_rect_m = bfm.boundingRect(
            QRect(0, 0, int(max_w), int(rect.height())),
            int(Qt.TextWordWrap), card["body"])
        body_h = max(52.0, body_rect_m.height() + 6)
        block_h = box + 26 + title_h + 12 + body_h
        y0 = max(pad, (rect.height() - block_h) / 2)
        ix, iy = rect.left() + pad, rect.top() + y0

        p.setBrush(QColor(255, 255, 255, 30))
        p.drawRoundedRect(QRectF(ix, iy, box, box), 18, 18)
        pm = icon(card["icon"], "#ffffff", 64).pixmap(34, 34)
        p.drawPixmap(int(ix + (box - 34) / 2), int(iy + (box - 34) / 2), pm)

        ty = iy + box + 26

        p.setPen(QColor(255, 255, 255, 244))
        p.setFont(title_font)
        p.drawText(QRectF(ix, ty, max_w, title_h),
                   Qt.AlignLeft | Qt.AlignVCenter, card["title"])

        p.setPen(QColor(255, 255, 255, 198))
        p.setFont(body_font)
        body_rect = QRectF(ix, ty + title_h + 12, max_w, body_h)
        p.drawText(body_rect,
                   int(Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap),
                   card["body"])

    def _paint_badge(self, p: QPainter, rect: QRectF) -> None:
        n = self._count()
        if n <= 1:
            return
        label = (f"图片 {self._index % n + 1}/{n}" if self.using_images()
                 else f"放松小贴士 {self._index % n + 1}/{n}")
        p.setFont(QFont("Microsoft YaHei UI", 11))
        tw = QFontMetrics(p.font()).horizontalAdvance(label) + 22
        box = QRectF(rect.right() - tw - 14, rect.top() + 14, tw, 26)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 92))
        p.drawRoundedRect(box, 13, 13)
        p.setPen(QColor(255, 255, 255, 226))
        p.drawText(box, Qt.AlignCenter, label)

    def _paint_dots(self, p: QPainter, rect: QRectF) -> None:
        n = self._count()
        if n <= 1:
            return
        y = rect.bottom() - 20
        if n > 12:                       # 太多时用文字表示，避免超出宽度
            p.setPen(QColor(255, 255, 255, 200))
            p.setFont(QFont("Microsoft YaHei UI", 11))
            p.drawText(QRectF(rect.left(), y - 8, rect.width(), 20),
                       Qt.AlignRight, f"{self._index % n + 1} / {n}")
            return
        d, gap = 7.0, 9.0
        total = n * d + (n - 1) * gap
        x = rect.center().x() - total / 2
        p.setPen(Qt.NoPen)
        for i in range(n):
            active = (i == self._index % n)
            if active:
                p.setBrush(QColor(255, 255, 255, 240))
                p.drawEllipse(QRectF(x, y, d, d))
            else:
                p.setBrush(QColor(255, 255, 255, 96))
                p.drawEllipse(QRectF(x + 1, y + 1, d - 2, d - 2))
            x += d + gap


# =====================================================================
# 结束前警示条
# =====================================================================
class WarningBanner(QWidget):
    """休息即将结束时的醒目提示条：呼吸式闪烁 + 上下跳动。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(76)
        self._t = 0.0
        self._remaining = 0
        self._color = QColor("#ffb020")
        self._text_color = QColor("#3a2400")
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._step)
        self.hide()

    def set_colors(self, warn: str, warn_text: str) -> None:
        self._color, self._text_color = QColor(warn), QColor(warn_text)
        self.update()

    def set_remaining(self, sec: int) -> None:
        if sec != self._remaining:
            self._remaining = max(0, int(sec))
            self.update()

    def start(self) -> None:
        self._t = 0.0
        self.show()
        if not self._timer.isActive():
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _step(self) -> None:
        if not self.isVisible():
            return
        self._t += 0.033
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setFont(QFont("Microsoft YaHei UI", 15, QFont.Bold))
        text = f"即将结束 · 还剩 {self._remaining} 秒，准备回到工作"
        fm = QFontMetrics(p.font())
        tw = fm.horizontalAdvance(text)
        ic = 24
        pill_w = min(self.width() - 8, tw + ic + 22 + 64)
        pill_h = 54.0
        x = (self.width() - pill_w) / 2

        k = abs(math.sin(self._t * 2.4))            # 0..1 呼吸
        dy = -abs(math.sin(self._t * 3.6)) * 5.0    # 上下跳动
        rect = QRectF(x, (self.height() - pill_h) / 2 + dy, pill_w, pill_h)

        # 外发光
        glow = QColor(self._color)
        glow.setAlpha(int(36 + 74 * k))
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawRoundedRect(rect.adjusted(-5, -5, 5, 5),
                          rect.height() / 2 + 5, rect.height() / 2 + 5)

        # 主体
        body = QColor(self._color)
        body.setAlpha(int(198 + 57 * k))
        pen = QPen(QColor(255, 255, 255, int(70 + 130 * k)))
        pen.setWidth(2)
        p.setBrush(body)
        p.setPen(pen)
        p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        # 图标 + 文字
        pm = icon("bell", self._text_color.name(), 48).pixmap(ic, ic)
        start = rect.center().x() - (ic + 10 + tw) / 2
        p.drawPixmap(int(start), int(rect.center().y() - ic / 2), pm)
        p.setPen(self._text_color)
        p.drawText(QRectF(start + ic + 10, rect.top(), tw + 4, rect.height()),
                   Qt.AlignVCenter | Qt.AlignLeft, text)
        p.end()


# =====================================================================
# 全屏休息面板
# =====================================================================
class BreakOverlay(QWidget):
    """全屏休息界面。

    信号：
        finished(str)    - 休息结束，参数为原因（ok / skip）
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
        self._warn_sec = 15
        self._warning = False
        self._glow = 0.0
        self._folder = ""
        self._glow_timer = QTimer(self)
        self._glow_timer.setInterval(33)
        self._glow_timer.timeout.connect(self._step_glow)
        self._build()
        self._apply_style()

    # ------------------------------------------------------------------
    # 构建界面
    # ------------------------------------------------------------------
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(46, 32, 46, 28)
        root.setSpacing(0)

        # ---- 品牌行 ----
        top = QHBoxLayout()
        top.setSpacing(10)
        self.lb_brand = QLabel("今日小憩 · 休息中")
        self.lb_brand.setObjectName("OvBrand")
        top.addWidget(self.lb_brand)
        dot = QLabel("·")
        dot.setObjectName("OvMuted")
        top.addWidget(dot)
        self.lb_music = QLabel("")
        self.lb_music.setObjectName("OvMuted")
        top.addWidget(self.lb_music)
        top.addStretch(1)
        self.lb_round = QLabel("")
        self.lb_round.setObjectName("OvMuted")
        top.addWidget(self.lb_round)
        root.addLayout(top)

        root.addSpacing(12)

        # ---- 细进度条 ----
        self.bar = ThinProgress()
        root.addWidget(self.bar)
        root.addSpacing(20)

        # ---- 主体：左轮播 / 右倒计时 ----
        main = QHBoxLayout()
        main.setSpacing(22)

        self.card_media = GlassCard(22)
        cl = QVBoxLayout(self.card_media)
        cl.setContentsMargins(12, 12, 12, 12)
        self.carousel = MediaCarousel()
        cl.addWidget(self.carousel)
        main.addWidget(self.card_media, 11)

        self.card_time = GlassCard(22)
        tl = QVBoxLayout(self.card_time)
        tl.setContentsMargins(22, 20, 22, 20)
        tl.setSpacing(14)
        self.ring = CountdownRing()
        self.ring.setFixedSize(300, 300)
        tl.addStretch(3)
        tl.addWidget(self.ring, 0, Qt.AlignHCenter)
        tl.addStretch(4)

        tip_row = QHBoxLayout()
        tip_row.setSpacing(14)
        self.breath = BreathingCircle()
        self.breath.setFixedSize(96, 96)
        tip_row.addWidget(self.breath, 0, Qt.AlignVCenter)
        self.lb_tip = QLabel(random.choice(REST_TIPS))
        self.lb_tip.setObjectName("OvTip")
        self.lb_tip.setWordWrap(True)
        self.lb_tip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        tip_row.addWidget(self.lb_tip, 1)
        tl.addLayout(tip_row)
        main.addWidget(self.card_time, 9)

        root.addLayout(main, 1)
        root.addSpacing(10)

        # ---- 警示条 ----
        self.banner = WarningBanner()
        root.addWidget(self.banner)
        root.addSpacing(6)

        # ---- 底部按钮 ----
        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_mute = QPushButton("静音")
        self.btn_mute.setObjectName("OverlayBtn")
        self.btn_mute.clicked.connect(self._toggle_mute)
        self.btn_next = QPushButton("换一张")
        self.btn_next.setObjectName("OverlayBtn")
        self.btn_next.clicked.connect(self.carousel.next_slide)
        self.btn_snooze = QPushButton("休息 5 分钟后再继续")
        self.btn_snooze.setObjectName("OverlayBtn")
        self.btn_snooze.clicked.connect(self._on_snooze)
        self.btn_end = QPushButton("结束休息")
        self.btn_end.setObjectName("OverlayBtnPrimary")
        self.btn_end.clicked.connect(lambda: self._finish("skip"))
        for b in (self.btn_mute, self.btn_next, self.btn_snooze, self.btn_end):
            btns.addWidget(b)
        btns.addStretch(1)
        root.addLayout(btns)

        self._style_labels()

    def _style_labels(self) -> None:
        self.lb_brand.setStyleSheet(
            "color:rgba(255,255,255,0.94);font-size:19px;font-weight:700;"
            "background:transparent;")
        for lb in (self.lb_music, self.lb_round):
            lb.setStyleSheet(
                "color:rgba(255,255,255,0.52);font-size:12px;"
                "background:transparent;")
        self.lb_tip.setStyleSheet(
            "color:rgba(255,255,255,0.76);font-size:14px;line-height:150%;"
            "background:transparent;")

    def _apply_style(self) -> None:
        """按当前配色方案刷新休息层配色。

        所有样式都直接设在具体控件上，避免父级样式表的 ID 选择器级联问题。
        """
        c = palette(self._theme)
        self.ring.set_colors(c["ov_accent1"], c["ov_accent2"])
        self.ring.set_warn_color(c["ov_warn"])
        self.breath.set_colors(c["ov_accent1"], c["ov_accent2"])
        self.carousel.set_colors(c["ov_accent1"], c["ov_accent2"])
        self.bar.set_colors(c["ov_accent1"], c["ov_accent2"])
        self.banner.set_colors(c["ov_warn"], c["ov_warn_text"])

        ghost = ("QPushButton{background:rgba(255,255,255,0.10);"
                 "border:1px solid rgba(255,255,255,0.24);color:#ffffff;"
                 "border-radius:11px;padding:11px 24px;font-size:14px;}"
                 "QPushButton:hover{background:rgba(255,255,255,0.22);}")
        primary = (f"QPushButton{{background:{c['ov_primary']};border:none;"
                   f"color:{c['ov_primary_text']};border-radius:11px;"
                   f"padding:11px 30px;font-size:14px;font-weight:700;}}"
                   f"QPushButton:hover{{background:{c['ov_primary_hover']};}}")
        for b in (self.btn_mute, self.btn_next, self.btn_snooze):
            b.setStyleSheet(ghost)
        self.btn_end.setStyleSheet(primary)

        self._style_labels()
        self.update()

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self._apply_style()

    def apply_settings(self, conf) -> None:
        """从配置读取轮播与警示相关设置。"""
        try:
            self._warn_sec = max(3, int(conf.get("break_warn_sec", 15) or 15))
        except (TypeError, ValueError):
            self._warn_sec = 15
        folder = conf.get("break_image_dir", "") or default_slides_dir()
        self._folder = str(folder)
        try:
            slide_sec = int(conf.get("break_slide_sec", 12) or 12)
        except (TypeError, ValueError):
            slide_sec = 12
        self.carousel.set_source(self._folder, slide_sec,
                                 bool(conf.get("break_carousel", True)))

    def slides_folder(self) -> str:
        """当前轮播图片来源目录。"""
        return self._folder or str(default_slides_dir())

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

        # 警示期：屏幕边缘呼吸式光边
        if self._warning:
            k = abs(math.sin(self._glow * 2.4))
            col = QColor(c["ov_warn"])
            col.setAlpha(int(70 + 120 * k))
            pen = QPen(col)
            pen.setWidth(10)
            pen.setJoinStyle(Qt.MiterJoin)
            p.setBrush(Qt.NoBrush)
            p.setPen(pen)
            p.drawRect(self.rect().adjusted(5, 5, -5, -5))
        p.end()

    def _step_glow(self) -> None:
        if not self.isVisible():
            return
        self._glow += 0.033
        self.update()

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
        self.bar.set_value(1.0)
        self._exit_warning()

        # 铺满主屏
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.geometry())
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

        # 动画与轮播
        self.carousel.set_active(True)
        self.breath.set_active(True)

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
        progress = remaining / self._total
        self.ring.set_progress(progress)
        self.bar.set_value(progress)

        if remaining <= self._warn_sec and remaining > 0:
            if not self._warning:
                self._enter_warning()
            self.banner.set_remaining(remaining)
        elif self._warning:
            self._exit_warning()

    @staticmethod
    def _fmt(sec: int) -> str:
        sec = max(0, int(sec))
        m, s = divmod(sec, 60)
        return f"{m:02d}:{s:02d}"

    # ------------------------------------------------------------------
    def _enter_warning(self) -> None:
        """进入结束前警示：环变色跳动 + 边缘光边 + 醒目警示条。"""
        self._warning = True
        self._glow = 0.0
        self.ring.set_warning(True)
        self.ring.set_subtitle("即将结束，准备回到工作")
        self.banner.start()
        if not self._glow_timer.isActive():
            self._glow_timer.start()
        self.update()

    def _exit_warning(self) -> None:
        if not self._warning:
            self.banner.stop()
            return
        self._warning = False
        self._glow_timer.stop()
        self.ring.set_warning(False)
        self.ring.set_subtitle("休息倒计时")
        self.banner.stop()
        self.update()

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
        self._exit_warning()
        self.carousel.set_active(False)
        self.breath.set_active(False)
        self.ring.stop_animation()
        self.hide()

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key in (Qt.Key_Space, Qt.Key_Right, Qt.Key_MediaNext):
            self.carousel.next_slide()
        elif key == Qt.Key_Escape:
            self._finish("skip")
        elif key == Qt.Key_M:
            self._toggle_mute()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        if self._strict:
            event.ignore()
            return
        super().closeEvent(event)
