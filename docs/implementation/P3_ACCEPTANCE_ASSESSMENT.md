# PHASE 3 — ACCEPTANCE ASSESSMENT (`P3_ACCEPTANCE_ASSESSMENT`)

**Dự án:** Ride_Sharing  
**Phase đánh giá:** Phase 3 — Định giá dịch vụ, Định giá ghép xe hai phía, Khóa giá, Phí hủy, Tất toán & Sổ cái Quỹ bảo đảm  
**Commit được kiểm toán:** `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` (`main`)  
**Ngày đánh giá:** 2026-11-09  

---

## 1. Kết luận Trạng thái Nghiệm thu Phase 3

> **TRẠNG THÁI NGHIỆM THU ĐỀ XUẤT:** **`PARTIALLY_VERIFIED` — SẴN SÀNG TRÌNH CHỦ DỰ ÁN PHÊ DUYỆT KỸ THUẬT (`TECHNICAL_READY_PENDING_OWNER_DECISIONS_AND_DOCKER_RERUN`)**  
> *(Lưu ý tuân thủ quy tắc nghiệm thu: Không tự ý cấp trạng thái `OWNER_ACCEPTED` và không tạo file `PHASE_3_COMPLETION_REPORT.md` khi còn quyết định của Chủ dự án chưa phê duyệt và chưa chạy lại được nhóm test phụ thuộc Docker/PostgreSQL/OSRM trên máy hiện tại).*

---

## 2. Đánh giá Chi tiết theo 10 Tiêu chí Nghiệm thu Phase 3 (Đặc tả Revision 9 — Mục 79)

| STT | Tiêu chí Nghiệm thu Phase 3 | Trạng thái | Bằng chứng xác minh |
|---|---|---|---|
| 1 | **Số học tiền tệ chính xác (Exact Rational Money), không sai số dấu phẩy động** | **VERIFIED (PASS)** | `backend/app/modules/pricing/money.py:14-66` sử dụng `Fraction` + `Decimal(repr(value))`; lưu song song `NUMERIC(12,2)` và chuỗi phân số tối giản `"p/q"`; kiểm chứng mới bằng `test_pricing_regression.py` (PASS 13/13) |
| 2 | **Định giá và tất toán chính xác 4 dịch vụ ngoài ghép đô thị (`BIKE_URBAN`, `CAR_URBAN_SINGLE`, `CAR_INTERCITY_PRIVATE`, `CAR_INTERCITY_POOL`)** | **VERIFIED (PASS)** | `backend/app/modules/pricing/tariff.py:42-220` và `settlement.py:36-135`; kiểm chứng mới bằng `test_pricing_regression.py` (PASS 13/13) |
| 3 | **Định giá ghép xe đô thị hai phía (`CAR_URBAN_POOL` — `price_new_plan` & `allocate_two_sided`)** | **VERIFIED (PASS)** | `backend/app/modules/pricing/pool.py:85-234`: thực thi đầy đủ D1 (co-riding), Gate 1 (`C_plan <= sum(P_i)`), biên `[Floor_i, Cap_i]` theo `D-43` & `D-45b`, `on_lower_bound_infeasible = "REJECT"`, làm tròn xuống `1.000đ`, và Gate 2A/2B tính **sau làm tròn** theo `D-45a`; kiểm chứng mới bằng `test_pricing_pool.py` (PASS 22 hàm / 31 test cases) |
| 4 | **Chèn động giữ nguyên giá nhóm đóng băng $F$ và không tăng giá nhóm mở $U$ (`price_insertion` — D5 & D6)** | **VERIFIED (PASS)** | `backend/app/modules/pricing/pool.py:237-307` và `pooling/pricing_state.py:21-150`; kiểm chứng mới bằng `test_pricing_pool.py` (PASS) và kiểm chứng lịch sử bằng Hypothesis (`test_pricing_properties.py`) |
| 5 | **Điểm khóa giá ghép (`Pool Lock Point = 3 km`) & Chia sẻ rủi ro không ghép được (`NO_MATCH_FOUND` vs `PASSENGER_SELF_RESTRICTED`)** | **IMPLEMENTED & UNIT-VERIFIED (Cần chốt `SF-P3-16`)** | `final_price_at_lock()` (`pool.py:310-336`), `urban_pool_unmatched_settlement()` (`settlement.py:160-200`), trigger `bookings_locked_pool_price_guard()` (`0006:175-194`). Phát hiện xung đột tham số `SF-P3-16` khi `s_i = 2` làm `Quote_unmatched_i > P_i` cần Chủ dự án quyết định |
| 6 | **Chính sách phí hủy & vắng mặt (`D-52`) trên cả 5 dịch vụ** | **VERIFIED (PASS)** | `backend/app/modules/pricing/cancellation.py:24-190` và `fund/service.py:157-170`; kiểm chứng mới bằng `test_pricing_cancellation.py` (PASS 7 hàm / 17 test cases) |
| 7 | **Sổ cái Quỹ bảo đảm (`fund_ledger`) append-only, đối soát số dư & Thanh toán tài xế (`driver_payouts`) bất biến** | **SOURCE-VERIFIED & HISTORICAL-DB-VERIFIED** | `backend/app/modules/fund/service.py:42-227`, `alembic/versions/0006_p3_pricing_fund.py:101-194`; có đầy đủ 12 bài test DB trong `test_fund_and_price_protection.py` (PASS trong bằng chứng lịch sử; `NOT_EXECUTED` trên máy hiện tại do thiếu Docker/PostgreSQL) |
| 8 | **Tích hợp định giá Phase 3 vào bộ sinh ứng viên Phase 2 (`candidate/generator.py` & `pooling/insertion.py`)** | **SOURCE-VERIFIED & HISTORICAL-BENCH-VERIFIED** | `backend/app/modules/pricing/pool_check.py:18-115`, `pooling/insertion.py:216-226`, `candidate/generator.py:305-419`; hậu kiểm độc lập `64.698` ứng viên trong `20261105T054653Z-p3-integrated-verify/result.json` đạt **`0` vi phạm** |
| 9 | **Độ trễ sinh ứng viên tích hợp định giá Phase 3 đạt `p95 < 300 ms`** | **HISTORICAL_EVIDENCE_ONLY (PASS)** | Trong 3 lượt chạy chuẩn `a4`, `a5`, `a6` (`docs/implementation/evidence/p3_runs/`), độ trễ `generation_total_ms` `p95` cao nhất ở cấu hình nặng nhất `1000x20` là `150.78 ms` (`a4`), `162.78 ms` (`a5`), `109.76 ms` (`a6`) — thấp hơn nhiều so với ngưỡng `300 ms` |
| 10 | **Tuân thủ ranh giới kiến trúc Modular Monolith & Bất biến Cấu hình Baseline** | **VERIFIED (PASS)** | Kiểm chứng mới bằng `test_config_baseline.py` (PASS 4/4) và `test_architecture.py` (PASS 2/2 AST checks) |

---

## 3. Lý do Chưa Cấp `FULLY_VERIFIED` / `OWNER_ACCEPTED` Ngay Trong Phiên Này

1. **Về môi trường thực thi kiểm thử (`Test Re-execution Gap`):**
   - Máy Windows hiện tại chỉ có `Python 3.12.10` thuần và không có `docker`, `wsl`, `postgresql/postgis`, `redis`, `osrm`, `sqlalchemy`, `hypothesis`.
   - Do đó, **48 hàm test thuần Python (67 test cases)** đã được thực thi mới và PASS 100%, nhưng các bài test phụ thuộc cơ sở dữ liệu/container (`test_fund_and_price_protection.py`, `test_pricing_properties.py`, `test_candidate_generation.py`, `test_schema.py`, v.v.) và script benchmark `scripts/p2_benchmark.py` mới chỉ có bằng chứng chạy lịch sử (`HISTORICAL_EVIDENCE_ONLY` tại ngày 2026-11-05 trên cùng commit `f97a509`).
2. **Về quyết định nghiệp vụ của Chủ dự án (`Owner Decision Gap`):**
   - Finding **`SF-P3-16`** (xung đột công thức `Quote_unmatched_i` cho nhóm 2 ghế làm giá báo trước khi chưa ghép cao hơn giá đi riêng `P_i`) và 2 quyết định **`SF-P3-02`**, **`SF-P3-10`** cần Chủ dự án phê duyệt chính thức.

---

## 4. Điều kiện Đóng Nghiệm thu Phase 3 (`Exit Gate Checklist`)

- [x] Khảo sát 100% source code Phase 0–3 tại commit `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`.
- [x] Lập hồ sơ hiệu chỉnh 10 điểm sai lệch của báo cáo kiểm toán trước (`docs/implementation/P3_CODE_AUDIT_CORRECTIONS.md`).
- [x] Đối chiếu toàn bộ yêu cầu Revision 9 & Baseline v1 sang từng hàm và dòng code (`docs/implementation/P3_REQUIREMENT_TRACEABILITY.md`).
- [x] Thực thi mới toàn bộ 48 hàm test thuần Python (67 test cases) trên máy hiện tại (PASS 100%) và kiểm toán đầy đủ hồ sơ benchmark lịch sử (`docs/implementation/P3_TEST_AND_BENCHMARK_VERIFICATION.md`).
- [x] Lập sổ đăng ký 16 findings trình Chủ dự án (`docs/implementation/P3_OWNER_DECISION_REGISTER.md`).
- [x] Đánh giá mức độ sẵn sàng và các phụ thuộc cho Phase 4 (`docs/implementation/P3_PHASE4_READINESS.md`).
- [ ] Chủ dự án phê duyệt phương án xử lý `SF-P3-16`, `SF-P3-02`, `SF-P3-10`.
- [ ] Chạy lại `docker compose exec backend pytest` trên máy có Docker/WSL2 để xác nhận lại toàn bộ 135 bài test (bao gồm DB triggers, PostGIS, OSRM và Hypothesis) trước khi xuất `PHASE_3_COMPLETION_REPORT.md`.

