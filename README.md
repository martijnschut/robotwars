# Robot Wars

Een programmeerspel voor kinderen van 8–12 jaar, gemaakt door Martijn en Wessel.
Je bestuurt een robot door commando's te typen (zoals in CT-3000) en probeert de
toren van de tegenstander kapot te schieten (zoals in Clash Royale).

## Spelen

```
robot = vooruit      robot = achteruit
robot = omhoog       robot = omlaag
robot = schiet       (schiet 4 vakjes vooruit)
schild = (4, 2)      (kolom, rij; 3 per potje, alleen op je eigen helft)
herhaal 3 keer
  robot = vooruit
klaar
```

De kolommen tel je vanaf jouw eigen kant: 1 staat bij jouw toren, 13 bij die
van de ander; de rijen lopen van boven (1) naar beneden (7).

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

## Online zetten achter Caddy

```
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Met de meegeleverde `Caddyfile` (pas de domeinnaam aan) regelt Caddy HTTPS en de
WebSocket-verbinding automatisch: `caddy run`.

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
- `app/game.py` – de spelregels (veld, lopen, schieten, schilden, winnen)
- `app/ai.py` – Robo, de computerspeler
- `app/editor.py` – de editor: regels bevriezen, herhaal-blokken, hints
- `app/lobby.py` – wie speelt tegen wie
- `app/weergave.py` – veldmatrix en filters voor de templates
- `app/db.py` – scorebord in SQLite
- `app/main.py` – de webserver (FastAPI + HTMX over een WebSocket)

Het ontwerp staat in `docs/superpowers/specs/2026-09-20-robotwars-design.md`.

## Licentie

MIT, zie `LICENSE`. De sprites en het idee zijn geïnspireerd door [CT-3000](https://github.com/Q42/CT-3000) (ook MIT).
