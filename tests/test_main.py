import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from app import main
from app.db import ScoreDb
from app.parser import Move, Shoot


@pytest.fixture
def client():
    main.lobby.__init__()            # schone lobby, db en verbindingen per test
    main.db = ScoreDb(":memory:")
    main.verbindingen.clear()
    with TestClient(app=main.app) as c:
        yield c


def test_startpagina(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Hoe heet je?" in r.text and "Speel tegen de computer" in r.text


def test_naam_verplicht(client):
    r = client.post("/start", data={"naam": "   ", "modus": "computer"})
    assert r.status_code == 400
    assert "Vul een naam in" in r.text


def test_start_tegen_computer_maakt_spel_en_cookie(client):
    r = client.post("/start", data={"naam": "Wessel", "modus": "computer"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/spel/")
    assert "token" in r.cookies
    game_id = r.headers["location"].split("/")[-1]
    game = main.lobby.games[game_id]
    assert game.tegen_computer and game.spelers[1].naam == "Wessel"


def test_cookie_is_secure_achter_https(client):
    r = client.post("/start", data={"naam": "Wessel", "modus": "computer"},
                    headers={"x-forwarded-proto": "https"}, follow_redirects=False)
    assert "Secure" in r.headers["set-cookie"]
    client.cookies.clear()
    r = client.post("/start", data={"naam": "Wessel", "modus": "computer"}, follow_redirects=False)
    assert "Secure" not in r.headers["set-cookie"]


def test_terugkomen_stuurt_door_naar_lopend_spel(client):
    r = client.post("/start", data={"naam": "Wessel", "modus": "computer"}, follow_redirects=False)
    doel = r.headers["location"]
    r2 = client.get("/", follow_redirects=False)
    assert r2.status_code == 303 and r2.headers["location"] == doel


def test_scorebord(client):
    main.db.sla_op("Wessel", "Robo", True, 83)
    main.db.sla_op("Papa", "Wessel", False, 120)
    r = client.get("/scorebord")
    assert r.status_code == 200
    assert "Wessel" in r.text and "1:23" in r.text and "2:00" in r.text
    assert "Tegen de computer" in r.text and "Tegen een mens" in r.text


def test_wachtkamer_en_koppelen(client):
    a = client.post("/start", data={"naam": "A", "modus": "mens"}, follow_redirects=False)
    assert a.headers["location"] == "/wachten"
    token_a = a.cookies["token"]
    r = client.get("/wachten")
    assert r.status_code == 200 and "Wachten op een tegenstander" in r.text
    r = client.get("/wachten/status")
    assert r.status_code == 200 and "HX-Redirect" not in r.headers and "aan het wachten" in r.text
    # tweede speler in een andere browser (andere cookies)
    client.cookies.clear()
    b = client.post("/start", data={"naam": "B", "modus": "mens"}, follow_redirects=False)
    assert b.headers["location"].startswith("/spel/")
    # A pollt en wordt doorgestuurd
    client.cookies.set("token", token_a)
    r = client.get("/wachten/status")
    assert r.headers["HX-Redirect"] == b.headers["location"]


def test_toch_tegen_de_computer(client):
    client.post("/start", data={"naam": "A", "modus": "mens"}, follow_redirects=False)
    r = client.post("/wachten/computer", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/spel/")
    assert main.lobby.wachtende is None


def start_spel(client, naam="Wessel"):
    r = client.post("/start", data={"naam": naam, "modus": "computer"}, follow_redirects=False)
    game_id = r.headers["location"].split("/")[-1]
    return main.lobby.games[game_id], r.cookies["token"]


def test_spelpagina(client):
    game, token = start_spel(client)
    r = client.get(f"/spel/{game.id}")
    assert r.status_code == 200
    for fragment in ('id="veld"', 'id="status"', 'id="kop"', 'id="regels"', 'id="invoer"', 'id="einde"'):
        assert fragment in r.text
    assert f'ws-connect="/ws/spel/{game.id}"' in r.text
    assert "Wessel" in r.text and "Robo" in r.text
    client.cookies.clear()
    assert client.get(f"/spel/{game.id}", follow_redirects=False).status_code == 303   # vreemde: weg


def test_websocket_typen_voert_uit(client):
    game, token = start_spel(client)
    with client.websocket_connect(f"/ws/spel/{game.id}", headers={"cookie": f"token={token}"}) as ws:
        ws.send_json({"regel": "robot = vo"})
        html = ws.receive_text()
        assert 'id="markering"' in html and 'id="invoer"' not in html
        ws.send_json({"regel": "robot = vooruit"})
        html = ws.receive_text()
        assert 'id="invoer"' in html and "robot = vooruit" in html and 'class="mk ok"' in html
        assert list(game.spelers[1].wachtrij) == [Move("vooruit")]
        ws.send_json({"actie": "stop"})
        ws.receive_text()
        assert len(game.spelers[1].wachtrij) == 0
        ws.send_json({"regel": "robot = links"})
        html = ws.receive_text()
        assert 'id="hint"' in html and "links" in html


def test_websocket_ongeldig_bericht_wordt_genegeerd(client):
    game, token = start_spel(client)
    with client.websocket_connect(f"/ws/spel/{game.id}", headers={"cookie": f"token={token}"}) as ws:
        ws.send_text("dit is geen json")
        ws.send_bytes(b"\x00\x01")                      # binair frame
        ws.send_json(["ook", "geen", "dict"])
        ws.send_json({"regel": "robot = schiet"})
        assert 'id="invoer"' in ws.receive_text()


def test_tik_stuurt_veld_naar_verbonden_spelers(client):
    game, token = start_spel(client)
    with client.websocket_connect(f"/ws/spel/{game.id}", headers={"cookie": f"token={token}"}) as ws:
        ws.send_json({"regel": "robot = omhoog"})
        ws.receive_text()
        main.tik_alles()
        client.portal.call(main.zend_alles)
        html = ws.receive_text()
        assert 'id="veld"' in html and 'id="status"' in html and 'id="kop"' in html
        assert (game.spelers[1].x, game.spelers[1].y) == (2, 3)


def test_winst_wordt_opgeslagen_en_getoond(client):
    game, token = start_spel(client)
    game.spelers[2].gebouw_levens = 1
    game.spelers[1].x, game.spelers[1].y = 9, 4
    game.spelers[2].x, game.spelers[2].y = 12, 1
    game.voeg_stappen_toe(1, [Shoot()])
    with client.websocket_connect(f"/ws/spel/{game.id}", headers={"cookie": f"token={token}"}) as ws:
        main.tik_alles()
        client.portal.call(main.zend_alles)
        html = ws.receive_text()
        assert "wint!" in html and "Wessel" in html and 'class="overlay"' in html
        # de eindstand gaat één keer: daarna is de socket gesloten en wordt niets meer gestuurd
        assert game.einde_gezonden is True
        assert not main.verbindingen[game.id][1]
        client.portal.call(main.zend_alles)
        with pytest.raises(Exception):
            ws.receive_text()
    assert game.score_opgeslagen
    assert main.db.top(True)[0]["winnaar"] == "Wessel"
    assert client.get("/", follow_redirects=False).status_code == 200   # niet meer terug het spel in


def test_weg_zijn_is_verlies_zonder_score(client):
    game, token = start_spel(client)
    game.laatst_gezien[1] = time.time() - main.WEG_NA - 1
    main.tik_alles()
    assert game.afgelopen and game.winnaar == 2 and game.opgegeven
    assert main.db.top(True) == []


def test_verbonden_speler_is_niet_weg(client):
    game, token = start_spel(client)
    with client.websocket_connect(f"/ws/spel/{game.id}", headers={"cookie": f"token={token}"}):
        game.laatst_gezien[1] = time.time() - main.WEG_NA - 1
        main.tik_alles()
        assert not game.afgelopen                     # verbonden wint van tijd
    assert game.laatst_gezien[1] > time.time() - 5    # bij het verbreken bijgewerkt


def test_kapot_spel_houdt_de_rest_niet_tegen(client):
    kapot, _ = start_spel(client, "Kapot")
    client.cookies.clear()
    gezond, _ = start_spel(client, "Gezond")
    kapot.voeg_stappen_toe(1, [Move("omhoog")])       # geeft Robo tegoed, dus het brein wordt gevraagd
    kapot.brein = lambda g, n: 1 / 0
    main.tik_alles()
    assert gezond.tik == 1


class NepSocket:
    """Een socket die niet meer reageert op send_text."""
    def __init__(self):
        self.gesloten_met = None

    async def send_text(self, html):
        raise asyncio.TimeoutError()

    async def close(self, code=1000, reason=None):
        self.gesloten_met = code


def test_stokkende_socket_wordt_gesloten_met_1013(client):
    game, token = start_spel(client)
    nep = NepSocket()
    main.verbindingen[game.id] = {1: {nep}}

    async def zend_en_wacht():
        await main.zend_alles()
        await asyncio.sleep(0)            # de losse sluit-taak laten lopen

    client.portal.call(zend_en_wacht)
    assert nep not in main.verbindingen[game.id][1]
    assert nep.gesloten_met == 1013


def test_melding_wordt_hint_na_tik(client):
    game, token = start_spel(client)
    game.spelers[1].melding = "Hier kan geen schild."
    main.tik_alles()
    assert game.editors[1].hint == "Hier kan geen schild." and game.spelers[1].melding is None
    html = main.weergave.tik_html(main.templates, game, 1)
    assert 'id="hint"' in html and "Hier kan geen schild." in html
    assert game.editors[1].hint == "Hier kan geen schild."   # renderen verandert niets
