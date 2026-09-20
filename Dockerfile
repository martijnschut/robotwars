FROM python:3.12-slim

# uv (alleen uv, geen pip) — zie README
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Eerst alleen de afhankelijkheden, voor laag-caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app/ ./app/

# De SQLite-database van het scorebord staat in een volume (zie docker-compose.production.yml)
ENV ROBOTWARS_DB=/data/robotwars.db
RUN mkdir -p /data

EXPOSE 8000

# Precies één worker: lopende spellen en sessies leven in het geheugen van het proces.
# --proxy-headers: achter Caddy komen X-Forwarded-Proto/For mee (Secure-cookie, echte IP).
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
