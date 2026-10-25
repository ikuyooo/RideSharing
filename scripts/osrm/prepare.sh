#!/bin/sh
# Build an OSRM Contraction-Hierarchies graph for one profile.
#
# Usage (inside the OSRM image): prepare.sh <profile.lua> <name>
#   /osm  : osm_data volume (read-only), must contain region.osm.pbf
#   /data : per-profile output volume (osrm_car_data / osrm_motorbike_data)
#
# Idempotent: skipped when /data/PREPARED.key matches the current region
# extract, profile file(s) and OSRM version. Set FORCE=1 to rebuild.
set -eu

PROFILE="${1:?profile path required}"
NAME="${2:?profile name required}"
FORCE="${FORCE:-0}"
THREADS="${OSRM_THREADS:-2}"
REGION=/osm/region.osm.pbf

log() { echo "[osrm-prep:$NAME] $*"; }

if [ ! -f "$REGION" ]; then
    log "missing $REGION - run the osm-fetch service first (see README)"
    exit 1
fi

osrm_version=$(osrm-routed --version)
region_md5=$(md5sum "$REGION" | cut -d' ' -f1)
# The motorbike profile builds on /opt/car.lua, so hash both.
profile_md5=$(cat "$PROFILE" /opt/car.lua | md5sum | cut -d' ' -f1)
key="osrm=$osrm_version region_md5=$region_md5 profile_md5=$profile_md5"

# Core CH artifacts osrm-routed needs; used when adopting a build made before
# the manifest existed.
CORE_FILES="hsgr fileIndex geometry properties ramIndex timestamp nbg_nodes ebg_nodes edges names"

artifacts_valid() {
    if [ -f /data/ARTIFACTS.md5 ]; then
        (cd /data && md5sum -c --quiet ARTIFACTS.md5) && return 0
        log "artifact checksum mismatch"
        return 1
    fi
    for ext in $CORE_FILES; do
        if [ ! -s "/data/region.osrm.$ext" ]; then
            log "missing or empty artifact region.osrm.$ext"
            return 1
        fi
    done
    log "no manifest yet; core artifacts present - recording manifest"
    (cd /data && md5sum region.osrm.* > ARTIFACTS.md5)
}

if [ -f /data/PREPARED.key ] && [ "$(cat /data/PREPARED.key)" = "$key" ] && [ "$FORCE" != "1" ]; then
    if artifacts_valid; then
        log "graph up to date and artifacts verified, skipping ($key)"
        exit 0
    fi
    log "stamp matches but artifacts are invalid - rebuilding"
fi

log "building graph ($key)"
rm -f /data/region.osrm* /data/PREPARED /data/PREPARED.key /data/ARTIFACTS.md5
cp "$REGION" /data/region.osm.pbf
start=$(date +%s)
osrm-extract -p "$PROFILE" -t "$THREADS" /data/region.osm.pbf
osrm-contract -t "$THREADS" /data/region.osrm
rm -f /data/region.osm.pbf
end=$(date +%s)

{
    echo "profile_name: $NAME"
    echo "profile_path: $PROFILE"
    echo "algorithm: CH"
    echo "osrm_version: $osrm_version"
    echo "region_md5: $region_md5"
    echo "profile_md5: $profile_md5"
    echo "build_seconds: $((end - start))"
    echo "built_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > /data/PREPARED
(cd /data && md5sum region.osrm.* > ARTIFACTS.md5)
echo "$key" > /data/PREPARED.key
log "done in $((end - start))s"
cat /data/PREPARED
