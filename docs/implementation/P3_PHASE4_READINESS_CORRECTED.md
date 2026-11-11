# ĐÁNH GIÁ MỨC ĐỘ SẴN SÀNG CHO PHASE 4 ĐÃ HIỆU CHỈNH (PHASE 4 READINESS REASSESSMENT)

- **Repository Root**: `C:\RideSharing`
- **Commit HEAD**: `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`
- **Căn cứ đặc tả**: Mục 79 (dòng 3365–3381) và Mục 73 Đặc tả Revision 9.

---

## 1. Xác định Ranh giới Phạm vi Chuẩn của Phase 4 theo Revision 9 Mục 79

Báo cáo phiên trước đã liệt kê sai phạm vi Phase 4 khi đưa cả các module và tính năng thuộc các phase sau vào (như nghiệp vụ liên tỉnh của Phase 5, giao diện Web và gợi ý Top-K của Phase 6, hợp đồng thông minh Blockchain của Phase 9, hay thuật toán ghép theo lô CP-SAT của Phase 10).

Theo **Mục 79 (dòng 3373)** của Đặc tả Revision 9:

> **Phase 4**: Cài đặt Module `booking`, `ride`, `jobs` (`SELECT ... FOR UPDATE SKIP LOCKED`), máy trạng thái trực giao (`ride_status`, `price_status`), chuỗi `Offer Cascade` với `Per-Offer Seat Hold`, `Idempotency-Key` và kích hoạt `pool_lock_point`.
> **Tiêu chí nghiệm thu mốc**: Vượt qua toàn bộ bài test đồng thời (Mục 73): `0 oversell`, chuỗi 3 lần offer không rớt ghế.

### Bảng phân định ranh giới giữa Phase 4 và các Phase kế tiếp

| Thành phần / Tính năng | Thuộc Phase | Ghi chú lộ trình |
|---|---|---|
| Module `booking`, tạo booking, máy trạng thái trực giao (`ride_status`, `price_status`) | **Phase 4** | Cốt lõi giao dịch |
| Chuỗi gửi Offer (`Offer Cascade`) với `Per-Offer Seat Hold` (TTL 35s/75s) | **Phase 4** | Chống rớt ghế |
| Hàng đợi tác vụ nền `scheduled_jobs` (`FOR UPDATE SKIP LOCKED`) | **Phase 4** | Quét timeout offer, timeout cọc |
| Kích hoạt khóa giá tại `pool_lock_point` (chuyển `MATCHED_LOCKED` / `UNMATCHED_LOCKED`) | **Phase 4** | Kích hoạt bộ tính giá P3 |
| Kiểm soát đồng thời đặt ghế cuối cùng (`0 oversell`, Mục 73.1) | **Phase 4** | Khóa dòng cấp CSDL |
| Nghiệp vụ Liên tỉnh (`intercity`): đăng chuyến, đặt ghế, chốt T-72h, hủy T-60h, thứ tự đón T-24h | **Phase 5** | Không thuộc Phase 4 |
| Gợi ý Baseline Top-K đa phương tiện có giải thích (Mục 35.5, 40) | **Phase 6** | Mốc Nghiệm thu 1 |
| Giao diện Web hợp nhất (`Unified Demo Workbench`, Mục 62) | **Phase 6** | Mốc Nghiệm thu 1 |
| Simulator 5 dịch vụ, ước lượng MNL từ Khảo sát S1, sinh 50K requests (Mục 48) | **Phase 7** | Đóng vòng giả lập |
| Huấn luyện mô hình AI: `P(match)` OOF, `P(fulfill)`, `LGBMRanker` (Mục 44–47) | **Phase 8** | Mốc Nghiệm thu 2 |
| Tích hợp Blockchain Escrow on-chain, ví HD Custodial, kiểm tra cổng `RIDE_STARTED` | **Phase 9** | Mốc Nghiệm thu 3 |
| Ghép theo lô OR-Tools CP-SAT trên đồ thị RTV (S4) và Gộp/Góp liên tỉnh (S5) | **Phase 10** | Mở rộng SHOULD |

---

## 2. Kiểm kê Tài sản Kỹ thuật của Phase 3 Sẵn sàng Bàn giao cho Phase 4

Toàn bộ các thành phần nền tảng thuộc phạm vi Phase 3 đã sẵn sàng để phục vụ Phase 4:

1. **Biểu giá và Định giá hoàn chỉnh (`pricing/tariff.py`, `pool.py`)**:
   - `pool_quote_for(p, private)`: Cung cấp trần giá `Quote_i` và mức ký quỹ tối đa `Unmatched_i` khi tạo booking `CAR_URBAN_POOL`.
   - `price_insertion(p, input)`: Cung cấp thuật toán phân bổ 2 cận cho các chèn điểm động khi xe đang chạy.
   - `final_price_at_lock(p, private, matched, fare_charged, cause)`: Cung cấp giá khóa chuẩn xác khi booking chạm `pool_lock_point`.
2. **Cổng kiểm tra điều kiện sinh ứng viên (`candidate/service.py`)**:
   - Hàm `offerable(c.pricing_check)` đã được hiện thực: chỉ cho phép chào offer hoặc đặt chỗ đối với các ứng viên có `pricing_check == "COMPLETE"`, ngăn chặn việc chào các ứng viên chưa hoàn tất định giá hoặc thuộc kế hoạch lỗi.
3. **Sổ cái Quỹ và Đối soát tự động (`fund/service.py`, `pricing/settlement.py`, `cancellation.py`)**:
   - `record_settlement()`: Ghi nhận tất toán chuyến đi (hoa hồng, thu nhập tài xế, trích quỹ 3%, chi bù bảo đảm) theo phương thức lũy đẳng.
   - `cancellation_fee()`: Tính toán chính xác phí hủy chuyến và hoàn trả cọc theo đúng Mục 18.7.
   - `reconcile()`: Đối soát tức thời số dư Quỹ và tổng dòng tiền, bảo đảm cổng `G12 = 0 VND`.
4. **Bảo vệ toàn vẹn dữ liệu ở tầng CSDL (`0006_p3_pricing_fund.py`)**:
   - Trigger `trg_bookings_locked_pool_price`: Khóa cứng giá trong bảng `bookings` sau khi đã đạt `MATCHED_LOCKED` hoặc `UNMATCHED_LOCKED`, bảo đảm Phase 4 không bao giờ vô tình ghi đè giá đã khóa.
   - Trigger `trg_ride_participants_frozen`: Đóng băng toàn bộ các trường giá của hành khách đã qua `pool_lock_point`.
   - Trigger `trg_fund_ledger_guard`: Bảo đảm sổ cái Quỹ chỉ-ghi-thêm (append-only) và chuỗi số dư liên tục có khóa `pg_advisory_xact_lock`.

---

## 3. Các Điều kiện Tiên quyết Cần Chủ Dự án Phê duyệt Trước khi Triển khai Phase 4

Mặc dù nền tảng mã nguồn đã hoàn chỉnh, để Phase 4 được triển khai mà không phải phỏng đoán nghiệp vụ, cần các quyết định chính sách sau từ Project Owner:

1. **Quyết định về `SF-P3-10` (Chính sách xử lý khi Quỹ bảo đảm không đủ số dư)**:
   - Hiện tại code ném lỗi `FundInsufficient` và migration 0006 chặn số dư âm (`balance_after_vnd >= 0`).
   - Project Owner cần phê duyệt chính sách: Nền tảng sẽ tự động nạp vốn mồi bổ sung (`TOPUP_SEED`) khi số dư chạm ngưỡng tối thiểu, hay tạm hoãn chuyến xe, hay chuyển sang cơ chế bảo lãnh tài chính khác.
2. **Quyết định về `SF-P3-05` (Khấu trừ hay cộng thêm phí hủy của đồng hành khi hủy sớm `CORIDER_CANCELLED_EARLY`)**:
   - Project Owner cần phê duyệt: Khoản 50% phí hủy của người hủy sớm trả cho tài xế có được khấu trừ vào khoản bù `GuaranteePayout = 7.300 đ` của hành khách còn lại hay được coi là khoản bù riêng cho thời gian chạy rỗng đã phát sinh.
3. **Định hướng về `SF-P3-16` (Tương tác giữa Gate 2B và OSRM free-flow)**:
   - Gate 2B với `eps_hourly = 0` trên OSRM free-flow loại hầu hết các phương án ghép Nhánh A. Điều này không chặn việc phát triển máy trạng thái booking và luồng đi xe đơn của Phase 4, nhưng cần định hướng trước khi đánh giá tỷ lệ ghép ở Phase 6–8.

---

## 4. Kết luận Mức độ Sẵn sàng

- **Trạng thái**: **CONDITIONALLY READY FOR PHASE 4 (ĐỦ ĐIỀU KIỆN THIẾT KẾ KIẾN TRÚC VÀ BƯỚC VÀO PHASE 4 SAU KHI CÓ PHÊ DUYỆT CỦA PROJECT OWNER)**.
- **Ràng buộc tuân thủ**:
  - Không được cấp quyền `OWNER_ACCEPTED` trong báo cáo này.
  - Không được tự ý triển khai code Phase 4 khi Project Owner chưa ra chỉ thị bắt đầu Phase mới.

