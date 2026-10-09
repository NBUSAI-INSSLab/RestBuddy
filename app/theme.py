"""主题系统：多套配色方案与全局 QSS 样式表。

每个方案（scheme）都是一份完整的颜色令牌表，涵盖窗口底色、卡片、侧边栏、
文字、强调色以及全屏休息层的配色。所有方案都显式给出叠加在主色之上的
文字颜色（``primary_text``）与侧边栏文字色，确保任何配色下文字都清晰可读。
"""
from __future__ import annotations

# =====================================================================
# 配色令牌
# =====================================================================
# 通用令牌说明：
#   bg / surface / surface_alt / border ...  界面层次
#   text / text_muted                        正文与次要文字
#   primary / primary_hover / primary_soft   主强调色
#   primary_text                             叠加在 primary 之上的文字颜色
#   accent                                   辅助强调色（卡片标题竖条等）
#   sidebar*                                 侧边栏专用（支持深色侧边栏）
#   ov_*                                     全屏休息层专用
# =====================================================================

# ---- 薄荷绿 · 浅色 ---------------------------------------------------
LIGHT = {
    "dark": False,
    "bg": "#eef2f6",
    "surface": "#ffffff",
    "surface_alt": "#f6f8fb",
    "sidebar": "#ffffff",
    "sidebar_border": "#e2e8f0",
    "sidebar_text": "#1e2a38",
    "sidebar_muted": "#5b6b82",
    "sidebar_hover": "#f1f5f9",
    "sidebar_active_bg": "#e2f5f0",
    "sidebar_active_text": "#116b58",
    "sidebar_card_bg": "#f6f8fb",
    "sidebar_card_border": "#e2e8f0",
    "border": "#e2e8f0",
    "border_strong": "#cbd5e1",
    "text": "#1e2a38",
    "text_muted": "#5b6b82",
    "primary": "#17836d",
    "primary_hover": "#116b58",
    "primary_soft": "#e2f5f0",
    "primary_text": "#ffffff",
    "accent": "#17836d",
    "danger": "#c0392b",
    "warning": "#b8760b",
    "success": "#1f7a44",
    "shadow": "rgba(24, 46, 74, 0.10)",
    "overlay": "rgba(14, 26, 40, 0.92)",
    "hover": "#f1f5f9",
    "ov_bg": "#0f1a22",
    "ov_bg2": "#12202b",
    "ov_bg3": "#0c1620",
    "ov_accent1": "#3ad3b1",
    "ov_accent2": "#5b9cf0",
    "ov_glow1": "#1a2fc3a2",
    "ov_glow2": "#185b9cf0",
    "ov_primary": "#2fc3a2",
    "ov_primary_hover": "#3ad3b1",
    "ov_primary_text": "#04302a",
}

# ---- 薄荷绿 · 深色 ---------------------------------------------------
DARK = {
    "dark": True,
    "bg": "#14181d",
    "surface": "#1d232a",
    "surface_alt": "#232b34",
    "sidebar": "#1a2027",
    "sidebar_border": "#2c353f",
    "sidebar_text": "#e7edf3",
    "sidebar_muted": "#8a97a6",
    "sidebar_hover": "#252d36",
    "sidebar_active_bg": "#173a34",
    "sidebar_active_text": "#3ad3b1",
    "sidebar_card_bg": "#232b34",
    "sidebar_card_border": "#2c353f",
    "border": "#2c353f",
    "border_strong": "#3a4551",
    "text": "#e7edf3",
    "text_muted": "#98a5b4",
    "primary": "#2fc3a2",
    "primary_hover": "#3ad3b1",
    "primary_soft": "#173a34",
    "primary_text": "#04302a",
    "accent": "#2fc3a2",
    "danger": "#ef7b66",
    "warning": "#e6b265",
    "success": "#3ecf8e",
    "shadow": "rgba(0, 0, 0, 0.45)",
    "overlay": "rgba(8, 12, 16, 0.94)",
    "hover": "#252d36",
    "ov_bg": "#0f1a22",
    "ov_bg2": "#12202b",
    "ov_bg3": "#0c1620",
    "ov_accent1": "#3ad3b1",
    "ov_accent2": "#5b9cf0",
    "ov_glow1": "#1a2fc3a2",
    "ov_glow2": "#185b9cf0",
    "ov_primary": "#2fc3a2",
    "ov_primary_hover": "#3ad3b1",
    "ov_primary_text": "#04302a",
}

# ---- 橙色 · 暖阳 -----------------------------------------------------
ORANGE = {
    "dark": False,
    "bg": "#fdf4ec",
    "surface": "#ffffff",
    "surface_alt": "#fdf0e4",
    "sidebar": "#ffffff",
    "sidebar_border": "#f1dcc7",
    "sidebar_text": "#3b2a1d",
    "sidebar_muted": "#8a6b52",
    "sidebar_hover": "#fbeee1",
    "sidebar_active_bg": "#ffe7d2",
    "sidebar_active_text": "#a03605",
    "sidebar_card_bg": "#fdf0e4",
    "sidebar_card_border": "#f1dcc7",
    "border": "#f2e0cf",
    "border_strong": "#e3c4a6",
    "text": "#3b2a1d",
    "text_muted": "#8a6b52",
    "primary": "#c9490a",
    "primary_hover": "#a03605",
    "primary_soft": "#ffe7d2",
    "primary_text": "#ffffff",
    "accent": "#c9490a",
    "danger": "#c62f22",
    "warning": "#b8760b",
    "success": "#1f7a44",
    "shadow": "rgba(122, 62, 12, 0.14)",
    "overlay": "rgba(48, 24, 8, 0.93)",
    "hover": "#fbeee1",
    "ov_bg": "#241407",
    "ov_bg2": "#2d1a0a",
    "ov_bg3": "#1d1005",
    "ov_accent1": "#ff9f45",
    "ov_accent2": "#f2c14e",
    "ov_glow1": "#22ea5a0c",
    "ov_glow2": "#1ef59e0b",
    "ov_primary": "#ff9147",
    "ov_primary_hover": "#ffa96a",
    "ov_primary_text": "#331500",
}

# ---- 橙蓝 · 活力（深蓝侧边栏 + 橙色主色） ----------------------------
ORANGEBLUE = {
    "dark": False,
    "bg": "#f1f5fb",
    "surface": "#ffffff",
    "surface_alt": "#eef3fb",
    "sidebar": "#123a72",
    "sidebar_border": "#0e2f5e",
    "sidebar_text": "#ffffff",
    "sidebar_muted": "#a9c2e4",
    "sidebar_hover": "rgba(255, 255, 255, 0.14)",
    "sidebar_active_bg": "rgba(255, 255, 255, 0.20)",
    "sidebar_active_text": "#ffb87a",
    "sidebar_card_bg": "rgba(255, 255, 255, 0.12)",
    "sidebar_card_border": "rgba(255, 255, 255, 0.20)",
    "border": "#dbe4f2",
    "border_strong": "#bccee6",
    "text": "#17263f",
    "text_muted": "#5f7391",
    "primary": "#c9490a",
    "primary_hover": "#a03605",
    "primary_soft": "#ffe7d2",
    "primary_text": "#ffffff",
    "accent": "#1d4ed8",
    "danger": "#cf2f2f",
    "warning": "#b8730a",
    "success": "#12784a",
    "shadow": "rgba(20, 48, 96, 0.16)",
    "overlay": "rgba(9, 24, 48, 0.93)",
    "hover": "#e7eefb",
    "ov_bg": "#08182e",
    "ov_bg2": "#0c2240",
    "ov_bg3": "#061223",
    "ov_accent1": "#ff9f45",
    "ov_accent2": "#5b9cf0",
    "ov_glow1": "#22e2560a",
    "ov_glow2": "#1e3b82f6",
    "ov_primary": "#ff9147",
    "ov_primary_hover": "#ffa96a",
    "ov_primary_text": "#331500",
}

# ---- 黑灰 · 极简 -----------------------------------------------------
GRAY = {
    "dark": True,
    "bg": "#141517",
    "surface": "#1c1e21",
    "surface_alt": "#24272b",
    "sidebar": "#17191c",
    "sidebar_border": "#2c3035",
    "sidebar_text": "#eceef1",
    "sidebar_muted": "#a2a9b2",
    "sidebar_hover": "#272a2e",
    "sidebar_active_bg": "#33373c",
    "sidebar_active_text": "#ffffff",
    "sidebar_card_bg": "#24272b",
    "sidebar_card_border": "#2c3035",
    "border": "#2c3035",
    "border_strong": "#3d4249",
    "text": "#eceef1",
    "text_muted": "#a4abb4",
    "primary": "#e4e8ec",
    "primary_hover": "#cdd4da",
    "primary_soft": "#33373c",
    "primary_text": "#16181b",
    "accent": "#98a2ae",
    "danger": "#f0736b",
    "warning": "#e3b45f",
    "success": "#5fd39a",
    "shadow": "rgba(0, 0, 0, 0.55)",
    "overlay": "rgba(6, 7, 8, 0.94)",
    "hover": "#272a2e",
    "ov_bg": "#0e0f11",
    "ov_bg2": "#17191c",
    "ov_bg3": "#0b0c0d",
    "ov_accent1": "#e4e8ec",
    "ov_accent2": "#98a2ae",
    "ov_glow1": "#16e4e8ec",
    "ov_glow2": "#1498a2ae",
    "ov_primary": "#e4e8ec",
    "ov_primary_hover": "#f2f5f8",
    "ov_primary_text": "#16181b",
}

SCHEMES: dict[str, dict] = {
    "light": LIGHT,
    "dark": DARK,
    "orange": ORANGE,
    "orangeblue": ORANGEBLUE,
    "gray": GRAY,
}

# 供界面下拉框使用的顺序与名称
SCHEME_LABELS: list[tuple[str, str]] = [
    ("light", "薄荷绿 · 浅色"),
    ("dark", "薄荷绿 · 深色"),
    ("orange", "橙色 · 暖阳"),
    ("orangeblue", "橙蓝 · 活力"),
    ("gray", "黑灰 · 极简"),
]

DEFAULT_SCHEME = "light"


# =====================================================================
# 工具函数
# =====================================================================
def palette(theme: str) -> dict:
    """返回指定方案的完整令牌表，未知方案回退到浅色。"""
    return SCHEMES.get(theme or "", LIGHT)


def is_dark(theme: str) -> bool:
    """该方案是否为深色底。"""
    return bool(palette(theme).get("dark"))


def scheme_label(theme: str) -> str:
    for key, label in SCHEME_LABELS:
        if key == theme:
            return label
    return SCHEME_LABELS[0][1]


def _luminance(color: str) -> float:
    """计算颜色的相对亮度（0-1），支持 #rgb / #rrggbb。"""
    hexs = color.strip().lstrip("#")
    if len(hexs) == 3:
        hexs = "".join(ch * 2 for ch in hexs)
    if len(hexs) != 6:
        return 1.0
    try:
        r, g, b = (int(hexs[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return 1.0

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG 对比度，1.0 - 21.0。"""
    l1, l2 = _luminance(fg), _luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def readable_text(bg: str, prefer_light: bool = True) -> str:
    """在给定底色上挑选可读的文字颜色（自动选对比度更高的一个）。"""
    light, dark = "#ffffff", "#16181b"
    if contrast_ratio(light, bg) >= contrast_ratio(dark, bg):
        return light
    return dark


def sample_colors(theme: str) -> list[tuple[str, str, str]]:
    """返回用于界面预览的色卡（底色, 文字色, 说明）。"""
    c = palette(theme)
    return [
        (c["primary"], readable_text(c["primary"]), "主色"),
        (c["accent"], readable_text(c["accent"]), "辅色"),
        (c["surface_alt"], c["text"], "正文"),
        (c["bg"], c["text"], "底纹"),
    ]


# =====================================================================
# 全局样式表
# =====================================================================
def build_qss(theme: str) -> str:
    c = palette(theme)
    return f"""
* {{
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 14px;
    color: {c['text']};
    outline: none;
}}
QWidget#RootWindow {{
    background: {c['bg']};
    border: 1px solid {c['border_strong']};
    border-radius: 12px;
}}
QWidget {{
    background: transparent;
}}

/* ---------- 对话框（必须显式给底色，否则顶级窗口会呈现黑底） ---------- */
QDialog {{
    background: {c['surface']};
    color: {c['text']};
}}
QDialog QLabel, QDialog QCheckBox, QDialog QRadioButton {{
    color: {c['text']};
    background: transparent;
}}
QDialog#ReminderDialog {{
    background: transparent;
}}
QMessageBox {{
    background: {c['surface']};
}}
QMessageBox QLabel {{
    color: {c['text']};
    background: transparent;
    font-size: 14px;
}}
QMessageBox QPushButton {{
    min-width: 82px;
}}
QInputDialog {{
    background: {c['surface']};
}}

/* ---------- 侧边栏 ---------- */
QWidget#Sidebar {{
    background: {c['sidebar']};
    border-right: 1px solid {c['sidebar_border']};
    border-top-left-radius: 12px;
    border-bottom-left-radius: 12px;
}}
QLabel#BrandTitle {{
    font-size: 19px;
    font-weight: 700;
    color: {c['sidebar_text']};
    background: transparent;
}}
QLabel#BrandSub {{
    font-size: 12px;
    color: {c['sidebar_muted']};
    background: transparent;
}}
QPushButton#NavButton {{
    text-align: left;
    padding: 10px 14px;
    border: none;
    border-radius: 9px;
    color: {c['sidebar_muted']};
    font-size: 14px;
    background: transparent;
}}
QPushButton#NavButton:hover {{
    background: {c['sidebar_hover']};
    color: {c['sidebar_text']};
}}
QPushButton#NavButton:checked {{
    background: {c['sidebar_active_bg']};
    color: {c['sidebar_active_text']};
    font-weight: 600;
}}
QWidget#Sidebar QFrame#CardFlat {{
    background: {c['sidebar_card_bg']};
    border: 1px solid {c['sidebar_card_border']};
    border-radius: 10px;
}}
QWidget#Sidebar QLabel#Muted {{
    color: {c['sidebar_muted']};
    background: transparent;
}}
QLabel#SidebarCount {{
    font-size: 22px;
    font-weight: 700;
    color: {c['sidebar_text']};
    background: transparent;
}}

/* ---------- 顶部标题栏 ---------- */
QWidget#TitleBar {{
    background: {c['surface']};
    border-top-right-radius: 12px;
}}
QLabel#PageTitle {{
    font-size: 16px;
    font-weight: 600;
    color: {c['text']};
}}
QPushButton#WinBtn {{
    border: none;
    background: transparent;
    border-radius: 6px;
    padding: 4px 10px;
    color: {c['text_muted']};
    font-size: 15px;
}}
QPushButton#WinBtn:hover {{
    background: {c['hover']};
    color: {c['text']};
}}
QPushButton#WinBtnClose:hover {{
    background: {c['danger']};
    color: {readable_text(c['danger'])};
}}

/* ---------- 卡片 ---------- */
QFrame#Card {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 14px;
}}
QFrame#CardFlat {{
    background: {c['surface_alt']};
    border: 1px solid {c['border']};
    border-radius: 10px;
}}
QLabel#CardTitle {{
    font-size: 15px;
    font-weight: 600;
    color: {c['text']};
    border-left: 3px solid {c['accent']};
    padding-left: 9px;
}}
QLabel#Muted {{
    color: {c['text_muted']};
    font-size: 12px;
    background: transparent;
}}
QLabel#BigNumber {{
    font-size: 34px;
    font-weight: 700;
    color: {c['primary']};
    background: transparent;
}}
QLabel#H1 {{
    font-size: 24px;
    font-weight: 700;
    color: {c['text']};
}}
QLabel#H2 {{
    font-size: 17px;
    font-weight: 600;
    color: {c['text']};
}}
QLabel#Clock {{
    font-size: 40px;
    font-weight: 700;
    color: {c['text']};
}}

/* ---------- 按钮 ---------- */
QPushButton {{
    background: {c['surface_alt']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 8px 16px;
    color: {c['text']};
}}
QPushButton:hover {{
    background: {c['hover']};
    border-color: {c['border_strong']};
}}
QPushButton:pressed {{
    background: {c['border']};
}}
QPushButton:disabled {{
    color: {c['text_muted']};
}}
QPushButton#Primary {{
    background: {c['primary']};
    border: 1px solid {c['primary']};
    color: {c['primary_text']};
    font-weight: 700;
}}
QPushButton#Primary:hover {{
    background: {c['primary_hover']};
    border-color: {c['primary_hover']};
}}
QPushButton#Danger {{
    background: transparent;
    border: 1px solid {c['danger']};
    color: {c['danger']};
}}
QPushButton#Danger:hover {{
    background: {c['danger']};
    color: {readable_text(c['danger'])};
}}
QPushButton#Ghost {{
    background: transparent;
    border: 1px solid {c['border_strong']};
}}
QPushButton#Chip {{
    border-radius: 14px;
    padding: 6px 14px;
    background: {c['surface_alt']};
    border: 1px solid {c['border']};
}}
QPushButton#Chip:checked {{
    background: {c['primary_soft']};
    border-color: {c['primary']};
    color: {c['primary']};
    font-weight: 600;
}}

/* ---------- 输入控件 ---------- */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QTimeEdit, QDateEdit {{
    background: {c['surface_alt']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 7px 10px;
    color: {c['text']};
    selection-background-color: {c['primary']};
    selection-color: {c['primary_text']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus,
QComboBox:focus, QTimeEdit:focus, QDateEdit:focus {{
    border: 1px solid {c['primary']};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    selection-background-color: {c['primary_soft']};
    selection-color: {c['primary']};
}}
QSpinBox::up-button, QSpinBox::down-button,
QTimeEdit::up-button, QTimeEdit::down-button,
QDateEdit::up-button, QDateEdit::down-button {{
    width: 16px;
    border: none;
    background: transparent;
}}

/* ---------- 开关 ---------- */
QCheckBox {{
    spacing: 8px;
    color: {c['text']};
    background: transparent;
}}
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 1.5px solid {c['border_strong']};
    background: {c['surface_alt']};
}}
QCheckBox::indicator:checked {{
    background: {c['primary']};
    border-color: {c['primary']};
    image: url(:/qt-project.org/styles/commonstyle/images/standardbutton-apply-16.png);
}}
QRadioButton {{
    spacing: 8px;
    color: {c['text']};
    background: transparent;
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1.5px solid {c['border_strong']};
    background: {c['surface_alt']};
}}
QRadioButton::indicator:checked {{
    border: 5px solid {c['primary']};
    background: {c['surface']};
}}

/* ---------- 滑块 ---------- */
QSlider::groove:horizontal {{
    height: 6px;
    border-radius: 3px;
    background: {c['border']};
}}
QSlider::sub-page:horizontal {{
    background: {c['primary']};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
    background: #ffffff;
    border: 2px solid {c['primary']};
}}

/* ---------- 滚动条 ---------- */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {c['border_strong']};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['text_muted']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
}}
QScrollBar::handle:horizontal {{
    background: {c['border_strong']};
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ---------- 列表 ---------- */
QListWidget, QListWidget#TaskList {{
    background: transparent;
    border: none;
    color: {c['text']};
}}
QListWidget::item {{
    border-radius: 8px;
    margin: 2px 0;
    color: {c['text']};
}}
QListWidget::item:selected {{
    background: {c['primary_soft']};
    color: {c['primary']};
}}
QListWidget::item:hover {{
    background: {c['hover']};
}}

/* ---------- 日历 ---------- */
QCalendarWidget QWidget {{
    alternate-background-color: {c['surface_alt']};
    color: {c['text']};
}}
QCalendarWidget QToolButton {{
    background: transparent;
    color: {c['text']};
    border-radius: 8px;
    padding: 4px 8px;
    font-weight: 600;
}}
QCalendarWidget QToolButton:hover {{
    background: {c['hover']};
}}
QCalendarWidget QAbstractItemView:enabled {{
    background: {c['surface']};
    color: {c['text']};
    selection-background-color: {c['primary']};
    selection-color: {c['primary_text']};
    outline: none;
}}
QCalendarWidget QAbstractItemView:disabled {{
    color: {c['text_muted']};
}}
QCalendarWidget QMenu {{
    background: {c['surface']};
}}
QCalendarWidget QSpinBox {{
    background: {c['surface_alt']};
}}

/* ---------- 标签页 ---------- */
QTabWidget::pane {{
    border: 1px solid {c['border']};
    border-radius: 12px;
    background: {c['surface']};
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {c['text_muted']};
    padding: 8px 18px;
    margin-right: 4px;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
}}
QTabBar::tab:selected {{
    color: {c['primary']};
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-bottom: none;
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    color: {c['text']};
}}

/* ---------- 表格 ---------- */
QTableWidget {{
    background: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    gridline-color: {c['border']};
}}
QHeaderView::section {{
    background: {c['surface_alt']};
    border: none;
    border-bottom: 1px solid {c['border']};
    padding: 8px;
    color: {c['text_muted']};
}}

/* ---------- 进度条 ---------- */
QProgressBar {{
    border: none;
    border-radius: 6px;
    background: {c['border']};
    height: 12px;
    text-align: center;
    color: {c['text']};
}}
QProgressBar::chunk {{
    border-radius: 6px;
    background: {c['primary']};
}}

/* ---------- 提示条 ---------- */
QToolTip {{
    background: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border_strong']};
    border-radius: 6px;
    padding: 6px 8px;
}}

/* ---------- 分组框 ---------- */
QGroupBox {{
    border: 1px solid {c['border']};
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 600;
    color: {c['text']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {c['text_muted']};
}}

/* ---------- 菜单 ---------- */
QMenu {{
    background: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    padding: 5px;
}}
QMenu::item {{
    padding: 7px 22px 7px 30px;
    border-radius: 6px;
    color: {c['text']};
}}
QMenu::item:selected {{
    background: {c['primary_soft']};
    color: {c['primary']};
}}
QMenu::item:checked {{
    color: {c['primary']};
    font-weight: 600;
}}
QMenu::indicator {{
    width: 14px;
    height: 14px;
    margin-left: 8px;
    border-radius: 7px;
    border: 1.5px solid {c['border_strong']};
    background: transparent;
}}
QMenu::indicator:checked {{
    background: {c['primary']};
    border-color: {c['primary']};
}}
QMenu::separator {{
    height: 1px;
    background: {c['border']};
    margin: 4px 8px;
}}
"""
