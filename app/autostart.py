"""Windows 开机自启动管理（写入 HKCU\\...\\Run 注册表项）。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import winreg  # type: ignore
except ImportError:  # 非 Windows 平台
    winreg = None  # type: ignore

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "RestBuddy"


def _launch_command() -> str:
    """构造开机启动命令行。

    打包成 exe 时直接使用 exe 路径；否则回退到 pythonw + main.py。
    """
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'

    root = Path(__file__).resolve().parent.parent
    main_py = root / "main.py"
    exe = Path(sys.executable)
    pythonw = exe.with_name("pythonw.exe")
    launcher = pythonw if pythonw.exists() else exe
    return f'"{launcher}" "{main_py}"'


def is_enabled() -> bool:
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, APP_REG_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable() -> tuple[bool, str]:
    if winreg is None:
        return False, "当前系统不支持注册表自启动（非 Windows）"
    try:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                                winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ,
                              _launch_command())
        return True, "已开启开机自启动"
    except OSError as exc:
        return False, f"写入注册表失败：{exc}"


def disable() -> tuple[bool, str]:
    if winreg is None:
        return False, "当前系统不支持注册表自启动（非 Windows）"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_REG_NAME)
        return True, "已关闭开机自启动"
    except FileNotFoundError:
        return True, "开机自启动本就未开启"
    except OSError as exc:
        return False, f"删除注册表项失败：{exc}"
