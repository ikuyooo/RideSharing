# PHASE 1 — BÁO CÁO TIẾN ĐỘ (chưa phải báo cáo hoàn thành)

- **Cập nhật:** 2026-10-26 (sau quyết định "P1: GEOGRAPHY & S1 CLOSURE"). **Trạng thái P1: `IN_PROGRESS`.**
- `PHASE_1_COMPLETION_REPORT.md` **chưa được tạo** — tiêu chí P1 (Mục 79) chưa đạt đủ (mục 7).
- Giữ nguyên: `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`; SF-06 = OPEN; Revision 9 và Baseline v1 không bị sửa.
- Quy ước: **DIRECTLY_VERIFIED** = đã chạy trong phiên; **OWNER_DECISION** = quyết định của Chủ dự án; **CANDIDATE** = chưa phê duyệt.

## 1. Quyết định đã thực hiện được

| Mã | Kết quả | Trạng thái |
|---|---|---|
| A1 | Bảng ánh xạ hành chính có mã QĐ 19/2025, khoản NQ 1656, quan hệ OSM, mức chắc chắn; kiểm chứng chéo 126 đơn vị Hà Nội (51 phường + 75 xã) khớp OSM | Đã làm — cần đối chiếu PDF chính thức |
| A2 | An Khánh = polygon khu đô thị OSM (U3); La Phù ngoài nội đô; Phenikaa → La Phù URBAN qua nhánh 2b | Đạt trên ứng viên; ranh giới La Phù lịch sử `PENDING_GEOMETRY_EVIDENCE` |
| A3 | Mỹ Đình (HIGH), Gia Lâm (MEDIUM) giải quyết; Đông Anh PENDING | Một phần |
| A4 | Điểm gốc xác minh đủ 6 bước; phát hiện 79 đơn vị chỉ một phần ở đúng phía ngưỡng | Đã làm; cần quyết định SF-P1-12 |
| A5 | Phạm vi mọi tỉnh, mức xã/phường | Đã áp dụng (ứng viên) |
| A6 | Phân loại 332 + 7 thành phần, không sửa hình học | Đã làm; cần quyết định SF-P1-13 |
| A7 | Mặc định detour 0,30 + test | **Hoàn tất** |
| A8 | Phố Hiến làm điểm đại diện ứng viên | Đã dùng; không phải ánh xạ chính thức |
| A9 | Giữ bbox; loại 2.045 đơn vị ngoài vùng định tuyến, có lý do | Đã làm |
| D | Commit local `9d5befe` (mốc P1 đã kiểm chứng); không push; `c4051ed` không đổi | Đã làm |

## 2. Hình học ứng viên mới

**`sa-cand-acce13159a8c`** — CANDIDATE, không GEOMETRY_APPROVED. Bundle: `docs/implementation/service_area/sa-cand-acce13159a8c/`
(urban.geojson, total.geojson, units.csv, excluded_units.csv, admin_mapping.csv, components.csv, sensitivity_150km.csv,
routing_coverage.csv, report.json, REVIEW.md, CHECKSUMS.sha256, TRIP_CLASSIFICATION_EVAL.md).

| | v1 `sa-cand-3873dfbee116` | v2 `sa-cand-acce13159a8c` |
|---|---|---|
| Nội đô | 511,166 km², 2 thành phần | 484,116 km², 7 thành phần |
| Vùng tổng | 26.349,323 km², 222 thành phần | 38.618,767 km², 332 thành phần |
| Điểm đổi trạng thái (4.888 node `place=*`) | — | 11 rời nội đô, 372 vào vùng tổng, 0 rời vùng tổng |
| SHA-256 urban / total GeoJSON | — | `d3e27cdc…f232f` / `115295ba…52609` |

Import lại 2 lần: cùng version, `unchanged (ST_Equals)`. So sánh đầy đủ: `COMPARE_sa-cand-3873dfbee116_vs_sa-cand-acce13159a8c.md`.
v1 giữ nguyên CANDIDATE và mọi bằng chứng gốc (lần đánh giá lại ghi ra file riêng `TRIP_CLASSIFICATION_REEVAL_P1_CLOSURE.md`).

## 3. Ca biên địa lý (Mục 72.2 + Mục 2.3) — trên `sa-cand-acce13159a8c`

Nguồn tọa độ: đối tượng OSM trong export (ways/relations dùng `ST_PointOnSurface`); cặp biên 15 km / 150 km chọn tất định từ node `place=*`.

| Ca | R9 § | Nguồn tọa độ | Expected | Actual | Nhánh | Kết quả trên ứng viên | Nghiệm thu |
|---|---|---|---|---|---|---|---|
| Phenikaa → La Phù (5,977 km) | 72.2 | way/973433275 → node/12147486706 | URBAN | URBAN | 2b | PASS | NOT_VERIFIED |
| ~3 km trong TP Hưng Yên (2,589 km) | 72.2 | node/13155709564 → node/11518465547 | UNSUPPORTED_INTER_PROVINCE_ROUTE | UNSUPPORTED_INTER_PROVINCE_ROUTE | 3b | PASS | NOT_VERIFIED |
| Vùng đệm ≤ 15 km (14,992 km) | 2.3 | way/973433275 → node/12607118252 | URBAN | URBAN | 2b | PASS | NOT_VERIFIED |
| Vùng đệm > 15 km (15,321 km) | 2.3 | way/973433275 → node/12611713598 | INTERCITY | INTERCITY | 3a | PASS | NOT_VERIFIED |
| Giới hạn ≤ 150 km (149,984 km) | 2.3 / Baseline | node/74132064 → node/11578421390 | INTERCITY | INTERCITY | 3a | PASS | NOT_VERIFIED |
| Giới hạn > 150 km (150,024 km) | 2.3 / Baseline | node/74132064 → node/6766268697 | OUT_OF_SERVICE_AREA | OUT_OF_SERVICE_AREA | 1 | PASS | NOT_VERIFIED |
| 71 h 59 / 72 h 00 / 7 ngày / 12 h | 72.2 | (thời gian, không địa lý) | theo Mục 6 | đúng | — | PASS (`test_trip_rules.py`) | DIRECTLY_VERIFIED |

"Nghiệm thu = NOT_VERIFIED" vì hình học chưa được phê duyệt. Trên v1, ca La Phù đi nhánh 2a và ca ≤ 150 km FAIL (Tứ Quận ngoài danh sách tỉnh đóng).

## 4. Mâu thuẫn địa lý

**Đã xử lý (trên ứng viên):** SF-P1-01 (ánh xạ), SF-P1-02 (La Phù ngoài nội đô qua U3), SF-P1-03 (Mỹ Đình), SF-P1-04 Gia Lâm, SF-P1-06 (phạm vi), SF-P1-08 (detour), SF-P1-10 (bbox).

**Chưa xử lý / cần quyết định:**
- Đông Anh (SF-P1-04): thị trấn cũ chia 3 xã; node thị trấn ở Phúc Thịnh.
- Ranh giới La Phù lịch sử: không có hình học (`PENDING_GEOMETRY_EVIDENCE`); Splendora = Bắc An Khánh là giả định.
- SF-P1-11: Phường Tùng Thiện (Sơn Tây cũ) vào nội đô do quy tắc "mọi phường".
- SF-P1-12: chọn theo điểm đại diện → 47 đơn vị được chọn có phần > 150 km, 32 đơn vị bị loại có phần ≤ 150 km.
- SF-P1-13: 312 mảnh đảo không đường (29,4 km²) trong vùng tổng.
- SF-P1-09: Phố Hiến chỉ là điểm đại diện; quãng đường thực 58,1 km so với 65 km minh họa.
- Nội dung NQ 1656 / mã QĐ 19 cần đối chiếu văn bản chính thức.

## 5. Khảo sát S1

Bảng 8 điểm và đề xuất phát hành: `docs/implementation/survey/SURVEY_S1_DESIGN_REVIEW.md` §9–§11. Còn chờ phê duyệt: phương pháp 6 km, giá ghép 14 km (143k/145k), biến thiên giá độc lập, cách thể hiện đi bộ 200 m, mức "khả năng đủ khách", khoảng D2–D4, ngưỡng QC2/QC5, cỡ mẫu + kênh + nơi triển khai + thời hạn lưu trữ.
Bản nháp dev đã có (biểu mẫu + API + export + quota, dataset TEST, 0 dữ liệu trên DB chính). **Chưa phát hành — không phải `SURVEY_S1_RELEASED`.**

## 6. File thay đổi (sau commit `9d5befe`)

- **Mới:** `config/service_area_rules.candidate.v2.yaml`; `backend/app/modules/trip/service_area_compare.py`; `backend/app/modules/ml_models/{__init__,models,survey_design,survey_schemas,survey_service,survey_api}.py`, `static/survey_s1.html`; `backend/alembic/versions/0002_p1_survey_s1_draft_storage.py`; `backend/tests/{test_service_area_versioning,test_survey_s1}.py`; bundle `docs/implementation/service_area/sa-cand-acce13159a8c/`, `COMPARE_…md`, `sa-cand-3873dfbee116/TRIP_CLASSIFICATION_REEVAL_P1_CLOSURE.{md,json}`; `docs/implementation/evidence/p0_smoke_check_p1_closure.json`.
- **Sửa:** `backend/app/modules/trip/{service_area_build,boundary_eval,rules,service,schemas}.py`; `backend/app/core/{settings,logging}.py`; `backend/app/{main,db/models}.py`; `backend/pyproject.toml`; `backend/tests/{conftest,test_schema,test_trip_api}.py`; `scripts/osm/export_service_area_sources.sh`; `docker-compose.yml`; `.env.example`; `README.md`; tài liệu `SPEC_FINDINGS_P1.md`, `P1_DESIGN_DECISIONS.md`, `SURVEY_S1_DESIGN_REVIEW.md`, báo cáo này.

## 7. Kiểm thử (DIRECTLY_VERIFIED)

| Bộ | Kết quả |
|---|---|
| Backend pytest | **103 tests: 103 passed, 0 failed, 0 skipped** (architecture 2, config 4, driver 6, health 2, identity 11, routing 5, schema 24, service-area versioning 4, survey 9, trip API 12, trip rules 24) |
| Migration | DB trống → head; downgrade → upgrade; `alembic check`; DB chính `0001 → 0002` |
| Ràng buộc schema 56.2 | 24 test (trong `test_schema.py`) PASS |
| Phân loại chuyến / vùng đệm / 150 km | Logic + API PASS; dữ liệu thật trên ứng viên 6/6 PASS (mục 3) |
| Phiên bản service area | version tất định, `unchanged (ST_Equals)`, chặn đổi hình học, chặn RETIRED/chưa duyệt |
| Bảo mật / ẩn danh | token, RBAC, sở hữu đối tượng, không log tọa độ, không log IP khảo sát, không cột định danh trong bảng khảo sát |
| Smoke check P0 (`--restart-test`) | **18/18 PASS** — `evidence/p0_smoke_check_p1_closure.json` |

## 8. Blocker cuối cùng trước khi đóng P1

| Tiêu chí P1 (Mục 79 + chỉ thị) | Trạng thái |
|---|---|
| Schema + ràng buộc bắt buộc | ĐẠT |
| Identity + Driver/KYC mock | ĐẠT |
| Trip Intent phân loại đúng mọi ca biên **đã phê duyệt** | **CHƯA** — cần phê duyệt hình học (`sa-cand-acce13159a8c` hoặc bản sửa) sau khi quyết định Đông Anh, SF-P1-11, SF-P1-12, SF-P1-13 |
| Khảo sát S1 phát hành và bắt đầu thu thập | **CHƯA** — cần duyệt 8 điểm nội dung + hạ tầng công khai |
| Không còn blocker P1 | **CHƯA** — hai mục trên |
| `PHASE_1_COMPLETION_REPORT.md` | Chưa tạo |
