# Geographic edge cases on real data — `sa-cand-7da7fbe2e01b` (CANDIDATE)

Production classification (`app.modules.trip.rules.classify`) + OSRM car road distance (P1-D2). Buffer 15.0 km and limit 150.0 km from the baseline. Coordinates: OSM objects from the places export (`@type/@id` below; ways/relations use `ST_PointOnSurface`).

| Case | R9 § | Pickup (OSM) | Dropoff (OSM) | Road km | Expected | Actual | Branch | Result on candidate | Acceptance |
|---|---|---|---|---|---|---|---|---|---|
| Phenikaa → La Phù | 72.2 | way/973433275 Đại học Phenikaa | node/12147486706 La Phù | 5.9768 | URBAN | URBAN | 2b | **PASS** | NOT_VERIFIED (geometry not approved) |
| ~3 km inside TP Hưng Yên | 72.2 | node/13155709564 Phố Hiến | node/11518465547 Minh Khai | 2.589 | UNSUPPORTED_INTER_PROVINCE_ROUTE | UNSUPPORTED_INTER_PROVINCE_ROUTE | 3b | **PASS** | NOT_VERIFIED (geometry not approved) |
| buffer <= 15 km from Phenikaa | 2.3 | way/973433275 Đại học Phenikaa | node/12607118252 Vĩnh Thịnh | 14.9919 | URBAN | URBAN | 2b | **PASS** | NOT_VERIFIED (geometry not approved) |
| buffer > 15 km from Phenikaa | 2.3 | way/973433275 Đại học Phenikaa | node/12611713598 Yên Kiện | 15.321299999999999 | INTERCITY | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| limit <= 150 km from anchor | 2.3 / Baseline max_total_service_radius_km | node/74132064 Hà Nội | node/11578421390 Tứ Quận | 149.9839 | INTERCITY | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| limit > 150 km from anchor | 2.3 / Baseline max_total_service_radius_km | node/74132064 Hà Nội | node/6766268697  | 150.024 | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | 1 | **PASS** | NOT_VERIFIED (geometry not approved) |
| Đông Anh (town node) → Hoàn Kiếm | landmark (GEO closure) | node/13799910539 Đông Anh | node/13709921432 Hoàn Kiếm | 19.6784 | URBAN | INTERCITY | 3a | **FAIL** | NOT_VERIFIED (geometry not approved) |
| An Khánh (Splendora) → Hoàn Kiếm | landmark (GEO closure) | way/1565297218 Splendora Terrace Mailand | node/13709921432 Hoàn Kiếm | — | URBAN | URBAN | 2a | **PASS** | NOT_VERIFIED (geometry not approved) |
| La Phù → Hoàn Kiếm | landmark (GEO closure) | node/12147486706 La Phù | node/13709921432 Hoàn Kiếm | 17.1913 | INFO | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| Tùng Thiện (Xuân Khanh) → Hoàn Kiếm | landmark (GEO closure) | node/12629466848 Xuân Khanh | node/13709921432 Hoàn Kiếm | 47.377300000000005 | INTERCITY | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| Phố Hiến → Hoàn Kiếm | landmark (GEO closure) | node/13155709564 Phố Hiến | node/13709921432 Hoàn Kiếm | 56.3785 | INTERCITY | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| inside polygon, BEYOND_MAX_ROAD_DISTANCE (tier 2) | GEO-03 | node/13709921432 Hoàn Kiếm | sample point  | — | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | 1 | **PASS** | NOT_VERIFIED (geometry not approved) |
| inside polygon, NO_ROAD_ACCESS (tier 2) | GEO-03 | node/13709921432 Hoàn Kiếm | sample point  | — | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | 1 | **PASS** | NOT_VERIFIED (geometry not approved) |
| point in largest EXCLUDED component (tier 1) | GEO-04 | node/13709921432 Hoàn Kiếm | EXCLUDED component  | — | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | 1 | **PASS** | NOT_VERIFIED (geometry not approved) |

Tier-2 reasons (GEO-03): Phenikaa → La Phù: pickup None, dropoff None (anchor km 17.403, snap 37.5 m); ~3 km inside TP Hưng Yên: pickup None, dropoff None (anchor km 58.033, snap 1.9 m); buffer <= 15 km from Phenikaa: pickup None, dropoff None (anchor km 14.362, snap 1.1 m); buffer > 15 km from Phenikaa: pickup None, dropoff None (anchor km 14.294, snap 13.4 m); limit <= 150 km from anchor: pickup None, dropoff None (anchor km 149.984, snap 9.8 m); limit > 150 km from anchor: pickup None, dropoff BEYOND_MAX_ROAD_DISTANCE (anchor km 150.024, snap 32.7 m); Đông Anh (town node) → Hoàn Kiếm: pickup None, dropoff None (anchor km 0.724, snap 0.5 m); An Khánh (Splendora) → Hoàn Kiếm: pickup None, dropoff None (anchor km 0.724, snap 0.5 m); La Phù → Hoàn Kiếm: pickup None, dropoff None (anchor km 0.724, snap 0.5 m); Tùng Thiện (Xuân Khanh) → Hoàn Kiếm: pickup None, dropoff None (anchor km 0.724, snap 0.5 m); Phố Hiến → Hoàn Kiếm: pickup None, dropoff None (anchor km 0.724, snap 0.5 m); inside polygon, BEYOND_MAX_ROAD_DISTANCE (tier 2): pickup None, dropoff BEYOND_MAX_ROAD_DISTANCE (anchor km 154.347, snap 91.5 m); inside polygon, NO_ROAD_ACCESS (tier 2): pickup None, dropoff NO_ROAD_ACCESS (anchor km 153.746, snap 373.1 m); point in largest EXCLUDED component (tier 1): pickup None, dropoff UNSERVICEABLE_COMPONENT (anchor km None, snap None m)

Seeded sample of the accept-able polygon:

```json
{
  "sample": "400 points, ST_GeneratePoints seed 1 over TOTAL minus EXCLUDED",
  "by_outcome": {
    "BEYOND_MAX_ROAD_DISTANCE": 19,
    "NO_ROAD_ACCESS": 118,
    "SERVED": 263
  }
}
```

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
