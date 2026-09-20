"""Lobby: wie is wie (cookie-token), wie wacht, en welke spellen lopen er."""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field

from .ai import kies_stap
from .editor import Editor
from .game import Game

OPRUIMEN_NA = 300   # seconden na het einde van een spel
NAAM_COMPUTER = "Robo"
MAX_SESSIES = 5000        # cookies die we onthouden; daarboven vergeten we de oudste zonder spel
MAX_SPELLEN = 200         # lopende spellen tegelijk; daarboven "het is druk"
SESSIE_TTL = 24 * 3600    # seconden stilte waarna een sessie zonder spel vergeten wordt


@dataclass
class Uitslag:
    """Hoe het laatste potje afliep, vanuit het perspectief van één speler."""
    tegen: str
    ik_won: bool
    opgegeven: bool      # het spel eindigde doordat iemand wegviel of stopte
    ik_was_weg: bool     # ...en dat was ik
    gestopt: bool        # ...bewust, met de knop "Stop spel" (anders: verbinding weg)
    seconden: int
    te_lang: bool = False   # de server heeft het potje gestopt omdat het te lang duurde


@dataclass
class Sessie:
    token: str
    naam: str
    game_id: str | None = None
    nummer: int | None = None
    laatste_uitslag: Uitslag | None = None
    laatst_gezien: float = field(default_factory=time.time)


class Lobby:
    def __init__(self) -> None:
        self.sessies: dict[str, Sessie] = {}
        self.games: dict[str, Game] = {}
        self.spelers_van: dict[str, list[str]] = {}   # game_id -> tokens van de spelers
        self.wachtende: str | None = None     # token van de speler die wacht
        self.wacht_sinds: float = 0.0
        self.laatst_gepolld: float = 0.0      # wanneer de wachtende voor het laatst iets vroeg

    def registreer(self, naam: str, token: str | None = None) -> Sessie:
        sessie = self.sessies.get(token) if token else None
        if sessie is None:
            self._maak_plaats()
            sessie = Sessie(secrets.token_urlsafe(16), naam)
            self.sessies[sessie.token] = sessie
        else:
            sessie.naam = naam
        sessie.laatst_gezien = time.time()
        return sessie

    def _maak_plaats(self) -> None:
        """Bij MAX_SESSIES sessies: vergeet de langst niet geziene sessies zonder lopend spel."""
        te_veel = len(self.sessies) - MAX_SESSIES + 1
        if te_veel <= 0:
            return
        kandidaten = sorted((s for s in self.sessies.values() if not self._speelt(s)),
                            key=lambda s: s.laatst_gezien)
        for sessie in kandidaten[:te_veel]:
            del self.sessies[sessie.token]

    def _speelt(self, sessie: Sessie) -> bool:
        game = self.games.get(sessie.game_id) if sessie.game_id else None
        return game is not None and not game.afgelopen

    def sessie(self, token: str | None) -> Sessie | None:
        return self.sessies.get(token) if token else None

    def vol(self) -> bool:
        """True als er al MAX_SPELLEN potjes lopen: dan komt er even geen spel bij."""
        return sum(1 for g in self.games.values() if not g.afgelopen) >= MAX_SPELLEN

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
            if self.wachtende is None:
                self.wacht_sinds = self.laatst_gepolld = time.time()
            self.wachtende = token
            return None
        ander = self.wachtende
        self.wachtende = None
        return self._nieuwe_game(ander, token, tegen_computer=False)

    def verlaat_wachtrij(self, token: str) -> None:
        if self.wachtende == token:
            self.wachtende = None

    def ruim_wachtende_op(self, nu: float, max_stil: float = 5.0) -> bool:
        """Vergeet een wachtende die al max_stil seconden niet meer pollt (tabblad dicht),
        anders wordt de volgende speler aan een spook gekoppeld. True als er iets opgeruimd is."""
        if self.wachtende is not None and nu - self.laatst_gepolld > max_stil:
            self.wachtende = None
            return True
        return False

    def start_tegen_computer(self, token: str) -> Game:
        self.verlaat_wachtrij(token)
        return self._nieuwe_game(token, None, tegen_computer=True)

    def bewaar_uitslag(self, game: Game) -> None:
        """Zet de uitslag van een afgelopen spel bij de sessies van zijn spelers, zodat ze
        hem ook zien als het spel al opgeruimd is (bijvoorbeeld na verbindingsverlies)."""
        for token in self.spelers_van.get(game.id, []):
            sessie = self.sessies.get(token)
            if sessie is None or sessie.game_id != game.id:
                continue
            ik_won = sessie.nummer == game.winnaar
            te_lang = game.opgegeven_reden == "tijd"
            sessie.laatste_uitslag = Uitslag(
                tegen=game.tegenstander(sessie.nummer).naam,
                ik_won=ik_won,
                opgegeven=game.opgegeven,
                ik_was_weg=game.opgegeven and not ik_won and not te_lang,
                gestopt=game.opgegeven_reden == "gestopt",
                seconden=game.tik,
                te_lang=te_lang,
            )

    def ruim_op(self, nu: float | None = None) -> list[str]:
        """Verwijdert spellen die al OPRUIMEN_NA seconden afgelopen zijn (geeft hun ids)
        en sessies zonder lopend spel die al SESSIE_TTL seconden niets lieten horen."""
        nu = nu or time.time()
        weg = [g.id for g in self.games.values()
               if g.geeindigd_op is not None and nu - g.geeindigd_op > OPRUIMEN_NA]
        for game_id in weg:
            del self.games[game_id]
            self.spelers_van.pop(game_id, None)
        oud = [s.token for s in self.sessies.values()
               if nu - s.laatst_gezien > SESSIE_TTL and not self._speelt(s)]
        for token in oud:
            del self.sessies[token]
        return weg

    def _nieuwe_game(self, token1: str, token2: str | None, tegen_computer: bool) -> Game:
        s1 = self.sessies[token1]
        s2 = self.sessies[token2] if token2 else None
        game_id = secrets.token_urlsafe(6)
        game = Game(game_id, s1.naam, s2.naam if s2 else NAAM_COMPUTER,
                    tegen_computer=tegen_computer, brein=kies_stap if tegen_computer else None)
        game.editors = {1: Editor(), 2: Editor()}
        self.games[game_id] = game
        self.spelers_van[game_id] = [token1] + ([token2] if token2 else [])
        s1.game_id, s1.nummer, s1.laatste_uitslag = game_id, 1, None
        if s2:
            s2.game_id, s2.nummer, s2.laatste_uitslag = game_id, 2, None
        return game
