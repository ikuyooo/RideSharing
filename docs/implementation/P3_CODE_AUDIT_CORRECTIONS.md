# PHASE 3 — CODE AUDIT CORRECTIONS REGISTER

**Dự án:** Ride_Sharing  
**Commit kiểm chứng:** `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`  
**Mục đích:** Ghi nhận và hiệu chỉnh toàn bộ các điểm mô tả chưa chính xác trong báo cáo kiểm toán trước đây, đối chiếu trực tiếp với mã nguồn thực tế tại commit `HEAD`.

---

## Bảng tổng hợp các hiệu chỉnh bắt buộc (10 hạng mục)

| Mã hiệu chỉnh | Nội dung trong báo cáo kiểm toán cũ | Sự thật kỹ thuật trong Source Code (`f97a509`) | File & Dòng code chứng minh | Tác động nếu không hiệu chỉnh |
|---|---|---|---|---|
| **CORR-01** | Ghi nhận hệ thống có **19 HTTP endpoints** và nêu sai đường dẫn nhiều route (`/api/drivers/me`, `/api/drivers/status`, `/api/trips/intents`, `/api/trips/intents/{id}/candidates`, `/api/survey/s1/draft`) | Hệ thống thực tế đăng ký **26 HTTP routes** trên 6 router được mount trong `backend/app/main.py:21-26` (chi tiết toàn bộ 26 route ở Mục 1 bên dưới). Đặc biệt, API sinh ứng viên là **ADMIN-only** (`POST /api/admin/candidates/runs` và `GET /api/admin/candidates/runs/{run_id}` dùng `require_roles("ADMIN")`), không phải `/api/trips/intents/{id}/candidates`. | `backend/app/main.py:21-26`, `backend/app/api/health.py:13-22`, `backend/app/modules/identity/api.py:26-79`, `backend/app/modules/driver/api.py:26-100`, `backend/app/modules/trip/api.py:22-45`, `backend/app/modules/candidate/api.py:22-48`, `backend/app/modules/ml_models/survey_api.py:42-135` | Sai lệch tài liệu API contract khi tích hợp Phase 4 hoặc kiểm thử E2E |
| **CORR-02** | Ghi nhận có **25 bảng ứng dụng** (24 bảng ORM + 1 bảng `survey_responses` ngoài ORM) | Thực tế chỉ có **24 bảng ứng dụng** được tạo qua migrations `0001`–`0006` (cộng bảng kỹ thuật `alembic_version` của Alembic). Cả **24/24 bảng ứng dụng đều được ánh xạ vào SQLAlchemy ORM** (bao gồm cả `SurveyRespondent` và `SurveyResponse` trong `app/modules/ml_models/models.py`). Bảng `test_schema.py` có bài test `test_models_cover_all_migrated_tables` kiểm tra `migrated == set(metadata.tables)`. | `backend/app/db/models.py:1-21`, `backend/app/modules/ml_models/models.py:19-83`, `backend/tests/test_schema.py:42-45` | Gây nhầm lẫn về độ phủ ORM và số lượng bảng khi viết migration Phase 4 |
| **CORR-03** | Ghi nhận `pricing/money.py` định nghĩa kiểu `VND(int)` và hàm `floor_to_step` | `pricing/money.py` thực tế định nghĩa type alias `Money = Fraction`, ngoại lệ `NonIntegralAmount(ArithmeticError)`, và 6 hàm: `q(value) -> Fraction`, `floor_step(amount: Fraction, step: int) -> int`, `exact_vnd(amount: Fraction) -> int`, `to_numeric_2(value: Fraction) -> Decimal`, `to_rational_text(value: Fraction) -> str`, `from_rational_text(text: str) -> Fraction`. Không có kiểu `VND(int)` hay tên hàm `floor_to_step`. | `backend/app/modules/pricing/money.py:14-66` | Gọi sai tên hàm khi viết code Phase 4/5 gọi sang `pricing.money` |
| **CORR-04** | Ghi nhận `pricing/pool.py` có hàm `allocate_two_sided_bounded` và `pooling/insertion.py` có hàm `evaluate_dynamic_insertion`, `insert_stop_pair` | - Trong `pricing/pool.py`, tên hàm thực tế là `allocate_two_sided(target, P, w, floor, cap) -> Allocation`, `price_new_plan(p, riders, d_plan_m, t_plan_s, total_stops) -> PoolPricing`, `price_insertion(p, x: InsertionInput) -> PoolPricing`, `final_price_at_lock(p, private, matched, fare_charged, unmatched_cause) -> int`, `plan_fare`, `gate1`, `gate2`, `seat_factor`, `weight`, `cap`, `raw_floor` (`price_v9_two_sided_bounded` là chuỗi `pricing_version`, không phải tên hàm Python).<br>- Trong `pooling/insertion.py`, tên hàm thực tế là `insert(...) -> InsertionReport`, `simulate(...) -> Simulation`, `plan_extent(...) -> tuple[float, float]`, `evaluate_chain(...) -> Evaluation`. | `backend/app/modules/pricing/pool.py:85-336`, `backend/app/modules/pooling/insertion.py:85-343` | Gọi sai tên hàm khi tích hợp Batch Matching hoặc Booking ở Phase 4 |
| **CORR-05** | Ghi nhận `fund/service.py` có các hàm `lock_participant_at_pool_lock_point`, `settle_completed_booking`, `cancel_booking_with_policy` và `fund/chain.py` có `NoopEscrowPort` | - `fund/service.py` thực tế có các hàm: `balance(session) -> int`, `append_entry(...) -> FundLedgerEntry`, `seed_fund(session, baseline) -> FundLedgerEntry`, `record_settlement(...) -> DriverPayout`, `cancellation_settlement(outcome: CancelOutcome) -> Settlement`, `settlement_for_completed_booking(...) -> BookingSettlement`, `reconcile(session) -> ReconcileReport`, `ledger_total(session) -> int`.<br>- `fund/chain.py` định nghĩa `LedgerEvent` (dataclass) và `FundChainSync(Protocol)` với phương thức `submit(self, event: LedgerEvent) -> str` (không có class `NoopEscrowPort`).<br>- Chuyển trạng thái lock point (`MATCHED_LOCKED` / `UNMATCHED_LOCKED`) khi xe còn cách điểm trả 3 km thuộc state machine của chuyến đi ở Phase 4/5; Phase 3 hiện cung cấp hàm tính giá khóa `final_price_at_lock()` (`pricing/pool.py:310-336`) và DB trigger `bookings_locked_pool_price_guard()` (`0006_p3_pricing_fund.py:175-194`). | `backend/app/modules/fund/service.py:42-227`, `backend/app/modules/fund/chain.py:13-33`, `backend/app/modules/pricing/pool.py:310-336`, `backend/alembic/versions/0006_p3_pricing_fund.py:175-194` | Ngộ nhận rằng orchestration khóa giá tại 3 km và state machine hủy/hoàn thành booking đã được viết xong trong `fund/service.py` |
| **CORR-06** | Ghi nhận `booking/service.py` có `get_booking` và `pooling/repository.py` có `find_open_pool_plans_near`, `get_plan_for_update` | - `booking/service.py` thực tế có `BookingView` (frozen dataclass), `booking_views(session, booking_ids) -> dict[uuid.UUID, BookingView]` và `set_current_estimated_price(session, booking_id, price_vnd) -> None`.<br>- `pooling/repository.py` thực tế có `open_plan_drivers(session) -> dict[uuid.UUID, uuid.UUID]` và `plan_records(session, plan_ids) -> list[PlanRecord]`.<br>- `pooling/pricing_state.py` thực tế có `plan_pricing_states(session, plan_ids) -> dict[uuid.UUID, PlanPricingState]`, `store_plan_pricing(...) -> int` (optimistic locking qua `WHERE id = :pid AND version = :v`), và `participant_private_fare(session, booking_id) -> tuple[int \| None, uuid.UUID] \| None`. | `backend/app/modules/booking/service.py:14-60`, `backend/app/modules/pooling/repository.py:18-92`, `backend/app/modules/pooling/pricing_state.py:21-150` | Tránh gọi nhầm API nội bộ giữa `candidate`, `pooling`, `booking`, `fund` |
| **CORR-07** | Ghi nhận `routing/osrm.py` dùng `http.client` với `TCP_NODELAY`, `routing/cache.py` cache ma trận OSRM dưới key `osrm:table:v1:...`, và `driver/service.py` dùng Redis `GEOADD` | - `routing/osrm.py` sử dụng `httpx.Client(limits=httpx.Limits(max_keepalive_connections=0))` và truyền `headers={"Connection": "close"}` trên mỗi request (tái sử dụng 1 `httpx.Client` để không phải khởi tạo lại SSL context theo `SF-P2-17`, đồng thời đóng TCP socket ngay để tránh lỗi keep-alive timeout 5s của `osrm-routed` theo `SF-P2-16`).<br>- `routing/cache.py` (`CachedRoutingProvider`) **chỉ cache kết quả `route()` không có waypoints** với key `rt:{policy.key()}:{profile}:{geohash7_o}:{geohash7_d}:static`. Phương thức `matrix()` **không bao giờ cache** (`OD-P2-02` / `SF-P2-14`: chuyển thẳng xuống `self._inner.matrix(...)`).<br>- `driver/service.py` lưu vị trí tài xế trong bảng PostgreSQL/PostGIS `driver_locations` (`WKTElement("POINT(lon lat)", srid=4326)`) và truy vấn bằng 1 câu SQL kết hợp `ST_Expand` + `ST_DWithin` + `row_number() OVER (PARTITION BY dl.driver_id ORDER BY dl.recorded_at DESC)` trong `nearby_idle_drivers()`. Không dùng Redis `GEOADD`. | `backend/app/modules/routing/osrm.py:44-59,90-100`, `backend/app/modules/routing/cache.py:57-89`, `backend/app/modules/driver/service.py:109-189` | Tránh hiểu sai kiến trúc cache và truy vấn không gian hiện tại |
| **CORR-08** | Ghi nhận có 6 hàm trigger (tên `forbid_pricing_configs_mutation()`) và constraint `uq_ride_stops_plan_seq DEFERRABLE INITIALLY IMMEDIATE` trên cột `stop_sequence` | - Thực tế có **5 hàm trigger PL/pgSQL gắn vào 6 triggers**:<br>  1. `pricing_configs_immutable()` (`0001:84-99`) gắn vào 2 triggers trên `pricing_configs`: `trg_pricing_configs_immutable` (`BEFORE UPDATE OR DELETE FOR EACH ROW`) và `trg_pricing_configs_no_truncate` (`BEFORE TRUNCATE FOR EACH STATEMENT`).<br>  2. `fund_ledger_guard()` (`0006:101-131`) gắn vào `trg_fund_ledger_guard` (`BEFORE INSERT OR UPDATE OR DELETE ON fund_ledger FOR EACH ROW`).<br>  3. `driver_payouts_immutable()` (`0006:134-144`) gắn vào `trg_driver_payouts_immutable` (`BEFORE UPDATE OR DELETE ON driver_payouts FOR EACH ROW`).<br>  4. `ride_participants_frozen_guard()` (`0006:147-172`) gắn vào `trg_ride_participants_frozen` (`BEFORE UPDATE ON ride_participants FOR EACH ROW`).<br>  5. `bookings_locked_pool_price_guard()` (`0006:175-194`) gắn vào `trg_bookings_locked_pool_price` (`BEFORE UPDATE ON bookings FOR EACH ROW`).<br>- Trên bảng `ride_stops` (`0005:73-91`), tên cột thứ tự điểm dừng là `seq` (không phải `stop_sequence`), và unique constraint là `uq_ride_stops_ride_plan_id_seq` với `deferrable=True, initially="DEFERRED"` (`DEFERRABLE INITIALLY DEFERRED`). | `backend/alembic/versions/0001_p1_core_schema.py:84-99`, `backend/alembic/versions/0005_p2_routing_candidate_pooling.py:73-91`, `backend/alembic/versions/0006_p3_pricing_fund.py:101-194` | Rất quan trọng khi Phase 4 chèn thêm điểm dừng vào `ride_stops` trong transaction (nhờ `INITIALLY DEFERRED` nên không cần `SET CONSTRAINTS` thủ công) |
| **CORR-09** | Ghi nhận script benchmark tên là `scripts/p3_benchmark.py` và cấu hình lớn nhất là `1000x50` | Script benchmark thực tế là `scripts/p2_benchmark.py` (gọi `scripts/p2_verify.py` và được chạy qua `scripts/p2_bench_run.sh` với nhãn `--label p3-integrated-...`). 7 cấu hình được đo trong mỗi lượt chạy là: `50x0`, `200x0`, `1000x0`, `200x10`, `200x20`, `1000x20`, và `200x20-hc` (constraint-stress workload). | `scripts/p2_benchmark.py:52,105`, `docs/implementation/evidence/p3_runs/*/result.json` | Đảm bảo truy vết đúng script và đúng cấu hình benchmark thực nghiệm |
| **CORR-10** | Ghi nhận `test_architecture.py` có hàm `test_no_cross_module_private_imports` | `backend/tests/test_architecture.py` thực tế có 3 hàm test: `test_no_cross_module_model_imports`, `test_every_table_is_owned_by_exactly_one_module`, và `test_ai_modules_cannot_reach_the_hard_constraints`. | `backend/tests/test_architecture.py:21-72` | Truy vết chính xác bộ test kiến trúc |

---

## 1. Danh mục Chính xác 26 HTTP Routes tại HEAD (`f97a509`)

Dưới đây là danh sách đầy đủ 26 HTTP routes thực tế trong source code:

### 1.1. `backend/app/api/health.py` (2 routes)
1. `GET /health/live` → `live()` (`health.py:13`)
2. `GET /health/ready` → `ready()` (`health.py:18`)

### 1.2. `backend/app/modules/identity/api.py` (6 routes)
3. `POST /api/auth/register` (`status_code=201`) → `register()` (`identity/api.py:26`)
4. `POST /api/auth/login` → `login()` (`identity/api.py:39`)
5. `POST /api/auth/refresh` → `refresh()` (`identity/api.py:48`)
6. `POST /api/auth/logout` (`status_code=204`) → `logout()` (`identity/api.py:57`)
7. `GET /api/users/me` → `me()` (`identity/api.py:66`)
8. `PUT /api/users/me/gender` → `update_my_gender()` (`identity/api.py:71`)

### 1.3. `backend/app/modules/driver/api.py` (7 routes)
9. `GET /api/driver/profile` → `get_my_profile()` (`driver/api.py:26`, `require_roles("DRIVER")`)
10. `POST /api/driver/vehicles` (`status_code=201`) → `register_vehicle()` (`driver/api.py:35`, `require_roles("DRIVER")`)
11. `POST /api/driver/kyc/submit` → `submit_kyc()` (`driver/api.py:47`, `require_roles("DRIVER")`)
12. `PUT /api/driver/settings` → `update_settings()` (`driver/api.py:56`, `require_roles("DRIVER")`)
13. `PUT /api/driver/location` → `report_location()` (`driver/api.py:67`, `require_roles("DRIVER")`)
14. `PUT /api/driver/availability` → `set_availability()` (`driver/api.py:78`, `require_roles("DRIVER")`)
15. `POST /api/admin/drivers/{driver_id}/kyc-review` → `review_kyc()` (`driver/api.py:89`, `require_roles("ADMIN")`)

### 1.4. `backend/app/modules/trip/api.py` (2 routes)
16. `POST /api/trip-requests` (`status_code=201`) → `create_trip()` (`trip/api.py:22`, `require_roles("PASSENGER")`)
17. `GET /api/trip-requests/{trip_id}` → `get_trip()` (`trip/api.py:36`, `get_current_user` — owner PASSENGER hoặc ADMIN)

### 1.5. `backend/app/modules/candidate/api.py` (2 routes — ADMIN-only diagnostic endpoints)
18. `POST /api/admin/candidates/runs` (`status_code=201`) → `create_run()` (`candidate/api.py:22`, `require_roles("ADMIN")`)
19. `GET /api/admin/candidates/runs/{run_id}` → `read_run()` (`candidate/api.py:38`, `require_roles("ADMIN")`)

### 1.6. `backend/app/modules/ml_models/survey_api.py` (7 routes)
20. `GET /survey/s1` → `landing_page()` (`survey_api.py:42`)
21. `POST /api/survey/s1/sessions` (`status_code=201`) → `start()` (`survey_api.py:61`)
22. `POST /api/survey/s1/sessions/{respondent_id}/submit` → `submit()` (`survey_api.py:74`)
23. `GET /api/admin/survey/s1/export/{table}` → `export_csv()` (`survey_api.py:92`, `require_roles("ADMIN")`)
24. `GET /api/admin/survey/s1/quota` → `quota()` (`survey_api.py:114`, `require_roles("ADMIN")`)
25. `GET /api/admin/survey/s1/rejections` → `rejections()` (`survey_api.py:121`, `require_roles("ADMIN")`)
26. `DELETE /api/admin/survey/s1/respondents/{respondent_id}` → `withdraw()` (`survey_api.py:128`, `require_roles("ADMIN")`)

