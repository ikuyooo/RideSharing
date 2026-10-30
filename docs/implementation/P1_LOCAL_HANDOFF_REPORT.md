# P1 — BÁO CÁO BÀN GIAO LOCAL (không phải báo cáo hoàn thành P1)

- **Ngày:** 2026-10-29
- **Căn cứ:** quyết định "OWNER STRATEGIC DECISION — RIDE_SHARING DEVELOPMENT FIRST, DEPLOYMENT LATER".
- **Ngoại lệ tiến độ do Chủ dự án phê duyệt:** hoàn thiện dự án trên môi trường local trước. Hoãn:
  - domain, VPS và HTTPS công khai;
  - phát hành S1 công khai và thu dữ liệu thật.
- Revision 9 và MVP_CONFIG_BASELINE_V1 **không bị sửa**.
- Phát hiện đặc tả: SF-P1-27, SF-P1-28. Cách hiện thực quyết định: `P1_DESIGN_DECISIONS.md` §7.
- **Kết luận:**
  - Phần lập trình P1 đạt `IMPLEMENTATION_COMPLETE` + `LOCAL_VERIFIED`.
  - P1 **không** đạt `FORMAL_PHASE_ACCEPTANCE` theo R9 §79, vì "link Khảo sát S1 bắt đầu thu thập dữ liệu" chưa diễn ra. P1 **không** được gán COMPLETE.
  - Theo ngoại lệ, lập trình P2 được bắt đầu (kế hoạch: `P2_IMPLEMENTATION_PLAN.md`).

## 1. Bốn loại trạng thái dùng trong báo cáo

| Trạng thái | Nghĩa |
|---|---|
| `IMPLEMENTATION_COMPLETE` | Mã nguồn, cấu hình, migration và tài liệu đã xong |
| `LOCAL_VERIFIED` | Đã kiểm chứng trên stack local bằng test hoặc bằng chứng tái lập được (ghi rõ lệnh và tệp) |
| `EXTERNAL_VALIDATION_DEFERRED` | Cần hạ tầng công khai, người dùng thật hoặc dữ liệu thật. Đã hoãn theo ngoại lệ; **chưa thực hiện và không được trình bày là đã đạt** |
| `FORMAL_PHASE_ACCEPTANCE` | Đạt nguyên văn tiêu chí nghiệm thu của R9 §79 |

## 2. Hạng mục và trạng thái

| # | Hạng mục (R9 §79 P1) | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1 | Schema CSDL, ràng buộc / chỉ mục §56.2 | IMPLEMENTATION_COMPLETE · LOCAL_VERIFIED | Migration head `0004`; `test_schema.py` (24); CSDL tạm head → base → head + `alembic check` (vòng trước, chưa có migration mới) |
| 2 | `identity` (đăng ký, đăng nhập, refresh, RBAC) | IMPLEMENTATION_COMPLETE · LOCAL_VERIFIED | `test_identity.py` (11) |
| 3 | `driver` + KYC mock S7 | IMPLEMENTATION_COMPLETE · LOCAL_VERIFIED | `test_driver.py` (6); ràng buộc `kyc_gates_pool_and_intercity` |
| 4 | `trip`: phân loại URBAN / INTERCITY, vùng đệm 15 km, luật thời gian đặt, `allowed_service_codes` | IMPLEMENTATION_COMPLETE · LOCAL_VERIFIED · **FORMAL_PHASE_ACCEPTANCE (vế 1 của §79: 100% ca biên)** | `test_trip_rules.py` (24), `test_trip_api.py` (23). Hình học v5 `sa-cand-0d5347b4294e` = `GEOMETRY_APPROVED_FOR_MVP`: 8/8 cổng, 15/15 ca nghiệm thu, đánh giá lại sau phê duyệt PASS. Giữ snap 300 m, 150 km theo OSRM car, không đi phà |
| 5 | Địa giới hành chính | LOCAL_VERIFIED (phạm vi MVP học thuật) | `OFFICIAL_SOURCE_VERIFICATION.md`, `test_official_units.py` (5). **Không phải** chứng nhận pháp lý. Rủi ro Đông Anh: `GEOMETRY_REVIEW_P1_HARDENING.md` §10 |
| 6 | Bộ câu hỏi S1 draft 5: D2, MNL gọn, R1–R4 | IMPLEMENTATION_COMPLETE · LOCAL_VERIFIED | `questionnaire.draft.yaml`; `test_survey_s1.py` (20); pilot TEST D / D_bal / D2 `test_survey_pilot.py` (3); `evidence/s1_design_diagnostics.json` |
| 7 | Chuỗi khảo sát local đầy đủ: form → API → DB → export → ước lượng | LOCAL_VERIFIED (**dữ liệu synthetic**) | `scripts/survey/local_e2e.sh` PASS; `survey/evidence/s1_local_e2e.json` (§3) |
| 8 | HTTPS / quyền riêng tư (cấu hình Caddy, log không IP, CSP / HSTS, giới hạn route) | IMPLEMENTATION_COMPLETE · LOCAL_VERIFIED (HTTPS local, CA nội bộ) · EXTERNAL_VALIDATION_DEFERRED (domain thật) | `staging_e2e.sh` PASS (vòng 2026-10-28) |
| 9 | Backup / restore / purge | LOCAL_VERIFIED (CSDL tạm) | `backup_restore_drill.sh`, `purge_survey.sh` |
| 10 | Thông báo đồng ý chính thức, thời hạn lưu trữ 12 tháng, đầu mối liên hệ | Bản nháp (`PRIVACY_NOTICE.draft.md`) · **chờ Chủ dự án duyệt trước khi phát hành** | Không chặn phát triển local |
| 11 | Phát hành S1 công khai (`SURVEY_S1_RELEASED`), QR, truy cập từ thiết bị ngoài | EXTERNAL_VALIDATION_DEFERRED | Chưa thực hiện |
| 12 | Thu dữ liệu RESEARCH thật, quota 150 (40–60%) trên dữ liệu thật | EXTERNAL_VALIDATION_DEFERRED | Chưa thực hiện; RESEARCH đang bị chặn (403 `SURVEY_NOT_RELEASED`) |
| 13 | Ước lượng MNL trên dữ liệu thật, hiệu chỉnh θ cho simulator | EXTERNAL_VALIDATION_DEFERRED | Phụ thuộc mục 12; ảnh hưởng P7 (SF-P1-28) |
| 14 | Tiêu chí §79 P1 "link Khảo sát S1 bắt đầu thu thập dữ liệu" | **FORMAL_PHASE_ACCEPTANCE: KHÔNG ĐẠT** | SF-P1-27 |

## 3. Chạy end-to-end khảo sát local (dữ liệu synthetic)

**Lệnh** (từ gốc repo, khi stack đang chạy):

```sh
MSYS_NO_PATHCONV=1 sh scripts/survey/local_e2e.sh <python có httpx>
```

**Môi trường chạy**
- Container backend riêng, uvicorn thật.
- Redis thật, database số 15.
- CSDL tạm `s1_local_e2e`, dataset TEST.
- Cả ba được xóa khi kết thúc.

**Dữ liệu và kết quả** (2026-10-29)

| Kiểm tra | Kết quả |
|---|---|
| Người trả lời synthetic | 150 người (75/75), lựa chọn mô phỏng từ prior giả định |
| Phiên bỏ dở | 16 |
| Lần nộp bị từ chối | 4 |
| Tỷ lệ hoàn thành (R1) | 0,9036 / 0,9036 |
| Bộ đếm 422 (R3) | `INVALID_START_TOKEN` 2, `REQUEST_VALIDATION` 2 |
| Export | Đủ 3 bảng; RESEARCH rỗng |
| MNL đầy đủ, ước lượng từ export | \|z\| lớn nhất so với prior mô phỏng 1,31; t(giá) −8,21; t(thời gian) −2,51 |
| MNL gọn (mô hình chính), ước lượng từ export | t(thời gian) −4,12 |
| CSDL tạm (completed / started) | 150 / 166 |
| CSDL chính | Không đổi |

**Giới hạn của lần chạy này**
- Giới hạn bắt đầu / nộp được nâng lên 1.000/giờ **chỉ cho lần chạy này**, vì mọi phiên đến từ một địa chỉ. Giá trị mặc định 60/giờ có test riêng.
- Các con số trên kiểm tra pipeline. **Không phải kết quả khảo sát** và không được trích dẫn như dữ liệu hành vi.

**Lưu ý:** CSDL chính có sẵn **1 phiên TEST** (`s1-draft-4`, nhóm STUDENT, 2026-10-28 16:24 UTC). Phiên này không do các kịch bản tự động tạo ra, nhiều khả năng từ lần chạy thử biểu mẫu thủ công. Đây không phải dữ liệu nghiên cứu. Dọn bằng `purge_survey.sh` trước khi phát hành, theo quyết định của Chủ dự án.

## 4. Hạng mục hoãn (EXTERNAL_VALIDATION_DEFERRED) và điều kiện để đóng P1 chính thức

1. Có domain hoặc subdomain và máy chủ. Khi đó mới chạy `SURVEY_S1_DEPLOYMENT_PLAN.md`: TLS hợp lệ, truy cập từ thiết bị ngoài, QR.
2. Chủ dự án duyệt thông báo đồng ý, thời hạn lưu trữ và đầu mối liên hệ.
3. Một phiên thử trên domain thật, không làm bẩn RESEARCH.
4. Dọn TEST, bật `SURVEY_DATASET=RESEARCH` và `SURVEY_S1_RELEASED=true`, rồi bắt đầu thu dữ liệu. Đến bước này P1 mới đạt `FORMAL_PHASE_ACCEPTANCE`.
5. Ước lượng MNL trên dữ liệu thật theo đặc tả gọn: R4 phân tích chính + phân tích độ nhạy.

Kế hoạch chi tiết `DEPLOYMENT_AND_EXTERNAL_VALIDATION_PLAN.md` sẽ được lập **sau khi** phần mềm local hoàn tất, theo quyết định của Chủ dự án. Không cần domain hay VPS để tiếp tục lập trình P2–P11.

## 5. Tách biệt TEST / RESEARCH và cam kết không giả mạo

- Dataset do cấu hình máy chủ quyết định, không do request: mặc định `TEST`.
- RESEARCH bị từ chối (403) cho đến khi phát hành; có test `test_research_dataset_blocked_until_release`.
- Giá thí nghiệm D2 chỉ nằm trong tệp câu hỏi, không ghi vào `pricing_configs`. Có test: chuỗi `survey` không xuất hiện trong seed giá; md5 `pricing_configs` không đổi trong pilot.
- Bằng chứng synthetic đều mang nhãn `SYNTHETIC TEST DATA`. Không tài liệu nào trình bày chúng là kết quả khảo sát.
- Hệ quả cho các phase sau:
  - P7 (simulator) chạy với θ giả định có nhãn cho đến khi có dữ liệu S1 thật (SF-P1-28).
  - Kiểm định H4 trên dữ liệu thật thuộc nhóm hoãn.

## 6. Những gì P2 dùng lại từ P1

| Thành phần | Giao diện |
|---|---|
| Trip Intent | `trip_requests`: `mode`, `allowed_service_codes`, `passenger_count`, `earliest/latest_departure`, `latest_arrival`, `budget_max`, `max_passenger_detour_ratio`, `max_in_vehicle_time_s`, `max_walk_m`, `categorical_preferences_json`, `direct_distance_km` |
| Vùng phục vụ | `trip.service.assess()` (lớp 1 PostGIS + lớp 2 OSRM: snap 300 m, anchor, 150 km, `exclude=ferry`); mã lỗi `OUT_OF_SERVICE_AREA`, `ROUTE_NOT_FOUND`, `ROUTING_UNAVAILABLE` (không fallback đường chim bay) |
| Định tuyến tối thiểu | `routing.service.OsrmCarDistance` (`/table` 1 lần cho khả năng tiếp cận, `/route` cho khoảng cách) → P2.1 thay bằng `RoutingProvider` đầy đủ |
| Tài xế | `driver_profiles` (KYC, `accepts_urban`, `pool_enabled`, `accepts_intercity`, `max_additional_pickups`, giới hạn đi vòng), `vehicles` (BIKE = 1, CAR4 = 4), `driver_locations` (GIST) |
| Giới tính xác thực (RB 11) | `users.gender` + `gender_verification_status` (giới tính tự khai không bao giờ thỏa RB 11) |
| Bảng P2 / P3 / P4 đã có schema | `ride_plans` (`completed_stop_index`, `plan_version`), `ride_participants`, `ride_candidates`, `bookings`, `seat_holds`, `idempotency_records` |

## 7. Kiểm thử tại thời điểm bàn giao (2026-10-29)

| Bộ | Kết quả |
|---|---|
| Backend pytest | **139 passed, 0 failed, 0 skipped**. Theo tệp: architecture 2, config 4, driver 6, health 2, identity 11, official units 5, routing 8, schema 24, service-area versioning 7, survey pilot 3, survey 20, trip API 23, trip rules 24 |
| E2E khảo sát local | PASS (§3) |
| Smoke check P0 `--restart-test` | **18/18 PASS** — `evidence/p0_smoke_check_p1_local_handoff.json` |
| Diagnostics thiết kế | Tái lập đúng số liệu cũ, chỉ đổi nhãn: D VIF 5,42, κ 151 / 241; D2 VIF 6,28, κ 98 / 115 |
| Rủi ro mở chuyển sang P2 | SF-06 (OSRM 100×100 chưa đạt < 50 ms) vẫn **OPEN** |
