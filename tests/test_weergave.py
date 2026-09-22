from pathlib import Path

from app.weergave import (veld_matrix, kolommen, kogelbanen, STAP_SECONDEN, SCHUINE_STAP_SECONDEN, mmss, datum,
                          hartjes, kleur, symbool, log_regels, schermnaam, KANON_STAPPEN)
from app.game import SCHIET_BEREIK
from app.game import Game, Schild, Gebeurtenis, MELD_HELFT, MELD_BEZET
from app.parser import Shoot


def test_kolommen_gespiegeld_voor_speler_2():
    assert list(kolommen(1))[:3] == [1, 2, 3]
    assert list(kolommen(2))[:3] == [13, 12, 11]


def test_matrix_soorten_en_inhoud():
    g = Game("g", "A", "B")
    g.schilden.append(Schild(4, 3, eigenaar=1))
    rijen = veld_matrix(g, ik=1)
    assert len(rijen) == 7 and len(rijen[0]) == 13
    # assenstelsel: de bovenste rij op het scherm is y=7, de onderste y=1
    assert rijen[0][0].y == 7 and rijen[6][0].y == 1
    assert [rij[0].y for rij in rijen] == [7, 6, 5, 4, 3, 2, 1]
    cel = rijen[3][0]                       # (1,4): gebouw speler 1
    assert (cel.x, cel.y) == (1, 4) and cel.soort == "b" and cel.gebouw.nummer == 1
    assert rijen[3][1].robot.nummer == 1    # (2,4)
    assert rijen[3][11].robot.nummer == 2   # (12,4)
    assert rijen[4][3].schild.eigenaar == 1 # (4,3)
    assert rijen[0][6].soort == "w" and rijen[1][6].soort == "br"   # y=7 water, y=6 brug
    assert rijen[5][6].soort == "br" and rijen[6][6].soort == "w"   # y=2 brug, y=1 water
    assert rijen[0][7].soort == "r"
    # gespiegeld: eerste kolom is x=13
    assert veld_matrix(g, ik=2)[3][0].gebouw.nummer == 2
    assert veld_matrix(g, ik=2)[0][0].y == 7


def test_matrix_toont_kogelbaan():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()                                # niets geraakt: kogel eindigt op (6,1)
    rijen = veld_matrix(g, 1)
    onder = rijen[6]                        # y=1 is de onderste rij op het scherm
    assert [c.spoor for c in onder[2:6]] == [True] * 4
    assert [c.spoor_index for c in onder[2:6]] == [0, 1, 2, 3]
    assert not onder[5].raak                       # mis: nergens een knal
    g.spelers[2].x, g.spelers[2].y = 4, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    onder = veld_matrix(g, 1)[6]
    assert onder[3].raak and onder[3].robot.nummer == 2
    # de vakjes van de baan flitsen in golf: vertraging loopt op per vakje
    assert onder[2].spoor_index == 0 and onder[3].spoor_index == 1
    assert onder[3].knal_vertraging == round(2 * STAP_SECONDEN, 2)


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
    # speler 1 kijkt normaal: schutter op schermkolom 2, eind op 6; gridkolom = schermkolom + 1;
    # y=1 is de onderste veldrij, dus gridrij 7 (y=7 is gridrij 1)
    assert baan == {"kol_van": 3, "kol_tot": 8, "rij_van": 7, "rij_tot": 8, "n": 5, "richting": "rechts",
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
    # schutter op y=7 (bovenste rij) ligt in gridrij 1; y=4 in gridrij 4
    g.spelers[1].x, g.spelers[1].y = 2, 7
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert kogelbanen(g, 1)[0]["rij_van"] == 1
    g.spelers[2].gebouw_levens = 1
    g.spelers[1].x, g.spelers[1].y = 9, 4
    g.spelers[2].x, g.spelers[2].y = 12, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()                                # winnend schot
    assert g.afgelopen and g.schoten and kogelbanen(g, 1) == []


def test_kogelbanen_verticaal():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 3, 2
    g.spelers[1].kanon = 90
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()                                # mis: cellen (3,3)..(3,6)
    (baan,) = kogelbanen(g, 1)
    # één kolom breed (schermkolom 3 → gridkolom 4); schutter op y=2 is gridrij 6, eind y=6 is gridrij 2
    assert baan == {"kol_van": 4, "kol_tot": 5, "rij_van": 2, "rij_tot": 7, "n": 5, "richting": "omhoog",
                    "duur": round(4 * STAP_SECONDEN, 2), "schutter": 1, "raak": False}
    # speler 2 ziet het gespiegeld in x, maar omhoog blijft omhoog
    (baan2,) = kogelbanen(g, 2)
    assert baan2["kol_van"] == 12 and baan2["kol_tot"] == 13 and baan2["richting"] == "omhoog"
    assert baan2["rij_van"] == 2 and baan2["rij_tot"] == 7   # rijen worden niet gespiegeld
    # omlaag, treffer op het vakje eronder: n = 2, gridrijen 6 t/m 7
    g.spelers[2].x, g.spelers[2].y = 3, 1
    g.spelers[1].kanon = 270
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    (baan3,) = kogelbanen(g, 1)
    assert baan3["richting"] == "omlaag" and baan3["n"] == 2 and baan3["raak"] is True
    assert baan3["rij_van"] == 6 and baan3["rij_tot"] == 8 and baan3["kol_van"] == 4


def test_matrix_toont_verticaal_spoor():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 3, 2
    g.spelers[1].kanon = 90
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()                                # mis: cellen (3,3)..(3,6)
    rijen = veld_matrix(g, 1)
    kolom = [rij[2] for rij in rijen]       # schermkolom 3, van y=7 (boven) naar y=1
    assert [c.spoor for c in kolom] == [False, True, True, True, True, False, False]
    assert [c.spoor_index for c in kolom[1:5]] == [3, 2, 1, 0]


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


# ---- bommen ----

from app.game import Mijn, MELD_WATER


def test_matrix_toont_mijn_en_knal():
    g = Game("g", "A", "B")
    g.mijnen.append(Mijn(5, 3, eigenaar=2))
    g.knallen.append((9, 6))
    rijen = veld_matrix(g, ik=1)
    assert rijen[4][4].mijn == Mijn(5, 3, eigenaar=2)     # (5,3): y=3 is gridrij 5
    assert rijen[4][3].mijn is None
    knal = rijen[1][8]                                    # (9,6)
    assert knal.raak and knal.knal_vertraging == 0 and not knal.spoor
    rijen2 = veld_matrix(g, ik=2)                         # gespiegeld: x=5 staat op schermkolom 9
    assert rijen2[4][8].mijn is not None


def test_log_regels_bommen():
    g = Game("g", "Wessel", "Robo")
    for tik, e in [
        (1, Gebeurtenis("bom", 1, 3, 5)),
        (2, Gebeurtenis("bom_fout", 1, 7, 3, tekst=MELD_WATER)),
        (3, Gebeurtenis("bom_raak", 1, 9, 4, doel=2)),
        (4, Gebeurtenis("bom_raak", 2, 8, 4, doel=1)),
        (5, Gebeurtenis("bom_raak", 1, 2, 4, doel=1)),
        (6, Gebeurtenis("mijn_raak", 2, 9, 4, doel=1)),
        (7, Gebeurtenis("mijn_raak", 1, 4, 4, doel=1)),
        (8, Gebeurtenis("mijn_dubbel", 2, 7, 2, doel=1)),
        (9, Gebeurtenis("bom", 2, 10, 3)),
        (10, Gebeurtenis("bom_fout", 2, 13, 4, tekst=MELD_BEZET)),
    ]:
        g.log.append((tik, e))
    oudste_eerst_1 = [r["tekst"] for r in log_regels(g, 1, aantal=99)][::-1]
    assert oudste_eerst_1 == [
        "Jij legt een bom op (3, 5)",
        f"Bom geweigerd: {MELD_WATER}",
        "💥 Jouw bom raakt Robo!",
        "💥 De bom van Robo raakt jou!",
        "💥 Je legt een bom op jezelf!",
        "💥 Robo stapt op een mijn!",
        "💥 Je stapt op een mijn!",
        "Twee mijnen knallen op (7, 2)",
        "Robo legt een bom op (10, 3)",
        "Robo probeert een bom, maar dat mag niet",
    ]
    oudste_eerst_2 = [r["tekst"] for r in log_regels(g, 2, aantal=99)][::-1]
    assert oudste_eerst_2[2:6] == [
        "💥 De bom van Wessel raakt jou!",
        "💥 Jouw bom raakt Wessel!",
        "💥 Wessel legt een bom op zichzelf!",
        "💥 Je stapt op een mijn!",
    ]
    assert oudste_eerst_2[8] == "Jij legt een bom op (4, 3)"   # speler 2 ziet kolommen gespiegeld



def test_kanon_richting_op_het_scherm():
    g = Game("g", "A", "B")
    rijen = veld_matrix(g, 1)
    assert rijen[3][1].kanon == "rechts"      # eigen robot (2,4): 0 = vooruit = naar rechts
    assert rijen[3][11].kanon == "links"      # robot van de ander (12,4) kijkt naar mij toe
    assert rijen[3][0].kanon is None          # geen robot: geen kanon
    rijen2 = veld_matrix(g, 2)
    assert rijen2[3][1].kanon == "rechts"     # speler 2 ziet zijn eigen robot ook links, vooruit = rechts
    assert rijen2[3][11].kanon == "links"
    g.spelers[1].kanon, g.spelers[2].kanon = 90, 180
    assert veld_matrix(g, 1)[3][1].kanon == "omhoog"
    assert veld_matrix(g, 2)[3][11].kanon == "omhoog"    # verticaal spiegelt niet
    assert veld_matrix(g, 1)[3][11].kanon == "rechts"    # achteruit van speler 2, gezien door speler 1
    assert veld_matrix(g, 2)[3][1].kanon == "links"      # … en door speler 2 zelf
    g.spelers[1].kanon = 270
    assert veld_matrix(g, 1)[3][1].kanon == "omlaag"


def test_logtekst_kanon():
    g = Game("g", "Wessel", "Papa")
    g.log.append((1, Gebeurtenis("kanon", 1, graden=90)))
    assert log_regels(g, 1)[0]["tekst"] == "Jij draait je kanon naar 90°"
    assert log_regels(g, 2)[0]["tekst"] == "Wessel draait het kanon naar 90°"


def test_kanon_schuin_op_het_scherm():
    g = Game("g", "A", "B")                   # robots op (2,4) en (12,4)
    g.spelers[1].kanon = g.spelers[2].kanon = 45
    rijen1, rijen2 = veld_matrix(g, 1), veld_matrix(g, 2)
    assert rijen1[3][1].kanon == "rechtsboven"     # eigen robot: 45 = vooruit-omhoog = naar rechtsboven
    assert rijen1[3][11].kanon == "linksboven"     # de ander kijkt naar mij toe, maar ook omhoog
    assert rijen2[3][1].kanon == "rechtsboven"     # speler 2 ziet zijn eigen robot net zo
    assert rijen2[3][11].kanon == "linksboven"
    g.spelers[1].kanon = 135
    assert veld_matrix(g, 1)[3][1].kanon == "linksboven"    # achteruit-omhoog
    g.spelers[1].kanon = 225
    assert veld_matrix(g, 1)[3][1].kanon == "linksonder"    # achteruit-omlaag
    g.spelers[1].kanon = 315
    assert veld_matrix(g, 1)[3][1].kanon == "rechtsonder"   # vooruit-omlaag
    assert veld_matrix(g, 2)[3][11].kanon == "linksonder"   # diezelfde robot bij de ander op het scherm


def test_kogelbanen_schuin():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 3, 2
    g.spelers[1].kanon = 45
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()                                # mis: cellen (4,3)..(7,6), over het water heen
    (baan,) = kogelbanen(g, 1)
    # vierkant blok: gridkolommen 4 t/m 8 (schutter x=3, eind x=7) en gridrijen 2 t/m 6
    assert baan == {"kol_van": 4, "kol_tot": 9, "rij_van": 2, "rij_tot": 7, "n": 5,
                    "richting": "rechtsboven", "duur": round(4 * SCHUINE_STAP_SECONDEN, 2),
                    "schutter": 1, "raak": False}
    # speler 2 ziet het gespiegeld in x: schuin omhoog naar links
    (baan2,) = kogelbanen(g, 2)
    assert baan2["richting"] == "linksboven" and baan2["kol_van"] == 8 and baan2["kol_tot"] == 13
    assert baan2["rij_van"] == 2 and baan2["rij_tot"] == 7      # rijen worden niet gespiegeld
    # schuin omlaag met een treffer op het vakje schuin ernaast: n = 2
    g.spelers[1].kanon = 315
    g.spelers[2].x, g.spelers[2].y = 4, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    (baan3,) = kogelbanen(g, 1)
    assert baan3["richting"] == "rechtsonder" and baan3["n"] == 2 and baan3["raak"] is True
    assert baan3["kol_van"] == 4 and baan3["kol_tot"] == 6 and baan3["rij_van"] == 6 and baan3["rij_tot"] == 8


def test_matrix_toont_schuin_spoor():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 3, 2
    g.spelers[1].kanon = 45
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()                                # mis: cellen (4,3)..(7,6)
    rijen = veld_matrix(g, 1)               # rij 0 is y=7, rij 6 is y=1
    schuin = [rijen[7 - y][x - 1] for x, y in ((4, 3), (5, 4), (6, 5), (7, 6))]
    assert [c.spoor for c in schuin] == [True, True, True, True]
    assert [c.spoor_index for c in schuin] == [0, 1, 2, 3]


def test_elke_schermrichting_heeft_css():
    """Een nieuwe hoek zonder stijl zou onzichtbaar mislukken: driehoekje en kogel
    hebben voor elke richting uit KANON_STAPPEN een eigen regel nodig."""
    css = (Path(__file__).resolve().parents[1] / "app" / "static" / "style.css").read_text(encoding="utf-8")
    richtingen = {schermnaam(dx, dy) for dx, dy in KANON_STAPPEN.values()}
    assert len(richtingen) == 8
    for richting in richtingen:
        assert f".kanon.{richting} " in css, richting
        assert ("@keyframes vlieg-" + richting + " ") in css, richting
        if richting != "rechts":   # rechts is de basisregel van .kogelbaan svg, zonder eigen klasse
            assert f".kogelbaan.{richting} " in css, richting
            assert f".kogelbaan.mis.{richting} " in css, richting


def test_schuine_kogel_vliegt_even_hard_als_een_rechte():
    """Een schuin vakje ligt √2 keer zo ver, dus de kogel doet er ongeveer √2 keer
    zo lang over; anders zou hij schuin harder lijken te gaan."""
    assert SCHUINE_STAP_SECONDEN > STAP_SECONDEN
    assert abs(SCHUINE_STAP_SECONDEN / STAP_SECONDEN - 2 ** 0.5) < 0.1
    # het verste schot moet nog binnen één tik (1 seconde) aankomen, anders mist de 💥
    assert SCHIET_BEREIK * SCHUINE_STAP_SECONDEN < 1


def test_spoor_en_knal_wachten_op_de_schuine_kogel():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 3, 2
    g.spelers[1].kanon = 45
    g.spelers[2].x, g.spelers[2].y = 5, 4        # twee vakjes schuin erboven: raak
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    rijen = veld_matrix(g, 1)
    eerste, raak = rijen[7 - 3][4 - 1], rijen[7 - 4][5 - 1]
    assert eerste.spoor_vertraging == round(SCHUINE_STAP_SECONDEN, 2)
    assert raak.spoor_vertraging == round(2 * SCHUINE_STAP_SECONDEN, 2)
    assert raak.knal_vertraging == round(2 * SCHUINE_STAP_SECONDEN, 2)


def test_spoor_van_een_recht_schot_houdt_de_gewone_stap():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 3, 2
    g.spelers[2].x, g.spelers[2].y = 5, 2
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    rijen = veld_matrix(g, 1)
    assert rijen[7 - 2][4 - 1].spoor_vertraging == round(STAP_SECONDEN, 2)
    assert rijen[7 - 2][5 - 1].knal_vertraging == round(2 * STAP_SECONDEN, 2)
