"""定时休息设置页：节奏配置 + 休息音乐管理。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QScrollArea, QSlider, QSpinBox, QCheckBox, QVBoxLayout,
    QWidget,
)

from ..icons import icon
from ..services.break_service import BreakService, BreakState
from ..services.music_player import AUDIO_EXTS
from ..theme import palette
from ..widgets.common import Card


class BreakView(QWidget):
    """定时休息配置。"""

    settings_saved = Signal()
    start_break_requested = Signal()

    def __init__(self, conf, break_service: BreakService, music_player,
                 theme: str = "light", parent=None) -> None:
        super().__init__(parent)
        self.conf = conf
        self.break_service = break_service
        self.music = music_player
        self._theme = theme
        self._files: list[str] = list(conf.get("music_files", []))
        self._build()
        self._load()
        self.break_service.tick.connect(self._on_tick)

    # ------------------------------------------------------------------
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        root = QHBoxLayout(content)
        root.setContentsMargins(4, 4, 12, 12)
        root.setSpacing(16)

        # ---------- 左：节奏 ----------
        left = Card("休息节奏", self._theme,
                    subtitle="合理安排工作与休息的交替")
        self.cb_enabled = QCheckBox("启用定时休息提醒")
        left.add(self.cb_enabled)

        self.cb_auto = QCheckBox("到点后自动进入全屏休息（不询问）")
        left.add(self.cb_auto)

        self.cb_strict = QCheckBox("严格模式（休息时不可跳过）")
        left.add(self.cb_strict)

        left.add(self._spin_row("工作间隔", "break_interval_min", 5, 240,
                                " 分钟", "每工作多久提醒休息一次"))
        left.add(self._spin_row("休息时长", "break_duration_min", 1, 60,
                                " 分钟", "单次休息持续时长"))
        left.add(self._spin_row("推迟时长", "break_snooze_min", 1, 60,
                                " 分钟", "点击推迟后延后多久再提醒"))

        win_row = QHBoxLayout()
        win_row.setSpacing(8)
        win_row.addWidget(QLabel("生效时段"))
        self.sp_start = QSpinBox()
        self.sp_start.setRange(0, 23)
        self.sp_start.setSuffix(" 时")
        self.sp_end = QSpinBox()
        self.sp_end.setRange(1, 24)
        self.sp_end.setSuffix(" 时")
        win_row.addWidget(self.sp_start)
        win_row.addWidget(QLabel("至"))
        win_row.addWidget(self.sp_end)
        win_row.addStretch(1)
        left.add_layout(win_row)

        c = palette(self._theme)
        self.lb_next = QLabel("")
        self.lb_next.setStyleSheet(f"color:{c['primary']};font-weight:600;")
        left.add(self.lb_next)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        self.btn_now = QPushButton("立即休息")
        self.btn_now.setObjectName("Primary")
        self.btn_now.clicked.connect(self.start_break_requested.emit)
        self.btn_reset = QPushButton("重新计时")
        self.btn_reset.clicked.connect(self._reset_timer)
        self.btn_save = QPushButton("保存设置")
        self.btn_save.clicked.connect(self.save)
        btns.addWidget(self.btn_now)
        btns.addWidget(self.btn_reset)
        btns.addStretch(1)
        btns.addWidget(self.btn_save)
        left.add_layout(btns)
        left.body.addStretch(1)
        root.addWidget(left, 3)

        # ---------- 右：音乐 ----------
        right = Card("休息音乐", self._theme, subtitle="休息时自动播放")
        mrow = QHBoxLayout()
        self.btn_add = QPushButton("添加音乐")
        self.btn_add.setIcon(icon("plus", c["text"], 32))
        self.btn_add.clicked.connect(self._add_files)
        self.btn_del = QPushButton("移除选中")
        self.btn_del.clicked.connect(self._remove_selected)
        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self._clear_files)
        mrow.addWidget(self.btn_add)
        mrow.addWidget(self.btn_del)
        mrow.addWidget(self.btn_clear)
        mrow.addStretch(1)
        right.add_layout(mrow)

        self.list = QListWidget()
        self.list.setMinimumHeight(170)
        right.add(self.list, 1)

        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("音量"))
        self.sl_vol = QSlider(Qt.Horizontal)
        self.sl_vol.setRange(0, 100)
        self.sl_vol.valueChanged.connect(self._on_volume)
        self.lb_vol = QLabel("60%")
        self.lb_vol.setFixedWidth(44)
        vol_row.addWidget(self.sl_vol, 1)
        vol_row.addWidget(self.lb_vol)
        right.add_layout(vol_row)

        opts = QHBoxLayout()
        self.cb_loop = QCheckBox("循环播放")
        self.cb_shuffle = QCheckBox("随机播放")
        opts.addWidget(self.cb_loop)
        opts.addWidget(self.cb_shuffle)
        opts.addStretch(1)
        self.btn_preview = QPushButton("试听")
        self.btn_preview.clicked.connect(self._preview)
        opts.addWidget(self.btn_preview)
        right.add_layout(opts)

        hint = QLabel(f"支持格式：{'、'.join(sorted(e.lstrip('.') for e in AUDIO_EXTS))}")
        hint.setObjectName("Muted")
        right.add(hint)
        right.body.addStretch(1)
        root.addWidget(right, 2)

    def _spin_row(self, label: str, key: str, lo: int, hi: int,
                  suffix: str, tip: str) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)
        lb = QLabel(label)
        lb.setFixedWidth(70)
        h.addWidget(lb)
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setSuffix(suffix)
        spin.setToolTip(tip)
        h.addWidget(spin, 1)
        setattr(self, f"sp_{key}", spin)
        return row

    # ------------------------------------------------------------------
    def _load(self) -> None:
        c = palette(self._theme)
        self.cb_enabled.setChecked(bool(self.conf.get("break_enabled", True)))
        self.cb_auto.setChecked(bool(self.conf.get("break_auto_start", False)))
        self.cb_strict.setChecked(bool(self.conf.get("break_strict", False)))
        self.sp_break_interval_min.setValue(int(self.conf.get("break_interval_min", 45)))
        self.sp_break_duration_min.setValue(
            max(1, int(self.conf.get("break_duration_sec", 300)) // 60))
        self.sp_break_snooze_min.setValue(int(self.conf.get("break_snooze_min", 5)))
        win = self.conf.get("break_work_windows", {"start": 8, "end": 22})
        self.sp_start.setValue(int(win.get("start", 8)))
        self.sp_end.setValue(int(win.get("end", 22)))

        self.sl_vol.setValue(int(self.conf.get("music_volume", 60)))
        self.cb_loop.setChecked(bool(self.conf.get("music_loop", True)))
        self.cb_shuffle.setChecked(bool(self.conf.get("music_shuffle", False)))

        self._refresh_list()
        if self.music is not None:
            self.music.set_playlist(self._files)
            self.music.set_volume(self.sl_vol.value())
            self.music.set_loop(self.cb_loop.isChecked())
            self.music.set_shuffle(self.cb_shuffle.isChecked())

    def _refresh_list(self) -> None:
        self.list.clear()
        if not self._files:
            hint = QListWidgetItem("尚未添加音乐，点击上方「添加音乐」选择本地音频文件")
            hint.setFlags(Qt.NoItemFlags)
            self.list.addItem(hint)
            return
        for f in self._files:
            name = Path(f).name
            item = QListWidgetItem(icon("music", palette(self._theme)["primary"], 32),
                                   name)
            item.setToolTip(f)
            self.list.addItem(item)

    # ------------------------------------------------------------------
    def _add_files(self) -> None:
        patterns = " ".join(f"*{e}" for e in sorted(AUDIO_EXTS))
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择休息音乐", "", f"音频文件 ({patterns});;所有文件 (*.*)")
        for f in files:
            if f not in self._files:
                self._files.append(f)
        self._refresh_list()

    def _remove_selected(self) -> None:
        for item in self.list.selectedItems():
            row = self.list.row(item)
            if 0 <= row < len(self._files):
                self._files.pop(row)
        self._refresh_list()

    def _clear_files(self) -> None:
        self._files.clear()
        self._refresh_list()

    def _on_volume(self, val: int) -> None:
        self.lb_vol.setText(f"{val}%")
        if self.music is not None:
            self.music.set_volume(val)
        self.conf.set("music_volume", val)

    def _preview(self) -> None:
        if self.music is None or not self.music.available:
            return
        if self.music.is_playing():
            self.music.stop()
            self.btn_preview.setText("试听")
            return
        self.music.set_playlist(self._files)
        self.music.set_volume(self.sl_vol.value())
        if self._files:
            self.music.play()
            self.btn_preview.setText("停止")

    def _reset_timer(self) -> None:
        self.break_service.reset()

    # ------------------------------------------------------------------
    def save(self) -> None:
        self.conf.update({
            "break_enabled": self.cb_enabled.isChecked(),
            "break_auto_start": self.cb_auto.isChecked(),
            "break_strict": self.cb_strict.isChecked(),
            "break_interval_min": self.sp_break_interval_min.value(),
            "break_duration_sec": self.sp_break_duration_min.value() * 60,
            "break_snooze_min": self.sp_break_snooze_min.value(),
            "break_work_windows": {
                "start": self.sp_start.value(),
                "end": self.sp_end.value(),
            },
            "music_files": self._files,
            "music_volume": self.sl_vol.value(),
            "music_loop": self.cb_loop.isChecked(),
            "music_shuffle": self.cb_shuffle.isChecked(),
        })
        self.conf.save()
        if self.music is not None:
            self.music.set_playlist(self._files)
            self.music.set_loop(self.cb_loop.isChecked())
            self.music.set_shuffle(self.cb_shuffle.isChecked())

        # 让调度器按新配置重启
        if self.conf.get("break_enabled", True):
            self.break_service.stop()
            self.break_service.start()
        else:
            self.break_service.stop()
        self.settings_saved.emit()

    # ------------------------------------------------------------------
    def _on_tick(self, remaining: int, state: str) -> None:
        if state == BreakState.WORKING.value:
            self.lb_next.setText(f"距离下次休息：{BreakService.format_hms(remaining)}")
        elif state == BreakState.BREAKING.value:
            self.lb_next.setText(f"正在休息：{BreakService.format_hms(remaining)}")
        elif state == BreakState.READY.value:
            self.lb_next.setText("该休息了！")
        else:
            self.lb_next.setText("定时休息已关闭")
