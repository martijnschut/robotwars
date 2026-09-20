"""Parser voor de Robot Wars-taal: één regel tekst in, één commando uit.

Geen afhankelijkheden, zodat dit los te testen is.
"""
from __future__ import annotations

from dataclasses import dataclass

MAX_HERHAAL = 20


@dataclass(frozen=True)
class Move:
    richting: str


@dataclass(frozen=True)
class Shoot:
    pass


@dataclass(frozen=True)
class Shield:
    x: int
    y: int


@dataclass(frozen=True)
class Bomb:
    """Bom op een buurvak: dx en dy zijn -1, 0 of 1 ten opzichte van de robot."""
    dx: int
    dy: int


@dataclass(frozen=True)
class RepeatStart:
    n: int


@dataclass(frozen=True)
class RepeatEnd:
    pass


@dataclass(frozen=True)
class Incomplete:
    """Nog geen commando, maar het kan er nog één worden (bijv. 'robot = vo')."""


@dataclass(frozen=True)
class Invalid:
    """Kan geen commando meer worden; hint is kindvriendelijk Nederlands."""
    hint: str


Step = Move | Shoot | Shield | Bomb
Command = Step | RepeatStart | RepeatEnd
ParseResult = Command | Incomplete | Invalid

HINT_ROBOT = 'Ik ken "{}" niet. Probeer vooruit, achteruit, omhoog, omlaag of schiet.'
HINT_SCHILD = "Schild heeft twee getallen nodig: schild = (x, y), bijvoorbeeld schild = (4, 2)."
HINT_BOM = ("Bom heeft twee getallen van -1 tot 1 nodig: bom = (dx, dy), "
            "bijvoorbeeld bom = (1, 0) voor het vak vóór je.")
HINT_HERHAAL = "Herhaal hoeveel keer? Bijvoorbeeld herhaal 3 keer (maximaal 20)."
HINT_START = "Begin met robot = ..., schild = (...), bom = (...), herhaal ... keer of klaar."
BOM_BEREIK = 1   # dx en dy lopen van -BOM_BEREIK t/m BOM_BEREIK

# Sjablonen zonder spaties; '#' staat voor een getal van 1 of 2 cijfers,
# '±' voor een getal van één cijfer met optioneel een minteken ervoor.
_SJABLONEN = (
    "robot=vooruit",
    "robot=achteruit",
    "robot=omhoog",
    "robot=omlaag",
    "robot=schiet",
    "schild=(#,#)",
    "bom=(±,±)",
    "herhaal#keer",
    "klaar",
)


def _compact(tekst: str) -> str:
    """Kleine letters, alle witruimte weg."""
    return "".join(tekst.lower().split())


def _past(compact: str, sjabloon: str) -> tuple[bool, bool, list[int]]:
    """Vergelijk compact met sjabloon.

    Geeft (compleet, kan_nog, getallen):
    - compleet: de tekst is precies dit sjabloon;
    - kan_nog: de tekst is een begin van dit sjabloon;
    - getallen: de gevonden getallen op de '#'-plekken.
    """
    i = 0
    getallen: list[int] = []
    for teken in sjabloon:
        if i >= len(compact):
            return False, True, getallen
        if teken == "#":
            start = i
            while i < len(compact) and compact[i].isdigit() and i - start < 2:
                i += 1
            if i == start:
                return False, False, getallen
            getallen.append(int(compact[start:i]))
        elif teken == "±":
            start = i
            if compact[i] == "-":
                i += 1
                if i >= len(compact):
                    return False, True, getallen
            if not compact[i].isdigit():
                return False, False, getallen
            i += 1
            getallen.append(int(compact[start:i]))
        else:
            if compact[i] != teken:
                return False, False, getallen
            i += 1
    return i == len(compact), False, getallen


def parse_line(tekst: str) -> ParseResult:
    compact = _compact(tekst)
    if not compact:
        return Incomplete()
    kan_nog = False
    for sjabloon in _SJABLONEN:
        compleet, nog, getallen = _past(compact, sjabloon)
        if compleet:
            return _maak_commando(sjabloon, getallen)
        kan_nog = kan_nog or nog
    if kan_nog:
        return Incomplete()
    return Invalid(_hint(compact, tekst))


def _maak_commando(sjabloon: str, getallen: list[int]) -> ParseResult:
    if sjabloon.startswith("robot="):
        waarde = sjabloon[len("robot="):]
        return Shoot() if waarde == "schiet" else Move(waarde)
    if sjabloon.startswith("schild"):
        return Shield(getallen[0], getallen[1])
    if sjabloon.startswith("bom"):
        dx, dy = getallen
        if not (-BOM_BEREIK <= dx <= BOM_BEREIK and -BOM_BEREIK <= dy <= BOM_BEREIK):
            return Invalid(HINT_BOM)
        return Bomb(dx, dy)
    if sjabloon.startswith("herhaal"):
        n = getallen[0]
        if not 1 <= n <= MAX_HERHAAL:
            return Invalid(HINT_HERHAAL)
        return RepeatStart(n)
    return RepeatEnd()


def _hint(compact: str, tekst: str) -> str:
    if compact.startswith("robot"):
        rest = tekst.split("=", 1)[1].strip() if "=" in tekst else tekst.strip()
        return HINT_ROBOT.format(rest[:40])
    if compact.startswith("schild"):
        return HINT_SCHILD
    if compact.startswith("bom"):
        return HINT_BOM
    if compact.startswith("herhaal"):
        return HINT_HERHAAL
    return HINT_START


def expand(commands: list[Command], max_stappen: int | None = None) -> list[Step]:
    """Rolt herhaal-blokken uit tot een platte lijst stappen.

    Gooit ValueError bij een 'klaar' zonder 'herhaal' of andersom, en (als
    max_stappen is opgegeven) zodra een gesloten blok, of het eindresultaat,
    meer dan max_stappen stappen bevat.
    """
    stapel: list[list[Step]] = [[]]
    tellers: list[int] = []
    for c in commands:
        if isinstance(c, RepeatStart):
            stapel.append([])
            tellers.append(c.n)
        elif isinstance(c, RepeatEnd):
            if len(stapel) == 1:
                raise ValueError("klaar zonder herhaal")
            blok = stapel.pop()
            stapel[-1].extend(blok * tellers.pop())
            if max_stappen is not None and len(stapel[-1]) > max_stappen:
                raise ValueError("te veel stappen")
        else:
            stapel[-1].append(c)
    if len(stapel) > 1:
        raise ValueError("herhaal zonder klaar")
    if max_stappen is not None and len(stapel[-1]) > max_stappen:
        raise ValueError("te veel stappen")
    return stapel[0]
