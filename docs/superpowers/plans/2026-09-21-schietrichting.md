# Schietrichting in graden – implementatieplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `robot = schiet(90)` schiet omhoog, `schiet(180)` achteruit, `schiet(270)` omlaag; `schiet` en `schiet(0)` blijven vooruit.

**Architecture:** `Shoot` krijgt een veld `graden` (default 0). De parser krijgt één extra sjabloon `robot=schiet(#)` en een hint voor foute graden. `Game._schiet` vertaalt graden naar een (dx, dy)-stap per vakje, de rest van de schietlogica blijft gelijk. De weergave beschrijft een kogelbaan voortaan als grid-gebied met `rij_van/rij_tot/kol_van/kol_tot`, zodat verticale banen hetzelfde pad volgen als horizontale; CSS krijgt twee extra keyframes.

**Tech Stack:** Python 3.12+, FastAPI/Jinja2, pytest via `uv run pytest`. Spec: `docs/superpowers/specs/2026-09-21-schietrichting-design.md`.

---

## Bestanden

- `app/parser.py` – `Shoot.graden`, sjabloon `robot=schiet(#)`, `#` leest tot 3 cijfers, `HINT_GRADEN`.
- `app/game.py` – `_schiet(speler, graden)` met richtingvector.
- `app/weergave.py` – `kogelbanen` met `rij_van/rij_tot` en richtingen `omhoog`/`omlaag`.
- `app/templates/fragments/veld.html` – grid-area uit de vier nieuwe sleutels.
- `app/static/style.css` – keyframes `vlieg-omhoog`/`vlieg-omlaag`, gedraaide sprite.
- `app/templates/start.html` – regel in de speluitleg.
- `tests/test_parser.py`, `tests/test_game.py`, `tests/test_weergave.py`.

Alle tests draaien met `uv run pytest` (nooit pip/venv).

---

### Task 1: Parser – `Shoot(graden)` en het sjabloon `robot=schiet(#)`

**Files:**
- Modify: `app/parser.py`
- Test: `tests/test_parser.py`

- [ ] **Step 1: Schrijf de falende tests**

Voeg onderaan `tests/test_parser.py` toe:

```python
from app.parser import HINT_GRADEN, HINT_ROBOT


def test_schiet_zonder_haakjes_is_nul_graden():
    assert parse_line("robot = schiet") == Shoot(0)
    assert Shoot() == Shoot(0)


def test_schiet_in_vier_richtingen():
    for graden in (0, 90, 180, 270):
        assert parse_line(f"robot = schiet({graden})") == Shoot(graden)
    assert parse_line("robot=schiet( 90 )") == Shoot(90)     # spaties maken niet uit
    assert parse_line("robot = schiet(090)") == Shoot(90)     # voorloopnul is geen fout


def test_schiet_foute_graden_geeft_graden_hint():
    assert parse_line("robot = schiet(45)") == Invalid(HINT_GRADEN)
    assert parse_line("robot = schiet(360)") == Invalid(HINT_GRADEN)
    assert parse_line("robot = schiet 90") == Invalid(HINT_GRADEN)      # haakjes vergeten
    assert parse_line("robot = schiet omhoog") == Invalid(HINT_GRADEN)  # woord in plaats van graden
    assert "robot = schiet(90)" in HINT_GRADEN


def test_schiet_half_getypt_is_incomplete():
    assert parse_line("robot = schiet(") == Incomplete()
    assert parse_line("robot = schiet(9") == Incomplete()
    assert parse_line("robot = schiet(270") == Incomplete()


def test_andere_robot_fouten_houden_de_oude_hint():
    assert parse_line("robot = links") == Invalid(HINT_ROBOT.format("links"))
```

- [ ] **Step 2: Draai de tests en zie ze falen**

Run: `uv run pytest tests/test_parser.py -v`
Expected: ImportError op `HINT_GRADEN` (de hele module faalt).

- [ ] **Step 3: Implementeer in `app/parser.py`**

Vervang de klasse `Shoot`:

```python
@dataclass(frozen=True)
class Shoot:
    """Schiet in graden: 0 vooruit, 90 omhoog, 180 achteruit, 270 omlaag."""
    graden: int = 0
```

Voeg na `HINT_ROBOT` toe:

```python
HINT_GRADEN = ("Schiet in 0, 90, 180 of 270 graden, bijvoorbeeld robot = schiet(90) voor omhoog. "
               "0 is vooruit, 180 achteruit, 270 omlaag.")
GRADEN = (0, 90, 180, 270)
```

Pas het commentaar boven `_SJABLONEN` aan en voeg het sjabloon toe (direct na `"robot=schiet"`):

```python
# Sjablonen zonder spaties; '#' staat voor een getal van 1 tot 3 cijfers,
# '±' voor een getal van één cijfer met optioneel een minteken ervoor.
_SJABLONEN = (
    "robot=vooruit",
    "robot=achteruit",
    "robot=omhoog",
    "robot=omlaag",
    "robot=schiet",
    "robot=schiet(#)",
    "schild=(#,#)",
    "bom=(±,±)",
    "herhaal#keer",
    "klaar",
)
```

In `_past`, bij `if teken == "#":`, verander `i - start < 2` in `i - start < 3`.

In `_maak_commando` vervang de `robot=`-tak:

```python
    if sjabloon.startswith("robot="):
        waarde = sjabloon[len("robot="):]
        if waarde == "schiet":
            return Shoot()
        if waarde == "schiet(#)":
            graden = getallen[0]
            return Shoot(graden) if graden in GRADEN else Invalid(HINT_GRADEN)
        return Move(waarde)
```

In `_hint` vervang de `robot`-tak:

```python
    if compact.startswith("robot=schiet"):
        return HINT_GRADEN       # haakjes vergeten, of een woord in plaats van graden
    if compact.startswith("robot"):
        rest = tekst.split("=", 1)[1].strip() if "=" in tekst else tekst.strip()
        return HINT_ROBOT.format(rest[:40])
```

- [ ] **Step 4: Draai alle tests**

Run: `uv run pytest -q`
Expected: alles slaagt. (`schild = (123, 4)` en `herhaal 100 keer` geven nog steeds dezelfde melding als eerst: het getal wordt nu gelezen en daarna afgekeurd door het spel resp. `MAX_HERHAAL`.)

- [ ] **Step 5: Commit**

```bash
git add app/parser.py tests/test_parser.py
git commit -m "Parser: robot = schiet(graden) met 0/90/180/270 en hint bij foute graden

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Game – schieten in vier richtingen

**Files:**
- Modify: `app/game.py` (`_voer_uit`, `_schiet`)
- Test: `tests/test_game.py`

- [ ] **Step 1: Schrijf de falende tests**

Voeg onderaan `tests/test_game.py` toe:

```python
from app.game import GEBOUW_LEVENS


def test_schiet_omhoog_raakt_robot_in_dezelfde_kolom():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 4, 2
    g.spelers[2].x, g.spelers[2].y = 4, 5        # drie vakjes erboven
    g.voeg_stappen_toe(1, [Shoot(90)])
    g.tick()
    assert g.spelers[2].robot_levens == 4
    assert g.schoten[0].cellen == [(4, 3), (4, 4), (4, 5)]
    assert g.schoten[0].raak == (4, 5)


def test_schiet_omlaag_stopt_bij_schild():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 3, 6
    g.schilden.append(Schild(3, 4, eigenaar=1))
    g.spelers[2].x, g.spelers[2].y = 3, 3
    g.voeg_stappen_toe(1, [Shoot(270)])
    g.tick()
    assert g.spelers[2].robot_levens == 5
    assert g.schild_op(3, 4).levens == SCHILD_LEVENS - 1
    assert g.schoten[0].raak == (3, 4)


def test_schiet_achteruit_is_gespiegeld_per_speler():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 8, 1        # speler 1 staat rechts van speler 2
    g.spelers[2].x, g.spelers[2].y = 5, 1
    g.voeg_stappen_toe(1, [Shoot(180)])          # achteruit = naar links voor speler 1
    g.tick()
    assert g.spelers[2].robot_levens == 4
    assert g.schoten[0].cellen == [(7, 1), (6, 1), (5, 1)]   # over het water heen
    g.voeg_stappen_toe(2, [Shoot(180)])          # achteruit = naar rechts voor speler 2
    g.tick()
    assert g.spelers[1].robot_levens == 4
    assert g.schoten[0].cellen == [(6, 1), (7, 1), (8, 1)]


def test_schiet_achteruit_vanaf_startvak_raakt_eigen_toren():
    g = nieuw()                                  # speler 1 op (2,4), eigen toren op (1,4)
    g.voeg_stappen_toe(1, [Shoot(180)])
    g.tick()
    assert g.spelers[1].gebouw_levens == GEBOUW_LEVENS - 1
    assert g.schoten[0].cellen == [(1, 4)] and g.schoten[0].raak == (1, 4)
    g.spelers[1].gebouw_levens = 1
    g.voeg_stappen_toe(1, [Shoot(180)])
    g.tick()
    assert g.winnaar == 2 and g.afgelopen        # eigen toren kapot: de ander wint


def test_schiet_omhoog_aan_de_rand_is_mis():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 2, 6        # één vakje onder de bovenrand
    g.voeg_stappen_toe(1, [Shoot(90)])
    g.tick()
    assert g.schoten[0].raak is None
    assert g.schoten[0].cellen == [(2, 7)]       # alleen het vakje binnen het veld


def test_schiet_zonder_graden_is_vooruit():
    g = nieuw()
    g.spelers[1].x, g.spelers[1].y = 4, 3
    g.spelers[2].x, g.spelers[2].y = 6, 3
    g.voeg_stappen_toe(1, [Shoot()])
    g.tick()
    assert g.schoten[0].raak == (6, 3)
```

- [ ] **Step 2: Draai de tests en zie ze falen**

Run: `uv run pytest tests/test_game.py -v -k "schiet_omhoog or schiet_omlaag or schiet_achteruit or schiet_zonder"`
Expected: de omhoog/omlaag/achteruit-tests falen (de kogel vliegt nog altijd vooruit, dus `cellen` en `raak` kloppen niet); `schiet_zonder_graden` slaagt al.

- [ ] **Step 3: Implementeer in `app/game.py`**

In `_voer_uit`:

```python
        elif isinstance(stap, Shoot):
            self._schiet(speler, stap.graden)
```

Vervang de kop en de eerste regels van `_schiet` (tot en met de regel `x, y = ...` in de lus); de rest van de methode blijft ongewijzigd:

```python
    def _schiet(self, speler: Speler, graden: int) -> None:
        """Kogel vliegt max SCHIET_BEREIK vakjes in de schietrichting (0 vooruit, 90 omhoog,
        180 achteruit, 270 omlaag; vooruit/achteruit gespiegeld per speler zoals bij lopen)
        en raakt het eerste schild, de eerste robot of het eerste gebouw dat hij tegenkomt.
        Ook je eigen toren: een kogel raakt wat hij tegenkomt."""
        dx, dy = {
            0: (speler.richting, 0),
            180: (-speler.richting, 0),
            90: (0, 1),      # y + 1
            270: (0, -1),    # y - 1
        }[graden]
        cellen: list[tuple[int, int]] = []
        raak: tuple[int, int] | None = None
        for i in range(1, SCHIET_BEREIK + 1):
            x, y = speler.x + dx * i, speler.y + dy * i
```

- [ ] **Step 4: Draai alle tests**

Run: `uv run pytest -q`
Expected: alles slaagt (Robo's `Shoot()` is `Shoot(0)`, dus `tests/test_ai.py` verandert niet).

- [ ] **Step 5: Commit**

```bash
git add app/game.py tests/test_game.py
git commit -m "Game: schieten in vier richtingen, ook je eigen toren is raakbaar

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Weergave – verticale kogelbanen

**Files:**
- Modify: `app/weergave.py` (`kogelbanen`)
- Modify: `app/templates/fragments/veld.html` (de `kogelbaan`-div)
- Modify: `app/static/style.css` (regels rond `.kogelbaan`)
- Test: `tests/test_weergave.py`

- [ ] **Step 1: Pas de bestaande test aan en schrijf de nieuwe**

In `tests/test_weergave.py`, in `test_kogelbanen_vliegen_over_het_scherm`, vervang de eerste assert:

```python
    assert baan == {"kol_van": 3, "kol_tot": 8, "rij_van": 7, "rij_tot": 8, "n": 5, "richting": "rechts",
                    "duur": round(4 * STAP_SECONDEN, 2), "schutter": 1, "raak": False}
```

en verderop in dezelfde test:

```python
    assert kogelbanen(g, 1)[0]["rij_van"] == 1
```

Voeg direct na die test toe:

```python
def test_kogelbanen_verticaal():
    g = Game("g", "A", "B")
    g.spelers[1].x, g.spelers[1].y = 3, 2
    g.voeg_stappen_toe(1, [Shoot(90)])
    g.tick()                                # mis: cellen (3,3)..(3,6)
    (baan,) = kogelbanen(g, 1)
    # één kolom breed (schermkolom 3 → gridkolom 4); schutter op y=2 is gridrij 6, eind y=6 is gridrij 2
    assert baan == {"kol_van": 4, "kol_tot": 5, "rij_van": 2, "rij_tot": 7, "n": 5, "richting": "omhoog",
                    "duur": round(4 * STAP_SECONDEN, 2), "schutter": 1, "raak": False}
    # speler 2 ziet het gespiegeld in x, maar omhoog blijft omhoog
    (baan2,) = kogelbanen(g, 2)
    assert baan2["kol_van"] == 12 and baan2["richting"] == "omhoog"
    # omlaag, treffer op het vakje eronder: n = 2, gridrijen 6 t/m 7
    g.spelers[2].x, g.spelers[2].y = 3, 1
    g.voeg_stappen_toe(1, [Shoot(270)])
    g.tick()
    (baan3,) = kogelbanen(g, 1)
    assert baan3["richting"] == "omlaag" and baan3["n"] == 2 and baan3["raak"] is True
    assert baan3["rij_van"] == 6 and baan3["rij_tot"] == 8 and baan3["kol_van"] == 4
```

- [ ] **Step 2: Draai de tests en zie ze falen**

Run: `uv run pytest tests/test_weergave.py -v -k kogelbanen`
Expected: beide falen (`"rij"` in plaats van `rij_van`/`rij_tot`; verticale baan krijgt nu nog `richting` `links`/`rechts` en de verkeerde kolommen).

- [ ] **Step 3: Implementeer `kogelbanen` in `app/weergave.py`**

Vervang de hele functie:

```python
def kogelbanen(game: Game, ik: int) -> list[dict]:
    """Per schot van de laatste tik: waar de kogel over het scherm vliegt.

    Gridkolommen tellen vanaf 2 (kolom 1 is de y-nummers). Gridrijen 1..7 zijn het
    veld met y=7 bovenaan (gridrij = HOOGTE - y + 1); gridrij 8 is de x-nummers.
    De baan is het grid-gebied rij_van/kol_van t/m rij_tot/kol_tot (exclusief, zoals
    CSS grid-area): één rij hoog bij horizontaal, één kolom breed bij verticaal.
    `n` = aantal vakjes inclusief dat van de schutter.
    """
    if game.afgelopen:          # na het winnende schot geen kogel meer laten staan
        return []
    banen = []
    for schot in game.schoten:
        if not schot.cellen:
            continue
        schutter = game.spelers[schot.schutter]
        van = (schermkolom(schutter.x, ik), gridrij(schutter.y))
        tot = (schermkolom(schot.cellen[-1][0], ik), gridrij(schot.cellen[-1][1]))
        if tot[0] > van[0]:
            richting = "rechts"
        elif tot[0] < van[0]:
            richting = "links"
        elif tot[1] < van[1]:   # kleinere gridrij = hoger op het scherm
            richting = "omhoog"
        else:
            richting = "omlaag"
        banen.append({
            "kol_van": min(van[0], tot[0]) + 1,
            "kol_tot": max(van[0], tot[0]) + 2,
            "rij_van": min(van[1], tot[1]),
            "rij_tot": max(van[1], tot[1]) + 1,
            "n": len(schot.cellen) + 1,
            "richting": richting,
            "duur": round(len(schot.cellen) * STAP_SECONDEN, 2),
            "schutter": schot.schutter,
            "raak": schot.raak is not None,
        })
    return banen
```

- [ ] **Step 4: Pas het template aan**

In `app/templates/fragments/veld.html` vervang de `style` van de kogelbaan-div:

```html
  <div class="kogelbaan {{ b.richting }}{% if not b.raak %} mis{% endif %}"
       style="grid-area: {{ b.rij_van }} / {{ b.kol_van }} / {{ b.rij_tot }} / {{ b.kol_tot }}; --n: {{ b.n }}; --duur: {{ b.duur }}s">
```

- [ ] **Step 5: Pas de CSS aan**

In `app/static/style.css` vervang het blok van `.kogelbaan { ... }` t/m `@keyframes doof` door:

```css
.kogelbaan { position: relative; z-index: 3; pointer-events: none; }
/* horizontaal: de kogel is één vakje breed (100% / n) en schuift met `left` over de baan */
.kogelbaan svg { position: absolute; top: 2%; left: 0; height: 96%; width: calc(100% / var(--n)); filter: drop-shadow(0 0 6px var(--geel)); animation: vlieg-rechts var(--duur) linear forwards; }
.kogelbaan.links svg { transform: scaleX(-1); animation-name: vlieg-links; }
/* verticaal: één vakje hoog, schuift met `top`; de sprite wijst naar rechts, dus draaien */
.kogelbaan.omhoog svg, .kogelbaan.omlaag svg { left: 2%; width: 96%; height: calc(100% / var(--n)); }
.kogelbaan.omhoog svg { transform: rotate(-90deg); animation-name: vlieg-omhoog; }
.kogelbaan.omlaag svg { transform: rotate(90deg); animation-name: vlieg-omlaag; }
.kogelbaan.mis svg { animation: vlieg-rechts var(--duur) linear forwards, doof var(--duur) linear forwards; }
.kogelbaan.mis.links svg { animation-name: vlieg-links, doof; }
.kogelbaan.mis.omhoog svg { animation-name: vlieg-omhoog, doof; }
.kogelbaan.mis.omlaag svg { animation-name: vlieg-omlaag, doof; }
@keyframes vlieg-rechts { from { left: 0; } to { left: calc(100% - 100% / var(--n)); } }
@keyframes vlieg-links { from { left: calc(100% - 100% / var(--n)); } to { left: 0; } }
@keyframes vlieg-omhoog { from { top: calc(100% - 100% / var(--n)); } to { top: 0; } }
@keyframes vlieg-omlaag { from { top: 0; } to { top: calc(100% - 100% / var(--n)); } }
@keyframes doof { 0%, 75% { opacity: 1; } 100% { opacity: 0; } }
```

- [ ] **Step 6: Draai alle tests**

Run: `uv run pytest -q`
Expected: alles slaagt.

- [ ] **Step 7: Bekijk het in de browser**

Run: `uv run uvicorn app.main:app --port 8000` en open http://localhost:8000, speel tegen de computer. Typ `robot = omhoog`, dan `robot = schiet(270)`: de kogel moet omlaag vliegen met de punt naar beneden en uitdoven op de onderrand. Typ `robot = schiet(180)`: kogel naar links in je eigen toren, 💥 op de toren, hartje eraf in het log. Stop de server daarna.

- [ ] **Step 8: Commit**

```bash
git add app/weergave.py app/templates/fragments/veld.html app/static/style.css tests/test_weergave.py
git commit -m "Weergave: kogel vliegt ook omhoog en omlaag

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Speluitleg op de startpagina

**Files:**
- Modify: `app/templates/start.html`

- [ ] **Step 1: Pas de regel over schieten aan**

Vervang in `app/templates/start.html` de `<li>` met 🔫 door:

```html
    <li>🔫 <code>robot = schiet</code> schiet 4 vakjes vooruit. Met graden kies je de richting: <code>robot = schiet(90)</code> is omhoog, 0 vooruit, 180 achteruit, 270 omlaag. Raak de toren van de ander 5 keer en je wint!</li>
```

- [ ] **Step 2: Draai alle tests**

Run: `uv run pytest -q`
Expected: alles slaagt.

- [ ] **Step 3: Commit en push (push naar main = deploy naar robot.schut.me)**

```bash
git add app/templates/start.html
git commit -m "Startpagina: uitleg over schieten in graden

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
git push
```
