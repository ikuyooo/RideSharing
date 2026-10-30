# OSRM client overhead - micro-benchmark (2026-10-30, inside the compose network)

Backend container -> osrm-motorbike:5000, `/table` 16 sources x 2 destinations, 30 calls each,
idle stack, synthetic coordinates (seed 1). Command: inline Python in `docker compose exec backend`.

| Client | p50 | p95 |
|---|---|---|
| `httpx.get` (new Client per call - code before optimisation) | 20.6 ms | 29.2 ms |
| one shared `httpx.Client`, keep-alive disabled | 10.1 ms | 12.0 ms |
| `http.client`, new connection | 8.6 ms | 11.6 ms |

cProfile of 100 generation runs (run before-cprofile): `SSLContext.load_verify_locations` 200 calls,
1.54 s - httpx builds an SSL context (CA bundle) for every new Client even for plain http.
