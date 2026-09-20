"""Spelregels van Robot Wars: veld, lopen, schieten, schilden, bommen, respawn, winnen.

Pure Python; de server roept alleen voeg_stappen_toe(), stop(), tick() en
geef_op() aan en leest de toestand voor de weergave.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from .parser import Move, Shoot, Shield, Bomb, Step

# Het veld is een wiskundig assenstelsel: x loopt naar rechts (1..13), y omhoog (1 onderaan,
# 7 bovenaan). Bruggen, torens en startvakken liggen symmetrisch, dus (x, y) is eenduidig.
BREEDTE, HOOGTE = 13, 7
RIVIER_X = 7
BRUG_RIJEN = (2, 6)
SCHIET_BEREIK = 4
GEBOUW_LEVENS = 5
ROBOT_LEVENS = 5
SCHILD_LEVENS = 8
SCHILDEN_PER_SPELER = 3
BOMMEN_PER_SPELER = 3
RESPAWN_TIKKEN = 3
MAX_WACHTRIJ = 50
MAX_SPELDUUR = 30 * 60   # tikken; daarna stopt de server het potje (reden "tijd")

# per spelernummer: gebouw, startvak en looprichting (+1 = naar rechts)
GEBOUW = {1: (1, 4), 2: (13, 4)}
START = {1: (2, 4), 2: (12, 4)}
RICHTING = {1: 1, 2: -1}

MELD_OP = "Je schilden zijn op."
MELD_BESTAAT_NIET = "Dat vak bestaat niet."
MELD_HELFT = "Een schild mag alleen op je eigen helft."
MELD_STARTVAK = "Niet op een startvak, anders kan een robot nooit meer terugkomen."
MELD_BEZET = "Dat vak is niet leeg."
MELD_BOMMEN_OP = "Je bommen zijn op."
MELD_WATER = "Daar is water."
MELD_DRUK = "Wacht even, je robot is nog bezig."


def in_veld(x: int, y: int) -> bool:
    return 1 <= x <= BREEDTE and 1 <= y <= HOOGTE


def is_water(x: int, y: int) -> bool:
    return x == RIVIER_X and y not in BRUG_RIJEN


def eigen_kolom(nummer: int, x: int) -> int:
    """Kolomnummer zoals speler `nummer` hem ziet: iedereen telt vanaf zijn eigen kant
    1 t/m 13. Voor speler 1 is dat de echte x; voor speler 2 gespiegeld. De functie is
    haar eigen inverse, dus ook bruikbaar om getypte kolommen terug te vertalen."""
    return x if nummer == 1 else BREEDTE + 1 - x


def eigen_helft(nummer: int, x: int) -> bool:
    return 1 <= x <= RIVIER_X - 1 if nummer == 1 else RIVIER_X + 1 <= x <= BREEDTE


@dataclass
class Schild:
    x: int
    y: int
    eigenaar: int
    levens: int = SCHILD_LEVENS


@dataclass
class Mijn:
    """Een bom die is blijven liggen: gaat af zodra een robot erop stapt (van wie ook)."""
    x: int
    y: int
    eigenaar: int


@dataclass
class Schot:
    """Eén schot in de laatste tik, voor de weergave van de kogelbaan."""
    schutter: int
    cellen: list[tuple[int, int]]        # vakjes die de kogel passeerde (incl. trefvak)
    raak: tuple[int, int] | None         # geraakt vak, of None als niets geraakt


@dataclass
class Gebeurtenis:
    """Eén regel voor het log "Wat gebeurt er?" (de weergave maakt er tekst van)."""
    soort: str                   # loop, geblokkeerd, raak_schild, raak_robot, raak_gebouw, mis,
                                 # dood, terug, schild, schild_fout, bom, bom_fout, bom_raak,
                                 # mijn_raak, mijn_dubbel, win
    speler: int                  # wie het deed (of wie het overkwam bij dood/terug/win)
    x: int = 0
    y: int = 0
    doel: int | None = None      # geraakte speler / eigenaar van het geraakte voorwerp
    levens: int | None = None    # resterende levens van het geraakte voorwerp
    tekst: str | None = None     # richting bij lopen, melding bij schild_fout


LOG_LENGTE = 30


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
    bommen_over: int = BOMMEN_PER_SPELER
    wachtrij: deque[Step] = field(default_factory=deque)
    respawn_over: int = 0        # tikken tot de robot terugkomt (0 = leeft of wacht niet)
    tegoed: int = 0              # stappen die Robo nog mag doen (één per uitgevoerde stap van de mens)
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
        self.mijnen: list[Mijn] = []
        self.knallen: list[tuple[int, int]] = []   # explosies van de laatste tik (bom/mijn), voor de 💥
        self.log: deque[tuple[int, Gebeurtenis]] = deque(maxlen=LOG_LENGTE)   # (tik, gebeurtenis)
        self.tik = 0
        self.winnaar: int | None = None
        self.opgegeven = False           # winst doordat de ander wegging of stopte: niet voor het scorebord
        self.opgegeven_reden = ""        # "weg", "gestopt" of "tijd"
        self.geeindigd_op: float | None = None
        self.score_opgeslagen = False
        self.einde_gezonden = False      # de eindstand is één keer naar de spelers gestuurd
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

    def mijn_op(self, x: int, y: int) -> Mijn | None:
        return next((m for m in self.mijnen if (m.x, m.y) == (x, y)), None)

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
        return True

    def stop(self, nummer: int) -> None:
        self.spelers[nummer].wachtrij.clear()

    def geef_op(self, nummer: int, reden: str = "weg") -> None:
        """Speler `nummer` is weg of is gestopt; de ander wint, maar dit telt niet voor
        het scorebord. `reden` is "weg" (verbinding verbroken), "gestopt" (knop) of
        "tijd" (het potje duurde langer dan MAX_SPELDUUR)."""
        if not self.afgelopen:
            self.opgegeven = True
            self.opgegeven_reden = reden
            self._zet_winnaar(self.tegenstander(nummer).nummer)

    def tick(self) -> None:
        """Eén seconde spel: elke speler doet één stap (speler 1 eerst)."""
        if self.afgelopen:
            return
        self.schoten = []
        self.knallen = []
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
                # Robo krijgt één tegoed per stap die de mens echt zet (niet bij het
                # inplannen), zodat hij stilstaat na Stop of als de mens sneuvelt.
                if self.tegen_computer:
                    self.spelers[2].tegoed += 1
                self._voer_uit(speler, speler.wachtrij.popleft())
            if self.afgelopen:
                return

    # ---- intern ----

    def _meld(self, soort: str, speler: int, x: int = 0, y: int = 0, **rest) -> None:
        self.log.append((self.tik, Gebeurtenis(soort, speler, x, y, **rest)))

    def _zet_winnaar(self, nummer: int) -> None:
        self.winnaar = nummer
        self.geeindigd_op = time.time()
        self._meld("win", nummer)

    def _respawn(self, speler: Speler) -> None:
        speler.respawn_over -= 1
        if speler.respawn_over == 0:
            if self.robot_op(*speler.startvak) is None:
                speler.x, speler.y = speler.startvak
                speler.robot_levens = ROBOT_LEVENS
                self._meld("terug", speler.nummer, speler.x, speler.y)
            else:
                speler.respawn_over = 1   # volgende tik opnieuw proberen

    def _robot_kapot(self, robot: Speler, x: int, y: int) -> None:
        """Robot sneuvelt op (x, y): hartjes op 0, wachtrij leeg, terug na RESPAWN_TIKKEN."""
        robot.robot_levens = 0
        robot.respawn_over = RESPAWN_TIKKEN
        robot.wachtrij.clear()
        self._meld("dood", robot.nummer, x, y)

    def _voer_uit(self, speler: Speler, stap: Step) -> None:
        if isinstance(stap, Move):
            self._loop(speler, stap.richting)
        elif isinstance(stap, Shoot):
            self._schiet(speler)
        elif isinstance(stap, Shield):
            self._zet_schild(speler, stap.x, stap.y)
        elif isinstance(stap, Bomb):
            self._leg_bom(speler, stap.dx, stap.dy)

    def _loop(self, speler: Speler, richting: str) -> None:
        # Het veld is een assenstelsel: y=1 ligt onderaan, y=7 bovenaan.
        dx, dy = {
            "vooruit": (speler.richting, 0),
            "achteruit": (-speler.richting, 0),
            "omhoog": (0, 1),    # y + 1
            "omlaag": (0, -1),   # y - 1
        }[richting]
        doel = (speler.x + dx, speler.y + dy)
        if self.is_vrij(*doel):
            speler.x, speler.y = doel
            self._meld("loop", speler.nummer, speler.x, speler.y, tekst=richting)
            mijn = self.mijn_op(*doel)
            if mijn is not None:
                self.mijnen.remove(mijn)
                self.knallen.append(doel)
                self._meld("mijn_raak", speler.nummer, *doel, doel=mijn.eigenaar)
                self._robot_kapot(speler, *doel)
        else:
            self._meld("geblokkeerd", speler.nummer, tekst=richting)

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
                self._meld("raak_schild", speler.nummer, x, y, doel=schild.eigenaar, levens=schild.levens)
                raak = (x, y)
                break
            robot = self.robot_op(x, y)
            if robot is not None:
                robot.robot_levens -= 1
                self._meld("raak_robot", speler.nummer, x, y, doel=robot.nummer, levens=robot.robot_levens)
                if robot.robot_levens == 0:
                    self._robot_kapot(robot, x, y)
                raak = (x, y)
                break
            gebouw = self.gebouw_op(x, y)
            if gebouw is not None:
                gebouw.gebouw_levens -= 1
                self._meld("raak_gebouw", speler.nummer, x, y, doel=gebouw.nummer, levens=gebouw.gebouw_levens)
                if gebouw.gebouw_levens == 0:
                    self._zet_winnaar(self.tegenstander(gebouw.nummer).nummer)
                raak = (x, y)
                break
        if raak is None:
            laatste = cellen[-1] if cellen else (speler.x, speler.y)
            self._meld("mis", speler.nummer, *laatste)
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
            self._meld("schild", speler.nummer, x, y)
            return
        self._meld("schild_fout", speler.nummer, x, y, tekst=speler.melding)

    def _leg_bom(self, speler: Speler, dx: int, dy: int) -> None:
        """Bom op een buurvak (dx, dy al in echte veldrichting). Staat er een robot: meteen
        kapot. Ligt er een mijn: beide weg. Anders blijft de bom liggen als mijn."""
        x, y = speler.x + dx, speler.y + dy
        if speler.bommen_over == 0:
            speler.melding = MELD_BOMMEN_OP
        elif not in_veld(x, y):
            speler.melding = MELD_BESTAAT_NIET
        elif is_water(x, y):
            speler.melding = MELD_WATER
        elif self.gebouw_op(x, y) is not None or self.schild_op(x, y) is not None:
            speler.melding = MELD_BEZET
        elif (x, y) in START.values() and self.robot_op(x, y) is None:
            speler.melding = MELD_STARTVAK   # anders zou de mijn blijven liggen en kan niemand terugkomen
        else:
            speler.bommen_over -= 1
            speler.melding = None
            robot = self.robot_op(x, y)
            mijn = self.mijn_op(x, y)
            if robot is not None:
                self.knallen.append((x, y))
                self._meld("bom_raak", speler.nummer, x, y, doel=robot.nummer)
                self._robot_kapot(robot, x, y)
            elif mijn is not None:
                self.mijnen.remove(mijn)
                self.knallen.append((x, y))
                self._meld("mijn_dubbel", speler.nummer, x, y, doel=mijn.eigenaar)
            else:
                self.mijnen.append(Mijn(x, y, speler.nummer))
                self._meld("bom", speler.nummer, x, y)
            return
        self._meld("bom_fout", speler.nummer, x, y, tekst=speler.melding)
