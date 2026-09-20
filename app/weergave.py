"""Alles wat de templates nodig hebben: veldmatrix, context en Jinja-filters."""
from __future__ import annotations

from dataclasses import dataclass

from .game import (BREEDTE, BRUG_RIJEN, GEBOUW_LEVENS, HOOGTE, RESPAWN_TIKKEN, RIVIER_X,
                   ROBOT_LEVENS, Game, Gebeurtenis, Schild, Speler)

MAANDEN = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
SYMBOLEN = {"ok": "✓", "wacht": "…", "fout": "!"}


@dataclass
class Cel:
    x: int
    y: int
    soort: str                   # "b" (helft 1), "r" (helft 2), "w" (water), "br" (brug)
    robot: Speler | None = None
    gebouw: Speler | None = None
    schild: Schild | None = None
    spoor: bool = False          # de kogel kwam hier langs in de laatste tik
    spoor_index: int = 0         # hoeveelste vakje van de baan (0 = eerste na de schutter)
    raak: bool = False           # hier is iets geraakt in de laatste tik
    knal_vertraging: float = 0.0 # seconden tot de kogel hier aankomt (de 💥 wacht daarop)


STAP_SECONDEN = 0.18   # vliegtijd van de kogel per vakje; 4 vakjes passen ruim in één tik


def kolommen(ik: int) -> range:
    """Kolomvolgorde op het scherm: speler 2 ziet het veld gespiegeld."""
    return range(1, BREEDTE + 1) if ik == 1 else range(BREEDTE, 0, -1)


def schermkolom(x: int, ik: int) -> int:
    """Op welke schermkolom (1..13) staat veldkolom x voor kijker ik."""
    return x if ik == 1 else BREEDTE + 1 - x


def kogelbanen(game: Game, ik: int) -> list[dict]:
    """Per schot van de laatste tik: waar de kogel over het scherm vliegt.

    Gridkolommen tellen vanaf 2 (kolom 1 is de rijnummers), gridrijen vanaf 2
    (rij 1 is de kolomnummers). `n` = aantal vakjes inclusief dat van de schutter.
    """
    banen = []
    for schot in game.schoten:
        if not schot.cellen:
            continue
        schutter = game.spelers[schot.schutter]
        van = schermkolom(schutter.x, ik)
        tot = schermkolom(schot.cellen[-1][0], ik)
        banen.append({
            "kol_van": min(van, tot) + 1,
            "kol_tot": max(van, tot) + 2,
            "rij": schutter.y + 1,
            "n": len(schot.cellen) + 1,
            "richting": "rechts" if tot > van else "links",
            "duur": round(len(schot.cellen) * STAP_SECONDEN, 2),
            "schutter": schot.schutter,
            "raak": schot.raak is not None,
        })
    return banen


def veld_matrix(game: Game, ik: int) -> list[list[Cel]]:
    rijen = []
    for y in range(1, HOOGTE + 1):
        rij = []
        for x in kolommen(ik):
            if x == RIVIER_X:
                soort = "br" if y in BRUG_RIJEN else "w"
            else:
                soort = "b" if x < RIVIER_X else "r"
            cel = Cel(x, y, soort, robot=game.robot_op(x, y),
                      gebouw=game.gebouw_op(x, y), schild=game.schild_op(x, y))
            for schot in game.schoten:
                if (x, y) in schot.cellen:
                    cel.spoor = True
                    cel.spoor_index = schot.cellen.index((x, y))
                    if schot.raak == (x, y):
                        cel.raak = True
                        cel.knal_vertraging = round(len(schot.cellen) * STAP_SECONDEN, 2)
            rij.append(cel)
        rijen.append(rij)
    return rijen


def context(game: Game, ik: int) -> dict:
    return {
        "game": game,
        "ik": ik,
        "jij": game.spelers[ik],
        "ander": game.tegenstander(ik),
        "rijen": veld_matrix(game, ik),
        "kolommen": list(kolommen(ik)),
        "kogelbanen": kogelbanen(game, ik),
        "editor": game.editors[ik],
        "log": log_regels(game, ik),
    }


# ---- log "Wat gebeurt er?" ----

def log_tekst(game: Game, ik: int, e: Gebeurtenis) -> str:
    """Eén gebeurtenis als zin vanuit het perspectief van kijker `ik`."""
    mij = e.speler == ik
    wie = "Jij" if mij else game.spelers[e.speler].naam
    doel_mij = e.doel == ik
    doel_naam = game.spelers[e.doel].naam if e.doel is not None else ""
    if e.soort == "loop":
        return f"{wie} loopt {e.tekst} naar ({e.x}, {e.y})"
    if e.soort == "geblokkeerd":
        return f"{wie} loopt tegen iets aan en blijft staan"
    if e.soort == "raak_robot":
        geraakt = "jou" if doel_mij else doel_naam
        return f"{wie} schiet → raakt {geraakt}! {hartjes(e.levens, ROBOT_LEVENS)}"
    if e.soort == "raak_schild":
        van = "jouw schild" if doel_mij else f"het schild van {doel_naam}"
        return f"{wie} schiet → raakt {van} (nog {e.levens})"
    if e.soort == "raak_gebouw":
        toren = "jouw toren" if doel_mij else f"de toren van {doel_naam}"
        return f"{wie} raakt {toren}! 🏰 {hartjes(e.levens, GEBOUW_LEVENS)}"
    if e.soort == "mis":
        return f"{wie} schiet → mis"
    if e.soort == "dood":
        if mij:
            return f"💥 Je robot is kapot! Hij komt terug over {RESPAWN_TIKKEN} seconden"
        return f"💥 De robot van {wie} is kapot!"
    if e.soort == "terug":
        return "Je robot is terug op het startvak" if mij else f"De robot van {wie} is terug"
    if e.soort == "schild":
        return f"{wie} zet een schild op ({e.x}, {e.y})"
    if e.soort == "schild_fout":
        return f"Schild geweigerd: {e.tekst}" if mij else f"{wie} probeert een schild, maar dat mag niet"
    if e.soort == "win":
        return "🏆 Jij wint!" if mij else f"🏆 {wie} wint!"
    return e.soort


def log_regels(game: Game, ik: int, aantal: int = 10) -> list[dict]:
    """De laatste `aantal` gebeurtenissen als regels voor het log, nieuwste eerst."""
    return [
        {"tik": tik, "tijd": mmss(tik), "tekst": log_tekst(game, ik, e), "soort": e.soort, "mij": e.speler == ik}
        for tik, e in list(game.log)[::-1][:aantal]
    ]

    jij, ander = game.spelers[ik], game.tegenstander(ik)
    if not jij.leeft:
        return {"tekst": "💥 Je robot is kapot!", "sub": f"Hij komt terug over {jij.respawn_over}…", "soort": "ik"}
    if not ander.leeft:
        return {"tekst": f"💥 De robot van {ander.naam} is kapot!",
                "sub": f"Komt terug over {ander.respawn_over}…", "soort": "ander"}
    return None


# ---- Jinja-filters ----

def mmss(seconden: int) -> str:
    return f"{seconden // 60}:{seconden % 60:02d}"


def datum(iso: str) -> str:
    jaar, maand, dag = iso[:10].split("-")
    return f"{int(dag)} {MAANDEN[int(maand) - 1]}"


def hartjes(aantal: int, maximum: int) -> str:
    return "❤️" * aantal + "🖤" * (maximum - aantal)


def kleur(nummer: int) -> str:
    return "gb" if nummer == 1 else "gr"


def symbool(markering: str) -> str:
    return SYMBOLEN.get(markering, "")


FILTERS = {"mmss": mmss, "datum": datum, "hartjes": hartjes, "kleur": kleur, "symbool": symbool}


# ---- fragmenten voor de WebSocket (HTMX swapt ze out-of-band op id) ----

def render(templates, naam: str, game: Game, ik: int) -> str:
    return templates.get_template(f"fragments/{naam}.html").render(context(game, ik))


def editor_html(templates, game: Game, ik: int, met_invoer: bool) -> str:
    """Na een editor-actie: regels, markering, hint en de stappenteller (de wachtrij
    verandert bij bevriezen en bij Stop); bij een bevroren regel ook een lege invoer."""
    delen = ["regels", "markering", "hint", "teller"] + (["invoer"] if met_invoer else [])
    return "\n".join(render(templates, d, game, ik) for d in delen)


def tik_html(templates, game: Game, ik: int) -> str:
    """Na een tik: kop, veld, status, log, teller en hint; bij een afgelopen
    spel ook einde en invoer."""
    delen = ["kop", "veld", "status", "log", "teller", "hint"]
    if game.afgelopen:
        delen += ["einde", "invoer"]
    return "\n".join(render(templates, d, game, ik) for d in delen)
