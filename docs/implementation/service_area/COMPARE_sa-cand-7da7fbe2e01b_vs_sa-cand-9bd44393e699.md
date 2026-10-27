# Service-area comparison `sa-cand-7da7fbe2e01b` → `sa-cand-9bd44393e699`

Both versions are CANDIDATE (not approved). Read-only comparison; no geometry was changed.

## 1. Area and components

| Area | Old km² | New km² | Added km² | Removed km² | Old parts | New parts |
|---|---|---|---|---|---|---|
| URBAN | 340.034 | 340.034 | 0.000 | 0.000 | 6 | 6 |
| TOTAL | 42275.390 | 68374.523 | 26099.134 | 0.000 | 335 | 1782 |
| EXCLUDED | 29.158 | 488.167 | 459.009 | 0.000 | 324 | 1770 |

## 2. Points that change status

Sample: every OSM `place=*` node (city, town, suburb, quarter, neighbourhood, village, hamlet, isolated_dwelling) inside the routing bbox — 4888 points.

| Area | Entered (out → in) | Left (in → out) |
|---|---|---|
| URBAN | 0 | 0 |
| TOTAL | 686 | 0 |

Urban status changes (named points):


## 3. Unit changes

Urban units added: none

Urban units removed: none

Urban OSM areas (U3) added: relation/21054720 Khu đô thị Nam An Khánh, way/1484064385 Vista Lago Nam An Khánh, way/1298606975 The Golden An Khánh, way/1565334267 An Khánh Ecomony, way/1565297217 Splendora Villas, way/1565297218 Splendora Terrace Mailand, way/1565297219 Splendora Lakeside Villas

Total units added by province: {'Tỉnh Phú Thọ': 2, 'Tỉnh Thanh Hóa': 90, 'Thành phố Quảng Ninh': 15, 'Tỉnh Tuyên Quang': 22, 'Tỉnh Thái Nguyên': 22, 'Tỉnh Lạng Sơn': 30, 'Tỉnh Nghệ An': 1, 'Tỉnh Lào Cai': 22, 'Tỉnh Sơn La': 23}

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
| Đông Anh (town place node) | False / MISMATCH(urban) | False / MISMATCH(urban) |
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
| Đông Anh (town node) → Hoàn Kiếm | INTERCITY (3a) / FAIL | INTERCITY (3a) / FAIL |
| An Khánh (Splendora) → Hoàn Kiếm | URBAN (2a) / PASS | URBAN (2a) / PASS |
| La Phù → Hoàn Kiếm | INTERCITY (3a) / PASS | INTERCITY (3a) / PASS |
| Tùng Thiện (Xuân Khanh) → Hoàn Kiếm | INTERCITY (3a) / PASS | INTERCITY (3a) / PASS |
| Phố Hiến → Hoàn Kiếm | INTERCITY (3a) / PASS | INTERCITY (3a) / PASS |
| inside polygon, BEYOND_MAX_ROAD_DISTANCE (tier 2) | OUT_OF_SERVICE_AREA (1) / PASS | OUT_OF_SERVICE_AREA (1) / PASS |
| inside polygon, NO_ROAD_ACCESS (tier 2) | OUT_OF_SERVICE_AREA (1) / PASS | OUT_OF_SERVICE_AREA (1) / PASS |
| point in largest EXCLUDED component (tier 1) | OUT_OF_SERVICE_AREA (1) / PASS | OUT_OF_SERVICE_AREA (1) / PASS |
| point exactly on the TOTAL polygon boundary | — | OUT_OF_SERVICE_AREA (1) / PASS |
