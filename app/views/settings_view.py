"""软件配置页：配色方案、启动行为、开机自启、数据管理。"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QRadioButton, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget,
)

from .. import autostart
from ..config import app_data_dir, app_root_dir
from ..icons import icon
from ..theme import SCHEME_LABELS, palette, sample_colors
from ..widgets.break_overlay import default_slides_dir, scan_images
from ..widgets.common import Card

PAGE_NAMES = {
    "dashboard": "今日总览",
    "calendar": "任务日历",
    "break": "定时休息",
}


class SettingsView(QWidget):
    """应用设置。"""

    theme_changed = Signal(str)
    startup_changed = Signal()
    break_ui_changed = Signal()

    def __init__(self, conf, repo, theme: str = "light", parent=None) -> None:
        super().__init__(parent)
        self.conf = conf
        self.repo = repo
        self._theme = theme
        self._build()
        self._load()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        self.scroll = scroll
        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(4, 4, 12, 12)
        root.setSpacing(16)

        # ---- 外观与配色 ----
        look = Card("外观与配色", self._theme,
                    subtitle="配色方案统一作用于窗口、卡片与文字，切换后立即生效")
        row = QHBoxLayout()
        row.addWidget(QLabel("配色方案"))
        self.cb_theme = QComboBox()
        for key, label in SCHEME_LABELS:
            self.cb_theme.addItem(label, key)
        self.cb_theme.currentIndexChanged.connect(self._on_theme)
        row.addWidget(self.cb_theme, 1)
        row.addStretch(2)
        look.add_layout(row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        for i, (bg, fg, name) in enumerate(sample_colors(self._theme)):
            chip = QLabel(f"{name}  Aa 示例文字")
            chip.setAlignment(Qt.AlignCenter)
            chip.setFixedHeight(38)
            chip.setStyleSheet(
                f"background:{bg};color:{fg};border-radius:9px;"
                f"font-size:13px;font-weight:600;"
            )
            grid.addWidget(chip, i // 2, i % 2)
        look.add_layout(grid)

        self.lb_theme_hint = QLabel(
            "已内置薄荷绿（浅/深）、橙色、橙蓝、黑灰五套方案，"
            "每套都已按对比度配好文字颜色，确保清晰可读。")
        self.lb_theme_hint.setObjectName("Muted")
        self.lb_theme_hint.setWordWrap(True)
        look.add(self.lb_theme_hint)
        root.addWidget(look)

        # ---- 全屏休息界面 ----
        brk = Card("全屏休息界面", self._theme,
                   subtitle="休息全屏页展示的内容，以及结束前的警示方式")
        self.cb_carousel = QCheckBox("休息时显示图片轮播（无图片则展示内置放松内容卡）")
        brk.add(self.cb_carousel)

        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("图片目录"))
        self.lb_slides_dir = QLabel("")
        self.lb_slides_dir.setObjectName("Muted")
        self.lb_slides_dir.setTextInteractionFlags(Qt.TextSelectableByMouse)
        btn_open_slides = QPushButton("打开目录")
        btn_open_slides.clicked.connect(self._open_slides_dir)
        btn_pick_slides = QPushButton("更换目录")
        btn_pick_slides.clicked.connect(self._pick_slides_dir)
        btn_reset_slides = QPushButton("恢复默认")
        btn_reset_slides.clicked.connect(self._reset_slides_dir)
        dir_row.addWidget(self.lb_slides_dir, 1)
        dir_row.addWidget(btn_open_slides)
        dir_row.addWidget(btn_pick_slides)
        dir_row.addWidget(btn_reset_slides)
        brk.add_layout(dir_row)

        self.lb_slides_hint = QLabel("")
        self.lb_slides_hint.setObjectName("Muted")
        self.lb_slides_hint.setWordWrap(True)
        brk.add(self.lb_slides_hint)

        num_row = QHBoxLayout()
        num_row.addWidget(QLabel("每张停留"))
        self.sp_slide = QSpinBox()
        self.sp_slide.setRange(5, 120)
        self.sp_slide.setSuffix(" 秒")
        self.sp_slide.setFixedWidth(110)
        num_row.addWidget(self.sp_slide)
        num_row.addSpacing(28)
        num_row.addWidget(QLabel("结束前警示"))
        self.sp_warn = QSpinBox()
        self.sp_warn.setRange(5, 120)
        self.sp_warn.setSuffix(" 秒")
        self.sp_warn.setFixedWidth(110)
        num_row.addWidget(self.sp_warn)
        num_row.addStretch(1)
        brk.add_layout(num_row)

        self.btn_save_brk = QPushButton("保存休息界面设置")
        self.btn_save_brk.setObjectName("Primary")
        self.btn_save_brk.clicked.connect(self._save_break_ui)
        brk.body.addWidget(self.btn_save_brk, 0, Qt.AlignRight)
        root.addWidget(brk)

        # ---- 启动行为 ----
        start = Card("启动与运行", self._theme,
                     subtitle="控制开机自启与每次启动时的界面状态")
        self.cb_autostart = QCheckBox("开机后自动启动今日小憩")
        self.cb_autostart.toggled.connect(self._on_autostart)
        start.add(self.cb_autostart)

        self.lb_autostart_hint = QLabel("")
        self.lb_autostart_hint.setObjectName("Muted")
        start.add(self.lb_autostart_hint)

        self.cb_show_today = QCheckBox("启动时弹出今日任务提醒")
        start.add(self.cb_show_today)

        self.cb_tray = QCheckBox("关闭主窗口时最小化到系统托盘继续计时")
        start.add(self.cb_tray)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("启动界面状态"))
        self.rb_default = QRadioButton("默认状态")
        self.rb_last = QRadioButton("上一次打开状态")
        mode_row.addWidget(self.rb_default)
        mode_row.addWidget(self.rb_last)
        mode_row.addStretch(1)
        start.add_layout(mode_row)

        page_row = QHBoxLayout()
        page_row.addWidget(QLabel("默认起始页面"))
        self.cb_default_page = QComboBox()
        for key, name in PAGE_NAMES.items():
            self.cb_default_page.addItem(name, key)
        page_row.addWidget(self.cb_default_page, 1)
        page_row.addStretch(2)
        start.add_layout(page_row)

        self.btn_save_start = QPushButton("保存启动设置")
        self.btn_save_start.setObjectName("Primary")
        self.btn_save_start.clicked.connect(self._save_startup)
        start.body.addWidget(self.btn_save_start, 0, Qt.AlignRight)
        root.addWidget(start)

        # ---- 数据 ----
        data = Card("数据与关于", self._theme)
        path_row = QHBoxLayout()
        lb = QLabel("数据目录")
        self.lb_datadir = QLabel(str(app_data_dir()))
        self.lb_datadir.setObjectName("Muted")
        self.lb_datadir.setTextInteractionFlags(Qt.TextSelectableByMouse)
        btn_open = QPushButton("打开目录")
        btn_open.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(app_data_dir()))))
        path_row.addWidget(lb)
        path_row.addWidget(self.lb_datadir, 1)
        path_row.addWidget(btn_open)
        data.add_layout(path_row)

        act = QHBoxLayout()
        btn_csv = QPushButton("导出任务为 CSV")
        btn_csv.clicked.connect(self._export_csv)
        btn_json = QPushButton("备份配置")
        btn_json.clicked.connect(self._export_config)
        btn_del = QPushButton("清空所有任务")
        btn_del.setObjectName("Danger")
        btn_del.clicked.connect(self._clear_tasks)
        act.addWidget(btn_csv)
        act.addWidget(btn_json)
        act.addStretch(1)
        act.addWidget(btn_del)
        data.add_layout(act)

        about = QLabel("今日小憩 v1.0 · 定时休息 · 任务日历 · 当日任务提醒 · 开机自启")
        about.setObjectName("Muted")
        data.add(about)
        root.addWidget(data)
        root.addStretch(1)

    # ------------------------------------------------------------------
    def _load(self) -> None:
        self.cb_theme.blockSignals(True)
        idx = self.cb_theme.findData(self.conf.get("theme", "light"))
        self.cb_theme.setCurrentIndex(max(0, idx))
        self.cb_theme.blockSignals(False)
        self.cb_autostart.blockSignals(True)
        self.cb_autostart.setChecked(autostart.is_enabled() or
                                     bool(self.conf.get("autostart", False)))
        self.cb_autostart.blockSignals(False)
        self._update_autostart_hint()
        self.cb_show_today.setChecked(bool(self.conf.get("show_today_on_start", True)))
        self.cb_tray.setChecked(bool(self.conf.get("minimize_to_tray", True)))
        mode = self.conf.get("startup_mode", "last")
        self.rb_last.setChecked(mode == "last")
        self.rb_default.setChecked(mode != "last")
        pidx = self.cb_default_page.findData(self.conf.get("default_page", "dashboard"))
        self.cb_default_page.setCurrentIndex(max(0, pidx))

        # 全屏休息界面
        self.cb_carousel.setChecked(bool(self.conf.get("break_carousel", True)))
        self.sp_slide.setValue(int(self.conf.get("break_slide_sec", 12) or 12))
        self.sp_warn.setValue(int(self.conf.get("break_warn_sec", 15) or 15))
        self._refresh_slides_hint()

    def _update_autostart_hint(self) -> None:
        enabled = autostart.is_enabled()
        self.lb_autostart_hint.setText(
            "自启动已在系统中注册（可通过任务管理器关闭）" if enabled
            else "开启后会写入当前用户的启动项，登录 Windows 后自动运行"
        )

    # ------------------------------------------------------------------
    def _on_theme(self) -> None:
        theme = self.cb_theme.currentData()
        self.conf.set("theme", theme)
        self.conf.save()
        self.theme_changed.emit(theme)

    def _on_autostart(self, checked: bool) -> None:
        if checked:
            ok, msg = autostart.enable()
        else:
            ok, msg = autostart.disable()
        self.conf.set("autostart", checked and ok)
        self.conf.save()
        self._update_autostart_hint()
        if not ok:
            QMessageBox.warning(self, "开机自启动", msg)

    def _save_startup(self) -> None:
        self.conf.update({
            "show_today_on_start": self.cb_show_today.isChecked(),
            "minimize_to_tray": self.cb_tray.isChecked(),
            "startup_mode": "last" if self.rb_last.isChecked() else "default",
            "default_page": self.cb_default_page.currentData(),
        })
        self.conf.save()
        self.startup_changed.emit()
        QMessageBox.information(self, "已保存", "启动设置已更新。")

    # ------------------------------------------------------------------
    # 全屏休息界面
    # ------------------------------------------------------------------
    def _slides_dir(self) -> Path:
        raw = str(self.conf.get("break_image_dir", "") or "").strip()
        return Path(raw) if raw else default_slides_dir()

    def _refresh_slides_hint(self) -> None:
        d = self._slides_dir()
        self.lb_slides_dir.setText(str(d))
        n = len(scan_images(d))
        if n:
            self.lb_slides_hint.setText(
                f"已发现 {n} 张图片，休息时会自动轮播（点击轮播区域或按空格键可手动切换）。"
            )
        else:
            self.lb_slides_hint.setText(
                "该目录下暂无图片。放入 jpg / png / bmp / webp 等图片即可自动轮播；"
                "没有图片时会展示内置的放松内容卡（护眼法则、深呼吸、颈肩舒展等）。"
            )

    def _open_slides_dir(self) -> None:
        d = self._slides_dir()
        try:
            d.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))

    def _pick_slides_dir(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, "选择轮播图片目录",
                                               str(self._slides_dir()))
        if not path:
            return
        self.conf.set("break_image_dir", path)
        self.conf.save()
        self._refresh_slides_hint()
        self.break_ui_changed.emit()

    def _reset_slides_dir(self) -> None:
        self.conf.set("break_image_dir", "")
        self.conf.save()
        self._refresh_slides_hint()
        self.break_ui_changed.emit()

    def _save_break_ui(self) -> None:
        self.conf.update({
            "break_carousel": self.cb_carousel.isChecked(),
            "break_slide_sec": self.sp_slide.value(),
            "break_warn_sec": self.sp_warn.value(),
        })
        self.conf.save()
        self.break_ui_changed.emit()
        QMessageBox.information(self, "已保存", "休息界面设置已更新，下次进入休息时生效。")

    # ------------------------------------------------------------------
    def _export_csv(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "导出任务", f"任务清单_{dt.date.today():%Y%m%d}.csv",
            "CSV 文件 (*.csv)")
        if not path:
            return
        try:
            import csv
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["标题", "日期", "时间", "优先级", "类别", "完成", "备注"])
                for t in self.repo.all():
                    writer.writerow([
                        t.title, t.date, t.time, t.priority_label, t.category,
                        "是" if t.done else "否", t.notes,
                    ])
            QMessageBox.information(self, "导出成功", f"已导出到：\n{path}")
        except OSError as exc:
            QMessageBox.warning(self, "导出失败", str(exc))

    def _export_config(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "备份配置", "今日小憩配置备份.json", "JSON 文件 (*.json)")
        if not path:
            return
        try:
            Path(path).write_text(
                json.dumps(self.conf.as_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8")
            QMessageBox.information(self, "备份成功", f"配置已备份到：\n{path}")
        except OSError as exc:
            QMessageBox.warning(self, "备份失败", str(exc))

    def _clear_tasks(self) -> None:
        ret = QMessageBox.question(
            self, "确认清空", "确定要删除所有任务吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret != QMessageBox.Yes:
            return
        for t in self.repo.all():
            if t.id is not None:
                self.repo.delete(t.id)
        QMessageBox.information(self, "已清空", "所有任务已删除。")
