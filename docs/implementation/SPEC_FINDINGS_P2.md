# PHASE 2 — PHÁT HIỆN ĐẶC TẢ VÀ DIỄN GIẢI ĐÃ ÁP DỤNG

- **Cập nhật:** 2026-11-04, theo "OWNER ACCEPTANCE OF P2 LOCAL & PHASE 3 KICKOFF" (ghi nhận quyết định). Trước đó: 2026-10-31 (hardening), bản đầu 2026-10-29.
- **Trạng thái phase:** `PHASE_2_LOCAL_ACCEPTED__KNOWN_LIMITATIONS` (`P2_LOCAL_ACCEPTANCE_RECORD.md`).
- Revision 9 và Baseline v1 **không bị sửa**.
- Một phát hiện chỉ được ghi `APPROVED` khi có quyết định OD-P2 tương ứng của Chủ dự án.
- Quyết định OD: `P2_IMPLEMENTATION_PLAN.md` §10. Bằng chứng: `evidence/p2_runs/<run_id>/`.

**Ý nghĩa cột "Trạng thái":**

| Trạng thái | Nghĩa |
|---|---|
| `APPROVED` | Theo OD-P2 / quyết định Chủ dự án đã duyệt |
| `APPROVED_FOR_MVP`, `APPROVED_AS_P2_BASELINE`, `APPROVED_WITH_SAFEGUARDS` | Duyệt có phạm vi hoặc điều kiện kèm theo (ghi trong cột Đề xuất) |
| `APPROVED_MITIGATION_FOR_P4` | Đã duyệt **phương án**, việc hiện thực thuộc P4 — chưa phải `RESOLVED` |
| `LOCAL_PROVISIONAL` | Áp dụng tạm cho local, chờ Chủ dự án |
| `IMPLEMENTED` | Bổ sung kỹ thuật đã hiện thực, chưa có quyết định riêng |
| `OPEN` | Chưa xử lý xong hoặc cần quyết định |
| `RESOLVED` | Lỗi / hạn chế đã sửa và có bằng chứng |

| ID | Nguyên văn phát hiện | Bằng chứng | Tác động | Đề xuất | Trạng thái | Có chặn P2 không |
|---|---|---|---|---|---|---|
| SF-P2-01 | "1 lệnh OSRM Table duy nhất" (§34, §79), nhưng 3 dịch vụ nội đô dùng 2 profile (`motorbike`, `car`) | §34, §35.1; `candidate_runs.osrm_requests` = 2 ở mọi lượt (`final-verify`: 1.400 lượt) | Mỗi lượt 2 request song song | 1 request / profile | **APPROVED** (OD-P2-01) | Không |
| SF-P2-02 | Khi có kế hoạch ghép, §34 nói `matrix(all_points, all_points)`; khi chỉ có xe đơn, §35.1 nói `matrix([xe, P], [P, Q])` | 2026-10-31: bảng `car` khi có kế hoạch đổi từ vuông sang **`sources` = mọi nút, `destinations` = điểm dừng phía trước + P + Q** (vẫn 1 request). Chứng minh: `test_insertion_reads_only_stop_destinations` (3.000 kịch bản: thuật toán chèn chỉ đọc ô có đích trong tập đó, kết quả giống bảng vuông); kiểm chứng độc lập 0 vi phạm, 0 bỏ sót | OSRM car p95 ~119–122 → ~64–73 ms ở 20 kế hoạch | Giữ; khác chữ "all_points × all_points" nhưng cung cấp **mọi** cặp thuật toán dùng (chỉ thị §7 cho phép) | **APPROVED** (2026-11-04: giữ ma trận chữ nhật có kiểm chứng tương đương với ma trận vuông) | Không |
| SF-P2-03 | `R_urban = 5 km`, `N_single = 15` có trong §35.1 nhưng không có trong YAML Baseline; `R_pool` không có số | Phân tích `final-radius` (dữ liệu synthetic, ETA OSRM không kẹt xe): tài xế ngoài 5 km vẫn kịp đón. **Case (a)** — trong 5 km có < 15 tài xế kịp: 87/200 yêu cầu (200 tài xế), 31/200 (1.000 tài xế). **Case (b)** — ngoài 5 km có người nhanh hơn người chậm nhất của top-15: 164/200 và 73/200 | Có false negative thật; case (b) một phần do chính quy tắc chọn top-N theo đường chim bay của §35.1 | Giữ 5 km cho P2. False negative và phương án mở rộng theo ETA chuyển sang cổng đánh giá chất lượng gợi ý P6. Số đo phóng đại vì OSRM không có dữ liệu kẹt xe | **APPROVED_AS_P2_BASELINE** (OD-P2-05, 2026-11-04) | Không; vấn đề false negative còn mở ở cổng P6 |
| SF-P2-04 | RB 1 cần "đang trực tuyến, rảnh" nhưng §56.1 không có cột | `driver_locations.availability`, `active_vehicle_id`; vị trí cũ hơn 120 s bị loại | — | Giữ | **APPROVED_FOR_LOCAL** (OD-P2-07) | Không |
| SF-P2-05 | `ride_stops` có ở §54 nhưng không có cột | Migration 0005 | — | Giữ; P4 dùng | **IMPLEMENTED** | Không |
| SF-P2-06 | RB 5 / 6 của khách đang trên xe cần quãng / thời gian đi thẳng của khách | `ride_participants.direct_distance_m / direct_duration_s`; thiếu → bỏ kế hoạch, không đoán | P4 phải ghi hai cột này khi đặt | Giữ | **IMPLEMENTED** | Không |
| SF-P2-07 | Khung `[T_earliest, T_latest]` mặc định khi khách không nhập | `tests/test_candidate_windows.py` (NOW, NOW + khung khách, hẹn giờ có / không khung, chỉ có `T_earliest`, luật thời gian đặt) | Ảnh hưởng RB 3 / RB 9 | Giữ cửa sổ hiện tại; phân biệt theo dịch vụ, kiểm luật đặt trước (RB 9), không đón trước thời điểm khách chọn (`test_scheduled_pickup_never_before_the_chosen_time`) | **APPROVED_FOR_MVP** (OD-P2-03, 2026-11-04) | Không |
| SF-P2-08 | §36 bước 4–5 (PlanFare, Cổng 1, D1–D6, phân bổ, Cổng 2) thuộc P3 | `final-verify`: 822 ứng viên `PENDING_P3`, **0** qua `offerable()`; test `test_pending_p3_candidates_are_never_offerable` | Nhánh A chưa chào được tới khi có P3 | Giữ | **APPROVED** (OD-P2-04) | Không (thuộc P3) |
| SF-P2-09 | `T_plan` của `ΔCost` có gồm thời gian chờ / dừng không | Đang tính thời gian trôi qua thực tế | Chỉ ảnh hưởng chọn vị trí chèn | Chủ dự án (2026-11-04): phân tích và thống nhất `T_plan` với `PlanFare` ở P3 (di chuyển, dừng, chờ theo đúng đặc tả) | **OPEN — chuyển P3** (xem `SPEC_FINDINGS_P3.md`) | Không |
| SF-P2-10 | RB 11 cần giới tính **đã xác thực**; P1-D6 chỉ có `UNVERIFIED` | Cấu hình HC: 3.301 phương án bị RB 11 loại, 0 vi phạm. Nhánh "cùng giới đã xác thực → được ghép" chỉ kiểm bằng unit test (CSDL không cho phép `VERIFIED`) | Khách bật cùng giới không thể đi chung đoạn với ai | Chủ dự án (2026-11-04): giữ fail-closed cho giới tính chưa xác thực; chưa mở chức năng xác thực thật | **OPEN** (fail-closed giữ nguyên) | Không |
| SF-P2-11 | `max_driver_detour_km/min` để trống (NULL) | Cấu hình HC: ngưỡng 3 km / 10 phút và 6 km / 15 phút được kiểm độc lập; 5.666 phương án bị RB 7 loại, 0 vi phạm | NULL hiện = không giới hạn đi vòng (vẫn áp `k_max`, `max_additional_pickups`) | NULL = không khai báo giới hạn đi vòng riêng; mọi ràng buộc khác vẫn bắt buộc; NULL ≠ 0 (`test_null_detour_limit_is_not_zero`) | **APPROVED_WITH_SAFEGUARDS** (OD-P2-06, 2026-11-04) | Không |
| SF-P2-12 | Ngưỡng RB 6 mặc định ghi "cho taxi ghép nội đô" | Áp cho mọi dịch vụ; xe đơn luôn đạt | — | Giữ | **IMPLEMENTED** | Không |
| SF-P2-13 | Vector hướng của kế hoạch (§35.2 bước 2) không được định nghĩa | Vị trí xe → điểm dừng cuối phía trước; bbox = xe + điểm dừng | — | Giữ | **LOCAL_PROVISIONAL** | Không |
| SF-P2-14 | Cache geohash-7 (~150 m) có thể đưa sai số vào RB | Ma trận kiểm RB không bao giờ đi qua cache (`test_route_cache_hit_miss_on_real_redis`) | — | Giữ | **APPROVED** (OD-P2-02) | Không |
| SF-P2-15 | Bảng `/table` tính mỗi cặp độc lập, cho phép quay đầu tại điểm dừng; tuyến thật qua nhiều điểm thì không | Xem chi tiết dưới bảng | Rủi ro mô hình đã định lượng, không phải lỗi thuật toán theo R9 | Chủ dự án chọn phương án (2), 2026-11-04: P4 dùng `/route` xác minh chuỗi điểm dừng cuối trước khi chào; kiểm lại mọi ràng buộc cứng bị ảnh hưởng; không bỏ qua lỗi định tuyến | **APPROVED_MITIGATION_FOR_P4** — chưa hiện thực, chưa `RESOLVED` | Không chặn §79 P2; **chặn việc chào ứng viên ghép ở P4** cho tới khi hiện thực |
| SF-P2-16 | Phép đo độ trễ nhạy với điều kiện đo | Từ Windows qua port proxy: ~1 s / kết nối (bị loại). Bộ lấy mẫu `docker stats` chạy liên tục nghi gây nhiễu (`before-r1` 1000×0 PostGIS p95 339 ms; `before-r2` bị dừng). Bảng mới nạp chưa ANALYZE → planner ước lượng 1 dòng, chọn Seq Scan lặp 478 lần (75 ms). Số FAIL ngày 29/10 (516 / 331 ms) đo khi xen kiểm chứng và ở điều kiện máy khác; baseline cùng mã ngày 30/10 được 228–281 ms | Kết luận hiệu năng phải dựa trên nhiều lượt và cùng điều kiện | Đo trong mạng compose, lấy mẫu 10 s, báo cáo cả có / không ANALYZE, ≥ 3 lượt | **RESOLVED** (quy trình đo) | Không |
| SF-P2-17 | `httpx.get()` tạo Client mới mỗi request → dựng lại SSL context (~10 ms / request kể cả với `http://`) | cProfile `before-cprofile`: `load_verify_locations` 1,54 s / 200 lần gọi; đo nhỏ: p50 20,6 → 10,1 ms | ~20 ms mỗi lượt | Một `httpx.Client` dùng chung, vẫn không keep-alive (phát hiện P0) | **RESOLVED** | Không |
| SF-P2-18 | RB 10 (đi bộ) chưa kích hoạt được trong generator vì P2 chưa có điểm đón gặp nhau C9: `walk_m` luôn 0 | Unit test RB 10 (`test_each_violation`) | Phạm vi kiểm chứng độc lập không bao gồm vi phạm RB 10 thật | Chủ dự án (2026-11-04): giữ unit test RB 10; kiểm thử tích hợp đầy đủ khi triển khai C9 | **OPEN** (giới hạn phạm vi kiểm chứng; chuyển C9) | Không |

## Chi tiết SF-P2-15 (`final-verify`, 2026-10-31)

**Nguyên nhân.** Profile car của OSRM có `continue_straight_at_waypoint = true` và `u_turn_penalty = 20 s`. Do đó `/route` với mặc định không quay đầu tại điểm dừng trung gian. Trong khi đó `/table` (R9 §34 / §36) tính từng cặp độc lập.

**Quy mô.** Trên **18.415** ứng viên ghép, nếu đi chuỗi điểm dừng bằng `/route` mặc định thay vì các chặng độc lập:

| Chỉ số | Giá trị |
|---|---|
| Ứng viên sẽ vi phạm | **349 (1,9%)** |
| Phân bố theo mã RB | HC03 162, HC05 192, HC06 3 (một ứng viên có thể vi phạm nhiều mã) |
| Tỷ lệ quãng chuỗi (mặc định / bảng) | p50 1,00 · p95 1,06–1,09 · p99 1,12–1,21 · max 2,04 |
| Chuỗi dài hơn 1% | 5.537 |
