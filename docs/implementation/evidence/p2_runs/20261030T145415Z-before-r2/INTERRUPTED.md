# Run 20261030T145415Z-before-r2 - INTERRUPTED

Stopped by the operator on 2026-10-30 before it finished (no manifest, no result.json; exit code
unknown). Reason: run before-r1 showed unusually high variance (1000x0 PostGIS p95 339 ms vs 59 ms
the day before) while the docker stats sampler ran back-to-back without pause (826 samples in ~5 min).
Suspected measurement interference; the sampler was changed to one sample every 10 s and the
baseline was repeated. This folder is kept as history, not as a result.
