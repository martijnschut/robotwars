# Robot Wars – schuin schieten (kanon op 45, 135, 225 en 315)

Datum: 22 september 2026
Voor: Martijn & Wessel
Status: goedgekeurd, klaar voor implementatieplan
Hoort bij: `2026-09-21-schietrichting-design.md` (het kanon in graden; dit is een uitbreiding)

## 1. Wat is het

Het kanon kent nu vier standen. Voortaan zijn het er acht, met stapjes van 45
graden, zodat Wessel de hele wijzerplaat leert kennen:

```
        135   90 (omhoog)  45
            ↖  ↑  ↗
180 (achteruit) ← 🤖 → 0 (vooruit)
            ↙  ↓  ↘
        225   270 (omlaag) 315
```

`kanon = 45` richt schuin vooruit-omhoog, `robot = schiet` schiet die kant op.
Verder verandert er niets: richten en schieten blijven twee losse commando's,
de hoek blijft staan tot je hem verandert, en de kogel vliegt 4 vakjes ver.

## 2. Taal

- `GRADEN` wordt `(0, 45, 90, 135, 180, 225, 270, 315)`. Dat is nog steeds de
  enige plek waar de geldige hoeken staan; de parser zelf verandert niet.
- De graden blijven **relatief aan de speler**, net als bij lopen. De
  horizontale helft van een schuine hoek spiegelt mee (45 is voor speler 1
  naar rechtsboven en voor speler 2 naar linksboven op het echte veld), de
  verticale helft niet: 45, 90 en 135 zijn voor allebei omhoog.
- Onaf en fout gaan vanzelf goed, omdat geen enkele geldige hoek het begin is
  van een andere: `kanon = 3` is onaf (kan nog 315 worden), `kanon = 31` ook,
  `kanon = 315` is een commando. `kanon = 30` is fout en geeft `HINT_KANON`.
- Nieuwe `HINT_KANON`:
  *"Kanon draait met stapjes van 45 graden: 0, 45, 90, 135, 180, 225, 270 of
  315. 0 is vooruit, 90 omhoog, 180 achteruit, 270 omlaag; 45 is er schuin
  tussenin."*
- Nieuwe `HINT_SCHIET`:
  *"Schieten is gewoon robot = schiet. De richting kies je met kanon = 90
  (0 vooruit, 90 omhoog, 180 achteruit, 270 omlaag, en schuin met 45, 135,
  225 of 315)."*
- `HINT_ROBOT`, `HINT_START` en alle andere commando's blijven gelijk.

## 3. Spelregels

- `_schiet` krijgt vier regels bij in de tabel van hoek naar stap per vakje,
  met `richting` = +1 voor speler 1 en −1 voor speler 2:

  | hoek | dx, dy | betekenis |
  |------|--------|-----------|
  | 45   | (richting, +1)  | schuin vooruit-omhoog |
  | 135  | (−richting, +1) | schuin achteruit-omhoog |
  | 225  | (−richting, −1) | schuin achteruit-omlaag |
  | 315  | (richting, −1)  | schuin vooruit-omlaag |

- **Een schuin schot gaat even ver als een recht schot: 4 vakjes.** Eén regel
  om te onthouden — het kanon schiet altijd 4 vakjes. Schuin kom je daarmee
  verder van je robot af, en dat mag.
- Verder verandert er niets aan schieten: de kogel raakt het eerste schild, de
  eerste robot of de eerste toren die hij tegenkomt (ook je eigen toren),
  vliegt over water en bruggen heen, en stopt aan de rand van het veld ("mis").
- `Speler.kanon` blijft een `int` uit `GRADEN` en gaat bij sneuvelen terug
  naar 0.
- **Robo** (de computer) richt nog steeds nooit en schiet dus vooruit. Buiten
  scope.

## 4. Weergave

- **Kanondriehoekje:** `kanonrichting()` rekent de hoek om naar een
  schermrichting. In plaats van vier losse gevallen splitst de functie de hoek
  in een horizontale stap (−1, 0 of +1) en een verticale stap; de horizontale
  stap spiegelt per kijker en per robot, precies zoals nu bij 0 en 180. Dat
  geeft acht namen: `rechts`, `links`, `omhoog`, `omlaag`, `rechtsboven`,
  `linksboven`, `rechtsonder`, `linksonder`. De vier oude namen houden exact
  hun huidige betekenis.
- **CSS:** vier extra regels voor de nieuwe klassen. Het gele driehoekje staat
  in de hoek van het vakje en is 45° gedraaid (`rechtsboven` → `rotate(45deg)`
  rechtsboven in de cel, enzovoort). Op een smal scherm blijft het driehoekje
  kleiner, zoals nu.
- **Kogelbaan:** `kogelbanen()` bepaalt de richting nu met een of-of-keten
  (eerst horizontaal, anders verticaal). Dat wordt: kijk naar het kolomverschil
  én het rijverschil, en zet de twee namen achter elkaar. De berekening van
  `grid-area` blijft ongewijzigd — bij een schuin schot levert diezelfde
  formule vanzelf een vierkant blok op (5×5 vakjes bij een schot van 4).
- **CSS voor de schuine kogel:** de kogel is één vakje groot (breedte én hoogte
  `100% / var(--n)`) en schuift met `left` én `top` tegelijk van hoek naar
  hoek. Vier nieuwe keyframes (`vlieg-rechtsboven`, `vlieg-linksboven`,
  `vlieg-rechtsonder`, `vlieg-linksonder`), en de sprite — die naar rechts
  wijst — draait 45°: rechtsboven −45°, rechtsonder 45°, linksboven −135°,
  linksonder 135°. Dat is dezelfde aanpak als bij omhoog/omlaag (−90°/90°).
  Ook de `mis`-variant (kogel dooft) krijgt de vier richtingen.
- **Spoor en 💥** werken al per vakje via `spoor_index` en veranderen niet.
- **Statuskaart** (`🔫 45°`) en **log** (*"Jij draait je kanon naar 45°"*)
  werken al met elke hoek en veranderen niet.
- **Speluitleg** op de startpagina en in `README.md`: noem de acht standen met
  de wijzerplaat-uitleg dat er tussen elke stand 45 graden zit.

## 5. Tests

- **Parser:** `kanon = 45/135/225/315` → `Aim(graden)`, ook zonder spaties;
  `kanon = 3` en `kanon = 31` zijn Incomplete; `kanon = 30` en `kanon = 400`
  geven `Invalid(HINT_KANON)`; de bestaande tests voor 0/90/180/270 blijven
  gelijk.
- **Editor:** `kanon = 315` teken voor teken invoeren levert `[Aim(315)]` op,
  zonder dat er onderweg iets anders is uitgevoerd.
- **Game:** een schot met 45 raakt een robot op het schuine pad; 315 stopt bij
  het eerste schild schuin naar beneden; 135 is voor speler 2 gespiegeld
  (naar rechtsboven op het echte veld); een schuin schot dat het veld uit
  vliegt is "mis"; een schuin schot gaat maximaal 4 vakjes ver.
- **Weergave:** `Cel.kanon` geeft voor beide kijkers de goede schermrichting
  bij alle acht hoeken (eigen robot met 45 → `rechtsboven`, robot van de ander
  met 45 → `linksboven`, 135 → `linksboven` voor de eigen robot); een schuine
  kogelbaan krijgt de klasse `rechtsboven` en een vierkant `grid-area`; het
  spoor licht op in elk schuin vakje.

## 6. Bestanden

- `app/parser.py` – `GRADEN`, `HINT_KANON`, `HINT_SCHIET`.
- `app/game.py` – vier regels in de richtingstabel van `_schiet`, docstring.
- `app/weergave.py` – `kanonrichting()` en de richtingbepaling in
  `kogelbanen()`.
- `app/static/style.css` – driehoekje in vier hoeken, schuine kogelbanen.
- `app/templates/start.html`, `README.md` – uitleg.
- `tests/test_parser.py`, `tests/test_editor.py`, `tests/test_game.py`,
  `tests/test_weergave.py`.

Geen wijzigingen nodig in `app/editor.py`, `app/ai.py`, `app/db.py` en de
templates: die werken al met elke hoek uit `GRADEN`.
