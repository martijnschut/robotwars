"""Robo, de computerspeler: kiest per tik één stap op basis van het actuele veld."""
from __future__ import annotations

from .game import Game, Speler, BRUG_RIJEN, RIVIER_X, SCHIET_BEREIK, eigen_helft
from .parser import Move, Shoot, Shield, Step

SCHILD_VAK = (11, 4)   # vóór Robo's startvak (12,4), dus de kogel raakt het schild eerder dan de toren

_DELTA = {"vooruit": (1, 0), "achteruit": (-1, 0), "omhoog": (0, 1), "omlaag": (0, -1)}


def _verticaal(van_y: int, naar_y: int) -> str:
    """Welke kant op om van van_y naar naar_y te komen: y loopt van onder naar boven,
    dus naar een hogere y is 'omhoog'."""
    return "omhoog" if naar_y > van_y else "omlaag"


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
    return ik.x + dx * ik.richting, ik.y + dy


def _stap_of_schot(game: Game, ik: Speler, richting: str) -> Step | None:
    """Zet een stap als het vak vrij is en er geen mijn ligt. Staat er vooruit een schild
    in de weg, schiet er dan op. Anders None (even wachten)."""
    x, y = _doel(ik, richting)
    if game.is_vrij(x, y) and game.mijn_op(x, y) is None:
        return Move(richting)
    if richting == "vooruit" and game.schild_op(x, y) is not None:
        return Shoot()
    return None


def _kies_brug(game: Game, ik: Speler) -> int:
    """De dichtstbijzijnde brug (bij gelijke afstand de onderste), maar een brug waarvan
    de rij tussen Robo en de rivier een mijn bevat slaat hij over: die kan hij niet
    wegschieten, en omdat hij elke tik opnieuw kiest zou hij anders eeuwig heen en weer
    lopen. Liggen er op beide rijen mijnen, dan toch de dichtstbijzijnde."""
    def afstand(rij: int) -> tuple[int, int]:
        return abs(rij - ik.y), rij
    naar_rivier = range(RIVIER_X, ik.x, 1 if ik.x > RIVIER_X else -1)
    vrij = [rij for rij in BRUG_RIJEN if not any(game.mijn_op(x, rij) for x in naar_rivier)]
    return min(vrij or BRUG_RIJEN, key=afstand)


def _loop_stap(game: Game, ik: Speler, vijand: Speler) -> Step | None:
    if ik.x == RIVIER_X:                         # op de brug: doorlopen
        return _stap_of_schot(game, ik, "vooruit")
    over = (ik.x - RIVIER_X) * ik.richting > 0   # al aan de kant van de vijand
    if not over:
        brug = _kies_brug(game, ik)
        andere = BRUG_RIJEN[1] if brug == BRUG_RIJEN[0] else BRUG_RIJEN[0]
        if ik.y == brug:
            return _stap_of_schot(game, ik, "vooruit")
        stap = _stap_of_schot(game, ik, _verticaal(ik.y, brug))
        if stap is not None:
            return stap
        return _stap_of_schot(game, ik, _verticaal(ik.y, andere))
    doel_y = vijand.gebouw[1]
    if ik.y == doel_y:
        return _stap_of_schot(game, ik, "vooruit")
    return _stap_of_schot(game, ik, _verticaal(ik.y, doel_y))
