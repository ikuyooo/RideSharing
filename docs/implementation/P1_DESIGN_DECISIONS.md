# Phase 1 — Hồ sơ quyết định thiết kế triển khai

Ghi lại cách các quyết định của Chủ dự án (OWNER P1 DECISION & IMPLEMENTATION AUTHORIZATION, 2026-10-25)
được hiện thực, và mọi lựa chọn kỹ thuật **không có trong Revision 9**. Tài liệu này không sửa
Revision 9, Baseline v1 hay Decision Register.

## 1. Trạng thái các quyết định của Chủ dự án

| Mã | Trạng thái do Chủ dự án ghi | Cách hiện thực | Còn chờ |
|---|---|---|---|
| P1-D1 Service area polygons | APPROVED_METHOD / GEOMETRY_PENDING_APPROVAL | Pipeline `app.modules.trip.service_area_build` + quy tắc `config/service_area_rules.candidate.yaml`; hình học lưu `status = CANDIDATE` | Phê duyệt hình học cụ thể (`sa-cand-3873dfbee116` hoặc bản sửa) |
| P1-D2 `direct_distance_km` | APPROVED_IMPLEMENTATION_CHOICE | `app.modules.routing.service.OsrmCarDistance`: khoảng cách `routes[0].distance` (mét → km) của OSRM car; so sánh `<= 15.0` → URBAN, `> 15.0` → INTERCITY; lỗi `NoRoute`/`NoSegment` → `ROUTE_NOT_FOUND` (422), OSRM không trả lời → `ROUTING_UNAVAILABLE` (503); **không fallback** khoảng cách trắc địa | — |
| P1-D3 total_service_area | POLYGON_METHOD_APPROVED / EXTENT_PENDING_APPROVAL | Đa giác PostGIS = hợp các xã/phường của các tỉnh được chọn có điểm đại diện trong 150 km đường bộ (OSRM car) từ điểm gốc | **ANCHOR_DEFINITION_REQUIRED**; phạm vi tỉnh |
| P1-D4 Schema | APPROVED_WITH_REQUIREMENTS | Alembic `0001`; mọi ràng buộc 56.2 có test vi phạm cố ý | — |
| P1-D5 Survey S1 | APPROVED_DELIVERY_METHOD / EXPERIMENT_VALUES_PENDING_APPROVAL | `SURVEY_S1_DESIGN_REVIEW.md`, bảng hỏi nháp, schema export | Duyệt nội dung + hạ tầng phát hành |
| P1-D6 Gender | APPROVED_WITH_PRIVACY_RESTRICTIONS | Trường tùy chọn `users.gender`; `gender_verification_status` bị CHECK ở DB chỉ cho phép `UNVERIFIED` | Phương pháp xác minh (thuộc S9/P2+) |
| P1-D7 pricing_configs | APPROVED | Seed idempotent, bất biến (trigger chặn UPDATE/DELETE/TRUNCATE) | — |

> P1-D2 là quyết định **làm rõ** phương pháp đo mà Mục 2.3 không định nghĩa tường minh; Revision 9 không quy định lựa chọn này.

## 2. Bổ sung kỹ thuật (không có trong Revision 9)

| Hạng mục | Nội dung | Lý do |
|---|---|---|
| Kiểu enum | `VARCHAR` + `CHECK IN (...)` với đúng tập giá trị Mục 56.1 | Migration đơn giản, dễ mở rộng |
| `users` (toàn bộ cột) | `email` (unique không phân biệt hoa thường), `password_hash` (Argon2id), `role`, `display_name`, `gender`, `gender_verification_status`, `is_active`, `created_at` | Mục 56.1 không đặc tả `users`; cần cho Mục 59.1 và làm đích FK |
| `refresh_tokens` | Lưu SHA-256 của token, `family_id` (phát hiện dùng lại), `expires_at`, `revoked_at` | "Refresh Token có cơ chế thu hồi" (Mục 59.1) |
| Thời hạn refresh token | 14 ngày | Revision 9 không quy định |
| Chính sách mật khẩu | tối thiểu 8 ký tự | Revision 9 không quy định |
| `driver_profiles.kyc_*` | `kyc_submission_json`, `kyc_submitted_at`, `kyc_reviewed_at`, `kyc_reviewed_by` | Luồng KYC mock Mục 81 |
| CHECK `kyc_gates_pool_and_intercity` | `pool_enabled`/`accepts_intercity` = false khi chưa VERIFIED | Bảo vệ hai lớp cho Mục 81 |
| CHECK `capacity_matches_type` | BIKE = 1, CAR4 = 4 | Mục 56.1 ghi "(BIKE = 1, CAR4 = 4)" |
| `trip_requests.service_area_version`, `direct_distance_km`, `created_at` | Truy vết phân loại | Tái lập kết quả Mục 2.3 |
| `service_areas` (toàn bộ cột) | `area_type`, `service_area_version`, `status` (CANDIDATE/APPROVED/RETIRED), `geom`, `source_json`, `approved_at`, `approval_reference` | Mục 56.1 không đặc tả; cần cho P1-D1/D3 |
| `pickup_points`, `seat_holds`, `idempotency_records`, `driver_locations` | Cấu trúc tối thiểu | Để hiện thực FK/index bắt buộc của 56.1–56.2 |
| `pricing_configs.config_baseline_version`, `source_sha256`, `created_at` | Truy vết về YAML | P1-D7 |
| Ánh xạ dịch vụ → mục YAML trong `params_json` | BIKE_URBAN→`bike_urban`; CAR_URBAN_*→`car_urban`; CAR_INTERCITY_PRIVATE→`car_intercity_private`; CAR_INTERCITY_POOL→`car_intercity_pool`+`car_intercity_private` | Diễn giải từ Phụ lục B và Mục 28.1 |
| `active_from` | 2026-10-23 (Asia/Ho_Chi_Minh) | Ngày phê duyệt ghi trên Baseline |
| API bổ sung | `GET /api/driver/profile`, `POST /api/driver/vehicles`, `POST /api/driver/kyc/submit`, `POST /api/auth/*`, `GET /api/users/me`, `PUT /api/users/me/gender`, `GET /api/trip-requests/{id}` | Cần cho luồng Mục 3, 59, 81; Mục 57 không liệt kê |
| Mã lý do loại dịch vụ | `MODE_MISMATCH`, `VEHICLE_PREFERENCE_MISMATCH`, `RIDE_PREFERENCE_MISMATCH`, `PASSENGER_COUNT_EXCEEDED`, `LUGGAGE_NOT_ALLOWED`, `LEAD_TIME_OUT_OF_WINDOW` (+ `suggested_service_code`) | Mục 6 yêu cầu "mã lý do cụ thể" nhưng không định danh |
| Giới hạn số khách | BIKE = `bike_urban.capacity`; CAR_URBAN_POOL = `max_party_seats_pool`; các dịch vụ CAR4 khác = `car_urban.capacity` | Không có khóa capacity riêng cho dịch vụ liên tỉnh trong Baseline |
| Yêu cầu bị từ chối không gian | `OUT_OF_SERVICE_AREA`, `UNSUPPORTED_INTER_PROVINCE_ROUTE` trả 422 và **không** lưu `trip_requests` (cột `mode` NOT NULL) | |
| Bộ lọc log tọa độ | Che mọi số thập phân ≥ 4 chữ số lẻ trong log | Lưới an toàn cho Mục 59.2 |
| Client OSRM | Kết nối mới mỗi request (`Connection: close`) | Phát hiện keep-alive ~40 ms ở P0 |
