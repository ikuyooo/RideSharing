#!/bin/sh
# Export pre-2025 (historic) commune-level boundaries from the verified P0
# Geofabrik download, as GEOMETRY EVIDENCE for Revision 9 place names whose
# historic unit was split by the 2025 reform (GEO-01 Đông Anh, A2 La Phù /
# An Khánh, A3 Gia Lâm / Mỹ Đình). Evidence only: the pipeline never repairs,
# closes or redraws these rings.
#   historic_areas.geojsonseq   : boundary=historic relations (admin_level 8)
#                                 that osmium can assemble into areas
#   historic_relations.opl      : the same relations as OPL (tags + member list),
#                                 including those whose rings cannot be assembled
#   historic_member_ways.geojsonseq : member ways as lines (gap diagnostics)
#   MANIFEST_HISTORIC           : source md5, osmium version, output md5s
# Kept apart from MANIFEST so that earlier candidate versions (which hash
# MANIFEST) stay reproducible.
#
# Usage: docker compose --profile osrm-prep run --rm --no-deps --entrypoint sh \
#          osm-fetch /scripts/export_historic_boundaries.sh
set -eu

SOURCE=/data/source.osm.pbf
OUT=/data/service_area
TMP=$(mktemp -d)
mkdir -p "$OUT"

log() { echo "[historic-export] $*"; }

[ -f "$SOURCE" ] || { log "missing $SOURCE (run osm-fetch first)"; exit 1; }
expected=$(cut -d' ' -f1 "$SOURCE.md5")
actual=$(md5sum "$SOURCE" | cut -d' ' -f1)
[ "$expected" = "$actual" ] || { log "source MD5 mismatch ($actual != $expected)"; exit 1; }

log "filtering boundary=historic relations (admin_level 8)"
osmium tags-filter -O -o "$TMP/hist.osm.pbf" "$SOURCE" r/boundary=historic
osmium tags-filter -O -o "$TMP/hist8.osm.pbf" "$TMP/hist.osm.pbf" r/admin_level=8
osmium export -O -f geojsonseq --geometry-types=polygon -a type,id \
    -o "$OUT/historic_areas.geojsonseq" "$TMP/hist8.osm.pbf"
osmium cat -O -f opl -t relation -o "$OUT/historic_relations.opl" "$TMP/hist8.osm.pbf"
osmium export -O -f geojsonseq --geometry-types=linestring -a type,id \
    -o "$OUT/historic_member_ways.geojsonseq" "$TMP/hist8.osm.pbf"

{
    echo "boundary_input: source.osm.pbf"
    echo "source_md5: $actual"
    grep -E '^source_replication_timestamp:' /data/region.meta
    echo "osmium_version: $(osmium --version | head -1)"
    echo "historic_areas_md5: $(md5sum "$OUT/historic_areas.geojsonseq" | cut -d' ' -f1)"
    echo "historic_areas_features: $(wc -l < "$OUT/historic_areas.geojsonseq")"
    echo "historic_relations_md5: $(md5sum "$OUT/historic_relations.opl" | cut -d' ' -f1)"
    echo "historic_relations: $(wc -l < "$OUT/historic_relations.opl")"
    echo "historic_member_ways_md5: $(md5sum "$OUT/historic_member_ways.geojsonseq" | cut -d' ' -f1)"
} > "$OUT/MANIFEST_HISTORIC"
rm -rf "$TMP"
log "done"
cat "$OUT/MANIFEST_HISTORIC"
