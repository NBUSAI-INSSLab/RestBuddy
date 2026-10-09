"""今日小憩 · 程序入口。

功能：定时休息（全屏音乐）、任务日历、当日任务醒目提醒、
      开机自启与启动状态记忆。
运行：python main.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

# 保证以脚本方式运行时能找到 app 包
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import Qt, QSharedMemory  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from app import __app_name__, __version__  # noqa: E402
from app.config import config, app_data_dir  # noqa: E402
from app.main_window import MainWindow  # noqa: E402
from app.theme import build_qss  # noqa: E402


def _install_excepthook() -> None:
    """未捕获异常写入日志文件，便于桌面端排障。"""
    import traceback

    log_path = app_data_dir() / "error.log"

    def hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("\n==== %s ====\n" % dt.datetime.now().isoformat())
                traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
        except OSError:
            pass

    sys.excepthook = hook


def _acquire_single_instance() -> QSharedMemory | None:
    """通过共享内存实现单实例，返回持有对象（避免被回收）。"""
    shm = QSharedMemory("RestBuddy-SingleInstance")
    if shm.attach():
        shm.detach()
    if not shm.create(1):
        return None
    return shm


def main() -> int:
    _install_excepthook()
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("RestBuddy")
    app.setQuitOnLastWindowClosed(False)   # 托盘常驻

    guard = _acquire_single_instance()
    if guard is None:
        from PySide6.QtCore import QTimer
        box = QMessageBox(QMessageBox.Information, __app_name__,
                          "今日小憩已经在运行中，请查看系统托盘。")
        QTimer.singleShot(4000, box.accept)   # 无人值守时自动关闭
        box.exec()
        return 0
    app._guard = guard  # type: ignore[attr-defined]

    conf = config()
    app.setStyleSheet(build_qss(conf.get("theme", "light")))

    window = MainWindow()

    # 用应用 logo 作为任务栏 / 托盘图标
    window.setWindowIcon(QIcon(window._make_logo(128)))

    window.show()
    conf.set("first_run", False)
    conf.save()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
