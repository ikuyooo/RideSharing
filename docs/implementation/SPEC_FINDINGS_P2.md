# PHASE 2 — PHÁT HIỆN ĐẶC TẢ VÀ DIỄN GIẢI ĐÃ ÁP DỤNG

- **Ngày:** 2026-10-29
- Revision 9 và Baseline v1 **không bị sửa**.
- Mỗi diễn giải dưới đây đang được dùng **tạm cho môi trường local**, ghi rõ để Chủ dự án duyệt hoặc đổi.
- Quyết định mở tương ứng: `P2_IMPLEMENTATION_PLAN.md` §10.

| Mã | Phát hiện | Nguồn | Cách hiện thực hiện tại | Cần quyết định |
|---|---|---|---|---|
| SF-P2-01 | "1 lệnh OSRM Table duy nhất" (§34, §79). Nhưng 3 dịch vụ nội đô dùng 2 profile: xe máy `motorbike`, ô tô `car` | §34, §35.1, §79 | Mỗi lượt gửi 1 lệnh cho **mỗi profile** (tối đa 2), chạy song song. Bao xe + ghép dùng chung lệnh `car`. Số request được đếm và lưu ở `candidate_runs.osrm_requests` | OD-P2-01 |
| SF-P2-02 | Khi có kế hoạch ghép, §34 nói `matrix(all_points, all_points)`; khi chỉ có xe đơn, §35.1 nói `matrix([xe, P], [P, Q])` | §34, §35.1 | Làm đúng cả hai: chỉ xe đơn → ma trận chữ nhật; có kế hoạch ghép → ma trận vuông trên mọi nút `car` | Không |
| SF-P2-03 | `R_urban = 5 km` và `N_single = 15` có trong văn bản §35.1 nhưng không có trong khối YAML Baseline. `R_pool` không có số | §35.1, §35.2, Baseline §4 | Hằng số trong `candidate/generator.py` có ghi nguồn. `R_pool = R_urban` | OD-P2-05 |
| SF-P2-04 | RB 1 cần "đang trực tuyến, rảnh (IDLE)" nhưng §56.1 không có cột trạng thái | §7, §35.1, §56.1 | Bổ sung kỹ thuật `driver_locations.availability` + `active_vehicle_id`; vị trí cũ hơn 120 s coi như ngoại tuyến | OD-P2-07 |
| SF-P2-05 | `ride_stops` được liệt kê ở §54 nhưng không có cột | §54 | Bổ sung kỹ thuật (migration 0005): `seq`, `kind`, `booking_id`, `geom`, `status`, `planned_eta`, `completed_at`; `UNIQUE (plan, seq)` DEFERRABLE | Không (P4 dùng) |
| SF-P2-06 | RB 5 / RB 6 của khách đang trên xe cần **quãng / thời gian đi thẳng** của khách đó. Sau khi đón, điểm đón đã ở phía sau nên ma trận hiện tại không có | §7, §36 | `ride_participants.direct_distance_m / direct_duration_s` (bổ sung kỹ thuật) — P4 ghi lúc đặt. Thiếu dữ liệu → bỏ kế hoạch (`PLAN_DATA_INCOMPLETE`), không đoán | Không |
| SF-P2-07 | Khung `[T_earliest, T_latest]` mặc định khi khách không nhập | §2.2, §6, §7 | NOW: cửa sổ §2.2 sau `T_preferred` (xe máy 3–15 phút, ô tô 5–20 phút), giao với khung khách nhập. Hẹn giờ: `[T_preferred, + độ rộng cửa sổ]`. Xe đến sớm thì **chờ** tới `T_earliest` | OD-P2-03 |
| SF-P2-08 | §36 bước 4–5 (PlanFare, Cổng 1, D1–D6, phân bổ, Cổng 2) thuộc định giá P3 | §36, §79 | Hook `PoolPricingCheck`. Ứng viên nhánh A có `pricing_check = PENDING_P3`, chỉ ghi nhật ký, không chào | OD-P2-04 |
| SF-P2-09 | `ΔCost = PlanFare_new − PlanFare_old`: `T_plan` "thời gian thực tế" — có tính thời gian chờ và dừng đón trả hay không | §13, §36 | Tính thời gian trôi qua thực tế (gồm dừng 60 s và thời gian chờ). Chỉ dùng để chọn vị trí chèn; P3 sở hữu `PlanFare` | Khi làm P3 |
| SF-P2-10 | RB 11 cần giới tính **đã xác thực**. P1-D6 chưa có phương thức xác thực, chỉ có `UNVERIFIED` | §7, P1-D6 | Khách bật `same_gender_coride` **không thể** đi chung đoạn với ai: chỉ còn kế hoạch mới (nhánh B), không chèn được vào xe đang có khách | Khi duyệt phương thức xác thực giới tính |
| SF-P2-11 | `max_driver_detour_km/min` để trống | §7 RB 7 | Coi như tài xế không khai báo ngưỡng. Vẫn áp `k_max_stops = 8` và `max_additional_pickups` (mặc định 0) | OD-P2-06 |
| SF-P2-12 | Ngưỡng RB 6 mặc định `direct × 1,5 + 10 phút` ghi "cho taxi ghép nội đô"; với xe đơn thời gian ngồi xe = đi thẳng | §7, Baseline `in_vehicle_time_default` | Áp cùng công thức cho mọi dịch vụ. Xe đơn luôn đạt; `latest_arrival` vẫn được kiểm | Không |
| SF-P2-13 | Hướng đi (§35.2 bước 2): "góc lệch < 60° hoặc bounding box giao nhau" — vector của kế hoạch không được định nghĩa | §35.2 | Vector kế hoạch = vị trí xe → điểm dừng cuối phía trước. Bounding box = vị trí xe + mọi điểm dừng phía trước | Không |
| SF-P2-14 | Cache khóa geohash-7 (~150 m) có thể mang sai số vào RB 3 / 5 / 6 | §34 | Chỉ cache `route()` không waypoint. Ma trận kiểm RB luôn gọi OSRM | OD-P2-02 |
| SF-P2-15 | Ma trận `/table` (R9 §34 / §36) tính mỗi cặp điểm độc lập, cho phép quay đầu tại điểm dừng. Một tuyến thật qua nhiều điểm (`/route`, mặc định `continue_straight=true` với ô tô) có thể dài hơn vì không quay đầu được tại điểm đón | Benchmark P2 ngày 2026-10-29: 6 ứng viên lệch RB 5 khi bộ kiểm chứng dùng `/route` mặc định; **0 lệch** khi các chặng độc lập như bảng | Giữ đúng R9 (bảng). Bộ kiểm chứng dùng `continue_straight=false`. Ghi nhận: quãng đi vòng thực tế có thể lớn hơn ước tính khi phải đi vòng để quay đầu | Rủi ro mô hình. Xem lại khi có dữ liệu chuyến thật / simulator P7 |
