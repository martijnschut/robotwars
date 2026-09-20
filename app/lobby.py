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
        self.laatst_gepolld: float = 0.0      # wanneer de wachtende voor het laatst iets vroeg

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
