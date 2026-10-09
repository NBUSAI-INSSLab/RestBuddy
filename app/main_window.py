"""主窗口：无边框窗口 + 侧边导航 + 各功能页面 + 系统托盘 + 休息流程编排。"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFrame, QHBoxLayout, QLabel, QMenu,
    QMessageBox, QPushButton, QSizeGrip, QStackedWidget, QSystemTrayIcon,
    QVBoxLayout, QWidget,
)

from .config import config
from .database import TaskRepository
from .icons import icon
from .services.break_service import BreakService, BreakState
from .services.music_player import MusicPlayer
from .theme import SCHEME_LABELS, build_qss, palette, scheme_label
from .views.break_view import BreakView
from .views.calendar_view import CalendarView
from .views.dashboard import DashboardView
from .views.settings_view import SettingsView
from .widgets.break_overlay import BreakOverlay
from .widgets.today_reminder import TodayReminderDialog

NAV_ITEMS = [
    ("dashboard", "今日总览", "dashboard"),
    ("calendar", "任务日历", "calendar"),
    ("break", "定时休息", "coffee"),
    ("settings", "软件配置", "settings"),
]

PAGE_TITLES = {
    "dashboard": "今日总览",
    "calendar": "任务日历",
    "break": "定时休息",
    "settings": "软件配置",
}


class MainWindow(QWidget):
    """应用主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.conf = config()
        self.repo = TaskRepository()
        self.music = MusicPlayer(self)
        self.break_service = BreakService(self.conf, self)

        self._rest_count = 0
        self._drag_pos: QPoint | None = None
        self._resize_edge = None

        self.setWindowTitle("今日小憩")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(1080, 720)
        self.resize(1200, 780)

        self._build()
        self._build_tray()
        self._wire_services()
        self.apply_theme(self.conf.get("theme", "light"))
        self._restore_startup_state()

        self._second_timer = QTimer(self)
        self._second_timer.setInterval(30000)
        self._second_timer.timeout.connect(self._check_task_reminders)
        self._second_timer.start()

        self.break_service.start()

        if self.conf.get("show_today_on_start", True):
            QTimer.singleShot(700, self.show_today_reminder)

    # ==================================================================
    # 构建
    # ==================================================================
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.root = QFrame()
        self.root.setObjectName("RootWindow")
        outer.addWidget(self.root)

        root_layout = QHBoxLayout(self.root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---- 侧边栏 ----
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(216)
        sl = QVBoxLayout(self.sidebar)
        sl.setContentsMargins(14, 18, 14, 16)
        sl.setSpacing(6)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        self.logo_label = QLabel()
        self.logo_label.setPixmap(self._make_logo(40))
        brand.addWidget(self.logo_label)
        col = QVBoxLayout()
        col.setSpacing(0)
        t = QLabel("今日小憩")
        t.setObjectName("BrandTitle")
        s = QLabel("工作节律 · 任务提醒")
        s.setObjectName("BrandSub")
        col.addWidget(t)
        col.addWidget(s)
        brand.addLayout(col)
        brand.addStretch(1)
        sl.addLayout(brand)
        sl.addSpacing(14)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: dict[str, QPushButton] = {}
        for key, label, ic in NAV_ITEMS:
            btn = QPushButton("  " + label)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _c=False, k=key: self.switch_page(k))
            self.nav_group.addButton(btn)
            self.nav_buttons[key] = btn
            sl.addWidget(btn)

        sl.addStretch(1)

        # 侧边栏底部：倒计时
        self.rest_box = QFrame()
        self.rest_box.setObjectName("CardFlat")
        rb = QVBoxLayout(self.rest_box)
        rb.setContentsMargins(12, 10, 12, 12)
        rb.setSpacing(4)
        cap = QLabel("距离下次休息")
        cap.setObjectName("Muted")
        self.lb_sidebar_count = QLabel("--:--")
        self.lb_sidebar_count.setObjectName("SidebarCount")
        self.btn_sidebar_break = QPushButton("立即休息")
        self.btn_sidebar_break.setObjectName("Primary")
        self.btn_sidebar_break.clicked.connect(self.do_break_now)
        rb.addWidget(cap)
        rb.addWidget(self.lb_sidebar_count)
        rb.addWidget(self.btn_sidebar_break)
        sl.addWidget(self.rest_box)
        root_layout.addWidget(self.sidebar)

        # ---- 右侧主体 ----
        main = QWidget()
        ml = QVBoxLayout(main)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        # 标题栏
        self.titlebar = QWidget()
        self.titlebar.setObjectName("TitleBar")
        self.titlebar.setFixedHeight(52)
        self.titlebar.mousePressEvent = self._title_press
        self.titlebar.mouseMoveEvent = self._title_move
        self.titlebar.mouseReleaseEvent = self._title_release
        self.titlebar.mouseDoubleClickEvent = lambda _e: self._toggle_max()
        tl = QHBoxLayout(self.titlebar)
        tl.setContentsMargins(20, 0, 10, 0)
        tl.setSpacing(8)
        self.lb_page = QLabel("今日总览")
        self.lb_page.setObjectName("PageTitle")
        tl.addWidget(self.lb_page)
        tl.addStretch(1)

        self.btn_theme = self._win_btn("palette", "切换配色方案", self._show_scheme_menu)
        tl.addWidget(self.btn_theme)
        self.btn_min = self._win_btn("min", "最小化", self.showMinimized)
        self.btn_max = self._win_btn("max", "最大化/还原", self._toggle_max)
        self.btn_close = self._win_btn("close", "关闭", self.close)
        self.btn_close.setObjectName("WinBtnClose")
        for b in (self.btn_min, self.btn_max, self.btn_close):
            tl.addWidget(b)
        ml.addWidget(self.titlebar)

        # 页面栈
        self.stack = QStackedWidget()
        self.stack.setContentsMargins(16, 12, 6, 12)
        ml.addWidget(self.stack, 1)

        self.page_dashboard = DashboardView(self.repo, self.break_service,
                                            self.conf, self.conf.get("theme", "light"))
        self.page_calendar = CalendarView(self.repo, self.conf,
                                          self.conf.get("theme", "light"))
        self.page_break = BreakView(self.conf, self.break_service, self.music,
                                    self.conf.get("theme", "light"))
        self.page_settings = SettingsView(self.conf, self.repo,
                                          self.conf.get("theme", "light"))
        self.pages = {
            "dashboard": self.page_dashboard,
            "calendar": self.page_calendar,
            "break": self.page_break,
            "settings": self.page_settings,
        }
        for w in self.pages.values():
            self.stack.addWidget(w)
        root_layout.addWidget(main, 1)

        # 尺寸调整手柄
        self.grip = QSizeGrip(self)
        self.grip.setFixedSize(16, 16)
        self.grip.setStyleSheet("background:transparent;")

        # 信号连接
        self.page_dashboard.tasks_changed.connect(self._on_tasks_changed)
        self.page_dashboard.start_break_requested.connect(self.do_break_now)
        self.page_dashboard.snooze_requested.connect(self._snooze_break)
        self.page_calendar.tasks_changed.connect(self._on_tasks_changed)
        self.page_break.start_break_requested.connect(self.do_break_now)
        self.page_break.settings_saved.connect(self._on_break_settings)
        self.page_settings.theme_changed.connect(self.apply_theme)

        self.switch_page(self._initial_page())

    # ------------------------------------------------------------------
    def _make_logo(self, size: int) -> QPixmap:
        """生成应用 logo：圆角方块使用当前方案主色，叶片取主色上的文字色。"""
        c = palette(self.conf.get("theme", "light"))
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)
        path = QPainterPath()
        r = size * 0.28
        path.addRoundedRect(0, 0, size, size, r, r)
        p.fillPath(path, QColor(c["primary"]))
        leaf = icon("leaf", c["primary_text"], 64).pixmap(int(size * 0.62),
                                                          int(size * 0.62))
        p.drawPixmap(int(size * 0.19), int(size * 0.19), leaf)
        p.end()
        return pm

    def _win_btn(self, name: str, tip: str, slot) -> QPushButton:
        c = palette(self.conf.get("theme", "light"))
        b = QPushButton()
        b.setObjectName("WinBtn")
        b.setIcon(icon(name, c["text_muted"], 32))
        b.setToolTip(tip)
        b.setFixedSize(38, 32)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(slot)
        return b

    # ==================================================================
    # 托盘
    # ==================================================================
    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(QIcon(self._make_logo(64)), self)
        self.tray.setToolTip("今日小憩")
        menu = QMenu()
        act_show = QAction("显示主窗口", self)
        act_show.triggered.connect(self._restore_window)
        act_break = QAction("立即休息", self)
        act_break.triggered.connect(self.do_break_now)
        act_quit = QAction("退出", self)
        act_quit.triggered.connect(self._quit)
        menu.addAction(act_show)
        menu.addAction(act_break)
        menu.addSeparator()
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self._restore_window()

    def _restore_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ==================================================================
    # 服务编排
    # ==================================================================
    def _wire_services(self) -> None:
        self.overlay = BreakOverlay(self.music, self.conf.get("theme", "light"), self)
        self.overlay.finished.connect(self._on_overlay_finished)
        self.overlay.snooze_requested.connect(self._snooze_break)

        self.music.set_playlist(self.conf.get("music_files", []))
        self.music.set_volume(int(self.conf.get("music_volume", 60)))
        self.music.set_loop(bool(self.conf.get("music_loop", True)))
        self.music.set_shuffle(bool(self.conf.get("music_shuffle", False)))

        self.break_service.tick.connect(self._on_break_tick)
        self.break_service.break_ready.connect(self._on_break_ready)
        self.break_service.break_started.connect(self._on_break_started)
        self.break_service.break_finished.connect(self._on_break_finished)

    def do_break_now(self) -> None:
        self.break_service.start_break_now()

    def _snooze_break(self) -> None:
        self.break_service.snooze()

    def _on_break_ready(self) -> None:
        self.tray.showMessage("该休息了", "已连续工作一段时间，起来活动一下吧。",
                              QSystemTrayIcon.Information, 4000)
        box = QMessageBox(self)
        box.setWindowTitle("该休息了")
        box.setIcon(QMessageBox.Information)
        box.setText("已经连续工作一段时间啦")
        box.setInformativeText("起来走动一下、看看远方，让眼睛和大脑放松片刻。")
        btn_now = box.addButton("立即休息", QMessageBox.AcceptRole)
        btn_snooze = box.addButton("推迟几分钟", QMessageBox.RejectRole)
        btn_skip = box.addButton("跳过本次", QMessageBox.DestructiveRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is btn_now:
            self.break_service.start_break_now()
        elif clicked is btn_snooze:
            self.break_service.snooze()
        elif clicked is btn_skip:
            self.break_service.reset()

    def _on_break_started(self, duration: int) -> None:
        self._rest_count += 1
        self.page_dashboard.set_break_count(self._rest_count)
        strict = bool(self.conf.get("break_strict", False))
        self.overlay.begin(duration, strict=strict, round_no=self._rest_count)

    def _on_break_finished(self, reason: str) -> None:
        self.overlay.close_overlay()
        if reason == "ok":
            self.tray.showMessage("休息结束", "欢迎回来，继续加油！",
                                  QSystemTrayIcon.Information, 3000)

    def _on_overlay_finished(self, reason: str) -> None:
        self.break_service.finish_break(reason)

    def _on_break_tick(self, remaining: int, state: str) -> None:
        self.lb_sidebar_count.setText(BreakService.format_hms(remaining))
        if state == BreakState.BREAKING.value:
            self.overlay.update_countdown(remaining)

    def _on_break_settings(self) -> None:
        self.music.set_playlist(self.conf.get("music_files", []))
        self.music.set_volume(int(self.conf.get("music_volume", 60)))

    # ==================================================================
    # 任务提醒
    # ==================================================================
    def _check_task_reminders(self) -> None:
        due = self.repo.upcoming(minutes=1)
        for t in due:
            self.tray.showMessage(f"任务提醒 · {t.time}", t.title,
                                  QSystemTrayIcon.Information, 6000)

    def show_today_reminder(self) -> None:
        tasks = self.repo.today()
        dlg = TodayReminderDialog(tasks, self.conf.get("theme", "light"), self)
        dlg.snooze_requested.connect(
            lambda mins: QTimer.singleShot(mins * 60 * 1000, self.show_today_reminder))
        dlg.exec()

    def _on_tasks_changed(self) -> None:
        self.page_dashboard.refresh()
        self.page_calendar.refresh()

    # ==================================================================
    # 页面切换 / 主题 / 窗口
    # ==================================================================
    def switch_page(self, key: str) -> None:
        if key not in self.pages:
            key = "dashboard"
        self.stack.setCurrentWidget(self.pages[key])
        self.lb_page.setText(PAGE_TITLES.get(key, ""))
        self.nav_buttons[key].setChecked(True)
        self.conf.set("last_page", key)
        if self.conf.get("startup_mode") == "last":
            self.conf.save()

    def _initial_page(self) -> str:
        if self.conf.get("startup_mode", "last") == "last":
            key = self.conf.get("last_page", "dashboard")
        else:
            key = self.conf.get("default_page", "dashboard")
        # 兼容旧配置中已被移除的页面
        if key not in self.pages:
            key = "dashboard"
        return key or "dashboard"

    def apply_theme(self, theme: str) -> None:
        self.conf.set("theme", theme)
        self.conf.save()
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_qss(theme))
        c = palette(theme)
        for name, b in self.nav_buttons.items():
            ic = dict((k, i) for k, _l, i in NAV_ITEMS)[name]
            b.setIcon(icon(ic, c["sidebar_muted"], 40))
        self.btn_theme.setIcon(icon("palette", c["text_muted"], 32))
        self.btn_theme.setToolTip(f"切换配色方案（当前：{scheme_label(theme)}）")
        if hasattr(self, "logo_label"):
            self.logo_label.setPixmap(self._make_logo(40))
        if hasattr(self, "tray"):
            self.tray.setIcon(QIcon(self._make_logo(64)))
        if hasattr(self, "overlay"):
            self.overlay.set_theme(theme)
        # 重建页面以应用新配色
        self._rebuild_pages(theme)

    def _rebuild_pages(self, theme: str) -> None:
        current = self.stack.currentWidget()
        current_key = next((k for k, v in self.pages.items() if v is current), "dashboard")

        for w in self.pages.values():
            self.stack.removeWidget(w)
            w.deleteLater()

        self.page_dashboard = DashboardView(self.repo, self.break_service, self.conf, theme)
        self.page_calendar = CalendarView(self.repo, self.conf, theme)
        self.page_break = BreakView(self.conf, self.break_service, self.music, theme)
        self.page_settings = SettingsView(self.conf, self.repo, theme)
        self.pages = {
            "dashboard": self.page_dashboard,
            "calendar": self.page_calendar,
            "break": self.page_break,
            "settings": self.page_settings,
        }
        for w in self.pages.values():
            self.stack.addWidget(w)

        self.page_dashboard.tasks_changed.connect(self._on_tasks_changed)
        self.page_dashboard.start_break_requested.connect(self.do_break_now)
        self.page_dashboard.snooze_requested.connect(self._snooze_break)
        self.page_calendar.tasks_changed.connect(self._on_tasks_changed)
        self.page_break.start_break_requested.connect(self.do_break_now)
        self.page_break.settings_saved.connect(self._on_break_settings)
        self.page_settings.theme_changed.connect(self.apply_theme)

        self.stack.setCurrentWidget(self.pages.get(current_key, self.page_dashboard))
        self.page_dashboard.set_break_count(self._rest_count)

    def _show_scheme_menu(self) -> None:
        """标题栏配色按钮：弹出配色方案菜单。"""
        current = self.conf.get("theme", "light")
        menu = QMenu(self)
        for key, label in SCHEME_LABELS:
            act = QAction(label, self)
            act.setCheckable(True)
            act.setChecked(key == current)
            act.triggered.connect(lambda _checked=False, k=key: self.apply_theme(k))
            menu.addAction(act)
        menu.addSeparator()
        act_more = QAction("更多配色设置…", self)
        act_more.triggered.connect(lambda: self._open_settings_appearance())
        menu.addAction(act_more)
        pos = self.btn_theme.mapToGlobal(QPoint(0, self.btn_theme.height() + 6))
        menu.exec(pos)

    def _open_settings_appearance(self) -> None:
        self.switch_page("settings")
        page = self.pages.get("settings")
        if page is not None and hasattr(page, "scroll"):
            page.scroll.verticalScrollBar().setValue(0)

    # ---- 启动状态 ----
    def _restore_startup_state(self) -> None:
        import base64
        geo = self.conf.get("last_geometry", "")
        if self.conf.get("startup_mode", "last") == "last" and geo:
            try:
                self.restoreGeometry(base64.b64decode(geo.encode()))
            except (ValueError, TypeError):
                pass

    def _save_window_state(self) -> None:
        import base64
        try:
            self.conf.set("last_geometry",
                          base64.b64encode(self.saveGeometry()).decode())
        except (ValueError, TypeError):
            pass
        self.conf.save()

    # ---- 窗口拖动 / 缩放 ----
    def _title_press(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._drag_start = self.frameGeometry().topLeft()

    def _title_move(self, event) -> None:
        if self._drag_pos is None or not (event.buttons() & Qt.LeftButton):
            return
        delta = event.globalPosition().toPoint() - self._drag_pos
        if self.isMaximized():
            return
        self.move(self._drag_start + delta)

    def _title_release(self, _event) -> None:
        self._drag_pos = None

    def _toggle_max(self) -> None:
        if self.isMaximized():
            self.showNormal()
            self.btn_max.setIcon(icon("max", palette(self.conf.get("theme", "light"))["text_muted"], 32))
        else:
            self.showMaximized()
            self.btn_max.setIcon(icon("restore", palette(self.conf.get("theme", "light"))["text_muted"], 32))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "grip"):
            self.grip.move(self.width() - 20, self.height() - 20)

    def closeEvent(self, event) -> None:
        if self.conf.get("minimize_to_tray", True) and self.tray.isVisible() \
                and not getattr(self, "_really_quit", False):
            event.ignore()
            self.hide()
            self.tray.showMessage("今日小憩", "已最小化到托盘，休息计时继续运行。",
                                  QSystemTrayIcon.Information, 3000)
            return
        self._save_window_state()
        super().closeEvent(event)

    def _quit(self) -> None:
        self._really_quit = True
        self._save_window_state()
        self.break_service.stop()
        self.music.stop()
        self.tray.hide()
        QApplication.instance().quit()
