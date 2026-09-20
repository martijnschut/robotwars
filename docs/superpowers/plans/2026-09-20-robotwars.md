# Robot Wars – implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Een werkend online Robot Wars-spel (twee spelers of tegen Robo) zoals beschreven in `docs/superpowers/specs/2026-09-20-robotwars-design.md`.

**Architecture:** FastAPI-server met alle spellogica in pure Python-modules (`parser`, `game`, `ai`, `editor`, `lobby`, `db`) die los van de server getest worden. De browser krijgt server-side gerenderde Jinja2-HTML; tijdens het spel stuurt de server elke seconde HTML-fragmenten over een WebSocket die HTMX out-of-band in de pagina swapt. Geen eigen JavaScript.

**Tech Stack:** Python ≥3.12 via **uv** (uitsluitend), FastAPI, uvicorn[standard] (WebSockets), Jinja2, python-multipart, SQLite (stdlib `sqlite3`), HTMX 2 + `htmx-ext-ws`, pytest + httpx (dev).

**Taal in code:** Nederlandse namen voor domeinbegrippen (`Speler`, `wachtrij`, `schild`), Engelse namen voor de parser-commando's (`Move`, `Shoot`, `Shield`, `RepeatStart`, `RepeatEnd`) zoals in het ontwerp. Commentaar en teksten in het Nederlands.

**Commits:** elke commit eindigt met de regel
`Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

**Werkwijze:** schrijf bestanden met de Write/Edit-tool, niet met Bash-heredocs
(die breken in deze omgeving op apostrofs). Draai tests altijd met `uv run pytest`.

---

## Bestandsstructuur

```
robotwars/
  pyproject.toml                  uv-project (deps + pytest-config)
  .gitignore
  Caddyfile
  README.md
  app/
    __init__.py
    parser.py        tekst → commando's (Move/Shoot/Shield/RepeatStart/RepeatEnd), Incomplete/Invalid, expand()
    game.py          Game/Speler/Schild/Schot: veld, lopen, schieten, respawn, schilden, wachtrij, winnen
    ai.py            kies_stap(game, nummer): Robo's beslisregels
    editor.py        Editor: regels typen, herhaal-blokken, markeringen, hints
    db.py            ScoreDb (SQLite): sla_op(), top()
    lobby.py         Lobby: sessies (cookie-token), wachtrij, koppelen, games, opruimen
    weergave.py      veld_matrix(), context(), Jinja-filters, fragment-renderers
    main.py          FastAPI: routes, WebSocket, tik-taak, uitzenden
    templates/
      base.html, start.html, wachten.html, spel.html, scorebord.html
      fragments/sprites.html, kop.html, veld.html, status.html,
                regels.html, markering.html, invoer.html, hint.html, einde.html
    static/
      style.css, htmx.min.js, ws.js
  tests/
    conftest.py, test_parser.py, test_game.py, test_ai.py, test_editor.py,
    test_db.py, test_lobby.py, test_weergave.py, test_main.py
```

---

### Task 1: Projectopzet met uv

**Files:**
- Create: `pyproject.toml` (via `uv init`), `app/__init__.py`, `tests/__init__.py`, `tests/test_smoke.py`, `app/static/htmx.min.js`, `app/static/ws.js`
- Modify: `.gitignore`

- [ ] **Step 1: Initialiseer het uv-project en voeg afhankelijkheden toe**

Run (in `C:\programming\robotwars`):
```bash
uv init --bare --name robotwars
uv add fastapi "uvicorn[standard]" jinja2 python-multipart
uv add --dev pytest httpx
```
Expected: `pyproject.toml`, `uv.lock` en `.venv/` bestaan; laatste regel van elke `uv add` toont de geïnstalleerde pakketten.

- [ ] **Step 2: Zet pytest-config en Python-versie in pyproject.toml**

Open `pyproject.toml`; zorg dat het minimaal dit bevat (laat de `dependencies`-lijst zoals uv hem maakte):
```toml
[project]
name = "robotwars"
version = "0.1.0"
description = "Programmeerspel voor kinderen: CT-3000 x Clash Royale"
requires-python = ">=3.12"
dependencies = [
    # door uv add ingevuld
]

[dependency-groups]
dev = [
    # door uv add --dev ingevuld
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: Maak de pakketten en een rooktest**

`app/__init__.py` en `tests/__init__.py`: leeg bestand.

`tests/test_smoke.py`:
```python
def test_python_werkt():
    assert 1 + 1 == 2
```

- [ ] **Step 4: Draai de test**

Run: `uv run pytest -q`
Expected: `1 passed`

- [ ] **Step 5: Download HTMX en de WebSocket-extensie naar static/**

Run:
```bash
mkdir -p app/static app/templates/fragments
curl -L -o app/static/htmx.min.js https://cdn.jsdelivr.net/npm/htmx.org@2/dist/htmx.min.js
curl -L -o app/static/ws.js https://cdn.jsdelivr.net/npm/htmx-ext-ws@2/ws.js
head -c 200 app/static/htmx.min.js; echo; head -c 200 app/static/ws.js
```
Expected: beide bestanden beginnen met JavaScript (bijv. `var htmx=` en `(function(){` / `htmx.defineExtension("ws"`), niet met `<html`.

- [ ] **Step 6: Vul .gitignore aan**

`.gitignore` (volledige inhoud):
```
__pycache__/
*.pyc
.venv/
robotwars.db
.pytest_cache/
.superpowers/
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "Projectopzet met uv, FastAPI en HTMX

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Parser – robot-commando's, Incomplete en Invalid

**Files:**
- Create: `app/parser.py`, `tests/test_parser.py`
- Delete: `tests/test_smoke.py`

- [ ] **Step 1: Schrijf de falende tests**

`tests/test_parser.py`:
```python
from app.parser import parse_line, Move, Shoot, Incomplete, Invalid


def test_robot_vooruit():
    assert parse_line("robot = vooruit") == Move("vooruit")


def test_alle_richtingen():
    for r in ("vooruit", "achteruit", "omhoog", "omlaag"):
        assert parse_line(f"robot = {r}") == Move(r)


def test_schiet():
    assert parse_line("robot = schiet") == Shoot()


def test_hoofdletters_en_spaties_maken_niet_uit():
    assert parse_line("  ROBOT=Vooruit ") == Move("vooruit")


def test_lege_regel_is_incomplete():
    assert parse_line("") == Incomplete()
    assert parse_line("   ") == Incomplete()


def test_half_getypt_is_incomplete():
    assert parse_line("rob") == Incomplete()
    assert parse_line("robot = vo") == Incomplete()
    assert parse_line("robot =") == Incomplete()


def test_onbekende_richting_is_invalid_met_hint():
    r = parse_line("robot = links")
    assert isinstance(r, Invalid)
    assert r.hint == 'Ik ken "links" niet. Probeer vooruit, achteruit, omhoog, omlaag of schiet.'


def test_te_lang_is_invalid():
    assert isinstance(parse_line("robot = vooruitt"), Invalid)


def test_onbekend_begin_is_invalid():
    r = parse_line("lamp = aan")
    assert isinstance(r, Invalid)
    assert r.hint == "Begin met robot = ..., schild = (...), herhaal ... keer of klaar."
```

- [ ] **Step 2: Verwijder de rooktest en draai de tests**

Run: `rm tests/test_smoke.py && uv run pytest -q`
Expected: FAIL met `ModuleNotFoundError: No module named 'app.parser'`

- [ ] **Step 3: Schrijf de parser**

`app/parser.py`:
```python
"""Parser voor de Robot Wars-taal: één regel tekst in, één commando uit.

Geen afhankelijkheden, zodat dit los te testen is.
"""
from __future__ import annotations

from dataclasses import dataclass

RICHTINGEN = ("vooruit", "achteruit", "omhoog", "omlaag")
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


Step = Move | Shoot | Shield
Command = Step | RepeatStart | RepeatEnd
ParseResult = Command | Incomplete | Invalid

HINT_ROBOT = 'Ik ken "{}" niet. Probeer vooruit, achteruit, omhoog, omlaag of schiet.'
HINT_SCHILD = "Schild heeft twee getallen nodig, zoals schild = (4, 2)."
HINT_HERHAAL = "Herhaal hoeveel keer? Bijvoorbeeld herhaal 3 keer (maximaal 20)."
HINT_START = "Begin met robot = ..., schild = (...), herhaal ... keer of klaar."

# Sjablonen zonder spaties; '#' staat voor een getal van 1 of 2 cijfers.
_SJABLONEN = (
    "robot=vooruit",
    "robot=achteruit",
    "robot=omhoog",
    "robot=omlaag",
    "robot=schiet",
    "schild=(#,#)",
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
    if sjabloon.startswith("herhaal"):
        n = getallen[0]
        if not 1 <= n <= MAX_HERHAAL:
            return Invalid(HINT_HERHAAL)
        return RepeatStart(n)
    return RepeatEnd()


def _hint(compact: str, tekst: str) -> str:
    if compact.startswith("robot"):
        rest = tekst.split("=", 1)[1].strip() if "=" in tekst else tekst.strip()
        return HINT_ROBOT.format(rest)
    if compact.startswith("schild"):
        return HINT_SCHILD
    if compact.startswith("herhaal"):
        return HINT_HERHAAL
    return HINT_START
```

- [ ] **Step 4: Draai de tests**

Run: `uv run pytest -q`
Expected: `9 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Parser: robot-commando's, Incomplete en Invalid met hints

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Parser – schild, herhaal en klaar

**Files:**
- Modify: `tests/test_parser.py`
- (`app/parser.py` is al compleet voor deze commando's; deze taak bewijst dat met tests)

- [ ] **Step 1: Voeg tests toe**

Onderaan `tests/test_parser.py`:
```python
from app.parser import Shield, RepeatStart, RepeatEnd, HINT_SCHILD, HINT_HERHAAL


def test_schild_met_coordinaten():
    assert parse_line("schild = (4, 2)") == Shield(4, 2)
    assert parse_line("schild=(12,7)") == Shield(12, 7)


def test_schild_half_getypt_is_incomplete():
    assert parse_line("schild = (4") == Incomplete()
    assert parse_line("schild = (4,") == Incomplete()


def test_schild_zonder_getallen_is_invalid():
    r = parse_line("schild = (a, b)")
    assert isinstance(r, Invalid)
    assert r.hint == HINT_SCHILD


def test_herhaal():
    assert parse_line("herhaal 3 keer") == RepeatStart(3)
    assert parse_line("HERHAAL 20 KEER") == RepeatStart(20)


def test_herhaal_half_is_incomplete():
    assert parse_line("herhaal 3") == Incomplete()
    assert parse_line("herhaal 3 ke") == Incomplete()


def test_herhaal_nul_of_te_veel_is_invalid():
    for tekst in ("herhaal 0 keer", "herhaal 21 keer", "herhaal 100 keer", "herhaal keer"):
        r = parse_line(tekst)
        assert isinstance(r, Invalid), tekst
        assert r.hint == HINT_HERHAAL


def test_klaar():
    assert parse_line("klaar") == RepeatEnd()
    assert parse_line("kl") == Incomplete()
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest -q`
Expected: `16 passed`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "Parser: tests voor schild, herhaal en klaar

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Parser – expand (herhaal uitrollen)

**Files:**
- Modify: `app/parser.py`, `tests/test_parser.py`

- [ ] **Step 1: Schrijf de falende tests**

Onderaan `tests/test_parser.py`:
```python
import pytest
from app.parser import expand


def test_expand_zonder_herhaal():
    assert expand([Move("vooruit"), Shoot()]) == [Move("vooruit"), Shoot()]


def test_expand_herhaal_3_keer_geeft_3_stappen():
    cmds = [RepeatStart(3), Move("vooruit"), RepeatEnd()]
    assert expand(cmds) == [Move("vooruit")] * 3


def test_expand_genest():
    cmds = [RepeatStart(2), Move("omhoog"), RepeatStart(2), Shoot(), RepeatEnd(), RepeatEnd()]
    assert expand(cmds) == [Move("omhoog"), Shoot(), Shoot()] * 2


def test_expand_klaar_zonder_herhaal():
    with pytest.raises(ValueError):
        expand([RepeatEnd()])


def test_expand_herhaal_zonder_klaar():
    with pytest.raises(ValueError):
        expand([RepeatStart(2), Move("vooruit")])
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest -q`
Expected: FAIL met `ImportError: cannot import name 'expand'`

- [ ] **Step 3: Voeg expand toe**

Onderaan `app/parser.py`:
```python
def expand(commands: list[Command]) -> list[Step]:
    """Rolt herhaal-blokken uit tot een platte lijst stappen.

    Gooit ValueError bij een 'klaar' zonder 'herhaal' of andersom.
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
        else:
            stapel[-1].append(c)
    if len(stapel) > 1:
        raise ValueError("herhaal zonder klaar")
    return stapel[0]
```

- [ ] **Step 4: Draai de tests**

Run: `uv run pytest -q`
Expected: `21 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Parser: expand rolt herhaal-blokken uit

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Game – veld, spelers en lopen

**Files:**
- Create: `app/game.py`, `tests/test_game.py`

- [ ] **Step 1: Schrijf de falende tests**

`tests/test_game.py`:
```python
from app.game import Game, is_water, in_veld, eigen_helft, BREEDTE, HOOGTE
from app.parser import Move


def nieuw():
    return Game("g1", "Wessel", "Papa")


def test_veldfuncties():
    assert in_veld(1, 1) and in_veld(BREEDTE, HOOGTE)
    assert not in_veld(0, 1) and not in_veld(14, 1) and not in_veld(1, 8)
    assert is_water(7, 1) and is_water(7, 4)
    assert not is_water(7, 2) and not is_water(7, 6)   # bruggen
    assert not is_water(6, 4)
    assert eigen_helft(1, 6) and not eigen_helft(1, 7) and not eigen_helft(1, 8)
    assert eigen_helft(2, 8) and not eigen_helft(2, 7)


def test_startopstelling():
    g = nieuw()
    s1, s2 = g.spelers[1], g.spelers[2]
    assert (s1.x, s1.y) == (2, 4) and s1.gebouw == (1, 4) and s1.richting == 1
    assert (s2.x, s2.y) == (12, 4) and s2.gebouw == (13, 4) and s2.richting == -1
    assert s1.robot_levens == 5 and s1.gebouw_levens == 5 and s1.schilden_over == 3
    assert g.tik == 0 and g.winnaar is None and not g.afgelopen


def test_vooruit_is_richting_tegenstander():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("vooruit")])
    g.voeg_stappen_toe(2, [Move("vooruit")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (3, 4)
    assert (g.spelers[2].x, g.spelers[2].y) == (11, 4)
    assert g.tik == 1


def test_een_stap_per_tik():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog"), Move("omhoog"), Move("vooruit")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 3)
    g.tick()
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (3, 2)
    assert len(g.spelers[1].wachtrij) == 0


def test_niet_het_water_in():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 6, 4
    g.voeg_stappen_toe(1, [Move("vooruit")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (6, 4)


def test_wel_over_de_brug():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 6, 2
    g.voeg_stappen_toe(1, [Move("vooruit"), Move("vooruit")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (7, 2)
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (8, 2)


def test_niet_buiten_het_veld_of_in_gebouw_of_robot():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.voeg_stappen_toe(1, [Move("omhoog")])
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 1)
    g.spelers[1].x, g.spelers[1].y = 2, 4
    g.voeg_stappen_toe(1, [Move("achteruit")])   # gebouw op (1,4)
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 4)
    g.spelers[2].x, g.spelers[2].y = 3, 4
    g.voeg_stappen_toe(1, [Move("vooruit")])     # andere robot op (3,4)
    g.tick()
    assert (g.spelers[1].x, g.spelers[1].y) == (2, 4)
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_game.py -q`
Expected: FAIL met `ModuleNotFoundError: No module named 'app.game'`

- [ ] **Step 3: Schrijf game.py (eerste versie: model en lopen)**

`app/game.py`:
```python
"""Spelregels van Robot Wars: veld, lopen, schieten, schilden, respawn, winnen.

Pure Python; de server roept alleen voeg_stappen_toe(), stop(), tick() en
geef_op() aan en leest de toestand voor de weergave.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from .parser import Move, Shoot, Shield, Step

BREEDTE, HOOGTE = 13, 7
RIVIER_X = 7
BRUG_RIJEN = (2, 6)
SCHIET_BEREIK = 4
GEBOUW_LEVENS = 5
ROBOT_LEVENS = 5
SCHILD_LEVENS = 3
SCHILDEN_PER_SPELER = 3
RESPAWN_TIKKEN = 3
MAX_WACHTRIJ = 50

# per spelernummer: gebouw, startvak en looprichting (+1 = naar rechts)
GEBOUW = {1: (1, 4), 2: (13, 4)}
START = {1: (2, 4), 2: (12, 4)}
RICHTING = {1: 1, 2: -1}

MELD_OP = "Je schilden zijn op."
MELD_BESTAAT_NIET = "Dat vak bestaat niet."
MELD_HELFT = "Een schild mag alleen op je eigen helft."
MELD_STARTVAK = "Niet op een startvak, anders kan een robot nooit meer terugkomen."
MELD_BEZET = "Dat vak is niet leeg."
MELD_DRUK = "Wacht even, je robot is nog bezig."


def in_veld(x: int, y: int) -> bool:
    return 1 <= x <= BREEDTE and 1 <= y <= HOOGTE


def is_water(x: int, y: int) -> bool:
    return x == RIVIER_X and y not in BRUG_RIJEN


def eigen_helft(nummer: int, x: int) -> bool:
    return 1 <= x <= 6 if nummer == 1 else 8 <= x <= BREEDTE


@dataclass
class Schild:
    x: int
    y: int
    eigenaar: int
    levens: int = SCHILD_LEVENS


@dataclass
class Schot:
    """Eén schot in de laatste tik, voor de weergave van de kogelbaan."""
    schutter: int
    cellen: list[tuple[int, int]]        # vakjes die de kogel passeerde (incl. trefvak)
    raak: tuple[int, int] | None         # geraakt vak, of None als niets geraakt


@dataclass
class Speler:
    nummer: int
    naam: str
    is_computer: bool = False
    x: int = 0
    y: int = 0
    robot_levens: int = ROBOT_LEVENS
    gebouw_levens: int = GEBOUW_LEVENS
    schilden_over: int = SCHILDEN_PER_SPELER
    wachtrij: deque[Step] = field(default_factory=deque)
    respawn_over: int = 0        # tikken tot de robot terugkomt (0 = leeft of wacht niet)
    tegoed: int = 0              # stappen die Robo nog mag doen
    melding: str | None = None   # foutmelding uit het spel (bijv. schild geweigerd)

    def __post_init__(self) -> None:
        self.x, self.y = START[self.nummer]

    @property
    def leeft(self) -> bool:
        return self.robot_levens > 0

    @property
    def richting(self) -> int:
        return RICHTING[self.nummer]

    @property
    def gebouw(self) -> tuple[int, int]:
        return GEBOUW[self.nummer]

    @property
    def startvak(self) -> tuple[int, int]:
        return START[self.nummer]


class Game:
    def __init__(self, id: str, naam1: str, naam2: str, tegen_computer: bool = False,
                 brein: Callable[["Game", int], Step | None] | None = None) -> None:
        self.id = id
        self.tegen_computer = tegen_computer
        self.brein = brein   # kiest Robo's stap; alleen gebruikt als tegen_computer
        self.spelers = {
            1: Speler(1, naam1),
            2: Speler(2, naam2, is_computer=tegen_computer),
        }
        self.schilden: list[Schild] = []
        self.schoten: list[Schot] = []   # schoten van de laatste tik
        self.tik = 0
        self.winnaar: int | None = None
        self.opgegeven = False           # winst doordat de ander wegging: niet voor het scorebord
        self.geeindigd_op: float | None = None
        self.score_opgeslagen = False
        # Gevuld door de lobby/server: editor per speler en wanneer een speler voor het laatst verbonden was.
        self.editors: dict[int, object] = {}
        self.laatst_gezien: dict[int, float] = {1: time.time(), 2: time.time()}

    # ---- vragen aan het veld ----

    @property
    def afgelopen(self) -> bool:
        return self.winnaar is not None

    def tegenstander(self, nummer: int) -> Speler:
        return self.spelers[2 if nummer == 1 else 1]

    def schild_op(self, x: int, y: int) -> Schild | None:
        return next((s for s in self.schilden if (s.x, s.y) == (x, y)), None)

    def robot_op(self, x: int, y: int) -> Speler | None:
        return next((p for p in self.spelers.values() if p.leeft and (p.x, p.y) == (x, y)), None)

    def gebouw_op(self, x: int, y: int) -> Speler | None:
        return next((p for p in self.spelers.values() if p.gebouw == (x, y)), None)

    def is_vrij(self, x: int, y: int) -> bool:
        return (in_veld(x, y) and not is_water(x, y)
                and self.schild_op(x, y) is None
                and self.gebouw_op(x, y) is None
                and self.robot_op(x, y) is None)

    # ---- acties van buiten ----

    def voeg_stappen_toe(self, nummer: int, stappen: list[Step]) -> bool:
        """Zet stappen in de wachtrij. False als de rij te vol zou worden."""
        speler = self.spelers[nummer]
        if len(speler.wachtrij) + len(stappen) > MAX_WACHTRIJ:
            return False
        speler.wachtrij.extend(stappen)
        if self.tegen_computer and nummer == 1:
            self.spelers[2].tegoed += len(stappen)
        return True

    def stop(self, nummer: int) -> None:
        self.spelers[nummer].wachtrij.clear()

    def geef_op(self, nummer: int) -> None:
        """Speler `nummer` is weg; de ander wint, maar dit telt niet voor het scorebord."""
        if not self.afgelopen:
            self.opgegeven = True
            self._zet_winnaar(self.tegenstander(nummer).nummer)

    def tick(self) -> None:
        """Eén seconde spel: elke speler doet één stap (speler 1 eerst)."""
        if self.afgelopen:
            return
        self.schoten = []
        self.tik += 1
        # Eerst terugkomen (zodat een robot die net dood is deze tik niet al aftelt),
        # dan handelen: speler 1 eerst, dan speler 2.
        for speler in self.spelers.values():
            if speler.respawn_over > 0:
                self._respawn(speler)
        for speler in (self.spelers[1], self.spelers[2]):
            if not speler.leeft:
                continue
            if speler.is_computer:
                if speler.tegoed > 0 and self.brein is not None:
                    speler.tegoed -= 1
                    stap = self.brein(self, speler.nummer)
                    if stap is not None:
                        self._voer_uit(speler, stap)
            elif speler.wachtrij:
                self._voer_uit(speler, speler.wachtrij.popleft())
            if self.afgelopen:
                return

    # ---- intern ----

    def _zet_winnaar(self, nummer: int) -> None:
        self.winnaar = nummer
        self.geeindigd_op = time.time()

    def _respawn(self, speler: Speler) -> None:
        speler.respawn_over -= 1
        if speler.respawn_over == 0:
            if self.robot_op(*speler.startvak) is None:
                speler.x, speler.y = speler.startvak
                speler.robot_levens = ROBOT_LEVENS
            else:
                speler.respawn_over = 1   # volgende tik opnieuw proberen

    def _voer_uit(self, speler: Speler, stap: Step) -> None:
        if isinstance(stap, Move):
            self._loop(speler, stap.richting)
        elif isinstance(stap, Shoot):
            self._schiet(speler)
        elif isinstance(stap, Shield):
            self._zet_schild(speler, stap.x, stap.y)

    def _loop(self, speler: Speler, richting: str) -> None:
        dx, dy = {
            "vooruit": (speler.richting, 0),
            "achteruit": (-speler.richting, 0),
            "omhoog": (0, -1),
            "omlaag": (0, 1),
        }[richting]
        doel = (speler.x + dx, speler.y + dy)
        if self.is_vrij(*doel):
            speler.x, speler.y = doel

    def _schiet(self, speler: Speler) -> None:
        raise NotImplementedError   # Task 6

    def _zet_schild(self, speler: Speler, x: int, y: int) -> None:
        raise NotImplementedError   # Task 7
```

- [ ] **Step 4: Draai de tests**

Run: `uv run pytest -q`
Expected: `28 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Game: veld, spelers, wachtrij en lopen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Game – schieten, levens, respawn en winnen

**Files:**
- Modify: `app/game.py`, `tests/test_game.py`

- [ ] **Step 1: Schrijf de falende tests**

Onderaan `tests/test_game.py`:
```python
from app.game import Schild, RESPAWN_TIKKEN
from app.parser import Shoot


def test_schot_raakt_robot_op_afstand_4_niet_op_5():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 4, 3
    g.spelers[2].x, g.spelers[2].y = 8, 3        # afstand 4
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.spelers[2].robot_levens == 4
    assert g.schoten[0].raak == (8, 3)
    assert g.schoten[0].cellen == [(5, 3), (6, 3), (7, 3), (8, 3)]
    g.spelers[2].x = 9                            # afstand 5
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.spelers[2].robot_levens == 4
    assert g.schoten[0].raak is None


def test_schot_stopt_bij_schild():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 2
    g.schilden.append(Schild(4, 2, eigenaar=1))
    g.spelers[2].x, g.spelers[2].y = 5, 2
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.spelers[2].robot_levens == 5
    assert g.schild_op(4, 2).levens == 2


def test_schild_verdwijnt_na_3_treffers():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 2
    g.schilden.append(Schild(4, 2, eigenaar=1))
    g.voeg_stappen_toe(1, [Shoot(), Shoot(), Shoot()])
    for _ in range(3):
        g.tick()
    assert g.schild_op(4, 2) is None


def test_robot_gaat_dood_en_komt_terug_op_startvak():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 8, 1
    g.spelers[2].x, g.spelers[2].y = 10, 1
    g.spelers[2].robot_levens = 1
    g.voeg_stappen_toe(2, [Move("vooruit")])     # wordt gewist bij dood
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    s2 = g.spelers[2]
    assert not s2.leeft and s2.respawn_over == RESPAWN_TIKKEN
    assert len(s2.wachtrij) == 0
    assert g.robot_op(10, 1) is None             # dode robot blokkeert niets
    for _ in range(RESPAWN_TIKKEN):
        g.tick()
    assert s2.leeft and s2.robot_levens == 5 and (s2.x, s2.y) == (12, 4)


def test_respawn_wacht_als_startvak_bezet():
    g = nieuw()
    g.spelers[2].robot_levens = 0
    g.spelers[2].respawn_over = 1
    g.spelers[1].x, g.spelers[1].y = 12, 4       # staat op het startvak van speler 2
    g.tick()
    assert not g.spelers[2].leeft
    g.spelers[1].x = 11
    g.tick()
    assert g.spelers[2].leeft


def test_gebouw_kapot_is_winst():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 9, 4        # 4 vakjes van gebouw (13,4)
    g.spelers[2].x, g.spelers[2].y = 12, 1       # uit de weg
    g.voeg_stappen_toe(1, [Shoot()] * 5)
    for _ in range(4):
        g.tick()
    assert g.spelers[2].gebouw_levens == 1 and not g.afgelopen
    g.tick()
    assert g.spelers[2].gebouw_levens == 0
    assert g.winnaar == 1 and g.afgelopen and g.tik == 5
    g.tick()                                     # na afloop gebeurt niets meer
    assert g.tik == 5


def test_speler_1_wint_bij_gelijktijdige_treffer():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 9, 4
    g.spelers[2].x, g.spelers[2].y = 5, 4
    g.spelers[1].gebouw_levens = 1
    g.spelers[2].gebouw_levens = 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.voeg_stappen_toe(2, [Shoot()])
    g.tick()
    assert g.winnaar == 1 and g.spelers[1].gebouw_levens == 1


def test_geef_op():
    g = nieuw()
    g.geef_op(2)
    assert g.winnaar == 1 and g.opgegeven and g.geeindigd_op is not None
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_game.py -q`
Expected: 8 nieuwe tests FAIL met `NotImplementedError`

- [ ] **Step 3: Implementeer _schiet**

Vervang in `app/game.py` de methode `_schiet`:
```python
    def _schiet(self, speler: Speler) -> None:
        """Kogel vliegt vooruit, max SCHIET_BEREIK vakjes, en raakt het eerste
        schild, de eerste robot of het eerste gebouw dat hij tegenkomt."""
        cellen: list[tuple[int, int]] = []
        raak: tuple[int, int] | None = None
        for i in range(1, SCHIET_BEREIK + 1):
            x, y = speler.x + speler.richting * i, speler.y
            if not in_veld(x, y):
                break
            cellen.append((x, y))
            schild = self.schild_op(x, y)
            if schild is not None:
                schild.levens -= 1
                if schild.levens == 0:
                    self.schilden.remove(schild)
                raak = (x, y)
                break
            robot = self.robot_op(x, y)
            if robot is not None:
                robot.robot_levens -= 1
                if robot.robot_levens == 0:
                    robot.respawn_over = RESPAWN_TIKKEN
                    robot.wachtrij.clear()
                raak = (x, y)
                break
            gebouw = self.gebouw_op(x, y)
            if gebouw is not None:
                gebouw.gebouw_levens -= 1
                if gebouw.gebouw_levens == 0:
                    self._zet_winnaar(self.tegenstander(gebouw.nummer).nummer)
                raak = (x, y)
                break
        self.schoten.append(Schot(speler.nummer, cellen, raak))
```

- [ ] **Step 4: Draai de tests**

Run: `uv run pytest -q`
Expected: `36 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Game: schieten, levens, respawn en winnen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Game – schilden zetten en wachtrij-limiet

**Files:**
- Modify: `app/game.py`, `tests/test_game.py`

- [ ] **Step 1: Schrijf de falende tests**

Onderaan `tests/test_game.py`:
```python
from app.game import (MELD_OP, MELD_BESTAAT_NIET, MELD_HELFT, MELD_STARTVAK,
                      MELD_BEZET, MAX_WACHTRIJ)
from app.parser import Shield as ShieldCmd


def zet(g, nummer, x, y):
    g.spelers[nummer].melding = None      # de server wist meldingen na het tonen; hier doen we dat zelf
    g.voeg_stappen_toe(nummer, [ShieldCmd(x, y)])
    g.tick()
    return g.spelers[nummer].melding


def test_schild_zetten_op_eigen_helft():
    g = nieuw()
    assert zet(g, 1, 4, 3) is None
    assert g.schild_op(4, 3).eigenaar == 1
    assert g.spelers[1].schilden_over == 2
    assert zet(g, 2, 11, 5) is None
    assert g.spelers[2].schilden_over == 2


def test_schild_niet_op_andere_helft_of_rivier():
    g = nieuw()
    assert zet(g, 1, 9, 3) == MELD_HELFT
    assert zet(g, 1, 7, 2) == MELD_HELFT
    assert zet(g, 2, 4, 3) == MELD_HELFT
    assert g.spelers[1].schilden_over == 3     # geweigerd telt niet


def test_schild_niet_buiten_veld_startvak_of_bezet():
    g = nieuw()
    assert zet(g, 1, 0, 3) == MELD_BESTAAT_NIET
    assert zet(g, 1, 2, 4) == MELD_STARTVAK
    assert zet(g, 1, 1, 4) == MELD_BEZET       # gebouw
    g.spelers[2].x, g.spelers[2].y = 5, 5
    assert zet(g, 1, 5, 5) == MELD_BEZET       # robot
    assert zet(g, 1, 4, 3) is None
    assert zet(g, 1, 4, 3) == MELD_BEZET       # al een schild


def test_maximaal_drie_schilden():
    g = nieuw()
    for y in (1, 2, 3):
        assert zet(g, 1, 4, y) is None
    assert zet(g, 1, 4, 5) == MELD_OP


def test_wachtrij_maximaal_50():
    g = nieuw()
    assert g.voeg_stappen_toe(1, [Move("omhoog")] * MAX_WACHTRIJ)
    assert not g.voeg_stappen_toe(1, [Move("omhoog")])
    assert len(g.spelers[1].wachtrij) == MAX_WACHTRIJ
    g.stop(1)
    assert len(g.spelers[1].wachtrij) == 0
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_game.py -q`
Expected: 4 tests FAIL met `NotImplementedError`, `test_wachtrij_maximaal_50` PASS

- [ ] **Step 3: Implementeer _zet_schild**

Vervang in `app/game.py` de methode `_zet_schild`:
```python
    def _zet_schild(self, speler: Speler, x: int, y: int) -> None:
        if speler.schilden_over == 0:
            speler.melding = MELD_OP
        elif not in_veld(x, y):
            speler.melding = MELD_BESTAAT_NIET
        elif not eigen_helft(speler.nummer, x):
            speler.melding = MELD_HELFT
        elif (x, y) in START.values():
            speler.melding = MELD_STARTVAK
        elif not self.is_vrij(x, y):
            speler.melding = MELD_BEZET
        else:
            self.schilden.append(Schild(x, y, speler.nummer))
            speler.schilden_over -= 1
```

- [ ] **Step 4: Draai de tests**

Run: `uv run pytest -q`
Expected: `41 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Game: schilden zetten met regels, wachtrij-limiet

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Robo (ai.py)

**Files:**
- Create: `app/ai.py`, `tests/test_ai.py`

- [ ] **Step 1: Schrijf de falende tests**

`tests/test_ai.py`:
```python
from app.ai import kies_stap, SCHILD_VAK
from app.game import Game, Schild
from app.parser import Move, Shoot, Shield


def nieuw():
    return Game("g", "Wessel", "Robo", tegen_computer=True, brein=kies_stap)


def test_schiet_op_robot_in_dezelfde_rij_binnen_bereik():
    g = nieuw()
    g.spelers[2].x, g.spelers[2].y = 10, 3
    g.spelers[1].x, g.spelers[1].y = 6, 3       # afstand 4, vóór Robo
    assert kies_stap(g, 2) == Shoot()
    g.spelers[1].x = 5                           # afstand 5: te ver
    assert kies_stap(g, 2) != Shoot()
    g.spelers[1].x = 11                          # achter Robo
    assert kies_stap(g, 2) != Shoot()


def test_schiet_niet_door_een_schild_heen_op_robot():
    g = nieuw()
    g.spelers[2].x, g.spelers[2].y = 10, 3
    g.spelers[1].x, g.spelers[1].y = 7, 3
    g.schilden.append(Schild(8, 3, eigenaar=2))
    # schild staat in de weg van het lopen én van het schot op de robot: schiet het schild kapot
    assert kies_stap(g, 2) == Shoot() or isinstance(kies_stap(g, 2), Move)


def test_schiet_op_gebouw_binnen_bereik():
    g = nieuw()
    g.spelers[2].x, g.spelers[2].y = 5, 4        # gebouw (1,4) op afstand 4
    g.spelers[1].x, g.spelers[1].y = 2, 1        # uit de weg
    assert kies_stap(g, 2) == Shoot()


def test_zet_schild_als_vijand_op_eigen_helft():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 9, 1        # op Robo's helft, niet in Robo's rij
    g.spelers[2].x, g.spelers[2].y = 12, 4
    assert kies_stap(g, 2) == Shield(*SCHILD_VAK)
    g.schilden.append(Schild(*SCHILD_VAK, eigenaar=2))
    assert kies_stap(g, 2) != Shield(*SCHILD_VAK)   # vak bezet: iets anders doen


def test_loopt_naar_dichtstbijzijnde_brug_en_dan_vooruit():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 1        # uit de weg (anders schiet Robo op rij 4)
    r = g.spelers[2]
    r.x, r.y = 12, 4
    assert kies_stap(g, 2) == Move("omhoog")     # brug op rij 2 is even ver als 6; kies 2
    r.y = 2
    assert kies_stap(g, 2) == Move("vooruit")
    r.x = 7                                      # op de brug
    assert kies_stap(g, 2) == Move("vooruit")
    r.x = 6                                      # over de rivier: naar rij 4
    assert kies_stap(g, 2) == Move("omlaag")
    r.y = 4
    assert kies_stap(g, 2) == Move("vooruit")    # tot binnen bereik (rule 2 schiet dan)
    r.y = 5
    assert kies_stap(g, 2) == Move("omhoog")


def test_schild_in_de_weg_op_rij_4_wordt_kapotgeschoten():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.spelers[2].x, g.spelers[2].y = 6, 4
    g.schilden.append(Schild(5, 4, eigenaar=1))
    assert kies_stap(g, 2) == Shoot()


def test_andere_brug_als_weg_geblokkeerd():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 12, 3       # vijand blokkeert 'omhoog' vanaf (12,4)
    g.spelers[2].x, g.spelers[2].y = 12, 4
    g.spelers[2].schilden_over = 0               # anders zet hij eerst een schild
    assert kies_stap(g, 2) == Move("omlaag")


def test_dode_robo_doet_niets():
    g = nieuw()
    g.spelers[2].robot_levens = 0
    assert kies_stap(g, 2) is None


def test_tegoed_in_het_spel():
    g = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog"), Move("omhoog")])
    assert g.spelers[2].tegoed == 2
    g.tick()
    assert g.spelers[2].tegoed == 1
    assert (g.spelers[2].x, g.spelers[2].y) == (12, 3)   # Robo liep omhoog
    g.tick()
    g.tick()
    assert g.spelers[2].tegoed == 0
    assert (g.spelers[2].x, g.spelers[2].y) == (12, 2)   # niet verder zonder tegoed
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_ai.py -q`
Expected: FAIL met `ModuleNotFoundError: No module named 'app.ai'`

- [ ] **Step 3: Schrijf ai.py**

`app/ai.py`:
```python
"""Robo, de computerspeler: kiest per tik één stap op basis van het actuele veld."""
from __future__ import annotations

from .game import Game, Speler, BRUG_RIJEN, RIVIER_X, SCHIET_BEREIK, eigen_helft
from .parser import Move, Shoot, Shield, Step

SCHILD_VAK = (11, 4)   # vóór Robo's startvak (12,4), dus de kogel raakt het schild eerder dan de toren

_DELTA = {"vooruit": (1, 0), "achteruit": (-1, 0), "omhoog": (0, -1), "omlaag": (0, 1)}


def kies_stap(game: Game, nummer: int = 2) -> Step | None:
    ik = game.spelers[nummer]
    vijand = game.tegenstander(nummer)
    if not ik.leeft:
        return None
    # 1. vijandelijke robot vóór ons, zelfde rij, binnen bereik, niets ertussen
    if vijand.leeft and _kan_raken(game, ik, (vijand.x, vijand.y)):
        return Shoot()
    # 2. vijandelijk gebouw binnen bereik
    if _kan_raken(game, ik, vijand.gebouw):
        return Shoot()
    # 3. vijand op onze helft: schild vóór ons startvak
    if (vijand.leeft and eigen_helft(nummer, vijand.x)
            and ik.schilden_over > 0 and game.is_vrij(*SCHILD_VAK)):
        return Shield(*SCHILD_VAK)
    # 4. lopen
    return _loop_stap(game, ik, vijand)


def _kan_raken(game: Game, ik: Speler, doel: tuple[int, int]) -> bool:
    """Ligt doel vóór ons in dezelfde rij, binnen bereik, zonder schild of robot ertussen?"""
    dx, dy = doel
    if dy != ik.y:
        return False
    afstand = (dx - ik.x) * ik.richting
    if not 1 <= afstand <= SCHIET_BEREIK:
        return False
    for i in range(1, afstand):
        x = ik.x + ik.richting * i
        if game.schild_op(x, ik.y) is not None or game.robot_op(x, ik.y) is not None:
            return False
    return True


def _doel(ik: Speler, richting: str) -> tuple[int, int]:
    dx, dy = _DELTA[richting]
    return ik.x + dx * ik.richting if dx else ik.x, ik.y + dy


def _stap_of_schot(game: Game, ik: Speler, richting: str) -> Step | None:
    """Zet een stap als het vak vrij is. Staat er vooruit een schild in de weg,
    schiet er dan op. Anders None (even wachten)."""
    x, y = _doel(ik, richting)
    if game.is_vrij(x, y):
        return Move(richting)
    if richting == "vooruit" and game.schild_op(x, y) is not None:
        return Shoot()
    return None


def _loop_stap(game: Game, ik: Speler, vijand: Speler) -> Step | None:
    if ik.x == RIVIER_X:                         # op de brug: doorlopen
        return _stap_of_schot(game, ik, "vooruit")
    over = (ik.x - RIVIER_X) * ik.richting > 0   # al aan de kant van de vijand
    if not over:
        brug = min(BRUG_RIJEN, key=lambda rij: (abs(rij - ik.y), rij))
        if ik.y == brug:
            return _stap_of_schot(game, ik, "vooruit")
        stap = _stap_of_schot(game, ik, "omhoog" if brug < ik.y else "omlaag")
        if stap is not None:
            return stap
        andere = BRUG_RIJEN[1] if brug == BRUG_RIJEN[0] else BRUG_RIJEN[0]
        return _stap_of_schot(game, ik, "omhoog" if andere < ik.y else "omlaag")
    doel_y = vijand.gebouw[1]
    if ik.y == doel_y:
        return _stap_of_schot(game, ik, "vooruit")
    return _stap_of_schot(game, ik, "omhoog" if doel_y < ik.y else "omlaag")
```

- [ ] **Step 4: Draai de tests**

Run: `uv run pytest -q`
Expected: `50 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Robo: beslisregels en tegoed

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Editor – regels typen, herhaal-blokken, markeringen

**Files:**
- Create: `app/editor.py`, `tests/test_editor.py`

Markeringen zijn woorden (voor CSS-klassen): `""` (bezig), `"fout"` (!), `"wacht"` (…), `"ok"` (✓).

- [ ] **Step 1: Schrijf de falende tests**

`tests/test_editor.py`:
```python
from app.editor import Editor, Regel, HINT_KLAAR
from app.game import Game, MELD_DRUK
from app.parser import Move, Shoot


def nieuw():
    g = Game("g", "Wessel", "Papa")
    return g, Editor()


def test_half_getypt_geen_markering_niets_uitgevoerd():
    g, e = nieuw()
    assert e.verwerk(g, 1, "robot = vo") is False
    assert e.markering == "" and e.hint is None and e.regels == []
    assert len(g.spelers[1].wachtrij) == 0


def test_fout_geeft_markering_en_hint():
    g, e = nieuw()
    assert e.verwerk(g, 1, "robot = links") is False
    assert e.markering == "fout"
    assert "links" in e.hint


def test_geldig_commando_wordt_direct_uitgevoerd_en_bevroren():
    g, e = nieuw()
    assert e.verwerk(g, 1, "robot = vooruit") is True
    assert list(g.spelers[1].wachtrij) == [Move("vooruit")]
    assert e.regels == [Regel("ok", "robot = vooruit", 0)]
    assert e.markering == "" and e.hint is None


def test_herhaal_blok_wordt_pas_bij_klaar_uitgevoerd():
    g, e = nieuw()
    assert e.verwerk(g, 1, "herhaal 3 keer") is True
    assert e.markering == "wacht"
    assert e.regels[-1] == Regel("wacht", "herhaal 3 keer", 0)
    assert e.verwerk(g, 1, "robot = vooruit") is True
    assert e.regels[-1] == Regel("wacht", "robot = vooruit", 1)
    assert len(g.spelers[1].wachtrij) == 0
    assert e.verwerk(g, 1, "klaar") is True
    assert list(g.spelers[1].wachtrij) == [Move("vooruit")] * 3
    assert [r.markering for r in e.regels] == ["ok", "ok", "ok"]
    assert e.regels[-1] == Regel("ok", "klaar", 0)
    assert e.markering == ""


def test_genest_blok():
    g, e = nieuw()
    for tekst in ("herhaal 2 keer", "robot = omhoog", "herhaal 2 keer", "robot = schiet", "klaar"):
        e.verwerk(g, 1, tekst)
    assert e.markering == "wacht"                  # buitenste blok nog open
    assert e.regels[3].inspringing == 2
    e.verwerk(g, 1, "klaar")
    assert list(g.spelers[1].wachtrij) == [Move("omhoog"), Shoot(), Shoot()] * 2


def test_klaar_zonder_herhaal_is_fout():
    g, e = nieuw()
    assert e.verwerk(g, 1, "klaar") is False
    assert e.markering == "fout" and e.hint == HINT_KLAAR


def test_fout_binnen_blok_laat_blok_open():
    g, e = nieuw()
    e.verwerk(g, 1, "herhaal 2 keer")
    assert e.verwerk(g, 1, "robot = links") is False
    assert e.markering == "fout"
    assert e.verwerk(g, 1, "robot = vo") is False
    assert e.markering == "wacht"


def test_volle_wachtrij_weigert_commando():
    g, e = nieuw()
    g.voeg_stappen_toe(1, [Move("omhoog")] * 50)
    assert e.verwerk(g, 1, "robot = vooruit") is False
    assert e.markering == "fout" and e.hint == MELD_DRUK


def test_wis_maakt_regels_leeg():
    g, e = nieuw()
    e.verwerk(g, 1, "robot = vooruit")
    e.wis()
    assert e.regels == []
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_editor.py -q`
Expected: FAIL met `ModuleNotFoundError: No module named 'app.editor'`

- [ ] **Step 3: Schrijf editor.py**

`app/editor.py`:
```python
"""De editor van één speler: wat gebeurt er als hij een regel typt.

Zoals CT-3000: geen Start-knop. Zodra een regel een geldig commando is, wordt
hij uitgevoerd (in de wachtrij gezet) en bevroren. Herhaal-blokken worden
verzameld tot 'klaar' en dan in één keer uitgerold.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .game import Game, MELD_DRUK
from .parser import (Command, Incomplete, Invalid, RepeatEnd, RepeatStart,
                     expand, parse_line)

HINT_KLAAR = "Je bent niet in een herhaal. Typ eerst herhaal 3 keer."


@dataclass
class Regel:
    markering: str      # "ok", "wacht" of "fout"
    tekst: str
    inspringing: int    # diepte in herhaal-blokken, voor de weergave


@dataclass
class Editor:
    regels: list[Regel] = field(default_factory=list)   # bevroren regels
    blok: list[Command] = field(default_factory=list)   # open herhaal-blok(ken)
    diepte: int = 0                                     # aantal open herhaal-blokken
    markering: str = ""                                 # bij de invoerregel: "", "fout" of "wacht"
    hint: str | None = None

    def wis(self) -> None:
        self.regels.clear()

    def verwerk(self, game: Game, nummer: int, tekst: str) -> bool:
        """Verwerkt de getypte invoerregel. True = regel is bevroren (invoer leegmaken)."""
        self.hint = None
        r = parse_line(tekst)
        if isinstance(r, Incomplete):
            self.markering = "wacht" if self.diepte else ""
            return False
        if isinstance(r, Invalid):
            self.markering = "fout"
            self.hint = r.hint
            return False
        if isinstance(r, RepeatStart):
            self.blok.append(r)
            self._bevries("wacht", tekst, self.diepte)
            self.diepte += 1
            self.markering = "wacht"
            return True
        if isinstance(r, RepeatEnd):
            if self.diepte == 0:
                self.markering = "fout"
                self.hint = HINT_KLAAR
                return False
            self.diepte -= 1
            self.blok.append(r)
            if self.diepte > 0:
                self._bevries("wacht", tekst, self.diepte)
                return True
            stappen = expand(self.blok)
            self.blok = []
            gelukt = game.voeg_stappen_toe(nummer, stappen)
            nieuw = "ok" if gelukt else "fout"
            for regel in self.regels:
                if regel.markering == "wacht":
                    regel.markering = nieuw
            self._bevries(nieuw, tekst, 0)
            if not gelukt:
                self.hint = MELD_DRUK
            return True
        # Move / Shoot / Shield
        if self.diepte > 0:
            self.blok.append(r)
            self._bevries("wacht", tekst, self.diepte)
            return True
        if game.voeg_stappen_toe(nummer, [r]):
            self._bevries("ok", tekst, 0)
            return True
        self.markering = "fout"
        self.hint = MELD_DRUK
        return False

    def _bevries(self, markering: str, tekst: str, inspringing: int) -> None:
        self.regels.append(Regel(markering, tekst.strip(), inspringing))
        self.markering = "wacht" if self.diepte else ""
```

- [ ] **Step 4: Draai de tests**

Run: `uv run pytest -q`
Expected: `59 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Editor: regels typen, herhaal-blokken, markeringen en hints

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: ScoreDb (SQLite)

**Files:**
- Create: `app/db.py`, `tests/test_db.py`

- [ ] **Step 1: Schrijf de falende tests**

`tests/test_db.py`:
```python
from datetime import datetime
from app.db import ScoreDb


def test_opslaan_en_top_gesorteerd_op_tijd():
    db = ScoreDb(":memory:")
    db.sla_op("Wessel", "Robo", True, 83, datetime(2026, 9, 20, 10, 0))
    db.sla_op("Papa", "Robo", True, 58, datetime(2026, 9, 20, 11, 0))
    db.sla_op("Wessel", "Papa", False, 200, datetime(2026, 9, 20, 12, 0))
    top = db.top(tegen_computer=True)
    assert [(r["winnaar"], r["seconden"]) for r in top] == [("Papa", 58), ("Wessel", 83)]
    assert top[0]["verliezer"] == "Robo"
    assert top[0]["gespeeld_op"].startswith("2026-09-20")
    assert [r["winnaar"] for r in db.top(tegen_computer=False)] == ["Wessel"]


def test_top_maximaal_limiet():
    db = ScoreDb(":memory:")
    for i in range(12):
        db.sla_op("W", "R", True, 100 + i)
    assert len(db.top(True)) == 10
    assert len(db.top(True, limiet=3)) == 3


def test_bestand_blijft_bestaan(tmp_path):
    pad = tmp_path / "scores.db"
    ScoreDb(str(pad)).sla_op("W", "R", True, 5)
    assert ScoreDb(str(pad)).top(True)[0]["seconden"] == 5
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_db.py -q`
Expected: FAIL met `ModuleNotFoundError: No module named 'app.db'`

- [ ] **Step 3: Schrijf db.py**

`app/db.py`:
```python
"""Scorebord in SQLite. Alleen echte overwinningen (gebouw op 0) komen hierin."""
from __future__ import annotations

import sqlite3
from datetime import datetime


class ScoreDb:
    def __init__(self, pad: str = "robotwars.db") -> None:
        self.conn = sqlite3.connect(pad, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS scores (
                 id INTEGER PRIMARY KEY,
                 winnaar TEXT NOT NULL,
                 verliezer TEXT NOT NULL,
                 tegen_computer INTEGER NOT NULL,
                 seconden INTEGER NOT NULL,
                 gespeeld_op TEXT NOT NULL)"""
        )
        self.conn.commit()

    def sla_op(self, winnaar: str, verliezer: str, tegen_computer: bool,
               seconden: int, wanneer: datetime | None = None) -> None:
        wanneer = wanneer or datetime.now()
        self.conn.execute(
            "INSERT INTO scores (winnaar, verliezer, tegen_computer, seconden, gespeeld_op)"
            " VALUES (?, ?, ?, ?, ?)",
            (winnaar, verliezer, int(tegen_computer), seconden, wanneer.isoformat(timespec="seconds")),
        )
        self.conn.commit()

    def top(self, tegen_computer: bool, limiet: int = 10) -> list[dict]:
        rijen = self.conn.execute(
            "SELECT winnaar, verliezer, seconden, gespeeld_op FROM scores"
            " WHERE tegen_computer = ? ORDER BY seconden ASC, id ASC LIMIT ?",
            (int(tegen_computer), limiet),
        ).fetchall()
        return [dict(r) for r in rijen]
```

- [ ] **Step 4: Draai de tests**

Run: `uv run pytest -q`
Expected: `62 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "ScoreDb: scorebord in SQLite

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: Lobby – sessies, wachtrij, koppelen, opruimen

**Files:**
- Create: `app/lobby.py`, `tests/test_lobby.py`

- [ ] **Step 1: Schrijf de falende tests**

`tests/test_lobby.py`:
```python
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
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_lobby.py -q`
Expected: FAIL met `ModuleNotFoundError: No module named 'app.lobby'`

- [ ] **Step 3: Schrijf lobby.py**

`app/lobby.py`:
```python
"""Lobby: wie is wie (cookie-token), wie wacht, en welke spellen lopen er."""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass

from .ai import kies_stap
from .editor import Editor
from .game import Game

OPRUIMEN_NA = 300   # seconden na het einde van een spel
NAAM_COMPUTER = "Robo"


@dataclass
class Sessie:
    token: str
    naam: str
    game_id: str | None = None
    nummer: int | None = None


class Lobby:
    def __init__(self) -> None:
        self.sessies: dict[str, Sessie] = {}
        self.games: dict[str, Game] = {}
        self.wachtende: str | None = None     # token van de speler die wacht
        self.wacht_sinds: float = 0.0

    def registreer(self, naam: str, token: str | None = None) -> Sessie:
        sessie = self.sessies.get(token) if token else None
        if sessie is None:
            sessie = Sessie(secrets.token_urlsafe(16), naam)
            self.sessies[sessie.token] = sessie
        else:
            sessie.naam = naam
        return sessie

    def sessie(self, token: str | None) -> Sessie | None:
        return self.sessies.get(token) if token else None

    def game_van(self, token: str) -> tuple[Game, int] | None:
        """Het lopende spel van deze speler, of None."""
        sessie = self.sessie(token)
        if sessie is None or sessie.game_id is None:
            return None
        game = self.games.get(sessie.game_id)
        if game is None or game.afgelopen:
            return None
        return game, sessie.nummer

    def zoek_tegenstander(self, token: str) -> Game | None:
        """Zet de speler in de wachtrij, of koppelt hem aan wie al wacht."""
        if self.wachtende is None or self.wachtende == token:
            self.wachtende = token
            self.wacht_sinds = time.time()
            return None
        ander = self.wachtende
        self.wachtende = None
        return self._nieuwe_game(ander, token, tegen_computer=False)

    def verlaat_wachtrij(self, token: str) -> None:
        if self.wachtende == token:
            self.wachtende = None

    def start_tegen_computer(self, token: str) -> Game:
        self.verlaat_wachtrij(token)
        return self._nieuwe_game(token, None, tegen_computer=True)

    def ruim_op(self, nu: float | None = None) -> list[str]:
        """Verwijdert spellen die al OPRUIMEN_NA seconden afgelopen zijn; geeft hun ids."""
        nu = nu or time.time()
        weg = [g.id for g in self.games.values()
               if g.geeindigd_op is not None and nu - g.geeindigd_op > OPRUIMEN_NA]
        for game_id in weg:
            del self.games[game_id]
        return weg

    def _nieuwe_game(self, token1: str, token2: str | None, tegen_computer: bool) -> Game:
        s1 = self.sessies[token1]
        s2 = self.sessies[token2] if token2 else None
        game_id = secrets.token_urlsafe(6)
        game = Game(game_id, s1.naam, s2.naam if s2 else NAAM_COMPUTER,
                    tegen_computer=tegen_computer, brein=kies_stap if tegen_computer else None)
        game.editors = {1: Editor(), 2: Editor()}
        self.games[game_id] = game
        s1.game_id, s1.nummer = game_id, 1
        if s2:
            s2.game_id, s2.nummer = game_id, 2
        return game
```

- [ ] **Step 4: Draai de tests**

Run: `uv run pytest -q`
Expected: `67 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Lobby: sessies, wachtrij, koppelen en opruimen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: Weergave – veldmatrix en filters

**Files:**
- Create: `app/weergave.py`, `tests/test_weergave.py`

- [ ] **Step 1: Schrijf de falende tests**

`tests/test_weergave.py`:
```python
from app.weergave import veld_matrix, kolommen, mmss, datum, hartjes, kleur, symbool
from app.game import Game, Schild
from app.parser import Shoot


def test_kolommen_gespiegeld_voor_speler_2():
    assert list(kolommen(1))[:3] == [1, 2, 3]
    assert list(kolommen(2))[:3] == [13, 12, 11]


def test_matrix_soorten_en_inhoud():
    g = Game("g", "A", "B")
    g.schilden.append(Schild(4, 3, eigenaar=1))
    rijen = veld_matrix(g, ik=1)
    assert len(rijen) == 7 and len(rijen[0]) == 13
    cel = rijen[3][0]                       # (1,4): gebouw speler 1
    assert (cel.x, cel.y) == (1, 4) and cel.soort == "b" and cel.gebouw.nummer == 1
    assert rijen[3][1].robot.nummer == 1    # (2,4)
    assert rijen[3][11].robot.nummer == 2   # (12,4)
    assert rijen[2][3].schild.eigenaar == 1 # (4,3)
    assert rijen[0][6].soort == "w" and rijen[1][6].soort == "br"
    assert rijen[0][7].soort == "r"
    # gespiegeld: eerste kolom is x=13
    assert veld_matrix(g, ik=2)[3][0].gebouw.nummer == 2


def test_matrix_toont_kogelbaan():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 2, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()                                # niets geraakt: kogel eindigt op (6,1)
    rijen = veld_matrix(g, 1)
    assert [c.spoor for c in rijen[0][2:6]] == [True] * 4
    assert rijen[0][5].kogel == 1 and rijen[0][4].kogel is None
    g.spelers[2].x, g.spelers[2].y = 4, 1
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    rijen = veld_matrix(g, 1)
    assert rijen[0][3].raak and rijen[0][3].robot.nummer == 2


def test_filters():
    assert mmss(83) == "1:23" and mmss(5) == "0:05"
    assert datum("2026-09-20T10:00:00") == "20 sep"
    assert hartjes(3, 5) == "❤️❤️❤️🖤🖤"
    assert kleur(1) == "gb" and kleur(2) == "gr"
    assert symbool("ok") == "✓" and symbool("wacht") == "…" and symbool("fout") == "!" and symbool("") == ""
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_weergave.py -q`
Expected: FAIL met `ModuleNotFoundError: No module named 'app.weergave'`

- [ ] **Step 3: Schrijf weergave.py**

`app/weergave.py`:
```python
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
```

- [ ] **Step 4: Draai de tests**

Run: `uv run pytest -q`
Expected: `71 passed`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Weergave: veldmatrix, context en filters

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 13: Server-basis – startpagina, scorebord, CSS, sprites

**Files:**
- Create: `app/main.py`, `app/templates/base.html`, `app/templates/start.html`, `app/templates/scorebord.html`, `app/templates/fragments/sprites.html`, `app/static/style.css`, `tests/conftest.py`, `tests/test_main.py`

- [ ] **Step 1: Schrijf conftest en de falende tests**

`tests/conftest.py` (moet vóór `app.main` geïmporteerd worden; pytest laadt conftest eerst):
```python
import os

# Geen echte tik-loop en geen db-bestand tijdens tests.
os.environ["ROBOTWARS_TIK"] = "3600"
os.environ["ROBOTWARS_DB"] = ":memory:"
```

`tests/test_main.py`:
```python
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
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_main.py -q`
Expected: FAIL met `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Kopieer de sprites**

Run:
```bash
cp docs/superpowers/specs/sprites.svg app/templates/fragments/sprites.html
grep -c "<symbol" app/templates/fragments/sprites.html
```
Expected: `9`

- [ ] **Step 4: Schrijf de CSS**

`app/static/style.css`:
```css
/* Robot Wars – donker thema, teamkleuren blauw/rood, accent geel */
:root {
  --bg: #1a1d2b; --paneel: #2a2f45; --paneel-donker: #12141f; --rand: #636363;
  --tekst: #eee; --grijs: #8b91b0; --geel: #ffd23f; --rood-knop: #c0392b; --blauw-knop: #2f7fe0;
  --blauw: #4aa8ff; --rood: #ff5f5f;
  --helft-b: #26456e; --helft-r: #6e2630; --water: #2a7fd4; --brug: #8a5a2b;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--tekst); font-family: system-ui, sans-serif; }
a { color: var(--blauw); }
.pagina { max-width: 960px; margin: 0 auto; padding: 18px; }

/* sprites: teamkleur via --kleur, tegenstander gespiegeld */
.gb { --kleur: var(--blauw); } .gr { --kleur: var(--rood); }
.spiegel { transform: scaleX(-1); }
.naam.gb { color: var(--blauw); } .naam.gr { color: var(--rood); }
/* toren-schade: lampjes uit per aantal levens (zie sprites.html, --l1..--l5) */
.t4 { --l5: hidden; }
.t3 { --l5: hidden; --l4: hidden; }
.t2 { --l5: hidden; --l4: hidden; --l3: hidden; }
.t1 { --l5: hidden; --l4: hidden; --l3: hidden; --l2: hidden; }
/* schild-barsten (--b1, --b2) */
.sc2 { --b1: visible; }
.sc1 { --b1: visible; --b2: visible; }

/* startpagina, wachtkamer, scorebord */
.logo { font-size: 40px; font-weight: 900; text-align: center; margin: 24px 0 4px; }
.logo .a { color: var(--blauw); } .logo .b { color: var(--rood); }
.sub { text-align: center; color: var(--grijs); margin-bottom: 18px; }
.helden { display: flex; justify-content: center; align-items: flex-end; gap: 6px; margin: 6px 0 12px; }
.helden svg { width: 110px; height: 110px; }
.helden .vs { font-weight: 900; font-size: 28px; color: var(--geel); padding: 0 10px 36px; }
.formulier { display: flex; flex-direction: column; gap: 10px; max-width: 360px; margin: 0 auto; }
.formulier label { font-size: 14px; color: var(--grijs); }
.formulier input[type=text] { background: var(--paneel-donker); border: 2px solid var(--rand); border-radius: 8px; padding: 12px 14px; color: #fff; font-size: 20px; font-family: ui-monospace, Consolas, monospace; }
.knop { display: block; border: 0; border-radius: 10px; padding: 14px 18px; font-size: 17px; font-weight: 700; color: #fff; text-align: center; text-decoration: none; cursor: pointer; }
.knop.blauw { background: var(--blauw-knop); } .knop.rood { background: var(--rood-knop); } .knop.grijs { background: var(--paneel); font-weight: 500; }
.fout-melding { color: #ff8a80; text-align: center; }
.link { text-align: center; margin-top: 24px; }
.wacht { text-align: center; }
.wacht svg { width: 140px; height: 140px; animation: zweef 1.6s ease-in-out infinite; }
@keyframes zweef { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
.puntjes span { display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: var(--blauw); margin: 0 4px; animation: stuiter 1.2s infinite; }
.puntjes span:nth-child(2) { animation-delay: .2s; } .puntjes span:nth-child(3) { animation-delay: .4s; }
@keyframes stuiter { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-12px); } }
.tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.tabs h2 { flex: 1; text-align: center; padding: 10px; border-radius: 10px; background: var(--paneel); font-size: 17px; margin: 0; }
.kolommen { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.lijst { list-style: none; margin: 0; padding: 0; }
.lijst li { display: grid; grid-template-columns: 34px 1fr auto; gap: 10px; align-items: center; padding: 9px 12px; border-radius: 8px; margin-bottom: 6px; background: #22263a; }
.lijst .nr { font-weight: 900; font-size: 18px; color: var(--grijs); text-align: center; }
.lijst li:nth-child(1) { background: linear-gradient(90deg, #4a3d10, #22263a); } .lijst li:nth-child(1) .nr { color: var(--geel); }
.lijst li:nth-child(2) .nr { color: #d8dbe3; } .lijst li:nth-child(3) .nr { color: #cd7f32; }
.lijst .tijd { font-weight: 700; color: var(--geel); font-variant-numeric: tabular-nums; }
.lijst .tegen { color: var(--grijs); font-size: 13px; display: block; }

/* spelpagina */
.rw-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; font-size: 20px; font-weight: 700; }
.rw-top .tijd { background: var(--paneel); padding: 6px 14px; border-radius: 20px; font-variant-numeric: tabular-nums; }
.rw-veld { display: grid; grid-template-columns: 26px repeat(13, 56px); grid-auto-rows: 56px; gap: 2px; justify-content: center; }
.rw-veld .co { display: flex; align-items: center; justify-content: center; color: var(--grijs); font-size: 13px; font-weight: 600; }
.rw-veld .c { display: flex; align-items: center; justify-content: center; border-radius: 6px; }
.rw-veld .c svg { width: 54px; height: 54px; }
.c.b { background: var(--helft-b); } .c.r { background: var(--helft-r); }
.c.w { background: var(--water); background-image: repeating-linear-gradient(90deg, transparent 0 10px, rgba(255,255,255,.18) 10px 14px); }
.c.br { background: var(--brug); background-image: repeating-linear-gradient(0deg, transparent 0 8px, rgba(0,0,0,.25) 8px 10px); box-shadow: inset 0 0 0 2px #5a3a1b; }
.c.spoor { box-shadow: inset 0 0 0 3px rgba(255,210,63,.8); }
.c.boem { box-shadow: 0 0 0 3px var(--geel), 0 0 18px 6px rgba(255,210,63,.6); animation: schud .3s 3 alternate; }
@keyframes schud { from { transform: translate(-2px, 0); } to { transform: translate(2px, 0); } }
.rw-status { display: flex; gap: 12px; margin: 14px 0; }
.rw-status .kaart { flex: 1; background: var(--paneel); border-radius: 10px; padding: 10px 14px; line-height: 1.7; display: flex; align-items: center; gap: 12px; }
.rw-status .kaart svg { width: 44px; height: 44px; flex: none; }
.rw-status .kaart b { display: block; font-size: 18px; }
.rw-status .kaart.gb b { color: var(--blauw); } .rw-status .kaart.gr b { color: var(--rood); }
.rw-status .dood { color: var(--grijs); font-size: 13px; }
.rw-editor { background: var(--paneel-donker); border: 3px solid var(--rand); border-radius: 10px; padding: 12px 14px; font-family: ui-monospace, Consolas, monospace; font-size: 17px; }
.rw-editor .regel { display: flex; align-items: center; gap: 10px; padding: 3px 0; }
.rw-editor .oud { color: var(--grijs); }
.rw-editor .mk { width: 22px; text-align: center; font-weight: 700; }
.rw-editor .mk.ok { color: #6bd36b; } .rw-editor .mk.wacht { color: var(--geel); } .rw-editor .mk.fout { color: #ff5252; }
.rw-editor .in1 { padding-left: 2ch; } .rw-editor .in2 { padding-left: 4ch; } .rw-editor .in3 { padding-left: 6ch; }
.rw-editor #invoer { flex: 1; background: #1e2130; border: 2px solid var(--rand); border-radius: 6px; padding: 6px 10px; color: #fff; font: inherit; }
.rw-editor #invoer:focus { outline: none; border-color: var(--blauw); }
.rw-editor .invoerregel:has(.mk.fout) #invoer { border-color: #ff5252; }
.rw-editor .hint { color: #ff8a80; font-size: 14px; min-height: 20px; margin: 4px 0 8px 32px; font-family: system-ui, sans-serif; }
.rw-knoppen { display: flex; gap: 10px; margin-top: 10px; }
.rw-knoppen form { display: inline; }
.rw-knoppen button { background: var(--paneel); color: var(--tekst); border: 0; border-radius: 8px; padding: 8px 18px; font-size: 15px; cursor: pointer; }
.rw-knoppen .stop { background: var(--rood-knop); }
.overlay { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(10,12,20,.7); }
.win { background: var(--bg); border: 3px solid var(--geel); border-radius: 16px; padding: 24px 32px; text-align: center; box-shadow: 0 0 40px rgba(255,210,63,.35); max-width: 420px; }
.win .beker { font-size: 54px; line-height: 1; }
.win h2 { font-size: 26px; margin: 6px 0 2px; }
.win .tijd { font-size: 40px; font-weight: 900; color: var(--geel); margin: 4px 0 6px; }
.win p { color: var(--grijs); }
.win .knoppen { display: flex; gap: 10px; justify-content: center; }
.win .knop { padding: 10px 18px; font-size: 15px; }
@media (max-width: 860px) {
  .rw-veld { grid-template-columns: 20px repeat(13, 1fr); grid-auto-rows: auto; }
  .rw-veld .c { aspect-ratio: 1; } .rw-veld .c svg { width: 90%; height: 90%; }
  .rw-status { flex-direction: column; }
}
```

- [ ] **Step 5: Schrijf de templates**

`app/templates/base.html`:
```html
<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block titel %}Robot Wars{% endblock %}</title>
  <link rel="stylesheet" href="/static/style.css">
  <script src="/static/htmx.min.js"></script>
  <script src="/static/ws.js"></script>
</head>
<body>
  <div class="pagina">
    {% block inhoud %}{% endblock %}
  </div>
</body>
</html>
```

`app/templates/start.html`:
```html
{% extends "base.html" %}
{% block inhoud %}
{% include "fragments/sprites.html" %}
<div class="logo"><span class="a">ROBOT</span> <span class="b">WARS</span></div>
<div class="sub">Programmeer je robot. Schiet de toren van de ander kapot.</div>
<div class="helden">
  <svg class="gb"><use href="#bolbot"/></svg>
  <span class="vs">VS</span>
  <svg class="gr spiegel"><use href="#bolbot"/></svg>
</div>
<form class="formulier" method="post" action="/start">
  <label for="naam">Hoe heet je?</label>
  <input type="text" id="naam" name="naam" value="{{ naam }}" maxlength="20" autocomplete="off" autofocus required>
  {% if fout %}<div class="fout-melding">{{ fout }}</div>{% endif %}
  <button class="knop blauw" name="modus" value="mens">🎮 Speel tegen iemand</button>
  <button class="knop rood" name="modus" value="computer">🤖 Speel tegen de computer</button>
</form>
<div class="link"><a href="/scorebord">🏆 Scorebord</a></div>
{% endblock %}
```

`app/templates/scorebord.html`:
```html
{% extends "base.html" %}
{% block titel %}Scorebord – Robot Wars{% endblock %}
{% block inhoud %}
<div class="logo"><span class="a">ROBOT</span> <span class="b">WARS</span></div>
<div class="sub">De snelste overwinningen</div>
<div class="kolommen">
  {% for titel, lijst in (("🤖 Tegen de computer", computer), ("🧑 Tegen een mens", mens)) %}
  <div>
    <div class="tabs"><h2>{{ titel }}</h2></div>
    <ol class="lijst">
      {% for s in lijst %}
      <li><span class="nr">{{ loop.index }}</span>
          <span>{{ s.winnaar }}<span class="tegen">tegen {{ s.verliezer }} · {{ s.gespeeld_op|datum }}</span></span>
          <span class="tijd">{{ s.seconden|mmss }}</span></li>
      {% else %}
      <li><span class="nr">–</span><span>Nog geen overwinningen</span><span></span></li>
      {% endfor %}
    </ol>
  </div>
  {% endfor %}
</div>
<div class="link"><a href="/">← Terug naar start</a></div>
{% endblock %}
```

- [ ] **Step 6: Schrijf main.py (eerste versie)**

`app/main.py`:
```python
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
```

- [ ] **Step 7: Draai de tests**

Run: `uv run pytest -q`
Expected: `76 passed`

- [ ] **Step 8: Bekijk de startpagina in de browser**

Run: `uv run uvicorn app.main:app --reload` (laat draaien in een aparte terminal) en open http://localhost:8000.
Expected: logo ROBOT WARS, twee bolbots, naamveld, twee knoppen; `/scorebord` toont twee lege lijsten. Stop de server daarna met Ctrl+C.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "Server: startpagina, scorebord, CSS en sprites

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 14: Wachtkamer

**Files:**
- Create: `app/templates/wachten.html`
- Modify: `app/main.py`, `tests/test_main.py`

- [ ] **Step 1: Schrijf de falende tests**

Onderaan `tests/test_main.py`:
```python
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
```

- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_main.py -q`
Expected: 2 tests FAIL (404 op `/wachten`)

- [ ] **Step 3: Schrijf de template**

`app/templates/wachten.html`:
```html
{% extends "base.html" %}
{% block titel %}Wachten – Robot Wars{% endblock %}
{% block inhoud %}
{% include "fragments/sprites.html" %}
<div class="wacht">
  <svg class="gb"><use href="#bolbot"/></svg>
  <h2>Wachten op een tegenstander</h2>
  <p>Jij bent <b class="naam gb">{{ naam }}</b>. Zodra iemand anders zijn naam invult, begint het spel vanzelf.</p>
  <div class="puntjes"><span></span><span></span><span></span></div>
  <p class="sub" hx-get="/wachten/status" hx-trigger="every 1s" hx-swap="innerHTML">Al 0:00 aan het wachten</p>
  <form method="post" action="/wachten/computer">
    <button class="knop grijs">🤖 Toch tegen de computer</button>
  </form>
</div>
{% endblock %}
```

- [ ] **Step 4: Voeg de routes toe**

In `app/main.py`, na de scorebord-route:
```python
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
```

- [ ] **Step 5: Draai de tests**

Run: `uv run pytest -q`
Expected: `78 passed`

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "Wachtkamer met polling en koppelen

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 15: Spelpagina, WebSocket en tik-loop

**Files:**
- Create: `app/templates/spel.html`, `app/templates/fragments/kop.html`, `veld.html`, `status.html`, `regels.html`, `markering.html`, `invoer.html`, `hint.html`, `einde.html`
- Modify: `app/weergave.py`, `app/main.py`, `tests/test_main.py`

- [ ] **Step 1: Schrijf de falende tests**

Onderaan `tests/test_main.py`:
```python
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
    assert game.score_opgeslagen
    assert main.db.top(True)[0]["winnaar"] == "Wessel"
    assert client.get("/", follow_redirects=False).status_code == 200   # niet meer terug het spel in


def test_weg_zijn_is_verlies_zonder_score(client):
    game, token = start_spel(client)
    game.laatst_gezien[1] = time.time() - main.WEG_NA - 1
    main.tik_alles()
    assert game.afgelopen and game.winnaar == 2 and game.opgegeven
    assert main.db.top(True) == []
```
- [ ] **Step 2: Draai de tests**

Run: `uv run pytest tests/test_main.py -q`
Expected: 6 nieuwe tests FAIL (404 op `/spel/...`)

- [ ] **Step 3: Schrijf de fragmenten**

`app/templates/fragments/kop.html`:
```html
<div id="kop" class="rw-top">
  <div><span class="naam {{ jij.nummer|kleur }}">{{ jij.naam }}</span> (jij) &nbsp;tegen&nbsp; <span class="naam {{ ander.nummer|kleur }}">{{ ander.naam }}</span></div>
  <div class="tijd">⏱ {{ game.tik|mmss }}</div>
</div>
```

`app/templates/fragments/veld.html`:
```html
<div id="veld" class="rw-veld">
  <div class="co"></div>
  {% for x in kolommen %}<div class="co">{{ x }}</div>{% endfor %}
  {% for rij in rijen %}
  <div class="co">{{ loop.index }}</div>
  {% for cel in rij %}
  <div class="c {{ cel.soort }}{% if cel.spoor %} spoor{% endif %}{% if cel.raak %} boem{% endif %}">
    {% if cel.gebouw %}
      {% set g = cel.gebouw %}
      <svg class="{{ g.nummer|kleur }}{% if g.nummer != ik %} spiegel{% endif %} t{{ g.gebouw_levens }}">
        {% if g.gebouw_levens == 0 %}<use href="#puin"/>
        {% else %}<use href="#toren"/>
          {% if g.gebouw_levens == 4 %}<use href="#barst1"/>{% elif g.gebouw_levens < 4 %}<use href="#barst2"/>{% endif %}
          {% if g.gebouw_levens == 2 %}<use href="#rook"/>{% elif g.gebouw_levens == 1 %}<use href="#vlammen"/>{% endif %}
        {% endif %}
      </svg>
    {% elif cel.schild %}
      <svg class="{{ cel.schild.eigenaar|kleur }} sc{{ cel.schild.levens }}"><use href="#schild"/></svg>
    {% elif cel.robot %}
      <svg class="{{ cel.robot.nummer|kleur }}{% if cel.robot.nummer != ik %} spiegel{% endif %}"><use href="#bolbot"/></svg>
    {% elif cel.kogel %}
      <svg class="{{ cel.kogel|kleur }}{% if cel.kogel != ik %} spiegel{% endif %}"><use href="#kogel"/></svg>
    {% endif %}
  </div>
  {% endfor %}
  {% endfor %}
</div>
```

`app/templates/fragments/status.html`:
```html
<div id="status" class="rw-status">
  {% for p in (jij, ander) %}
  <div class="kaart {{ p.nummer|kleur }}">
    <svg class="{{ p.nummer|kleur }}{% if p.nummer != ik %} spiegel{% endif %}"><use href="#bolbot"/></svg>
    <div>
      <b>{{ p.naam }}{% if p.nummer == ik %} (jij){% endif %}</b>
      robot {{ p.robot_levens|hartjes(5) }} &nbsp; toren {{ p.gebouw_levens|hartjes(5) }} &nbsp; 🛡️ nog {{ p.schilden_over }}
      {% if not p.leeft and not game.afgelopen %}<span class="dood">· komt terug over {{ p.respawn_over }}</span>{% endif %}
    </div>
  </div>
  {% endfor %}
</div>
```

`app/templates/fragments/regels.html`:
```html
<div id="regels">
  {% for r in editor.regels %}
  <div class="regel oud in{{ r.inspringing }}"><span class="mk {{ r.markering }}">{{ r.markering|symbool }}</span>{{ r.tekst }}</div>
  {% endfor %}
</div>
```

`app/templates/fragments/markering.html`:
```html
<span id="markering" class="mk {{ editor.markering }}">{{ editor.markering|symbool }}</span>
```

`app/templates/fragments/invoer.html`:
```html
<input id="invoer" name="regel" type="text" value="" placeholder="robot = vooruit"
       autocomplete="off" spellcheck="false" autofocus
       ws-send hx-trigger="input changed delay:50ms"{% if game.afgelopen %} disabled{% endif %}>
```

`app/templates/fragments/hint.html`:
```html
<div id="hint" class="hint">{{ editor.hint or "" }}</div>
```

`app/templates/fragments/einde.html`:
```html
<div id="einde">
  {% if game.afgelopen %}
  {% set winnaar = game.spelers[game.winnaar] %}
  <div class="overlay">
    <div class="win">
      <div class="beker">🏆</div>
      <h2><span class="naam {{ winnaar.nummer|kleur }}">{{ winnaar.naam }}</span> wint!</h2>
      <div class="tijd">{{ game.tik|mmss }}</div>
      {% if game.opgegeven %}
        <p>{{ game.tegenstander(game.winnaar).naam }} is weg. Dit potje telt niet voor het scorebord.</p>
      {% else %}
        <p>De toren van {{ game.tegenstander(game.winnaar).naam }} ligt in puin.</p>
      {% endif %}
      <div class="knoppen">
        <a class="knop blauw" href="/">🔁 Nog een keer</a>
        <a class="knop grijs" href="/scorebord">🏆 Scorebord</a>
      </div>
    </div>
  </div>
  {% endif %}
</div>
```

`app/templates/spel.html`:
```html
{% extends "base.html" %}
{% block titel %}{{ jij.naam }} tegen {{ ander.naam }} – Robot Wars{% endblock %}
{% block inhoud %}
{% include "fragments/sprites.html" %}
<div hx-ext="ws" ws-connect="/ws/spel/{{ game.id }}">
  {% include "fragments/kop.html" %}
  {% include "fragments/veld.html" %}
  {% include "fragments/status.html" %}
  <div class="rw-editor">
    {% include "fragments/regels.html" %}
    <div class="regel invoerregel">
      {% include "fragments/markering.html" %}
      {% include "fragments/invoer.html" %}
    </div>
    {% include "fragments/hint.html" %}
    <div class="rw-knoppen">
      <form ws-send><input type="hidden" name="actie" value="stop"><button class="stop" type="submit">■ Stop</button></form>
      <form ws-send><input type="hidden" name="actie" value="wis"><button type="submit">Wis</button></form>
    </div>
  </div>
  {% include "fragments/einde.html" %}
</div>
{% endblock %}
```

- [ ] **Step 4: Voeg fragment-renderers toe aan weergave.py**

Onderaan `app/weergave.py`:
```python
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
```

- [ ] **Step 5: Voeg spelpagina, WebSocket en uitzenden toe aan main.py**

Vervang in `app/main.py` het blok `# ---- tik-taak ... ` t/m het einde door:
```python
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
            except ValueError:            # geen geldige JSON: negeren
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


def tik_alles() -> None:
    nu = time.time()
    for game in list(lobby.games.values()):
        if game.afgelopen:
            continue
        game.tick()
        controleer_weg(game, nu)
        if game.afgelopen and not game.score_opgeslagen:
            game.score_opgeslagen = True
            if not game.opgegeven:
                winnaar = game.spelers[game.winnaar]
                verliezer = game.tegenstander(game.winnaar)
                db.sla_op(winnaar.naam, verliezer.naam, game.tegen_computer, game.tik)
    for game_id in lobby.ruim_op(nu):
        verbindingen.pop(game_id, None)


async def zend_alles() -> None:
    for game_id, per_speler in list(verbindingen.items()):
        game = lobby.games.get(game_id)
        if game is None:
            continue
        for nummer, sockets in per_speler.items():
            if not sockets:
                continue
            html = weergave.tik_html(templates, game, nummer)
            for ws in list(sockets):
                try:
                    await ws.send_text(html)
                except Exception:
                    sockets.discard(ws)


async def tik_loop() -> None:
    while True:
        await asyncio.sleep(TIK_SECONDEN)
        try:
            tik_alles()
            await zend_alles()
        except Exception:      # nooit de loop laten sterven
            log.exception("fout in tik")
```

Voeg bovenaan `main.py` bij de imports toe: `from .game import Game` is niet nodig (typehints zijn strings/none); laat de imports zoals ze zijn.

- [ ] **Step 6: Draai de tests**

Run: `uv run pytest -q`
Expected: `84 passed`

Als `test_tik_stuurt_veld_naar_verbonden_spelers` faalt op `client.portal`: gebruik dan in die twee tests in plaats van `client.portal.call(main.zend_alles)` het volgende:
```python
import anyio
anyio.from_thread.run(main.zend_alles)   # werkt alleen binnen de TestClient-context
```
en als ook dat niet werkt: `asyncio.run(main.zend_alles())` (de sockets van de TestClient zijn thread-veilig genoeg voor `send_text`).

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "Spelpagina, WebSocket-editor en tik-loop met uitzenden

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 16: Handmatige controle in de browser

**Files:**
- Geen nieuwe code, tenzij een controle faalt (dan fix + test + commit).

- [ ] **Step 1: Start de server**

Run: `uv run uvicorn app.main:app --reload`
Open http://localhost:8000 in Chrome.

- [ ] **Step 2: Tegen de computer**

1. Vul "Wessel" in, klik **Speel tegen de computer**. Expected: spelpagina met veld, jouw bolbot links op (2,4), Robo rechts op (12,4), torens op (1,4) en (13,4), cursor knippert in de invoerregel.
2. Typ `robot = vo` → geen markering. Typ door tot `robot = vooruit` → regel bevriest met ✓, invoer is leeg **en heeft focus** (je kunt direct doortypen), robot loopt binnen 1 seconde één vakje naar rechts, Robo doet daarna ook één stap.
3. Typ `robot = links` → rood `!` en de hint *Ik ken "links" niet…*. Maak leeg.
4. Typ `herhaal 3 keer` → gele `…`; typ `robot = omhoog` (ingesprongen, `…`), typ `klaar` → alle drie ✓, robot loopt 3 stappen omhoog (1 per seconde), timer loopt.
5. Typ `schild = (4, 3)` → schild verschijnt; `schild = (9, 3)` → hint *alleen op je eigen helft*.
6. Loop naar Robo's rij en typ `robot = schiet` → gele kogelbaan; raak Robo → vakje flitst/schudt, hartje minder in de status.
7. Klik **Stop** tijdens een herhaal → robot stopt. Klik **Wis** → lijst leeg.
8. Speel uit tot een toren op 0 staat → overlay "… wint!" met tijd; **Scorebord** toont de score onder *Tegen de computer*; **Nog een keer** gaat naar de startpagina (niet terug het spel in).

**Als de focus na het bevriezen niet in de nieuwe invoer staat:** voeg aan `app/templates/fragments/invoer.html` het attribuut `hx-on:htmx:load="this.focus()"` toe. Werkt dat ook niet, voeg dan onderaan `base.html` toe:
```html
<script>
  document.body.addEventListener("htmx:load", e => { if (e.detail.elt.id === "invoer") e.detail.elt.focus(); });
</script>
```

- [ ] **Step 3: Twee mensen**

1. Tab 1: naam "A", **Speel tegen iemand** → wachtkamer, teller loopt.
2. Tab 2 in een **incognitovenster** (andere cookies): naam "B", **Speel tegen iemand** → direct in het spel; tab 1 springt binnen een seconde ook naar het spel.
3. In tab 2 (speler B) staat B's eigen kant **links** (gespiegeld) en de kolomnummers lopen 13 → 1. Typ in tab 2 `robot = vooruit` → B's robot beweegt op het scherm naar rechts; in tab 1 beweegt dezelfde robot naar links.
4. Refresh tab 1 → je zit meteen weer in het spel met dezelfde bevroren regels.
5. Sluit tab 2 en wacht 60+ seconden → tab 1 toont "B is weg" en wint; het scorebord onder *Tegen een mens* blijft leeg.

- [ ] **Step 4: Telefoonbreedte**

Maak het venster smal (< 860 px) → het veld schaalt mee, de statuskaarten staan onder elkaar, geen horizontale scroll.

- [ ] **Step 5: Leg afwijkingen vast**

Elke gevonden fout: schrijf eerst een test die hem reproduceert (in de passende testmodule), fix, `uv run pytest -q` groen, commit met een beschrijvende boodschap.

---

### Task 17: README en Caddyfile

**Files:**
- Create: `README.md`, `Caddyfile`

- [ ] **Step 1: Schrijf de README**

`README.md`:
```markdown
# Robot Wars

Een programmeerspel voor kinderen van 8–12 jaar, gemaakt door Martijn en Wessel.
Je bestuurt een robot door commando's te typen (zoals in CT-3000) en probeert de
toren van de tegenstander kapot te schieten (zoals in Clash Royale).

## Spelen

```
robot = vooruit      robot = achteruit
robot = omhoog       robot = omlaag
robot = schiet       (schiet 4 vakjes vooruit)
schild = (4, 2)      (3 per potje, alleen op je eigen helft)
herhaal 3 keer
  robot = vooruit
klaar
```

Je hoeft niet op Enter te drukken: zodra een regel klopt, doet je robot hem.
Wie de toren van de ander op 0 schiet, wint. De snelste tijd staat bovenaan het
scorebord.

## Starten (alleen met uv)

```
uv sync
uv run uvicorn app.main:app --reload
```

Open http://localhost:8000. Voor twee spelers: open de pagina in twee
verschillende browsers (of een incognitovenster).

## Testen

```
uv run pytest -q
```

## Instellingen (omgevingsvariabelen)

- `ROBOTWARS_DB` – pad van het SQLite-bestand (standaard `robotwars.db`)
- `ROBOTWARS_TIK` – seconden per stap (standaard `1`; kleiner = sneller spel)

## Online zetten achter Caddy

```
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Met de meegeleverde `Caddyfile` (pas de domeinnaam aan) regelt Caddy HTTPS en de
WebSocket-verbinding automatisch: `caddy run`.

## Hoe het werkt

- `app/parser.py` – zet een getypte regel om in een commando
- `app/game.py` – de spelregels (veld, lopen, schieten, schilden, winnen)
- `app/ai.py` – Robo, de computerspeler
- `app/editor.py` – de editor: regels bevriezen, herhaal-blokken, hints
- `app/lobby.py` – wie speelt tegen wie
- `app/main.py` – de webserver (FastAPI + HTMX over een WebSocket)

Het ontwerp staat in `docs/superpowers/specs/2026-09-20-robotwars-design.md`.
```

- [ ] **Step 2: Schrijf de Caddyfile**

`Caddyfile`:
```
# Vervang robotwars.example.nl door je eigen domein.
robotwars.example.nl {
    reverse_proxy localhost:8000
}
```

- [ ] **Step 3: Controleer dat alles nog groen is**

Run: `uv run pytest -q`
Expected: `84 passed`

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "README en Caddyfile

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Zelfcontrole tegen het ontwerp

| Ontwerp-onderdeel | Taak |
|---|---|
| Veld 13×7, rivier, bruggen, startvakken, richting | 5 |
| Bewegen en blokkades | 5 |
| Schieten (bereik 4, eerste voorwerp, kogelbaan) | 6, 12, 15 |
| Levens, respawn na 3 tikken, startvak bezet | 6 |
| Schilden (eigen helft, leeg, niet startvak, 3 per potje, 3 treffers) | 6, 7 |
| Winnen, speler 1 eerst, tijd = tik | 6 |
| Taal + parser (Incomplete/Invalid, hints, herhaal 1–20, nesten) | 2, 3, 4 |
| Editor: typen zonder Enter, markeringen, blokken, wachtrij 50, Stop, Wis | 9, 15 |
| WebSocket met `ws-send` per toetsaanslag, OOB-fragmenten, autofocus | 15, 16 |
| Startpagina, cookie, naam 1–20 | 13 |
| Wachtkamer, polling, HX-Redirect, toch tegen computer | 14 |
| Terugkomen in lopend spel | 13, 16 |
| Weg zijn (60 s) → ander wint, niet op scorebord | 15 |
| Spelpagina, spiegeling voor speler 2, status, einde-overlay | 12, 15 |
| Robo: tegoed, 4 regels, schild op (11,4) | 8 |
| Scorebord SQLite, twee lijsten, top-10 | 10, 13 |
| Opruimen na 5 minuten | 11, 15 |
| Sprites, toren-schade, schild-barsten, kogel | 13, 15 |
| uv, Caddy, README | 1, 17 |
```
