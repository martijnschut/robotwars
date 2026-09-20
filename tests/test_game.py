from app.game import Game, is_water, in_veld, eigen_helft, BREEDTE, HOOGTE
from app.parser import Move


def nieuw():
    return Game("g1", "Wessel", "Papa")


def test_veldfuncties():
    assert in_veld(1, 1) and in_veld(BREEDTE, HOOGTE)
    assert not in_veld(0, 1) and not in_veld(14, 1) and not in_veld(1, 8)
    assert is_water(7, 1) and is_water(7, 4)
    assert not is_water(7, 2) and not is_water(7, 6)   # bruggen
    assert not is_water(6, 4)
    assert eigen_helft(1, 6) and not eigen_helft(1, 7) and not eigen_helft(1, 8)
    assert eigen_helft(2, 8) and not eigen_helft(2, 7)


def test_startopstelling():
    g = nieuw()
    s1, s2 = g.spelers[1], g.spelers[2]
    assert (s1.x, s1.y) == (2, 4) and s1.gebouw == (1, 4) and s1.richting == 1
    assert (s2.x, s2.y) == (12, 4) and s2.gebouw == (13, 4) and s2.richting == -1
    assert s1.robot_levens == 5 and s1.gebouw_levens == 5 and s1.schilden_over == 3
    assert g.tik == 0 and g.winnaar is None and not g.afgelopen


def test_vooruit_is_richting_tegenstander():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("vooruit")])
    g.voeg_stappen_toe(2, [Move("vooruit")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (3, 4)
    assert (g.spelers[2].x, g.spelers[2].y) == (11, 4)
    assert g.tik == 1


def test_een_stap_per_tik():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog"), Move("omhoog"), Move("vooruit")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 3)
    g.tick()
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (3, 2)
    assert len(g.spelers[1].wachtrij) == 0


def test_niet_het_water_in():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 6, 4
    g.voeg_stappen_toe(1, [Move("vooruit")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (6, 4)


def test_wel_over_de_brug():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 6, 2
    g.voeg_stappen_toe(1, [Move("vooruit"), Move("vooruit")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (7, 2)
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (8, 2)


def test_niet_buiten_het_veld_of_in_gebouw_of_robot():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.voeg_stappen_toe(1, [Move("omhoog")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 1)
    g.spelers[1].x, g.spelers[1].y = 2, 4
    g.voeg_stappen_toe(1, [Move("achteruit")])   # gebouw op (1,4)
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 4)
    g.spelers[2].x, g.spelers[2].y = 3, 4
    g.voeg_stappen_toe(1, [Move("vooruit")])     # andere robot op (3,4)
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 4)
