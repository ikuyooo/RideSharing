#!/bin/sh
# Export realistic pickup / dropoff coordinates (GEO-D) from the verified P0
# Geofabrik download: OSM NODES where people actually start trips - bus stops,
# schools, universities, hospitals / clinics, markets, town halls, banks, post
# offices, fuel stations, and settlement place nodes. Used only to measure the
# tier-2 rejection rate (snap distance, road reach) - never to build geometry.
#   pickup_candidates.geojsonseq, MANIFEST_PICKUP
#
# Usage: docker compose --profile osrm-prep run --rm --no-deps --entrypoint sh \
#          osm-fetch /scripts/export_pickup_candidates.sh
set -eu

SOURCE=/data/source.osm.pbf
OUT=/data/service_area
TMP=$(mktemp -d)
mkdir -p "$OUT"

log() { echo "[pickup-export] $*"; }

expected=$(cut -d' ' -f1 "$SOURCE.md5")
actual=$(md5sum "$SOURCE" | cut -d' ' -f1)
[ "$expected" = "$actual" ] || { log "source MD5 mismatch ($actual != $expected)"; exit 1; }

log "filtering pickup candidate nodes"
osmium tags-filter -O -R -o "$TMP/pick.osm.pbf" "$SOURCE" \
    n/highway=bus_stop \
    n/amenity=school,university,college,hospital,clinic,marketplace,townhall,bank,post_office,fuel \
    n/place=city,town,suburb,quarter,neighbourhood,village,hamlet
osmium export -O -f geojsonseq --geometry-types=point -a type,id \
    -o "$OUT/pickup_candidates.geojsonseq" "$TMP/pick.osm.pbf"
{
    echo "source_md5: $actual"
    grep -E '^source_replication_timestamp:' /data/region.meta
    echo "osmium_version: $(osmium --version | head -1)"
    echo "pickup_candidates_md5: $(md5sum "$OUT/pickup_candidates.geojsonseq" | cut -d' ' -f1)"
    echo "pickup_candidates_features: $(wc -l < "$OUT/pickup_candidates.geojsonseq")"
} > "$OUT/MANIFEST_PICKUP"
rm -rf "$TMP"
log "done"
cat "$OUT/MANIFEST_PICKUP"
