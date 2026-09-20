from app.parser import parse_line, Move, Shoot, Incomplete, Invalid


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
    assert r.hint == "Begin met robot = ..., schild = (...), herhaal ... keer of klaar."
