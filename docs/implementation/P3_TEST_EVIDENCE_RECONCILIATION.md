# ĐỐI SOÁT BẰNG CHỨNG KIỂM THỬ VÀ BENCHMARK PHASE 3 (TEST & BENCHMARK EVIDENCE RECONCILIATION)

- **Repository Root**: `C:\RideSharing`
- **Commit HEAD**: `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`
- **Môi trường hiện tại**: Windows host, Python 3.12.10 (không có Docker daemon chạy trực tiếp trên shell host, thiếu các gói C-extension `psycopg`, `geoalchemy2`, `fastapi`, `httpx`).

---

## 1. Đối soát Số lượng Bài kiểm thử (Reconciling Test Counts: 210 vs 291 vs 135)

### 1.1. Thực tế trong Codebase tại Commit HEAD

Khi phân tích cú pháp AST trực tiếp trên toàn bộ 23 file kiểm thử trong `backend/tests/`:
- **Tổng số file test**: **`23` files `test_*.py`** (cùng 4 file hỗ trợ: `api_helpers.py`, `conftest.py`, `p2_fixtures.py`, `p2_reference.py`).
- **Tổng số hàm `def test_*` định nghĩa trong mã nguồn**: **`210` hàm kiểm thử**.
- **Tổng số test items thu thập bởi `pytest` (`pytest collection`)**: **`291` test items** (`290` ca thông thường + `1` ca kiểm thử bất biến Hypothesis trên 10.000 mẫu ngẫu nhiên).

### 1.2. Giải trình Toán học về việc Mở rộng Parametrize: `210 + 81 = 291`

Sự chênh lệch giữa 210 hàm định nghĩa và 291 test items của pytest xuất phát từ chính xác **81 lượt mở rộng tham số hóa (`@pytest.mark.parametrize`)**:

| File kiểm thử | Tên hàm kiểm thử có `@pytest.mark.parametrize` | Số ca cơ sở | Số ca mở rộng sau tham số hóa | Số ca tăng thêm |
|---|---|---|---|---|
| `test_candidate_constraints.py` | `test_each_violation` | 1 | 20 kịch bản vi phạm (`HC01`–`HC10`) | +19 |
| `test_candidate_windows.py` | `test_scheduled_pickup_never_before_the_chosen_time` | 1 | 3 dịch vụ nội đô (`BIKE`, `PRIVATE`, `POOL`) | +2 |
| `test_pooling_insertion.py` | `test_random_insertions_have_zero_violations_and_are_optimal` | 1 | 10 khối hạt giống (10.000 mẫu ngẫu nhiên) | +9 |
| `test_pooling_insertion.py` | `test_insertion_reads_only_stop_destinations` | 1 | 3 khối hạt giống (3.000 mẫu ma trận chữ nhật) | +2 |
| `test_pricing_cancellation.py` | `test_urban_single` | 1 | 2 dịch vụ (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`) | +1 |
| `test_pricing_cancellation.py` | `test_driver_or_system_cancellation_is_free_everywhere` | 1 | 10 tổ hợp (5 dịch vụ × 2 chủ thể `DRIVER`/`SYSTEM`) | +9 |
| `test_pricing_pool.py` | `test_out_of_domain_parameters_are_refused` | 1 | 10 tham số vi phạm miền giá trị | +9 |
| `test_routing.py` | `test_no_route_is_explicit` | 1 | 2 mã lỗi OSRM (`NoRoute`, `NoSegment`) | +1 |
| `test_routing_provider.py` | `test_osrm_errors_are_explicit` | 1 | 5 mã phản hồi HTTP/lỗi OSRM | +4 |
| `test_routing_provider.py` | `test_real_matrix_matches_pairwise_routes` | 1 | 2 profiles (`CAR`, `MOTORBIKE`) | +1 |
| `test_schema.py` | `test_required_index_exists` | 1 | 8 chỉ mục bắt buộc theo Mục 56.2 | +7 |
| `test_schema.py` | `test_pricing_configs_are_immutable` | 1 | 3 câu lệnh (`UPDATE`, `DELETE`, `TRUNCATE`) | +2 |
| `test_service_area_versioning.py` | `test_classification_refuses_retired_or_unapproved` | 1 | 2 trạng thái (`RETIRED`, `CANDIDATE`) | +1 |
| `test_survey_pilot.py` | `test_pilot_matrix_d_is_estimable_from_exported_test_data` | 1 | 3 biến thể ma trận (`D`, `D_bal`, `D2`) | +2 |
| `test_trip_api.py` | `test_buffer_boundary_through_api` | 1 | 2 cự ly biên (`15.0 km`, `15.01 km`) | +1 |
| `test_trip_api.py` | `test_tier2_road_limit_exactly_150_accepted_beyond_rejected` | 1 | 4 cự ly biên (`149.98`, `150.0`, `150.001`, `150.02`) | +3 |
| `test_trip_api.py` | `test_tier2_snap_distance_limit` | 1 | 2 khoảng cách snap (`300.0 m`, `300.1 m`) | +1 |
| `test_trip_rules.py` | `test_step1_outside_total_area` | 1 | 3 tổ hợp ngoài vùng | +2 |
| `test_trip_rules.py` | `test_buffer_boundary_is_inclusive_at_15_km` | 1 | 2 tổ hợp biên 15 km | +1 |
| `test_trip_rules.py` | `test_preference_filters` | 1 | 5 bộ lọc phương tiện/loại chuyến | +4 |
| **Tổng cộng các ca tham số hóa** | | **20 hàm** | **101 ca kiểm thử** | **+81 ca** |

$$\text{Tổng số test items của pytest} = 210\text{ (hàm cơ sở)} + 81\text{ (mở rộng)} = \mathbf{291\text{ items}}$$

Con số này **khớp chính xác 100%** với biên bản nghiệm thu trước đây ghi trong `docs/implementation/P3_PROGRESS_REPORT.md:40`:
> *"Toàn bộ test (P1 + P2 + P3): 290 passed + test Hypothesis 1 passed (chạy riêng 99 s) = **291 passed, 0 failed**."*

### 1.3. Nguyên nhân xuất hiện con số "135 passed" trong Báo cáo Phiên trước

Trong phiên làm việc trước, sau khi cửa sổ ngữ cảnh bị nén, tác tử đã chạy một script runner tùy biến chỉ tìm nạp các hàm có tham số rỗng hoặc `['p']`, `['car']`, `['tmp_path']` mà bỏ qua toàn bộ các hàm kiểm thử tích hợp yêu cầu fixtures phức tạp (`world`, `db_session`, `client`), đồng thời đếm sót các hàm AST, dẫn đến việc bịa ra con số `135 tests passed`.

---

## 2. Kết quả Thực thi Kiểm thử Mới trong Phiên Hiện tại (Executed Now)

Do máy chủ Windows host hiện tại không cài đặt các thư viện phụ thuộc C/PostGIS (`psycopg`, `geoalchemy2`) và không có Docker chạy trực tiếp ngoài terminal sandbox, toàn bộ các bộ kiểm thử thuần thuật toán Python (Pure Python) đã được chạy kiểm chứng độc lập ngay trong phiên này:

| File kiểm thử | Số hàm định nghĩa | Số ca chạy thực tế (sau mở rộng) | Trạng thái thực thi trong phiên này | Nội dung kiểm chứng |
|---|---|---|---|---|
| `test_config_baseline.py` | 4 | 4 | **PASSED (100%)** | Khớp từng dòng giữa `config/mvp_config_baseline_v1.yaml` và `docs/pre/mvp_config_baseline_v1.md`, cơ chế chống drift cấu hình, đóng băng thuộc tính read-only. |
| `test_pricing_regression.py` | 13 | 13 | **PASSED (100%)** | Khớp từng xu các vector hồi quy cố định: Vector 1 (16.1 & 17), Vector 2 (18.4 & 18.5), Vector 3A, 3B, 3C (16.2), Vector 4 (16.3), Vector 72.1, 10.4, 19.2, 28.3, và kiểm tra dải giá vé liên tỉnh. |
| `test_pricing_pool.py` | 22 | 31 | **PASSED (100%)** | Khớp các bất biến số học `Fraction`, điều kiện khả thi $F1, F2, F3$, kẹp hai đầu cùng lúc, biên Cổng 1, biên Cổng 2A & 2B, hệ 6 điều kiện chèn động $D1$–$D6$, đóng băng nhóm $L$, nhóm $U$ không tăng giá, từ chối tham số ngoài miền hợp lệ. |
| `test_pricing_cancellation.py` | 7 | 17 | **PASSED (100%)** | Chính sách phí hủy & No-Show 5 dịch vụ theo Mục 18.7 và Phụ lục B, các mốc biên thời gian 120s, 2h, 72h, 24h, bảo toàn `fee + refund == deposit`. |
| `test_pooling_insertion.py` | 11 | 22 | **PASSED (100%)** | Kiểm chứng 11 ràng buộc cứng trên thuật toán chèn động `insert()` so với bộ giải vét cạn độc lập `tests/p2_reference.py` trên 10.000 kịch bản ngẫu nhiên và chứng minh tính hợp lệ của ma trận OSRM chữ nhật. |
| `test_architecture.py` | 2 | 2 | **PASSED (100%)** | Kiểm tra ranh giới AST giữa các module: `0` cross-module model imports, `0` mô-đun AI vi phạm ranh giới tiếp cận trực tiếp 11 ràng buộc cứng. |
| `test_pricing_properties.py` | 1 | 1 | **PASSED (100%)** | **10.000 mẫu ngẫu nhiên Hypothesis** (2–4 bookings, 2–30 km, $s_i \in \{1, 2\}$, đi vòng, đi bộ): nghiệm phân bổ kẹp hai đầu khớp 100% với bộ giải độc lập active-set enumeration, $0$ vi phạm bất biến 1–7. |

**Tổng số kiểm thử đã thực thi và PASS 100% ngay trong phiên hiện tại**:
- **59 hàm định nghĩa** $\to$ **89 test cases mở rộng** + **10.000 ví dụ kiểm thử bất biến ngẫu nhiên**.

---

## 3. Bằng chứng Lịch sử đối với các Bài kiểm thử CSDL và Môi trường Tích hợp (Historical Evidence Only)

Các bài kiểm thử còn lại (151 hàm định nghĩa / 202 test items) yêu cầu môi trường tích hợp đầy đủ (PostgreSQL/PostGIS, Redis, 2 container OSRM):
- `test_fund_and_price_protection.py` (8 defs): Kiểm tra các triggers CSDL bất biến, chuỗi số dư advisory lock, chống âm Quỹ, chống sửa giá đã khóa.
- `test_schema.py` (15 defs / 24 items): Kiểm tra migration 0001–0006 upgrade/downgrade/re-upgrade, 8 partial indexes, trigger bất biến `pricing_configs`.
- `test_identity.py` (11 defs), `test_driver.py` (6 defs), `test_trip_api.py` (18 defs / 27 items), `test_candidate_generation.py` (8 defs), `test_routing.py` (7 defs / 8 items), `test_routing_provider.py` (12 defs / 17 items), `test_survey_s1.py` (20 defs), `test_survey_pilot.py` (1 def / 3 items), `test_service_area_versioning.py` (6 defs / 7 items), `test_health.py` (2 defs).

Trạng thái: **`HISTORICAL_EVIDENCE_ONLY`** (đã được ghi nhận đạt `291 passed, 0 failed` tại `docs/implementation/P3_PROGRESS_REPORT.md:40` khi chạy trên môi trường có đầy đủ Docker compose containers).

---

## 4. Bằng chứng Hiệu năng và Benchmark (Benchmark Evidence)

Dữ liệu benchmark lịch sử được thực hiện độc lập tại mốc hoàn thiện P3 (ghi nhận tại `docs/implementation/P3_PROGRESS_REPORT.md:62-95`) trên 3 lượt kiểm thử liên tiếp ($a_4, a_5, a_6$) với tải 200 yêu cầu sinh ứng viên đồng thời:

| Phạm vi đo lường (Latency Scopes) | Mục tiêu SLA (Revision 9 Mục 77 / 79) | Kết quả đo thực tế (p95 qua 3 lượt $a_4 / a_5 / a_6$) | Đánh giá |
|---|---|---|---|
| **Scope 1: PostGIS + OSRM Table** | $p95 \le 300\text{ ms}$ | `54,1 ms / 46,4 ms / 66,2 ms` | **ĐẠT XUẤT SẮC** (nhanh gấp 4.5 lần trần SLA) |
| **Scope 2: Toàn bộ quá trình sinh ứng viên (trước khi lưu DB)** | $p95 \le 300\text{ ms}$ | `75,8 ms / 70,3 ms / 104,6 ms` | **ĐẠT** ($104,6\text{ ms} < 300\text{ ms}$) |
| **Scope 3: Sinh ứng viên + Ghi nhận Audit CSDL (`candidate_runs` & `ride_candidates`)** | $p95 \le 800\text{ ms}$ (E2E) | `206,2 ms / 175,1 ms / 290,1 ms` (p99 cao nhất 217 ms) | **ĐẠT** ($290,1\text{ ms} \ll 800\text{ ms}$) |

**Chi phí tính toán bổ sung của Phase 3**:
- Pha tra cứu trạng thái định giá của kế hoạch đang mở (`plan_pricing_state`): tiêu tốn `10–19 ms` $p95$ (đọc 2 truy vấn CSDL và snapshot booking).
- Thuật toán phân bổ điểm gãy hai cận và kiểm tra Cổng 2 trên bộ nhớ tiêu tốn `< 1 ms` cho mỗi ứng viên.

