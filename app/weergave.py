"""Alles wat de templates nodig hebben: veldmatrix, context en Jinja-filters."""
from __future__ import annotations

from dataclasses import dataclass

from .game import (BREEDTE, BRUG_RIJEN, HOOGTE, RIVIER_X, Game, Schild, Speler)

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
    raak: bool = False           # hier is iets geraakt in de laatste tik
    kogel: int | None = None     # nummer van de schutter als de kogel hier eindigde zonder te raken


def kolommen(ik: int) -> range:
    """Kolomvolgorde op het scherm: speler 2 ziet het veld gespiegeld."""
    return range(1, BREEDTE + 1) if ik == 1 else range(BREEDTE, 0, -1)


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
                    if schot.raak == (x, y):
                        cel.raak = True
                    elif schot.raak is None and schot.cellen[-1] == (x, y):
                        cel.kogel = schot.schutter
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
        "editor": game.editors[ik],
    }


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
    delen = ["regels", "markering", "hint"] + (["invoer"] if met_invoer else [])
    return "\n".join(render(templates, d, game, ik) for d in delen)


def tik_html(templates, game: Game, ik: int) -> str:
    """Na een tik: kop, veld en status; plus hint als het spel een melding heeft; plus einde."""
    delen = ["kop", "veld", "status"]
    speler = game.spelers[ik]
    if speler.melding:
        game.editors[ik].hint = speler.melding
        speler.melding = None
        delen.append("hint")
    if game.afgelopen:
        delen += ["einde", "invoer"]
    return "\n".join(render(templates, d, game, ik) for d in delen)
