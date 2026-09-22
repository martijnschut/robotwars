from app.parser import (parse_line, Move, Shoot, Aim, Incomplete, Invalid, HINT_START, HINT_ROBOT,
                        HINT_KANON, HINT_SCHIET)


def test_robot_vooruit():
    assert parse_line("robot = vooruit") == Move("vooruit")


def test_alle_richtingen():
    for r in ("vooruit", "achteruit", "omhoog", "omlaag"):
        assert parse_line(f"robot = {r}") == Move(r)


def test_schiet():
    assert parse_line("robot = schiet") == Shoot()


def test_hoofdletters_en_spaties_maken_niet_uit():
    assert parse_line("  ROBOT=Vooruit ") == Move("vooruit")


def test_lege_regel_is_incomplete():
    assert parse_line("") == Incomplete()
    assert parse_line("   ") == Incomplete()


def test_half_getypt_is_incomplete():
    assert parse_line("rob") == Incomplete()
    assert parse_line("robot = vo") == Incomplete()
    assert parse_line("robot =") == Incomplete()


def test_onbekende_richting_is_invalid_met_hint():
    r = parse_line("robot = links")
    assert isinstance(r, Invalid)
    assert r.hint == 'Ik ken "links" niet. Probeer vooruit, achteruit, omhoog, omlaag of schiet.'


def test_te_lang_is_invalid():
    assert isinstance(parse_line("robot = vooruitt"), Invalid)


def test_onbekend_begin_is_invalid():
    r = parse_line("lamp = aan")
    assert isinstance(r, Invalid)
    assert r.hint == HINT_START == "Begin met robot = ..., kanon = ..., schild = (...), bom = (...), herhaal ... keer of klaar."


from app.parser import Shield, RepeatStart, RepeatEnd, HINT_SCHILD, HINT_HERHAAL


def test_schild_met_coordinaten():
    assert parse_line("schild = (4, 2)") == Shield(4, 2)
    assert parse_line("schild=(12,7)") == Shield(12, 7)


def test_schild_half_getypt_is_incomplete():
    assert parse_line("schild = (4") == Incomplete()
    assert parse_line("schild = (4,") == Incomplete()


def test_schild_zonder_getallen_is_invalid():
    r = parse_line("schild = (a, b)")
    assert isinstance(r, Invalid)
    assert r.hint == HINT_SCHILD
    assert r.hint == "Schild heeft twee getallen nodig: schild = (x, y), bijvoorbeeld schild = (4, 2)."


def test_herhaal():
    assert parse_line("herhaal 3 keer") == RepeatStart(3)
    assert parse_line("HERHAAL 20 KEER") == RepeatStart(20)


def test_herhaal_half_is_incomplete():
    assert parse_line("herhaal 3") == Incomplete()
    assert parse_line("herhaal 3 ke") == Incomplete()


def test_herhaal_nul_of_te_veel_is_invalid():
    for tekst in ("herhaal 0 keer", "herhaal 21 keer", "herhaal 100 keer", "herhaal keer"):
        r = parse_line(tekst)
        assert isinstance(r, Invalid), tekst
        assert r.hint == HINT_HERHAAL


def test_klaar():
    assert parse_line("klaar") == RepeatEnd()
    assert parse_line("kl") == Incomplete()


import pytest
from app.parser import expand


def test_expand_zonder_herhaal():
    assert expand([Move("vooruit"), Shoot()]) == [Move("vooruit"), Shoot()]


def test_expand_herhaal_3_keer_geeft_3_stappen():
    cmds = [RepeatStart(3), Move("vooruit"), RepeatEnd()]
    assert expand(cmds) == [Move("vooruit")] * 3


def test_expand_genest():
    cmds = [RepeatStart(2), Move("omhoog"), RepeatStart(2), Shoot(), RepeatEnd(), RepeatEnd()]
    assert expand(cmds) == [Move("omhoog"), Shoot(), Shoot()] * 2


def test_expand_klaar_zonder_herhaal():
    with pytest.raises(ValueError):
        expand([RepeatEnd()])


def test_expand_herhaal_zonder_klaar():
    with pytest.raises(ValueError):
        expand([RepeatStart(2), Move("vooruit")])


def test_expand_max_stappen_beperkt_geneste_herhaal_blokken():
    cmds = [RepeatStart(20), RepeatStart(20), RepeatStart(20), Move("vooruit"),
            RepeatEnd(), RepeatEnd(), RepeatEnd()]
    with pytest.raises(ValueError):
        expand(cmds, max_stappen=50)
    # zonder max_stappen blijft het oude gedrag (alles uitrollen)
    assert expand(cmds) == [Move("vooruit")] * 8000


# ---- bom ----

from app.parser import Bomb, HINT_BOM


def test_bom_met_dx_dy():
    assert parse_line("bom = (-1,1)") == Bomb(-1, 1)
    assert parse_line("bom = ( 1 , 0 )") == Bomb(1, 0)
    assert parse_line("BOM=(0,0)") == Bomb(0, 0)
    assert parse_line("bom = (0, -1)") == Bomb(0, -1)


def test_bom_half_getypt_is_incomplete():
    for tekst in ["b", "bom", "bom =", "bom = (", "bom = (-", "bom = (-1", "bom = (-1,", "bom = (-1, 1"]:
        assert parse_line(tekst) == Incomplete(), tekst


def test_bom_verder_dan_een_vakje_is_invalid():
    assert parse_line("bom = (2, 0)") == Invalid(HINT_BOM)
    assert parse_line("bom = (0, -2)") == Invalid(HINT_BOM)
    assert parse_line("bom = (10, 0)") == Invalid(HINT_BOM)


def test_bom_zonder_of_met_kapotte_getallen_is_invalid():
    assert parse_line("bom = (a, 1)") == Invalid(HINT_BOM)
    assert parse_line("bom = (--1, 0)") == Invalid(HINT_BOM)
    assert parse_line("bom = 1") == Invalid(HINT_BOM)


def test_start_hint_noemt_bom():
    assert parse_line("xyz") == Invalid(HINT_START)
    assert "bom = (...)" in HINT_START


def test_expand_herhaal_met_bom():
    stappen = expand([RepeatStart(2), Bomb(1, 0), RepeatEnd()])
    assert stappen == [Bomb(1, 0), Bomb(1, 0)]


# ---- kanon richten ----


def test_kanon_in_vier_richtingen():
    for graden in (0, 90, 180, 270):
        assert parse_line(f"kanon = {graden}") == Aim(graden)
    assert parse_line("kanon=90") == Aim(90)            # spaties maken niet uit
    assert parse_line("kanon = 090") == Aim(90)         # voorloopnul is geen fout


def test_kanon_schuin_in_vier_richtingen():
    for graden in (45, 135, 225, 315):
        assert parse_line(f"kanon = {graden}") == Aim(graden)
    assert parse_line("kanon=45") == Aim(45)            # spaties maken niet uit


def test_kanon_foute_graden_geeft_kanon_hint():
    assert parse_line("kanon = 5") == Invalid(HINT_KANON)       # los cijfer, geen prefix
    assert parse_line("kanon = 19") == Invalid(HINT_KANON)      # begint als 180, maar wijkt af
    assert parse_line("kanon = 30") == Invalid(HINT_KANON)      # begint als 315, maar wijkt af
    assert parse_line("kanon = 360") == Invalid(HINT_KANON)
    assert parse_line("kanon = 1800") == Invalid(HINT_KANON)
    assert parse_line("kanon = omhoog") == Invalid(HINT_KANON)
    assert parse_line("kanon 90") == Invalid(HINT_KANON)
    assert "kanon = 90" in HINT_KANON and "45" in HINT_KANON


def test_kanon_half_getypt_is_incomplete():
    # het getal staat aan het eind, dus "9" en "18" moeten nog 90 en 180 kunnen worden
    for tekst in ("kan", "kanon", "kanon =", "kanon = 9", "kanon = 1", "kanon = 18", "kanon = 27", "kanon = 09"):
        assert parse_line(tekst) == Incomplete(), tekst


def test_kanon_schuin_half_getypt_is_incomplete():
    # "4" kan nog 45 worden, "3"/"31" nog 315, "2"/"22" nog 225 (of 270), "13" nog 135
    for tekst in ("kanon = 4", "kanon = 3", "kanon = 31", "kanon = 2", "kanon = 22", "kanon = 13"):
        assert parse_line(tekst) == Incomplete(), tekst


def test_schiet_blijft_zonder_richting():
    assert parse_line("robot = schiet") == Shoot()


def test_schiet_met_richting_wijst_naar_kanon():
    assert parse_line("robot = schiet(90)") == Invalid(HINT_SCHIET)
    assert parse_line("robot = schiet omhoog") == Invalid(HINT_SCHIET)
    assert "kanon = 90" in HINT_SCHIET


def test_andere_robot_fouten_houden_de_oude_hint():
    assert parse_line("robot = links") == Invalid(HINT_ROBOT.format("links"))


def test_start_hint_noemt_kanon():
    assert parse_line("xyz") == Invalid(HINT_START)
    assert "kanon = ..." in HINT_START


def test_schild_met_drie_cijfers_is_voor_het_spel():
    assert parse_line("schild = (123, 4)") == Shield(123, 4)   # het spel keurt dat vak af
