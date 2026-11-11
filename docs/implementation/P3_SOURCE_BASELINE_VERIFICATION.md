# PHASE 3 — SOURCE BASELINE & REPOSITORY VERIFICATION

**Dự án:** Ride_Sharing  
**Phạm vi kiểm toán:** Phase 0 → Phase 3 (Standardization, Verification & Acceptance Preparation)  
**Ngày kiểm toán:** 2026-11-09  
**Commit tham chiếu & HEAD thực tế:** `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` (`main`)

---

## 1. Xác minh Git & Repository Root

Kết quả kiểm tra trực tiếp bằng lệnh Git tại thời điểm bắt đầu phiên kiểm toán:

| Hạng mục | Giá trị thực tế | Bằng chứng lệnh / Nguồn |
|---|---|---|
| **Repository Root** | `C:/RideSharing` (`C:\RideSharing`) | `git rev-parse --show-toplevel` |
| **Git Branch** | `main` (tracking `origin/main`) | `git status --short --branch` (`## main...origin/main`) |
| **HEAD Commit** | `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` | `git rev-parse HEAD` |
| **Remote Origin** | `https://github.com/ikuyooo/RideSharing.git` (fetch & push) | `git remote -v` |
| **So sánh với commit tham chiếu** | Trùng khớp 100% (`0` commit lệch so với `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`) | `git log -n 5 --oneline` |
| **Trạng thái Working Tree ban đầu** | Clean (`0` modified, `0` untracked) | `git status --short` |
| **Tổng số file Git Tracked** | `463` files | `git ls-files` |

### Lịch sử 5 commit gần nhất trên nhánh `main`

```text
f97a509 update
2dc3da6 Complete Phase 2 candidate generation and pooling
00037e1 Update progress report for Phase 0 and Phase 1
8ab241d Complete Phase 1 database schema, identity, driver, trip and survey S1
2c807c0 Initial repository with Phase 0 infrastructure and baseline
```

---

## 2. Xác minh Môi trường Thực thi (Host & Container Runtime)

| Thành phần | Trạng thái trên máy kiểm toán hiện tại | Hệ quả đối với kiểm thử |
|---|---|---|
| **Hệ điều hành Host** | Windows (PowerShell) | Chạy trực tiếp các công cụ và Python trên host |
| **Host Python** | `Python 3.12.10` (`C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe`) | Chạy được toàn bộ module thuần Python (`app.modules.pricing`, `app.core.config_baseline`) và kiểm tra AST (`test_architecture.py`) |
| **Packages trên Host Python** | Có `PyYAML 6.0.3`, `numpy 2.5.4`, `networkx 3.7`, `requests 2.34.2`; **không có** `pytest`, `hypothesis`, `sqlalchemy`, `alembic`, `fastapi`, `httpx`, `psycopg`, `geoalchemy2`, `redis` | Các bài test thuần Python (48 hàm / 67 test cases trong `test_config_baseline.py`, `test_architecture.py`, `test_pricing_regression.py`, `test_pricing_pool.py`, `test_pricing_cancellation.py`) chạy PASS trực tiếp qua Python 3.12.10; các bài test cần `hypothesis`/`sqlalchemy`/DB/OSRM được ghi nhận `NOT_EXECUTED` trên máy hiện tại |
| **Docker CLI / Daemon** | Không cài đặt trên máy hiện tại (`docker: CommandNotFoundException`) | Không thể khởi chạy container `postgres`, `redis`, `osrm-car`, `osrm-motorbike`, `backend` trong phiên này |
| **WSL2** | Không cài đặt (`WSL is not installed` / `WSL_E_WSL_OPTIONAL_COMPONENT_REQUIRED`) | Các kết quả chạy trong container WSL2 Linux (`Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.41`) tại ngày `2026-11-04` và `2026-11-05` được phân loại nghiêm ngặt là `HISTORICAL_EVIDENCE_ONLY` |

---

## 3. Xác minh Cấu hình Baseline Đang Khóa (`MVP_CONFIG_BASELINE_V1`)

Đối chiếu trực tiếp giữa `docs/pre/mvp_config_baseline_v1.md` (§4), `config/mvp_config_baseline_v1.yaml` (dòng 1–140), `backend/app/core/config_baseline.py` (dòng 16–57), `backend/app/modules/pricing/params.py` (dòng 18–194) và `backend/app/modules/pricing/seed.py` (dòng 20–56):

| Khóa cấu hình | Giá trị trong `config/mvp_config_baseline_v1.yaml` | Vị trí nạp / kiểm tra trong code | Trạng thái |
|---|---|---|---|
| `config_baseline_version` | `"MVP_CONFIG_BASELINE_V1"` | `app/core/config_baseline.py:16,39` (`EXPECTED_BASELINE_VERSION`) | `VERIFIED` |
| `config_status` | `"LOCKED_AND_APPROVED"` | `app/core/config_baseline.py:17,43` (`EXPECTED_STATUS`) | `VERIFIED` |
| `blueprint_revision` | `"Revision_9"` | `config/mvp_config_baseline_v1.yaml:10`, `test_config_baseline.py:21` | `VERIFIED` |
| `pricing_version` | `"price_v9_two_sided_bounded"` | `app/modules/pricing/params.py:139`, `seed.py:24` | `VERIFIED` |
| `pool_policy_version` | `"guarantee_fund_v2_post_rounding_hourly_gate"` | `app/modules/pricing/params.py:140`, `seed.py:25` | `VERIFIED` |
| `bike_urban` | `base_vnd=10000`, `per_km_vnd=4500`, `per_min_vnd=250`, `commission_rate=0.20`, `rounding_step_vnd=1000`, `capacity=1` | `app/modules/pricing/params.py:141-147` | `VERIFIED` |
| `car_urban` | `base_vnd=20000`, `per_km_vnd=11000`, `per_min_vnd=500`, `extra_stop_fee_vnd=5000`, `stop_dwell_time_s=60`, `commission_private=0.20`, `commission_pool_total=0.15`, `platform_net_pool_rate=0.12`, `fund_contribution_rate=0.03`, `d_min=0.20`, `d_max=0.60`, `on_lower_bound_infeasible="REJECT"`, `allow_dynamic_insertion_after_partial_lock=true`, `d_matched_typical=0.25`, `party_seat_surcharge_gamma=0.35`, `detour_weight_lambda=1.0`, `walk_weight_mu=2.0`, `unmatched_passenger_share_alpha=0.50`, `enforce_driver_hourly_rate_gate=true`, `driver_hourly_rate_tolerance_eps=0.00`, `rounding_step_vnd=1000`, `capacity=4`, `max_party_seats_pool=2`, `pool_lock_remaining_km=3.0`, `k_max_stops=8`, `n_pool_max_candidates=20` | `app/modules/pricing/params.py:148-174` | `VERIFIED` |
| `car_intercity_private` | `base_vnd=150000`, `per_km_vnd=7500`, `commission_rate=0.15`, `rounding_step_vnd=1000` | `app/modules/pricing/params.py:175-180` | `VERIFIED` |
| `car_intercity_pool` | `commission_seat=0.10`, `commission_topup=0.15`, `min_seats_ref=3`, `allowed_driver_min_seats=[2, 3]`, `default_min_seats_to_run=3`, `seat_price_band=[0.90, 1.10]`, `door_surcharge_per_km_vnd=4000`, `max_corridor_deviation_km=10.0`, `rounding_step_vnd=1000` | `app/modules/pricing/params.py:181-191` | `VERIFIED` |
| `cancellation_policy` | `urban_free_cancel_grace_s=120`, `urban_no_show_wait_min=5`, `urban_single_cancel_fee_rate=0.20`, `urban_single_cancel_fee_cap_vnd=20000`, `urban_pool_cancel_fee_rate_on_quote=0.20`, `intercity_private_free_cancel_lead_h=2.0`, `intercity_private_late_cancel_fee_rate=0.20`, `intercity_pool_free_cancel_before_h=72`, `intercity_pool_cancel_fee_rate_72h_to_24h=0.50`, `intercity_pool_cancel_fee_rate_after_24h=1.00` | `app/modules/pricing/params.py:120-133,192` | `VERIFIED` |
| `booking_and_concurrency.initial_guarantee_fund_seed_vnd` | `5000000` | `app/modules/pricing/params.py:193`, `app/modules/fund/service.py:124` | `VERIFIED` |

---

## 4. Xác minh Chuỗi Alembic Migrations (`0001` → `0006`)

Toàn bộ các file migration nằm trong `backend/alembic/versions/`:

| Thứ tự | Revision ID | Down Revision | File | Nội dung chính |
|---|---|---|---|---|
| 1 | `0001_p1_core_schema` | `None` | `backend/alembic/versions/0001_p1_core_schema.py` | Bật extension `postgis`; tạo 19 bảng cốt lõi & phụ trợ (`users`, `refresh_tokens`, `driver_profiles`, `vehicles`, `driver_locations`, `service_areas`, `pickup_points`, `pricing_configs`, `trip_requests`, `ride_plans`, `ride_candidates`, `bookings`, `ride_participants`, `scheduled_trips`, `seat_bookings`, `seat_holds`, `driver_payouts`, `fund_ledger`, `idempotency_records`, `scheduled_jobs`) + hàm trigger `pricing_configs_immutable()` gắn vào 2 trigger `trg_pricing_configs_immutable` và `trg_pricing_configs_no_truncate` |
| 2 | `0002_p1_survey_s1` | `0001_p1_core_schema` | `backend/alembic/versions/0002_p1_survey_s1.py` | Tạo 2 bảng `survey_respondents` và `survey_responses` |
| 3 | `0003_p1_hardening` | `0002_p1_survey_s1` | `backend/alembic/versions/0003_p1_hardening.py` | Bổ sung 19 `CHECK` constraints bảo vệ domain (capacity, status, toạ độ Hà Nội/Miền Bắc, khoảng giá, giới tính, KYC) và unique partial index `ix_vehicles_one_active_per_driver` |
| 4 | `0004_p1_service_area_audit` | `0003_p1_hardening` | `backend/alembic/versions/0004_p1_service_area_audit.py` | Thêm cột `validation_Meta` (`JSONB`) và `ck_service_areas_approved_has_approver` cho bảng `service_areas` |
| 5 | `0005_p2_routing_candidate_pooling` | `0004_p1_service_area_audit` | `backend/alembic/versions/0005_p2_routing_candidate_pooling.py` | Tạo 2 bảng mới `candidate_runs` và `ride_stops` (`uq_ride_stops_ride_plan_id_seq` `DEFERRABLE INITIALLY DEFERRED`); mở rộng `driver_profiles` (`max_additional_pickups`, `current_trip_started_at`), `ride_plans` (`vehicle_id`, `started_at`, `total_distance_m`, `total_duration_s`, `total_stops`), `ride_candidates` (các cột routing/detour/evaluation JSONB); thêm GIST index `ix_driver_locations_geom_4326_gist` và `ix_driver_locations_driver_id_recorded_at` |
| 6 | `0006_p3_pricing_fund` | `0005_p2_routing_candidate_pooling` | `backend/alembic/versions/0006_p3_pricing_fund.py` | Mở rộng `ride_participants` (`fare_exact_rational`, `private_fare_vnd`, `detour_ratio`, `walk_m`), `bookings` (`unmatched_cause`), `ride_candidates` (`pricing_version`, `pool_policy_version`, `fare_exact_rational`, `rounding_absorbed_vnd`, `driver_payout_vnd`, `platform_fee_vnd`, `fund_contribution_vnd`, `discount_rate`, `price_breakdown`), `driver_payouts` (`gross_fare_charged_vnd`, `platform_fee_vnd`, `fund_contribution_vnd`, `cancelled_co_rider_share_vnd`), `fund_ledger` (`ride_plan_id`, `reason`); thêm 4 hàm trigger bất biến (`fund_ledger_guard`, `driver_payouts_immutable`, `ride_participants_frozen_guard`, `bookings_locked_pool_price_guard`) |

**Tổng số bảng ứng dụng sau `0006_p3_pricing_fund`:** **24 bảng ứng dụng** (tất cả 24 bảng đều được ánh xạ trong SQLAlchemy `metadata.tables` qua `backend/app/db/models.py`, được kiểm chứng bởi `test_models_cover_all_migrated_tables` trong `backend/tests/test_schema.py:42-45`).

---

## 5. Kiểm kê Cấu trúc Module trong `backend/app/modules/`

Toàn bộ 14 module theo Mục 54.1 của Đặc tả Revision 9 đã tồn tại trong `backend/app/modules/`:

| STT | Module | Trạng thái tại HEAD (`f97a509`) | Các file hiện có | Các bảng sở hữu (`models.py`) |
|---|---|---|---|---|
| 1 | `identity` | **IMPLEMENTED (Phase 1)** | `__init__.py`, `api.py`, `cli.py`, `deps.py`, `models.py`, `schemas.py`, `security.py`, `service.py` | `users`, `refresh_tokens` |
| 2 | `driver` | **IMPLEMENTED (Phase 1–2)** | `__init__.py`, `api.py`, `models.py`, `schemas.py`, `service.py` | `driver_profiles`, `vehicles`, `driver_locations` |
| 3 | `trip` | **IMPLEMENTED (Phase 1)** | `__init__.py`, `api.py`, `models.py`, `schemas.py`, `service.py` | `service_areas`, `pickup_points`, `trip_requests` |
| 4 | `routing` | **IMPLEMENTED (Phase 2)** | `__init__.py`, `cache.py`, `osrm.py`, `provider.py`, `types.py` | *(Không sở hữu bảng DB)* |
| 5 | `candidate` | **IMPLEMENTED (Phase 2–3)** | `__init__.py`, `api.py`, `constraints.py`, `generator.py`, `models.py`, `schemas.py`, `service.py` | `candidate_runs`, `ride_candidates` |
| 6 | `pooling` | **IMPLEMENTED (Phase 2–3)** | `__init__.py`, `insertion.py`, `models.py`, `pricing_state.py`, `repository.py`, `types.py` | `ride_plans`, `ride_participants`, `ride_stops` |
| 7 | `pricing` | **IMPLEMENTED (Phase 3)** | `__init__.py`, `cancellation.py`, `models.py`, `money.py`, `params.py`, `pool.py`, `pool_check.py`, `seed.py`, `service.py`, `settlement.py`, `tariff.py` | `pricing_configs` |
| 8 | `fund` | **IMPLEMENTED (Phase 3)** | `__init__.py`, `chain.py`, `models.py`, `service.py` | `driver_payouts`, `fund_ledger` |
| 9 | `booking` | **PARTIAL (Phase 1 Schema + Phase 3 Helper; Phase 4 Lifecycle chưa triển khai)** | `__init__.py`, `models.py`, `service.py` | `bookings`, `scheduled_trips`, `seat_bookings`, `seat_holds`, `idempotency_records`, `scheduled_jobs` |
| 10 | `ml_models` | **PARTIAL (Phase 1 Survey S1 API; Phase 6 ML chưa triển khai)** | `__init__.py`, `models.py`, `survey_api.py`, `survey_config.py`, `survey_schemas.py`, `survey_service.py` | `survey_respondents`, `survey_responses` |
| 11 | `matching` | **STUB (Phase 4)** | `__init__.py` (chỉ có docstring) | *(Chưa có)* |
| 12 | `dispatch` | **STUB (Phase 4)** | `__init__.py` (chỉ có docstring) | *(Chưa có)* |
| 13 | `blockchain` | **STUB (Phase 5)** | `__init__.py` (chỉ có docstring) | *(Chưa có)* |
| 14 | `simulator` | **STUB (Phase 6–7)** | `__init__.py` (chỉ có docstring) | *(Chưa có)* |

