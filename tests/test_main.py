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
