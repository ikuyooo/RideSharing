# KIỂM KÊ MÃ NGUỒN CHUẨN TẠI COMMIT HEAD (CANONICAL SOURCE INVENTORY)

- **Repository Root**: `C:\RideSharing` (`C:/RideSharing`)
- **Commit HEAD**: `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`
- **Commit Parent (`HEAD^`)**: `d9a2a324d7a887ceaeff52a82b8a45bcad6d0ea9`
- **Git Tree SHA**: `2126a22d634e455e28bddf47d0d5fbf699fcc640`
- **Tổng số file được Git theo dõi (`git ls-files`)**: `463` files

---

## 1. Kiểm kê 12 Module trong `backend/app/modules/`

Tại `HEAD = f97a5092ece737d70051d08e6e3604e6a0c6bd1d`, thư mục `backend/app/modules/` có **đúng 12 module** (không tồn tại các thư mục `matching`, `dispatch`, `blockchain` hay `simulator`):

| STT | Tên Module | Các file thực tế trong module | Các bảng CSDL sở hữu (`models.py`) | Trạng thái hiện thực tại Phase 3 |
|---|---|---|---|---|
| 1 | `booking` | `__init__.py`, `models.py`, `service.py` | `bookings`, `seat_holds`, `idempotency_records` | **Helper + Schema**: Có `booking_views()` (`service.py:29`) và `set_current_estimated_price()` (`service.py:40`) phục vụ P2/P3 và các cột/ràng buộc/trigger bảo vệ giá P3 trên `bookings`. Chưa có luồng tạo booking, giữ ghế (`seat_holds`), hay `Offer Cascade` (thuộc Phase 4). |
| 2 | `candidate` | `__init__.py`, `api.py`, `constraints.py`, `generator.py`, `models.py`, `service.py` | `candidate_runs`, `ride_candidates` | **Đã hiện thực (P2 + P3)**: Sinh ứng viên 3 dịch vụ nội đô (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`), kiểm tra 11 ràng buộc cứng (`HC01`–`HC11`), tích hợp `PoolPricingCheck` (`generator.py:415-422`) cho Nhánh A và hàm `offerable()` (`service.py:42-43`). |
| 3 | `driver` | `__init__.py`, `api.py`, `models.py`, `schemas.py`, `service.py` | `driver_profiles`, `vehicles`, `driver_locations` | **Đã hiện thực (P1 + P2)**: Quản lý hồ sơ tài xế, phương tiện (`BIKE`, `CAR4`), luồng nộp/duyệt KYC mock (S7), cập nhật vị trí PostGIS, trạng thái `availability` (`OFFLINE`, `IDLE`, `BUSY`) và truy vấn tài xế lân cận (`nearby_idle_drivers`, `driver_snapshots`). |
| 4 | `fund` | `__init__.py`, `chain.py`, `models.py`, `service.py` | `driver_payouts`, `fund_ledger` | **Đã hiện thực đầy đủ cho P3**: Sổ cái `fund_ledger` chỉ-ghi-thêm (append-only), chuỗi số dư khóa advisory lock `pg_advisory_xact_lock`, ghi nhận `record_settlement()` lũy đẳng, `seed_fund()`, `settlement_for_completed_booking()`, đối soát `reconcile()` (G12), và giao diện đồng bộ on-chain `FundChainSync(Protocol)` + `LedgerEvent` (`chain.py:14,22`) — chưa có hiện thực Blockchain (P9). |
| 5 | `identity` | `__init__.py`, `api.py`, `cli.py`, `deps.py`, `models.py`, `schemas.py`, `security.py`, `service.py` | `users`, `refresh_tokens` | **Đã hiện thực đầy đủ (P1)**: Đăng ký, đăng nhập (`Argon2id`), JWT access token (15 phút), xoay vòng `refresh_tokens` theo `family_id` chống dùng lại, RBAC (`PASSENGER`, `DRIVER`, `ADMIN`), khai báo giới tính tự nguyện (`UNVERIFIED`). |
| 6 | `intercity` | `__init__.py`, `models.py` | `scheduled_trips`, `seat_bookings` | **Chỉ mới có Schema (P1)**: Đã định nghĩa ORM models và CHECK constraints (`ck_scheduled_trips_min_seats_rules`, `ck_scheduled_trips_seat_price_band`, `ck_scheduled_trips_seats_within_capacity`). Logic nghiệp vụ liên tỉnh thuộc Phase 5 (biểu giá/phụ phí liên tỉnh đã có trong `pricing/tariff.py` và `pricing/settlement.py`). |
| 7 | `jobs` | `__init__.py`, `models.py` | `scheduled_jobs` | **Chỉ mới có Schema (P1)**: Đã có bảng `scheduled_jobs` và partial index `idx_scheduled_jobs_due`. Worker quét hàng đợi `SELECT ... FOR UPDATE SKIP LOCKED` thuộc Phase 4. |
| 8 | `ml_models` | `__init__.py`, `models.py`, `survey_api.py`, `survey_derive.py`, `survey_design.py`, `survey_guard.py`, `survey_schemas.py`, `survey_service.py`, `survey_stats.py` | `survey_respondents`, `survey_responses` | **Đã hiện thực Khảo sát S1 (P1)**: Thiết kế thực nghiệm lựa chọn rời rạc S1 (ma trận D2), kiểm soát chất lượng (`QC1`–`QC3`), rate-limit ẩn danh qua Redis, xuất CSV cho `5-fold GroupKFold` và `H4`, ước lượng thử nghiệm Conditional Logit (`survey_stats.py`). Các mô hình `P(match)`, `P(fulfill)`, `LGBMRanker` thuộc Phase 8. |
| 9 | `pooling` | `__init__.py`, `insertion.py`, `models.py`, `pricing_state.py`, `repository.py` | `ride_plans`, `ride_participants`, `ride_stops` | **Đã hiện thực (P2 + P3)**: Thuật toán chèn điểm đón/trả động `insert()` (`insertion.py`), tính `plan_extent()` (`D_plan`, `T_plan`), đọc kế hoạch đang mở (`repository.py`), đọc/lưu trạng thái định giá không mất độ chính xác `plan_pricing_states()` và `store_plan_pricing()` có kiểm tra `plan_version` (`pricing_state.py`). |
| 10 | `pricing` | `__init__.py`, `cancellation.py`, `models.py`, `money.py`, `params.py`, `pool.py`, `pool_check.py`, `seed.py`, `service.py`, `settlement.py`, `tariff.py` | `pricing_configs` | **Đã hiện thực đầy đủ (P1 + P3)**: Số học phân số chính xác `Fraction` (`money.py`), nạp/kiểm tra tham số (`params.py`, `service.py`, `seed.py`), 5 biểu giá & phụ phí (`tariff.py`), định giá ghép 2 cận & chèn động `D1`–`D6` (`pool.py`, `pool_check.py`), tất toán (`settlement.py`), phí hủy & No-Show (`cancellation.py`). |
| 11 | `routing` | `__init__.py`, `cache.py`, `factory.py`, `models.py`, `osrm.py`, `provider.py`, `service.py` | `pickup_points` | **Đã hiện thực đầy đủ (P1 + P2)**: Kết nối OSRM (`car` + `motorbike`), gọi 1 lệnh `/table` duy nhất mỗi profile (`osrm.py`), bộ nhớ đệm Redis theo Geohash (`cache.py`), loại trừ phà (`exclude=ferry`), xử lý lỗi tường minh không dùng khoảng cách chim bay. Bảng `pickup_points` mới ở mức schema cho C9. |
| 12 | `trip` | `__init__.py`, `api.py`, `boundary_eval.py`, `historic_sources.py`, `models.py`, `pickup_survey.py`, `rules.py`, `schemas.py`, `service.py`, `service_area_approve.py`, `service_area_build.py`, `service_area_compare.py` | `trip_requests`, `service_areas` | **Đã hiện thực đầy đủ (P1)**: Phân loại tự động `URBAN` / `INTERCITY` 2 tầng (PostGIS + vùng đệm đường bộ OSRM `15 km`), kiểm tra 5 dịch vụ và cửa sổ thời gian đặt (`rules.py`), quản lý phiên bản vùng phục vụ (`v1`–`v5`). |

---

## 2. Kiểm kê các Router và API Endpoints đang gắn vào FastAPI (`backend/app/main.py`)

Trong `backend/app/main.py:14-25`, hàm `create_app()` đăng ký **6 router** với tổng cộng **26 route handlers** (25 endpoint JSON + 1 trang HTML `include_in_schema=False`). Không có endpoint booking/offer/ride nào:

| Router / Module | File định nghĩa | HTTP Method & Path | Phân quyền / Vai trò | Mô tả chức năng |
|---|---|---|---|---|
| `health` | `app/api/health.py` | `GET /health/live` | Public | Kiểm tra tiến trình API đang sống (`200 OK`). |
| `health` | `app/api/health.py` | `GET /health/ready` | Public | Kiểm tra kết nối thực tới PostgreSQL, Redis, OSRM (`car`, `motorbike`) và `config_baseline` (`200` hoặc `503`). |
| `identity` | `app/modules/identity/api.py` | `POST /api/auth/register` | Public | Đăng ký tài khoản `PASSENGER` hoặc `DRIVER` (từ chối tự đăng ký `ADMIN`). |
| `identity` | `app/modules/identity/api.py` | `POST /api/auth/login` | Public | Đăng nhập, trả về cặp `access_token` và `refresh_token`. |
| `identity` | `app/modules/identity/api.py` | `POST /api/auth/refresh` | Public (Refresh Token) | Xoay vòng `refresh_token` theo `family_id`, thu hồi toàn bộ họ token nếu phát hiện dùng lại. |
| `identity` | `app/modules/identity/api.py` | `POST /api/auth/logout` | Public (Refresh Token) | Thu hồi `refresh_token`. |
| `identity` | `app/modules/identity/api.py` | `GET /api/users/me` | Authenticated (`get_current_user`) | Lấy thông tin tài khoản hiện tại. |
| `identity` | `app/modules/identity/api.py` | `PUT /api/users/me/gender` | Authenticated (`get_current_user`) | Cập nhật giới tính tự khai báo (`gender_verification_status = UNVERIFIED`). |
| `driver` | `app/modules/driver/api.py` | `GET /api/driver/profile` | `DRIVER` | Xem hồ sơ tài xế và danh sách phương tiện. |
| `driver` | `app/modules/driver/api.py` | `POST /api/driver/vehicles` | `DRIVER` | Đăng ký phương tiện (`BIKE` sức chứa 1, `CAR4` sức chứa 4 từ baseline). |
| `driver` | `app/modules/driver/api.py` | `POST /api/driver/kyc/submit` | `DRIVER` | Nộp hồ sơ KYC giả lập (`PENDING`). |
| `driver` | `app/modules/driver/api.py` | `PUT /api/driver/settings` | `DRIVER` | Cập nhật cấu hình nhận chuyến (`accepts_urban`, `pool_enabled`, `accepts_intercity`, giới hạn đi vòng). |
| `driver` | `app/modules/driver/api.py` | `PUT /api/driver/location` | `DRIVER` | Cập nhật tọa độ GPS hiện tại vào `driver_locations`. |
| `driver` | `app/modules/driver/api.py` | `PUT /api/driver/availability` | `DRIVER` | Cập nhật trạng thái `OFFLINE` / `IDLE` / `BUSY` và `active_vehicle_id`. |
| `driver` | `app/modules/driver/api.py` | `POST /api/admin/drivers/{driver_id}/kyc-review` | `ADMIN` | Admin phê duyệt (`VERIFIED`) hoặc từ chối (`REJECTED`) KYC của tài xế. |
| `trip` | `app/modules/trip/api.py` | `POST /api/trip-requests` | `PASSENGER` | Tạo yêu cầu chuyến đi, tự động phân loại `URBAN`/`INTERCITY` và lọc các `allowed_service_codes`. |
| `trip` | `app/modules/trip/api.py` | `GET /api/trip-requests/{trip_id}` | Owner (`PASSENGER`) hoặc `ADMIN` | Xem chi tiết yêu cầu chuyến đi đã tạo. |
| `candidate` | `app/modules/candidate/api.py:26` | `POST /api/admin/candidates/runs` | `ADMIN` | Chạy bộ sinh ứng viên (P2 + định giá P3) cho một `request_id` và lưu audit vào `candidate_runs` + `ride_candidates`. |
| `candidate` | `app/modules/candidate/api.py:33` | `GET /api/admin/candidates/runs/{run_id}` | `ADMIN` | Truy xuất kết quả chạy ứng viên, độ trễ từng pha, số lần gọi OSRM và danh sách ứng viên khả thi. |
| `ml_models` (`survey_api`) | `app/modules/ml_models/survey_api.py` | `GET /survey/s1` | Public (HTML) | Giao diện trang khảo sát lựa chọn rời rạc S1 (bản nháp). |
| `ml_models` (`survey_api`) | `app/modules/ml_models/survey_api.py` | `POST /api/survey/s1/sessions` | Public (Rate-limited) | Khởi tạo phiên khảo sát ẩn danh, cấp block thiết kế và `start_token` ký HMAC. |
| `ml_models` (`survey_api`) | `app/modules/ml_models/survey_api.py` | `POST /api/survey/s1/sessions/{respondent_id}/submit` | Public (Rate-limited) | Nộp câu trả lời khảo sát S1, gắn cờ chất lượng (`QC1`–`QC3`). |
| `ml_models` (`survey_api`) | `app/modules/ml_models/survey_api.py` | `GET /api/admin/survey/s1/export/{table}` | `ADMIN` | Xuất CSV dữ liệu khảo sát (`respondents`, `choices`, `fairness_h4`). |
| `ml_models` (`survey_api`) | `app/modules/ml_models/survey_api.py` | `GET /api/admin/survey/s1/quota` | `ADMIN` | Xem tiến độ hạn ngạch mẫu khảo sát theo nhóm (`STUDENT`, `WORKER`). |
| `ml_models` (`survey_api`) | `app/modules/ml_models/survey_api.py` | `GET /api/admin/survey/s1/rejections` | `ADMIN` | Xem thống kê lỗi `422` theo ngày và mã lỗi (Quy tắc R3). |
| `ml_models` (`survey_api`) | `app/modules/ml_models/survey_api.py` | `DELETE /api/admin/survey/s1/respondents/{respondent_id}` | `ADMIN` | Xóa dữ liệu khảo sát của một mã phiên theo yêu cầu người tham gia. |

*(Tổng cộng: `2` health + `6` identity + `7` driver + `2` trip + `2` candidate + `7` survey = **`26` route handlers**).*

---

## 3. Kiểm kê 6 File Migration (`backend/alembic/versions/`) và 23 Bảng CSDL

### 3.1. Chuỗi 6 Migration thực tế

| Revision | Down Revision | Tên file chính xác | Nội dung chính |
|---|---|---|---|
| `0001` | `None` | `0001_p1_core_schema.py` | Cài đặt `postgis`, tạo 19 bảng cốt lõi theo Mục 56.1/56.2/55 và Baseline Mục 5 (`pickup_points`, `pricing_configs`, `scheduled_jobs`, `service_areas`, `users`, `driver_profiles`, `idempotency_records`, `refresh_tokens`, `trip_requests`, `driver_locations`, `seat_holds`, `vehicles`, `ride_plans`, `scheduled_trips`, `bookings`, `ride_candidates`, `driver_payouts`, `fund_ledger`, `ride_participants`, `seat_bookings` — *20 bảng*), kèm 2 trigger bất biến trên `pricing_configs`. |
| `0002` | `0001` | `0002_p1_survey_s1_draft_storage.py` | Tạo 2 bảng khảo sát ẩn danh `survey_respondents` và `survey_responses`. |
| `0003` | `0002` | `0003_p1_service_area_excluded_layer.py` | Mở rộng `ck_service_areas_area_type` cho phép `'URBAN'`, `'TOTAL'`, `'EXCLUDED'` (`GEO-03`/`GEO-04`). |
| `0004` | `0003` | `0004_p1_survey_s1_duration.py` | Thêm cột `duration_s` và `ck_survey_respondents_duration_non_negative` vào `survey_respondents` (`QC2`). |
| `0005` | `0004` | `0005_p2_routing_candidate_pooling.py` | Tạo 2 bảng `candidate_runs` và `ride_stops`; thêm `availability`, `active_vehicle_id` vào `driver_locations`; thêm `direct_distance_m`, `direct_duration_s` vào `ride_participants`; thêm các cột truy vết P2 vào `ride_candidates`. |
| `0006` | `0005` | `0006_p3_pricing_fund.py` | Thêm các cột định giá/truy vết P3 vào `bookings`, `ride_plans`, `ride_participants`, `driver_payouts`, `fund_ledger`; bổ sung 8 `CHECK` constraints, 2 `UNIQUE` partial indexes và **4 PostgreSQL triggers** bảo vệ tính bất biến của sổ cái Quỹ bảo đảm, bảng `driver_payouts`, và giá đã khóa (`is_price_frozen` / `MATCHED_LOCKED` / `UNMATCHED_LOCKED`). |

*(Tổng số bảng ứng dụng: `20` bảng ở `0001` + `2` bảng ở `0002` + `2` bảng ở `0005` = **`24` bảng ORM** trong `metadata.tables`, khớp 100% với `test_architecture.py:test_every_table_is_owned_by_exactly_one_module`).*

### 3.2. Chi tiết các Trigger và Ràng buộc CSDL của Phase 3 (`0006_p3_pricing_fund.py`)

1. **Trên `bookings`**:
   - Cột mới: `pricing_version VARCHAR(64)`.
   - Trigger `trg_bookings_pool_locked_price`: Chặn thay đổi `final_price_vnd`, `price_status`, `unmatched_cause`, `pricing_version` sau khi `price_status IN ('MATCHED_LOCKED', 'UNMATCHED_LOCKED')` (cho phép Phase 4 cập nhật `ride_status`, `escrow_status`).
2. **Trên `ride_plans`**:
   - Cột mới: `pricing_version VARCHAR(64)`, `plan_fare_exact TEXT`, `driven_m_since_start FLOAT DEFAULT 0`, `started_at TIMESTAMPTZ`.
   - Ràng buộc: `ck_ride_plans_driven_m_non_negative` (`driven_m_since_start >= 0`).
3. **Trên `ride_participants`**:
   - Cột mới: `fare_exact_rational TEXT` (lưu chuỗi phân số `"num/den"` không mất độ chính xác).
   - Trigger `trg_ride_participants_frozen`: Khi `OLD.is_price_frozen = true`, cấm mở khóa (`NEW.is_price_frozen = false`) và cấm sửa các trường giá (`fare_exact_vnd`, `fare_exact_rational`, `fare_charged_vnd`, `rounding_absorbed_vnd`, `private_fare_vnd`) — bảo đảm cổng `G08` ngay ở tầng CSDL.
4. **Trên `driver_payouts`**:
   - Cột mới: `payout_kind VARCHAR(24) DEFAULT 'RIDE_SETTLEMENT'`, `pricing_version VARCHAR(64)`, `pool_policy_version VARCHAR(64)`, `unmatched_cause VARCHAR(32) DEFAULT 'NONE'`, `created_at TIMESTAMPTZ`.
   - Ràng buộc: `ck_driver_payouts_payout_kind`, `ck_driver_payouts_payout_amounts_non_negative`, `ck_driver_payouts_payout_total_is_base_plus_guarantee` (`total_driver_payout_vnd = driver_base_amount_vnd + guarantee_amount_vnd`), `ck_driver_payouts_payout_gross_is_split_exactly` (`gross_fare_charged_vnd = driver_base_amount_vnd + platform_net_amount_vnd + fund_contribution_vnd`).
   - Trigger: `trg_driver_payouts_immutable` (`BEFORE UPDATE OR DELETE`, cấm sửa/xóa dòng sau khi đã ghi).
5. **Trên `fund_ledger`**:
   - Cột mới: `ride_plan_id UUID`, `pricing_version VARCHAR(64)`, `pool_policy_version VARCHAR(64)`, `reason VARCHAR(64)`.
   - Ràng buộc:
     - `ck_fund_ledger_ledger_sign_by_type`: `GUARANTEE_PAYOUT` phải `< 0`; `CONTRIBUTION`, `CANCEL_FEE_INFLOW`, `INITIAL_SEED` phải `> 0`.
     - `ck_fund_ledger_ledger_balance_non_negative`: `balance_after_vnd >= 0`.
     - `ck_fund_ledger_ledger_booking_by_type`: `(entry_type = 'INITIAL_SEED') = (booking_id IS NULL)`.
     - `ck_fund_ledger_ledger_pricing_version_by_type`: `entry_type = 'INITIAL_SEED' OR pricing_version IS NOT NULL`.
   - Unique Partial Indexes: `uq_fund_ledger_single_seed` (`UNIQUE (entry_type) WHERE entry_type = 'INITIAL_SEED'`), `uq_fund_ledger_booking_entry` (`UNIQUE (booking_id, entry_type) WHERE booking_id IS NOT NULL`).
   - Trigger: `trg_fund_ledger_guard` (`BEFORE INSERT OR UPDATE OR DELETE`):
     - Khi `INSERT`: lấy `pg_advisory_xact_lock`, kiểm tra `NEW.balance_after_vnd = COALESCE(last_balance, 0) + NEW.amount_signed_vnd` để đảm bảo chuỗi số dư liên tục không đứt gãy.
     - Khi `UPDATE`: chỉ cho phép cập nhật duy nhất cột `onchain_tx_hash` từ `NULL` sang chuỗi giao dịch Blockchain (phục vụ Phase 9); cấm sửa mọi trường khác.
     - Khi `DELETE`: từ chối với lỗi `restrict_violation` (sổ cái chỉ-ghi-thêm append-only).

