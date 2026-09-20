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
