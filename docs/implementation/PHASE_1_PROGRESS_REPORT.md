# PHASE 1 — BÁO CÁO TIẾN ĐỘ (chưa phải báo cáo hoàn thành)

- **Ngày:** 2026-10-26 (UTC). **Trạng thái P1: `IN_PROGRESS — BLOCKED_ON_OWNER_APPROVALS`.**
- P1 **chưa** được tuyên bố hoàn thành; `PHASE_1_COMPLETION_REPORT.md` chưa được tạo (điều kiện ở mục 4).
- P0 giữ nguyên `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`; SF-06 vẫn OPEN; không có tuyên bố nào về SLA OSRM < 50 ms.
- Quy ước: **DIRECTLY_VERIFIED** = đã chạy/kiểm tra trong phiên; **REPORTED** = theo tuyên bố trước đó; **PENDING_APPROVAL** = chờ Chủ dự án.

## 0. Git (chỉ thị §9)

| Kiểm tra | Kết quả |
|---|---|
| Mốc P0 | Đã tồn tại sẵn commit `c4051ed` "Initial commit: RideSharing project" (tác giả git `ikuyooo`), **đã có trên `origin/main`** — không do phiên này tạo/push. Tôi **không** tạo thêm commit và không sửa lịch sử. |
| Nội dung commit `c4051ed` | 38 file; không có `.env`, PBF, artifact OSRM, volume, cache; quét giá trị mật khẩu thật và mẫu khóa: 0 kết quả; chứa báo cáo P0 bản đã đính chính (10.15) và SF-06 "OPEN". |
| Ghi chú | Thông điệp commit không nêu "P0 CONDITIONAL"; nội dung báo cáo trong commit đã nêu. |
| Công việc P1 | **Chưa commit** (chỉ được phép một commit mốc P0). |

## 1. Theo gói công việc

### P1.1 — Nền tảng (migrations, cấu trúc module, quy ước)
- **Nguồn:** Mục 5, 54 (D-31), 59.2. **Quyết định:** P1-D4.
- **File:** `backend/app/db/{base,session,models,types}.py`, `backend/app/core/{errors,logging,settings}.py`, `backend/alembic/`, `backend/alembic.ini`, `backend/Dockerfile`, `backend/pyproject.toml` (thêm Alembic 1.15.2, GeoAlchemy2 0.17.1, argon2-cffi 23.1.0, PyJWT 2.10.1, email-validator), `docker-compose.yml`, `.env.example`.
- **Test:** `test_architecture.py` (không import chéo `models`, mỗi bảng thuộc đúng 1 module).
- **Kết quả:** DIRECTLY_VERIFIED — PASS.

### P1.2 — Schema và ràng buộc
- **Nguồn:** Mục 56.1–56.2, 55, Baseline §5. **Quyết định:** P1-D4, P1-D7.
- **File:** `backend/app/modules/*/models.py`, `backend/alembic/versions/0001_p1_core_schema.py`, `backend/app/modules/pricing/seed.py`, `backend/tests/test_schema.py`.
- **Test:** migration từ DB trống; upgrade → downgrade → upgrade; `alembic check` (model = schema); 8 index/unique 56.2 đúng tên và điều kiện; mọi CHECK 56.2 có ca vi phạm cố ý (gồm biên 90%/110%, ±0,01 đ); seed idempotent + từ chối ghi đè + chặn UPDATE/DELETE/TRUNCATE.
- **Kết quả:** DIRECTLY_VERIFIED — PASS. DB chính: `alembic_version = 0001`, 20 bảng ứng dụng, 5 hàng `pricing_configs` (`price_v9_two_sided_bounded`).
- **Đã sửa:** seed báo sai `unchanged` ở lần chèn đầu (dùng `rowcount` của `INSERT … ON CONFLICT` qua ORM). Dữ liệu đúng (5 hàng cùng `created_at` của lần đầu); chỉ báo cáo sai. Sửa bằng `RETURNING` + test hồi quy.
- **Vấn đề mở:** không.

### P1.3 — Identity và RBAC
- **Nguồn:** Mục 3, 59.1. **Quyết định:** P1-D6.
- **File:** `backend/app/modules/identity/{models,security,schemas,service,deps,api,cli}.py`, `backend/tests/test_identity.py`.
- **Test:** Argon2id (`$argon2id$`), access token 15 phút, token sai/hết hạn/giả chữ ký, xoay vòng refresh + phát hiện dùng lại (thu hồi cả họ), logout, refresh hết hạn, tài khoản vô hiệu, RBAC, không tự đăng ký ADMIN, email trùng không phân biệt hoa thường, lỗi đăng nhập không lộ tài khoản, giới tính tùy chọn và luôn `UNVERIFIED`.
- **Kết quả:** DIRECTLY_VERIFIED — PASS.

### P1.4 — Driver, Vehicle, KYC mock
- **Nguồn:** Mục 3, 56.1, 57, 81.
- **File:** `backend/app/modules/driver/{models,schemas,service,api}.py`, `backend/tests/test_driver.py`.
- **Test:** sức chứa xe lấy từ Baseline; biển số trùng; khóa `pool_enabled`/`accepts_intercity` (403 `KYC_REQUIRED`) đến khi VERIFIED; vẫn bật được nhận nội đô; NONE→PENDING→VERIFIED/REJECTED→nộp lại; duyệt chỉ khi PENDING; pool cần xe CAR4; vị trí GPS lưu đúng và **không xuất hiện trong log**.
- **Kết quả:** DIRECTLY_VERIFIED — PASS.

### P1.5 — Trip Intent và luật thời gian
- **Nguồn:** Mục 2.2, 2.3, 6, 72.2. **Quyết định:** P1-D2.
- **File:** `backend/app/modules/trip/{rules,schemas,service,api,boundary_eval}.py`, `backend/app/modules/routing/service.py`, `backend/tests/{test_trip_rules,test_trip_api,test_routing}.py`.
- **Test (logic, DIRECTLY_VERIFIED — PASS):** 3 bước Mục 2.3 (khoảng cách chỉ gọi khi đúng 1 đầu nội đô); 15,0 km → URBAN, 15,000001 km → INTERCITY; bảng Mục 6; 71h59 → từ chối POOL liên tỉnh + gợi ý PRIVATE; đúng 72h00 → hợp lệ; 12 h và 7 ngày; G13 ở mức suy diễn dịch vụ; lỗi định tuyến tường minh, không fallback; OSRM thật trả khoảng cách (mét), không phải thời gian.
- **Test API (đa giác SYNTHETIC, chỉ chứng minh hành vi API):** 503 khi chưa cấu hình / chưa phê duyệt; ALLOW_CANDIDATE chỉ cho phát triển; OUT_OF_SERVICE_AREA; UNSUPPORTED_INTER_PROVINCE_ROUTE; quyền sở hữu (người khác 404, admin 200); tọa độ không vào log.
- **Đánh giá trên dữ liệu thật** (`docs/implementation/service_area/sa-cand-3873dfbee116/TRIP_CLASSIFICATION_EVAL.md`, hình học **CANDIDATE** — chỉ là bằng chứng tham khảo): ~3 km trong "TP Hưng Yên" (2,589 km) → UNSUPPORTED ✔; 14,99 km → URBAN ✔; 15,32 km → INTERCITY ✔; điểm ngoài vùng tổng → OUT_OF_SERVICE_AREA ✔; **Phenikaa → La Phù → URBAN nhưng qua bước 2a** (đặc tả hàm ý 2b) — xem SF-P1-02.
- **Kết quả nghiệm thu phân loại địa lý:** **PENDING_APPROVAL** (cần hình học được duyệt).

### P1.6 — Pipeline đa giác ứng viên
- **Nguồn:** Mục 1, 2.3. **Quyết định:** P1-D1, P1-D3.
- **File:** `scripts/osm/export_service_area_sources.sh`, `config/service_area_rules.candidate.yaml`, `backend/app/modules/trip/service_area_build.py`, service compose `service-area-build`, bundle `docs/implementation/service_area/sa-cand-3873dfbee116/` (REVIEW.md, urban.geojson, total.geojson, units.csv, report.json).
- **Kết quả (DIRECTLY_VERIFIED):** 33 tỉnh / 3.321 xã-phường nạp được, 0 cần sửa hình học; nội đô 54 đơn vị (51 phường + 3 xã có tên trong Mục 2.3), 511,2 km²; vùng tổng 714 đơn vị, 26.349,3 km²; hình học hợp lệ; nội đô ⊂ vùng tổng; **import lại ổn định** (cùng MD5 export, cùng version, `ST_Equals`).
- **Đã sửa:** bản ứng viên đầu `sa-cand-362c22716ade` dựng từ extract đã cắt bbox — các quan hệ ranh giới vắt qua bbox không đầy đủ (chỉ 6 tỉnh dựng được; thiếu Hải Phòng, Ninh Bình). Đã chứng minh nguyên nhân (6 vs 39 đa giác cấp tỉnh), chuyển sang export từ file nguồn Geofabrik đã kiểm MD5, bản cũ đặt `RETIRED` + `SUPERSEDED.md`.
- **Trạng thái:** `CANDIDATE` — **không** GEOMETRY_APPROVED; `ANCHOR_DEFINITION_REQUIRED`. Vấn đề mở: SF-P1-01 … SF-P1-07, SF-P1-09, SF-P1-10.

### P1.7 — Khảo sát S1 (chuẩn bị)
- **Nguồn:** Mục 59.2, 65. **Quyết định:** P1-D5.
- **File:** `docs/implementation/survey/SURVEY_S1_DESIGN_REVIEW.md`, `survey/s1/questionnaire.draft.yaml`, `survey/s1/export_schema.md`.
- **Kết quả:** đủ 8 mục yêu cầu; mọi giá trị có nguồn (`R9:` / `DERIVED:B` / `TBD`). Phương pháp B tái tạo đúng 5 con số 14 km của Revision 9 (đã chạy kiểm tra).
- **Chưa làm (chờ duyệt nội dung):** biểu mẫu web, API ghi, bảng `survey_responses`, phát hành. **Không có link hoạt động.**

## 2. Kết quả kiểm thử tổng hợp (DIRECTLY_VERIFIED)

| Bộ test | Kết quả |
|---|---|
| Backend pytest (toàn bộ) | **88 tests: 88 passed, 0 failed, 0 skipped**, exit 0 |
| P0 smoke check sau khi tích hợp migration (`--restart-test`) | **18/18 PASS** — `docs/implementation/evidence/p0_smoke_check_after_p1_migrations.json` |
| Pipeline service area chạy 2 lần | cùng version `sa-cand-3873dfbee116`, `unchanged (ST_Equals)` |
| Đánh giá phân loại trên dữ liệu thật (CANDIDATE) | 5 ca: 4 khớp, 1 khớp kết quả nhưng khác đường đi |

## 3. Quyết định cần Chủ dự án

1. **Hình học vùng phục vụ** (P1-D1/D3): duyệt hoặc chỉnh `sa-cand-3873dfbee116` — kèm SF-P1-01…07, 09, 10 (ánh xạ tỉnh, An Khánh/La Phù, Mỹ Đình, Gia Lâm/Đông Anh, phạm vi tỉnh, phân mảnh).
2. **Điểm gốc 150 km** (`ANCHOR_DEFINITION_REQUIRED`).
3. **Nội dung khảo sát S1**: 8 điểm ở cuối `SURVEY_S1_DESIGN_REVIEW.md`, gồm nơi triển khai công khai và kênh phát hành.
4. SF-P1-08 (giá trị mặc định `max_passenger_detour_ratio`) — cần trước P2.
5. Cho phép commit công việc P1 (hiện chưa commit).

## 4. Điều kiện để đóng P1 (chỉ thị §12) — hiện trạng

| Điều kiện | Trạng thái |
|---|---|
| 1. Schema và ràng buộc bắt buộc đạt | **ĐẠT** (DIRECTLY_VERIFIED) |
| 2. Identity và Driver/KYC Mock hoạt động | **ĐẠT** (DIRECTLY_VERIFIED) |
| 3. Trip Intent phân loại đúng toàn bộ ca biên **đã phê duyệt** | **CHƯA** — chờ hình học được duyệt; logic đã kiểm chứng |
| 4. Khảo sát S1 phát hành và bắt đầu thu thập | **CHƯA** — chờ duyệt nội dung + hạ tầng |
| 5. Không còn blocker P1 | **CHƯA** — blocker là các phê duyệt ở mục 3 |
| 6. `PHASE_1_COMPLETION_REPORT.md` + bằng chứng | **CHƯA** — sẽ lập khi 3–5 đạt |
