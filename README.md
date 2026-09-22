# Robot Wars

Een programmeerspel voor kinderen van 8–12 jaar, gemaakt door Martijn en Wessel.
Je bestuurt een robot door commando's te typen (zoals in CT-3000) en probeert de
toren van de tegenstander kapot te schieten (zoals in Clash Royale).

Spelen: **https://robot.schut.me**

## Spelen

```
robot = vooruit      robot = achteruit
robot = omhoog       robot = omlaag
robot = schiet       (schiet 4 vakjes in de richting van je kanon)
kanon = 90           (stapjes van 45: 0 vooruit, 90 omhoog, 180 achteruit, 270 omlaag,
                      45/135/225/315 schuin ertussenin; blijft staan tot je hem verandert)
schild = (4, 2)      (x, y; 3 per potje, alleen op je eigen helft; kapot na 8 treffers)
bom = (1, 0)         (dx, dy van -1 tot 1 rondom je robot; 3 per potje; robot erop = kapot)
herhaal 3 keer
  robot = vooruit
klaar
```

De kolommen (x) tel je vanaf jouw eigen kant: 1 bij jouw toren, 13 bij die van
de ander; de rijen (y) tellen van onder (1) naar boven (7), net als in een
assenstelsel. `robot = omhoog` is dus y + 1.

Je hoeft niet op Enter te drukken: zodra een regel klopt, doet je robot hem.
Wie de toren van de ander op 0 schiet, wint. De snelste tijd staat bovenaan het
scorebord.

## Starten (alleen met uv)

```
uv sync
uv run uvicorn app.main:app --reload
```

Open http://localhost:8000. Voor twee spelers: open de pagina in twee
verschillende browsers (of een incognitovenster).

## Testen

```
uv run pytest -q
```

## Instellingen (omgevingsvariabelen)

- `ROBOTWARS_DB` – pad van het SQLite-bestand (standaard `robotwars.db`)
- `ROBOTWARS_TIK` – seconden per stap (standaard `1`; kleiner = sneller spel).
  Kanttekening: de tijd op het scorebord telt in tikken, dus alleen bij `1`
  klopt hij in seconden.

## Spelen op meerdere laptops thuis

```
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open op de andere laptop `http://<ip-van-deze-laptop>:8000` (zelfde wifi;
Windows Firewall moet poort 8000 toestaan).

## Online: robot.schut.me

De app draait op de VPS als Docker-container (`Dockerfile`,
`docker-compose.production.yml`) achter Caddy. Een push naar `main` wordt
automatisch uitgerold door de webhook-receiver uit de repo `schut-infra`
(`webhook-receiver/scripts/deploy-robotwars.sh`); het scorebord staat in het
volume `robotwars_data`. Details: `schut-infra/VPS_DEPLOYMENT.md`.

Zelf ergens anders draaien achter Caddy kan ook; zie de meegeleverde
`Caddyfile` (pas de domeinnaam aan): `caddy run`.

## Bekende beperkingen

- Zodra een regel klopt, vervangt de server de invoerregel door een lege. Wat je
  in die paar milliseconden nog typt, gaat verloren. Op een trage verbinding kan
  het helpen om na elke regel even te wachten op het ✓.
- Speel je in twee tabbladen tegelijk, dan zien beide het veld, maar alleen het
  tabblad waarin je typt toont je bevroren regels.
- Het scorebord is per server; er is geen account of wachtwoord — je naam is
  genoeg.

## Hoe het werkt

- `app/parser.py` – zet een getypte regel om in een commando
- `app/game.py` – de spelregels (veld, lopen, schieten, schilden, bommen, winnen)
- `app/ai.py` – Robo, de computerspeler
- `app/editor.py` – de editor: regels bevriezen, herhaal-blokken, hints
- `app/lobby.py` – wie speelt tegen wie
- `app/weergave.py` – veldmatrix en filters voor de templates
- `app/db.py` – scorebord in SQLite
- `app/main.py` – de webserver (FastAPI + HTMX over een WebSocket)

Het ontwerp staat in `docs/superpowers/specs/2026-09-20-robotwars-design.md`.

## Licentie

MIT, zie `LICENSE`. De sprites en het idee zijn geïnspireerd door [CT-3000](https://github.com/Q42/CT-3000) (ook MIT).
