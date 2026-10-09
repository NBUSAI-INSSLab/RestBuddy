"""内置矢量图标（无需外部图片资源）。

所有图标以 24x24 viewBox 的 SVG path 描述，运行时按需着色并渲染为 QIcon。
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# 线条型图标：stroke 填充
_ICONS: dict[str, str] = {
    "dashboard": (
        '<rect x="3" y="3" width="7.5" height="9.5" rx="1.6"/>'
        '<rect x="13.5" y="3" width="7.5" height="5.5" rx="1.6"/>'
        '<rect x="13.5" y="11.5" width="7.5" height="9.5" rx="1.6"/>'
        '<rect x="3" y="15.5" width="7.5" height="5.5" rx="1.6"/>'
    ),
    "calendar": (
        '<rect x="3" y="4.5" width="18" height="16.5" rx="2.2"/>'
        '<line x1="3" y1="9.5" x2="21" y2="9.5"/>'
        '<line x1="8" y1="2.5" x2="8" y2="6.5"/>'
        '<line x1="16" y1="2.5" x2="16" y2="6.5"/>'
        '<circle cx="8" cy="14" r="1"/>'
        '<circle cx="12" cy="14" r="1"/>'
        '<circle cx="16" cy="14" r="1"/>'
        '<circle cx="8" cy="17.6" r="1"/>'
        '<circle cx="12" cy="17.6" r="1"/>'
    ),
    "break": (
        '<path d="M4 8.5h12.5v4.5a5 5 0 0 1-5 5h-2.5a5 5 0 0 1-5-5z"/>'
        '<path d="M16.5 9.5h1.6a2.7 2.7 0 0 1 0 5.4h-1.6"/>'
        '<line x1="7" y1="3" x2="7" y2="5.5"/>'
        '<line x1="10.5" y1="2.5" x2="10.5" y2="5.5"/>'
    ),
    "game": (
        '<rect x="2.5" y="7" width="19" height="11" rx="4"/>'
        '<line x1="7.5" y1="10.5" x2="7.5" y2="14.5"/>'
        '<line x1="5.5" y1="12.5" x2="9.5" y2="12.5"/>'
        '<circle cx="15.5" cy="11" r="1.1"/>'
        '<circle cx="18" cy="13.8" r="1.1"/>'
    ),
    "ai": (
        '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>'
        '<path d="M18.5 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z"/>'
    ),
    "settings": (
        '<circle cx="12" cy="12" r="3.2"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'
    ),
    "clock": (
        '<circle cx="12" cy="12" r="8.5"/>'
        '<polyline points="12 7 12 12 15.5 14"/>'
    ),
    "plus": (
        '<line x1="12" y1="5" x2="12" y2="19"/>'
        '<line x1="5" y1="12" x2="19" y2="12"/>'
    ),
    "check": '<polyline points="4.5 12.5 9.5 17.5 19.5 6.5"/>',
    "trash": (
        '<polyline points="3.5 6.5 20.5 6.5"/>'
        '<path d="M6 6.5l1 13a1.5 1.5 0 0 0 1.5 1.4h7a1.5 1.5 0 0 0 1.5-1.4l1-13"/>'
        '<path d="M9 6.5V4.5a1.5 1.5 0 0 1 1.5-1.5h3a1.5 1.5 0 0 1 1.5 1.5v2"/>'
    ),
    "edit": (
        '<path d="M4 20h4L18.5 9.5a2.1 2.1 0 0 0-3-3L5 17z"/>'
        '<line x1="14.5" y1="6.5" x2="17.5" y2="9.5"/>'
    ),
    "play": '<polygon points="7 4.5 19 12 7 19.5" fill="{color}" stroke="none"/>',
    "pause": (
        '<rect x="6.5" y="5" width="3.6" height="14" rx="1.2" fill="{color}" stroke="none"/>'
        '<rect x="13.9" y="5" width="3.6" height="14" rx="1.2" fill="{color}" stroke="none"/>'
    ),
    "skip": (
        '<polygon points="5 5 14 12 5 19" fill="{color}" stroke="none"/>'
        '<rect x="15.5" y="5" width="3" height="14" rx="1" fill="{color}" stroke="none"/>'
    ),
    "music": (
        '<path d="M8 18V5l10-2v13"/>'
        '<circle cx="5.5" cy="18" r="2.6"/>'
        '<circle cx="15.5" cy="16" r="2.6"/>'
    ),
    "sun": (
        '<circle cx="12" cy="12" r="4.2"/>'
        '<line x1="12" y1="1.5" x2="12" y2="4"/>'
        '<line x1="12" y1="20" x2="12" y2="22.5"/>'
        '<line x1="1.5" y1="12" x2="4" y2="12"/>'
        '<line x1="20" y1="12" x2="22.5" y2="12"/>'
        '<line x1="4.6" y1="4.6" x2="6.4" y2="6.4"/>'
        '<line x1="17.6" y1="17.6" x2="19.4" y2="19.4"/>'
        '<line x1="4.6" y1="19.4" x2="6.4" y2="17.6"/>'
        '<line x1="17.6" y1="6.4" x2="19.4" y2="4.6"/>'
    ),
    "moon": '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/>',
    "palette": (
        '<path d="M12 3.2a8.8 8.8 0 1 0 0 17.6c1.6 0 2.3-1.1 1.5-2.1'
        '-.8-1.1.1-2.3 1.4-2.3h2.4a3.9 3.9 0 0 0 3.9-4c0-4.9-4-9.2-9.2-9.2z"/>'
        '<circle cx="7.6" cy="10.8" r="1.1"/>'
        '<circle cx="10.4" cy="7.1" r="1.1"/>'
        '<circle cx="14.6" cy="7.6" r="1.1"/>'
        '<circle cx="17" cy="11.2" r="1.1"/>'
    ),
    "bell": (
        '<path d="M18 8a6 6 0 0 0-12 0c0 6-2.5 7.5-2.5 7.5h17S18 14 18 8z"/>'
        '<path d="M10.3 20a2 2 0 0 0 3.4 0"/>'
    ),
    "close": (
        '<line x1="5.5" y1="5.5" x2="18.5" y2="18.5"/>'
        '<line x1="18.5" y1="5.5" x2="5.5" y2="18.5"/>'
    ),
    "min": '<line x1="5" y1="12" x2="19" y2="12"/>',
    "max": '<rect x="5" y="5" width="14" height="14" rx="2"/>',
    "restore": (
        '<rect x="4" y="8" width="12" height="12" rx="2"/>'
        '<polyline points="8 8 8 4 20 4 20 16 16 16"/>'
    ),
    "leaf": (
        '<path d="M20 4C10 4 4 9 4 16a4 4 0 0 0 4 4c7 0 12-6 12-16z"/>'
        '<path d="M4 20C8 14 12 10 17 7"/>'
    ),
    "target": (
        '<circle cx="12" cy="12" r="8.5"/>'
        '<circle cx="12" cy="12" r="4.6"/>'
        '<circle cx="12" cy="12" r="1" fill="{color}" stroke="none"/>'
    ),
    "wind": (
        '<path d="M3 8h11a3 3 0 1 0-3-3"/>'
        '<path d="M3 12h15a3 3 0 1 1-3 3"/>'
        '<line x1="3" y1="16" x2="10" y2="16"/>'
    ),
    "sync": (
        '<path d="M20 11a8 8 0 0 0-14-4L4 9"/>'
        '<path d="M4 5v4h4"/>'
        '<path d="M4 13a8 8 0 0 0 14 4l2-2"/>'
        '<path d="M20 19v-4h-4"/>'
    ),
    "export": (
        '<path d="M12 3v12"/>'
        '<polyline points="7.5 10.5 12 15 16.5 10.5"/>'
        '<path d="M4 17v2.5A1.5 1.5 0 0 0 5.5 21h13a1.5 1.5 0 0 0 1.5-1.5V17"/>'
    ),
    "chevron-right": '<polyline points="9.5 6 15.5 12 9.5 18"/>',
    "chevron-left": '<polyline points="14.5 6 8.5 12 14.5 18"/>',
    "coffee": (
        '<path d="M5 8h11v6a5 5 0 0 1-5 5H10a5 5 0 0 1-5-5z"/>'
        '<path d="M16 9h1.5a2.5 2.5 0 0 1 0 5H16"/>'
        '<line x1="8" y1="2.5" x2="8" y2="5.5"/>'
        '<line x1="12" y1="2.5" x2="12" y2="5.5"/>'
    ),
    "eye": (
        '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/>'
        '<circle cx="12" cy="12" r="3"/>'
    ),
    "brain": (
        '<path d="M12 4.5a3 3 0 0 0-3 3v9a3 3 0 0 0 3 3 3 3 0 0 0 3-3v-9a3 3 0 0 0-3-3z"/>'
        '<path d="M9 8H7.5a2.5 2.5 0 1 0 0 5H9"/>'
        '<path d="M15 11h1.5a2.5 2.5 0 1 0 0-5H15"/>'
        '<path d="M9 16h1.5"/>'
        '<path d="M15 16h-1.5"/>'
    ),
}

_HEADER = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'fill="none" stroke="{color}" stroke-width="{width}" '
    'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
)


def svg_for(name: str, color: str = "#333333", width: float = 1.9) -> str:
    body = _ICONS.get(name, _ICONS["target"]).replace("{color}", color)
    return _HEADER.format(color=color, width=width, body=body)


def make_icon(name: str, color: str = "#333333", size: int = 40,
              width: float = 1.9) -> QIcon:
    """生成带颜色的 QIcon。"""
    svg = svg_for(name, color=color, width=width)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)


_icon_cache: dict[tuple, QIcon] = {}


def icon(name: str, color: str = "#333333", size: int = 40) -> QIcon:
    key = (name, color, size)
    if key not in _icon_cache:
        _icon_cache[key] = make_icon(name, color, size)
    return _icon_cache[key]


def pixmap(name: str, color: str = "#333333", size: int = 40) -> QPixmap:
    return icon(name, color, size).pixmap(size, size)
