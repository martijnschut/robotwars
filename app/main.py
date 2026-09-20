"""FastAPI-server van Robot Wars: pagina's, WebSocket en de tik-taak."""
from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import weergave
from .db import ScoreDb
from .lobby import Lobby

HIER = Path(__file__).parent
TIK_SECONDEN = float(os.environ.get("ROBOTWARS_TIK", "1"))
WEG_NA = 60          # seconden zonder verbinding: speler is weg
COOKIE_DUUR = 30 * 24 * 3600

log = logging.getLogger("robotwars")
lobby = Lobby()
db = ScoreDb(os.environ.get("ROBOTWARS_DB", "robotwars.db"))
templates = Jinja2Templates(directory=str(HIER / "templates"))
templates.env.filters.update(weergave.FILTERS)

# game_id -> spelernummer -> open WebSockets
verbindingen: dict[str, dict[int, set[WebSocket]]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    taak = asyncio.create_task(tik_loop())
    yield
    taak.cancel()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(HIER / "static")), name="static")


def huidige_sessie(request: Request):
    return lobby.sessie(request.cookies.get("token"))


# ---- startpagina en scorebord ----

@app.get("/", response_class=HTMLResponse)
async def start(request: Request):
    sessie = huidige_sessie(request)
    if sessie and (lopend := lobby.game_van(sessie.token)):
        return RedirectResponse(f"/spel/{lopend[0].id}", status_code=303)
    return templates.TemplateResponse(request, "start.html",
                                      {"naam": sessie.naam if sessie else "", "fout": None})


@app.post("/start")
async def start_post(request: Request, naam: str = Form(""), modus: str = Form("computer")):
    naam = naam.strip()
    if not 1 <= len(naam) <= 20:
        return templates.TemplateResponse(request, "start.html",
                                          {"naam": naam, "fout": "Vul een naam in van 1 tot 20 tekens."},
                                          status_code=400)
    sessie = lobby.registreer(naam, request.cookies.get("token"))
    if lopend := lobby.game_van(sessie.token):
        doel = f"/spel/{lopend[0].id}"
    elif modus == "mens":
        game = lobby.zoek_tegenstander(sessie.token)
        doel = f"/spel/{game.id}" if game else "/wachten"
    else:
        doel = f"/spel/{lobby.start_tegen_computer(sessie.token).id}"
    antwoord = RedirectResponse(doel, status_code=303)
    antwoord.set_cookie("token", sessie.token, max_age=COOKIE_DUUR, httponly=True, samesite="lax")
    return antwoord


@app.get("/scorebord", response_class=HTMLResponse)
async def scorebord(request: Request):
    return templates.TemplateResponse(request, "scorebord.html",
                                      {"computer": db.top(True), "mens": db.top(False)})


# ---- wachtkamer ----

@app.get("/wachten", response_class=HTMLResponse)
async def wachten(request: Request):
    sessie = huidige_sessie(request)
    if sessie is None:
        return RedirectResponse("/", status_code=303)
    if lopend := lobby.game_van(sessie.token):
        return RedirectResponse(f"/spel/{lopend[0].id}", status_code=303)
    if game := lobby.zoek_tegenstander(sessie.token):     # direct gekoppeld
        return RedirectResponse(f"/spel/{game.id}", status_code=303)
    return templates.TemplateResponse(request, "wachten.html", {"naam": sessie.naam})


@app.get("/wachten/status")
async def wachten_status(request: Request):
    sessie = huidige_sessie(request)
    if sessie and (lopend := lobby.game_van(sessie.token)):
        return Response(headers={"HX-Redirect": f"/spel/{lopend[0].id}"})
    wacht = int(time.time() - lobby.wacht_sinds) if lobby.wachtende else 0
    return HTMLResponse(f"Al {weergave.mmss(wacht)} aan het wachten")


@app.post("/wachten/computer")
async def wachten_computer(request: Request):
    sessie = huidige_sessie(request)
    if sessie is None:
        return RedirectResponse("/", status_code=303)
    if lopend := lobby.game_van(sessie.token):
        return RedirectResponse(f"/spel/{lopend[0].id}", status_code=303)
    game = lobby.start_tegen_computer(sessie.token)
    return RedirectResponse(f"/spel/{game.id}", status_code=303)


# ---- tik-taak (wordt in Task 15 uitgebreid) ----

def tik_alles() -> None:
    lobby.ruim_op()


async def tik_loop() -> None:
    while True:
        await asyncio.sleep(TIK_SECONDEN)
        try:
            tik_alles()
        except Exception:      # nooit de loop laten sterven
            log.exception("fout in tik")
