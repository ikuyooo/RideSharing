# PHASE 3 — PHASE 4 READINESS & DEPENDENCY ASSESSMENT

**Dự án:** Ride_Sharing  
**Commit kiểm chứng:** `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`  
**Mục tiêu Phase 4 theo Đặc tả Revision 9 (Mục 79):** Triển khai Vòng đời Đặt xe (`Booking Lifecycle`), Giữ ghế tạm thời (`Seat Hold`), Thác đề xuất Tài xế (`Offer Cascade`), Ghép chuyến theo lô (`Batch Matching` với OR-Tools CP-SAT RTV-Graph 30s), Chèn động thời gian thực (`Dynamic Insertion`), Điểm hẹn đi bộ (`Meeting Points`), và Gom khách liên tỉnh (`Intercity Pool`).

---

## 1. Đánh giá Các Thành phần Đã Sẵn sàng làm Nền tảng cho Phase 4

| Thành phần nền tảng (Phase 1–3) | Module & File cung cấp | Mức độ sẵn sàng cho Phase 4 | Bằng chứng trong Source Code |
|---|---|---|---|
| **1. Sinh ứng viên Đơn & Ghép xe kèm Định giá Phase 3** | `app/modules/candidate/generator.py`, `service.py`, `constraints.py` | **READY (100%)** | Hàm `generate_for_trip(session, routing, trip_id, now)` trả về danh sách ứng viên đã vượt qua 11 ràng buộc cứng (HC01–HC11) và toàn bộ cổng định giá Phase 3 (D1, Gate 1, biên `[Floor_i, Cap_i]`, Gate 2A/2B, D5–D6), lưu đầy đủ chi tiết giá vào `ride_candidates` |
| **2. Chèn động & Quản lý trạng thái giá chuyến mở (`CAR_URBAN_POOL`)** | `app/modules/pooling/insertion.py`, `pricing_state.py`, `repository.py` | **READY (100%)** | `insert()` kiểm tra toàn bộ cặp vị trí chèn $(p, q)$; `plan_pricing_states()` nạp trạng thái giá của các chuyến mở bằng 1 truy vấn SQL; `store_plan_pricing()` cập nhật giá hành khách mở với khóa lạc quan (`WHERE id = :pid AND version = :v`) và không chạm vào hành khách đã `is_price_frozen = true` |
| **3. Bộ công thức Báo giá, Khóa giá, Phí hủy & Tất toán** | `app/modules/pricing/service.py`, `tariff.py`, `pool.py`, `cancellation.py`, `settlement.py` | **READY (95% — chờ chốt `SF-P3-16`)** | `PricingService` cung cấp facade đầy đủ cho báo giá 5 dịch vụ, định giá chuyến ghép mới, định giá chèn động, tính giá tại điểm khóa 3 km (`final_price_at_lock`), tính phí hủy (`cancellation_fee`), và tính tất toán (`settlement`) |
| **4. Sổ cái Quỹ bảo đảm & Bảng thanh toán tài xế bất biến** | `app/modules/fund/service.py`, `models.py`, `0006_p3_pricing_fund.py` | **READY (100%)** | `record_settlement()`, `settlement_for_completed_booking()`, `cancellation_settlement()`, `reconcile()` đã hoàn thiện cùng 4 DB triggers bảo vệ bất biến |
| **5. Các bảng DB phục vụ Đặt chỗ, Giữ ghế, Idempotency & Lịch trình** | `app/modules/booking/models.py`, `0001_p1_core_schema.py` | **SCHEMA READY (Cần bổ sung bảng `offers`)** | Đã có sẵn các bảng `bookings`, `scheduled_trips`, `seat_bookings`, `seat_holds`, `idempotency_records`, `scheduled_jobs`, `ride_plans`, `ride_participants`, `ride_stops` |

---

## 2. Các Khoảng trống Kỹ thuật & Phụ thuộc Cần Giải quyết khi Bước vào Phase 4

Để triển khai Phase 4 mà không phá vỡ kiến trúc hiện tại, đội phát triển phải lưu ý 6 điểm kỹ thuật sau:

### 2.1. Cần quyết định của Chủ dự án về `SF-P3-16` trước khi mở đặt chuyến `CAR_URBAN_POOL` 2 ghế
- Hiện tại, nếu khách đặt `CAR_URBAN_POOL` với `party_size = 2`, hàm `car_urban_pool_unmatched_quote()` nhân `SeatFactor(2) = 1.35` làm `Quote_unmatched_i > P_i`, và nếu không ghép được ai (`NO_MATCH_FOUND`), `urban_pool_unmatched_settlement()` sẽ ném `ValueError("unmatched quote exceeds private fare")`.
- **Hành động bắt buộc trước Phase 4:** Chủ dự án phê duyệt phương án xử lý `SF-P3-16` (khuyến nghị: không nhân `SeatFactor(s_i)` vào `Quote_unmatched_i`).

### 2.2. Chưa có bảng `offers` cho Thác đề xuất Tài xế (Offer Cascade)
- Kiểm tra 24 bảng hiện tại trong `backend/app/db/models.py`: đã có `seat_holds`, `idempotency_records`, `scheduled_jobs`, nhưng **chưa có bảng `offers`** (để lưu trạng thái đề xuất gửi tới tài xế, thời hạn 20s đô thị / 60s liên tỉnh, lượt thử `1..3` theo `offer_cascade_max_attempts: 3`).
- **Hành động ở Phase 4:** Tạo migration `0007_p4_booking_dispatch_matching.py` bổ sung bảng `offers` thuộc quyền sở hữu của module `dispatch` (hoặc `booking` theo Mục 54.1).

### 2.3. Orchestration tại Điểm khóa giá 3 km (`Pool Lock Point`) và Đóng băng giá khi Đón khách (`is_price_frozen`)
- Phase 3 đã cung cấp hàm tính toán `final_price_at_lock()` (`pricing/pool.py:310-336`) và 2 DB triggers bảo vệ (`trg_ride_participants_frozen`, `trg_bookings_locked_pool_price`).
- Tuy nhiên, **chưa có hàm service chuyển trạng thái** trên DB:
  1. Khi tài xế đón khách lên xe (`PICKED_UP`): cập nhật `ride_participants.is_price_frozen = True` để các lần chèn động sau không được thay đổi giá của khách này (nhưng chú ý: chỉ đóng băng khi giá của khách đã là giá ghép thực tế hoặc tại điểm khóa).
  2. Khi quãng đường còn lại đến điểm trả của khách $\le 3.0\text{ km}$ (`pool_lock_remaining_km = 3.0`): gọi `final_price_at_lock()` và cập nhật `bookings.price_status` sang `MATCHED_LOCKED` hoặc `UNMATCHED_LOCKED` + `bookings.final_price_vnd` + `bookings.unmatched_cause`.
- **Hành động ở Phase 4:** Hiện thực state machine chuyến đi trong `booking/service.py` và `pooling` để kích hoạt đúng 2 sự kiện này.

### 2.4. Ghi đầy đủ thông tin định giá từ `ride_candidates` sang `ride_participants` và `ride_stops` khi Xác nhận Ghép chuyến
- Khi một ứng viên ghép xe (`CAR_URBAN_POOL`) được tài xế chấp nhận ở Phase 4:
  - Phải tạo/cập nhật `ride_plans`, `ride_stops` (lợi dụng constraint `uq_ride_stops_ride_plan_id_seq DEFERRABLE INITIALLY DEFERRED` đã có ở migration `0005`), và `ride_participants`.
  - Khi ghi `ride_participants`, bắt buộc điền đầy đủ `private_fare_vnd`, `fare_exact_vnd`, `fare_exact_rational`, `fare_charged_vnd`, `rounding_absorbed_vnd`, `detour_ratio`, `walk_m` từ `ride_candidates.price_breakdown` và calling `store_plan_pricing()` (`pooling/pricing_state.py:92-135`) để cập nhật lại giá của các hành khách chưa đóng băng trên chuyến xe.

### 2.5. Dependency cho Batch Matching (`ORTOOLS_CP_SAT_RTV`)
- Cấu hình baseline khóa `batch_matching.solver = "ORTOOLS_CP_SAT_RTV"` với `interval_s = 30` và `solver_time_limit_s = 3.0`.
- Kiểm tra `backend/pyproject.toml`: hiện tại `ortools` chưa có trong danh sách dependencies của `pyproject.toml`.
- **Hành động ở Phase 4:** Bổ sung `ortools` vào `backend/pyproject.toml` khi triển khai module `matching`.

### 2.6. Ranh giới Kiến trúc Bắt buộc Giữ vững (`test_architecture.py`)
- `backend/tests/test_architecture.py` kiểm tra tự động bằng AST:
  - Không module nào trong `app/modules/<A>/` được phép `import app.modules.<B>.models` (với `A != B`).
  - Mọi giao tiếp liên module phải đi qua `service.py` hoặc `repository.py` / `pricing_state.py` công khai của module sở hữu bảng.
  - Các module `ml_models` và `simulator` tuyệt đối không được import các hàm ghi/sửa ràng buộc cứng.

---

## 3. Kết luận về Mức độ Sẵn sàng cho Phase 4

- **Về mặt Kỹ thuật & Kiến trúc (Technical Readiness):** **SẴN SÀNG (READY WITH CONDITIONS)** — Toàn bộ nền tảng định giá, phân bổ tiền, phí hủy, sổ cái Quỹ bảo đảm, DB schema/triggers và tích hợp sinh ứng viên của Phase 3 đã hoàn chỉnh, tuân thủ chặt chẽ ranh giới kiến trúc Modular Monolith.
- **Điều kiện cần trước khi bắt đầu code Phase 4:**
  1. Chủ dự án phê duyệt quyết định cho **`SF-P3-16`** (và xác nhận `SF-P3-02`, `SF-P3-10`) trong `docs/implementation/P3_OWNER_DECISION_REGISTER.md`.
  2. Chạy lại lệnh kiểm thử tích hợp (`pytest` trong Docker Compose stack) khi môi trường Docker/WSL sẵn sàng để đóng dấu xác nhận thực thi trực tiếp cho các bài test phụ thuộc DB/OSRM.

