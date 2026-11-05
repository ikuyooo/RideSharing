# P3 — KẾ HOẠCH TRIỂN KHAI (pricing · fund)

- **Căn cứ:** R9 §79 P3 ("5 biểu giá, phân bổ kẹp hai đầu `[Floor_i, Cap_i]`, đóng băng khách đã khóa, Cổng thu nhập/giờ của tài xế, khung phí hủy Mục 18.7, `fund_ledger`, `driver_payouts`" — tiêu chí: "100% ca hồi quy cố định và 10.000 mẫu Hypothesis (Mục 71–72)"); chỉ thị "OWNER ACCEPTANCE OF P2 LOCAL & PHASE 3 KICKOFF" mục IV–VII.
- **Điều kiện bắt đầu:** P2 = `PHASE_2_LOCAL_ACCEPTED__KNOWN_LIMITATIONS` (commit `a1927de`).
- **Ngoài phạm vi P3:** Booking / Offer Cascade / máy trạng thái (P4), liên tỉnh vòng đời (P5), Smart Contract (P9). P3 không mở offer / booking.

## 1. Phân rã theo phụ thuộc kỹ thuật

| Bước | Nội dung | Phụ thuộc | Đầu ra |
|---|---|---|---|
| P3.1 | Lõi định giá: tiền tệ chính xác, tham số có kiểu đọc từ `pricing_configs`, 5 biểu giá | `pricing_configs` (P1) | `money.py`, `params.py`, `tariff.py`, `service.load_pricing` |
| P3.2 | Phân bổ công bằng: `PlanFare`, trọng số, `Floor_i` / `Cap_i`, F1–F3, thuật toán điểm gãy, làm tròn | P3.1 | `pool.py` |
| P3.3 | Cổng 1, Cổng 2A / 2B sau làm tròn, mã lý do chính xác | P3.2 | `pool.gate1`, `pool.gate2`, `pool.REASONS` |
| P3.4 | Chèn động D1–D6, nhóm L đóng băng, `PoolPricingCheck` tích hợp P2, lưu phân bổ theo `plan_version`, trigger bảo vệ giá | P3.2–3.3, P2 insertion | `pool.price_insertion`, `pool_check.py`, `pooling/pricing_state.py`, migration 0006 |
| P3.5 | Quỹ bảo đảm và payout: chia tiền, `GuaranteePayout` theo `unmatched_cause`, sổ cái chỉ ghi thêm, đối soát G12, giao diện P9 | P3.1 | `settlement.py`, `fund/service.py`, `fund/chain.py`, migration 0006 |
| P3.6 | Phí hủy §18.7 | P3.1 | `cancellation.py` |
| P3.7 | Kiểm thử: hồi quy §71.1 / §72.1, unit biên, Hypothesis ≥ 10.000 mẫu có bộ giải tham chiếu độc lập, CSDL, tích hợp generator; chạy lại toàn bộ P1 / P2 + smoke P0 + benchmark | P3.1–3.6 | `tests/test_pricing_*.py`, `tests/test_fund_and_price_protection.py` |

## 2. Giao diện với P2 (đã có) và P4 (sẽ dùng)

| Giao diện | Nội dung |
|---|---|
| P2 → P3 | `pooling.insertion.PricingCheck = Callable[[InsertionResult], Violation | None]`; P3 hiện thực bằng `PoolPricingCheck`. `InsertionResult` mang thêm `simulation` để đo `D_plan` / `T_plan` |
| P3 → P4 | `pool.price_new_plan`, `pool.price_insertion` (tính lại dưới khóa), `pricing_state.store_plan_pricing(plan_id, expected_version, …)`, `pool.final_price_at_lock`, `fund.settlement_for_completed_booking` + `fund.record_settlement`, `cancellation.cancellation_fee` + `fund.cancellation_settlement`. P4 còn phải: xác minh chuỗi bằng `/route` (SF-P2-15), cập nhật `driven_m_since_start` / `started_at` |
| P3 → P5 | `tariff.seat_reference / seat_price_band / door_surcharge / booking_price / topup_*`, `settlement.settle_intercity_pool` |
| P3 → P9 | `fund.chain.FundChainSync`, `LedgerEvent` (chưa có giao dịch on-chain nào) |

## 3. Bổ sung kỹ thuật vào schema (migration 0006)

| Bảng | Cột / ràng buộc | Lý do |
|---|---|---|
| `ride_plans` | `pricing_version`, `plan_fare_exact`, `driven_m_since_start`, `started_at` | Baseline §5.2; SF-P3-02, SF-P3-08 |
| `ride_participants` | `fare_exact_rational`; trigger đóng băng | SF-P3-08; G08 |
| `bookings` | `pricing_version`; trigger khóa giá pool | SF-P3-11; G08 |
| `driver_payouts` | `payout_kind`, `pricing_version`, `pool_policy_version`, `unmatched_cause`, `created_at`; CHECK chia tiền; trigger bất biến | G18; truy vết |
| `fund_ledger` | `pricing_version`, `pool_policy_version`, `ride_plan_id`, `reason`; CHECK dấu / số dư / seed; unique (booking, loại); trigger chỉ ghi thêm + chuỗi số dư | G12 |

## 4. Tiêu chí hoàn thành P3 (local)

1. 100 % ca hồi quy cố định §71.1 (4 vector, mọi nhánh) và §72.1 khớp **từng giá trị**; sai khác với ví dụ in → `SPEC_FINDINGS_P3`.
2. ≥ 10.000 mẫu Hypothesis của §71.2 chạy **và** đạt mọi bất biến 1–7, đối chiếu bộ giải độc lập; thêm bất biến G08 cho chèn động.
3. Test biên Floor / Cap, vô nghiệm, làm tròn, khách đã khóa, hourly rate, quỹ / payout, phí hủy, tích hợp `PoolPricingCheck`.
4. Toàn bộ test P1 / P2 vẫn đạt; smoke P0 đạt; `alembic check` sạch tại head 0006.
5. Hiệu năng sinh ứng viên sau tích hợp được đo lại theo đúng quy trình SF-P2-16 (worktree cố định, ≥ 3 lượt) và báo cáo trung thực.

`PHASE_3_COMPLETION_REPORT.md` chỉ được tạo khi cả 5 tiêu chí đạt và các phát hiện `OPEN` không chặn tiêu chí §79.
