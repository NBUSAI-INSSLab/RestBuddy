"""配置管理：使用 JSON 文件持久化用户设置。

配置保存在用户数据目录（%APPDATA%/RestBuddy/config.json），
包含休息节奏、主题、开机自启、启动状态、AI 接口等设置。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def app_data_dir() -> Path:
    """返回应用数据目录，必要时创建。"""
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = Path(base) / "RestBuddy"
    d.mkdir(parents=True, exist_ok=True)
    return d


def app_root_dir() -> Path:
    """返回项目根目录（main.py 所在目录）。"""
    return Path(__file__).resolve().parent.parent


# 默认配置
DEFAULTS: dict[str, Any] = {
    # 休息节奏
    "break_enabled": True,
    "break_interval_min": 45,        # 每工作多少分钟休息一次
    "break_duration_sec": 300,       # 单次休息时长（秒）
    "break_snooze_min": 5,           # 推迟休息的时长
    "break_strict": False,           # 严格模式：强制全屏不可跳过
    "break_work_windows": {          # 生效时间段（小时，24 制）
        "start": 8,
        "end": 22,
    },
    "break_auto_start": False,       # 到点自动进入休息（否则仅提醒）

    # 音乐
    "music_files": [],               # 休息音乐文件路径列表
    "music_volume": 60,              # 0-100
    "music_loop": True,
    "music_shuffle": False,

    # 界面
    "theme": "light",                # light / dark / orange / orangeblue / gray
    "startup_mode": "last",          # default（默认状态）/ last（上一次打开状态）
    "default_page": "dashboard",     # default 模式下的起始页面
    "last_page": "dashboard",        # last 模式记录的页面
    "last_geometry": "",             # 上次窗口几何（base64）

    # 提醒
    "show_today_on_start": True,     # 启动时弹出当日任务提醒
    "today_remind_times": ["09:00"],  # 每日固定提醒时间点

    # 系统
    "autostart": False,              # 开机自启
    "minimize_to_tray": True,
    "first_run": True,
}


class ConfigManager:
    """读写 JSON 配置，支持点号路径访问与默认值回退。"""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "config.json")
        self._data: dict[str, Any] = {}
        self.load()

    # ------------------------------------------------------------------
    def load(self) -> None:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self._data = loaded
            except (json.JSONDecodeError, OSError):
                self._data = {}
        # 补齐缺失的默认项
        merged = json.loads(json.dumps(DEFAULTS))
        merged.update(self._data)
        self._data = merged

    def save(self) -> None:
        try:
            tmp = self.path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            tmp.replace(self.path)
        except OSError:
            pass

    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        if key in self._data:
            return self._data[key]
        if default is not None:
            return default
        return DEFAULTS.get(key)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def update(self, values: dict[str, Any]) -> None:
        self._data.update(values)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)


# 全局单例
_config: ConfigManager | None = None


def config() -> ConfigManager:
    global _config
    if _config is None:
        _config = ConfigManager()
    return _config
