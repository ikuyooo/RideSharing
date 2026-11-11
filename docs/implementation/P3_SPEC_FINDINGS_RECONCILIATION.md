# ĐỐI SOÁT 16 SPEC FINDINGS PHASE 3 (`SF-P3-01` → `SF-P3-16`)

- **Nguồn sự thật duy nhất**: `docs/implementation/SPEC_FINDINGS_P3.md` (46 dòng, cập nhật 2026-11-05) tại `HEAD = f97a5092ece737d70051d08e6e3604e6a0c6bd1d`.
- **Phương pháp**: đọc nguyên văn file (dòng 16–33), đối chiếu nơi xử lý trong source, rồi đối chiếu với `P3_OWNER_DECISION_REGISTER.md` / `P3_ACCEPTANCE_ASSESSMENT.md` / `P3_PHASE4_READINESS.md` của phiên trước.
- Lưu ý thứ tự trong file gốc: dòng 32 là `SF-P3-16`, dòng 33 là `SF-P3-15`.

> [!WARNING]
> Bản nháp đầu tiên của chính tài liệu này (viết trong phiên hiện tại, trước 22:18 ngày 2026-11-09) có nội dung sai cho SF-P3-03 … SF-P3-15 vì được viết khi chưa đọc lại file gốc. Bản này thay thế hoàn toàn bản nháp đó.

---

## 1. Bảng nguyên văn (tóm lược trung thành) và nơi xử lý trong source

| ID | Nội dung thực tế | Cách xử lý hiện tại (theo file gốc) | Nơi kiểm chứng trong source / test | Trạng thái gốc |
|---|---|---|---|---|
| SF-P3-01 | §16.3 / §71.1 vector 4 in `Fare_exact(A)=135.228,10`, `Fare_exact(C)=48.076,16`; giải đúng §15.2–15.3 cho **135.213,09 / 48.091,17**. Không ảnh hưởng số tiền thu (A 135.000, C 48.000, B giữ 105.000) | Hiện thực theo công thức; test khẳng định đầu ra bắt buộc và giá trị chính xác | `test_pricing_regression.py::test_71_1_vector_4_insert_c_while_b_is_locked` (dòng 187–191) | `OPEN` (cần Chủ dự án ghi nhận lỗi in) |
| SF-P3-02 | Chuyển từ SF-P2-09. R9 §13 không nói về thời gian **chờ** tại điểm đón, quãng tiếp cận `S_0`, dwell tại `S_k` | Một định nghĩa duy nhất `pooling.insertion.plan_extent`: từ lúc xe sẵn sàng tại `S_0` đến khi tới `S_k`; gồm di chuyển, dwell `S_0..S_{k−1}`, thời gian chờ ở các điểm đón sau; không gồm tiếp cận `S_0`, dwell sau `S_k`; kế hoạch đang chạy cộng `driven_m_since_start` và thời gian từ `started_at` | `pooling/insertion.py:153` (`plan_extent`); `pricing/pool_check.py:67-71` | `LOCAL_PROVISIONAL` |
| SF-P3-03 | §71.2 bất biến 5 không nêu điều kiện **cùng số ghế** | Kiểm bất biến 5 với cùng số ghế | `test_pricing_properties.py:137-148` | `OPEN` (đề nghị thêm điều kiện "cùng s") |
| SF-P3-04 | §18.5 dòng 3 (`CORIDER_CANCELLED_EARLY`) và dòng 4 (`CORIDER_CANCELLED_LATE`) không có công thức | Dòng 3 → như `NO_COMPATIBLE`; dòng 4 → chia 85/12/3 + `Guarantee = max(0, 0,80·P_i − 0,85·final_i − phần phí hủy của bạn đi chung chuyển cho tài xế)` | `pricing/settlement.py:64` (`settle_pool_matched`); `pricing/pool.py:377` (`final_price_at_lock`); `test_18_5_row_4_corider_cancelled_late` | `LOCAL_PROVISIONAL` |
| SF-P3-05 | `cancellation_policy` và vốn mồi Quỹ có trong Baseline YAML nhưng không nằm trong `pricing_configs`; tỷ lệ chia phí hủy §18.7 không có khóa YAML | Đọc `cancellation_policy` từ YAML đã khóa; tỷ lệ chia = `1 − c` của dịch vụ; riêng 50/50 là hằng `POOL_SHARED_DRIVER_SHARE` | `pricing/params.py` (`CancellationParams.from_baseline`); `pricing/cancellation.py:119` | `LOCAL_PROVISIONAL` |
| SF-P3-06 | §18.7 không có dòng hủy miễn phí cho `CAR_URBAN_POOL` | Như xe đơn nội đô: `HELD` hoặc ≤ 120 s sau `CONFIRMED` khi tài xế chưa đến → 0 đ | `pricing/cancellation.py:110-114`; `test_pricing_cancellation.py::test_urban_pool` | `LOCAL_PROVISIONAL` |
| SF-P3-07 | Biên thời gian của §18.7 / §27 không nói rõ đóng/mở | ≤120 s miễn phí; bao xe liên tỉnh >2 h miễn phí, ≤2 h 20 %; ghép liên tỉnh >72 h miễn phí, 24 h ≤ còn ≤ 72 h → 50 %, < 24 h hoặc `NO_SHOW` → 100 % | `pricing/cancellation.py:136,148-153`; `test_intercity_private`, `test_intercity_pool_windows` | `LOCAL_PROVISIONAL` |
| SF-P3-08 | `PlanFare` có thể lẻ nhưng `plan_fare_vnd` là `BIGINT`; `Fare_exact` lưu `NUMERIC(12,2)` mất bảo toàn tổng | Thêm `ride_plans.plan_fare_exact`, `ride_participants.fare_exact_rational` dạng "tử/mẫu" | migration `0006:108,111`; `pooling/pricing_state.py:68,79` | `IMPLEMENTED` |
| SF-P3-09 | §71.2 bất biến 6 viết `>` nghiêm ngặt, §14.2 Cổng 2A viết `≥` | Theo §14.2: `≥` | `pricing/pool.py:142` (`gate2`); `test_gate2a_payout_and_2b_hourly_rate_boundaries` | `OPEN` (nhỏ) |
| SF-P3-10 | R9 không quy định khi Quỹ **không đủ** chi `GuaranteePayout` | Từ chối ghi (`FundInsufficient`), không bao giờ cho số dư âm | `fund/service.py:50,70`; `0006:144` (`ck_fund_ledger_ledger_balance_non_negative`); `test_guarantee_never_drives_the_fund_negative` | `OPEN` (cần quyết định) |
| SF-P3-11 | Baseline §5.2 yêu cầu lưu `pricing_version` nhưng §56.1 không có cột | Thêm `bookings.pricing_version`, `ride_plans.pricing_version`; ledger/payout ghi `pricing_version` + `pool_policy_version` | migration `0006:107,112,114-115,120-121` | `IMPLEMENTED` |
| SF-P3-12 | D1 theo chữ ("khách **đang trên xe**") khiến kế hoạch chưa đón ai không bao giờ nhận thêm khách | Hiểu là có ít nhất một đoạn ngồi chung với một khách của kế hoạch (đang ngồi hoặc đang chờ đón) | `pricing/pool_check.py:75-81` (tính `overlap` theo `span`) | `LOCAL_PROVISIONAL` |
| SF-P3-13 | Lần ghép đầu tiên chưa có `Fare_exact_old` nên `DynamicCap` không xác định | Lần đầu: `EffectiveCap = Cap_i`; từ lần 2: `min(Cap_i, Fare_exact_old)`; ≥2 booking mà chưa có phân bổ → `PLAN_PRICING_STATE_INCONSISTENT` | `pricing/pool.py:288` (`price_insertion`); `test_first_match_uses_cap_and_no_previous_price`, `test_inconsistent_stored_state_is_rejected` | `LOCAL_PROVISIONAL` |
| SF-P3-14 | §13 chưa có quy tắc gộp điểm dừng trùng tọa độ | Đếm mọi điểm dừng (P2 không gộp) | `pricing/pool.py:120` (`plan_fare`, tham số `total_stops`) | `OPEN` (nhỏ) |
| SF-P3-15 | `DoorSurcharge` (§28.3) cần hình học vùng đón/trả liên tỉnh | P3 cung cấp công thức tất định; phần hình học thuộc P5 | `pricing/tariff.py:106` (`door_surcharge`); `test_28_3_door_surcharge_and_28_4_booking_price` | `DEFERRED` (P5) |
| SF-P3-16 | Cổng 2B (`ε_hourly = 0`) gần như luôn loại kế hoạch ghép khi thời gian lấy từ OSRM không kẹt xe (~45–52 km/h). Thử 12 hình học trên OSRM thật: mọi phương án qua 11 RB và Cổng 1 đều bị `GATE2B` (ví dụ 449.076 < 512.644 đ/giờ) | Không đổi tham số (Baseline khóa `ε = 0`). Đề xuất cho Chủ dự án: thời gian có kẹt xe (V-03), thử `ε = 0,05` trong phân tích độ nhạy, hoặc xem lại SF-P3-02 | `test_candidate_generation.py:137-144` (OSRM thật → `P3_GATE2B…`); `:147-198` (router tổng hợp 20 km/h → `COMPLETE`) | `OPEN` (cần quyết định **trước P6**) |

**Phân bố trạng thái thực tế**: `OPEN` 6 (01, 03, 09, 10, 14, 16) · `LOCAL_PROVISIONAL` 7 (02, 04, 05, 06, 07, 12, 13) · `IMPLEMENTED` 2 (08, 11) · `DEFERRED` 1 (15).

---

## 2. Đối chiếu với hồ sơ phiên trước

| ID | Hồ sơ phiên trước ghi | Thực tế | Kết luận |
|---|---|---|---|
| SF-P3-16 | `P3_OWNER_DECISION_REGISTER.md:15`: "Báo giá `CAR_URBAN_POOL` cho nhóm 2 ghế cao hơn giá đi riêng" (`Quote_unmatched` nhân `SeatFactor`) | Vấn đề Cổng 2B × thời gian OSRM free-flow. `pool_quote_for(p, private)` (`tariff.py:69`) không nhân seat factor; `test_two_seat_quote_unmatched_below_private` và vector 3C (`Unmatched_A = 174.000 < 194.000`) đều PASS khi chạy lại | **Sai hoàn toàn** — mô tả một lỗi không tồn tại |
| SF-P3-02 | `P3_OWNER_DECISION_REGISTER.md:16`: "Vị trí `SeatFactor(s_i)` trong công thức `Floor_i`" | Định nghĩa `T_plan` (`plan_extent`) | **Sai hoàn toàn** |
| SF-P3-10 | `P3_OWNER_DECISION_REGISTER.md:17`: "Khách hủy sau 120 s … khi chưa gán tài xế" | Quỹ không đủ số dư chi `GuaranteePayout` | **Sai hoàn toàn** |
| SF-P3-09 | `P3_OWNER_DECISION_REGISTER.md:32`: "`PASSENGER_SELF_RESTRICTED` và 2 ghế" | `>` vs `≥` giữa §71.2 và §14.2. Giá trị `PASSENGER_SELF_RESTRICTED` không có trong `UNMATCHED_CAUSES` (`booking/models.py:64-71`) | **Sai** |
| Các ID khác | Không được đối chiếu từng dòng trong phiên này | — | `Chưa xác minh` từng dòng; coi toàn bộ register phiên trước là `SUPERSEDED` |

---

## 3. Việc cần Chủ dự án quyết định

| Ưu tiên | ID | Quyết định cần có | Thời hạn hợp lý |
|---|---|---|---|
| Cao | SF-P3-16 | Nguồn thời gian cho Cổng 2B (OSRM free-flow / hệ số kẹt xe V-03 / `ε` trong độ nhạy) | Trước P6 (ảnh hưởng tỷ lệ ghép, P(match), Simulator, H6); không chặn P4 về mặt kỹ thuật |
| Trung bình | SF-P3-10 | Chính sách khi Quỹ cạn (nền tảng bù? tạm dừng bảo đảm?) | Trước khi P4 ghi tất toán thật |
| Thấp | SF-P3-01, 03, 09, 14 | Ghi nhận lỗi in / điều chỉnh phát biểu bất biến / quy tắc gộp điểm dừng | Bất kỳ lúc nào |
| Phê duyệt | 7 mục `LOCAL_PROVISIONAL` | Chấp nhận hoặc thay diễn giải | Trước nghiệm thu Phase 3 |
