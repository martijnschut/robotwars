from datetime import datetime
from app.db import ScoreDb


def test_opslaan_en_top_gesorteerd_op_tijd():
    db = ScoreDb(":memory:")
    db.sla_op("Wessel", "Robo", True, 83, datetime(2026, 9, 20, 10, 0))
    db.sla_op("Papa", "Robo", True, 58, datetime(2026, 9, 20, 11, 0))
    db.sla_op("Wessel", "Papa", False, 200, datetime(2026, 9, 20, 12, 0))
    top = db.top(tegen_computer=True)
    assert [(r["winnaar"], r["seconden"]) for r in top] == [("Papa", 58), ("Wessel", 83)]
    assert top[0]["verliezer"] == "Robo"
    assert top[0]["gespeeld_op"].startswith("2026-09-20")
    assert [r["winnaar"] for r in db.top(tegen_computer=False)] == ["Wessel"]


def test_top_maximaal_limiet():
    db = ScoreDb(":memory:")
    for i in range(12):
        db.sla_op("W", "R", True, 100 + i)
    assert len(db.top(True)) == 10
    assert len(db.top(True, limiet=3)) == 3


def test_bestand_blijft_bestaan(tmp_path):
    pad = tmp_path / "scores.db"
    ScoreDb(str(pad)).sla_op("W", "R", True, 5)
    assert ScoreDb(str(pad)).top(True)[0]["seconden"] == 5
