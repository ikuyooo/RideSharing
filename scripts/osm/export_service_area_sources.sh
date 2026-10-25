#!/bin/sh
# Export the OSM inputs of the service-area pipeline (owner decision P1-D1/P1-D3)
# from the verified P0 Geofabrik download (/data/source.osm.pbf, MD5-checked).
# The bbox clip (region.osm.pbf, built with --strategy complete_ways) does not
# keep administrative relations that cross the bbox complete, so provinces such
# as Hải Phòng and Ninh Bình cannot be assembled from it; the unclipped source
# can. Routing still uses region.osm.pbf.
#   admin_boundaries.geojsonseq : boundary=administrative relations, admin_level 4 and 6
#   places.geojsonseq           : place=* nodes and amenity=university (test locations)
#   MANIFEST                    : region md5, osmium version, output md5s
#
# Runs inside the osm-fetch image; /data is the osm_data volume.
# Usage: docker compose --profile osrm-prep run --rm --no-deps --entrypoint sh \
#          osm-fetch /scripts/export_service_area_sources.sh
set -eu

REGION=/data/region.osm.pbf
SOURCE=/data/source.osm.pbf
OUT=/data/service_area
TMP=$(mktemp -d)
mkdir -p "$OUT"

log() { echo "[service-area-export] $*"; }

[ -f "$SOURCE" ] || { log "missing $SOURCE (run osm-fetch first)"; exit 1; }
expected=$(cut -d' ' -f1 "$SOURCE.md5")
actual=$(md5sum "$SOURCE" | cut -d' ' -f1)
[ "$expected" = "$actual" ] || { log "source MD5 mismatch ($actual != $expected)"; exit 1; }

log "filtering administrative boundaries (admin_level 4 and 6)"
osmium tags-filter -O -o "$TMP/admin.osm.pbf" "$SOURCE" \
    r/boundary=administrative
osmium tags-filter -O -o "$TMP/admin46.osm.pbf" "$TMP/admin.osm.pbf" \
    r/admin_level=4,6
osmium export -O -f geojsonseq --geometry-types=polygon -a type,id \
    -o "$OUT/admin_boundaries.geojsonseq" "$TMP/admin46.osm.pbf"

log "exporting place nodes and universities"
osmium tags-filter -O -o "$TMP/places.osm.pbf" "$SOURCE" n/place nwr/amenity=university
osmium export -O -f geojsonseq -a type,id -o "$OUT/places.geojsonseq" "$TMP/places.osm.pbf"

{
    echo "boundary_input: source.osm.pbf"
    echo "routing_extract_md5: $(md5sum "$REGION" | cut -d' ' -f1)"
    # The bbox clip drops the replication header; the snapshot time is the
    # source extract's, recorded in region.meta when the clip was made (P0).
    grep -E '^(source_url|source_md5|source_replication_timestamp|bbox):' /data/region.meta
    echo "osmium_version: $(osmium --version | head -1)"
    echo "admin_boundaries_md5: $(md5sum "$OUT/admin_boundaries.geojsonseq" | cut -d' ' -f1)"
    echo "admin_boundaries_features: $(wc -l < "$OUT/admin_boundaries.geojsonseq")"
    echo "places_md5: $(md5sum "$OUT/places.geojsonseq" | cut -d' ' -f1)"
    echo "places_features: $(wc -l < "$OUT/places.geojsonseq")"
} > "$OUT/MANIFEST"
rm -rf "$TMP"
log "done"
cat "$OUT/MANIFEST"
