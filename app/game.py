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
    return 1 <= x <= RIVIER_X - 1 if nummer == 1 else RIVIER_X + 1 <= x <= BREEDTE


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
            speler.melding = None
