from app.weergave import veld_matrix, kolommen, mmss, datum, hartjes, kleur, symbool
from app.game import Game, Schild
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
    assert rijen[0][5].kogel == 1 and rijen[0][4].kogel is None
    g.spelers[2].x, g.spelers[2].y = 4, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    rijen = veld_matrix(g, 1)
    assert rijen[0][3].raak and rijen[0][3].robot.nummer == 2


def test_filters():
    assert mmss(83) == "1:23" and mmss(5) == "0:05"
    assert datum("2026-09-20T10:00:00") == "20 sep"
    assert hartjes(3, 5) == "❤️❤️❤️🖤🖤"
    assert kleur(1) == "gb" and kleur(2) == "gr"
    assert symbool("ok") == "✓" and symbool("wacht") == "…" and symbool("fout") == "!" and symbool("") == ""
