# Robot Wars – bommen

Datum: 20 september 2026
Voor: Martijn & Wessel
Status: goedgekeurd, klaar voor implementatieplan
Hoort bij: `2026-09-20-robotwars-design.md` (het hoofdontwerp; dit is een uitbreiding)

## 1. Wat is het

Naast schieten en schilden krijgt elke speler **3 bommen** per potje. Een bom
leg je op één van de 9 vakjes rondom (of onder) je robot. Staat daar een robot,
dan is die meteen kapot. Anders blijft de bom liggen als **mijn**, zichtbaar
voor allebei, en gaat af zodra een robot erop stapt.

## 2. Regels

### Neerleggen

- Commando: `bom = (dx, dy)`, met dx en dy elk **−1, 0 of 1**. Het vak ligt
  ten opzichte van de robot: dx = 1 is "vooruit" (richting tegenstander), dx = −1
  achteruit, dy = 1 omhoog, dy = −1 omlaag. `bom = (1, 0)` is dus het vak vóór
  je, `bom = (-1, 1)` schuin achter je één omhoog, `bom = (0, 0)` je eigen vak.
  Verder dan één vakje kan niet: een getal buiten −1..1 is geen geldig commando.
- Het is een stap in de wachtrij en kost één tik, net als een schild.
- Elke speler heeft **3 bommen** per potje; de teller staat in de statuskaart
  naast de schilden ("💣 3").
- Een dode robot (in respawn) kan geen bom leggen; zijn wachtrij is dan toch
  leeg.

### Wat er gebeurt bij het neerleggen

Eerste regel die past:

1. **Er staat een robot** (van de tegenstander, of jijzelf bij `(0, 0)`):
   knal. De robot is meteen kapot: 0 hartjes, wachtrij leeg, terug op het
   startvak na 3 tikken (zoals nu bij sneuvelen door een kogel).
2. **Er ligt al een mijn** (van wie ook): beide knallen en zijn weg; niemand
   raakt gewond. Zo ruim je een mijn van de tegenstander op ten koste van een
   eigen bom.
3. **Anders**: de bom blijft liggen als mijn.

### Mijnen

- Een mijn is zichtbaar voor beide spelers.
- **Een robot die op een mijn stapt, is meteen kapot** (zie 1). De mijn is
  daarna weg. Dat geldt ook voor je eigen mijn.
- Kogels vliegen over mijnen heen; een mijn blokkeert een schot niet en gaat
  er niet van af.
- Een mijn blokkeert lopen niet (anders zou hij nooit afgaan).
- Robo (de computerspeler) legt geen bommen. Hij stapt wel niet op een mijn:
  ligt er een mijn op zijn volgende vak, dan telt dat als geblokkeerd en wordt
  de andere brug zijn doel (zoals nu bij een schild op zijn pad).

### Geweigerd

Voldoet het commando niet, dan zie je een foutmelding en gebeurt er niets; de
bom telt niet als gebruikt (zoals bij een schild):

| Situatie | Melding |
|---|---|
| bommen op | Je bommen zijn op. |
| buiten het veld | Dat vak bestaat niet. |
| water (rivier zonder brug) | Daar is water. |
| gebouw of schild op het vak | Dat vak is niet leeg. |
| leeg startvak (2,4) of (12,4) | Niet op een startvak, anders kan een robot nooit meer terugkomen. |

Staat er een robot op het startvak, dan mag de bom wél: hij knalt meteen en
er blijft geen mijn liggen. Bruggen en de helft van de tegenstander mogen wel.

### Speler 2

Het veld is voor speler 2 gespiegeld en "vooruit" is intern kolom −1. Daarom
wordt bij speler 2 de getypte dx vermenigvuldigd met zijn looprichting (−1),
zodat `bom = (1, 0)` voor allebei "het vak vóór je" is. dy blijft gelijk.

## 3. Taal

- Nieuw commando `bom = (dx, dy)`. Hoofdletters en spaties zijn vrij, zoals
  overal: `bom=(-1,1)` en `bom = ( -1 , 1 )` zijn hetzelfde.
- Hint bij een fout: `Bom heeft twee getallen van -1 tot 1 nodig: bom = (dx, dy),
  bijvoorbeeld bom = (1, 0) voor het vak vóór je.`
- `HINT_START` wordt: `Begin met robot = ..., schild = (...), bom = (...),
  herhaal ... keer of klaar.`
- Werkt binnen `herhaal … klaar` als elke andere stap.

## 4. Log en beeld

Logteksten (vanuit de kijker, zoals de andere regels):

- `Jij legt een bom op (5, 3)` / `Wessel legt een bom op (9, 3)`
- `💥 Jouw bom raakt Wessel! Zijn robot is kapot` / `💥 De bom van Wessel raakt
  jou! Je robot is kapot`
- `💥 Wessel stapt op een mijn! Zijn robot is kapot` / `💥 Je stapt op een
  mijn! Je robot is kapot`
- `Twee mijnen knallen op (7, 2)`
- `Bom geweigerd: Dat vak is niet leeg.` / `Wessel probeert een bom, maar dat
  mag niet`

Daarna volgt het bestaande "komt terug over 3 seconden"/"is terug"-verhaal.

Beeld:

- Nieuwe sprite `bom`: zwarte bol met lont en vonk, met een dun ringetje in de
  teamkleur van de eigenaar. Als `<symbol>` naast de andere sprites.
- Bij een knal de bestaande 💥 op dat vak, één tik lang (zonder kogelbaan).
- Statuskaart: "💣 3" naast de schilden-teller.

## 5. Techniek

Mijnen komen als eigen lijst naast de schilden; dat volgt precies het bestaande
patroon en houdt de wijziging klein.

- **`parser.py`**: `Bomb(dx, dy)` erbij in `Step`; sjabloon `bom=(±,±)`; `_past`
  leert het teken `±` (optioneel `-`, dan precies één cijfer);
  `_maak_commando` geeft `Invalid(HINT_BOM)` bij een getal buiten −1..1;
  `_hint` kent `bom`.
- **`editor.py`**: waar `Shield.x` voor speler 2 gespiegeld wordt, wordt bij
  `Bomb` de dx vermenigvuldigd met `RICHTING[nummer]`.
- **`game.py`**:
  - `BOMMEN_PER_SPELER = 3`, `Speler.bommen_over`, dataclass `Mijn(x, y,
    eigenaar)`, `Game.mijnen`, `Game.mijn_op(x, y)`, `Game.knallen:
    list[tuple[int, int]]` (explosies van de laatste tik, voor de 💥; wordt
    per tik geleegd zoals `schoten`).
  - `_voer_uit` → `_leg_bom(speler, dx, dy)`: controles met meldingen
    (`MELD_BOMMEN_OP`, `MELD_BESTAAT_NIET`, `MELD_WATER`, `MELD_BEZET`,
    `MELD_STARTVAK`), dan robot / mijn / leeg zoals in hoofdstuk 2.
  - `_loop`: na een geslaagde stap `mijn_op(doel)` → robot kapot, mijn weg,
    knal.
  - Nieuwe helper `_robot_kapot(robot, x, y)`: hartjes op 0, respawn starten,
    wachtrij leegmaken, "dood" loggen. `_schiet` gebruikt hem ook (nu inline).
  - `is_vrij` verandert niet.
  - Nieuwe gebeurtenissen: `bom` (gelegd), `bom_fout`, `bom_raak` (robot kapot
    door bom bij neerleggen, `doel` = geraakte speler), `mijn_raak` (robot
    stapt op mijn, `speler` = wie stapte, `doel` = eigenaar), `mijn_dubbel`.
- **`ai.py`**: in de loopstap telt een mijn op het doelvak als geblokkeerd.
- **`weergave.py`**: `Cel.mijn`, knallen → bestaande `raak`-💥 zonder
  vertraging; logteksten; statuskaart.
- **Templates/sprites**: `<symbol id="bom">` in `spel.html` en in
  `docs/superpowers/specs/sprites.svg`; `veld.html` toont de mijn;
  `status.html` de teller.
- **Hoofdontwerp**: kopje "Bommen" onder Spelregels en `bom = (dx, dy)` in
  hoofdstuk 4 (De taal) van `2026-09-20-robotwars-design.md`.

## 6. Tests (pytest, in de bestaande testbestanden)

- Parser: `bom = (-1,1)` → `Bomb(-1, 1)`; `bom = (0, 0)` → `Bomb(0, 0)`;
  `bom = (2, 0)` → `Invalid` met bomhint; `bom = (-` → `Incomplete`;
  `bom = (--1, 0)` → `Invalid`; `herhaal 2 keer / bom = (1,0) / klaar` → 2 stappen.
- Game: mijn blijft liggen op een leeg vak en `bommen_over` daalt; robot
  stapt op mijn → 0 hartjes, `respawn_over` 3, wachtrij leeg, mijn weg, knal
  gelogd; bom op vak met tegenstander → meteen kapot; `(0, 0)` → eigen robot
  kapot; bom op mijn → beide weg, niemand gewond; geweigerd op water, gebouw,
  schild, startvak, buiten veld en bij 0 bommen, en de bom is niet verbruikt;
  kogel vliegt over een mijn heen en raakt wat erachter staat; lopen over een
  vak met mijn wordt niet geblokkeerd (de robot komt er en sneuvelt).
- Editor: speler 2 typt `bom = (1, 0)` → mijn op x − 1.
- AI: Robo stapt niet op een mijn maar kiest de andere brug.

## 7. Niet in deze versie

Robo die zelf bommen legt, kettingreacties, mijnen die schilden of gebouwen
beschadigen, onzichtbare mijnen.
