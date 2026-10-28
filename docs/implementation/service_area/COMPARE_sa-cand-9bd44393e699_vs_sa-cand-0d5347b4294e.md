# Service-area comparison `sa-cand-9bd44393e699` → `sa-cand-0d5347b4294e`

Both versions are CANDIDATE (not approved). Read-only comparison; no geometry was changed.

## 1. Area and components

| Area | Old km² | New km² | Added km² | Removed km² | Old parts | New parts |
|---|---|---|---|---|---|---|
| URBAN | 340.034 | 344.381 | 4.347 | 0.000 | 6 | 7 |
| TOTAL | 68374.523 | 68374.523 | 0.000 | 0.000 | 1782 | 1782 |
| EXCLUDED | 488.167 | 488.167 | 0.000 | 0.000 | 1770 | 1770 |

## 2. Points that change status

Sample: every OSM `place=*` node (city, town, suburb, quarter, neighbourhood, village, hamlet, isolated_dwelling) inside the routing bbox — 4888 points.

| Area | Entered (out → in) | Left (in → out) |
|---|---|---|
| URBAN | 1 | 0 |
| TOTAL | 0 | 0 |

Urban status changes (named points):

- node/13799910539 Đông Anh: outside → URBAN

## 3. Unit changes

Urban units added: none

Urban units removed: none

Urban OSM areas (U3) added: relation/21054720 Khu đô thị Nam An Khánh, way/1484064385 Vista Lago Nam An Khánh, way/1298606975 The Golden An Khánh, way/1565334267 An Khánh Ecomony, way/1565297217 Splendora Villas, way/1565297218 Splendora Terrace Mailand, way/1565297219 Splendora Lakeside Villas

Total units added by province: none

Total units removed by province: none

## 4. Test locations

| Location | Old urban / result | New urban / result |
|---|---|---|
| Hoàn Kiếm | True / AS_EXPECTED | True / AS_EXPECTED |
| Hà Đông | True / AS_EXPECTED | True / AS_EXPECTED |
| Yên Nghĩa | True / AS_EXPECTED | True / AS_EXPECTED |
| Dương Nội | True / AS_EXPECTED | True / AS_EXPECTED |
| An Khánh (Khu đô thị Nam An Khánh) | True / AS_EXPECTED | True / AS_EXPECTED |
| An Khánh (Splendora / Bắc An Khánh) | True / AS_EXPECTED | True / AS_EXPECTED |
| Mỹ Đình (Sân vận động Quốc gia) | True / AS_EXPECTED | True / AS_EXPECTED |
| Mỹ Đình (Bến xe Mỹ Đình) | True / AS_EXPECTED | True / AS_EXPECTED |
| Gia Lâm (Khu tái định cư Trâu Quỳ) | True / AS_EXPECTED | True / AS_EXPECTED |
| Đông Anh (town place node) | False / MISMATCH(urban) | True / AS_EXPECTED |
| La Phù | False / AS_EXPECTED | False / AS_EXPECTED |
| Đại học Phenikaa | True / AS_EXPECTED | True / AS_EXPECTED |
| Tùng Thiện (Xuân Khanh) | False / AS_EXPECTED | False / AS_EXPECTED |
| Sơn Tây (city node) | False / AS_EXPECTED | False / AS_EXPECTED |
| Phố Hiến (TP Hưng Yên representative) | False / AS_EXPECTED | False / AS_EXPECTED |

## 5. Effect on Trip Intent classification (same deterministic cases)

| Case | Old actual (branch) / result | New actual (branch) / result |
|---|---|---|
| Phenikaa → La Phù | URBAN (2b) / PASS | URBAN (2b) / PASS |
| ~3 km inside TP Hưng Yên | UNSUPPORTED_INTER_PROVINCE_ROUTE (3b) / PASS | UNSUPPORTED_INTER_PROVINCE_ROUTE (3b) / PASS |
| buffer <= 15 km from Phenikaa | URBAN (2b) / PASS | URBAN (2b) / PASS |
| buffer > 15 km from Phenikaa | INTERCITY (3a) / PASS | INTERCITY (3a) / PASS |
| limit <= 150 km from anchor | INTERCITY (3a) / PASS | INTERCITY (3a) / PASS |
| limit > 150 km from anchor | OUT_OF_SERVICE_AREA (1) / PASS | OUT_OF_SERVICE_AREA (1) / PASS |
| Đông Anh (town node) → Hoàn Kiếm | INTERCITY (3a) / FAIL | URBAN (2a) / PASS |
| An Khánh (Splendora) → Hoàn Kiếm | URBAN (2a) / PASS | URBAN (2a) / PASS |
| La Phù → Hoàn Kiếm | INTERCITY (3a) / PASS | INTERCITY (3a) / PASS |
| Tùng Thiện (Xuân Khanh) → Hoàn Kiếm | INTERCITY (3a) / PASS | INTERCITY (3a) / PASS |
| Phố Hiến → Hoàn Kiếm | INTERCITY (3a) / PASS | INTERCITY (3a) / PASS |
| inside polygon, BEYOND_MAX_ROAD_DISTANCE (tier 2) | OUT_OF_SERVICE_AREA (1) / PASS | OUT_OF_SERVICE_AREA (1) / PASS |
| inside polygon, NO_ROAD_ACCESS (tier 2) | OUT_OF_SERVICE_AREA (1) / PASS | OUT_OF_SERVICE_AREA (1) / PASS |
| point in largest EXCLUDED component (tier 1) | OUT_OF_SERVICE_AREA (1) / PASS | OUT_OF_SERVICE_AREA (1) / PASS |
| point exactly on the TOTAL polygon boundary | OUT_OF_SERVICE_AREA (1) / PASS | OUT_OF_SERVICE_AREA (1) / PASS |
