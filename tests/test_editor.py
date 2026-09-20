from app.editor import Editor, Regel, HINT_KLAAR
from app.game import Game, MELD_DRUK
from app.parser import Move, Shoot


def nieuw():
    g = Game("g", "Wessel", "Papa")
    return g, Editor()


def test_half_getypt_geen_markering_niets_uitgevoerd():
    g, e = nieuw()
    assert e.verwerk(g, 1, "robot = vo") is False
    assert e.markering == "" and e.hint is None and e.regels == []
    assert len(g.spelers[1].wachtrij) == 0


def test_fout_geeft_markering_en_hint():
    g, e = nieuw()
    assert e.verwerk(g, 1, "robot = links") is False
    assert e.markering == "fout"
    assert "links" in e.hint


def test_geldig_commando_wordt_direct_uitgevoerd_en_bevroren():
    g, e = nieuw()
    assert e.verwerk(g, 1, "robot = vooruit") is True
    assert list(g.spelers[1].wachtrij) == [Move("vooruit")]
    assert e.regels == [Regel("ok", "robot = vooruit", 0)]
    assert e.markering == "" and e.hint is None


def test_herhaal_blok_wordt_pas_bij_klaar_uitgevoerd():
    g, e = nieuw()
    assert e.verwerk(g, 1, "herhaal 3 keer") is True
    assert e.markering == "wacht"
    assert e.regels[-1] == Regel("wacht", "herhaal 3 keer", 0)
    assert e.verwerk(g, 1, "robot = vooruit") is True
    assert e.regels[-1] == Regel("wacht", "robot = vooruit", 1)
    assert len(g.spelers[1].wachtrij) == 0
    assert e.verwerk(g, 1, "klaar") is True
    assert list(g.spelers[1].wachtrij) == [Move("vooruit")] * 3
    assert [r.markering for r in e.regels] == ["ok", "ok", "ok"]
    assert e.regels[-1] == Regel("ok", "klaar", 0)
    assert e.markering == ""


def test_genest_blok():
    g, e = nieuw()
    for tekst in ("herhaal 2 keer", "robot = omhoog", "herhaal 2 keer", "robot = schiet", "klaar"):
        e.verwerk(g, 1, tekst)
    assert e.markering == "wacht"                  # buitenste blok nog open
    assert e.regels[3].inspringing == 2
    e.verwerk(g, 1, "klaar")
    assert list(g.spelers[1].wachtrij) == [Move("omhoog"), Shoot(), Shoot()] * 2


def test_klaar_zonder_herhaal_is_fout():
    g, e = nieuw()
    assert e.verwerk(g, 1, "klaar") is False
    assert e.markering == "fout" and e.hint == HINT_KLAAR


def test_fout_binnen_blok_laat_blok_open():
    g, e = nieuw()
    e.verwerk(g, 1, "herhaal 2 keer")
    assert e.verwerk(g, 1, "robot = links") is False
    assert e.markering == "fout"
    assert e.verwerk(g, 1, "robot = vo") is False
    assert e.markering == "wacht"


def test_volle_wachtrij_weigert_commando():
    g, e = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog")] * 50)
    assert e.verwerk(g, 1, "robot = vooruit") is False
    assert e.markering == "fout" and e.hint == MELD_DRUK


def test_wis_maakt_regels_leeg():
    g, e = nieuw()
    e.verwerk(g, 1, "robot = vooruit")
    e.wis()
    assert e.regels == []
