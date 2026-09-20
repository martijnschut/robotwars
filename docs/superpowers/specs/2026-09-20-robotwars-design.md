# Robot Wars – ontwerp

Datum: 20 september 2026
Voor: Martijn & Wessel
Status: goedgekeurd (tekst en visuals), klaar voor implementatieplan

## 1. Wat is het

Robot Wars is een online spel voor kinderen van 8–12 jaar: een kruising tussen
[CT-3000](https://github.com/Q42/CT-3000) (programmeren in simpel Nederlands,
`robot = vooruit`) en Clash Royale (twee kanten, twee bruggen, val het gebouw van
de tegenstander aan). Twee spelers besturen elk een robot op een raster door
commando's te typen. Wie het gebouw van de ander kapotschiet, wint. De snelste
overwinning staat bovenaan het scorebord.

Je speelt tegen een andere mens (online) of tegen de computer ("Robo").

## 2. Techniek

- **Backend:** Python 3.12+, FastAPI, uvicorn (met `websockets`), Jinja2-templates.
  Pakketbeheer uitsluitend met **uv** (`pyproject.toml`, `uv add`, `uv run`);
  geen pip, geen handmatige venv, geen requirements.txt.
- **Frontend:** HTML5, HTMX + de HTMX WebSocket-extensie (`ws`). Geen eigen
  JavaScript, geen Node.js, geen bundler. HTMX-bestanden staan lokaal in `static/`.
- **Opslag:** SQLite (alleen voor het scorebord). Lopende spellen staan in het
  geheugen van de server.
- **Realtime:** één WebSocket per spelpagina. Server stuurt HTML-fragmenten,
  HTMX vervangt ze out-of-band op `id`.
- **Hosting:** achter Caddy. WebSockets werken zonder extra configuratie:

  ```
  robotwars.example.nl {
      reverse_proxy localhost:8000
  }
  ```

## 3. Speelveld en spelregels

### Het veld

13 kolommen × 7 rijen. Coördinaten zijn `(x, y)`, beide beginnend bij 1, en
staan langs de rand van het veld. Het veld is bewust een **wiskundig
assenstelsel**, zoals kinderen dat op school leren: x loopt naar rechts vanaf
je eigen kant, y loopt omhoog en de oorsprong ligt linksonder. Rij (y) 1 is dus
de onderste rij, rij 7 de bovenste. Kolom 7 is de rivier; op y=2 en y=6 ligt
een brug.

```
  7  .  .  .  .  .  .  ~  .  .  .  .  .  .
  6  .  .  .  .  .  .  =  .  .  .  .  .  .   brug
  5  .  .  .  .  .  .  ~  .  .  .  .  .  .
  4  B  R  .  .  .  .  ~  .  .  .  .  R  B   gebouwen + startvakken
  3  .  .  .  .  .  .  ~  .  .  .  .  .  .
  2  .  .  .  .  .  .  =  .  .  .  .  .  .   brug
  1  .  .  .  .  .  .  ~  .  .  .  .  .  .
     1  2  3  4  5  6  7  8  9 10 11 12 13
```

- Speler 1 (blauw): helft = kolom 1–6, gebouw op (1,4), robot start op (2,4).
- Speler 2 (rood): helft = kolom 8–13, gebouw op (13,4), robot start op (12,4).
- `vooruit` is voor speler 1 kolom +1, voor speler 2 kolom −1: altijd richting
  de tegenstander. `achteruit` is het omgekeerde. `omhoog` = y + 1,
  `omlaag` = y − 1.
- Op het scherm staan de y-nummers links (7 boven, 1 onder) en de x-nummers
  onder het veld, met de lege hoek linksonder als oorsprong.
- Speler 2 ziet het veld gespiegeld, zodat "vooruit" op het scherm altijd naar
  rechts is en de eigen kant links staat.
- **Iedere speler telt de kolommen vanaf zijn eigen kant**: links staat 1 (bij
  je eigen toren), rechts 13. Je eigen helft is dus voor allebei kolom 1–6 en
  `schild = (4, 2)` betekent voor allebei hetzelfde. Intern rekent het spel in
  echte veldcoördinaten; voor speler 2 worden getypte kolommen en getoonde
  coördinaten gespiegeld (`eigen_kolom`).

### Bewegen

Een stap mislukt (robot blijft staan, programma gaat door) als het doelvak:
buiten het veld ligt, water is (rivier zonder brug), een schild bevat, een
gebouw bevat, of de andere robot bevat.

### Schieten

`robot = schiet` vuurt vooruit. De kogel legt maximaal 4 vakjes af, vliegt over
water en bruggen heen, en raakt het eerste voorwerp dat hij tegenkomt: schild,
robot of gebouw. Dat voorwerp krijgt 1 schade. Niets geraakt binnen 4 vakjes:
kogel verdwijnt. In de tik van het schot vliegt de kogel zichtbaar vakje voor
vakje (0,18 s per vakje) van de robot naar het eindpunt: elk vakje flitst als
de kogel erlangs komt, bij een treffer verschijnt de 💥 pas bij aankomst, bij
een misser dooft de kogel aan het eind uit. Schoten van beide spelers zijn voor
beide spelers zichtbaar.

### Levens

- Gebouw: 5 levens. Op 0 is het spel afgelopen.
- Robot: 5 hartjes. Op 0 verdwijnt hij van het veld, zijn wachtrij wordt
  geleegd, en na 3 tikken staat hij weer op zijn startvak met 5 hartjes.
  Is het startvak bezet (andere robot), dan wacht hij tot het vrij is.

### Schilden

`schild = (x, y)` zet een schild neer. Voorwaarden:
- op de eigen helft (speler 1: kolom 1–6, speler 2: kolom 8–13);
- op een leeg vak (geen robot, gebouw, schild) en niet op een startvak
  ((2,4) of (12,4)), anders kan een robot nooit meer terugkomen;
- de speler heeft nog schilden over (3 per potje).

Een schild verdwijnt na 8 treffers. Voldoet het commando niet aan de
voorwaarden, dan zie je een foutmelding en gebeurt er niets (het commando telt
niet als gebruikt schild).

### Bommen

`bom = (dx, dy)` legt een bom op een buurvak van de robot: dx en dy zijn elk
−1, 0 of 1, met dx = 1 "vooruit" (richting tegenstander) en dy = 1 omhoog.
Elke speler heeft er 3 per potje. Staat er een robot (ook jijzelf bij
`(0, 0)`), dan is die meteen kapot. Ligt er al een mijn, dan knallen beide en
raakt niemand gewond. Anders blijft de bom liggen als **mijn**, zichtbaar voor
allebei: een robot die erop stapt (van wie ook) is meteen kapot. Kogels
vliegen over mijnen heen. Niet toegestaan (foutmelding, bom niet verbruikt):
buiten het veld, water, gebouw, schild, leeg startvak. Robo legt geen bommen
en loopt om mijnen heen. Volledig ontwerp: `2026-09-20-bom-design.md`.

### Winnen

Het gebouw van de tegenstander op 0 → jij wint. De tijd = seconden vanaf de
start van het potje tot en met de winnende treffer.

### Uiterlijk van het gebouw

Gekozen ontwerp: **Ruimtetoren** (SVG-sprite, in teamkleur): metalen romp,
glazen koepel met pulserende energiekern, drie lichtringen, antenne met
knipperend baken. De schade is aan het gebouw zelf te zien:

| Levens | Uiterlijk |
|---|---|
| 5 | alles aan |
| 4 | baken uit, kleine barst |
| 3 | bovenste lichtring uit, meer barsten |
| 2 | middelste ring uit, rook |
| 1 | onderste ring uit, vuur |
| 0 | ingestort: alleen puin, vlammen en rook |

Bij elke treffer schudt het gebouw kort en flitst het.

### Uiterlijk van robot, schild en kogel

- **Robot:** gekozen ontwerp **Bolbot** (SVG-sprite in teamkleur): zwevende
  bolrobot met één groot oog, straalmotor eronder (zweefanimatie), blaster
  aan de voorkant, antenne met knipperlicht. De robot kijkt altijd "vooruit";
  de tegenstander wordt gespiegeld (`scaleX(-1)`).
- **Schild:** zeshoek van energie in teamkleur met een lopende glans. Vanaf 4
  treffers één barst, vanaf 6 treffers meerdere barsten, na 8 treffers weg.
- **Kogel:** gloeiende energiebol met een staart; de vakjes die hij passeert
  lichten één tik geel op.

Alle sprites zijn inline SVG-`<symbol>`s in één bestand (`static/sprites.svg`
of in de template), hergebruikt via `<use>`, met de teamkleur als CSS-variabele
`--kleur`. Mockups staan in `.superpowers/brainstorm/` (niet in git).

## 4. De taal

Eén commando per regel. Hoofdletters/kleine letters maken niet uit; spaties
rondom `=`, `(`, `,` en `)` zijn vrij.

```
robot = vooruit
robot = achteruit
robot = omhoog
robot = omlaag
robot = schiet
schild = (4, 2)
bom = (1, 0)
herhaal 3 keer
  robot = vooruit
  robot = schiet
klaar
```

- `herhaal N keer` … `klaar`: N is 1 t/m 20. Nesten mag. Inspringen is niet
  verplicht.
- Lege regels worden overgeslagen.

### Parser (`app/parser.py`)

Pure Python, geen afhankelijkheden. Twee functies:

- `parse_line(text) -> ParseResult` — geeft één van:
  - `Command(...)`: een geldig, compleet commando (`Move(richting)`, `Shoot()`,
    `Shield(x, y)`, `Bomb(dx, dy)`, `RepeatStart(n)`, `RepeatEnd()`);
  - `Incomplete`: nog geen commando, maar het kan er nog één worden
    (`robot = vo`);
  - `Invalid(hint)`: dit kan geen commando meer worden (`robot = links`),
    met een kindvriendelijke Nederlandse hint.
- `expand(commands) -> list[Step]` — rolt `herhaal`-blokken uit tot een platte
  lijst stappen (`Move`, `Shoot`, `Shield`, `Bomb`).

Foutmeldingen (hints) zijn in het Nederlands, bijvoorbeeld:
- `Ik ken "links" niet. Probeer vooruit, achteruit, omhoog, omlaag of schiet.`
- `Schild heeft twee getallen nodig: schild = (x, y), bijvoorbeeld schild = (4, 2).`
- `Bom heeft twee getallen van -1 tot 1 nodig: bom = (dx, dy), bijvoorbeeld bom = (1, 0) voor het vak vóór je.`
- `Herhaal hoeveel keer? Bijvoorbeeld herhaal 3 keer (maximaal 20).`

## 5. Het typen (de editor)

Werkt zoals CT-3000: geen Start-knop, geen Enter.

- Je typt op de **onderste regel**. Elke toetsaanslag gaat naar de server.
- Zodra de regel een geldig commando is, wordt het **direct uitgevoerd**: de
  regel bevriest (grijs, `✓` ervoor) en er verschijnt een nieuwe lege regel
  met de cursor erin.
- Markering aan het begin van de regel:
  - *niets* — nog bezig, kan nog goed komen (`Incomplete`);
  - rood `!` + hint — kan geen commando meer worden (`Invalid`);
  - geel `…` — binnen een `herhaal`-blok, wachtend op `klaar`;
  - groen `✓` — uitgevoerd.
- `herhaal N keer` opent een blok. De regels erna worden verzameld (`…`)
  totdat `klaar` komt; dan wordt het blok uitgerold en in één keer in de
  wachtrij gezet. Een `Invalid`-regel binnen een blok wordt gemarkeerd en
  overgeslagen, het blok blijft open.
- Uitgevoerde commando's komen in de **wachtrij** van de robot; de robot doet
  er elke tik (1 seconde) één. Maximaal 50 stappen in de rij; daarboven wordt
  het commando geweigerd met de melding "Wacht even, je robot is nog bezig".
- Knoppen: **Stop** (leegt de wachtrij), **Wis** (leegt de lijst met bevroren
  regels; heeft geen effect op het spel).

### Techniek

- De invoerregel is een `<input>` met `hx-trigger="input changed delay:50ms"`
  en `ws-send`; het bericht bevat `{"regel": "<tekst>"}`.
- De server antwoordt met OOB-fragmenten: de markering, eventueel de bevroren
  regel (toegevoegd aan de lijst) en een nieuwe lege `<input autofocus>`.
  HTMX focust het `autofocus`-element na de swap, dus er is geen eigen
  JavaScript nodig.

## 6. Online spelen, lobby en verbinding

### Startpagina (`/`)

Naam invullen (1–20 tekens) en kiezen: **Speel tegen iemand** of **Speel
tegen de computer**. De naam en een willekeurig speler-token komen in een
cookie. Link naar het scorebord.

### Wachtkamer (`/wachten`)

Eén wachtrij op de server. Staat er al iemand, dan worden beiden gekoppeld en
gaan ze naar `/spel/{id}`. De wachtkamer pollt elke seconde `GET /wachten/status`
(`hx-get`, `hx-trigger="every 1s"`); bij een match antwoordt de server met een
`HX-Redirect`-header. Dit is het enige stukje polling. Knop: **Toch tegen de
computer**.

### Terugkomen

Kom je op `/` terwijl je cookie hoort bij een lopend spel, dan word je meteen
doorgestuurd naar dat spel. Refresh, tabblad sluiten en heropenen: alles komt
terug in hetzelfde potje. Het spel loopt intussen door.

### Weg zijn

Is een menselijke speler 60 seconden zonder open WebSocket, dan ziet de ander
"*naam* is weg" en wint hij het potje. Zo'n overwinning komt **niet** op het
scorebord.

De weggevallen speler mag niet in het duister tasten. Daarom:

- Bij het einde van elk spel bewaart de lobby de uitslag bij de sessie van
  beide spelers (`Sessie.laatste_uitslag`: tegenstander, gewonnen of niet,
  weggevallen of niet, tijd). Wie daarna op de startpagina komt, ziet boven het
  naamformulier een balk: "🏆 Je vorige potje tegen Wessel heb je gewonnen in
  1:23! Wessel was weg." of "📴 Je verbinding viel weg. Wessel heeft daardoor
  gewonnen (na 1:00). Dit potje telt niet voor het scorebord." Ook als het spel
  al opgeruimd is en `/spel/{id}` naar `/` doorstuurt, staat de uitslag daar
  dus nog. Een nieuw potje wist hem.
- Een spelpagina die na verbindingsverlies opnieuw verbindt met een spel dat
  al afgelopen is, krijgt meteen het eindscherm (de overlay) toegestuurd en
  daarna gaat de socket netjes dicht. De overlay legt vanuit de kijker uit wat
  er gebeurde: "Je verbinding viel weg; daardoor heeft Wessel gewonnen" voor
  de verliezer, "Martijn is weg" voor de winnaar.

### Spelpagina (`/spel/{id}`)

- Bovenaan: "Wessel (jij) tegen Papa" en de lopende tijd.
- Het veld (gespiegeld voor speler 2).
- Status: hartjes van beide robots, levens van beide gebouwen, schilden over,
  bommen over.
- Log "Wat gebeurt er?" onder de editor: de laatste 10 gebeurtenissen (lopen,
  geblokkeerd, treffers met resterende hartjes, mis, kapot, terug, schild,
  bom, mijn,
  winst), nieuwste bovenaan, met tijd, en verteld vanuit de kijker ("Jij
  schiet → raakt Robo! ❤️❤️❤️❤️🖤"). De spelmotor houdt daarvoor `Game.log`
  bij (laatste 30 gebeurtenissen).
- Sneuvelen: op het geraakte vak verschijnt kort een 💥-explosie, de kogelbaan
  flitst, en het log meldt "💥 Je robot is kapot! Hij komt terug over 3
  seconden" en later "Je robot is terug op het startvak". Geen aparte
  pop-up over het veld (bewust weggehaald: het log is genoeg).
- Knop **Stop spel** (rechts onder de editor): geeft op, de ander wint (telt
  niet voor het scorebord) en je gaat terug naar de startpagina, waar de
  uitslag staat. De tegenstander ziet "<naam> is gestopt".
- Stappenteller naast Stop en Wis: "Nog 4 stappen te gaan" of "Je robot wacht
  op een commando", zodat je ziet dat je stappen echt gepland staan.
- Onder het veld: de editor (hoofdstuk 5). Op brede schermen (vanaf 1180px)
  staat de editor rechts naast het veld en blijft hij in beeld (sticky); de
  lijst met bevroren regels scrolt binnen een vast vak, nieuwste onderaan. Zo
  scrolt het veld nooit uit beeld terwijl je typt.
- Bij einde: overlay "Wessel wint in 1:23!" met **Nog een keer** (terug naar
  `/`, naam onthouden) en **Scorebord**.
- WebSocket: `ws-connect="/ws/spel/{id}"`. De server stuurt na elke tik de
  bijgewerkte fragmenten (`#kop`, `#veld`, `#status`, `#log`,
  `#teller`, `#hint`) en na elke editor-actie de editor-fragmenten (`#regels`,
  `#markering`, `#hint`, `#teller`, eventueel `#invoer`).

### Onder de motorkap

- `lobby.py`: wachtrij, koppelen, cookie-token → (spel, speler-slot).
- Alle lopende spellen in één dict `games: dict[str, Game]`.
- Eén `asyncio`-taak tikt elke seconde: voor elk lopend spel `game.tick()`
  en daarna fragmenten naar alle open WebSockets van dat spel.
- Per speler-slot: naam, token, wachtrij, `herhaal`-stapel (open blokken),
  bevroren regels, lijst met open WebSockets. Twee tabbladen van dezelfde
  speler zien en typen allebei.
- Afgelopen spellen worden 5 minuten na het einde uit de dict gehaald.

### Uiterlijk van de schermen

Donker thema (achtergrond `#1a1d2b`, panelen `#2a2f45`), teamkleuren blauw
`#4aa8ff` en rood `#ff5f5f`, accent geel `#ffd23f`. Alle schermen delen één
`style.css`.

- **Startpagina:** logo "ROBOT WARS" (blauw/rood), blauwe en rode bolbot met
  "VS", veld "Hoe heet je?", grote knoppen **Speel tegen iemand** (blauw) en
  **Speel tegen de computer** (rood), link naar scorebord.
- **Wachtkamer:** zwevende bolbot, "Wachten op een tegenstander", stuiterende
  puntjes, wachttijd, knop **Toch tegen de computer**.
- **Spelpagina:** kop "Wessel (jij) tegen Papa" + tijd; veld van 13×7 met
  coördinaten langs de rand, blauwe/rode helften, rivier en bruggen; statuskaart
  per speler (bolbot, hartjes robot, hartjes toren, schilden over); editor met
  bevroren regels, markeringen, hint, knoppen Stop en Wis.
- **Winnaarsscherm:** overlay met gouden kader over het vervaagde veld: 🏆,
  "<naam> wint!", tijd groot in geel, eigen bolbot naast de ingestorte toren,
  knoppen **Nog een keer** en **Scorebord**.
- **Scorebord:** twee tabbladen (tegen de computer / tegen een mens), top-10
  met goud/zilver/brons-nummers, tijd in geel, "tegen <naam> · <datum>",
  eigen scores blauw omlijnd, link terug naar start.

## 7. De computerspeler (Robo, `app/ai.py`)

- Robo speelt als speler 2 en heeft geen WebSocket; verder gelden dezelfde
  regels (wachtrij, respawn, schilden).
- **Tempo:** Robo doet niets uit zichzelf. Telkens als de robot van de mens in
  een tik daadwerkelijk een stap uitvoert (niet bij het inplannen), krijgt Robo
  één stap **tegoed**. Elke tik waarin Robo tegoed heeft, kiest hij op dat
  moment één stap (op basis van het actuele veld), voert die uit en verbruikt
  één tegoed; omdat speler 1 eerst aan de beurt is, verwerkt Robo het tegoed in
  dezelfde tik. Typt de mens niets, dan staat Robo stil. Drukt de mens op Stop
  of sneuvelt zijn robot (wachtrij gewist), dan stopt Robo dus ook.
- **Keuze per stap**, eerste regel die past:
  1. Staat de vijandelijke robot vóór Robo in dezelfde rij, binnen 4 vakjes,
     zonder schild ertussen? → `schiet`.
  2. Staat het vijandelijke gebouw vóór Robo binnen 4 vakjes, zonder schild
     ertussen? → `schiet`.
  3. Is de vijandelijke robot op Robo's helft, heeft Robo nog schilden, en is
     het vak (11,4) leeg? → `schild = (11, 4)` (vóór zijn startvak, dus de
     kogel raakt het schild voordat hij het gebouw raakt).
  4. Anders lopen: naar de y van de dichtstbijzijnde brug (2 of 6; bij gelijke
     afstand de onderste, y=2), vooruit tot over de brug, dan naar y=4, dan
     vooruit tot binnen 4 vakjes van het vijandelijke gebouw. Is de volgende
     stap geblokkeerd, dan wordt de andere brug het doel.
- Doordat Robo per tik kiest (niet vooruit plant), reageert hij op de actuele
  situatie.

## 8. Scorebord en opslag (`app/db.py`)

SQLite-bestand `robotwars.db` in de projectmap. Tabel:

```
scores(id INTEGER PRIMARY KEY,
       winnaar TEXT, verliezer TEXT,
       tegen_computer INTEGER,   -- 0/1
       seconden INTEGER,
       gespeeld_op TEXT)         -- ISO-8601
```

Alleen echte overwinningen (gebouw op 0) worden opgeslagen. Alleen overwinningen
van menselijke spelers worden opgeslagen. Pagina
`/scorebord` toont twee lijsten: **Tegen de computer** en **Tegen een mens**,
elk de 10 snelste, snelste bovenaan, als
"1. Wessel – 1:23 – tegen Robo – 20 sep".

## 9. Projectstructuur

```
robotwars/
  app/
    main.py        FastAPI: routes, WebSocket, tik-taak
    parser.py      taal → commando's/stappen
    game.py        spelregels (veld, lopen, schieten, schilden, bommen, respawn, winnen)
    ai.py          Robo
    lobby.py       wachtrij, koppelen, cookie → speler
    db.py          SQLite scorebord
    templates/     start.html, wachten.html, spel.html, scorebord.html,
                   fragments/veld.html, status.html, editor.html
    static/        style.css, htmx.min.js, ws.js
  tests/
    test_parser.py, test_game.py, test_ai.py, test_lobby.py
  docs/superpowers/specs/   dit ontwerp + sprites.svg
  pyproject.toml            uv-project: fastapi, uvicorn[standard], jinja2,
                            python-multipart; dev: pytest, httpx
  Caddyfile
  README.md
```

## 10. Testen

- `parser.py`, `game.py`, `ai.py` zijn pure Python en worden met pytest getest,
  onder andere: `herhaal 3 keer` geeft 3 stappen; `robot = vo` is Incomplete
  en `robot = links` Invalid; kogel stopt bij schild; robot loopt niet het water
  in; schild alleen op eigen helft; respawn na 3 tikken; winst bij gebouw 0;
  Robo schiet als de vijand in zijn rij staat.
- Lobby en WebSocket: FastAPI `TestClient` (koppelen van twee spelers, redirect
  bij terugkomen, ongeldig WS-bericht wordt genegeerd).
- Het speelveld zelf wordt handmatig in de browser bekeken.

## 11. Fouten en randgevallen

- Server herstart: lopende spellen zijn weg; scores blijven.
- Onbekende of kapotte WebSocket-berichten worden genegeerd.
- Twee tabbladen van dezelfde speler: beide werken.
- Naam leeg of te lang: formulier toont foutmelding, geen cookie.
- Beide gebouwen kunnen niet in dezelfde tik op 0 komen: per tik verwerkt de
  server eerst speler 1, dan speler 2; wie eerst het gebouw op 0 krijgt, wint.

## 12. Niet in deze versie

Moeilijkheidsgraden voor Robo, geluid, meer dan twee spelers, chat, kaarten of
troepen zoals in Clash Royale, `als … dan …` uit CT-3000. Eerst dit werkend
krijgen.
