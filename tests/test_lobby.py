from app.lobby import Lobby, OPRUIMEN_NA
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
