"""Scorebord in SQLite. Alleen echte overwinningen (gebouw op 0) komen hierin."""
from __future__ import annotations

import sqlite3
from datetime import datetime


class ScoreDb:
    def __init__(self, pad: str = "robotwars.db") -> None:
        self.conn = sqlite3.connect(pad, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS scores (
                 id INTEGER PRIMARY KEY,
                 winnaar TEXT NOT NULL,
                 verliezer TEXT NOT NULL,
                 tegen_computer INTEGER NOT NULL,
                 seconden INTEGER NOT NULL,
                 gespeeld_op TEXT NOT NULL)"""
        )
        self.conn.commit()

    def sla_op(self, winnaar: str, verliezer: str, tegen_computer: bool,
               seconden: int, wanneer: datetime | None = None) -> None:
        wanneer = wanneer or datetime.now()
        self.conn.execute(
            "INSERT INTO scores (winnaar, verliezer, tegen_computer, seconden, gespeeld_op)"
            " VALUES (?, ?, ?, ?, ?)",
            (winnaar, verliezer, int(tegen_computer), seconden, wanneer.isoformat(timespec="seconds")),
        )
        self.conn.commit()

    def top(self, tegen_computer: bool, limiet: int = 10) -> list[dict]:
        rijen = self.conn.execute(
            "SELECT winnaar, verliezer, seconden, gespeeld_op FROM scores"
            " WHERE tegen_computer = ? ORDER BY seconden ASC, id ASC LIMIT ?",
            (int(tegen_computer), limiet),
        ).fetchall()
        return [dict(r) for r in rijen]
