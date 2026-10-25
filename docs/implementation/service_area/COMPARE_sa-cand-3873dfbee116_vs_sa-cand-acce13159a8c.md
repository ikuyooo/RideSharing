# Service-area comparison `sa-cand-3873dfbee116` → `sa-cand-acce13159a8c`

Both versions are CANDIDATE (not approved). Read-only comparison; no geometry was changed.

## 1. Area and components

| Area | Old km² | New km² | Added km² | Removed km² | Old parts | New parts |
|---|---|---|---|---|---|---|
| URBAN | 511.166 | 484.116 | 0.337 | 27.386 | 2 | 7 |
| TOTAL | 26349.323 | 38618.767 | 12269.445 | 0.000 | 222 | 332 |

## 2. Points that change status

Sample: every OSM `place=*` node (city, town, suburb, quarter, neighbourhood, village, hamlet, isolated_dwelling) inside the routing bbox — 4888 points.

| Area | Entered (out → in) | Left (in → out) |
|---|---|---|
| URBAN | 0 | 11 |
| TOTAL | 372 | 0 |

Urban status changes (named points):

- node/12589887268 An Bình: URBAN → outside
- node/12147486704 An Thượng: URBAN → outside
- node/12589872773 An Thọ: URBAN → outside
- node/12147486706 La Phù: URBAN → outside
- node/12589872774 Ngãi Cầu: URBAN → outside
- node/12589872775 Phú Vinh: URBAN → outside
- node/12589872776 Trường An: URBAN → outside
- node/12147486703 Vân Côn: URBAN → outside
- node/12589872778 Vân Lũng: URBAN → outside
- node/12589872777 Yên Lũng: URBAN → outside
- node/12147486705 Đông La: URBAN → outside

## 3. Unit changes

Urban units added: none

Urban units removed: Xã An Khánh

Urban OSM areas (U3) added: relation/21054720 Khu đô thị Nam An Khánh, way/1484064385 Vista Lago Nam An Khánh, way/1298606975 The Golden An Khánh, way/1565334267 An Khánh Ecomony, way/1565297217 Splendora Villas, way/1565297218 Splendora Terrace Mailand, way/1565297219 Splendora Lakeside Villas

Total units added by province: {'Tỉnh Thái Nguyên': 63, 'Tỉnh Thanh Hóa': 36, 'Tỉnh Lạng Sơn': 25, 'Tỉnh Tuyên Quang': 20, 'Tỉnh Lào Cai': 2, 'Thành phố Quảng Ninh': 17, 'Tỉnh Sơn La': 1}

Total units removed by province: none

## 4. Test locations

| Location | Old urban / result | New urban / result |
|---|---|---|
| Hoàn Kiếm | True / AS_EXPECTED | True / AS_EXPECTED |
| Hà Đông | True / AS_EXPECTED | True / AS_EXPECTED |
| Yên Nghĩa | True / AS_EXPECTED | True / AS_EXPECTED |
| Dương Nội | True / AS_EXPECTED | True / AS_EXPECTED |
| An Khánh (Khu đô thị Nam An Khánh) | not tested in old version | True / AS_EXPECTED |
| An Khánh (Splendora / Bắc An Khánh) | not tested in old version | True / AS_EXPECTED |
| Mỹ Đình (Sân vận động Quốc gia) | not tested in old version | True / AS_EXPECTED |
| Mỹ Đình (Bến xe Mỹ Đình) | not tested in old version | True / AS_EXPECTED |
| Gia Lâm (Khu tái định cư Trâu Quỳ) | not tested in old version | True / AS_EXPECTED |
| Đông Anh (town place node) | False / MISMATCH(urban) | False / MISMATCH(urban) |
| La Phù | True / MISMATCH(urban) | False / AS_EXPECTED |
| Đại học Phenikaa | True / AS_EXPECTED | True / AS_EXPECTED |
| Phố Hiến (TP Hưng Yên representative) | False / AS_EXPECTED | False / AS_EXPECTED |

## 5. Effect on Trip Intent classification (same deterministic cases)

| Case | Old actual (branch) / result | New actual (branch) / result |
|---|---|---|
| Phenikaa → La Phù | URBAN (2a) / PASS (mode) / branch 2a ≠ expected 2b | URBAN (2b) / PASS |
| ~3 km inside TP Hưng Yên | UNSUPPORTED_INTER_PROVINCE_ROUTE (3b) / PASS | UNSUPPORTED_INTER_PROVINCE_ROUTE (3b) / PASS |
| buffer <= 15 km from Phenikaa | URBAN (2b) / PASS | URBAN (2b) / PASS |
| buffer > 15 km from Phenikaa | INTERCITY (3a) / PASS | INTERCITY (3a) / PASS |
| limit <= 150 km from anchor | OUT_OF_SERVICE_AREA (1) / FAIL | INTERCITY (3a) / PASS |
| limit > 150 km from anchor | OUT_OF_SERVICE_AREA (1) / PASS | OUT_OF_SERVICE_AREA (1) / PASS |
