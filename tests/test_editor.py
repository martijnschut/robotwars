from app.editor import (Editor, Regel, HINT_KLAAR, HINT_TE_DIEP, HINT_TE_VEEL, MAX_DIEPTE, MAX_REGELS,
                        MAX_REGEL_LENGTE)
from app.game import Game, MELD_DRUK, MAX_WACHTRIJ
from app.parser import Move, Shoot, Aim


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
    for tekst in ("herhaal 2 keer", "robot = omhoog", "herhaal 2 keer", "kanon = 180", "robot = schiet", "klaar"):
        e.verwerk(g, 1, tekst)
    assert e.markering == "wacht"                  # buitenste blok nog open
    assert e.regels[3].inspringing == 2
    e.verwerk(g, 1, "klaar")
    assert list(g.spelers[1].wachtrij) == [Move("omhoog"), Aim(180), Shoot(), Aim(180), Shoot()] * 2


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
    g.voeg_stappen_toe(1, [Move("omhoog")] * MAX_WACHTRIJ)
    assert e.verwerk(g, 1, "robot = vooruit") is False
    assert e.markering == "fout" and e.hint == MELD_DRUK


def test_schild_van_speler_2_wordt_gespiegeld_naar_veldcoordinaten():
    from app.parser import Shield
    g, e = nieuw()
    e.verwerk(g, 1, "schild = (4, 3)")
    assert list(g.spelers[1].wachtrij) == [Shield(4, 3)]
    e2 = Editor()
    e2.verwerk(g, 2, "schild = (4, 3)")               # speler 2 telt vanaf zijn eigen kant
    assert list(g.spelers[2].wachtrij) == [Shield(10, 3)]
    assert e2.regels[-1].tekst == "schild = (4, 3)"    # de getypte regel blijft zoals getypt


def test_bom_dx_is_vooruit_dus_gespiegeld_voor_speler_2():
    from app.parser import Bomb
    g, e = nieuw()
    e.verwerk(g, 1, "bom = (1, -1)")
    assert list(g.spelers[1].wachtrij) == [Bomb(1, -1)]
    e2 = Editor()
    e2.verwerk(g, 2, "bom = (1, -1)")                  # vooruit is voor speler 2 kolom -1
    assert list(g.spelers[2].wachtrij) == [Bomb(-1, -1)]
    e2.verwerk(g, 2, "bom = (0, 1)")
    assert list(g.spelers[2].wachtrij)[-1] == Bomb(0, 1)
    assert e2.regels[-1].tekst == "bom = (0, 1)"       # de getypte regel blijft zoals getypt


def test_wis_maakt_regels_leeg():
    g, e = nieuw()
    e.verwerk(g, 1, "robot = vooruit")
    e.wis()
    assert e.regels == []


def test_herhaal_20_keer_met_zes_regels_past_in_de_wachtrij():
    g, e = nieuw()
    for tekst in ("herhaal 20 keer", "robot=omlaag", "robot=schiet", "robot=omlaag",
                  "robot=omhoog", "robot=schiet", "robot=omhoog", "klaar"):
        e.verwerk(g, 1, tekst)
    assert all(r.markering == "ok" for r in e.regels)
    assert len(g.spelers[1].wachtrij) == 120


def test_te_veel_geneste_stappen_is_fout_met_eigen_melding():
    g, e = nieuw()
    for tekst in ("herhaal 20 keer", "herhaal 20 keer", "herhaal 20 keer",
                  "robot = vooruit", "klaar", "klaar", "klaar"):
        e.verwerk(g, 1, tekst)
    assert e.regels[-1].markering == "fout"
    assert e.hint == HINT_TE_VEEL                    # 8000 stappen: niet "je robot is nog bezig"
    assert len(g.spelers[1].wachtrij) == 0


def test_wis_maakt_ook_open_herhaal_blok_leeg():
    g, e = nieuw()
    e.verwerk(g, 1, "herhaal 2 keer")
    e.verwerk(g, 1, "robot = vooruit")
    e.wis()
    assert e.verwerk(g, 1, "robot = schiet") is True
    assert list(g.spelers[1].wachtrij) == [Shoot()]
    assert e.markering == ""
    assert e.regels == [Regel("ok", "robot = schiet", 0)]


def test_alleen_de_laatste_honderd_regels_blijven_bewaard():
    g, e = nieuw()
    for i in range(MAX_REGELS + 5):
        e.verwerk(g, 1, "robot = schiet")
        g.stop(1)                                   # wachtrij leeg houden
    assert len(e.regels) == MAX_REGELS
    e.verwerk(g, 1, "robot = links")                # fout: niets bevroren, dus niets afgeknipt
    assert len(e.regels) == MAX_REGELS


def test_bevroren_regel_wordt_afgekapt():
    g, e = nieuw()
    e.verwerk(g, 1, "robot = schiet" + " " * 5000)     # spaties: geldig, maar erg lang
    assert len(e.regels) == 1 and len(e.regels[-1].tekst) <= MAX_REGEL_LENGTE


def test_te_diep_nesten_is_fout():
    g, e = nieuw()
    for _ in range(MAX_DIEPTE):
        assert e.verwerk(g, 1, "herhaal 2 keer") is True
    assert e.diepte == MAX_DIEPTE
    assert e.verwerk(g, 1, "herhaal 2 keer") is False
    assert e.markering == "fout" and e.hint == HINT_TE_DIEP
    assert e.diepte == MAX_DIEPTE and len(e.regels) == MAX_DIEPTE


def test_kanon_en_schiet_teken_voor_teken():
    """De editor voert een regel uit zodra hij klopt; onderweg mag niets afgaan of rood worden."""
    g, e = nieuw()
    for regel in ("kanon = 90", "robot = schiet"):
        for i in range(1, len(regel) + 1):
            bevroren = e.verwerk(g, 1, regel[:i])
            assert bevroren is (i == len(regel)), regel[:i]
            assert e.hint is None, regel[:i]
    assert list(g.spelers[1].wachtrij) == [Aim(90), Shoot()]
