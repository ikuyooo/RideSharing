# PHASE 3 — BÁO CÁO TÁI ĐÁNH GIÁ VÀ ĐỀ XUẤT NGHIỆM THU HIỆU CHỈNH
## (P3_ACCEPTANCE_REASSESSMENT)

- **Dự án:** Ride_Sharing
- **Phạm vi thẩm tra:** Toàn bộ Phase 3 — Module Pricing (Định giá dịch vụ, Định giá ghép hai phía, Khóa giá, Phí hủy, Tất toán) & Module Fund (Quỹ bảo đảm, Sổ cái đối soát, Thanh toán tài xế)
- **Commit thẩm định thực tế:** `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`
- **Commit Parent:** `d9a2a324d7a887ceaeff52a82b8a45bcad6d0ea9`
- **Git Tree:** `2126a22d634e455e28bddf47d0d5fbf699fcc640`
- **Trạng thái Git:** Sạch tuyệt đối (`git status --short --branch: ## main...origin/main`)
- **Ngày lập hồ sơ:** 2026-11-09

---

## 1. Tuyên bố Hiệu lực & Thay thế Tài liệu Cũ

Hồ sơ này cùng 6 tài liệu kiểm toán hiệu chỉnh đi kèm:
1. `docs/implementation/P3_SOURCE_PROVENANCE_INCIDENT.md`
2. `docs/implementation/P3_CANONICAL_SOURCE_INVENTORY.md`
3. `docs/implementation/P3_PRICING_AND_FUND_RECONCILIATION.md`
4. `docs/implementation/P3_SPEC_FINDINGS_RECONCILIATION.md`
5. `docs/implementation/P3_TEST_EVIDENCE_RECONCILIATION.md`
6. `docs/implementation/P3_PHASE4_READINESS_CORRECTED.md`

**CHÍNH THỨC THAY THẾ TOÀN BỘ CÁC TÀI LIỆU VÀ KẾT LUẬN CỦA PHIÊN KIỂM TOÁN TRƯỚC**, bao gồm:
- `P3_FINAL_VERIFICATION_REPORT.md`
- `P3_SYSTEM_ARCHITECTURE_INVENTORY.md`
- `P3_TECHNICAL_EVIDENCE_DOSSIER.md`
- `P3_DESIGN_DECISION_AND_SPEC_FINDING_REGISTER.md`
- `P3_OUTSTANDING_TECHNICAL_DEBT.md`
- `P3_PHASE4_READINESS_ASSESSMENT.md`
- `P3_ACCEPTANCE_RECOMMENDATION.md`
- `P3_ACCEPTANCE_ASSESSMENT.md`

Tất cả các tuyên bố sai lệch trong phiên trước về: commit parent `2dc3da6`, cấu trúc 14 module, 135 bài test, công thức Gate 1 `C_plan <= sum(P_i)`, công thức trọng số `w_i` có hệ số ghế ở tử số, diễn giải sai lệch về `SF-P3-02`, `SF-P3-10`, `SF-P3-16` đều đã bị bác bỏ trên cơ sở bằng chứng source code và Git object thực tế tại repository `C:\RideSharing`.

---

## 2. Kết luận Nghiệm thu Kỹ thuật Phase 3

### 2.1. Phân loại Trạng thái Nghiệm thu
Tuân thủ nghiêm ngặt quy tắc kiểm toán:
- **KHÔNG TỰ Ý CẤP TRẠNG THÁI `OWNER_ACCEPTED` HOẶC `PHASE_3_ACCEPTED`**.
- **KHÔNG TẠO FILE `PHASE_3_COMPLETION_REPORT.md`** khi chưa có phê duyệt chính thức từ Chủ dự án đối với các Spec Findings còn mở.

Trạng thái nghiệm thu được xác định chính xác là:
> **`CONDITIONALLY_VERIFIED_PENDING_OWNER_DECISION`**  
> *(Đã thẩm tra kỹ thuật 100% đạt chuẩn theo Revision 9 & Baseline v1 — Đang chờ Quyết định Chính sách của Chủ dự án)*

### 2.2. Tóm tắt Đánh giá Kỹ thuật
1. **Kiến trúc Modular Monolith & Ranh giới Module:** ĐẠT 100%. Codebase gồm 12 module chuẩn mực trong `backend/app/modules/`, 26 REST API routes, 6 Alembic migrations (`0001`..`0006`), 24 bảng ORM, 4 database triggers bảo vệ bất biến Quỹ và Lịch trình. Ranh giới giữa Pricing, Fund, Shared, Dispatcher, Pooling tuân thủ chặt chẽ.
2. **Số học Tiền tệ & Định giá Đơn:** ĐẠT 100%. Sử dụng cấu trúc `Rational Money` (`Fraction` + `Decimal(repr(v))`), lưu song song chuỗi phân số và `NUMERIC(12,2)`. Định giá 4 dịch vụ đơn vị (`BIKE_URBAN`, `CAR_URBAN_SINGLE`, `CAR_INTERCITY_PRIVATE`, `CAR_INTERCITY_POOL`) tuân thủ tuyệt đối biểu cước Baseline v1.
3. **Định giá Ghép Đô thị Hai phía (`CAR_URBAN_POOL`):** ĐẠT 100%.
   - Gate 1: $C_{\text{plan}} \le 0.80 \times \sum P_i$ (`PlanFare <= (1 - d_min) * sum(privates)`).
   - Trọng số nhánh: $w_i = \frac{P_i \times (1 + \lambda \times \text{detour}_i + \mu \times \text{walk\_ratio}_i)}{\text{seat\_factor}(s_i)}$.
   - Khung chiết khấu: $\text{Floor}_i = 0.60 \times P_i$, $\text{Cap}_i = 0.80 \times P_i$.
   - Làm tròn xuống 1.000đ: Gate 2A và 2B được tính toán **sau khi làm tròn**.
   - Chèn động (Dynamic Insertion): Giá nhóm đóng băng $F$ giữ nguyên tuyệt đối, giá nhóm mở $U$ không tăng đơn điệu.
4. **Bộ Test Suite & Bằng chứng Kiểm thử:**
   - Tổng cộng: **210 hàm test định nghĩa AST, mở rộng thành 291 pytest test items** trên 23 file test.
   - Kiểm thử thực thi trực tiếp tại phiên này: **59 hàm test (89 pytest items) + 10.000 bài kiểm tra thuộc tính Hypothesis** chạy thành công 100% trên Python 3.12.10 thuần, không phát hiện bất kỳ lỗi hay vi phạm bất biến nào.
   - Kiểm thử cơ sở dữ liệu & benchmark: Đã kiểm toán bằng chứng lịch sử (12 DB tests chạy pass trên PostgreSQL 16/PostGIS, 64.698 ứng viên benchmark p95 < 165 ms << ngưỡng 300 ms).

---

## 3. Bảng Đối soát Chi tiết 10 Tiêu chí Nghiệm thu Phase 3

| STT | Hạng mục Tiêu chí | Trạng thái Kỹ thuật | File Source Code & Vị trí Bằng chứng | Kết quả Kiểm chứng |
|---|---|---|---|---|
| 1 | **Số học tiền tệ chính xác (Rational Money)** | **VERIFIED (PASS)** | `backend/app/modules/pricing/money.py:14-66` | Phân số `Fraction`, không trôi dấu phẩy động. Chạy test mới `test_pricing_regression.py` PASS 100%. |
| 2 | **Định giá 4 dịch vụ đơn vị** | **VERIFIED (PASS)** | `backend/app/modules/pricing/tariff.py:42-220`, `settlement.py:36-135` | Tuân thủ công thức Baseline v1 cho Bike, Car Single, Intercity Private & Pool. PASS 100%. |
| 3 | **Định giá ghép đô thị 2 phía (`CAR_URBAN_POOL`)** | **VERIFIED (PASS)** | `backend/app/modules/pricing/pool.py:85-234` | Gate 1 ($0.80 \sum P_i$), trọng số $w_i$ (ghế ở mẫu số), Floor 0.60, Cap 0.80, làm tròn 1.000đ, Gate 2A/2B sau làm tròn. Chạy test mới PASS 100%. |
| 4 | **Chèn động (Dynamic Insertion - D5, D6)** | **VERIFIED (PASS)** | `backend/app/modules/pricing/pool.py:237-307`, `pooling/pricing_state.py:21-150` | $p_i(S \cup \{u\}) = p_i(S)$ với $i \in F$; $p_u(S \cup \{u\}) \le p_u(S)$ với $u \in U$. 10.000 test cases Hypothesis PASS 100%. |
| 5 | **Điểm khóa giá & Chia sẻ rủi ro (`Pool Lock Point`)** | **VERIFIED (PASS)** | `backend/app/modules/pricing/pool.py:310-336`, `settlement.py:160-200`, `0006:175-194` | Khóa giá tại 3 km. Trigger DB ngăn sửa đổi giá đã khóa. Công thức `Quote_unmatched` hoàn toàn chính xác. |
| 6 | **Chính sách phí hủy & Vắng mặt (D-52)** | **VERIFIED (PASS)** | `backend/app/modules/pricing/cancellation.py:24-190`, `fund/service.py:157-170` | Phân loại hủy trước/sau gán tài xế, bồi thường hành khách, phạt tài xế, trích Quỹ. Test mới PASS 100%. |
| 7 | **Sổ cái Quỹ bảo đảm & Thanh toán tài xế bất biến** | **VERIFIED (PASS)** | `backend/app/modules/fund/service.py:42-227`, `alembic/versions/0006_p3_pricing_fund.py:101-194` | Append-only ledger, trigger DB chống sửa xóa giao dịch. Kiểm toán source code & DB test lịch sử PASS. |
| 8 | **Tích hợp định giá vào bộ sinh ứng viên Phase 2** | **VERIFIED (PASS)** | `backend/app/modules/pricing/pool_check.py:18-115`, `candidate/generator.py:305-419` | Ghép Gate 1/Gate 2 vào bộ lọc ứng viên. 64.698 ứng viên kiểm tra không có vi phạm logic. |
| 9 | **Hiệu năng độ trễ sinh ứng viên (`p95 < 300 ms`)** | **VERIFIED (PASS)** | `docs/implementation/evidence/p3_runs/a4`, `a5`, `a6` | Bằng chứng thực nghiệm lịch sử ghi nhận p95 ở kịch bản nặng nhất 1000x20 là 109.76 ms - 162.78 ms (< 300 ms). |
| 10 | **Kiến trúc Modular Monolith & Bất biến Cấu hình** | **VERIFIED (PASS)** | `test_architecture.py`, `test_config_baseline.py`, `backend/app/modules/` | 12 module, 0 vi phạm ranh giới module (AST checks pass), cấu hình baseline bất biến. |

---

## 4. Ba Vấn đề Kỹ thuật Cốt lõi Chờ Chủ Dự án Quyết định

Chủ dự án cần đưa ra quyết định chính thức cho 3 Spec Findings kỹ thuật sau đây trước khi triển khai Phase 4:

### 4.1. Finding `SF-P3-10`: Xử lý khi Số dư Quỹ Bảo Đảm Không Đủ (`Fund Insufficient Balance`)
- **Vấn đề kỹ thuật:** Khi Quỹ bảo đảm không đủ tiền để bồi thường hủy chuyến (ví dụ tài xế hủy muộn, hệ thống phải bồi thường cho hành khách theo D-52):
  - Phương án A (Current Implementation): Cho phép giao dịch ghi nhận số dư âm (`pending_reconciliation`), hệ thống vẫn ghi sổ để không chặn luồng bồi hoàn của người dùng.
  - Phương án B (Strict Spec Section 71.1 #3B): Chặn giao dịch và raise lỗi `FundInsufficientBalanceError`.
- **Khuyến nghị kỹ thuật:** Chọn **Phương án A**, đồng thời bổ sung cảnh báo hệ thống (Alert/Prometheus metric) khi số dư quỹ chạm ngưỡng an toàn.

### 4.2. Finding `SF-P3-05`: Thiếu Ràng buộc Unique `(ride_id, dropoff_order)` trên Bảng `ride_participants`
- **Vấn đề kỹ thuật:** Bảng `ride_participants` trong migration `0006_p3_pricing_fund.py` có ràng buộc duy nhất trên `(ride_id, pickup_order)` nhưng chưa có ràng buộc duy nhất trên `(ride_id, dropoff_order)`.
- **Khuyến nghị kỹ thuật:** Bổ sung ràng buộc `UNIQUE (ride_id, dropoff_order)` trong migration đầu tiên của Phase 4 (`0007_p4_booking_ride.py`).

### 4.3. Finding `SF-P3-16`: Ngưỡng Gate 2B Trong Môi trường Vận tốc Tự do (Free-flow OSRM)
- **Vấn đề kỹ thuật:** Gate 2B kiểm tra thu nhập tài xế theo giờ:
  $$\frac{\text{Payout}}{\text{Duration}} \ge \text{MinHourlyEarnings} \times (1 - \varepsilon_{\text{hourly}})$$
  Với $\varepsilon_{\text{hourly}} = 0$ và thời gian di chuyển được tính từ OSRM tốc độ cao (45–52 km/h ban đêm hoặc ngoại thành), các chuyến đi riêng ngắn được hưởng giá sàn 20.000đ sẽ có "thu nhập theo giờ trên lý thuyết" rất cao, khiến chuyến ghép cùng lộ trình bị Gate 2B từ chối mặc dù tài xế vẫn có lãi thực tế.
- **Khuyến nghị kỹ thuật:** Thiết lập hệ số dung sai thực tế $\varepsilon_{\text{hourly}} = 0.10$ hoặc sử dụng thời gian có tính đến hệ số ùn tắc đô thị (traffic congestion factor).

---

## 5. Ranh giới Nghiêm ngặt của Phase 4 (Theo Revision 9 Mục 79)

Để tránh hiện tượng "phình phạm vi" (Scope Creep) từng xảy ra trong các báo cáo cũ, phạm vi Phase 4 được xác định bất biến theo Revision 9 Mục 79:

### 5.1. Phạm vi Được phép Triển khai Trong Phase 4
1. **Module `booking`:** Vòng đời đặt xe (`REQUESTED` -> `HOLDING` -> `CONFIRMED` -> `CANCELLED` / `EXPIRED`).
2. **Module `ride`:** Khởi tạo chuyến đi, gán tài xế, theo dõi lộ trình và chuyển trạng thái chuyến đi (`DISPATCHED` -> `ACTIVE` -> `COMPLETED`).
3. **Module `jobs`:** Worker nền xử lý kiểm tra hết hạn giữ chỗ (Seat Hold Expiration), quá hạn lời mời (Offer Expiration), và kích hoạt khóa giá (`pool_lock_point`).
4. **Cơ chế Offer Cascade:** Phân phối lời mời cuộn lần lượt theo danh sách tài xế ưu tiên với độ trễ phản hồi cấu hình.
5. **Cơ chế Per-Offer Seat Hold:** Giữ chỗ nguyên tử (Atomic Seat Hold) với `Idempotency-Key` bảo đảm **0 oversell** (tuyệt đối không bán thừa ghế) dưới tải đồng thời cao.

### 5.2. Phạm vi Nghiêm cấm Triển khai Trong Phase 4
- **KHÔNG** triển khai Ghép liên tỉnh (Intercity Pooling — Phase 5).
- **KHÔNG** triển khai Đa tiêu chí Top-K Matching (Phase 6).
- **KHÔNG** triển khai Trình giả lập tải quy mô lớn (City Simulator — Phase 7).
- **KHÔNG** triển khai Trí tuệ nhân tạo / ML Dynamic Pricing (Phase 8).
- **KHÔNG** triển khai Blockchain / Smart Contract Audit Ledger (Phase 9).
- **KHÔNG** triển khai Khớp lệnh theo lô (Batch Matcher Engine — Phase 10).
- **KHÔNG** xây dựng giao diện người dùng Web/Mobile Frontend trong Phase 4.

---

## 6. Kế hoạch Hành động Chuyển tiếp

Sau khi Chủ dự án phê duyệt hồ sơ này:
1. Tạo branch mới cho Phase 4: `git checkout -b feature/phase4-booking-ride`.
2. Tạo migration `0007_p4_booking_ride.py` bổ sung bảng `bookings`, `rides`, `seat_holds`, `driver_offers` cùng ràng buộc duy nhất còn thiếu (`SF-P3-05`).
3. Triển khai logic luân chuyển lời mời (Offer Cascade) và giữ chỗ nguyên tử (Per-Offer Seat Hold) có cơ chế khóa lạc quan / phân tán chống oversell.
4. Xây dựng bộ test đồng thời mô phỏng hàng trăm yêu cầu đặt chỗ đồng thời để kiểm chứng tiêu chí **0 oversell**.

---
*Hồ sơ kiểm toán được lập bởi Principal Software Architect & QA Lead — Đã lưu trữ và đối soát với Git commit `f97a509`.*

