from app.lobby import Lobby, OPRUIMEN_NA, Uitslag
from app.editor import Editor


def test_registreren_geeft_token_en_onthoudt_naam():
    lobby = Lobby()
    s = lobby.registreer("Wessel")
    assert len(s.token) >= 8 and s.naam == "Wessel"
    assert lobby.sessie(s.token) is s
    assert lobby.sessie("bestaat-niet") is None
    s2 = lobby.registreer("Wes", token=s.token)     # zelfde cookie: naam bijwerken
    assert s2 is s and s.naam == "Wes"


def test_twee_wachtenden_worden_gekoppeld():
    lobby = Lobby()
    a = lobby.registreer("A")
    b = lobby.registreer("B")
    assert lobby.zoek_tegenstander(a.token) is None
    assert lobby.wachtende == a.token
    game = lobby.zoek_tegenstander(b.token)
    assert game is not None and lobby.wachtende is None
    assert game.spelers[1].naam == "A" and game.spelers[2].naam == "B"
    assert not game.tegen_computer
    assert lobby.game_van(a.token) == (game, 1)
    assert lobby.game_van(b.token) == (game, 2)
    assert isinstance(game.editors[1], Editor) and isinstance(game.editors[2], Editor)


def test_nog_een_keer_zoeken_terwijl_je_al_wacht():
    lobby = Lobby()
    a = lobby.registreer("A")
    lobby.zoek_tegenstander(a.token)
    assert lobby.zoek_tegenstander(a.token) is None
    assert lobby.wachtende == a.token


def test_tegen_computer():
    lobby = Lobby()
    a = lobby.registreer("A")
    lobby.zoek_tegenstander(a.token)               # eerst wachten...
    game = lobby.start_tegen_computer(a.token)     # ...dan toch tegen de computer
    assert lobby.wachtende is None
    assert game.tegen_computer and game.spelers[2].naam == "Robo" and game.spelers[2].is_computer
    assert game.brein is not None
    assert lobby.game_van(a.token) == (game, 1)


def test_afgelopen_spel_is_geen_lopend_spel_en_wordt_opgeruimd():
    lobby = Lobby()
    a = lobby.registreer("A")
    game = lobby.start_tegen_computer(a.token)
    game.geef_op(1)
    assert lobby.game_van(a.token) is None
    verwijderd = lobby.ruim_op(nu=game.geeindigd_op + OPRUIMEN_NA - 1)
    assert verwijderd == [] and game.id in lobby.games
    verwijderd = lobby.ruim_op(nu=game.geeindigd_op + OPRUIMEN_NA + 1)
    assert verwijderd == [game.id] and game.id not in lobby.games


def test_wacht_sinds_blijft_staan_bij_nog_een_keer_zoeken():
    lobby = Lobby()
    a = lobby.registreer("A")
    lobby.zoek_tegenstander(a.token)
    lobby.wacht_sinds = 123.0
    assert lobby.zoek_tegenstander(a.token) is None
    assert lobby.wacht_sinds == 123.0


def test_wachtende_die_niet_meer_pollt_wordt_opgeruimd():
    lobby = Lobby()
    a = lobby.registreer("A")
    lobby.zoek_tegenstander(a.token)
    assert lobby.laatst_gepolld == lobby.wacht_sinds
    lobby.laatst_gepolld = 1000.0
    assert lobby.ruim_wachtende_op(nu=1004.0) is False
    assert lobby.wachtende == a.token
    assert lobby.ruim_wachtende_op(nu=1005.5) is True
    assert lobby.wachtende is None
    assert lobby.ruim_wachtende_op(nu=2000.0) is False    # niets meer op te ruimen


def test_bewaar_uitslag_bij_weg_zijn():
    lobby = Lobby()
    a = lobby.registreer("Martijn")
    b = lobby.registreer("Wessel")
    lobby.zoek_tegenstander(a.token)
    game = lobby.zoek_tegenstander(b.token)
    game.tik = 61
    game.geef_op(1)                                   # Martijn is weg, Wessel wint
    lobby.bewaar_uitslag(game)
    assert a.laatste_uitslag == Uitslag(tegen="Wessel", ik_won=False, opgegeven=True,
                                        ik_was_weg=True, gestopt=False, seconden=61)
    assert b.laatste_uitslag == Uitslag(tegen="Martijn", ik_won=True, opgegeven=True,
                                        ik_was_weg=False, gestopt=False, seconden=61)


def test_bewaar_uitslag_bij_gewoon_verlies():
    lobby = Lobby()
    a = lobby.registreer("A")
    game = lobby.start_tegen_computer(a.token)
    game.tik = 83
    game._zet_winnaar(2)
    lobby.bewaar_uitslag(game)
    assert a.laatste_uitslag == Uitslag(tegen="Robo", ik_won=False, opgegeven=False,
                                        ik_was_weg=False, gestopt=False, seconden=83)


def test_bewaar_uitslag_bij_stoppen_met_de_knop():
    lobby = Lobby()
    a = lobby.registreer("A")
    game = lobby.start_tegen_computer(a.token)
    game.tik = 20
    game.geef_op(1, reden="gestopt")
    lobby.bewaar_uitslag(game)
    assert a.laatste_uitslag.gestopt and a.laatste_uitslag.ik_was_weg and not a.laatste_uitslag.ik_won


def test_nieuw_spel_wist_de_uitslag():
    lobby = Lobby()
    a = lobby.registreer("A")
    game = lobby.start_tegen_computer(a.token)
    game.geef_op(1)
    lobby.bewaar_uitslag(game)
    assert a.laatste_uitslag is not None
    lobby.start_tegen_computer(a.token)
    assert a.laatste_uitslag is None
