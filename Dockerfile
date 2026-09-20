FROM python:3.12-slim

# uv (alleen uv, geen pip) — zie README; vaste versie, geen :latest
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /usr/local/bin/uv

WORKDIR /app

# Eerst alleen de afhankelijkheden, voor laag-caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app/ ./app/

# De SQLite-database van het scorebord staat in een volume (zie docker-compose.production.yml).
# Het proces draait als de systeemgebruiker "app" (uid 10001) zonder shell; /data is van hem,
# zodat Docker een nieuw named volume met die eigenaar aanmaakt.
ENV ROBOTWARS_DB=/data/robotwars.db
RUN useradd -u 10001 -r -s /usr/sbin/nologin app && mkdir -p /data && chown app /data
USER app

EXPOSE 8000

# Precies één worker: lopende spellen en sessies leven in het geheugen van het proces.
# --proxy-headers: achter Caddy komen X-Forwarded-Proto/For mee (Secure-cookie, echte IP).
# --ws-max-size: geen WebSocket-frames groter dan 4 KB. --no-access-log: Caddy logt al.
# Rechtstreeks uvicorn uit de venv, geen uv bij runtime.
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*", \
     "--ws-max-size", "4096", "--no-access-log"]
