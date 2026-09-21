# Robot Wars – kanon richten in graden

Datum: 21 september 2026
Voor: Martijn & Wessel
Status: goedgekeurd, klaar voor implementatieplan (tweede versie, zie §7)
Hoort bij: `2026-09-20-robotwars-design.md` (het hoofdontwerp; dit is een uitbreiding)

## 1. Wat is het

Nu schiet een robot altijd vooruit. Voortaan heeft elke robot een **kanon** dat
je in **graden** richt, zodat Wessel spelenderwijs leert hoe hoeken werken:

```
            90 (omhoog)
               ↑
180 (achteruit) ←  🤖  → 0 (vooruit)
               ↓
           270 (omlaag)
```

Alleen deze vier hoeken bestaan; er wordt niet schuin geschoten. Richten en
schieten zijn twee losse commando's:

```
kanon = 90         ← het kanon draait naar 90 graden
robot = schiet     ← schiet in die richting
```

De hoek blijft staan tot je hem verandert. `kanon = 90` gevolgd door
`herhaal 3 keer / robot = schiet / klaar` schiet dus drie keer omhoog, net als
een schildpad in Logo: eerst draaien, dan doen.

Waarom niet `robot = schiet(90)`: de editor voert een regel uit zodra hij een
geldig commando is (CT-3000-stijl, geen Enter). `robot = schiet` is geldig én
het begin van `robot = schiet(90)`, dus bij het typen van de haakjes was de
robot al vooruit aan het schieten. Met een apart commando `kanon = …` is geen
enkel commando het begin van een ander, en blijft `robot = schiet` precies wat
het nu is.

## 2. Taal

- `kanon = 90` richt het kanon omhoog; `kanon = 0` vooruit, `kanon = 180`
  achteruit, `kanon = 270` omlaag. Spaties maken niet uit, net als bij de
  andere commando's: `kanon=90` is hetzelfde.
- De graden zijn **relatief aan de speler**, precies zoals lopen: 0 is
  "vooruit" (richting de tegenstander), dus voor speler 1 naar rechts en voor
  speler 2 naar links. 90 is voor allebei omhoog op het scherm, 270 omlaag.
- `robot = schiet` verandert niet: het schiet in de richting waar het kanon
  staat, 4 vakjes ver.
- Een ander getal dan 0, 90, 180 of 270 (bijv. `kanon = 45` of `kanon = 360`)
  is geen geldig commando. Hint (`HINT_KANON`):
  *"Kanon draait naar 0, 90, 180 of 270 graden, bijvoorbeeld kanon = 90 voor
  omhoog. 0 is vooruit, 180 achteruit, 270 omlaag."*
- Voorloopnullen keurt de parser niet af (`090` leest als 90), maar in de editor
  bevriest `kanon = 0` al bij de 0, dus in de praktijk typ je ze nooit.
- `kanon =` en `kanon = 9` zijn nog onaf (Incomplete), geen fout.
- Iets fouts dat met `kanon` begint (`kanon = omhoog`, `kanon 90`) krijgt ook
  `HINT_KANON`.
- Wie toch `robot = schiet(90)` of `robot = schiet omhoog` typt, krijgt een
  hint die naar het goede commando wijst (`HINT_SCHIET`):
  *"Schieten is gewoon robot = schiet. De richting kies je met kanon = 90
  (0 vooruit, 90 omhoog, 180 achteruit, 270 omlaag)."*
  Alle andere onbekende robot-commando's houden de bestaande hint
  ("Ik ken … niet. Probeer vooruit, achteruit, omhoog, omlaag of schiet.").
- `HINT_START` noemt het nieuwe commando: *"Begin met robot = ..., kanon = ...,
  schild = (...), bom = (...), herhaal ... keer of klaar."*

### Parser

- Nieuw commando `Aim(graden)` (naast `Move`, `Shoot`, `Shield`, `Bomb`); het
  is een `Step`, dus het gaat in de wachtrij en mag in een herhaal-blok.
- `Shoot` blijft zonder velden.
- Nieuw sjabloon `kanon=#`. Het `#`-teken leest 1–3 cijfers (180 en 270 hebben
  er drie). Voor `schild = (123, 4)` betekent dat: waar de parser dat getal
  eerst zelf afkeurde met `HINT_SCHILD`, wordt het nu gelezen als
  `Shield(123, 4)` en pas een tik later door het spel afgekeurd met "Dat vak
  bestaat niet." — hetzelfde als nu al gebeurt bij bijvoorbeeld
  `schild = (99, 4)`. Dat is acceptabel. `herhaal 100 keer` geeft dezelfde
  melding als eerst (`MAX_HERHAAL`).
- `GRADEN = (0, 90, 180, 270)` is de enige plek waar de geldige hoeken staan.

## 3. Spelregels

- `Speler` krijgt een veld `kanon: int = 0` (de hoek, één van `GRADEN`).
- `Aim(graden)` kost één tik, zoals elke stap: het zet `speler.kanon` en meldt
  het in het log. Een dode robot heeft een lege wachtrij en richt dus niet.
- `Shoot` schiet in de richting van `speler.kanon`: stap per vakje
  0 → `(richting, 0)`, 180 → `(−richting, 0)`, 90 → `(0, +1)`, 270 → `(0, −1)`,
  met `richting` = +1 voor speler 1 en −1 voor speler 2 (zoals bij lopen).
- Verder blijft schieten gelijk: bereik 4 vakjes, de kogel raakt het eerste
  schild, de eerste robot of de eerste toren die hij tegenkomt, vliegt over
  water heen en stopt aan de rand van het veld (dan "mis").
- **Je eigen toren is niet beschermd.** Vanaf het startvak (2, 4) schiet
  `kanon = 180` + `robot = schiet` recht in je eigen toren op (1, 4), en die
  verliest dan gewoon een leven; bij 0 levens wint de tegenstander. Eén regel
  zonder uitzonderingen: een kogel raakt wat hij tegenkomt. Het log zegt dan
  "Jij raakt jouw toren!" (werkt al). Les: kijk waar je heen schiet.
- **Na sneuvelen staat het kanon weer op 0.** Als een robot kapotgaat wordt
  alles gereset (hartjes, wachtrij, kanon), zoals dat in een spel hoort.
- `Schot.cellen` blijft een lijst van (x, y); daar verandert niets aan.
- **Robo** (de computer) richt nooit en schiet dus altijd vooruit. Slimmer
  schieten voor Robo is bewust buiten scope.

## 4. Weergave

- **Kanon op het veld:** in het vakje van elke robot staat een klein geel
  driehoekje (▲) aan de rand, in de richting waar het kanon wijst. Altijd
  zichtbaar, ook bij 0, zodat "0 is vooruit" meteen te zien is. Op het scherm
  draait het mee met de spiegeling: de weergave rekent de hoek om naar een
  schermrichting `rechts`/`links`/`omhoog`/`omlaag` (0 en 180 hangen af van
  wie kijkt en van wie de robot is; 90 en 270 niet). `Cel` krijgt daarvoor een
  veld `kanon: str | None`, gevuld als er een robot staat.
- **Statuskaart:** `🔫 90°` naast de schilden en bommen, voor beide spelers.
- **Log:** bij richten *"Jij draait je kanon naar 90°"* / *"Robo draait het
  kanon naar 90°"*. Nieuwe gebeurtenis `kanon` met een veld `graden`.
- **Kogelbaan:** `kogelbanen` in `weergave.py` geeft naast `links`/`rechts`
  ook `omhoog`/`omlaag`; een verticale baan spant gridrijen in één kolom
  (`rij_van/rij_tot/kol_van/kol_tot`, exclusief zoals CSS grid-area). CSS
  heeft keyframes `vlieg-omhoog`/`vlieg-omlaag` en draait de kogel-sprite 90°.
  Het lichtspoor per vakje en de 💥 werken al per cel. (Dit deel is al
  gebouwd.)
- **Speluitleg** op de startpagina en in `README.md`: `kanon = 90` richt het
  kanon (0 vooruit, 90 omhoog, 180 achteruit, 270 omlaag); `robot = schiet`
  schiet die kant op.

## 5. Tests

- **Parser:** `kanon = 0/90/180/270` → `Aim(graden)`; spaties en voorloopnul;
  `kanon = 45`/`360`/`omhoog` → `Invalid(HINT_KANON)`; `kanon =` en `kanon = 9`
  Incomplete; `robot = schiet` → `Shoot()`; `robot = schiet(90)` en
  `robot = schiet omhoog` → `Invalid(HINT_SCHIET)`; `robot = links` houdt de
  oude hint; `schild = (123, 4)` → `Shield(123, 4)`.
- **Editor:** een regel teken voor teken invoeren (`kanon = 90`, daarna
  `robot = schiet`) levert wachtrij `[Aim(90), Shoot()]` op, zonder dat
  onderweg iets anders is uitgevoerd.
- **Game:** `Aim(90)` zet `kanon` en kost een tik; schot omhoog raakt een robot
  in dezelfde kolom; omlaag stopt bij een schild; achteruit is gespiegeld per
  speler; achteruit vanaf het startvak raakt de eigen toren en bij 0 levens
  wint de tegenstander; verticaal aan de rand is "mis" (ook met lege baan);
  verticaal is voor speler 2 ook omhoog; `Shoot()` zonder richten is vooruit;
  na sneuvelen staat `kanon` weer op 0.
- **Weergave:** `Cel.kanon` geeft de goede schermrichting voor beide kijkers
  (eigen robot met 0 → `rechts`, robot van de ander met 0 → `links`, 90 →
  `omhoog` voor iedereen); statuskaart toont `🔫 90°`; logtekst bij richten;
  verticale kogelbaan spant de goede gridrijen; verticaal spoor per cel.

## 6. Bestanden

- `app/parser.py` – `Aim`, sjabloon `kanon=#`, `HINT_KANON`, `HINT_SCHIET`,
  `HINT_START` bijgewerkt, `Shoot` weer zonder veld.
- `app/game.py` – `Speler.kanon`, `Aim` uitvoeren, `_schiet` met
  `speler.kanon`, reset bij sneuvelen, gebeurtenis `kanon`.
- `app/weergave.py` – `Cel.kanon`, logtekst, `kogelbanen` (al gebouwd).
- `app/templates/fragments/veld.html` – driehoekje in het robotvakje.
- `app/templates/fragments/status.html` – `🔫 …°`.
- `app/static/style.css` – driehoekje; kogelbanen (al gebouwd).
- `app/templates/start.html`, `README.md` – uitleg.
- `tests/test_parser.py`, `tests/test_editor.py`, `tests/test_game.py`,
  `tests/test_weergave.py`.

## 7. Geschiedenis

De eerste versie van dit ontwerp gebruikte `robot = schiet(90)`. Bij de
eindreview bleek dat onbruikbaar in de echte editor (zie §1). De branch
`schietrichting` bevat het werk van die versie; de kogelbaan-weergave en de
schietlogica daaruit blijven, de parser en de commando-vorm worden omgebouwd.
