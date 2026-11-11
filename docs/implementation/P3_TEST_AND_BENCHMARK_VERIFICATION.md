# PHASE 3 — TEST & BENCHMARK VERIFICATION REPORT

**Dự án:** Ride_Sharing  
**Commit kiểm chứng:** `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`  
**Ngày lập báo cáo:** 2026-11-09  
**Nguyên tắc phân loại:** Tách bạch tuyệt đối giữa **(1) Kiểm thử thực thi mới trong phiên kiểm toán hiện tại**, **(2) Kiểm thử chưa thực thi lại được do thiếu môi trường trên máy hiện tại (`NOT_EXECUTED`)**, và **(3) Bằng chứng thực nghiệm lịch sử (`HISTORICAL_EVIDENCE_ONLY`)**.

---

## 1. Phân loại & Kết quả Thực thi Automated Tests

Tổng số file kiểm thử trong `backend/tests/`: **14 files** (cộng `conftest.py` và `p2_fixtures.py`).

### 1.1. Các bài kiểm thử ĐÃ CHẠY MỚI trong phiên kiểm toán hiện tại (Host Python 3.12.10)

Môi trường thực thi: `Python 3.12.10` (`C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe`), `PYTHONPATH=backend;backend/tests`.

| File kiểm thử | Số hàm test chạy mới | Số test cases (gồm parametrize) | Kết quả thực thi mới | Phạm vi kiểm chứng thực tế |
|---|---|---|---|---|
| `backend/tests/test_config_baseline.py` | `4 / 4` | `4` | **PASSED (4/4)** | Kiểm tra `config/mvp_config_baseline_v1.yaml` khớp từng byte với khối YAML trong `docs/pre/mvp_config_baseline_v1.md` (§4), khóa `MVP_CONFIG_BASELINE_V1` / `LOCKED_AND_APPROVED`, tính bất biến của `MappingProxyType`, và báo lỗi khi thiếu/sai phiên bản |
| `backend/tests/test_architecture.py` *(phần AST)* | `2 / 3` | `2` | **PASSED (2/2)** | `test_no_cross_module_model_imports` (duyệt AST toàn bộ `backend/app/modules/` đảm bảo không module nào import `models.py` của module khác) và `test_ai_modules_cannot_reach_the_hard_constraints` (đảm bảo `ml_models`/`simulator` không thể ghi đè ràng buộc cứng) |
| `backend/tests/test_pricing_regression.py` | `13 / 13` | `13` | **PASSED (13/13)** | Kiểm tra `money.py` (`q`, `floor_step`, `exact_vnd`, `NonIntegralAmount`, `to_numeric_2`, `to_rational_text`), báo giá và tất toán 4 dịch vụ (`BIKE_URBAN`, `CAR_URBAN_SINGLE`, `CAR_INTERCITY_PRIVATE`, `CAR_INTERCITY_POOL`), kiểm tra dải giá ghế `[0.90, 1.10] * p_seat_ref`, phụ phí đón tận nơi (`<= 10km`), và quy tắc `AUTO_CONFIRM` / `SUGGEST_MERGE` / `TOP_UP` |
| `backend/tests/test_pricing_pool.py` | `22 / 22` | `31` | **PASSED (31/31)** | Kiểm tra thuật toán `allocate_two_sided`, `price_new_plan`, `price_insertion`, `final_price_at_lock`: kiểm chứng D1 (co-riding), Gate 1 (`C_plan <= sum(P_i)`), `SeatFactor(1)=1.0`, `SeatFactor(2)=1.35` chỉ áp vào `w_i` và `Floor_i` (`D-45b`), biên giá `[0.40 * P_i * SeatFactor, 0.80 * P_i]`, `on_lower_bound_infeasible="REJECT"`, Gate 2A & 2B tính **sau làm tròn** (`D-45a`), bảo vệ nhóm đóng băng $F$ và không tăng giá nhóm mở $U$ khi chèn động (`D-44`), và phát hiện xung đột `SF-P3-16` đối với báo giá 2 ghế không ghép được |
| `backend/tests/test_pricing_cancellation.py` | `7 / 7` | `17` | **PASSED (17/17)** | Kiểm tra toàn bộ ma trận phí hủy chuyến và vắng mặt (`NO_SHOW`) theo `D-52` cho cả 5 dịch vụ, miễn phí khi `DRIVER`/`SYSTEM` hủy, miễn phí trong 120s ân hạn đô thị, trần 20.000đ cho chuyến đơn đô thị, chia 85% tài xế / 15% Quỹ bảo đảm cho phí hủy chuyến ghép đô thị, và các mốc 72h / 24h / 2h của liên tỉnh |
| **TỔNG CỘNG (CHẠY MỚI)** | **48 hàm test** | **67 test cases** | **100% PASSED (`0` FAILED)** | Toàn bộ lõi toán học định giá, phân bổ tiền, khóa giá, phí hủy, cấu hình baseline và ranh giới AST kiến trúc đã được xác minh trực tiếp trên mã nguồn hiện tại |

---

### 1.2. Các bài kiểm thử CHƯA THỰC THI LẠI trên máy hiện tại (`NOT_EXECUTED`) & Bằng chứng lịch sử (`HISTORICAL_EVIDENCE_ONLY`)

Do máy Windows hiện tại không cài đặt `docker`, `wsl`, `postgresql`/`postgis`, `redis`, `osrm`, `sqlalchemy`, và `hypothesis`, các bài test tích hợp dưới đây được ghi nhận đúng nguyên tắc là **`NOT_EXECUTED` trong phiên hiện tại**, kèm trạng thái từ bằng chứng lịch sử tại commit `f97a509` (`docs/implementation/P3_PROGRESS_REPORT.md` và `docs/implementation/evidence/`):

| File kiểm thử | Số hàm test trong code | Trạng thái phiên hiện tại | Lý do kỹ thuật chưa chạy lại | Kết quả trong bằng chứng lịch sử (`HISTORICAL_EVIDENCE_ONLY`) | Nội dung kiểm chứng trong code test |
|---|---|---|---|---|---|
| `backend/tests/test_architecture.py::test_every_table_is_owned_by_exactly_one_module` | `1` | `NOT_EXECUTED` | Cần package `sqlalchemy` để nạp `app.db.models.metadata` | PASSED (trong tổng 135 passed tại `P3_PROGRESS_REPORT.md`) | Kiểm tra mọi bảng trong `metadata.tables` thuộc đúng 1 module duy nhất |
| `backend/tests/test_pricing_properties.py` | `6` | `NOT_EXECUTED` | Cần package `hypothesis` (`from hypothesis import given, settings, strategies as st`) | PASSED (6/6 hàm Hypothesis × 300 examples/hàm = 1.800 ngẫu nhiên sinh mẫu) | Kiểm chứng bất biến bằng Property-Based Testing: bảo toàn tổng tiền trước/sau làm tròn, tôn trọng biên `[Floor_i, Cap_i]`, tính đơn điệu theo trọng số $w_i$, tính bất biến của nhóm $F$ và không tăng giá nhóm $U$, Gate 1 & Gate 2A/2B, và bảo toàn hạch toán `driver + platform + fund == fare_charged + subsidy` |
| `backend/tests/test_fund_and_price_protection.py` | `12` | `NOT_EXECUTED` | Cần PostgreSQL + Alembic migrations `0001`–`0006` + `sqlalchemy` | PASSED (12/12 hàm trên PostgreSQL 16.4) | Kiểm chứng seed `pricing_configs` bất biến, seed Quỹ 5.000.000đ, chuỗi số dư `fund_ledger`, đối soát `reconcile()`, hạch toán chuyến ghép thành công / không ghép được (`NO_MATCH_FOUND` vs `PASSENGER_SELF_RESTRICTED`) / hủy chuyến, và kiểm chứng 4 DB triggers (`trg_fund_ledger_guard`, `trg_driver_payouts_immutable`, `trg_ride_participants_frozen`, `trg_bookings_locked_pool_price`) |
| `backend/tests/test_candidate_generation.py` | `20` | `NOT_EXECUTED` | Cần PostgreSQL/PostGIS + OSRM (`osrm-car`, `osrm-motorbike`) + Redis | PASSED (20/20 hàm trên Docker Compose stack) | Kiểm chứng sinh ứng viên đơn & ghép xe, đầy đủ 11 ràng buộc cứng (HC01–HC11), tích hợp định giá Phase 3 (lọc phương án vi phạm Gate 1/Gate 2/D1–D6), chọn phương án $(p, q)$ khả thi về giá có $\Delta D$ nhỏ nhất, và lưu trữ kết quả vào `candidate_runs` / `ride_candidates` |
| `backend/tests/test_osrm_provider.py` | `11` | `NOT_EXECUTED` | Cần `httpx` + OSRM containers | PASSED (11/11) | Kiểm chứng `OsrmRoutingProvider` (`nearest`, `route`, `matrix`, chunking `> 200`, `Connection: close`, xử lý lỗi và điểm ngoài vùng phủ) |
| `backend/tests/test_routing_cache.py` | `5` | `NOT_EXECUTED` | Cần `redis` + `sqlalchemy` | PASSED (5/5) | Kiểm chứng `CachedRoutingProvider` chỉ cache `route()` không có waypoints theo `geohash7`, không bao giờ cache `matrix()`, và tự động fallback khi Redis lỗi |
| `backend/tests/test_schema.py` | `11` | `NOT_EXECUTED` | Cần PostgreSQL/PostGIS + Alembic | PASSED (11/11) | Kiểm chứng 24 bảng ORM khớp 100% với migrations, kiểm tra `CHECK` constraints, partial unique index và trigger bất biến `pricing_configs` |
| `backend/tests/test_identity_and_driver.py` | `11` | `NOT_EXECUTED` | Cần `fastapi`, `sqlalchemy`, PostgreSQL | PASSED (11/11) | Kiểm chứng đăng ký, đăng nhập, refresh token rotation, RBAC, hồ sơ tài xế, đăng ký xe, duyệt KYC, cập nhật vị trí & trạng thái sẵn sàng |
| `backend/tests/test_trip_classification.py` | `10` | `NOT_EXECUTED` | Cần PostgreSQL/PostGIS + OSRM | PASSED (10/10) | Kiểm chứng phân loại vùng chuyến đi (`URBAN`, `INTERCITY`, `OUT_OF_ZONE`) theo `service_areas` |
| `backend/tests/test_survey_s1.py` | `12` | `NOT_EXECUTED` | Cần `fastapi`, `sqlalchemy`, PostgreSQL | PASSED (12/12) | Kiểm chứng Survey S1 (6 kịch bản SP, aandacht check, chống nộp trùng, xuất CSV ẩn danh, rút lui `WITHDRAWN`, khóa `RESEARCH`) |
| `backend/tests/test_health.py` | `3` | `NOT_EXECUTED` | Cần Docker Compose stack | PASSED (3/3) | Kiểm chứng `/health/live` và `/health/ready` |

---

## 2. Xác minh Bằng chứng Thực nghiệm & Benchmark Lịch sử (`HISTORICAL_EVIDENCE_ONLY`)

Tất cả các thư mục bằng chứng trong `docs/implementation/evidence/p3_runs/` và `docs/implementation/evidence/p0_smoke_check_p3_20261105.json` đã được đọc trực tiếp và xác minh tính toàn vẹn:

### 2.1. Danh sách 7 thư mục chạy thực nghiệm trong `docs/implementation/evidence/p3_runs/`

| Run ID | Mục đích / Giai đoạn tối ưu | Ghi chú kỹ thuật từ hồ sơ chạy |
|---|---|---|
| `20261104T180929Z-p3-integrated-a1` | Đo baseline tích hợp Phase 2 + Phase 3 lần 1 | Phát hiện chi phí đọc `plan_pricing_state` theo từng chuyến mở |
| `20261104T181309Z-p3-integrated-a2` | Đo tích hợp lần 2 | Kiểm tra phân rã từng stage (`plan_pricing_state`, `insertion_pool_plans`, `osrm_car`) |
| `20261104T185050Z-p3-integrated-a3` | Sau khi gộp truy vấn `plan_pricing_states` thành 1 câu SQL `WHERE ride_plan_id = ANY(:pids)` | Giảm thời gian đọc trạng thái giá chuyến mở xuống ~7–10 ms ở cấu hình 20 chuyến mở |
| `20261105T053415Z-p3-integrated-a4` | **Lượt chuẩn 1 (Clean Run A4)** trên code cuối cùng (`f97a509`) | 7 cấu hình × 200 requests = 1.400 lượt sinh ứng viên |
| `20261105T053903Z-p3-integrated-a5` | **Lượt chuẩn 2 (Clean Run A5)** trên code cuối cùng (`f97a509`) | 7 cấu hình × 200 requests = 1.400 lượt sinh ứng viên |
| `20261105T054312Z-p3-integrated-a6` | **Lượt chuẩn 3 (Clean Run A6)** trên code cuối cùng (`f97a509`) | 7 cấu hình × 200 requests = 1.400 lượt sinh ứng viên |
| `20261105T054653Z-p3-integrated-verify` | **Lượt kiểm chứng độc lập (`--verify`)** (`63.988` ứng viên được hậu kiểm độc lập) | Có file `LATENCY_DISTURBED.md` ghi nhận máy host bị suspend từ `06:15:20Z` → `06:48:01Z` (nên không dùng số đo độ trễ của lượt `verify`, nhưng kết quả hậu kiểm toán học & OSRM `/route` độc lập hoàn toàn hợp lệ) |

### 2.2. Bảng Tổng hợp Độ trễ Sinh Ứng Viên Tích hợp Định giá Phase 3 (3 lượt chạy sạch `a4`, `a5`, `a6` — `HISTORICAL_EVIDENCE_ONLY`)

Chỉ tiêu Đặc tả Revision 9:
- **Mục 77:** Lọc không gian PostGIS + Gọi 1 ma trận OSRM Table: `p95 <= 300 ms`
- **Mục 79 (P2/P3):** Tổng độ trễ sinh ứng viên (`generation_total_ms` trước lưu DB, bao gồm cả kiểm tra định giá Phase 3): `p95 < 300 ms`

| Cấu hình (`drivers x open_plans`) | Số request / lượt | `postgis_plus_osrm_table` `p95` (ms) [A4 / A5 / A6] | `generation_total_ms` `p50` (ms) [A4 / A5 / A6] | `generation_total_ms` `p95` (ms) [A4 / A5 / A6] | `generation_plus_persist_ms` `p95` (ms) [A4 / A5 / A6] | `insertion_pool_plans` `p95` (ms) [A4 / A5 / A6] | Đạt mục tiêu `p95 < 300 ms`? |
|---|---|---|---|---|---|---|---|
| **`50x0`** (50 tài xế, 0 chuyến mở) | 200 | `55.91 / 33.72 / 40.97` | `32.59 / 27.07 / 26.73` | **`63.66 / 44.37 / 50.86`** | `122.25 / 108.12 / 103.27` | `0.00 / 0.00 / 0.00` | **PASS** (cả 3 lượt) |
| **`200x0`** (200 tài xế, 0 chuyến mở) | 200 | `54.15 / 46.37 / 66.21` | `41.68 / 37.99 / 40.36` | **`75.82 / 70.32 / 104.60`** | `206.24 / 175.12 / 290.08` | `0.00 / 0.00 / 0.00` | **PASS** (cả 3 lượt) |
| **`1000x0`** (1000 tài xế, 0 chuyến mở) | 200 | `69.12 / 62.09 / 46.17` | `50.43 / 46.52 / 36.68` | **`93.76 / 84.23 / 57.50`** | `218.87 / 205.08 / 148.83` | `0.00 / 0.00 / 0.00` | **PASS** (cả 3 lượt) |
| **`200x10`** (200 tài xế, 10 chuyến mở) | 200 | `85.89 / 83.95 / 61.00` | `73.45 / 69.67 / 56.44` | **`115.38 / 117.64 / 84.31`** | `229.64 / 254.20 / 173.44` | `4.45 / 5.57 / 2.58` | **PASS** (cả 3 lượt) |
| **`200x20`** (200 tài xế, 20 chuyến mở) | 200 | `98.73 / 88.37 / 69.76` | `82.20 / 80.28 / 63.61` | **`140.37 / 129.12 / 97.18`** | `242.45 / 232.69 / 192.92` | `7.86 / 7.98 / 4.23` | **PASS** (cả 3 lượt) |
| **`1000x20`** (1000 tài xế, 20 chuyến mở) | 200 | `110.38 / 111.57 / 80.88` | `88.70 / 88.83 / 67.56` | **`150.78 / 162.78 / 109.76`** | `271.51 / 255.30 / 182.75` | `9.82 / 8.76 / 4.50` | **PASS** (cả 3 lượt) |
| **`200x20-hc`** (200 tài xế, 20 chuyến mở — tải căng ràng buộc) | 200 | `85.92 / 75.28 / 56.43` | `68.55 / 66.72 / 54.50` | **`121.03 / 111.23 / 78.59`** | `238.19 / 218.11 / 158.78` | `6.47 / 5.40 / 3.28` | **PASS** (cả 3 lượt) |

### 2.3. Kết quả Hậu kiểm Độc lập (`20261105T054653Z-p3-integrated-verify/result.json` — `HISTORICAL_EVIDENCE_ONLY`)

Trong lượt chạy `--verify`, bộ kiểm tra độc lập `scripts/p2_verify.py` đã kiểm tra lại từng ứng viên được sinh ra bằng truy vấn SQL độc lập và gọi trực tiếp OSRM `/route` theo chuỗi điểm dừng:

| Cấu hình | `candidates_checked` | `with_violation` (Vi phạm HC01–HC11 hoặc Định giá P3) | `pending_p3` / `pending_p3_offerable` | `single_rejections.correct` | `plan_checks.correct` | `plan_checks.rejected_by_pricing_gates` |
|---|---|---|---|---|---|---|
| `50x0` | `4.507` | **`0`** | `0 / 0` | `388` | `0` | `0` |
| `200x0` | `9.949` | **`0`** | `0 / 0` | `440` | `0` | `0` |
| `1000x0` | `10.735` | **`0`** | `0 / 0` | `218` | `0` | `0` |
| `200x10` | `10.038` | **`0`** | `0 / 0` | `493` | `567` | `67` |
| `200x20` | `10.009` | **`0`** | `0 / 0` | `491` | `997` | `263` |
| `1000x20` | `10.298` | **`0`** | `0 / 0` | `333` | `1.068` | `245` |
| `200x20-hc` | `9.162` | **`0`** | `0 / 0` | `1.352` | `413` | `247` |
| **TỔNG CỘNG** | **`64.698`** | **`0` vi phạm** | **`0 / 0`** | **`3.715`** | **`3.045`** | **`822`** |

*(Ghi chú: Tổng số ứng viên được kiểm chứng trong `verify/result.json` qua 7 cấu hình là `4507 + 9949 + 10735 + 10038 + 10009 + 10298 + 9162 = 64.698` ứng viên, với `with_violation = 0` và `pending_p3 = 0` trên toàn bộ 7 cấu hình).*

