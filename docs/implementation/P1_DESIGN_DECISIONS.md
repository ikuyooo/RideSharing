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

## 3. Quyết định "P1: GEOGRAPHY & S1 CLOSURE" (2026-10-26) — cách hiện thực

| Mã | Quyết định của Chủ dự án | Hiện thực | Còn chờ |
|---|---|---|---|
| A1 | Ánh xạ địa danh lịch sử sang đơn vị sau cải cách 2025, có nguồn thẩm quyền | `admin_mapping` trong `config/service_area_rules.candidate.v2.yaml` (mã QĐ 19/2025/QĐ-TTg, khoản NQ 1656/NQ-UBTVQH15, mức chắc chắn) → `admin_mapping.csv` | Đối chiếu bản PDF chính thức |
| A2 | Tách khu đô thị An Khánh khỏi La Phù nếu có bằng chứng hình học | Quy tắc **U3**: polygon `landuse=residential` có tên của các khu đô thị An Khánh trên OSM (cắt theo ranh giới thành phố); Xã An Khánh mới không lấy nguyên khối | Ranh giới La Phù lịch sử: `PENDING_GEOMETRY_EVIDENCE` |
| A3 | Đối chiếu Mỹ Đình / Gia Lâm / Đông Anh theo phạm vi địa danh | Điểm kiểm tra có tên (SVĐ & Bến xe Mỹ Đình, KTĐC Trâu Quỳ); bảng ánh xạ theo khoản NQ 1656 | Đông Anh |
| A4 | Điểm gốc node 74132064 (có điều kiện) | Xác minh vai trò `admin_centre` trên file nguồn; phân tích độ nhạy ±20 km × 12 điểm/đơn vị (`ST_GeneratePoints`, seed 1) | Quy tắc xử lý đơn vị chỉ một phần trong 150 km (SF-P1-12) |
| A5 | Danh sách tỉnh Mục 1 là ví dụ | `province_scope: all_within_range`, chọn từng xã/phường | — |
| A6 | Không tự xóa/nối/lấp | Chỉ phân loại thành phần (`components.csv`) | Quy tắc cho đảo không đường (SF-P1-13) |
| A7 | `max_passenger_detour_ratio` = 0,30 khi không nhập | `rules.SPEC_DEFAULT_MAX_PASSENGER_DETOUR_RATIO`, ghi rõ nguồn Mục 6, không thêm vào Baseline | — |
| A8 | Phố Hiến là điểm đại diện ứng viên | Dùng trong ca 72.2; kiểm tra ngữ cảnh 58,055 km vs 65 km | Không phải ánh xạ chính thức |
| A9 | Giữ bbox OSRM; vùng không có đường không sẵn sàng phục vụ | Loại đơn vị có điểm đại diện ngoài bbox hoặc không định tuyến được (`excluded_units.csv`) | — |

### Bổ sung kỹ thuật mới (không có trong Revision 9)

| Hạng mục | Nội dung |
|---|---|
| Ngưỡng phân tích A6 | Mảnh < 0,01 km² và cách thành phần khác < 10 m → `SLIVER_SUSPECTED`; "không có đường" = điểm OSRM `/nearest` của thành phần nằm ngoài thành phần (> 1 m). Chỉ dùng để phân loại, không phải quy tắc nghiệp vụ |
| Ngưỡng phân tích A4 | Dải ±20 km, 12 điểm mẫu/đơn vị — chỉ để báo cáo |
| `boundary_eval --report-name` | Không ghi đè bằng chứng gốc của bundle cũ (tự chặn với bundle quy tắc v1) |
| `service_area_compare` | So sánh hai phiên bản (diện tích, thành phần, đơn vị, điểm đổi trạng thái trên mọi node `place=*` trong bbox, ảnh hưởng phân loại) |
| Khảo sát S1 (bản nháp dev) | Bảng `survey_respondents` (kỹ thuật) + `survey_responses` (Mục 54) — migration `0002`; `dataset` TEST/RESEARCH theo cấu hình (`SURVEY_DATASET`, `SURVEY_S1_RELEASED`); thiết kế 2×2×2, xoay khối `(i + 2k) mod 6`; QC3/QC4 chỉ gắn cờ; export CSV; `SurveyClientAddressFilter` xóa địa chỉ client khỏi log truy cập của đường dẫn khảo sát |
| Export places | Thêm `leisure=stadium`, `amenity=bus_station`, `landuse=residential` để có điểm/polygon có tên làm bằng chứng |

## 4. Quyết định "PHASE 1 FINAL CLOSURE" (2026-10-27) — cách hiện thực

| Mã | Quyết định của Chủ dự án | Hiện thực | Còn chờ |
|---|---|---|---|
| GEO-01 | Đông Anh: phạm vi tra cứu Thư Lâm / Đông Anh / Phúc Thịnh; không lấy nguyên xã; chỉ dùng dữ liệu OSM có bằng chứng | Bỏ quy tắc U2 `Xã Đông Anh`. Tìm trong snapshot: có quan hệ lịch sử `relation/17627914` "Thị trấn Đông Anh" (`boundary=historic`, admin_level 8) nhưng **vòng ranh giới hở** (9 way → 1 chuỗi không khép, osmium không dựng được vùng); không có polygon khu dân cư/đô thị có tên gắn với thị trấn cũ. → `PENDING_GEOMETRY_EVIDENCE`; không tự khép/vẽ | Bằng chứng hình học hoặc quyết định khác |
| GEO-02 | Bỏ Tùng Thiện; bỏ quy tắc "mọi phường"; danh sách có kiểm soát, truy vết nguồn | `urban.include_units`: 48 phường NQ 1656 k1–k48 (hình thành từ phường của các quận cũ) + Xã Gia Lâm (k109); mỗi dòng có mã QĐ19 + khoản NQ1656, pipeline đối chiếu với bảng chính thức. Loại: Tùng Thiện (k51), Sơn Tây (k50), Chương Mỹ (k49, chờ duyệt) | Xác nhận Sơn Tây, Chương Mỹ |
| GEO-03 | Giữ anchor node 74132064 và giới hạn 150 km; hai lớp kiểm tra; từ chối điểm > 150 km / không định tuyến | **Lớp 1:** polygon TOTAL (đơn vị có điểm đại diện **hoặc** một điểm mẫu ≤ 150 km — `tier1_rule: any_sample_within`) trừ lớp `EXCLUDED`. **Lớp 2:** mỗi pickup/dropoff, một request OSRM `/table`: snap ≤ `max_snap_m`, có tuyến từ anchor, khoảng cách đường bộ ≤ 150 km (đúng 150 km được nhận), pickup→dropoff có tuyến. Tham số lưu trong `service_areas.source_json.serviceability` | `max_snap_m = 300` là **tham số triển khai chờ xác nhận** |
| GEO-04 | Giữ polygon gốc; đảo không phục vụ được phải bị loại hoặc chặn tin cậy | Lớp `EXCLUDED` riêng (migration `0003`): thành phần TOTAL không có đường ô tô định tuyến được bên trong (thăm dò 1 + 4 điểm/thành phần) hoặc không có tuyến từ anchor. TOTAL gốc giữ nguyên | — |
| GEO-05 | Splendora = Bắc An Khánh theo tên; đối chiếu vị trí chủ đầu tư | Giữ 3 polygon Splendora (U3), ghi chú địa chỉ chủ đầu tư "Km10+600 Đại lộ Thăng Long, Sơn Đồng" | — |
| GEO-06 | Đối chiếu mã/khoản với văn bản chính thức | Đọc trực tiếp PDF ký số QĐ 19/2025/QĐ-TTg (Phụ lục II, Hà Nội 126 đơn vị) và NQ 1656/NQ-UBTVQH15 (Điều 1); bảng `config/official/hanoi_units_qd19_nq1656.csv`; pipeline kiểm 126/126 tên OSM | — |

### Bổ sung kỹ thuật mới (không có trong Revision 9)

| Hạng mục | Nội dung |
|---|---|
| Lớp `EXCLUDED` (`service_areas.area_type`) | Migration `0003`; vùng chấp nhận = TOTAL − EXCLUDED; TOTAL gốc giữ nguyên |
| Lý do từ chối không gian | Mã lỗi vẫn là `OUT_OF_SERVICE_AREA` (Mục 2.3); `details.pickup/dropoff.reason` ∈ `OUTSIDE_TOTAL_POLYGON`, `UNSERVICEABLE_COMPONENT` (lớp 1), `NO_ROAD_ACCESS`, `NOT_ROUTABLE_FROM_ANCHOR`, `BEYOND_MAX_ROAD_DISTANCE` (lớp 2) |
| Phiên bản thiếu lớp 2 | Trip API trả 503 `SERVICE_AREA_NOT_CONFIGURED` nếu `source_json` không có `serviceability` (v1/v2 không dùng được cho API nữa; vẫn đánh giá được bằng `boundary_eval`) |
| Bằng chứng ranh giới lịch sử | `scripts/osm/export_historic_boundaries.sh` + `MANIFEST_HISTORIC` (tách khỏi `MANIFEST` để version id v1/v2 tái lập được) |
| Ảnh Docker dùng chung | `backend` và `service-area-build` cùng tag `ridesharing-backend:local` (trước đây `service-area-build` có ảnh riêng, dễ chạy mã cũ) |
| Chống ghi đè bằng chứng | `ensure_new_bundle`: không ghi vào bundle đã tồn tại; chạy lại dùng `--out` khác |
| Khảo sát | Nhóm chọn trước khi bắt đầu phiên (quota trần 90/nhóm); `duration_s` (migration `0004`) tính từ start token ký HMAC; QC2 chỉ gắn cờ; rate limit Redis khóa băm; xóa theo mã phiên (ADMIN) |
