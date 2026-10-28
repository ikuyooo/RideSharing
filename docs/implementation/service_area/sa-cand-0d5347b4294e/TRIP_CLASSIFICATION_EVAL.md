# Geographic edge cases on real data — `sa-cand-0d5347b4294e` (CANDIDATE)

Production classification (`app.modules.trip.rules.classify`) + OSRM car road distance (P1-D2). Buffer 15.0 km and limit 150.0 km from the baseline. Coordinates: OSM objects from the places export (`@type/@id` below; ways/relations use `ST_PointOnSurface`).

| Case | R9 § | Pickup (OSM) | Dropoff (OSM) | Road km | Expected | Actual | Branch | Result on candidate | Acceptance |
|---|---|---|---|---|---|---|---|---|---|
| Phenikaa → La Phù | 72.2 | way/973433275 Đại học Phenikaa | node/12147486706 La Phù | 5.9768 | URBAN | URBAN | 2b | **PASS** | NOT_VERIFIED (geometry not approved) |
| ~3 km inside TP Hưng Yên | 72.2 | node/13155709564 Phố Hiến | node/11518465547 Minh Khai | 2.589 | UNSUPPORTED_INTER_PROVINCE_ROUTE | UNSUPPORTED_INTER_PROVINCE_ROUTE | 3b | **PASS** | NOT_VERIFIED (geometry not approved) |
| buffer <= 15 km from Phenikaa | 2.3 | way/973433275 Đại học Phenikaa | node/12607118252 Vĩnh Thịnh | 14.9919 | URBAN | URBAN | 2b | **PASS** | NOT_VERIFIED (geometry not approved) |
| buffer > 15 km from Phenikaa | 2.3 | way/973433275 Đại học Phenikaa | node/12611713598 Yên Kiện | 15.321299999999999 | INTERCITY | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| limit <= 150 km from anchor | 2.3 / Baseline max_total_service_radius_km | node/74132064 Hà Nội | node/11578421390 Tứ Quận | 149.9839 | INTERCITY | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| limit > 150 km from anchor | 2.3 / Baseline max_total_service_radius_km | node/74132064 Hà Nội | node/6766268697  | 150.024 | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | 1 | **PASS** | NOT_VERIFIED (geometry not approved) |
| Đông Anh (town node) → Hoàn Kiếm | landmark (GEO closure) | node/13799910539 Đông Anh | node/13709921432 Hoàn Kiếm | — | URBAN | URBAN | 2a | **PASS** | NOT_VERIFIED (geometry not approved) |
| An Khánh (Splendora) → Hoàn Kiếm | landmark (GEO closure) | way/1565297218 Splendora Terrace Mailand | node/13709921432 Hoàn Kiếm | — | URBAN | URBAN | 2a | **PASS** | NOT_VERIFIED (geometry not approved) |
| La Phù → Hoàn Kiếm | landmark (GEO closure) | node/12147486706 La Phù | node/13709921432 Hoàn Kiếm | 17.1913 | INFO | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| Tùng Thiện (Xuân Khanh) → Hoàn Kiếm | landmark (GEO closure) | node/12629466848 Xuân Khanh | node/13709921432 Hoàn Kiếm | 47.377300000000005 | INTERCITY | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| Phố Hiến → Hoàn Kiếm | landmark (GEO closure) | node/13155709564 Phố Hiến | node/13709921432 Hoàn Kiếm | 56.3785 | INTERCITY | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| inside polygon, BEYOND_MAX_ROAD_DISTANCE (tier 2) | GEO-03 | node/13709921432 Hoàn Kiếm | sample point  | — | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | 1 | **PASS** | NOT_VERIFIED (geometry not approved) |
| inside polygon, NO_ROAD_ACCESS (tier 2) | GEO-03 | node/13709921432 Hoàn Kiếm | sample point  | — | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | 1 | **PASS** | NOT_VERIFIED (geometry not approved) |
| point in largest EXCLUDED component (tier 1) | GEO-04 | node/13709921432 Hoàn Kiếm | EXCLUDED component  | — | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | 1 | **PASS** | NOT_VERIFIED (geometry not approved) |
| point exactly on the TOTAL polygon boundary | GEO-C | node/13709921432 Hoàn Kiếm | boundary vertex  | — | INFO | OUT_OF_SERVICE_AREA | 1 | **PASS** | NOT_VERIFIED (geometry not approved) |

Tier-2 reasons (GEO-03): Phenikaa → La Phù: pickup None, dropoff None (anchor km 17.403, snap 37.5 m); ~3 km inside TP Hưng Yên: pickup None, dropoff None (anchor km 58.033, snap 1.9 m); buffer <= 15 km from Phenikaa: pickup None, dropoff None (anchor km 14.362, snap 1.1 m); buffer > 15 km from Phenikaa: pickup None, dropoff None (anchor km 14.294, snap 13.4 m); limit <= 150 km from anchor: pickup None, dropoff None (anchor km 149.984, snap 9.8 m); limit > 150 km from anchor: pickup None, dropoff BEYOND_MAX_ROAD_DISTANCE (anchor km 150.024, snap 32.7 m); Đông Anh (town node) → Hoàn Kiếm: pickup None, dropoff None (anchor km 0.724, snap 0.5 m); An Khánh (Splendora) → Hoàn Kiếm: pickup None, dropoff None (anchor km 0.724, snap 0.5 m); La Phù → Hoàn Kiếm: pickup None, dropoff None (anchor km 0.724, snap 0.5 m); Tùng Thiện (Xuân Khanh) → Hoàn Kiếm: pickup None, dropoff None (anchor km 0.724, snap 0.5 m); Phố Hiến → Hoàn Kiếm: pickup None, dropoff None (anchor km 0.724, snap 0.5 m); inside polygon, BEYOND_MAX_ROAD_DISTANCE (tier 2): pickup None, dropoff BEYOND_MAX_ROAD_DISTANCE (anchor km 256.43, snap 50.4 m); inside polygon, NO_ROAD_ACCESS (tier 2): pickup None, dropoff NO_ROAD_ACCESS (anchor km 177.321, snap 1576.6 m); point in largest EXCLUDED component (tier 1): pickup None, dropoff UNSERVICEABLE_COMPONENT (anchor km None, snap None m); point exactly on the TOTAL polygon boundary: pickup None, dropoff BEYOND_MAX_ROAD_DISTANCE (anchor km 205.38, snap 161.4 m)

Seeded sample of the accept-able polygon:

```json
{
  "sample": "400 points, ST_GeneratePoints seed 1 over TOTAL minus EXCLUDED",
  "by_outcome": {
    "BEYOND_MAX_ROAD_DISTANCE": 68,
    "NO_ROAD_ACCESS": 172,
    "SERVED": 160
  }
}
```

Ferry policy (GEO-E) — default route vs route with the version's OSRM exclusions:

| Destination | Default: km / ferry steps / ferry km | With policy: code / km / ferry steps | OK |
|---|---|---|---|
| component 2 | 214.708 / 0 / 0.0 | Ok / 214.708 / 0 | PASS |
| component 3 | 123.498 / 0 / 0.0 | Ok / 123.498 / 0 | PASS |
| component 4 | 197.094 / 0 / 0.0 | Ok / 197.094 / 0 | PASS |
| component 5 | 140.367 / 0 / 0.0 | Ok / 140.367 / 0 | PASS |
| component 6 | 146.414 / 0 / 0.0 | Ok / 146.414 / 0 | PASS |
| component 7 | 118.046 / 0 / 0.0 | Ok / 118.046 / 0 | PASS |
| component 8 | 149.726 / 0 / 0.0 | Ok / 149.726 / 0 | PASS |
| component 9 | 205.285 / 0 / 0.0 | Ok / 205.285 / 0 | PASS |
| component 10 | 204.246 / 0 / 0.0 | Ok / 204.246 / 0 | PASS |
| component 11 | 227.071 / 0 / 0.0 | Ok / 227.071 / 0 | PASS |
| component 12 | 119.575 / 0 / 0.0 | Ok / 119.575 / 0 | PASS |
| Cát Bà town (107.0496, 20.7262) | 150.577 / 1 / 2.015 | NoRoute / None / 0 | PASS |
| sample 155 | 75.324 / 1 / 0.204 | Ok / 77.531 / 0 | PASS |
| sample 367 | 212.472 / 1 / 0.733 | Ok / 218.092 / 0 | PASS |

Context check (A8):

```json
{
  "case": "A8 context: Hà Đông → Phố Hiến road distance",
  "section": "25.2",
  "revision9_value_km": 65.0,
  "osrm_km": 58.055,
  "relative_difference": -0.1068
}
```
