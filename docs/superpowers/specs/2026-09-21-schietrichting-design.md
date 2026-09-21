# Robot Wars – schietrichting in graden

Datum: 21 september 2026
Voor: Martijn & Wessel
Status: goedgekeurd, klaar voor implementatieplan
Hoort bij: `2026-09-20-robotwars-design.md` (het hoofdontwerp; dit is een uitbreiding)

## 1. Wat is het

Nu schiet een robot altijd vooruit. Voortaan kies je de richting in **graden**,
zodat Wessel spelenderwijs leert hoe hoeken werken:

```
            90 (omhoog)
               ↑
180 (achteruit) ←  🤖  → 0 (vooruit)
               ↓
           270 (omlaag)
```

Alleen deze vier hoeken bestaan; er wordt niet schuin geschoten.

## 2. Taal

- `robot = schiet(90)` schiet omhoog; `schiet(0)` vooruit, `schiet(180)`
  achteruit, `schiet(270)` omlaag.
- `robot = schiet` zonder haakjes blijft werken en betekent `schiet(0)`.
- Spaties maken niet uit, net als bij de andere commando's:
  `robot=schiet( 90 )` is hetzelfde.
- De graden zijn **relatief aan de speler**, precies zoals lopen: 0 is
  "vooruit" (richting de tegenstander), dus voor speler 1 naar rechts en voor
  speler 2 naar links. 90 is voor allebei omhoog op het scherm, 270 omlaag.
- Een ander getal dan 0, 90, 180 of 270 (bijv. `schiet(45)` of `schiet(360)`)
  is geen geldig commando. Hint (`HINT_GRADEN`):
  *"Schiet in 0, 90, 180 of 270 graden, bijvoorbeeld robot = schiet(90) voor
  omhoog. 0 is vooruit, 180 achteruit, 270 omlaag."*
- Voorloopnullen zijn geen fout: `schiet(090)` leest als 90.
- `robot = schiet(` en `robot = schiet(9` zijn nog onaf (Incomplete), geen
  fout.
- Iets fouts dat met `schiet` begint, zoals `robot = schiet 90` (haakjes
  vergeten) of `robot = schiet omhoog`, krijgt óók `HINT_GRADEN`, zodat het
  voorbeeld met haakjes meteen laat zien hoe het wel moet. De bestaande hint
  ("Ik ken … niet. Probeer vooruit, achteruit, omhoog, omlaag of schiet.")
  blijft voor alle andere onbekende robot-commando's.

### Parser

- `Shoot` krijgt een veld `graden: int = 0`. Alle bestaande `Shoot()` (Robo,
  editor, tests) betekenen daardoor nog steeds "vooruit".
- Nieuw sjabloon `robot=schiet(#)` naast `robot=schiet`. Het `#`-teken leest
  nu 1–2 cijfers; dat wordt 1–3 cijfers, want 180 en 270 hebben er drie. Voor
  `schild = (123, 4)` en `herhaal 100 keer` verandert daardoor de uitkomst
  niet: die geven dezelfde melding als nu ("Dat vak bestaat niet." /
  "maximaal 20").

## 3. Spelregels

- `_schiet` krijgt de graden mee en bepaalt de stap per vakje:
  0 → `(richting, 0)`, 180 → `(−richting, 0)`, 90 → `(0, +1)`, 270 → `(0, −1)`,
  met `richting` = +1 voor speler 1 en −1 voor speler 2 (zoals bij lopen).
- Verder blijft alles gelijk: bereik 4 vakjes, de kogel raakt het eerste
  schild, de eerste robot of de eerste toren die hij tegenkomt, vliegt over
  water heen en stopt aan de rand van het veld (dan "mis").
- **Je eigen toren is niet beschermd.** Vanaf het startvak (2, 4) schiet
  `schiet(180)` recht in je eigen toren op (1, 4), en die verliest dan gewoon
  een leven; bij 0 levens wint de tegenstander. Eén regel zonder
  uitzonderingen: een kogel raakt wat hij tegenkomt. Het log zegt dan
  "Jij raakt jouw toren!" (werkt al). Les: kijk waar je heen schiet.
- `Schot.cellen` is al een lijst van (x, y); daar verandert niets aan.
- **Robo** (de computer) blijft alleen vooruit schieten. Slimmer schieten voor
  Robo is bewust buiten scope; dat kan later apart.

## 4. Weergave

- `kogelbanen` in `weergave.py` geeft naast `links`/`rechts` ook `omhoog`/
  `omlaag`. Bij een verticale baan spant het grid-gebied rijen in plaats van
  kolommen (één kolom breed, `n` rijen hoog).
- CSS: twee extra keyframes `vlieg-omhoog` en `vlieg-omlaag` die `top`
  animeren in plaats van `left`; de kogel-sprite wordt 90° gedraaid zodat de
  staart achter de kogel aan komt. De varianten met `mis` (uitdoven) bestaan
  ook voor verticaal.
- Het lichtspoor per vakje en de 💥 op het geraakte vak werken al per cel en
  kloppen dus vanzelf, ook verticaal.
- De logregel blijft "Jij schiet → raakt …" / "… → mis"; de richting hoeft
  daar niet in.
- Speluitleg op de startpagina (`start.html`) krijgt een regel bij schieten:
  `robot = schiet(90)` schiet omhoog; 0 is vooruit, 90 omhoog, 180 achteruit,
  270 omlaag.

## 5. Tests

- **Parser:** alle vier hoeken geven `Shoot(graden)`; `robot = schiet` geeft
  `Shoot(0)`; spaties in de haakjes mogen; `schiet(45)` en `schiet(360)` geven
  Invalid met `HINT_GRADEN`; `schiet 90` en `schiet omhoog` (zonder haakjes)
  ook; `schiet(` en `schiet(9` zijn Incomplete; `robot = links` houdt de oude
  hint.
- **Game:** `schiet(90)` raakt een robot recht boven de schutter binnen bereik;
  `schiet(270)` raakt een schild eronder; `schiet(180)` raakt wat achter de
  schutter staat, voor speler 2 gespiegeld; `schiet(180)` vanaf het startvak
  raakt de eigen toren en bij 0 levens wint de tegenstander; verticaal
  schieten aan de rand van het veld is "mis" met alleen de vakjes binnen het
  veld in `cellen`; Robo's `Shoot()` gedraagt zich als voorheen.
- **Weergave:** een verticale kogelbaan krijgt richting `omhoog`/`omlaag` en
  spant de juiste gridrijen in één kolom; een horizontale baan blijft zoals
  hij was.

## 6. Bestanden

- `app/parser.py` – `Shoot.graden`, sjabloon `robot=schiet(#)`, `#` tot 3
  cijfers, `HINT_GRADEN` voor foute graden en voor alles wat met `schiet`
  begint maar niet klopt.
- `app/game.py` – `_schiet` met richting uit graden.
- `app/weergave.py` – `kogelbanen` met verticale banen.
- `app/static/style.css` – keyframes en gedraaide sprite voor verticaal.
- `app/templates/start.html` – regel in de speluitleg.
- `tests/test_parser.py`, `tests/test_game.py`, `tests/test_weergave.py`.
