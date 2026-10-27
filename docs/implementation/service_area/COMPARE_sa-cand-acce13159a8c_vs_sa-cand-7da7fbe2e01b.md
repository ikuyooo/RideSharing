# Service-area comparison `sa-cand-acce13159a8c` → `sa-cand-7da7fbe2e01b`

Both versions are CANDIDATE (not approved). Read-only comparison; no geometry was changed.

## 1. Area and components

| Area | Old km² | New km² | Added km² | Removed km² | Old parts | New parts |
|---|---|---|---|---|---|---|
| URBAN | 484.116 | 340.034 | 0.000 | 144.083 | 7 | 6 |
| TOTAL | 38618.767 | 42275.390 | 3656.622 | 0.000 | 332 | 335 |

## 2. Points that change status

Sample: every OSM `place=*` node (city, town, suburb, quarter, neighbourhood, village, hamlet, isolated_dwelling) inside the routing bbox — 4888 points.

| Area | Entered (out → in) | Left (in → out) |
|---|---|---|
| URBAN | 0 | 24 |
| TOTAL | 96 | 0 |

Urban status changes (named points):

- node/11217773959 Biên Giang: URBAN → outside
- node/10235622207 Bắc Sơn: URBAN → outside
- node/11672545174 Chúc Đồng: URBAN → outside
- node/13709960772 Chương Mỹ: URBAN → outside
- node/12137952441 Cổ Loa: URBAN → outside
- node/12137952442 Dục Tú: URBAN → outside
- node/12820372613 Lại Đà: URBAN → outside
- node/12139046639 Mai Lâm: URBAN → outside
- node/12154565348 Ngô Quyền: URBAN → outside
- node/12522412440 Ngọc Hòa: URBAN → outside
- node/12522412438 Phụng Châu: URBAN → outside
- node/13341355937 Sơn Tây: URBAN → outside
- node/9122373056 Thuỵ Hương: URBAN → outside
- node/12522412439 Tiên Phương: URBAN → outside
- node/12617825100 Trung Hưng: URBAN → outside
- node/12617825435 Trung Sơn Trầm: URBAN → outside
- node/11934668889 Uy Nỗ: URBAN → outside
- node/12154565360 Viên Sơn: URBAN → outside
- node/11934668841 Việt Hùng: URBAN → outside
- node/4903108773 Xuân Canh: URBAN → outside
- node/12629466848 Xuân Khanh: URBAN → outside
- node/10235684712 Yên Khê: URBAN → outside
- node/12137952387 Đông Hội: URBAN → outside
- node/12522412456 Đại Yên: URBAN → outside

## 3. Unit changes

Urban units added: none

Urban units removed: Xã Đông Anh, Phường Chương Mỹ, Phường Tùng Thiện, Phường Sơn Tây

Urban OSM areas (U3) added: relation/21054720 Khu đô thị Nam An Khánh, way/1484064385 Vista Lago Nam An Khánh, way/1298606975 The Golden An Khánh, way/1565334267 An Khánh Ecomony, way/1565297217 Splendora Villas, way/1565297218 Splendora Terrace Mailand, way/1565297219 Splendora Lakeside Villas

Total units added by province: {'Tỉnh Thanh Hóa': 13, 'Tỉnh Tuyên Quang': 1, 'Tỉnh Sơn La': 2, 'Tỉnh Phú Thọ': 2, 'Tỉnh Lào Cai': 5, 'Thành phố Quảng Ninh': 1, 'Tỉnh Lạng Sơn': 9, 'Tỉnh Ninh Bình': 1, 'Tỉnh Thái Nguyên': 1}

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
| Tùng Thiện (Xuân Khanh) | not tested in old version | False / AS_EXPECTED |
| Sơn Tây (city node) | not tested in old version | False / AS_EXPECTED |
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
| Đông Anh (town node) → Hoàn Kiếm | — | INTERCITY (3a) / FAIL |
| An Khánh (Splendora) → Hoàn Kiếm | — | URBAN (2a) / PASS |
| La Phù → Hoàn Kiếm | — | INTERCITY (3a) / PASS |
| Tùng Thiện (Xuân Khanh) → Hoàn Kiếm | — | INTERCITY (3a) / PASS |
| Phố Hiến → Hoàn Kiếm | — | INTERCITY (3a) / PASS |
| inside polygon, BEYOND_MAX_ROAD_DISTANCE (tier 2) | — | OUT_OF_SERVICE_AREA (1) / PASS |
| inside polygon, NO_ROAD_ACCESS (tier 2) | — | OUT_OF_SERVICE_AREA (1) / PASS |
| point in largest EXCLUDED component (tier 1) | — | OUT_OF_SERVICE_AREA (1) / PASS |
