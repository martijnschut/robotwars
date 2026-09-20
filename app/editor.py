"""De editor van één speler: wat gebeurt er als hij een regel typt.

Zoals CT-3000: geen Start-knop. Zodra een regel een geldig commando is, wordt
hij uitgevoerd (in de wachtrij gezet) en bevroren. Herhaal-blokken worden
verzameld tot 'klaar' en dan in één keer uitgerold.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .game import Game, MAX_WACHTRIJ, MELD_DRUK, RICHTING, eigen_kolom
from .parser import (Bomb, Command, Incomplete, Invalid, RepeatEnd, RepeatStart, Shield,
                     expand, parse_line)

HINT_KLAAR = "Je bent niet in een herhaal. Typ eerst herhaal 3 keer."
HINT_TE_DIEP = "Zo veel herhalingen in elkaar kan niet (maximaal 10)."
HINT_TE_VEEL = f"Dat zijn te veel stappen in één keer (maximaal {MAX_WACHTRIJ})."
MAX_DIEPTE = 10    # herhaal-blokken in elkaar
MAX_REGELS = 100   # bevroren regels die we bewaren (en elke keer meesturen)
MAX_REGEL_LENGTE = 200   # tekens per getypte regel; langere berichten negeert de server


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
        """Maakt de hele editor-toestand leeg, inclusief een open herhaal-blok.
        Heeft geen effect op het spel: de wachtrij van de speler blijft ongemoeid."""
        self.regels.clear()
        self.blok = []
        self.diepte = 0
        self.markering = ""
        self.hint = None

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
        if isinstance(r, Shield):
            # elke speler typt kolommen vanaf zijn eigen kant; het veld rekent in echte x
            r = Shield(eigen_kolom(nummer, r.x), r.y)
        if isinstance(r, Bomb):
            # dx = 1 is "vooruit"; voor speler 2 is dat op het veld kolom -1
            r = Bomb(r.dx * RICHTING[nummer], r.dy)
        if isinstance(r, RepeatStart):
            if self.diepte >= MAX_DIEPTE:
                self.markering = "fout"
                self.hint = HINT_TE_DIEP
                return False
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
            try:
                stappen = expand(self.blok, max_stappen=MAX_WACHTRIJ)
            except ValueError:
                gelukt, hint = False, HINT_TE_VEEL      # het blok zelf is te groot
            else:
                gelukt, hint = game.voeg_stappen_toe(nummer, stappen), MELD_DRUK
            self.blok = []
            nieuw = "ok" if gelukt else "fout"
            for regel in self.regels:
                if regel.markering == "wacht":
                    regel.markering = nieuw
            self._bevries(nieuw, tekst, 0)
            if not gelukt:
                self.hint = hint
            return True
        # Move / Shoot / Shield / Bomb
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
        self.regels.append(Regel(markering, tekst.strip()[:MAX_REGEL_LENGTE], inspringing))
        del self.regels[:-MAX_REGELS]
        self.markering = "wacht" if self.diepte else ""
