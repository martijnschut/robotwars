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
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 5)
    g.tick()
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (3, 6)
    assert len(g.spelers[1].wachtrij) == 0


def test_omhoog_is_y_plus_1_en_omlaag_y_min_1():
    """Het veld is een assenstelsel: y loopt van onder (1) naar boven (7)."""
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 5)
    g.voeg_stappen_toe(1, [Move("omlaag"), Move("omlaag")])
    g.tick()
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 3)
    g.voeg_stappen_toe(2, [Move("omlaag")])
    g.tick()
    assert (g.spelers[2].x, g.spelers[2].y) == (12, 3)


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
    g.spelers[1].x, g.spelers[1].y = 2, HOOGTE
    g.voeg_stappen_toe(1, [Move("omhoog")])      # boven rij 7 is niets
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, HOOGTE)
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.voeg_stappen_toe(1, [Move("omlaag")])      # onder rij 1 ook niet
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


from app.game import Schild, RESPAWN_TIKKEN, SCHILD_LEVENS
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
    assert g.schild_op(4, 2).levens == SCHILD_LEVENS - 1


def test_schild_verdwijnt_na_acht_treffers():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 2
    g.schilden.append(Schild(4, 2, eigenaar=1))
    g.voeg_stappen_toe(1, [Shoot()] * SCHILD_LEVENS)
    for _ in range(SCHILD_LEVENS - 1):
        g.tick()
    assert g.schild_op(4, 2).levens == 1
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


from app.game import (MELD_OP, MELD_BESTAAT_NIET, MELD_HELFT, MELD_STARTVAK,
                      MELD_BEZET, MAX_WACHTRIJ)
from app.parser import Shield as ShieldCmd


def zet(g, nummer, x, y):
    g.spelers[nummer].melding = None      # de server wist meldingen na het tonen; hier doen we dat zelf
    g.voeg_stappen_toe(nummer, [ShieldCmd(x, y)])
    g.tick()
    return g.spelers[nummer].melding


def test_schild_zetten_op_eigen_helft():
    g = nieuw()
    assert zet(g, 1, 4, 3) is None
    assert g.schild_op(4, 3).eigenaar == 1
    assert g.spelers[1].schilden_over == 2
    assert zet(g, 2, 11, 5) is None
    assert g.spelers[2].schilden_over == 2


def test_schild_niet_op_andere_helft_of_rivier():
    g = nieuw()
    assert zet(g, 1, 9, 3) == MELD_HELFT
    assert zet(g, 1, 7, 2) == MELD_HELFT
    assert zet(g, 2, 4, 3) == MELD_HELFT
    assert g.spelers[1].schilden_over == 3     # geweigerd telt niet


def test_schild_niet_buiten_veld_startvak_of_bezet():
    g = nieuw()
    assert zet(g, 1, 0, 3) == MELD_BESTAAT_NIET
    assert zet(g, 1, 2, 4) == MELD_STARTVAK
    assert zet(g, 1, 1, 4) == MELD_BEZET       # gebouw
    g.spelers[2].x, g.spelers[2].y = 5, 5
    assert zet(g, 1, 5, 5) == MELD_BEZET       # robot
    assert zet(g, 1, 4, 3) is None
    assert zet(g, 1, 4, 3) == MELD_BEZET       # al een schild


def test_maximaal_drie_schilden():
    g = nieuw()
    for y in (1, 2, 3):
        assert zet(g, 1, 4, y) is None
    assert zet(g, 1, 4, 5) == MELD_OP


def test_wachtrij_maximaal_50():
    g = nieuw()
    assert g.voeg_stappen_toe(1, [Move("omhoog")] * MAX_WACHTRIJ)
    assert not g.voeg_stappen_toe(1, [Move("omhoog")])
    assert len(g.spelers[1].wachtrij) == MAX_WACHTRIJ
    g.stop(1)
    assert len(g.spelers[1].wachtrij) == 0


def test_zet_schild_wist_oude_foutmelding_bij_succes():
    g = nieuw()
    g.voeg_stappen_toe(1, [ShieldCmd(9, 3)])       # geweigerd: andere helft
    g.tick()
    assert g.spelers[1].melding == MELD_HELFT
    g.voeg_stappen_toe(1, [ShieldCmd(4, 3)])       # geslaagd
    g.tick()
    assert g.spelers[1].melding is None


# ---- gebeurtenissenlog ----

from app.game import Gebeurtenis


def soorten(g):
    return [e.soort for _, e in g.log]


def test_log_loop_en_geblokkeerd():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("vooruit"), Move("achteruit"), Move("achteruit")])
    g.tick()
    assert g.log[-1] == (1, Gebeurtenis("loop", 1, 3, 4, tekst="vooruit"))
    g.tick()
    g.tick()                                     # (1,4) is het gebouw: geblokkeerd
    assert g.log[-1] == (3, Gebeurtenis("geblokkeerd", 1, tekst="achteruit"))
    assert soorten(g) == ["loop", "loop", "geblokkeerd"]


def test_log_schot_raakt_robot_schild_gebouw_of_mist():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 4, 3
    g.spelers[2].x, g.spelers[2].y = 6, 3
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.log[-1] == (1, Gebeurtenis("raak_robot", 1, 6, 3, doel=2, levens=4))
    g.schilden.append(Schild(5, 3, eigenaar=1))
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.log[-1] == (2, Gebeurtenis("raak_schild", 1, 5, 3, doel=1, levens=SCHILD_LEVENS - 1))
    g.spelers[1].x, g.spelers[1].y = 9, 4
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.log[-1] == (3, Gebeurtenis("raak_gebouw", 1, 13, 4, doel=2, levens=4))
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.log[-1] == (4, Gebeurtenis("mis", 1, 6, 1))


def test_log_dood_en_terug():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 8, 1
    g.spelers[2].x, g.spelers[2].y = 10, 1
    g.spelers[2].robot_levens = 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert soorten(g)[-2:] == ["raak_robot", "dood"]
    assert g.log[-1] == (1, Gebeurtenis("dood", 2, 10, 1))
    for _ in range(RESPAWN_TIKKEN):
        g.tick()
    assert g.log[-1] == (1 + RESPAWN_TIKKEN, Gebeurtenis("terug", 2, 12, 4))


def test_log_schild_gezet_of_geweigerd():
    g = nieuw()
    g.voeg_stappen_toe(1, [ShieldCmd(4, 3), ShieldCmd(9, 3)])
    g.tick()
    assert g.log[-1] == (1, Gebeurtenis("schild", 1, 4, 3))
    g.tick()
    assert g.log[-1] == (2, Gebeurtenis("schild_fout", 1, 9, 3, tekst=MELD_HELFT))


def test_log_win_en_maxlen():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 9, 4
    g.spelers[2].x, g.spelers[2].y = 12, 1
    g.spelers[2].gebouw_levens = 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert soorten(g)[-2:] == ["raak_gebouw", "win"]
    assert g.log[-1] == (1, Gebeurtenis("win", 1))
    assert g.log.maxlen == 30
    g2 = nieuw()
    g2.voeg_stappen_toe(1, [Move("omhoog"), Move("omlaag")] * 25)
    for _ in range(50):
        g2.tick()
    assert len(g2.log) == 30 and g2.log[-1][0] == 50


# ---- bommen en mijnen ----

from app.game import Mijn, BOMMEN_PER_SPELER, MELD_BOMMEN_OP, MELD_WATER
from app.parser import Bomb


def leg(g, nummer, dx, dy):
    g.spelers[nummer].melding = None
    g.voeg_stappen_toe(nummer, [Bomb(dx, dy)])
    g.tick()
    return g.spelers[nummer].melding


def test_bom_op_leeg_vak_blijft_liggen_als_mijn():
    g = nieuw()
    assert g.spelers[1].bommen_over == BOMMEN_PER_SPELER == 3
    assert leg(g, 1, 1, 1) is None                     # robot op (2,4) → mijn op (3,5)
    assert g.mijn_op(3, 5) == Mijn(3, 5, eigenaar=1)
    assert g.spelers[1].bommen_over == 2
    assert g.knallen == []
    assert g.log[-1] == (1, Gebeurtenis("bom", 1, 3, 5))


def test_mijn_blokkeert_lopen_niet_maar_robot_gaat_kapot():
    g = nieuw()
    g.mijnen.append(Mijn(3, 4, eigenaar=2))
    g.voeg_stappen_toe(1, [Move("vooruit"), Move("vooruit")])
    g.tick()
    s1 = g.spelers[1]
    assert (s1.x, s1.y) == (3, 4)                      # hij kwam er wel
    assert not s1.leeft and s1.respawn_over == RESPAWN_TIKKEN
    assert len(s1.wachtrij) == 0
    assert g.mijn_op(3, 4) is None                     # mijn is weg
    assert g.knallen == [(3, 4)]
    assert soorten(g)[-3:] == ["loop", "mijn_raak", "dood"]
    assert g.log[-2] == (1, Gebeurtenis("mijn_raak", 1, 3, 4, doel=2))
    for _ in range(RESPAWN_TIKKEN):
        g.tick()
    assert s1.leeft and (s1.x, s1.y) == (2, 4)


def test_eigen_mijn_is_ook_gevaarlijk():
    g = nieuw()
    g.mijnen.append(Mijn(3, 4, eigenaar=1))
    g.voeg_stappen_toe(1, [Move("vooruit")])
    g.tick()
    assert not g.spelers[1].leeft
    assert g.log[-2] == (1, Gebeurtenis("mijn_raak", 1, 3, 4, doel=1))


def test_bom_op_tegenstander_is_meteen_kapot():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 8, 3
    g.spelers[2].x, g.spelers[2].y = 9, 4
    assert leg(g, 1, 1, 1) is None
    s2 = g.spelers[2]
    assert not s2.leeft and s2.respawn_over == RESPAWN_TIKKEN
    assert g.mijn_op(9, 4) is None                     # geen mijn achtergebleven
    assert g.knallen == [(9, 4)]
    assert g.spelers[1].bommen_over == 2
    assert soorten(g)[-2:] == ["bom_raak", "dood"]
    assert g.log[-2] == (1, Gebeurtenis("bom_raak", 1, 9, 4, doel=2))


def test_bom_op_eigen_vak_blaast_jezelf_op():
    g = nieuw()
    assert leg(g, 1, 0, 0) is None                     # (2,4) is een startvak, maar er staat een robot
    assert not g.spelers[1].leeft
    assert g.log[-2] == (1, Gebeurtenis("bom_raak", 1, 2, 4, doel=1))


def test_bom_op_tegenstander_op_zijn_startvak_mag():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 11, 3
    assert leg(g, 1, 1, 1) is None                     # (12,4): startvak, robot 2 staat erop
    assert not g.spelers[2].leeft
    assert g.mijn_op(12, 4) is None


def test_bom_op_mijn_laat_beide_knallen_zonder_gewonden():
    g = nieuw()
    g.mijnen.append(Mijn(3, 4, eigenaar=2))
    assert leg(g, 1, 1, 0) is None
    assert g.mijnen == []
    assert g.spelers[1].leeft and g.spelers[2].leeft
    assert g.spelers[1].bommen_over == 2
    assert g.knallen == [(3, 4)]
    assert g.log[-1] == (1, Gebeurtenis("mijn_dubbel", 1, 3, 4, doel=2))


def test_knallen_worden_per_tik_geleegd():
    g = nieuw()
    leg(g, 1, 1, 1)                                    # mijn op (3,5)
    leg(g, 1, 1, 1)                                    # tweede bom erop: beide knallen
    assert g.knallen == [(3, 5)]
    g.tick()
    assert g.knallen == []


def test_bom_mag_op_brug_en_op_andere_helft():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 6, 2
    assert leg(g, 1, 1, 0) is None                     # brug (7,2)
    assert g.mijn_op(7, 2) is not None
    g.spelers[1].x, g.spelers[1].y = 7, 2
    assert leg(g, 1, 1, 0) is None                     # (8,2): helft van speler 2
    assert g.mijn_op(8, 2) is not None


def test_bom_geweigerd_en_niet_verbruikt():
    g = nieuw()
    s1 = g.spelers[1]
    s1.x, s1.y = 1, 1
    assert leg(g, 1, -1, 0) == MELD_BESTAAT_NIET       # (0,1)
    assert leg(g, 1, 0, -1) == MELD_BESTAAT_NIET       # (1,0)
    s1.x, s1.y = 6, 3
    assert leg(g, 1, 1, 0) == MELD_WATER               # (7,3)
    s1.x, s1.y = 2, 3
    assert leg(g, 1, -1, 1) == MELD_BEZET              # (1,4) gebouw
    assert leg(g, 1, 0, 1) == MELD_STARTVAK            # (2,4)
    g.schilden.append(Schild(3, 3, eigenaar=1))
    assert leg(g, 1, 1, 0) == MELD_BEZET               # schild
    assert s1.bommen_over == 3
    assert g.mijnen == []
    assert g.log[-1] == (6, Gebeurtenis("bom_fout", 1, 3, 3, tekst=MELD_BEZET))
    s1.bommen_over = 0
    assert leg(g, 1, 1, 1) == MELD_BOMMEN_OP


def test_kogel_vliegt_over_mijn_heen():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 8, 1
    g.spelers[2].x, g.spelers[2].y = 10, 1
    g.mijnen.append(Mijn(9, 1, eigenaar=2))
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.spelers[2].robot_levens == 4
    assert g.mijn_op(9, 1) is not None


def test_dode_robot_legt_geen_bom():
    g = nieuw()
    g.spelers[1].robot_levens = 0
    g.spelers[1].respawn_over = RESPAWN_TIKKEN
    g.voeg_stappen_toe(1, [Bomb(1, 0)])
    g.tick()
    assert g.mijnen == [] and g.spelers[1].bommen_over == 3


def test_speler_2_legt_bom_in_echte_veldrichting():
    g = nieuw()
    assert leg(g, 2, -1, 0) is None                    # dx is hier al gespiegeld (de editor doet dat)
    assert g.mijn_op(11, 4) == Mijn(11, 4, eigenaar=2)
    assert g.spelers[2].bommen_over == 2
