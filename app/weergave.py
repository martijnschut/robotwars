"""Alles wat de templates nodig hebben: veldmatrix, context en Jinja-filters."""
from __future__ import annotations

from dataclasses import dataclass

from .game import (BREEDTE, BRUG_RIJEN, GEBOUW_LEVENS, HOOGTE, RESPAWN_TIKKEN, RIVIER_X,
                   ROBOT_LEVENS, Game, Gebeurtenis, Mijn, Schild, Speler, eigen_kolom)

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
    mijn: Mijn | None = None
    spoor: bool = False          # de kogel kwam hier langs in de laatste tik
    spoor_index: int = 0         # hoeveelste vakje van de baan (0 = eerste na de schutter)
    raak: bool = False           # hier is iets geraakt in de laatste tik
    knal_vertraging: float = 0.0 # seconden tot de kogel hier aankomt (de 💥 wacht daarop)
    spoor_vertraging: float = 0.0 # seconden tot de kogel dit vakje passeert (het flitsje wacht daarop)
    kanon: str | None = None     # schermrichting van het kanon van de robot hier, zie schermnaam()


STAP_SECONDEN = 0.18   # vliegtijd van de kogel per vakje; 4 vakjes passen ruim in één tik
# Schuin ligt het volgende vakje √2 keer zo ver, dus duurt het ook langer: de kogel gaat
# daardoor overal even hard. √2 × 0,18 ≈ 0,25, naar beneden afgerond zodat het verste
# schot (4 × 0,24 = 0,96 s) nog binnen één tik aankomt — anders mist de 💥 zijn moment.
SCHUINE_STAP_SECONDEN = 0.24


def kolommen(ik: int) -> range:
    """Kolomvolgorde op het scherm: speler 2 ziet het veld gespiegeld."""
    return range(1, BREEDTE + 1) if ik == 1 else range(BREEDTE, 0, -1)


def schermkolom(x: int, ik: int) -> int:
    """Op welke schermkolom (1..13) staat veldkolom x voor kijker ik. Dat is ook het
    kolomnummer dat de kijker langs de rand ziet en in `schild = (…)` typt."""
    return eigen_kolom(ik, x)


def gridrij(y: int) -> int:
    """Op welke gridrij (1..7) veldrij y staat: het veld is een assenstelsel, dus y=7
    staat bovenaan (gridrij 1) en y=1 onderaan (gridrij 7)."""
    return HOOGTE - y + 1


# stap per hoek op het scherm van de eigen speler: (naar rechts, naar boven)
KANON_STAPPEN = {0: (1, 0), 45: (1, 1), 90: (0, 1), 135: (-1, 1),
                 180: (-1, 0), 225: (-1, -1), 270: (0, -1), 315: (1, -1)}


def schermnaam(dx: int, dy: int) -> str:
    """Naam van een schermrichting; dx > 0 is naar rechts, dy > 0 is naar boven.
    Recht omhoog/omlaag heet 'omhoog'/'omlaag', schuin heet bijvoorbeeld 'rechtsboven'."""
    if dx == 0:
        return "omhoog" if dy > 0 else "omlaag"
    horizontaal = "rechts" if dx > 0 else "links"
    if dy == 0:
        return horizontaal
    return horizontaal + ("boven" if dy > 0 else "onder")


def kanonrichting(speler: Speler, ik: int) -> str:
    """Waar het kanon van `speler` op het scherm van kijker `ik` heen wijst. De verticale
    helft van de hoek is voor iedereen hetzelfde; de horizontale helft ('vooruit'/'achteruit')
    spiegelt: op ieders scherm kijkt de eigen robot naar rechts en die van de ander naar links."""
    dx, dy = KANON_STAPPEN[speler.kanon]
    if speler.nummer != ik:
        dx = -dx
    return schermnaam(dx, dy)


def stap_seconden(game: Game, schot) -> float:
    """Vliegtijd per vakje van dit schot: schuin duurt een vakje langer dan recht."""
    schutter = game.spelers[schot.schutter]
    x, y = schot.cellen[0]
    schuin = x != schutter.x and y != schutter.y
    return SCHUINE_STAP_SECONDEN if schuin else STAP_SECONDEN


def kogelbanen(game: Game, ik: int) -> list[dict]:
    """Per schot van de laatste tik: waar de kogel over het scherm vliegt.

    Gridkolommen tellen vanaf 2 (kolom 1 is de y-nummers). Gridrijen 1..7 zijn het
    veld met y=7 bovenaan (gridrij = HOOGTE - y + 1); gridrij 8 is de x-nummers.
    De baan is het grid-gebied van rij_van/kol_van tot rij_tot/kol_tot (exclusief, zoals
    CSS grid-area): één rij hoog bij horizontaal, één kolom breed bij verticaal en een
    vierkant blok bij schuin.
    `n` = aantal vakjes inclusief dat van de schutter.
    """
    if game.afgelopen:          # na het winnende schot geen kogel meer laten staan
        return []
    banen = []
    for schot in game.schoten:
        if not schot.cellen:
            continue
        schutter = game.spelers[schot.schutter]
        kol_van, rij_van = schermkolom(schutter.x, ik), gridrij(schutter.y)
        kol_tot, rij_tot = schermkolom(schot.cellen[-1][0], ik), gridrij(schot.cellen[-1][1])
        # kleinere gridrij = hoger op het scherm, dus omkeren voor schermnaam()
        richting = schermnaam(kol_tot - kol_van, rij_van - rij_tot)
        banen.append({
            "kol_van": min(kol_van, kol_tot) + 1,
            "kol_tot": max(kol_van, kol_tot) + 2,
            "rij_van": min(rij_van, rij_tot),
            "rij_tot": max(rij_van, rij_tot) + 1,
            "n": len(schot.cellen) + 1,
            "richting": richting,
            "duur": round(len(schot.cellen) * stap_seconden(game, schot), 2),
            "schutter": schot.schutter,
            "raak": schot.raak is not None,
        })
    return banen


def veld_matrix(game: Game, ik: int) -> list[list[Cel]]:
    """De rijen zoals ze op het scherm staan: van boven (y=7) naar beneden (y=1)."""
    rijen = []
    for y in range(HOOGTE, 0, -1):
        rij = []
        for x in kolommen(ik):
            if x == RIVIER_X:
                soort = "br" if y in BRUG_RIJEN else "w"
            else:
                soort = "b" if x < RIVIER_X else "r"
            cel = Cel(x, y, soort, robot=game.robot_op(x, y),
                      gebouw=game.gebouw_op(x, y), schild=game.schild_op(x, y),
                      mijn=game.mijn_op(x, y))
            if cel.robot is not None:
                cel.kanon = kanonrichting(cel.robot, ik)
            if (x, y) in game.knallen:          # bom of mijn ging hier af: 💥 zonder kogelbaan
                cel.raak = True
            for schot in game.schoten:
                if (x, y) in schot.cellen:
                    stap = stap_seconden(game, schot)
                    cel.spoor = True
                    cel.spoor_index = schot.cellen.index((x, y))
                    cel.spoor_vertraging = round((cel.spoor_index + 1) * stap, 2)
                    if schot.raak == (x, y):
                        cel.raak = True
                        cel.knal_vertraging = round(len(schot.cellen) * stap, 2)
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
        return f"{wie} loopt {e.tekst} naar ({schermkolom(e.x, ik)}, {e.y})"
    if e.soort == "geblokkeerd":
        return f"{wie} loopt tegen iets aan en blijft staan"
    if e.soort == "kanon":
        return f"Jij draait je kanon naar {e.graden}°" if mij else f"{wie} draait het kanon naar {e.graden}°"
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
        return f"{wie} zet een schild op ({schermkolom(e.x, ik)}, {e.y})"
    if e.soort == "schild_fout":
        return f"Schild geweigerd: {e.tekst}" if mij else f"{wie} probeert een schild, maar dat mag niet"
    if e.soort == "bom":
        return f"{wie} legt een bom op ({schermkolom(e.x, ik)}, {e.y})"
    if e.soort == "bom_fout":
        return f"Bom geweigerd: {e.tekst}" if mij else f"{wie} probeert een bom, maar dat mag niet"
    if e.soort == "bom_raak":
        if e.doel == e.speler:
            return "💥 Je legt een bom op jezelf!" if mij else f"💥 {wie} legt een bom op zichzelf!"
        return f"💥 De bom van {wie} raakt jou!" if doel_mij else f"💥 Jouw bom raakt {doel_naam}!"
    if e.soort == "mijn_raak":
        return "💥 Je stapt op een mijn!" if mij else f"💥 {wie} stapt op een mijn!"
    if e.soort == "mijn_dubbel":
        return f"Twee mijnen knallen op ({schermkolom(e.x, ik)}, {e.y})"
    if e.soort == "win":
        return "🏆 Jij wint!" if mij else f"🏆 {wie} wint!"
    return e.soort


def log_regels(game: Game, ik: int, aantal: int = 10) -> list[dict]:
    """De laatste `aantal` gebeurtenissen als regels voor het log, nieuwste eerst."""
    return [
        {"tik": tik, "tijd": mmss(tik), "tekst": log_tekst(game, ik, e), "soort": e.soort, "mij": e.speler == ik}
        for tik, e in list(game.log)[::-1][:aantal]
    ]


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
