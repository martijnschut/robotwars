from app.weergave import (veld_matrix, kolommen, kogelbanen, STAP_SECONDEN, mmss, datum, hartjes, kleur, symbool,
                          log_regels)
from app.game import Game, Schild, Gebeurtenis, MELD_HELFT
from app.parser import Shoot


def test_kolommen_gespiegeld_voor_speler_2():
    assert list(kolommen(1))[:3] == [1, 2, 3]
    assert list(kolommen(2))[:3] == [13, 12, 11]


def test_matrix_soorten_en_inhoud():
    g = Game("g", "A", "B")
    g.schilden.append(Schild(4, 3, eigenaar=1))
    rijen = veld_matrix(g, ik=1)
    assert len(rijen) == 7 and len(rijen[0]) == 13
    cel = rijen[3][0]                       # (1,4): gebouw speler 1
    assert (cel.x, cel.y) == (1, 4) and cel.soort == "b" and cel.gebouw.nummer == 1
    assert rijen[3][1].robot.nummer == 1    # (2,4)
    assert rijen[3][11].robot.nummer == 2   # (12,4)
    assert rijen[2][3].schild.eigenaar == 1 # (4,3)
    assert rijen[0][6].soort == "w" and rijen[1][6].soort == "br"
    assert rijen[0][7].soort == "r"
    # gespiegeld: eerste kolom is x=13
    assert veld_matrix(g, ik=2)[3][0].gebouw.nummer == 2


def test_matrix_toont_kogelbaan():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()                                # niets geraakt: kogel eindigt op (6,1)
    rijen = veld_matrix(g, 1)
    assert [c.spoor for c in rijen[0][2:6]] == [True] * 4
    assert [c.spoor_index for c in rijen[0][2:6]] == [0, 1, 2, 3]
    assert not rijen[0][5].raak                    # mis: nergens een knal
    g.spelers[2].x, g.spelers[2].y = 4, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    rijen = veld_matrix(g, 1)
    assert rijen[0][3].raak and rijen[0][3].robot.nummer == 2
    # de vakjes van de baan flitsen in golf: vertraging loopt op per vakje
    assert rijen[0][2].spoor_index == 0 and rijen[0][3].spoor_index == 1
    assert rijen[0][3].knal_vertraging == round(2 * STAP_SECONDEN, 2)


def test_logtekst_toont_kolommen_vanuit_eigen_kant():
    g = Game("g", "Wessel", "Papa")
    g.log.append((1, Gebeurtenis("loop", 2, x=11, y=3, tekst="vooruit")))
    g.log.append((1, Gebeurtenis("schild", 2, x=10, y=3)))
    assert log_regels(g, 2)[1]["tekst"] == "Jij loopt vooruit naar (3, 3)"
    assert log_regels(g, 2)[0]["tekst"] == "Jij zet een schild op (4, 3)"
    assert log_regels(g, 1)[1]["tekst"] == "Papa loopt vooruit naar (11, 3)"


def test_kogelbanen_vliegen_over_het_scherm():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()                                # mis: cellen (3,1)..(6,1)
    (baan,) = kogelbanen(g, 1)
    # speler 1 kijkt normaal: schutter op schermkolom 2, eind op 6; gridkolom = schermkolom + 1
    assert baan == {"kol_van": 3, "kol_tot": 8, "rij": 2, "n": 5, "richting": "rechts",
                    "duur": round(4 * STAP_SECONDEN, 2), "schutter": 1, "raak": False}
    # speler 2 ziet het gespiegeld: x=2 wordt schermkolom 12, x=6 wordt 8 → kogel vliegt naar links
    (baan2,) = kogelbanen(g, 2)
    assert baan2["kol_van"] == 9 and baan2["kol_tot"] == 14 and baan2["richting"] == "links"
    # treffer op afstand 2: n = 3 (schutter + 2 vakjes), raak True
    g.spelers[2].x, g.spelers[2].y = 4, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    (baan3,) = kogelbanen(g, 1)
    assert baan3["n"] == 3 and baan3["raak"] is True and baan3["kol_tot"] == 6
    assert kogelbanen(Game("leeg", "A", "B"), 1) == []
    g.spelers[2].gebouw_levens = 1
    g.spelers[1].x, g.spelers[1].y = 9, 4
    g.spelers[2].x, g.spelers[2].y = 12, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()                                # winnend schot
    assert g.afgelopen and g.schoten and kogelbanen(g, 1) == []


def test_filters():
    assert mmss(83) == "1:23" and mmss(5) == "0:05"
    assert datum("2026-09-20T10:00:00") == "20 sep"
    assert hartjes(3, 5) == "❤️❤️❤️🖤🖤"
    assert kleur(1) == "gb" and kleur(2) == "gr"
    assert symbool("ok") == "✓" and symbool("wacht") == "…" and symbool("fout") == "!" and symbool("") == ""


# ---- log "Wat gebeurt er?" ----

def spel_met_log():
    g = Game("g", "Wessel", "Robo")
    for tik, e in [
        (1, Gebeurtenis("loop", 1, 6, 2, tekst="vooruit")),
        (2, Gebeurtenis("geblokkeerd", 2, tekst="omhoog")),
        (3, Gebeurtenis("raak_robot", 2, 6, 2, doel=1, levens=3)),
        (4, Gebeurtenis("raak_robot", 1, 8, 2, doel=2, levens=4)),
        (5, Gebeurtenis("raak_schild", 1, 9, 2, doel=2, levens=2)),
        (6, Gebeurtenis("raak_gebouw", 2, 1, 4, doel=1, levens=4)),
        (7, Gebeurtenis("mis", 1, 10, 2)),
        (8, Gebeurtenis("raak_robot", 2, 6, 2, doel=1, levens=0)),
        (8, Gebeurtenis("dood", 1, 6, 2)),
        (9, Gebeurtenis("dood", 2, 8, 2)),
        (11, Gebeurtenis("terug", 1, 2, 4)),
        (12, Gebeurtenis("schild", 1, 4, 3)),
        (13, Gebeurtenis("schild_fout", 1, 9, 3, tekst=MELD_HELFT)),
        (75, Gebeurtenis("win", 1)),
    ]:
        g.log.append((tik, e))
    return g


def test_log_regels_vanuit_speler_1():
    g = spel_met_log()
    regels = log_regels(g, 1, aantal=99)
    assert [r["tekst"] for r in regels] == [
        "🏆 Jij wint!",
        f"Schild geweigerd: {MELD_HELFT}",
        "Jij zet een schild op (4, 3)",
        "Je robot is terug op het startvak",
        "💥 De robot van Robo is kapot!",
        "💥 Je robot is kapot! Hij komt terug over 3 seconden",
        "Robo schiet → raakt jou! 🖤🖤🖤🖤🖤",
        "Jij schiet → mis",
        "Robo raakt jouw toren! 🏰 ❤️❤️❤️❤️🖤",
        "Jij schiet → raakt het schild van Robo (nog 2)",
        "Jij schiet → raakt Robo! ❤️❤️❤️❤️🖤",
        "Robo schiet → raakt jou! ❤️❤️❤️🖤🖤",
        "Robo loopt tegen iets aan en blijft staan",
        "Jij loopt vooruit naar (6, 2)",
    ]
    assert regels[0] == {"tik": 75, "tijd": "1:15", "tekst": "🏆 Jij wint!", "soort": "win", "mij": True}
    assert regels[-1]["tijd"] == "0:01" and regels[-1]["mij"] is True
    assert regels[-2]["mij"] is False and regels[-2]["soort"] == "geblokkeerd"
    assert regels[5]["soort"] == "dood" and regels[5]["mij"] is True
    assert regels[4]["mij"] is False


def test_log_regels_vanuit_speler_2():
    g = spel_met_log()
    regels = log_regels(g, 2, aantal=99)
    teksten = [r["tekst"] for r in regels]
    assert teksten[0] == "🏆 Wessel wint!"
    assert teksten[-1] == "Wessel loopt vooruit naar (8, 2)"   # x=6 gezien vanaf de kant van speler 2
    assert teksten[-2] == "Jij loopt tegen iets aan en blijft staan"
    assert teksten[-3] == "Jij schiet → raakt Wessel! ❤️❤️❤️🖤🖤"
    assert teksten[-4] == "Wessel schiet → raakt jou! ❤️❤️❤️❤️🖤"
    assert teksten[-5] == "Wessel schiet → raakt jouw schild (nog 2)"
    assert teksten[-6] == "Jij raakt de toren van Wessel! 🏰 ❤️❤️❤️❤️🖤"
    assert teksten[-7] == "Wessel schiet → mis"
    assert "Je robot is kapot" in teksten[4] and regels[4]["mij"] is True
    assert regels[0]["mij"] is False and regels[-1]["mij"] is False


def test_log_regels_nieuwste_eerst_en_maximaal_aantal():
    g = spel_met_log()
    regels = log_regels(g, 1, aantal=3)
    assert [r["tijd"] for r in regels] == ["1:15", "0:13", "0:12"]
    assert log_regels(g, 1) and len(log_regels(g, 1)) == 10
    assert log_regels(Game("leeg", "A", "B"), 1) == []

