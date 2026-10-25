# Trip classification on real data — `sa-cand-3873dfbee116` (CANDIDATE)

Production classification code + OSRM car road distance (P1-D2). **Geometry is CANDIDATE: review evidence only, not acceptance.**
Buffer (baseline urban_boundary_buffer_km): 15.0 km.

| Case | Pickup | Dropoff | Road km | Step | Result mode/error | Expected | Outcome |
|---|---|---|---|---|---|---|---|
| 72.2 Phenikaa -> La Phù | way/973433275 | node/12147486706  | — | 2a | URBAN | URBAN | **AS_EXPECTED_MODE_BUT_DIFFERENT_PATH (2a, spec implies 2b)** |
| 72.2 ~3 km inside former TP Hưng Yên | node/13155709564 | node/11518465547 Minh Khai | 2.589 | 3b | UNSUPPORTED_INTER_PROVINCE_ROUTE | UNSUPPORTED_INTER_PROVINCE_ROUTE | **AS_EXPECTED** |
| buffer <= 15 km from Phenikaa | way/973433275 | node/12607118252 Vĩnh Thịnh | 14.9919 | 2b | URBAN | URBAN | **AS_EXPECTED** |
| buffer > 15 km from Phenikaa | way/973433275 | node/12611713598 Yên Kiện | 15.321299999999999 | 3a | INTERCITY | INTERCITY | **AS_EXPECTED** |
| outside coverage: anchor -> nearest town/city outside TOTAL | node/74132064 | node/13146976467 Thành Công | — | 1 | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | **AS_EXPECTED** |
