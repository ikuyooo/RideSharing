# Geographic edge cases on real data — `sa-cand-3873dfbee116` (CANDIDATE)

Production classification (`app.modules.trip.rules.classify`) + OSRM car road distance (P1-D2). Buffer 15.0 km and limit 150.0 km from the baseline. Coordinates: OSM objects from the places export (`@type/@id` below; ways/relations use `ST_PointOnSurface`).

| Case | R9 § | Pickup (OSM) | Dropoff (OSM) | Road km | Expected | Actual | Branch | Result on candidate | Acceptance |
|---|---|---|---|---|---|---|---|---|---|
| Phenikaa → La Phù | 72.2 | way/973433275 Đại học Phenikaa | node/12147486706 La Phù | — | URBAN | URBAN | 2a | **PASS (mode) / branch 2a ≠ expected 2b** | NOT_VERIFIED (geometry not approved) |
| ~3 km inside TP Hưng Yên | 72.2 | node/13155709564 Phố Hiến | node/11518465547 Minh Khai | 2.589 | UNSUPPORTED_INTER_PROVINCE_ROUTE | UNSUPPORTED_INTER_PROVINCE_ROUTE | 3b | **PASS** | NOT_VERIFIED (geometry not approved) |
| buffer <= 15 km from Phenikaa | 2.3 | way/973433275 Đại học Phenikaa | node/12607118252 Vĩnh Thịnh | 14.9919 | URBAN | URBAN | 2b | **PASS** | NOT_VERIFIED (geometry not approved) |
| buffer > 15 km from Phenikaa | 2.3 | way/973433275 Đại học Phenikaa | node/12611713598 Yên Kiện | 15.321299999999999 | INTERCITY | INTERCITY | 3a | **PASS** | NOT_VERIFIED (geometry not approved) |
| limit <= 150 km from anchor | 2.3 / Baseline max_total_service_radius_km | node/74132064 Hà Nội | node/11578421390 Tứ Quận | 149.984 | INTERCITY | OUT_OF_SERVICE_AREA | 1 | **FAIL** | NOT_VERIFIED (geometry not approved) |
| limit > 150 km from anchor | 2.3 / Baseline max_total_service_radius_km | node/74132064 Hà Nội | node/6766268697  | 150.024 | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | 1 | **PASS** | NOT_VERIFIED (geometry not approved) |

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
