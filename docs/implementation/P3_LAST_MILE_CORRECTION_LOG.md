# NHẬT KÝ HIỆU CHỈNH KỸ THUẬT CUỐI CÙNG (LAST-MILE CORRECTION LOG)
## (P3_LAST_MILE_CORRECTION_LOG)

- **Dự án:** Ride_Sharing
- **Commit HEAD:** `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`
- **Thời điểm:** 2026-11-10
- **Mục đích:** Ghi nhận 12 hiệu chỉnh kỹ thuật chi tiết theo yêu cầu của Master Prompt Remediation.

---

| ID | Vấn đề Sai Lệch Cũ | Bằng Chứng Mã Nguồn Thực Tế (Source of Truth) | Nội Dung Đã Sửa Đổi | Tệp Tin Đã Hiệu Chỉnh | Trạng Thái Sau Sửa |
|---|---|---|---|---|---|
| `CORR-01` | Tham số Baseline `d_max` bị tính nhầm thành $1 - d_{\max} = 0.60$ | `mvp_config_baseline_v1.yaml:14` ghi `d_max: 0.60`. Trong code `pool.py:117` nhân với $(1 - d_{\max}) = \mathbf{0.40}$ | Sửa công thức Floor nhân đúng hệ số $0.40$ (thay vì $0.60$) | `P3_PRICING_FUND_FINAL_VERIFICATION.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-02` | `SeatFactor(2)` bị ghi nhầm thành 1.05 | `mvp_config_baseline_v1.yaml:15` ghi `party_seat_surcharge_gamma: 0.35`. `pool.py:105` tính `1 + 0.35*(2-1) = \mathbf{1.35}` | Khôi phục đúng $\text{SeatFactor}(2) = 1.35$ | `P3_PRICING_FUND_FINAL_VERIFICATION.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-03` | Số liệu kiểm chứng Vector 2 (2 ghế) bị sai ($122.220$đ) | `tests/test_pricing_regression.py:48`: `assert A.floor == q("104760")` | Sửa đúng $\text{raw\_floor} = \max(20k, 194k \times 0.40 \times 1.35) = \mathbf{104.760\text{ đ}}$ | `P3_PRICING_FUND_FINAL_VERIFICATION.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-04` | Phí hủy bị cào bằng thành "30% PrivateFare cho mọi dịch vụ" hoặc trần nhầm 50.000đ | `pricing/cancellation.py:86-140` và `mvp_config_baseline_v1.yaml:40-50`: Bike/Car Single áp dụng tỷ lệ 20% và trần 20.000đ; Pool áp dụng 20% trên Quote; Intercity 20%/50%/100% | Lập bảng ma trận phí hủy chuẩn hóa 20%, trần 20.000đ và tỷ lệ chia chi tiết cho từng dịch vụ | `P3_PRICING_FUND_FINAL_VERIFICATION.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-05` | Đề xuất sai ràng buộc `UNIQUE (ride_id, dropoff_order)` trên `ride_participants` (`TF-P3-01`) | `pooling/models.py:34-72`: `ride_participants` không có `ride_id`, không có `dropoff_order`. Thứ tự điểm dừng nằm ở `ride_stops.seq` | Hủy bỏ đề xuất constraint trên `ride_participants`; xác nhận `ride_stops.seq` quản lý chuẩn | `P3_PHASE4_HANDOFF_CHECKLIST.md`, `P3_OWNER_DECISION_PACKAGE.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-06` | Khóa ngoại `driver_offers.driver_id` tham chiếu nhầm `driver_profiles.id` | `driver/models.py:10`: Khóa chính của `driver_profiles` là `user_id` (không có cột `id`) | Sửa khóa ngoại tham chiếu chính xác tới `driver_profiles.user_id` | `P3_PHASE4_HANDOFF_CHECKLIST.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-07` | Pool Lock Point bị mô tả nhầm là "cách điểm đón $\le 3\text{ km}$" | `mvp_config_baseline_v1.yaml:31`: `pool_lock_remaining_km: 3.0` (quãng đường còn lại tới điểm TRẢ KHÁCH) | Sửa đúng vị trí kích hoạt là mốc còn lại $\le 3.0\text{ km}$ tới điểm trả khách (Drop-off) | `P3_PHASE4_HANDOFF_CHECKLIST.md`, `P3_FINAL_ACCEPTANCE_ASSESSMENT.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-08` | Đánh đồng `payment_status` với schema thực tế | `booking/models.py:52-63`: Cột chính xác là `escrow_status` (NONE, DEPOSITED, LOCKED, RELEASED, v.v.) | Khôi phục đúng tên trục trạng thái `escrow_status` trong máy trạng thái D-46 | `P3_PHASE4_HANDOFF_CHECKLIST.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-09` | Lấy nhầm số liệu độ trễ từ lượt benchmark `verify` bị gián đoạn (host suspend) | `verify/LATENCY_DISTURBED.md` cảnh báo cấm dùng độ trễ của verify. Các lượt sạch là `a4`, `a5`, `a6` | Lấy số liệu latency chuẩn từ `a4` (150.78 ms), `a5` (162.78 ms), `a6` (109.76 ms) | `P3_FINAL_TEST_EVIDENCE.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-10` | Bỏ sót rủi ro 204/17.640 pool candidates vi phạm khi recheck OSRM `/route` | `verify/result.json` mục `sf_p2_15_default_routing`: 204/17.640 ứng viên bị vi phạm HC03/HC05 do sai khác giữa `/table` và `/route` | Bổ sung bắt buộc bước recheck OSRM `/route` trong pipeline bàn giao Phase 4 | `P3_FINAL_TEST_EVIDENCE.md`, `P3_PHASE4_HANDOFF_CHECKLIST.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-11` | Giả định `seed_fund()` có thể dùng để nạp thêm vốn mồi khi vận hành | `fund/models.py:73-88`: Có index `uq_fund_ledger_single_seed` và chỉ cho phép 4 `entry_type`, cấm gọi seed lần 2 | Xác định code hiện tại chưa hỗ trợ top-up; thiết kế thêm `TOPUP` vào migration 0007 | `P3_OWNER_DECISION_PACKAGE.md`, `P3_PHASE4_HANDOFF_CHECKLIST.md` | **ĐÃ SỬA CHUẨN XÁC** |
| `CORR-12` | Tuyên bố chạy pytest và hypothesis trên host trong khi máy thiếu package | Lệnh `pip show pytest hypothesis` cảnh báo `Package(s) not found`. Docker không cài đặt | Phân loại minh bạch: test thuần chạy qua custom script, test DB/Docker là `HISTORICAL_EVIDENCE_ONLY` | `P3_FINAL_TEST_EVIDENCE.md`, `P3_FINAL_ACCEPTANCE_ASSESSMENT.md` | **ĐÃ SỬA CHUẨN XÁC** |

