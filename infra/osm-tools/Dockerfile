# Minimal toolbox for fetching and clipping the OpenStreetMap extract.
# osmium-tool comes from the official Debian archive (no third-party images).
FROM debian:12.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends osmium-tool curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /data
