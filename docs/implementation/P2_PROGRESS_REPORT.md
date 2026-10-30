# PHASE 2 — BÁO CÁO TIẾN ĐỘ (chưa phải báo cáo hoàn thành P2)

- **Ngày:** 2026-10-29
- **Căn cứ:**
  - Kế hoạch: `P2_IMPLEMENTATION_PLAN.md`.
  - Diễn giải đặc tả: `SPEC_FINDINGS_P2.md` (SF-P2-01..15).
  - P2 bắt đầu theo ngoại lệ "DEVELOPMENT FIRST": `P1_LOCAL_HANDOFF_REPORT.md`.
- **Trạng thái P2: `PHASE_2_IN_PROGRESS`.**
  - Ràng buộc cứng: `LOCAL_VERIFIED` (0 vi phạm).
  - Độ trễ < 300 ms: **chưa đạt** ở cấu hình 20 kế hoạch ghép mở (§4).
  - SF-06 vẫn **OPEN**.
  - Revision 9 và Baseline không bị sửa; SLA và khối lượng công việc không bị giảm.

## 1. Đã hiện thực

| Hạng mục | Nội dung | Trạng thái |
|---|---|---|
| **P2.1 Routing** | `routing/provider.py` (`RoutingProvider.route` / `matrix`, profile `car` / `motorbike`). `routing/osrm.py`: 1 request `/table` cho mỗi ma trận (gửi tọa độ phân biệt một lần, `sources` / `destinations`, `annotations=distance,duration`, `exclude=ferry` theo chính sách vùng); vượt `--max-table-size` → `MatrixTooLarge`, không cắt bớt. Lỗi tường minh: `RouteNotFound`, `RoutingUnavailable`, `RoutingTimeout`; ô null = không có đường; không fallback đường chim bay. `routing/cache.py`: Redis theo khóa §34 `(policy, profile, geohash7, geohash7, time_bucket)`, chỉ cho `route()` (OD-P2-02); Redis lỗi → gọi OSRM | IMPLEMENTATION_COMPLETE · LOCAL_VERIFIED |
| Migration `0005` | Bổ sung kỹ thuật: `driver_locations.availability` / `active_vehicle_id`, `ride_stops`, `candidate_runs`, cột kiểm toán của `ride_candidates`, `ride_participants.direct_distance_m` / `direct_duration_s`. CSDL tạm head → base → head + `alembic check` sạch; CSDL chính đã lên `0005` (chỉ thêm) | LOCAL_VERIFIED |
| **P2.2 Ràng buộc cứng** | `candidate/constraints.py`: đúng 11 mã HC01–HC11 (test khóa danh sách), áp cho **mọi** khách của chuỗi điểm dừng. Không có đường tắt: ứng viên chỉ được tạo khi `check_all` rỗng. Lớp AI (`ml_models`) bị test kiến trúc cấm import ràng buộc / thuật toán chèn (R9 §43 nguyên tắc 1) | IMPLEMENTATION_COMPLETE · LOCAL_VERIFIED |
| Sinh ứng viên | `candidate/generator.py`:<br>• PostGIS `ST_DWithin` trên geography + `&&` bbox cho chỉ mục GIST, `R_urban` 5 km, top `N_single` 15.<br>• Xe máy, bao xe, ghép nhánh B; ghép nhánh A: kế hoạch mở trong `R_pool`, lọc hướng / ghế, top `N_pool` 20.<br>• **1 lệnh table cho mỗi profile, chạy song song** (OD-P2-01).<br>• Mọi ứng viên đi qua thuật toán chèn §36 (xe mới = chèn vào kế hoạch rỗng).<br>• Giá cho RB 8: BikeFare / PrivateFare / Quote / Unmatched đọc `pricing_configs` của `pricing_version` Baseline.<br>• `candidate/service.py` ghi `candidate_runs` (chính sách, thời gian từng giai đoạn, số lượng, loại bỏ theo mã RB) + `ride_candidates` — nhật ký sự kiện cho P6–P8 | IMPLEMENTATION_COMPLETE · LOCAL_VERIFIED |
| **P2.3 Pooling §36** | `pooling/insertion.py`:<br>• chỉ chèn sau `S_curr`; điểm dừng đã hoàn thành bị đóng băng;<br>• `traveled_km` + quãng còn lại cho khách đang trên xe;<br>• dừng 60 s; chờ tới `T_earliest`;<br>• bước 1 `k_max` / `max_additional_pickups` → bước 2 tải ghế theo đoạn → bước 3 đủ 11 RB cho mọi khách → bước 4–5 qua hook `PoolPricingCheck` (P3) → bước 6 `ΔCost` nhỏ nhất.<br>`pooling/repository.py` đọc kế hoạch / điểm dừng / người tham gia | IMPLEMENTATION_COMPLETE · LOCAL_VERIFIED (bước 4–5 thuộc P3: `PENDING_P3`) |
| API | `PUT /api/driver/availability`; `POST /api/admin/candidates/runs`; `GET /api/admin/candidates/runs/{id}` (ADMIN) | LOCAL_VERIFIED |

## 2. Kiểm thử

| Bộ | Kết quả |
|---|---|
| Toàn bộ backend pytest | **203 passed, 0 failed** (lượt chạy đủ bộ). Sau đó thêm test kiến trúc thứ 3 (AI không với tới ràng buộc): 3/3 pass khi chạy riêng → **204 test** |
| `test_routing_provider.py` (16) | Đúng 1 request / ma trận, tọa độ trùng gửi một lần, ô null, `NoRoute` / `NoSegment` / 5xx / timeout / lỗi mạng / JSON hỏng, ma trận vượt giới hạn bị từ chối (không gọi OSRM), geohash chuẩn, khóa cache đổi theo chính sách / profile / graph, Redis thật (hit / miss / TTL; ma trận không cache), Redis hỏng → vẫn định tuyến. OSRM thật 2 profile: `matrix` khớp `route` từng cặp (≤ 1 m / 1 s) |
| `test_candidate_constraints.py` (24) | Mỗi RB: vi phạm và **đúng biên** (đi vòng đúng 0,30, thời gian ngồi xe đúng ngưỡng, đón đúng `T_latest`, giá đúng `B_max`, đi vòng tài xế đúng ngưỡng) |
| `test_pooling_insertion.py` (19) | Xe đang chạy không chèn trước `S_curr`. `k_max`, số đón thêm. Tải ghế theo đoạn. Khách cũ vi phạm → loại phương án. RB 11 chỉ trên đoạn chồng lấp. **10.000 kịch bản ngẫu nhiên có seed** so với bộ tham chiếu độc lập (`tests/p2_reference.py`): 0 vi phạm, và phương án chọn luôn rẻ nhất so với duyệt vét cạn. 1.945 kịch bản khả thi; 395 có khách đang trên xe; 208 có ≥ 2 khách cũ |
| `test_candidate_generation.py` (5) | CSDL tạm + OSRM thật:<br>• lọc PostGIS (ngoại tuyến, vị trí cũ, ngoài 5 km bị loại);<br>• 2 request OSRM / lượt;<br>• giá khớp công thức R9 tính từ `route()` độc lập;<br>• RB 8 loại bao xe / ghép khi `B_max` = 100.000 đ;<br>• nhánh A chèn vào xe đang chạy, khách cũ được kiểm lại, `PENDING_P3`;<br>• OSRM sập → 503 `ROUTING_UNAVAILABLE` + lượt chạy được ghi, 0 ứng viên;<br>• API ADMIN + tài xế bật trực tuyến qua API |
| Smoke P0 | 17/17 PASS (`evidence/p0_smoke_check_p2_progress.json`). Lần chạy đầu ngay sau khi container backend khởi động lại được 16/17; tệp bằng chứng của lần đó đã bị ghi đè nên không còn biết mục nào lỗi |

## 3. Kiểm chứng "0 vi phạm" (P2.4, `scripts/p2_benchmark.py`)

**Bộ kiểm chứng độc lập.** Bộ này không dùng mã của generator. Với mỗi ứng viên:
- Gọi OSRM `/route` theo đúng chuỗi điểm dừng, mỗi chặng độc lập (`continue_straight=false` — đúng ngữ nghĩa bảng của R9; xem SF-P2-15).
- Tính lại từ CSDL: cửa sổ đón, ngưỡng, giá, sức chứa, trạng thái tài xế.
- Kiểm HC01–HC09.

**Phạm vi chưa kiểm độc lập:**
- HC07 phần ngưỡng đi vòng của tài xế: dữ liệu benchmark không đặt ngưỡng này.
- HC10 và HC11: benchmark không bật đi bộ và không bật cùng giới.

Các mục này đã được kiểm trong `test_pooling_insertion.py`.

| Cấu hình (tài xế × kế hoạch mở) | Ứng viên khả thi | Vi phạm | Sát biên trong dung sai |
|---|---|---|---|
| 50 × 0 | 4.507 | **0** | 0 |
| 200 × 0 | 9.949 | **0** | 0 |
| 1.000 × 0 | 10.735 | **0** | 0 |
| 200 × 10 | 10.105 | **0** | 0 |
| 200 × 20 | 10.272 | **0** | 0 |
| 1.000 × 20 | 10.543 | **0** | 0 |

**Tổng: 56.111 ứng viên, 0 vi phạm.** Lần chạy đầu bộ kiểm chứng dùng `/route` mặc định và báo 6 lệch RB 5. Lệch này đến từ việc không quay đầu được tại điểm đón, không phải lỗi thuật toán; đã ghi thành rủi ro mô hình SF-P2-15.

## 4. Độ trễ (P2.4) — đo trong mạng compose

Đo bên trong container backend → `osrm-*` / `postgres`, 4 vCPU WSL2 trên Windows. Mỗi cấu hình 200 yêu cầu synthetic, có seed.

Từ máy Windows qua port proxy của Docker Desktop, mỗi kết nối mới mất ~1 s nên **không** dùng để đo. Lượt đo đó đã bị dừng và bỏ.

| Cấu hình | Tổng sinh ứng viên p50 / p95 / p99 (ms) | PostGIS + OSRM p95 | PostGIS p95 | OSRM car p95 | Ràng buộc + chèn p95 | p95 < 300 ms |
|---|---|---|---|---|---|---|
| 50 × 0 | 76 / 160 / 255 | 128 | 35 | 86 | 38 | **ĐẠT** |
| 200 × 0 | 92 / 201 / 261 | 139 | 32 | 102 | 59 | **ĐẠT** |
| 1.000 × 0 | 103 / 230 / 358 | 180 | 59 | 105 | 50 | **ĐẠT** |
| 200 × 10 | 133 / 242 / 328 | 175 | 69 | 102 | 51 | **ĐẠT** |
| 200 × 20 | 163 / **516** / 634 | 360 | 120 | 217 | 102 | **KHÔNG ĐẠT** |
| 1.000 × 20 | 165 / **331** / 529 | 276 | 133 | 138 | 75 | **KHÔNG ĐẠT** |

- Mọi lượt dùng đúng **2 request OSRM** (1 / profile); 0 lệnh `route()` trong vòng chèn.
- Bằng chứng: `evidence/p2_benchmark.json`, dữ liệu SYNTHETIC trên máy local.
- Hiệu năng trên máy chủ thật: `EXTERNAL_VALIDATION_DEFERRED`.

**Kết luận đo:** tiêu chí §79 P2 "< 300 ms" **chưa đạt** khi có 20 kế hoạch ghép mở. Ma trận vuông `car` lúc đó tới ~190 điểm. Không được trình bày là đã đạt.

**Điểm nóng theo profiling giai đoạn** (để tối ưu tiếp, không giảm N / k / SLA):
1. OSRM table vuông ~190 điểm: p95 138–217 ms. Gắn với SF-06.
2. Giai đoạn PostGIS khi có kế hoạch: p95 120–133 ms. Gồm 6–7 truy vấn tuần tự (xe máy, ô tô, ô tô ghép, kế hoạch mở, snapshot tài xế, 3 truy vấn kế hoạch); cần `EXPLAIN ANALYZE` và gộp truy vấn.
3. Vòng chèn Python: p95 75–102 ms. Dựng `datetime` / dataclass cho từng phương án; cần profile hàm.

## 5. Còn lại của P2

1. **Tối ưu theo profiling cho cấu hình 20 kế hoạch** (mục 4).
   - Không giảm `N_single` / `N_pool` / `k_max`, không nới SLA.
   - Nếu sau tối ưu vẫn không đạt, báo cáo kèm hồ sơ profiling để Chủ dự án quyết định.
2. Chủ dự án xem xét các quyết định mở OD-P2-01..07 và diễn giải SF-P2-01..15.
3. `P2_COMPLETION_REPORT` chỉ lập khi cả 2 tiêu chí §79 đạt ở môi trường local.

## 6. Ghi chú vận hành

- `scripts/p2_benchmark.py` chạy trong mạng compose:
  ```sh
  MSYS_NO_PATHCONV=1 docker compose run --rm --no-deps -v "$(pwd -W):/repo" backend python -I /repo/scripts/p2_benchmark.py --in-network
  ```
  Script tạo và xóa CSDL tạm `p2_bench`.
- `alembic.ini` có `prepend_sys_path = .`, nên script gắn gói `app` vào bản checkout trước khi migrate.
