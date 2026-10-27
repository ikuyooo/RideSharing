# PHASE 1 — BÁO CÁO TIẾN ĐỘ (chưa phải báo cáo hoàn thành)

- **Cập nhật:** 2026-10-27 (sau quyết định "PHASE 1 FINAL CLOSURE & OWNER DECISION IMPLEMENTATION").
- **Trạng thái P1: `PHASE_1_IN_PROGRESS__APPROVAL_REQUIRED`.** `PHASE_1_COMPLETION_REPORT.md` **không được tạo** — tiêu chí Mục 79 chưa đạt đủ (mục 9).
- Giữ nguyên: `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`; SF-06 = OPEN; Revision 9 và Baseline v1 không bị sửa; chưa chuyển sang P2.
- Quy ước: **DIRECTLY_VERIFIED** = đã chạy trong phiên; **OFFICIALLY_VERIFIED** = đọc trực tiếp văn bản gốc; **CANDIDATE** = chưa phê duyệt.

## 1. Quyết định đã thực hiện

| Mã | Kết quả | Trạng thái |
|---|---|---|
| GEO-01 Đông Anh | Bỏ quy tắc lấy nguyên Xã Đông Anh; tra cứu Thư Lâm / Đông Anh / Phúc Thịnh; ranh giới thị trấn cũ trong OSM (`relation/17627914`) là vòng hở 1.885,6 m; không có polygon khu dân cư có căn cứ | **`PENDING_GEOMETRY_EVIDENCE`** (Đông Anh → Hoàn Kiếm = INTERCITY 19,678 km, trái Mục 2.3 — SF-P1-14) |
| GEO-02 Tùng Thiện | Loại khỏi nội đô; danh sách nội đô có kiểm soát 49 đơn vị (48 phường k1–k48 + Xã Gia Lâm k109), mỗi dòng có mã QĐ19 + khoản NQ1656, được pipeline đối chiếu | Đã làm; Sơn Tây (k50), Chương Mỹ (k49) chờ xác nhận (SF-P1-20) |
| GEO-03 150 km | Anchor node 74132064 giữ; hai lớp: polygon (điểm đại diện **hoặc** điểm mẫu ≤ 150 km, trừ EXCLUDED) + kiểm tra từng pickup/dropoff bằng một request OSRM `/table` (snap ≤ 300 m, có tuyến từ anchor, ≤ 150 km, pickup→dropoff có tuyến). Ghi là quyết định triển khai, không phải công thức R9 | Đã làm; `max_snap_m = 300` chờ xác nhận (SF-P1-16); 4 đơn vị mép bị sót (SF-P1-15) |
| GEO-04 Đảo | Lớp `EXCLUDED` (migration `0003`): 324 thành phần / 29,158 km² không có đường định tuyến bên trong; polygon gốc giữ nguyên | Đã làm; tuyến qua phà (SF-P1-17) |
| GEO-05 Splendora | Giữ theo tên; vị trí chủ đầu tư (Km10+600 ĐL Thăng Long, Sơn Đồng) khớp polygon OSM ở Xã Sơn Đồng; La Phù lịch sử 0 km² chồng U3; Phenikaa → La Phù = URBAN 2b | Đã làm; diện tích OSM 32 ha / công bố 81,2 ha (SF-P1-19) |
| GEO-06 Nguồn chính thức | Đọc trực tiếp PDF ký số QĐ 19/2025/QĐ-TTg (126 đơn vị Hà Nội) và NQ 1656 (k1–k54, k97–k120); 126/126 tên OSM khớp | **OFFICIALLY_VERIFIED** (mã + khoản) |
| Khảo sát 1–8 | Draft 2: giá 6 km theo công thức khóa, ETA OSRM hiệu chỉnh; 145k thay 143k; ma trận biến thiên (không kích hoạt); đi bộ thuộc tính riêng; mức "đủ khách" giả định; D2–D4; QC2 gắn cờ; quota 150 (trần 90/nhóm) | Đã hiện thực; 9 dòng chờ duyệt (mục 5) |
| Hạ tầng khảo sát | Caddy HTTPS (chỉ route khảo sát, log không IP), overlay compose máy chủ riêng, rate limit Redis khóa băm, xóa theo mã phiên, backup/restore + diễn tập | `PREPARED — NOT DEPLOYED` |

## 2. Phiên bản vùng phục vụ

**`sa-cand-7da7fbe2e01b`** — CANDIDATE, **không** GEOMETRY_APPROVED. Rà soát: `service_area/GEOMETRY_REVIEW_P1_FINAL_CLOSURE.md`.

| | v1 `3873dfbee116` | v2 `acce13159a8c` | v3 `7da7fbe2e01b` |
|---|---|---|---|
| Nội đô | 511,166 km², 2 phần | 484,116 km², 7 phần | **340,034 km², 6 phần** |
| TOTAL gốc | 26.349,323 km², 222 phần | 38.618,767 km², 332 phần | **42.275,390 km², 335 phần** |
| EXCLUDED | — | — | **29,158 km², 324 phần** |
| Vùng chấp nhận lớp 1 | — | — | **42.246,232 km²** |

v2 → v3: nội đô −144,083 km² (bỏ Đông Anh, Chương Mỹ, Tùng Thiện, Sơn Tây); TOTAL +3.656,622 km² (35 đơn vị thêm theo điểm mẫu, 0 bỏ). v1/v2 giữ nguyên trong DB và bundle; v2 tái lập bằng mã mới: cùng id, `unchanged (ST_Equals)`, SHA-256 GeoJSON trùng. v3 import lần 2: 3 lớp `unchanged`. SHA-256 v3: urban `4a86d3ab…d539`, total `0c91cc6c…b7a4`, excluded `ba34ecc6…564e`.

## 3. Ca kiểm thử trên dữ liệu thật (v3, mã phân loại sản phẩm + OSRM, hai lớp)

| Ca | Kết quả | Nghiệm thu |
|---|---|---|
| Phenikaa → La Phù | URBAN 2b, 5,977 km — PASS | NOT_VERIFIED |
| ~3 km TP Hưng Yên | UNSUPPORTED 3b — PASS | NOT_VERIFIED |
| Đệm 14,992 / 15,321 km | URBAN / INTERCITY — PASS | NOT_VERIFIED |
| Giới hạn 149,984 / 150,024 km | INTERCITY / OUT_OF_SERVICE_AREA (lớp 2) — PASS | NOT_VERIFIED |
| Đông Anh → Hoàn Kiếm | **INTERCITY 19,678 km — FAIL so với Mục 2.3** | NOT_VERIFIED |
| An Khánh (Splendora) / Tùng Thiện / Phố Hiến → Hoàn Kiếm | URBAN 2a / INTERCITY 47,4 km / INTERCITY 56,4 km — PASS | NOT_VERIFIED |
| Điểm trong polygon > 150 km / xa đường / trong EXCLUDED | OUT_OF_SERVICE_AREA (lớp 2 / lớp 2 / lớp 1) — PASS | NOT_VERIFIED |
| Mẫu 400 điểm trong vùng chấp nhận | phục vụ 263, NO_ROAD_ACCESS 118, > 150 km 19 | — |

## 4. Kiểm chứng nguồn hành chính (GEO-06)

Đọc trực tiếp từ PDF gốc trên cổng Chính phủ: QĐ 19/2025/QĐ-TTg (MD5 `13C91AB4…796C`, Phụ lục II trang 6–10) và NQ 1656/NQ-UBTVQH15 (MD5 `E256FF94…5B6B`). Toàn bộ mã/khoản dùng ở v2/v3 trùng khớp. Còn thứ cấp: hình học (OSM), ranh giới lịch sử (OSM), vị trí Splendora (website chủ đầu tư, báo chí). Chi tiết: `service_area/OFFICIAL_SOURCE_VERIFICATION.md`.

## 5. Khảo sát S1

Bảng kịch bản 44 dòng (`survey/SURVEY_S1_SCENARIO_TABLE.md`): `OWNER_DECIDED` 31, `PENDING_OWNER_APPROVAL` 9, `NOT_ACTIVE_PROPOSAL` 4. **Chờ duyệt:** phương pháp hiệu chỉnh ETA 6 km (ô tô 19 / xe máy 16 phút; OSRM thô 9 / 10), đi vòng tối đa 6 km (6 phút), câu chữ "khả năng đủ khách", thiết kế ghép 1B, khoảng D2–D4, ngưỡng QC2 120 s. Các mức biến thiên giá ngoài d = 0,25: `EXPERIMENT_REVIEW_REQUIRED`, không hiển thị.
HTTPS / công khai: **chưa triển khai** — thiếu domain, quyền máy chủ, bộ câu hỏi cuối được duyệt, thời hạn lưu trữ. Caddyfile `caddy validate` hợp lệ; overlay compose hợp lệ; diễn tập backup/restore PASS. **Không phải `SURVEY_S1_RELEASED`**; DB chính 0 câu trả lời.

## 6. Kiểm thử (DIRECTLY_VERIFIED, 2026-10-27)

| Bộ | Kết quả |
|---|---|
| Backend pytest | **124 passed, 0 failed, 0 skipped** (architecture 2, config 4, driver 6, health 2, identity 11, official units 3, routing 7, schema 24, service-area versioning 7, survey 15, trip API 19, trip rules 24) |
| Migration | DB chính `0002 → 0003 → 0004`; CSDL tạm: head → downgrade `0002` → head → `alembic check` không lệch; CSDL tạm đã xóa |
| Smoke check P0 (`--restart-test`) | **18/18 PASS** — `evidence/p0_smoke_check_p1_final.json` |
| Ca biên địa lý | Đúng 150 km nhận / 150,001 từ chối; snap 300 / 300,1 m; không tuyến từ anchor; pickup→dropoff không tuyến; NoSegment; OSRM sập (503, không fallback); điểm trong EXCLUDED; phiên bản thiếu lớp 2 (503) |
| Phiên bản / bằng chứng | Version tất định; `ST_Equals` ổn định; lớp EXCLUDED rỗng ổn định; quy tắc điểm mẫu; không ghi đè bundle đã tồn tại |
| Khảo sát | Ẩn danh, quota đóng nhóm, rate limit (fake + Redis thật: `[True, True, False]`, khóa không chứa địa chỉ), start token giả mạo, QC2, tách TEST/RESEARCH, toàn vẹn export, xóa theo yêu cầu, tham số nghiên cứu ngoài `pricing_configs` |
| Backup / restore | Diễn tập trên 2 CSDL tạm: 3 người / 30 câu trả lời khôi phục giống hệt (hash nội dung `06fa654a…`) |

## 7. Sự cố trong phiên (đã khắc phục)

- `service-area-build` dùng ảnh Docker riêng 41 giờ tuổi → lần build v3 đầu chạy mã cũ (0 đơn vị nội đô); đã dừng trước khi ghi DB, xác nhận DB không có phiên bản rác; nay dùng chung tag `ridesharing-backend:local`.
- Truy vấn thành phần của lần chạy lỗi giữ CPU DB ~40 phút làm bộ test chậm (token 15 phút hết hạn → 1 test 401); chạy lại sau khi dừng: toàn bộ PASS.
- Chẩn đoán khoảng hở vòng ranh giới lịch sử ban đầu trả `None`; đã sửa và tạo lại bundle v3 (trước khi rà soát; hình học `unchanged`).

## 8. Tệp thay đổi (sau commit `552f414`)

- **Mới:** `config/service_area_rules.candidate.v3.yaml`, `config/official/hanoi_units_qd19_nq1656.csv`; `scripts/osm/export_historic_boundaries.sh`; `scripts/survey/{backup_survey,restore_survey,backup_restore_drill}.sh`, `drill.py`, `scenario_table.py`; `infra/survey/{Caddyfile,docker-compose.survey.yml}`; `backend/alembic/versions/0003_*.py`, `0004_*.py`; `backend/app/modules/ml_models/{survey_guard,survey_derive}.py`; `backend/tests/test_official_units.py`; bundle `service_area/sa-cand-7da7fbe2e01b/`, `COMPARE_*_vs_sa-cand-7da7fbe2e01b.md`, `GEOMETRY_REVIEW_P1_FINAL_CLOSURE.md`, `OFFICIAL_SOURCE_VERIFICATION.md`; `survey/SURVEY_S1_SCENARIO_TABLE.md`, `SURVEY_S1_DEPLOYMENT_PLAN.md`, `survey/evidence/s1_6km_eta_osrm.json`; `survey/s1/{scenario_table.csv,PRIVACY_NOTICE.draft.md}`; `evidence/p0_smoke_check_p1_final.json`.
- **Sửa:** `backend/app/modules/{routing/service,trip/{rules,service,api,models,boundary_eval,service_area_build},ml_models/{models,survey_api,survey_service,survey_schemas,survey_design,static/survey_s1.html}}.py`, `app/core/settings.py`; tests `test_trip_api`, `test_routing`, `test_service_area_versioning`, `test_survey_s1`; `survey/s1/questionnaire.draft.yaml` (draft 2); `docker-compose.yml`; `README.md`; tài liệu `SPEC_FINDINGS_P1.md`, `P1_DESIGN_DECISIONS.md`, `SURVEY_S1_DESIGN_REVIEW.md`, báo cáo này.

## 9. Tiêu chí đóng P1

| Tiêu chí (Mục 79 + chỉ thị) | Trạng thái |
|---|---|
| Schema + ràng buộc bắt buộc | ĐẠT |
| Identity + Driver/KYC mock | ĐẠT |
| Trip Intent phân loại đúng mọi ca biên **trên hình học đã phê duyệt** | **CHƯA** — `sa-cand-7da7fbe2e01b` chưa được phê duyệt; Đông Anh trái Mục 2.3 (SF-P1-14); SF-P1-15/16/17/20 cần quyết định |
| Khảo sát S1 phát hành và bắt đầu thu thập | **CHƯA** — 9 dòng chờ duyệt; chưa có domain / máy chủ |
| Không còn blocker P1 | **CHƯA** |
| `PHASE_1_COMPLETION_REPORT.md` | **Không tạo** |
