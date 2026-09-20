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


from app.game import Schild, RESPAWN_TIKKEN
from app.parser import Shoot


def test_schot_raakt_robot_op_afstand_4_niet_op_5():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 4, 3
    g.spelers[2].x, g.spelers[2].y = 8, 3        # afstand 4
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.spelers[2].robot_levens == 4
    assert g.schoten[0].raak == (8, 3)
    assert g.schoten[0].cellen == [(5, 3), (6, 3), (7, 3), (8, 3)]
    g.spelers[2].x = 9                            # afstand 5
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.spelers[2].robot_levens == 4
    assert g.schoten[0].raak is None


def test_schot_stopt_bij_schild():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 2
    g.schilden.append(Schild(4, 2, eigenaar=1))
    g.spelers[2].x, g.spelers[2].y = 5, 2
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.spelers[2].robot_levens == 5
    assert g.schild_op(4, 2).levens == 2


def test_schild_verdwijnt_na_3_treffers():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 2
    g.schilden.append(Schild(4, 2, eigenaar=1))
    g.voeg_stappen_toe(1, [Shoot(), Shoot(), Shoot()])
    for _ in range(3):
        g.tick()
    assert g.schild_op(4, 2) is None


def test_robot_gaat_dood_en_komt_terug_op_startvak():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 8, 1
    g.spelers[2].x, g.spelers[2].y = 10, 1
    g.spelers[2].robot_levens = 1
    g.voeg_stappen_toe(2, [Move("vooruit")])     # wordt gewist bij dood
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    s2 = g.spelers[2]
    assert not s2.leeft and s2.respawn_over == RESPAWN_TIKKEN
    assert len(s2.wachtrij) == 0
    assert g.robot_op(10, 1) is None             # dode robot blokkeert niets
    for _ in range(RESPAWN_TIKKEN):
        g.tick()
    assert s2.leeft and s2.robot_levens == 5 and (s2.x, s2.y) == (12, 4)


def test_respawn_wacht_als_startvak_bezet():
    g = nieuw()
    g.spelers[2].robot_levens = 0
    g.spelers[2].respawn_over = 1
    g.spelers[1].x, g.spelers[1].y = 12, 4       # staat op het startvak van speler 2
    g.tick()
    assert not g.spelers[2].leeft
    g.spelers[1].x = 11
    g.tick()
    assert g.spelers[2].leeft


def test_gebouw_kapot_is_winst():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 9, 4        # 4 vakjes van gebouw (13,4)
    g.spelers[2].x, g.spelers[2].y = 12, 1       # uit de weg
    g.voeg_stappen_toe(1, [Shoot()] * 5)
    for _ in range(4):
        g.tick()
    assert g.spelers[2].gebouw_levens == 1 and not g.afgelopen
    g.tick()
    assert g.spelers[2].gebouw_levens == 0
    assert g.winnaar == 1 and g.afgelopen and g.tik == 5
    g.tick()                                     # na afloop gebeurt niets meer
    assert g.tik == 5


def test_speler_1_wint_bij_gelijktijdige_treffer():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 9, 4
    g.spelers[2].x, g.spelers[2].y = 5, 4
    g.spelers[1].gebouw_levens = 1
    g.spelers[2].gebouw_levens = 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.voeg_stappen_toe(2, [Shoot()])
    g.tick()
    assert g.winnaar == 1 and g.spelers[1].gebouw_levens == 1


def test_geef_op():
    g = nieuw()
    g.geef_op(2)
    assert g.winnaar == 1 and g.opgegeven and g.geeindigd_op is not None
