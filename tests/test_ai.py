from app.ai import kies_stap, SCHILD_VAK
from app.game import Game, Schild
from app.parser import Move, Shoot, Shield


def nieuw():
    return Game("g", "Wessel", "Robo", tegen_computer=True, brein=kies_stap)


def test_schiet_op_robot_in_dezelfde_rij_binnen_bereik():
    g = nieuw()
    g.spelers[2].x, g.spelers[2].y = 10, 3
    g.spelers[1].x, g.spelers[1].y = 6, 3       # afstand 4, vóór Robo
    assert kies_stap(g, 2) == Shoot()
    g.spelers[1].x = 5                           # afstand 5: te ver
    assert kies_stap(g, 2) != Shoot()
    g.spelers[1].x = 11                          # achter Robo
    assert kies_stap(g, 2) != Shoot()


def test_schiet_niet_door_een_schild_heen_op_robot():
    g = nieuw()
    g.spelers[2].x, g.spelers[2].y = 10, 3
    g.spelers[1].x, g.spelers[1].y = 7, 3
    g.schilden.append(Schild(8, 3, eigenaar=2))
    # schild staat in de weg van het lopen én van het schot op de robot: schiet het schild kapot
    assert kies_stap(g, 2) == Shoot() or isinstance(kies_stap(g, 2), Move)


def test_schiet_op_gebouw_binnen_bereik():
    g = nieuw()
    g.spelers[2].x, g.spelers[2].y = 5, 4        # gebouw (1,4) op afstand 4
    g.spelers[1].x, g.spelers[1].y = 2, 1        # uit de weg
    assert kies_stap(g, 2) == Shoot()


def test_zet_schild_als_vijand_op_eigen_helft():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 9, 1        # op Robo's helft, niet in Robo's rij
    g.spelers[2].x, g.spelers[2].y = 12, 4
    assert kies_stap(g, 2) == Shield(*SCHILD_VAK)
    g.schilden.append(Schild(*SCHILD_VAK, eigenaar=2))
    assert kies_stap(g, 2) != Shield(*SCHILD_VAK)   # vak bezet: iets anders doen


def test_loopt_naar_dichtstbijzijnde_brug_en_dan_vooruit():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 1        # uit de weg (anders schiet Robo op rij 4)
    r = g.spelers[2]
    r.x, r.y = 12, 4
    assert kies_stap(g, 2) == Move("omlaag")     # brug op y=2 is even ver als 6; kies 2 (de onderste)
    r.y = 2
    assert kies_stap(g, 2) == Move("vooruit")
    r.x = 7                                      # op de brug
    assert kies_stap(g, 2) == Move("vooruit")
    r.x = 6                                      # over de rivier: naar y=4, dus omhoog
    assert kies_stap(g, 2) == Move("omhoog")
    r.y = 4
    assert kies_stap(g, 2) == Move("vooruit")    # tot binnen bereik (rule 2 schiet dan)
    r.y = 5
    assert kies_stap(g, 2) == Move("omlaag")


def test_vanaf_startvak_met_vijand_thuis_kiest_robo_de_onderste_brug():
    g = nieuw()                                  # mens op (2,4), Robo op (12,4)
    assert kies_stap(g, 2) == Move("omlaag")     # richting brug y=2
    g.spelers[2].y = 3
    assert kies_stap(g, 2) == Move("omlaag")
    g.spelers[2].y = 5                           # dichter bij y=6: dan omhoog
    assert kies_stap(g, 2) == Move("omhoog")


def test_schild_in_de_weg_op_rij_4_wordt_kapotgeschoten():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.spelers[2].x, g.spelers[2].y = 6, 4
    g.schilden.append(Schild(5, 4, eigenaar=1))
    assert kies_stap(g, 2) == Shoot()


def test_andere_brug_als_weg_geblokkeerd():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 12, 3       # vijand blokkeert 'omlaag' vanaf (12,4)
    g.spelers[2].x, g.spelers[2].y = 12, 4
    g.spelers[2].schilden_over = 0               # anders zet hij eerst een schild
    assert kies_stap(g, 2) == Move("omhoog")     # dan maar naar de brug op y=6


def test_dode_robo_doet_niets():
    g = nieuw()
    g.spelers[2].robot_levens = 0
    assert kies_stap(g, 2) is None


def test_tegoed_in_het_spel():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog"), Move("omhoog")])
    assert g.spelers[2].tegoed == 0                      # inplannen geeft nog geen tegoed
    g.tick()
    assert g.spelers[2].tegoed == 0                      # gekregen én in dezelfde tik verbruikt
    assert (g.spelers[2].x, g.spelers[2].y) == (12, 3)   # Robo liep omlaag, richting brug y=2
    g.tick()
    g.tick()
    assert g.spelers[2].tegoed == 0
    assert (g.spelers[2].x, g.spelers[2].y) == (12, 2)   # niet verder zonder tegoed


def test_stop_voor_de_eerste_tik_houdt_robo_stil():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog")] * 5)
    g.stop(1)
    for _ in range(5):
        g.tick()
    assert g.spelers[2].tegoed == 0
    assert (g.spelers[2].x, g.spelers[2].y) == (12, 4)


def test_stop_na_twee_ticks_geeft_robo_precies_twee_stappen():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog")] * 5)
    g.tick()
    g.tick()
    g.stop(1)
    for _ in range(5):
        g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 6)
    assert (g.spelers[2].x, g.spelers[2].y) == (12, 2)   # twee keer omlaag, niet meer


def test_sneuvelen_van_de_mens_houdt_robo_stil():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog")] * 5)
    g.spelers[1].robot_levens = 0
    g.spelers[1].respawn_over = 3
    g.spelers[1].wachtrij.clear()                        # zoals _schiet doet bij een dode robot
    g.tick()
    assert (g.spelers[2].x, g.spelers[2].y) == (12, 4)


from app.game import Mijn


def test_robo_stapt_niet_op_een_mijn_maar_kiest_de_andere_brug():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 1        # vijand uit de weg
    g.spelers[2].x, g.spelers[2].y = 12, 4
    g.mijnen.append(Mijn(12, 3, eigenaar=1))     # op weg naar de onderste brug
    assert kies_stap(g, 2) == Move("omhoog")
    g.spelers[2].y = 2                           # op de rij van de brug
    g.mijnen[:] = [Mijn(11, 2, eigenaar=1)]      # mijn vóór hem
    assert kies_stap(g, 2) == Move("omhoog")     # dan maar naar de brug op y=6


def test_robo_wacht_voor_mijn_op_de_brug_zelf():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.spelers[2].x, g.spelers[2].y = 7, 2        # op de brug, mijn op (6,2)
    g.mijnen.append(Mijn(6, 2, eigenaar=1))
    assert kies_stap(g, 2) is None               # geblokkeerd: even wachten, niet erop stappen


def test_robo_schiet_gewoon_over_een_mijn_heen():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 8, 4
    g.spelers[2].x, g.spelers[2].y = 11, 4
    g.mijnen.append(Mijn(9, 4, eigenaar=1))
    assert kies_stap(g, 2) == Shoot()
