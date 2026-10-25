#!/bin/sh
# Download the Geofabrik Vietnam extract (MD5-verified) and clip it to the
# Northern Vietnam bbox used by both OSRM profiles.
#
# Runs inside the `osm-fetch` compose service; /data is the `osm_data` volume.
# Idempotent: the download and the clip are skipped when their outputs already
# exist and match. Set FORCE=1 to redo both.
set -eu

: "${OSM_SOURCE_URL:?OSM_SOURCE_URL is required}"
: "${OSM_CLIP_BBOX:?OSM_CLIP_BBOX is required}"
FORCE="${FORCE:-0}"

SRC=/data/source.osm.pbf
REGION=/data/region.osm.pbf
META=/data/region.meta

log() { echo "[osm-fetch] $*"; }

# --- 1. Download (skipped if a verified copy exists) --------------------------
if [ -f "$SRC" ] && [ -f "$SRC.md5" ] && [ "$FORCE" != "1" ]; then
    expected=$(cut -d' ' -f1 "$SRC.md5")
    actual=$(md5sum "$SRC" | cut -d' ' -f1)
    if [ "$expected" != "$actual" ]; then
        log "existing source fails MD5 check (expected=$expected actual=$actual); rerun with FORCE=1"
        exit 1
    fi
    log "source already present and MD5-verified, skipping download ($SRC)"
else
    log "downloading $OSM_SOURCE_URL"
    curl -fL --retry 3 --retry-delay 5 -o "$SRC.part" "$OSM_SOURCE_URL"
    curl -fsSL -o "$SRC.md5.part" "$OSM_SOURCE_URL.md5"
    expected=$(cut -d' ' -f1 "$SRC.md5.part")
    actual=$(md5sum "$SRC.part" | cut -d' ' -f1)
    if [ "$expected" != "$actual" ]; then
        log "MD5 mismatch: expected=$expected actual=$actual"
        rm -f "$SRC.part" "$SRC.md5.part"
        exit 1
    fi
    mv "$SRC.part" "$SRC"
    mv "$SRC.md5.part" "$SRC.md5"
    log "download verified (md5=$actual)"
fi

src_md5=$(cut -d' ' -f1 "$SRC.md5")
src_ts=$(osmium fileinfo -g header.option.osmosis_replication_timestamp "$SRC" || echo unknown)
key="source_md5=$src_md5 bbox=$OSM_CLIP_BBOX"

# --- 2. Clip (skipped if the existing clip was made from the same inputs) -----
if [ -f "$REGION" ] && [ -f "$META" ] && grep -qxF "key: $key" "$META" \
    && grep -qxF "region_md5: $(md5sum "$REGION" | cut -d' ' -f1)" "$META" && [ "$FORCE" != "1" ]; then
    log "region clip up to date and MD5-verified, skipping ($REGION)"
else
    log "clipping bbox=$OSM_CLIP_BBOX"
    osmium extract --bbox "$OSM_CLIP_BBOX" --strategy complete_ways \
        --overwrite -o "$REGION" "$SRC"
    region_md5=$(md5sum "$REGION" | cut -d' ' -f1)
    {
        echo "key: $key"
        echo "source_url: $OSM_SOURCE_URL"
        echo "source_md5: $src_md5"
        echo "source_replication_timestamp: $src_ts"
        echo "bbox: $OSM_CLIP_BBOX"
        echo "region_md5: $region_md5"
        echo "region_bytes: $(wc -c < "$REGION")"
        echo "clipped_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } > "$META"
fi

log "done"
cat "$META"
