# P2 — KẾ HOẠCH TRIỂN KHAI CHI TIẾT (routing · candidate · pooling · hiệu năng)

- **Ngày:** 2026-10-29
- **Căn cứ:**
  - R9 §79 P2: "Module `routing` (1 lệnh OSRM Table duy nhất), `candidate` (11 ràng buộc cứng cho xe máy & bao xe) và `pooling` (Mục 36)". Nghiệm thu: "`0` vi phạm ràng buộc cứng; độ trễ sinh ứng viên `< 300 ms`".
  - R9 §7, §34–36, §42, §43, §70 (G01, G02, G10, G13), §77.
  - Baseline v1.
  - Ngoại lệ "DEVELOPMENT FIRST" (`P1_LOCAL_HANDOFF_REPORT.md`).
- **Không đổi:**
  - Revision 9, Baseline, SLA.
  - SF-06 vẫn **OPEN**: không tuyên bố 100×100 < 50 ms.
  - Tối ưu chỉ dựa trên profiling, không giảm khối lượng công việc.

## 1. Những phần đã có

| Thành phần | Trạng thái |
|---|---|
| OSRM v5.27.1 CH, 2 container `osrm-car` / `osrm-motorbike` | Đang chạy. Profile xe máy không dùng `motorway` (smoke 18/18). `--max-table-size 200`. Graph hỗ trợ `exclude=ferry` |
| `routing.service.OsrmCarDistance` | Chỉ có car: `/table` khả năng tiếp cận (3 điểm), `/route` khoảng cách. Lỗi tường minh `RouteNotFound` / `RoutingUnavailable`, không fallback. Kết nối mới mỗi request (độ trễ keep-alive ~40 ms, phát hiện P0) |
| Vùng phục vụ v5 + lớp 2 (snap 300 m, 150 km, `exclude=ferry`) | `trip.service.assess()` |
| Trip Intent | `trip_requests`: `allowed_service_codes`, khung giờ, `budget_max`, giới hạn đi vòng / thời gian ngồi xe / đi bộ, `categorical_preferences_json` |
| Tài xế | `driver_profiles` (KYC, cờ nhận dịch vụ, `max_additional_pickups` 0–3, giới hạn đi vòng km / phút), `vehicles` (ràng buộc BIKE = 1, CAR4 = 4), `driver_locations` (GIST), `PUT /api/driver/location`, `PUT /api/driver/settings` |
| Giới tính xác thực | `users.gender` + `gender_verification_status` |
| Schema P2 / P4 | `ride_plans` (`status`, `completed_stop_index`, `plan_version`), `ride_participants` (`traveled_km_before_last_replan`, …), `ride_candidates` (`source_plan_version`, …), `bookings`, `seat_holds`, `idempotency_records` |
| Benchmark OSRM | `scripts/osrm_benchmark.py`. Bằng chứng SF-06: 100×100 p95 69,6–200,9 ms |

## 2. Những phần chưa có

1. `RoutingProvider` đầy đủ:
   - 2 profile;
   - `route()` (quãng đường / thời gian / snap) và `matrix()` (`/table` khoảng cách + thời gian, `sources` / `destinations`);
   - Redis cache theo chính sách;
   - xử lý timeout / mạng / `NoRoute` / `NoSegment` / bảng quá lớn.
2. Trạng thái trực tuyến / rảnh của tài xế (RB 1 "đang trực tuyến, trạng thái rảnh IDLE"). R9 §56.1 không có cột → **bổ sung kỹ thuật**.
3. `ride_stops`: R9 §54 liệt kê bảng nhưng không có cột → **bổ sung kỹ thuật**.
4. Thư viện 11 ràng buộc cứng; bộ sinh ứng viên `BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL` (nhánh A + B).
5. Thuật toán chèn §36 có nhận biết trạng thái xe.
6. Nhật ký phục vụ AI:
   - mỗi lượt sinh ứng viên;
   - ứng viên khả thi;
   - thống kê loại bỏ theo ràng buộc.
7. Benchmark theo giai đoạn: PostGIS, OSRM Table, kiểm ràng buộc, sinh ứng viên, toàn pipeline.

## 3. Cấu trúc module

Mỗi module chỉ gọi module khác qua interface công khai (D-31; `test_architecture.py` kiểm tra).

```text
backend/app/modules/
  routing/
    provider.py      RoutingProvider (Protocol): route(profile, origin, destination, waypoints=[]),
                     matrix(profile, sources, destinations); dataclass Route, Matrix (distance_m,
                     duration_s, snap_m nguồn/đích); Profile = CAR | MOTORBIKE; RoutingPolicy
                     (exclude=("ferry",), max_snap_m, routing_version)
    osrm.py          OsrmRoutingProvider (httpx; 1 request /table cho cả ma trận; annotations=distance,duration;
                     kiểm tra kích thước ≤ max-table-size; timeout → RoutingUnavailable; NoRoute/NoSegment →
                     RouteNotFound; ô null → "không có đường" trong ma trận, không ném lỗi)
    cache.py         CachedRoutingProvider: key (policy, profile, origin_geohash7, dest_geohash7, time_bucket)
                     theo R9 §34, giá trị (distance_m, duration_s); MGET / pipeline SETEX; lỗi Redis → bỏ qua cache
    service.py       giữ OsrmCarDistance cho trip (P1) - chuyển sang dùng OsrmRoutingProvider bên trong
  candidate/
    constraints.py   HC01…HC11: hàm thuần, đầu vào là snapshot bất biến, trả về Violation(code, subject, detail);
                     check_all() chạy đủ 11 mã; đăng ký cứng đúng 11 mã (test khóa danh sách)
    context.py       Snapshot: TripSnapshot, DriverSnapshot, VehicleSnapshot, PlanSnapshot (frozen dataclass)
    tariff.py        giá cố định cần cho RB 8: BikeFare, PrivateFare (§10.1, §12.1), Quote/Unmatched (§18.3) -
                     đọc tham số từ pricing_configs; P3 mở rộng (phân bổ, Cổng 1/2, D1-D6)
    spatial.py       truy vấn PostGIS (ST_DWithin trên geography + GIST), top-N theo haversine
    generator.py     single_vehicle (§35.1), pool_branch_a (qua pooling.insertion), pool_branch_b (§35.2 B);
                     gom tọa độ → 1 lệnh matrix cho mỗi profile
    service.py       generate(request_id) → CandidateRun; ghi ride_candidates + candidate_runs
    api.py           endpoint phát triển / kiểm thử (mục 4)
  pooling/
    plan_state.py    Stop, OnboardPassenger, PlanState (r = completed_stop_index, S_curr, traveled_km,
                     actual_pickup_time, plan_version)
    insertion.py     §36 thuần trên ma trận (D, T): chỉ chèn sau S_curr, dwell 60 s, k_max 8,
                     max_additional_pickups, RB 3/4/5/6/7/8/11 cho MỌI khách; trả InsertionResult | None + lý do
    pricing_hook.py  PoolPricingCheck (Protocol) cho bước 4-5 §36 (Cổng 1, D1-D6, phân bổ, Cổng 2) - P3 hiện thực
    repository.py    nạp PlanState từ ride_plans / ride_stops / ride_participants
```

**Migration `0005_p2_routing_candidate_pooling`** — chỉ có bổ sung kỹ thuật, có ghi chú:

- `driver_locations`:
  - thêm `availability` ∈ {`OFFLINE`, `IDLE`, `BUSY`}, mặc định `OFFLINE`;
  - thêm chỉ mục GIST trên `geography(geom)` nếu profiling cần.
- `ride_stops`: `id`, `ride_plan_id`, `seq`, `kind` (PICKUP / DROPOFF), `booking_id`, `geom`, `status` (PLANNED / COMPLETED / SKIPPED), `planned_eta`, `completed_at`.
  - `UNIQUE (ride_plan_id, seq)` DEFERRABLE.
- `candidate_runs`: `id`, `request_id`, `created_at`, `routing_policy`, `timings_json`, `counts_json`, `rejections_json`, `osrm_calls`.
- `ride_candidates` thêm:
  - `run_id`, `driver_id`, `vehicle_id`;
  - `pickup_eta_s`, `direct_distance_m`, `direct_duration_s`;
  - `insertion_json` (vị trí chèn, ETA, tải ghế theo đoạn);
  - `constraint_audit_json` (11 mã đã kiểm + giá trị biên).

## 4. Danh sách API

P2 không mở API gợi ý cho hành khách. `GET /api/trip-requests/{id}/recommendations` thuộc P6 (cần định giá P3 và xếp hạng). P2 chỉ mở các API sau:

| Endpoint | Quyền | Nguồn | Nội dung |
|---|---|---|---|
| `PUT /api/driver/availability` | DRIVER | Bổ sung kỹ thuật (R9 §57 không có) | Bật / tắt trực tuyến. Hệ thống chuyển IDLE / BUSY theo chuyến (P4) |
| `PUT /api/driver/location` | DRIVER | R9 §57 (đã có) | Cập nhật `updated_at`; vị trí quá hạn (> `location_stale_s`) bị loại khỏi RB 1 |
| `POST /api/admin/candidates/runs` `{request_id}` | ADMIN | Bổ sung kỹ thuật (kiểm thử / demo) | Chạy sinh ứng viên. Trả ứng viên khả thi, thống kê loại bỏ theo HC, thời gian từng giai đoạn |
| `GET /api/admin/candidates/runs/{run_id}` | ADMIN | Bổ sung kỹ thuật | Xem lại một lượt chạy (nhật ký cho AI và cho kiểm toán) |

Routing không có API công khai. Benchmark chạy bằng CLI `scripts/p2_benchmark.py`.

## 5. Thiết kế chính

### 5.1. Routing (P2.1)

- **Một lệnh Table cho mỗi lượt sinh ứng viên, theo từng profile.**
  - `car`: tài xế rảnh (bao xe + nhánh B) + điểm dừng chưa đi qua của ≤ 20 kế hoạch + P, Q (≤ ~100 điểm).
  - `motorbike`: tài xế xe máy + P, Q.
  - Hai lệnh chạy song song khi khách cho phép cả hai loại xe (OD-P2-01).
  - Trong vòng chèn §36, **không** gọi `route()` tuần tự: chỉ tra bảng O(1).
- **Chính sách định tuyến** của vùng phục vụ áp cho mọi request: `exclude=ferry`; snap > 300 m của P / Q bị loại từ P1.
- **Lỗi.** Không bao giờ fallback đường chim bay:
  - `RoutingUnavailable` (mạng, timeout, 5xx) → lượt chạy thất bại `ROUTING_UNAVAILABLE` (503).
  - `RouteNotFound` cho P→Q → `ROUTE_NOT_FOUND`.
  - Ô null trong ma trận → cặp tương ứng không có đường. RB 2 loại ứng viên đó, không loại cả lượt.
- **Cache.** Khóa theo R9 §34: `(policy hash, profile, geohash7 gốc, geohash7 đích, time_bucket)`.
  - OSRM hiện không có dữ liệu giao thông nên `time_bucket` = hằng số `static` cho đến khi có profile theo giờ.
  - `policy hash` gồm `routing_version` (dấu graph), `exclude`, profile. Đổi graph hoặc chính sách thì vô hiệu cache.
  - Phạm vi dùng cache là OD-P2-02.

### 5.2. Ràng buộc cứng (P2.2)

| Mã | Kiểm tra (đơn vị: m, s, VND) | Dịch vụ |
|---|---|---|
| HC01 | `availability = IDLE`, vị trí còn hạn, `vehicle.is_active`, đúng loại xe (BIKE ↔ `BIKE_URBAN`, CAR4 ↔ dịch vụ ô tô), cờ `accepts_urban` / `pool_enabled`. POOL / liên tỉnh: `kyc_status = VERIFIED` | tất cả |
| HC02 | Mọi chặng của chuỗi điểm dừng có đường trong ma trận đúng profile (xe máy dùng `motorbike`) | tất cả |
| HC03 | `T_earliest ≤ planned_pickup ≤ T_latest` với `planned_pickup = max(now + ETA, T_earliest)` | tất cả; POOL: mọi khách chưa lên xe |
| HC04 | Mọi đoạn: ghế đang dùng + `passenger_count` ≤ `capacity` | tất cả |
| HC05 | `detour_i ≤ max_passenger_detour_ratio_i` (mặc định 0,30) | `CAR_URBAN_POOL`, mọi khách |
| HC06 | `in_vehicle_time_i ≤ max_in_vehicle_time_i` (mặc định direct × 1,5 + 10 phút, Baseline `in_vehicle_time_default`); `dropoff ≤ latest_arrival` | tất cả có `latest_arrival`; POOL: mọi khách |
| HC07 | Tăng quãng / thời gian kế hoạch ≤ `max_driver_detour_km/min`; số đón thêm ≤ `max_additional_pickups`; tổng điểm dừng ≤ `k_max_stops` (8) | POOL |
| HC08 | Giá tối đa thu được ≤ `B_max`: giá cố định cho BIKE / PRIVATE; `Unmatched_i` cho POOL | tất cả có `budget_max` |
| HC09 | Thời điểm đặt / khởi hành thỏa §2.2 (lead time + cửa sổ đón NOW) | tất cả |
| HC10 | `walk_m ≤ max_walk_m` (P2 chưa có C9: luôn đón tận nơi, `walk_m = 0`) | tất cả |
| HC11 | Nếu khách mới hoặc khách đang trên xe bật `same_gender_coride`: mọi khách có đoạn chồng lấp phải cùng giới tính **đã xác thực** | POOL |

- **Không có lối vòng.** Ứng viên chỉ được tạo từ hàm `check_all()` trả rỗng. Kiểu `FeasibleCandidate` chỉ dựng được trong `candidate.generator`.
- **AI tách khỏi khả thi.** Lớp xếp hạng (P6 / P8) chỉ nhận danh sách đã lọc, không truy cập snapshot hay ngưỡng (R9 §43 nguyên tắc 1). Test kiến trúc cấm `ml_models` import `candidate.constraints`.
- **Bộ kiểm chứng độc lập.** Một hàm thứ hai trong test, viết lại từ R9 §7, kiểm từng ứng viên đã sinh. Đây là phép đo cho tiêu chí "0 vi phạm" (G01, G02, G10, G13).
- **Phạm vi P2 với nhánh A của POOL:** hiện thực bước 1–3 và bước 6 của §36. Bước 4–5 (PlanFare, Cổng 1, D1–D6, phân bổ, Cổng 2) gọi `PoolPricingCheck`; P3 hiện thực. Trước P3, ứng viên nhánh A mang `pricing_check = PENDING_P3` và không được hiển thị hay đặt (OD-P2-04). `ΔCost` dùng `PlanFare` §13 (công thức đầy đủ trong R9, không phụ thuộc phân bổ).

### 5.3. Pooling (P2.3) — §36

- **Đầu vào: `PlanState`.**
  - `r = completed_stop_index`: `-1` khi `CONFIRMED`, `≥ 0` khi `RIDE_STARTED`.
  - Nút `S_curr` = vị trí GPS hiện tại.
  - Các điểm `S_0..S_r` bị đóng băng.
  - Mỗi khách đang trên xe có `traveled_km` (`traveled_km_before_last_replan`) và `actual_pickup_time`.
- **Duyệt.** `p_idx ∈ [0, m_f)` và `q_idx ∈ [p_idx, m_f)` trên `F = [S_curr, S_{r+1}..S_k]`. Tối đa 36 cặp × O(k).
- **Tính toán.** ETA cộng dồn từ `T[u][v] + dwell 60 s`; tải ghế theo đoạn.
- **Kiểm tra lại cho mọi khách.** RB 3 (khách chưa lên), RB 4, 5, 6 (khách đang trên xe dùng `traveled_km + remaining`), 7, 8, 11.
- **Mở rộng sau này** (không làm trong P2):
  - nhiều điểm đón ứng viên C9: tối đa 3 điểm P;
  - `batch_matcher` P10 dùng lại `insertion.evaluate()`;
  - khóa giá theo `pool_lock_point` P4.

## 6. Kiểm thử

| Lớp | Nội dung |
|---|---|
| Đơn vị routing | `httpx.MockTransport`: thành công, ô null, `NoRoute`, `NoSegment`, HTTP 5xx, timeout, lỗi kết nối, JSON hỏng, bảng > max-table-size → lỗi tường minh; tham số `exclude`, `sources` / `destinations`, `annotations` đúng |
| Tích hợp OSRM (`osrm` marker) | Ma trận thật 2 profile. `matrix` khớp `route` từng cặp (sai lệch ≤ 1 m / 1 s). Xe máy không đi `motorway`. `exclude=ferry` |
| Cache (Redis thật, DB index riêng) | Hit / miss, khóa đổi khi đổi policy / profile, Redis hỏng → vẫn đúng (bỏ qua cache) |
| Ràng buộc | Mỗi HC: ca đạt, ca biên (đúng ngưỡng), ca vi phạm. Danh sách đúng 11 mã |
| Chèn §36 | Ví dụ R9 §16.1 / §16.3. Xe đang chạy (`r ≥ 0`): không chèn trước `S_curr`, `traveled_km` đúng. `k_max`, `max_additional_pickups`. Một khách cũ vi phạm → loại phương án |
| Thuộc tính (Hypothesis, 10.000 mẫu có seed) | (a) Mọi phương án trả về thỏa bộ kiểm chứng độc lập. (b) So với duyệt vét cạn trên kế hoạch nhỏ: không bỏ sót phương án khả thi rẻ hơn. (c) Không chèn vào quá khứ |
| Sinh ứng viên (CSDL test + OSRM thật) | Đội xe synthetic có seed, 0 vi phạm theo bộ kiểm chứng độc lập. G10: PRIVATE không ghép. G13: không có BIKE cho liên tỉnh / > 1 khách / hành lý. Số lệnh OSRM = số profile |
| Hiệu năng | `scripts/p2_benchmark.py` (mục 7) |

## 7. Tiêu chí nghiệm thu P2 (local)

1. **0 vi phạm** 11 RB trên toàn bộ ứng viên sinh ra trong bộ kịch bản có seed. Kiểm chứng độc lập; đếm cả khách cũ (G01, G02, G10, G13).
2. **Độ trễ sinh ứng viên < 300 ms (p95).** Đo trên stack local theo R9 §77: "Lọc không gian PostGIS + Gọi 1 ma trận OSRM Table".
   - Báo cáo p50 / p95 / p99 từng giai đoạn: PostGIS, OSRM Table, kiểm ràng buộc, chèn §36, toàn pipeline.
   - Đo ở các cấu hình 50 / 200 / 1.000 tài xế và 0 / 10 / 20 kế hoạch × tối đa 8 điểm dừng.
   - Ghi phần cứng.
   - Nếu không đạt: báo cáo **không đạt** kèm hồ sơ profiling. Không đổi SLA, không giảm N_single = 15, N_pool = 20, k_max = 8.
3. Số request OSRM mỗi lượt = số profile cần dùng; 0 `route()` trong vòng chèn (đếm bằng instrumentation).
4. Toàn bộ test cũ vẫn pass. Migration head → base → head + `alembic check`. Smoke P0 18/18.
5. **Trạng thái:** con số đo trên máy local là `LOCAL_VERIFIED`. Hiệu năng trên máy chủ thật là `EXTERNAL_VALIDATION_DEFERRED`. SF-06 vẫn OPEN.

## 8. Rủi ro hiệu năng

| Rủi ro | Bằng chứng / lý do | Cách xử lý (chỉ sau profiling) |
|---|---|---|
| OSRM Table ~100 điểm chiếm phần lớn ngân sách 300 ms | SF-06: 100×100 p95 69,6–200,9 ms trên máy này | Đo riêng. Chạy song song 2 profile. Giữ kết nối mới (keep-alive chậm ~40 ms). Không cắt điểm khỏi ma trận |
| Ma trận vượt `max-table-size 200` | 20 kế hoạch × 8 điểm + 15 xe + P, Q ≈ 177 | Kiểm tra trước khi gọi; vượt thì báo lỗi tường minh, không tự cắt |
| Truy vấn PostGIS không dùng chỉ mục (ép kiểu geography) | `idx_driver_locations_geom` là geometry | `EXPLAIN ANALYZE` trong benchmark. Nếu cần, chỉ mục biểu thức geography (migration) |
| Python overhead của vòng chèn | 20 kế hoạch × 36 cặp × 8 bước | Đo. Cấu trúc mảng phẳng. Không đổi thuật toán |
| Redis round-trip của cache | MGET ~10⁴ khóa cho 100×100 | Chỉ dùng cache khi profiling chứng minh có lợi (OD-P2-02) |
| Máy Windows + Docker Desktop (WSL2) | Số liệu khác máy chủ thật | Ghi rõ phần cứng; kiểm chứng ngoài bị hoãn |

## 9. Phụ thuộc với P3 / P4

| Hướng | Nội dung |
|---|---|
| P2 → P3 | P3 hiện thực `PoolPricingCheck` (bước 4–5 §36: PlanFare, Cổng 1, D1–D6, phân bổ hai cận, làm tròn, Cổng 2) và mở rộng `tariff.py` thành module `pricing`. Ứng viên nhánh A chuyển từ `PENDING_P3` sang khả thi đầy đủ. RB 8 của P2 chỉ dùng công thức cố định §10.1 / §12.1 / §18.3 (đọc `pricing_configs`) |
| P2 → P4 | P4 đọc `ride_candidates.source_plan_version` để khóa lạc quan + `FOR UPDATE` (§42). Chuyển tài xế IDLE ↔ BUSY theo vòng đời chuyến. Cập nhật `ride_stops.status`, `completed_stop_index`, `traveled_km`. Offer cascade + seat hold dùng `insertion_json` |
| P2 cần trước từ P4 | Không bắt buộc. Kế hoạch đang chạy trong test được dựng bằng fixture trực tiếp vào bảng. Khi P4 xong, chạy lại bộ test chèn với trạng thái do P4 tạo |
| P2 → P6 / P8 | `candidate_runs` + `ride_candidates` (đặc trưng, ETA, giá, nhãn dịch vụ) là nguồn sự kiện cho xếp hạng và `P(match)` / `P(fulfill)`. Không có AI sản xuất trước khi có pipeline dữ liệu (P7) |

## 10. Quyết định còn mở thực sự ảnh hưởng P2

| Mã | Vấn đề | Đề xuất (áp dụng tạm cho local, ghi rõ, đổi được) |
|---|---|---|
| OD-P2-01 | "1 lệnh OSRM Table duy nhất" (§34, §79) với 3 dịch vụ nội đô dùng 2 profile (xe máy `motorbike`, ô tô `car`) | 1 lệnh **cho mỗi profile** mỗi lượt (tối đa 2, chạy song song); bao xe và ghép dùng chung lệnh `car` |
| OD-P2-02 | Cache khóa theo geohash-7 (~150 m) có thể đưa sai số tới ~150 m vào RB 3 / 5 / 6 | Không dùng cache cho ma trận phục vụ kiểm RB. Cache dùng cho `route()` ước lượng hiển thị và tra cặp lặp lại; khóa đúng §34 |
| OD-P2-03 | Khung `[T_earliest, T_latest]` khi đặt hẹn giờ mà khách không nhập | NOW: cửa sổ §2.2 (xe máy 3–15 phút, ô tô 5–20 phút) giao với khung khách nhập. Hẹn giờ không nhập: `[T_preferred, T_preferred + độ rộng cửa sổ NOW]` (12 / 15 phút) |
| OD-P2-04 | Ứng viên nhánh A trước khi có định giá P3 | Sinh và ghi nhật ký với `pricing_check = PENDING_P3`. Không hiển thị, không đặt cho đến P3 |
| OD-P2-05 | `R_pool` (bán kính lọc kế hoạch ghép) không có số trong R9 / Baseline | Dùng `R_urban` = 5 km (§35.1) |
| OD-P2-06 | `max_driver_detour_km/min` để trống | Hiểu là tài xế không khai báo ngưỡng. Vẫn áp `k_max_stops` và `max_additional_pickups` (mặc định 0 → không nhận khách thêm) |
| OD-P2-07 | Trạng thái trực tuyến / rảnh và độ tươi vị trí (RB 1) | `driver_locations.availability` + `location_stale_s = 120` (tham số kỹ thuật, không phải Baseline) |

## 11. Thứ tự thực hiện

1. P2.1 Routing: provider, OSRM, cache, lỗi, test.
2. Migration 0005 + availability.
3. P2.2 Constraints + tariff + generator single.
4. P2.3 Insertion + nhánh A / B.
5. P2.4 Benchmark + báo cáo `P2_PROGRESS_REPORT.md`.

Mỗi bước: chạy toàn bộ test. Không commit / push khi chưa có yêu cầu.
