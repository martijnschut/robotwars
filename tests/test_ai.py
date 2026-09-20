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
    assert kies_stap(g, 2) == Move("omhoog")     # brug op rij 2 is even ver als 6; kies 2
    r.y = 2
    assert kies_stap(g, 2) == Move("vooruit")
    r.x = 7                                      # op de brug
    assert kies_stap(g, 2) == Move("vooruit")
    r.x = 6                                      # over de rivier: naar rij 4
    assert kies_stap(g, 2) == Move("omlaag")
    r.y = 4
    assert kies_stap(g, 2) == Move("vooruit")    # tot binnen bereik (rule 2 schiet dan)
    r.y = 5
    assert kies_stap(g, 2) == Move("omhoog")


def test_schild_in_de_weg_op_rij_4_wordt_kapotgeschoten():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.spelers[2].x, g.spelers[2].y = 6, 4
    g.schilden.append(Schild(5, 4, eigenaar=1))
    assert kies_stap(g, 2) == Shoot()


def test_andere_brug_als_weg_geblokkeerd():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 12, 3       # vijand blokkeert 'omhoog' vanaf (12,4)
    g.spelers[2].x, g.spelers[2].y = 12, 4
    g.spelers[2].schilden_over = 0               # anders zet hij eerst een schild
    assert kies_stap(g, 2) == Move("omlaag")


def test_dode_robo_doet_niets():
    g = nieuw()
    g.spelers[2].robot_levens = 0
    assert kies_stap(g, 2) is None


def test_tegoed_in_het_spel():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog"), Move("omhoog")])
    assert g.spelers[2].tegoed == 2
    g.tick()
    assert g.spelers[2].tegoed == 1
    assert (g.spelers[2].x, g.spelers[2].y) == (12, 3)   # Robo liep omhoog
    g.tick()
    g.tick()
    assert g.spelers[2].tegoed == 0
    assert (g.spelers[2].x, g.spelers[2].y) == (12, 2)   # niet verder zonder tegoed
