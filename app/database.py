"""任务数据的 SQLite 持久化层。

任务表字段：
    id, title, notes, date(YYYY-MM-DD), time(HH:MM 或空),
    priority(0低/1中/2高), category, done(0/1),
    remind_min(提前提醒分钟, -1 表示不提醒), created_at, updated_at
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .config import app_data_dir

PRIORITY_LABELS = {0: "低", 1: "中", 2: "高"}
PRIORITY_COLORS = {0: "#7c9cbf", 1: "#e0a458", 2: "#e56a54"}


@dataclass
class Task:
    id: int | None = None
    title: str = ""
    notes: str = ""
    date: str = ""                                  # YYYY-MM-DD
    time: str = ""                                  # HH:MM
    priority: int = 1
    category: str = "默认"
    done: bool = False
    remind_min: int = 0
    created_at: str = ""
    updated_at: str = ""

    @property
    def priority_label(self) -> str:
        return PRIORITY_LABELS.get(self.priority, "中")

    @property
    def priority_color(self) -> str:
        return PRIORITY_COLORS.get(self.priority, "#e0a458")

    @property
    def datetime_str(self) -> str:
        if self.time:
            return f"{self.date} {self.time}"
        return self.date


class TaskRepository:
    """任务数据访问对象。"""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or (app_data_dir() / "tasks.db")
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    # ------------------------------------------------------------------
    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                notes       TEXT    DEFAULT '',
                date        TEXT    NOT NULL,
                time        TEXT    DEFAULT '',
                priority    INTEGER DEFAULT 1,
                category    TEXT    DEFAULT '默认',
                done        INTEGER DEFAULT 0,
                remind_min  INTEGER DEFAULT 0,
                created_at  TEXT    DEFAULT '',
                updated_at  TEXT    DEFAULT ''
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_date ON tasks(date)"
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            notes=row["notes"] or "",
            date=row["date"],
            time=row["time"] or "",
            priority=row["priority"],
            category=row["category"] or "默认",
            done=bool(row["done"]),
            remind_min=row["remind_min"],
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
        )

    def add(self, task: Task) -> int:
        now = dt.datetime.now().isoformat(timespec="seconds")
        task.created_at = task.created_at or now
        task.updated_at = now
        cur = self._conn.execute(
            """INSERT INTO tasks
               (title, notes, date, time, priority, category, done, remind_min,
                created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                task.title, task.notes, task.date, task.time, task.priority,
                task.category, int(task.done), task.remind_min,
                task.created_at, task.updated_at,
            ),
        )
        self._conn.commit()
        task.id = int(cur.lastrowid)
        return task.id

    def update(self, task: Task) -> None:
        if task.id is None:
            return
        task.updated_at = dt.datetime.now().isoformat(timespec="seconds")
        self._conn.execute(
            """UPDATE tasks SET title=?, notes=?, date=?, time=?, priority=?,
               category=?, done=?, remind_min=?, updated_at=? WHERE id=?""",
            (
                task.title, task.notes, task.date, task.time, task.priority,
                task.category, int(task.done), task.remind_min,
                task.updated_at, task.id,
            ),
        )
        self._conn.commit()

    def delete(self, task_id: int) -> None:
        self._conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self._conn.commit()

    def toggle_done(self, task_id: int) -> bool:
        row = self._conn.execute(
            "SELECT done FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
        if row is None:
            return False
        new_val = 0 if row["done"] else 1
        self._conn.execute(
            "UPDATE tasks SET done=?, updated_at=? WHERE id=?",
            (new_val, dt.datetime.now().isoformat(timespec="seconds"), task_id),
        )
        self._conn.commit()
        return bool(new_val)

    # ------------------------------------------------------------------
    def by_date(self, date_str: str) -> list[Task]:
        rows = self._conn.execute(
            """SELECT * FROM tasks WHERE date=? 
               ORDER BY done ASC, 
                        CASE WHEN time='' THEN 1 ELSE 0 END, 
                        time ASC, priority DESC, id ASC""",
            (date_str,),
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def by_range(self, start: str, end: str) -> list[Task]:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE date BETWEEN ? AND ? ORDER BY date, time",
            (start, end),
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def all(self) -> list[Task]:
        rows = self._conn.execute(
            "SELECT * FROM tasks ORDER BY date DESC, time"
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def dates_with_tasks(self, year: int, month: int) -> dict[str, int]:
        """返回该月每一天的任务数量，用于日历标记。"""
        prefix = f"{year:04d}-{month:02d}-"
        rows = self._conn.execute(
            "SELECT date, COUNT(*) AS c FROM tasks WHERE date LIKE ? GROUP BY date",
            (prefix + "%",),
        ).fetchall()
        return {r["date"]: r["c"] for r in rows}

    def today(self, date_str: str | None = None) -> list[Task]:
        date_str = date_str or dt.date.today().isoformat()
        return self.by_date(date_str)

    def stats(self, date_str: str) -> tuple[int, int]:
        """返回 (完成数, 总数)。"""
        tasks = self.by_date(date_str)
        total = len(tasks)
        done = sum(1 for t in tasks if t.done)
        return done, total

    def upcoming(self, minutes: int = 60) -> list[Task]:
        """返回未来 minutes 分钟内需要提醒的任务。"""
        now = dt.datetime.now()
        limit = now + dt.timedelta(minutes=minutes)
        result: list[Task] = []
        for t in self.by_date(now.date().isoformat()):
            if t.done or not t.time or t.remind_min < 0:
                continue
            try:
                hh, mm = map(int, t.time.split(":"))
                when = dt.datetime.combine(now.date(), dt.time(hh, mm))
            except (ValueError, TypeError):
                continue
            remind_at = when - dt.timedelta(minutes=max(0, t.remind_min))
            if now <= remind_at <= limit:
                result.append(t)
        return result

    def close(self) -> None:
        try:
            self._conn.close()
        except sqlite3.Error:
            pass
