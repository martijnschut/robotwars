"""FastAPI-server van Robot Wars: pagina's, WebSocket en de tik-taak."""
from __future__ import annotations

import asyncio
import contextlib
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
    with contextlib.suppress(asyncio.CancelledError):
        await taak


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
    secure = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
    antwoord.set_cookie("token", sessie.token, max_age=COOKIE_DUUR, httponly=True,
                        samesite="lax", secure=secure)
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


# ---- spelpagina ----

def spel_van(request_of_ws, game_id: str):
    """(game, nummer) als deze cookie bij dit spel hoort, anders None."""
    sessie = lobby.sessie(request_of_ws.cookies.get("token"))
    game = lobby.games.get(game_id)
    if sessie is None or game is None or sessie.game_id != game_id:
        return None
    return game, sessie.nummer


@app.get("/spel/{game_id}", response_class=HTMLResponse)
async def spel(request: Request, game_id: str):
    gevonden = spel_van(request, game_id)
    if gevonden is None:
        return RedirectResponse("/", status_code=303)
    game, ik = gevonden
    return templates.TemplateResponse(request, "spel.html", weergave.context(game, ik))


def verwerk_bericht(game, ik: int, bericht) -> str | None:
    """Een bericht van de editor: getypte regel of knop. Geeft de HTML om terug te sturen."""
    if game.afgelopen or not isinstance(bericht, dict):
        return None
    editor = game.editors[ik]
    if "regel" in bericht:
        bevroren = editor.verwerk(game, ik, str(bericht["regel"]))
        return weergave.editor_html(templates, game, ik, met_invoer=bevroren)
    actie = bericht.get("actie")
    if actie == "stop":
        game.stop(ik)
        editor.hint = "Gestopt. Je robot staat stil."
    elif actie == "wis":
        editor.wis()
    else:
        return None
    return weergave.editor_html(templates, game, ik, met_invoer=False)


@app.websocket("/ws/spel/{game_id}")
async def ws_spel(ws: WebSocket, game_id: str):
    gevonden = spel_van(ws, game_id)
    if gevonden is None:
        await ws.close(code=1008)
        return
    game, ik = gevonden
    await ws.accept()
    verbindingen.setdefault(game_id, {}).setdefault(ik, set()).add(ws)
    game.laatst_gezien[ik] = time.time()
    try:
        while True:
            try:
                bericht = await ws.receive_json()
            except WebSocketDisconnect:
                break
            except (ValueError, KeyError):   # geen geldige JSON of een binair frame: negeren
                continue
            game.laatst_gezien[ik] = time.time()
            html = verwerk_bericht(game, ik, bericht)
            if html:
                await ws.send_text(html)
    finally:
        verbindingen.get(game_id, {}).get(ik, set()).discard(ws)
        game.laatst_gezien[ik] = time.time()


# ---- tik-taak: elke seconde alle spellen een stap verder en uitzenden ----

def controleer_weg(game, nu: float) -> None:
    for nummer in (1, 2):
        speler = game.spelers[nummer]
        if speler.is_computer:
            continue
        verbonden = bool(verbindingen.get(game.id, {}).get(nummer))
        if not verbonden and nu - game.laatst_gezien[nummer] > WEG_NA:
            game.geef_op(nummer)
            return


def tik_spel(game, nu: float) -> None:
    """Eén spel een tik verder: stap, meldingen naar de editor, weg-controle, score."""
    game.tick()
    for nummer, speler in game.spelers.items():
        if speler.melding:
            game.editors[nummer].hint = speler.melding
            speler.melding = None
    controleer_weg(game, nu)
    if game.afgelopen and not game.score_opgeslagen:
        game.score_opgeslagen = True
        winnaar = game.spelers[game.winnaar]
        if not game.opgegeven and not winnaar.is_computer:
            verliezer = game.tegenstander(game.winnaar)
            db.sla_op(winnaar.naam, verliezer.naam, game.tegen_computer, game.tik)


def tik_alles() -> None:
    nu = time.time()
    for game in list(lobby.games.values()):
        if game.afgelopen:
            continue
        try:
            tik_spel(game, nu)
        except Exception:      # één kapot spel houdt de andere niet tegen
            log.exception("fout in spel %s", game.id)
    for game_id in lobby.ruim_op(nu):
        verbindingen.pop(game_id, None)


async def sluit(ws: WebSocket, code: int = 1000) -> None:
    with contextlib.suppress(Exception):
        await asyncio.wait_for(ws.close(code=code), timeout=TIK_SECONDEN)


async def zend(ws: WebSocket, html: str, sockets: set[WebSocket]) -> None:
    """Stuurt naar één socket; een trage of dode socket gaat uit de set en wordt gesloten
    met code 1013 (daarop verbindt HTMX opnieuw), los van de tik-loop."""
    try:
        await asyncio.wait_for(ws.send_text(html), timeout=TIK_SECONDEN)
    except Exception:
        sockets.discard(ws)
        asyncio.create_task(sluit(ws, code=1013))


async def zend_alles() -> None:
    for game_id, per_speler in list(verbindingen.items()):
        game = lobby.games.get(game_id)
        if game is None or (game.afgelopen and game.einde_gezonden):
            continue
        for nummer, sockets in list(per_speler.items()):
            if not sockets:
                continue
            html = weergave.tik_html(templates, game, nummer)
            for ws in list(sockets):
                await zend(ws, html, sockets)
        if game.afgelopen:
            # De eindstand gaat één keer; daarna sluiten (code 1000, dan verbindt HTMX niet opnieuw).
            game.einde_gezonden = True
            for sockets in list(per_speler.values()):
                for ws in list(sockets):
                    await sluit(ws)
                    sockets.discard(ws)


async def tik_loop() -> None:
    while True:
        await asyncio.sleep(TIK_SECONDEN)
        try:
            tik_alles()
            await zend_alles()
        except Exception:      # nooit de loop laten sterven
            log.exception("fout in tik")
