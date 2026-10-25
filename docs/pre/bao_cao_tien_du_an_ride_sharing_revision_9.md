# BÁO CÁO TIỀN DỰ ÁN — REVISION 9

## XÂY DỰNG NỀN TẢNG ĐẶT XE THÔNG MINH ĐA DỊCH VỤ (XE MÁY, TAXI BAO XE, TAXI GHÉP NỘI ĐÔ VÀ LIÊN TỈNH) VỚI ĐỊNH GIÁ GHÉP CÔNG BẰNG, GỢI Ý CHUYẾN BẰNG AI VÀ KÝ QUỸ BLOCKCHAIN

*A Multi-Service Smart Ride Platform (Motorbike, Private Taxi and Pooled Taxi, Urban and Intercity) with Fair Shared Pricing, AI Recommendation and Blockchain Escrow*

- **Loại tài liệu:** Pre-build Functional, Algorithmic & Technical Blueprint (Đặc tả Nghiệp vụ, Thuật toán và Kỹ thuật Tiền dự án)
- **Thay thế:** Revision 8 (Tích hợp kết quả kiểm toán toán học, đồng thời và thiết kế nghiên cứu)
- **Phạm vi:** Năm dịch vụ trên một lõi kiến trúc chung (Mục 2)
- **Thứ tự ưu tiên triển khai:** Core → **AI** → **Blockchain** (tận dụng nền tảng hợp đồng thông minh hiện có) → Mở rộng thuật toán ghép (Ghép theo lô & Gộp chuyến)
- **Quy ước trình bày:**
  - Mọi công thức toán học được viết ở dạng plain-text/biểu thức tường minh để hiển thị chính xác trên mọi trình đọc Markdown.
  - Mọi con số giá cơ sở, giá/km và giá/phút trong tài liệu là **tham số cấu hình minh họa** (Phụ lục B). Khi vận hành mô phỏng hoặc chạy thử nghiệm, quãng đường và thời gian di chuyển được lấy trực tiếp từ OSRM, còn biểu giá được hiệu chỉnh theo giá công bố của thị trường.
  - Để phân biệt rõ giữa các quy tắc đã có đủ căn cứ kỹ thuật và các quyết định cần phê duyệt hoặc kiểm chứng thêm, tài liệu sử dụng hệ thống 4 nhãn trạng thái quyết định xuyên suốt (chi tiết tại Phụ lục A và Phụ lục E):
    - `[ACCEPTED]`: Đã được chứng minh về mặt toán học/kỹ thuật và chốt đưa vào đặc tả chuẩn.
    - `[PROPOSED]`: Phương án thiết kế được khuyến nghị kèm phân tích đánh đổi (trade-off), chờ chủ dự án phê duyệt chính thức.
    - `[NEEDS_VALIDATION]`: Cần dữ liệu khảo sát, mô phỏng hoặc benchmark thực nghiệm để xác lập ngưỡng tham số tối ưu.
    - `[NEEDS_EXTERNAL_CONFIRMATION]`: Cần xác nhận từ giảng viên hướng dẫn, quản trị viên hợp đồng thông minh hoặc chuyên gia pháp lý.

> **Lưu ý về tài liệu và hiện trạng tiền dự án:** Tài liệu này là đặc tả thiết kế tiền dự án độc lập và hoàn chỉnh. Các tham chiếu tới mô-đun định giá (`pool_pricing`), hợp đồng thông minh ký quỹ (`RideEscrow`) hoặc khảo sát người dùng (`S1`) trong tài liệu mô tả **đặc tả mục tiêu và giao diện chuẩn** mà giai đoạn hiện thực hóa tiếp theo phải tuân thủ; tài liệu không giả định bất kỳ đoạn mã nguồn chưa được kiểm chứng nào là đã hoàn thành.

---

# TÓM TẮT THAY ĐỔI SO VỚI REVISION 8 (REVISION 8 → REVISION 9)

Revision 9 giữ nguyên tầm nhìn sản phẩm 5 dịch vụ, kiến trúc Modular Monolith và khung nghiên cứu của Revision 8, đồng thời giải quyết triệt để **8 điểm nghẽn nghiêm trọng (P0)** và **9 khoảng trống đặc tả (P1)** được phát hiện qua kiểm toán toán học và phân tích trạng thái:

| # | Hạng mục thay đổi trong Revision 9 | Vấn đề của Revision 8 được giải quyết | Mục tham chiếu | Trạng thái |
|---|---|---|---|---|
| 1 | **Bổ sung cận dưới giá ghép (`Floor_i`) và thuật toán phân bổ kẹp hai đầu (Two-sided Bounded Allocation)** | Công thức Mục 15.2 của Rev8 chỉ có trần `Cap_i` mà không có sàn `Floor_i`, dẫn đến phản ví dụ khách đi chặng ngắn kèm đi bộ/đi vòng nhận giá âm (`Fare_i = -3.677 đ`) hoặc gần bằng 0 khi ghép 3–4 khách. | Mục 15.1, 15.3, Phụ lục E (O-01) | `[ACCEPTED]` (Đã phê duyệt `d_max = 0.60`, `on_lower_bound_infeasible = "REJECT"`) |
| 2 | **Quy tắc đóng băng giá đã khóa (`Frozen Fare Rule`) và hệ 6 điều kiện `D1–D6` khi chèn khách động lúc xe đang chạy** | Xung đột giữa `pool_lock_point` cá nhân (Mục 11) và việc tính lại `PlanFare` toàn chuyến khi chèn thêm khách C (Mục 15.1), làm thay đổi giá của khách B đã khóa hoặc làm tăng giá ước tính của khách đang ngồi trên xe. | Mục 11, 15.5, 36, Phụ lục E (O-02) | `[ACCEPTED]` |
| 3 | **Tách bạch Bất biến tổng thu nhập chuyến của tài xế và Ràng buộc tốc độ sinh lời theo giờ sau làm tròn (`Driver Hourly Rate Filter`)** | Phản ví dụ chứng minh điều kiện Shareability (Mục 14) không tự động bảo đảm bất biến `thu_nhập_giờ(ghép) >= thu_nhập_giờ(xe đơn)` (Mục 17 & 71) khi thời gian dừng đón/trả làm tăng mẫu số thời gian (`223.125 đ/giờ < 232.800 đ/giờ`). | Mục 14, 17, 71, Phụ lục E (O-03) | `[ACCEPTED]` |
| 4 | **Chuẩn hóa Hệ số phụ trội ghế thứ hai (`party_seat_surcharge_gamma`) trong trọng số chia tiết kiệm $w_i$ & cận dưới `Floor_i` cho booking ghép 2 ghế nội đô, và Hoa hồng khi góp thêm liên tỉnh (`CONFIRMED_TOPUP`)** | Ở nội đô, khách đặt 2 ghế trả bằng khách đặt 1 ghế; nếu nhân hệ số ghế trực tiếp vào `PrivateFare` khi tính `Quote/Unmatched` sẽ vi phạm chính sách `Unmatched < PrivateFare`. Do đó giữ nguyên `PrivateFare(i)` làm cơ sở tính `Cap_i, Quote_i, Gap_i, Unmatched_i` và đưa hệ số ghế thứ hai $\gamma_{\text{seat}}$ vào giảm trọng số nhận tiết kiệm $w_i$ và nâng `Floor_i`. Ở liên tỉnh (Mục 29), quy định rõ hoa hồng 15% (`c_private`) cho `CONFIRMED_TOPUP`. | Mục 12.2, 15.2, 15.3, 18.3, 29, Phụ lục E (O-04) | `[ACCEPTED]` (Đã phê duyệt $\gamma_{\text{seat}} = 0.35$) |
| 5 | **Tách máy trạng thái trực giao (`ride_status` vs `price_status`) và cấp phát `seat_hold` theo từng bước Offer (`Per-Offer Seat Hold`)** | Ở Rev8, `PRICE_LOCKED` ghi đè lên `RIDE_STARTED` trên cùng một cột trạng thái; `seat_hold_ttl = 60s` xung đột với chuỗi 3 lần offer × 20s = 60s (và 90s < 3×60s ở liên tỉnh), đồng thời giữ khóa sai xe khi chuyển tiếp offer. | Mục 9, 22, 41, 42, 56 | `[ACCEPTED]` |
| 6 | **Chuẩn hóa đơn vị tiền tệ On-chain thành `1 VND` (số nguyên `uint256`) và hạch toán Quỹ bảo đảm nội bộ trên hợp đồng** | Quy ước `1 token = 1.000 đ để tránh số lẻ` (Mục 80.1 Rev8) mâu thuẫn trực tiếp với các khoản giải ngân lẻ hàng trăm/chục đồng (`147,9 token`, `7,3 token`, `541,45 token` ở Mục 80.2), gây lỗi cắt cụt số nguyên trên EVM. | Mục 80.1, 80.2, 80.3, Phụ lục E (O-05) | `[ACCEPTED]` |
| 7 | **Bổ sung cổng đồng bộ ký quỹ trước khi khởi hành (`RIDE_STARTED` Escrow Gate) và làm rõ mô hình ví Custodial/Relayer cho mức MUST** | Ký quỹ bất đồng bộ không chặn `CONFIRMED`, nhưng nếu cho phép `RIDE_STARTED` và `COMPLETED` khi giao dịch on-chain thất bại sẽ gây mất tiền giải ngân; làm rõ vai trò của ví hệ thống ở M12 so với MetaMask ở C7. | Mục 9.3, 80.1, 80.4, Phụ lục E (O-06) | `[ACCEPTED]` |
| 8 | **Đồng bộ hóa Đóng góp nghiên cứu (Mục 0.1), Giả thuyết H1–H11 (Mục 74) và nâng `H9` lên mức MUST** | Đóng góp về xếp hạng chung đa phương tiện (`H9`) được nêu ở Mục 0.1 nhưng lại xếp vào SHOULD ở Rev8; bổ sung đầy đủ quy trình Out-of-Fold cho `P(match)` và cây sự kiện tuần tự cho `p_fulfill` để triệt tiêu rò rỉ dữ liệu. | Mục 0.1, 0.2, 39, 44, 46, 74, 78 | `[ACCEPTED]` |
| 9 | **Bổ sung đặc tả vùng đệm không gian (`URBAN`/`INTERCITY`), công thức `DoorSurcharge`, mô hình đồ thị RTV cho CP-SAT và khung tham số Chính sách hủy (`S6`)** | Khắc phục chuyến ngắn 4,5 km cắt ranh giới quận/huyện bị ép thành liên tỉnh; định nghĩa `DoorSurcharge` tất định lúc đặt; sửa lỗi cộng tuyến tính hai cạnh độc lập trong ghép theo lô CP-SAT; định nghĩa tham số phí hủy cho Smart Contract. | Mục 2.3, 18.7, 28.3, 30, 36, 37.2, 61 | `[ACCEPTED]` |

---

# MỤC LỤC

- **PHẦN 0 — Đề tài, Mục tiêu nghiên cứu và Phân loại phạm vi (Must / Should / Could / Won't)**
  - 0.1. Đề tài và Đóng góp nghiên cứu – kỹ thuật
  - 0.2. Phân loại phạm vi (MoSCoW) và Tỷ trọng công sức
- **PHẦN I — Tổng quan bài toán, Đối tượng sử dụng và Ma trận năm dịch vụ**
  - 1. Phân tích bài toán thực tế và Nhu cầu người dùng
  - 2. Ma trận năm dịch vụ và Quy tắc phân loại không gian – thời gian
  - 3. Các vai trò và Quyền hạn trong hệ thống
  - 4. Luồng nghiệp vụ tổng quát theo từng nhóm dịch vụ
  - 5. Kiến trúc hệ thống mức cao (Modular Monolith)
- **PHẦN II — Quy tắc nghiệp vụ chung, Ràng buộc cứng và Vòng đời trạng thái**
  - 6. Trip Intent và Quy tắc suy diễn tập dịch vụ hợp lệ
  - 7. Hệ thống 11 ràng buộc cứng (Hard Constraints)
  - 8. Quy tắc ngân sách (Cứng và Mềm)
  - 9. Hệ thống máy trạng thái trực giao (Booking Ride Status, Price Status & Escrow Status)
- **PHẦN III — Nội đô: Xe máy, Taxi bao xe, Taxi ghép và Mô hình định giá – Kinh tế**
  - 10. Ba dịch vụ nội đô và Cơ chế Top-K đa phương tiện
  - 11. Hình thức đặt, Cửa sổ ghép động và Điểm khóa giá (`pool_lock_point`)
  - 12. Giá tham chiếu taxi bao xe nội đô và Hệ số ghế cho nhóm 2 khách
  - 13. Giá của cả chuyến ghép (`PlanFare`)
  - 14. Điều kiện khả năng chia sẻ (Shareability) và Ràng buộc sinh lời của tài xế
  - 15. Mô hình phân bổ giá ghép theo trọng số bất tiện có chặn hai đầu (`Floor_i` & `Cap_i`) và Chèn khách động
  - 16. Kiểm chứng định lượng: Ví dụ chuẩn Phenikaa → Đống Đa và các kịch bản biên (3–4 khách, chèn động)
  - 17. Thu nhập tài xế khi ghép, Quy tắc làm tròn và Đối soát phần lẻ
  - 18. Cơ chế chia sẻ rủi ro ba bên khi không ghép được, Chống phá ghép và Khung chính sách hủy
  - 19. Quỹ bảo đảm ghép: Công thức hòa vốn tổng quát và Phân tích độ nhạy
  - 20. Trải nghiệm hiển thị giá minh bạch và Vòng đời giá của Booking Pool
  - 21. Động cơ kinh tế của tài xế thay cho Quota 4:1
  - 22. Máy trạng thái chi tiết của Taxi ghép nội đô
  - 23. Điểm đón gặp nhau (Meeting Points — COULD C9)
  - 24. Chuyến quen lặp lại hằng ngày (Recurring Trips — COULD C4)
- **PHẦN IV — Liên tỉnh: Taxi bao xe và Taxi ghép theo lịch trình**
  - 25. Taxi bao xe liên tỉnh (`CAR_INTERCITY_PRIVATE`)
  - 26. Taxi ghép liên tỉnh (`CAR_INTERCITY_POOL`): Tài xế đăng chuyến và Quản lý ngưỡng
  - 27. Các mốc thời gian vòng đời chuyến ghép liên tỉnh (`T−7 ngày` → `T`)
  - 28. Mô hình giá ghế suy ngược từ ngưỡng khởi hành và Công thức phụ phí ngoài vùng (`DoorSurcharge`)
  - 29. Quy trình chốt chuyến tại `T−72h`, Góp thêm tự nguyện (`CONFIRMED_TOPUP`) và Xử lý thiếu khách
  - 30. Thuật toán và Quy tắc gộp chuyến liên tỉnh (`POOL_TRIP_MERGED` — SHOULD S5)
  - 31. Tối ưu hóa thứ tự đón tại `T−24h`
  - 32. Máy trạng thái chi tiết của Chuyến ghép liên tỉnh
  - 33. Các mở rộng liên tỉnh: Mô hình `P(fill)`, Danh sách chờ và Ghép chiều về (COULD C10, C11)
- **PHẦN V — Thuật toán Định tuyến, Sinh ứng viên, Ghép xe và Kiểm soát đồng thời**
  - 34. Định tuyến OSRM hai profile, Không gian PostGIS và Chiến lược gọi ma trận đơn lẻ
  - 35. Thuật toán sinh ứng viên cho năm dịch vụ và Quy tắc trộn Top-K
  - 36. Thuật toán chèn điểm đón/trả động có nhận biết trạng thái xe đang chạy
  - 37. Thuật toán ghép theo lô (Batch Matching CP-SAT trên đồ thị RTV rút gọn — SHOULD S4)
  - 38. Tổng hợp thuật toán định giá toàn hệ thống
  - 39. Mô hình xác suất hoàn thành chuyến (`p_fulfill`) theo cây sự kiện tuần tự
  - 40. Hàm mục tiêu gợi ý Baseline có giải thích
  - 41. Chuỗi gửi Offer (Offer Cascade) và Cơ chế giữ ghế theo từng bước (`Per-Offer Seat Hold`)
  - 42. Kiểm soát đồng thời bằng `plan_version`, Khóa dòng và Tính lũy đẳng (`Idempotency-Key`)
- **PHẦN VI — Trí tuệ nhân tạo (AI/ML), Simulator và Phương pháp nghiên cứu**
  - 43. Vai trò, Ranh giới an toàn và Các bài toán AI trong hệ thống
  - 44. Mô hình Learning-to-Rank (LTR) xếp hạng đa phương tiện và Thiết kế chẩn đoán 2×2
  - 45. Mô hình dự báo xác suất ghép thành công `P(match)` và Quy trình huấn luyện Out-of-Fold
  - 46. Mô hình hoàn thành chuyến có điều kiện và Xử lý rủi ro cạnh tranh (Competing Risks)
  - 47. Hiệu chỉnh xác suất (Calibration) và Công thức điểm xếp hạng cuối cùng
  - 48. Thiết kế Simulator 5 dịch vụ tái lập được và Cơ chế chống rò rỉ biến ẩn
  - 49. Xử lý khởi đầu lạnh (Cold Start) và Thiên lệch vị trí hiển thị (Position Bias)
  - 50. Chatbot chuyển đổi ngôn ngữ tự nhiên thành Trip Intent (COULD C1)
  - 51. Dự báo nhu cầu taxi ghép theo khu vực × 15 phút (COULD C2)
  - 52. Mô hình dự báo xác suất đủ ghế liên tỉnh `P(fill)` (COULD C10)
- **PHẦN VII — Kiến trúc phần mềm, Cơ sở dữ liệu, API, Bảo mật, An toàn và Pháp lý**
  - 53. Ngăn xếp công nghệ (Technology Stack)
  - 54. Phân rã Module và Ranh giới giao tiếp trong Modular Monolith
  - 55. Thiết kế bảng tác vụ định thời (`scheduled_jobs`) và Cơ chế thực thi an toàn
  - 56. Thiết kế Cơ sở dữ liệu, Ràng buộc toàn vẹn (Constraints) và Chỉ mục (Indexes)
  - 57. Đặc tả giao diện API và Quy tắc xử lý lỗi / Đồng thời
  - 58. Danh mục sự kiện hệ thống (Domain & Audit Events)
  - 59. Kiến trúc Bảo mật, Phân quyền và Bảo vệ dữ liệu cá nhân (Privacy)
  - 60. Cơ chế An toàn cho hành khách và tài xế khi đi ghép (SHOULD S9)
  - 61. Phân tích Rủi ro pháp lý tại Việt Nam và Giải pháp Hợp đồng điện tử đồng thuê chuyến
  - 62. Thiết kế giao diện người dùng (UI Screens & Unified Demo Workbench)
  - 63. Hệ thống chỉ số giám sát vận hành và kỹ thuật (Observability Metrics)
- **PHẦN VIII — Chiến lược Dữ liệu, Thiết kế Khảo sát và Quản lý Tập huấn luyện**
  - 64. Chiến lược nguồn dữ liệu đa tầng
  - 65. Thiết kế Khảo sát lựa chọn rời rạc (Stated Preference Survey — S1) và Phân tầng mẫu
  - 66. Cấu trúc bản ghi huấn luyện (Training Instance Schema)
  - 67. Quy tắc chia tập dữ liệu theo thời gian và Chống rò rỉ thông tin
  - 68. Quy mô dữ liệu theo từng cấp độ kiểm thử
  - 69. Quản lý phiên bản và Truy vết dữ liệu – mô hình (Lineage & Reproducibility)
- **PHẦN IX — Kế hoạch Kiểm thử, Giả thuyết nghiên cứu và Definition of Done**
  - 70. Hệ thống 18 Cổng đúng đắn bắt buộc (`= 0` Invariant Gates)
  - 71. Đặc tả kiểm thử định giá và Các bất biến toán học (Property-based Testing Spec)
  - 72. Đặc tả kiểm thử luật dịch vụ, Thời gian đặt và Vòng đời liên tỉnh
  - 73. Đặc tả kiểm thử đồng thời, State Machine và Bảo mật
  - 74. Hệ thống Giả thuyết nghiên cứu (`H1–H11`) và Ma trận ánh xạ đóng góp
  - 75. Thiết kế phương pháp đánh giá thực nghiệm và Kiểm định thống kê
  - 76. Hệ thống chỉ số đánh giá toàn diện (Mobility, Pooling, Economic, AI & Fairness Metrics)
  - 77. Chỉ tiêu hiệu năng hệ thống (SLA / Latency Targets)
  - 78. Tiêu chuẩn hoàn thành dự án (Definition of Done — Đạt / Tốt / Xuất sắc)
- **PHẦN X — Lộ trình triển khai, Tích hợp Blockchain Escrow và Quản trị rủi ro**
  - 79. Lộ trình 12 Phase theo phụ thuộc kỹ thuật và Thứ tự cắt giảm an toàn
  - 80. Thiết kế kiến trúc Ký quỹ Blockchain (Escrow Lifecycle, Đơn vị tiền tệ, Quỹ on-chain & Xử lý lỗi)
  - 81. Quy trình xác minh tài xế KYC Mock (SHOULD S7)
  - 82. Bảng quản trị rủi ro kỹ thuật, Nghiên cứu và Vận hành
  - 83. Tổng kết thiết kế Revision 9
  - 84. Hướng phát triển sau đồ án
- **PHỤ LỤC**
  - Phụ lục A — Decision Register cập nhật (`D-01` đến `D-52`) kèm nhãn trạng thái
  - Phụ lục B — Bảng tham số cấu hình chuẩn (YAML Specification)
  - Phụ lục C — Từ điển thuật ngữ và Ký hiệu toán học
  - Phụ lục D — Tài liệu tham khảo học thuật và Pháp lý
  - Phụ lục E — Hồ sơ phân tích các quyết định mở và Đánh đổi thiết kế (`O-01` đến `O-08`)

---

# PHẦN 0 — ĐỀ TÀI, MỤC TIÊU NGHIÊN CỨU VÀ PHÂN LOẠI PHẠM VI

# 0.1. ĐỀ TÀI VÀ ĐÓNG GÓP NGHIÊN CỨU – KỸ THUẬT

## Tên đề tài

**Phương án chính (Đầy đủ phạm vi sản phẩm và công nghệ):**

> **Xây dựng nền tảng đặt xe thông minh đa dịch vụ (xe máy, taxi bao xe và taxi ghép nội đô – liên tỉnh) với định giá ghép công bằng, gợi ý chuyến bằng AI và ký quỹ Blockchain**

**Phương án ngắn gọn:**

> **Nền tảng đặt xe và ghép xe nội đô – liên tỉnh ứng dụng AI gợi ý chuyến và Blockchain ký quỹ**

**Phương án nhấn mạnh trọng tâm nghiên cứu khoa học (Khuyến nghị học thuật `[NEEDS_EXTERNAL_CONFIRMATION]`):**

> **Định giá ghép xe công bằng và gợi ý chuyến đa phương tiện bằng Learning-to-Rank cho nền tảng đặt xe nội đô – liên tỉnh tích hợp ký quỹ Blockchain**

*Ghi chú:* Cả ba phương án đều giữ đầy đủ hai trụ cột công nghệ **AI** và **Blockchain** theo yêu cầu định hướng ban đầu. Việc chốt tên chính thức trong quyết định giao đề tài thuộc thẩm quyền xác nhận của giảng viên hướng dẫn (xem Phụ lục E, mục `O-07`).

## Đóng góp dự kiến của đề tài và Ma trận ánh xạ kiểm chứng

Để đảm bảo tính trung thực học thuật, tài liệu này phân biệt rõ giữa **Đóng góp thiết kế cơ chế & kỹ thuật hệ thống** (được chứng minh bằng tính chất toán học và kiểm thử bất biến) và **Đóng góp thực nghiệm AI & vận trù học** (là các giả thuyết khoa học sẽ được kiểm định bằng dữ liệu khảo sát và mô phỏng, không tuyên bố là kết quả đã được chứng minh khi chưa chạy thí nghiệm):

1. **Mô hình định giá taxi ghép nội đô công bằng có chặn hai đầu (Đóng góp cốt lõi #1 — MUST):**
   - Mỗi hành khách trả một mức giá riêng dựa trên giá xe đơn tham chiếu của chính họ, số ghế chiếm dụng và mức độ bất tiện thực tế (tỉ lệ đi vòng và đi bộ).
   - Mức giá luôn nằm trong khoảng an toàn có nghiệm `[Floor_i, Cap_i]`: luôn rẻ hơn đi xe riêng ít nhất mức cam kết `d_min` (20%) và không bao giờ vượt quá mức giảm tối đa `d_max` (60%) hay âm tiền trong mọi kịch bản ghép từ 2 đến 4 khách.
   - Bảo toàn tổng chi phí kế hoạch (`PlanFare`), bảo vệ giá đã khóa tại `pool_lock_point` và được kiểm định cảm nhận công bằng qua khảo sát người dùng (Giả thuyết **H4**).
2. **Mô hình chia sẻ rủi ro ba bên khi không ghép được và Quỹ bảo đảm ghép (Đóng góp cốt lõi #2 — MUST):**
   - Thay thế cơ chế phạt cố định bằng việc chia sẻ khoảng chênh `Gap_i` giữa hành khách (`α = 0.50`) và nền tảng/Quỹ bảo đảm (trích 3% từ các chuyến ghép thành công), giữ cho tài xế nhận đúng bằng thu nhập chạy xe đơn khi không tìm được khách ghép do yếu tố thị trường.
   - Thiết lập cơ chế tương thích khuyến khích (Incentive Compatibility): phạt mất bảo đảm đối với tài xế từ chối khách ghép hợp lệ, từ đó triệt tiêu động cơ phá ghép mà không cần ép buộc bằng hạn ngạch cứng (kiểm định qua các cổng bất biến Mục 71 và Giả thuyết **H3, H6, H8**).
3. **Mô hình định giá ghế liên tỉnh suy ngược từ ngưỡng khởi hành và Quy trình chốt chuyến tại `T−72h` (Đóng góp cốt lõi #3 — MUST / Mở rộng SHOULD):**
   - Giá ghế tham chiếu (`SeatReference`) được suy ra trực tiếp từ thu nhập bao xe của tài xế chia cho ngưỡng ghế khởi hành (`min_seats_to_run = 3`), giúp tài xế đạt ~100% thu nhập bao xe ngay tại ngưỡng và có lãi ròng ở ghế thứ 4, trong khi hành khách đi lẻ tiết kiệm ~68% chi phí.
   - Vòng đời đặt chỗ trước 3–7 ngày kết hợp tác vụ chốt chuyến tự động tại `T−72h` (MUST) và chuỗi cứu chuyến gồm Gộp chuyến + Góp thêm tự nguyện (SHOULD — kiểm định qua Giả thuyết **H10**).
4. **Hệ thống gợi ý chuyến đa phương tiện bằng Learning-to-Rank kết hợp xác suất ghép và hoàn thành (Đóng góp cốt lõi #4 — MUST / Mở rộng SHOULD):**
   - Xếp hạng chung các ứng viên của cả ba dịch vụ nội đô (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`) trong cùng một danh sách Top-K, học sự đánh đổi phi tuyến theo ngữ cảnh (thời tiết mưa, quãng đường, độ gấp, ngân sách).
   - Tích hợp xác suất ghép thành công `P(match)` (đã hiệu chỉnh xác suất) để tính giá kỳ vọng `ExpectedPrice` (MUST — kiểm định qua **H1, H2, H3, H9**) và mở rộng kết hợp xác suất hoàn thành chuyến `P(fulfill)` theo cây sự kiện tuần tự (SHOULD — kiểm định qua **H5**).
5. **Kiến trúc ký quỹ Blockchain bất đồng bộ gắn với vòng đời giá biến thiên của 5 dịch vụ (Đóng góp cốt lõi #5 — MUST):**
   - Thiết kế luồng ký quỹ theo mức trần nghĩa vụ tài chính (`quoted_price_cap`), tự động hoàn phần chênh lệch khi khóa giá (`PRICE_LOCKED`), hỗ trợ nạp thêm khi góp thêm liên tỉnh (`topUp`), và giải ngân tự động ba bên (tài xế, nền tảng, Quỹ bảo đảm nội bộ trên hợp đồng) theo đơn vị nguyên `1 VND`, đảm bảo `0` sai lệch số học giữa CSDL và chuỗi khối.

---

# 0.2. PHÂN LOẠI PHẠM VI (MoSCoW) VÀ TỶ TRỌNG CÔNG SỨC

```text
MUST   : Bắt buộc phải hoàn thành để bảo vệ đồ án, chứng minh đóng góp cốt lõi và demo end-to-end.
SHOULD : Tăng chiều sâu nghiên cứu và hoàn thiện sản phẩm rõ rệt; chỉ cắt giảm theo thứ tự Mục 79 nếu thiếu thời gian.
COULD  : Điểm cộng mở rộng và hướng nghiên cứu nâng cao.
WON'T  : Nằm ngoài phạm vi của đồ án này.
```

## Hạng mục MUST (Bắt buộc)

| ID | Hạng mục | Tiêu chí hoàn thành & Kiểm chứng |
|---|---|---|
| **M1** | Trip Intent đa dịch vụ + Tự động phân loại `URBAN`/`INTERCITY` (có vùng đệm) + Luật thời gian đặt (Mục 2.2, 2.3, 6) | Tạo được yêu cầu; phân loại đúng nội đô/liên tỉnh (kể cả chuyến ngắn cắt ranh giới); từ chối đúng các yêu cầu ngoài vùng phục vụ hoặc vi phạm thời gian đặt. |
| **M2** | Routing OSRM local 2 profile (`car` + `motorbike`) cho Hà Nội và các tỉnh lân cận (Mục 34) | Trả về quãng đường, thời gian và ma trận khoảng cách/thời gian chính xác theo từng loại phương tiện. |
| **M3** | Sinh ứng viên + Kiểm tra 11 ràng buộc cứng cho cả hai loại xe (Mục 7, 35) | `0` vi phạm: khung giờ, sức chứa theo từng đoạn (xe máy = 1, taxi = 4), tỉ lệ đi vòng, thời gian ngồi trên xe, trần ngân sách `B_max`. |
| **M4** | Taxi ghép nội đô: Chèn điểm đón/trả động có giới hạn, kể cả khi xe đang chạy (Mục 36) | Chỉ chèn vào sau vị trí hiện tại của xe; kiểm tra lại ràng buộc cứng và điều kiện bảo vệ giá cho toàn bộ hành khách đang có trong kế hoạch. |
| **M5** | Định giá 5 dịch vụ + Phân bổ giá ghép có chặn hai đầu `[Floor_i, Cap_i]` + Sổ cái Quỹ bảo đảm + Khung phí hủy cơ bản (Mục 10–19, 25–29) | Vượt qua toàn bộ 18 cổng đúng đắn `= 0` và bộ kiểm thử bất biến tại PHẦN IX; khớp tuyệt đối giữa `PlanFare`, tiền thu, hoa hồng và sổ cái Quỹ. |
| **M6** | Booking an toàn đồng thời + Máy trạng thái trực giao (`ride_status`, `price_status`) + Chuỗi Offer với `Per-Offer Seat Hold` + Bảng job định thời (Mục 9, 41, 42, 55) | Kiểm soát phiên bản `plan_version` + khóa dòng `FOR UPDATE` + `Idempotency-Key`; đạt `0 oversell` và không rớt ghế trong chuỗi 3 lần offer. |
| **M7** | Taxi ghép liên tỉnh (Lõi): Tài xế đăng chuyến, khách đặt ghế (`T−7 ngày` → `T−72h`), job chốt chuyến tại `T−72h`, chốt thứ tự đón tại `T−24h`, hủy + hoàn tiền 100% khi thiếu khách (Mục 26–29, 31) | Toàn bộ vòng đời chuyển trạng thái tự động chính xác thông qua bảng `scheduled_jobs`. |
| **M8** | Taxi bao xe liên tỉnh: Đặt đi ngay trong ngày hoặc hẹn trước tối đa 7 ngày (Mục 25) | Đón trong 15–45 phút đối với đặt ngay; hỗ trợ khách chuyển sang bao xe khi chuyến ghép liên tỉnh bị hủy tại `T−72h`. |
| **M9** | Gợi ý Baseline có giải thích và Top-K đa phương tiện (Mục 10.5, 40) | Trộn ứng viên xe máy, taxi bao xe và taxi ghép nội đô; bảo đảm có ít nhất 1 ứng viên mỗi dịch vụ hợp lệ; gắn nhãn giải thích Rẻ nhất / Nhanh nhất / Đề xuất / Thoải mái nhất. |
| **M10** | Simulator 5 dịch vụ tái lập được và chống rò rỉ biến ẩn (Mục 48) | Cùng `seed` sinh ra đúng cùng bộ dữ liệu; hành khách có hàm tiện ích ẩn dị biệt, phi tuyến và phụ thuộc ngữ cảnh (mưa, độ gấp). |
| **M11** | AI cốt lõi: Mô hình xếp hạng `LGBMRanker` (LTR) + Mô hình `P(match)` hiệu chỉnh (Mục 44, 45, 47) | Huấn luyện Out-of-Fold không rò rỉ; kiểm định thống kê đầy đủ cho các giả thuyết **H1, H2, H3 và H9** (báo cáo tách phân khúc nội đô 1 khách đa phương tiện). |
| **M12** | Blockchain Escrow trên testnet theo đơn vị nguyên `1 VND` gắn với vòng đời giá của 5 dịch vụ (Mục 80) | Ký quỹ mức trần `quoted_price_cap` → hoàn chênh lệch tại `PRICE_LOCKED` → cổng kiểm tra trước `RIDE_STARTED` → giải ngân 3 bên / hoàn tiền khớp 100% với `final_price`. |
| **M13** | Giao diện Web tối thiểu (Unified Demo Workbench) cho Khách, Tài xế và Admin (Mục 62) | Demo liền mạch end-to-end cả 5 dịch vụ và hiển thị bảng đối soát giá/quỹ/ký quỹ theo kịch bản nghiệm thu Mục 78. |
| **M14** | Bộ kiểm thử nghiệm thu toàn diện (Mục 70–73) | Toàn bộ 18 cổng đúng đắn `"= 0"` ở PHẦN IX đạt tuyệt đối. |

## Hạng mục SHOULD (Khuyến nghị thực hiện)

| ID | Hạng mục | Vai trò trong nghiên cứu & sản phẩm |
|---|---|---|
| **S1** | Khảo sát lựa chọn rời rạc 100–200 người có phân tầng mẫu (Mục 65) | Dùng cho 3 mục đích: hiệu chỉnh phân phối tham số ẩn của Simulator, làm tập kiểm thử người thật (qua 5-fold GroupKFold CV), và kiểm định cảm nhận công bằng của công thức chia giá (**H4**). |
| **S2** | Mô hình xác suất hoàn thành chuyến `P(fulfill)` theo cây sự kiện tuần tự + Xếp hạng có tính khả năng hoàn thành (Mục 39, 46) | Kiểm định giả thuyết **H5** trên Simulator đóng vòng (Closed-loop). |
| **S3** | Hiệu chỉnh xác suất điểm LTR bằng Temperature Scaling (NLL, Brier, ECE — Mục 47) | Điều kiện tiên quyết để nhân trực tiếp `p_hat_i × p_fulfill_i` trong công thức xếp hạng cuối. |
| **S4** | **Ghép theo lô (Batch Matching)** mỗi `Δ = 30 giây` dùng CP-SAT trên đồ thị RTV rút gọn cho taxi ghép nội đô (Mục 37) | So sánh hiệu quả toàn cục (tỉ lệ ghép thực tế, tổng km xe, số dư Quỹ bảo đảm) với thuật toán chèn tham lam trực tuyến (kiểm định **H6**). |
| **S5** | **Gộp chuyến ghép liên tỉnh (`MERGED`) và Đề nghị góp thêm tự nguyện (`CONFIRMED_TOPUP`)** tại `T−72h` (Mục 29, 30) | Giảm tỉ lệ hủy chuyến ghép liên tỉnh do thiếu khách và tích hợp hàm `topUp` trên Smart Contract (kiểm định **H10**). |
| **S6** | Chính sách phí hủy theo nấc thời gian và xử lý khách không đến (`NO_SHOW`) đầy đủ cho nội đô và liên tỉnh (Mục 18.7) | Mở rộng từ khung phí hủy cơ bản ở M5 để bao phủ các kịch bản hủy muộn phức tạp và đền bù chéo giữa các bên. |
| **S7** | Quy trình duyệt KYC dạng mock (`NONE / PENDING / VERIFIED / REJECTED` — Mục 81) | Điều kiện bắt buộc để tài xế được bật nhận taxi ghép nội đô, chạy bao xe liên tỉnh và đăng chuyến ghép liên tỉnh. |
| **S8** | Phân hệ Dashboard Admin chuyên sâu (Mục 62, 63) | Giám sát biểu đồ thu/chi Quỹ bảo đảm (`p_actual` vs `p*`), chất lượng hiệu chỉnh mô hình AI, các lượt chạy ghép theo lô và trạng thái chuyến liên tỉnh. |
| **S9** | Tính năng an toàn khi đi ghép (Mục 60) | Chia sẻ hành trình trực tiếp qua liên kết, nút cảnh báo SOS giả lập, và tùy chọn ràng buộc chỉ ghép cùng giới (`same_gender_coride`). |

## Hạng mục COULD (Mở rộng tùy chọn)

| ID | Hạng mục |
|---|---|
| **C1** | Chatbot LLM chuyển đổi câu nói tự nhiên tiếng Việt thành cấu trúc JSON Trip Intent (Mục 50). |
| **C2** | Dự báo nhu cầu taxi ghép nội đô theo `(zone × 15 phút)` và hiển thị bản đồ nhiệt gợi ý di chuyển cho tài xế (Mục 51). |
| **C3** | Định giá taxi ghép động theo `P(match)`: tự động điều chỉnh `d_min` và `α` theo mật độ khu vực/khung giờ (Mục 19.3). |
| **C4** | Chuyến quen (`Recurring Trips`): mẫu lịch đi cố định hằng ngày tự động sinh yêu cầu `SCHEDULED` ở mốc `T−12h` (Mục 24). |
| **C5** | Khử thiên lệch vị trí hiển thị (Inverse Propensity Scoring) và cơ chế khám phá có kiểm soát cho tài xế mới (Mục 49). |
| **C6** | Thí nghiệm đối chứng chính sách hạn ngạch cứng `Quota 4:1` so với cơ chế động cơ kinh tế tự nguyện (kiểm định **H8**). |
| **C7** | Cho phép người dùng tự liên kết ví cá nhân MetaMask trên trình duyệt (`bindWallet`) và luồng phân xử tranh chấp on-chain (`raiseDispute` / `resolveDispute`). |
| **C8** | Kiểm thử tải (Load testing) quy mô lớn lên tới 5.000 tài xế hoạt động đồng thời. |
| **C9** | **Điểm đón gặp nhau (`Meeting Points`)** trên đường trục chính cho taxi ghép nội đô kèm bù đắp quãng đi bộ trong công thức giá (Mục 23 — kiểm định **H7**). |
| **C10** | Mô hình dự báo xác suất chuyến ghép liên tỉnh đạt ngưỡng tại `T−72h` (**`P(fill)`** — kiểm định **H11**), kèm tính năng Danh sách chờ (`Waitlist`) gom nhu cầu cho tài xế (Mục 33, 52). |
| **C11** | Cơ chế gợi ý ghép chiều về (Backhaul Matching) cho tài xế chạy liên tỉnh (Mục 33). |

## Hạng mục WON'T (Không thực hiện trong đồ án này)

```text
- Xe máy đi ghép (2 khách trên 1 xe máy) hoặc xe máy chạy liên tỉnh
- Phương tiện xe 7 chỗ, xe limousine 16 chỗ hoặc xe khách tuyến cố định
- Tích hợp cổng thanh toán ngân hàng/ví điện tử bằng tiền thật
- Tích hợp dịch vụ eKYC xác thực căn cước công dân thật với nhà cung cấp bên thứ ba
- Triển khai kiến trúc Microservices phân tán hoặc vận hành trên cụm Kubernetes
- Xây dựng ứng dụng di động gốc (Native iOS/Android) — sử dụng Web App đáp ứng (Responsive Next.js)
- Vận hành thương mại ngoài đời thực với tài xế và hành khách thật
- Định giá nhân hệ số giờ cao điểm (Surge Pricing) cho các dịch vụ xe đơn
```

## Tỷ trọng phân bổ công sức dự kiến

```text
Core nội đô (Trip Intent, OSRM, xe máy, bao xe, ghép động, định giá, Quỹ) : ~28%
Core liên tỉnh (bao xe đi ngay/hẹn trước, đăng chuyến ghép, chốt T−72h)   : ~14%
AI & Nghiên cứu (Simulator, Khảo sát S1, LTR, P(match), P(fulfill))       : ~28%
Mở rộng thuật toán tối ưu (Ghép theo lô S4, Gộp chuyến & Góp thêm S5)     : ~8%
Blockchain Escrow (Tích hợp hợp đồng thông minh, adapter, đối soát)       : ~8%
Kiểm thử bất biến, Đánh giá thống kê & Viết báo cáo khoa học              : ~14%
```

---

# PHẦN I — TỔNG QUAN BÀI TOÁN, ĐỐI TƯỢNG SỬ DỤNG VÀ MA TRẬN NĂM DỊCH VỤ

# 1. PHÂN TÍCH BÀI TOÁN THỰC TẾ VÀ NHU CẦU NGƯỜI DÙNG

Người dân di chuyển tại khu vực đô thị lớn như Hà Nội và các tỉnh vệ tinh lân cận (Hưng Yên, Bắc Ninh, Hải Dương, Hà Nam, Vĩnh Phúc, Hòa Bình) có ba nhóm nhu cầu tách biệt rõ rệt về mặt kinh tế và vận hành:

1. **Di chuyển nội đô cá nhân, cần nhanh, linh hoạt và chi phí thấp:**
   - Với hành khách đi một mình, không mang hành lý cồng kềnh và trong điều kiện thời tiết thuận lợi, **xe máy (`BIKE_URBAN`)** là phương thức chiếm ưu thế tuyệt đối nhờ khả năng luồn lách trong giờ cao điểm và mức giá chỉ bằng ~40% taxi.
2. **Di chuyển nội đô quãng trung bình – dài từ các khu đô thị vệ tinh vào trung tâm:**
   - Hàng chục nghìn sinh viên và người đi làm di chuyển hằng ngày dọc các hành lang hướng tâm (ví dụ: từ Yên Nghĩa, Hà Đông, Dương Nội, Hoài Đức đi vào Thanh Xuân, Đống Đa, Cầu Giấy, Ba Đình) với cự ly 10–18 km.
   - Khi trời mưa, nắng gắt, mang theo đồ đạc hoặc đi 2 người, xe máy không còn phù hợp, nhưng chi phí gọi **taxi bao xe (`CAR_URBAN_PRIVATE`)** từ 150.000 – 220.000 đ/lượt là rào cản kinh tế lớn.
   - Các dịch vụ đi chung xe hiện hữu thường thất bại trong việc thuyết phục người dùng và tài xế vì ba nguyên nhân:
     - **Hộp đen định giá:** Hành khách không hiểu vì sao mình phải trả mức giá đó, và người chịu thiệt thòi ngồi đi vòng lâu hơn lại không được bù đắp thỏa đáng so với người đi thẳng.
     - **Rủi ro khi không tìm được người ghép:** Hoặc hành khách bị thu phụ phí nặng một cách bất ngờ, hoặc tài xế bị ép chạy chuyến ghép chỉ có 1 khách với mức cước thấp hơn chạy đơn, dẫn tới hành vi tài xế tìm cách hủy chuyến hoặc từ chối nhận khách thứ hai.
     - **Thiếu gợi ý đặt trong ngữ cảnh đa phương thức:** Các ứng dụng hiện tại bắt người dùng phải chọn trước loại xe rồi mới báo giá, thay vì xếp hạng thông minh giữa xe máy, taxi ghép và taxi bao xe theo đúng ngữ cảnh thời tiết, độ gấp và xác suất ghép thành công tại thời điểm đó.
3. **Di chuyển liên tỉnh cự ly ngắn và trung bình (30–120 km):**
   - **Nhóm cần đi gấp trong ngày (`CAR_INTERCITY_PRIVATE`):** Cần xe đón ngay trong vòng 15–45 phút để đi công tác, khám chữa bệnh hoặc về quê đột xuất, chấp nhận trả giá bao xe cố định.
   - **Nhóm có kế hoạch trước muốn tiết kiệm chi phí (`CAR_INTERCITY_POOL`):** Hiện nay phần lớn hành khách đặt "xe ghép / xe tiện chuyến" liên tỉnh thông qua các hội nhóm mạng xã hội hoặc tổng đài thủ công. Cách làm này tiềm ẩn nhiều rủi ro: giá cả thỏa thuận tùy tiện, tài xế tự ý nhồi nhét khách, gom khách lòng vòng quá lâu, hoặc hủy kèo sát giờ đi khi không gom đủ người khiến hành khách trở tay không kịp.

Nền tảng được thiết kế để giải quyết đồng thời cả ba nhóm nhu cầu trên một **lõi kỹ thuật thống nhất** (Trip Intent, OSRM Routing, Hard Constraints Engine, AI Recommendation, Concurrency Booking và Blockchain Escrow), trong đó mỗi dịch vụ được điều chỉnh bằng bộ quy tắc nghiệp vụ và công thức định giá chuyên biệt.

---

# 2. MA TRẬN NĂM DỊCH VỤ VÀ QUY TẮC PHÂN LOẠI KHÔNG GIAN – THỜI GIAN

## 2.1. Ma trận năm dịch vụ

| Mã dịch vụ (`service_code`) | Tên dịch vụ | Loại phương tiện | Phạm vi không gian | Cơ chế ghép khách | Số khách / ghế mỗi booking |
|---|---|---|---|---|---|
| `BIKE_URBAN` | Xe máy nội đô | Xe máy (`BIKE`) | Nội đô (`URBAN`) | Không ghép (chạy 1:1) | Đúng `1` khách (không hành lý lớn) |
| `CAR_URBAN_PRIVATE` | Taxi bao xe nội đô | Taxi 4 chỗ (`CAR4`) | Nội đô (`URBAN`) | Không ghép (thuê nguyên chuyến) | `1–4` khách |
| `CAR_URBAN_POOL` | Taxi ghép nội đô | Taxi 4 chỗ (`CAR4`) | Nội đô (`URBAN`) | Ghép động theo thời gian thực (kể cả khi xe đang chạy) | `1–2` ghế (`max_party_seats_pool = 2`) |
| `CAR_INTERCITY_PRIVATE` | Taxi bao xe liên tỉnh | Taxi 4 chỗ (`CAR4`) | Liên tỉnh (`INTERCITY`) | Không ghép (thuê nguyên chuyến) | `1–4` khách |
| `CAR_INTERCITY_POOL` | Taxi ghép liên tỉnh | Taxi 4 chỗ (`CAR4`) | Liên tỉnh (`INTERCITY`) | Ghép theo ghế trên chuyến tài xế đã đăng trước | `1–4` ghế |

*Quy ước sức chứa:* "Taxi 4 chỗ" (`CAR4`) trong toàn bộ tài liệu có nghĩa là **4 ghế dành cho hành khách** (không tính ghế tài xế), được biểu diễn bởi tham số cấu hình `vehicle.capacity = 4`.

## 2.2. Luật thời gian đặt theo từng dịch vụ

| Dịch vụ | Đặt sớm nhất (`max_lead_time`) | Đặt muộn nhất (`min_lead_time`) | Cửa sổ đón khi đặt đi ngay (`NOW`) |
|---|---|---|---|
| `BIKE_URBAN` | Trước `12 giờ` | Đặt đi ngay (`0 phút`) | Đón trong `3–15 phút` |
| `CAR_URBAN_PRIVATE` | Trước `12 giờ` | Đặt đi ngay (`0 phút`) | Đón trong `5–20 phút` |
| `CAR_URBAN_POOL` | Trước `12 giờ` | Đặt đi ngay (`0 phút`) | Đón trong `5–20 phút` |
| `CAR_INTERCITY_PRIVATE` | Trước `7 ngày` (`168 giờ`) | **Đặt ngay trong ngày, đi luôn** | Đón trong `15–45 phút` |
| `CAR_INTERCITY_POOL` | **Trước `7 ngày` (`168 giờ`)** | **Trước `3 ngày` (`T−72 giờ`)** | Không hỗ trợ đặt đi ngay |

- **Lý do giữ `max_ahead_days = 7` cho Taxi bao xe liên tỉnh (`[ACCEPTED]` — D-36):** Việc cho phép đặt `CAR_INTERCITY_PRIVATE` cả ở chế độ đi ngay lẫn hẹn trước tối đa 7 ngày tạo ra sự tương thích hoàn hảo với quy trình chốt chuyến ghép liên tỉnh tại mốc `T−72h`. Khi một chuyến `CAR_INTERCITY_POOL` bị hủy ở mốc `T−72h` (tức còn đúng 3 ngày trước giờ khởi hành) do thiếu khách, hành khách có thể chuyển đổi ngay lập tức sang đặt `CAR_INTERCITY_PRIVATE` cho đúng khung giờ khởi hành cách đó 3 ngày mà không bị hệ thống chặn bởi giới hạn thời gian.
- **Lý do đóng đặt chỗ chuẩn của `CAR_INTERCITY_POOL` tại `T−72h` (`[ACCEPTED]` — D-37) và tùy chọn đặt ghế vét (`[ACCEPTED: mặc định tắt false]` — O-08):** Đóng nhận khách mới và chốt trạng thái chuyến tại `T−72h` giúp cả tài xế và hành khách biết chắc chắn kết quả trước 3 ngày. Nếu chuyến bị hủy, khách vẫn còn đủ 3 ngày để xoay xở phương án khác. *(Lưu ý mở rộng tại Phụ lục E, mục O-08: đối với những chuyến đã đạt ngưỡng `CONFIRMED` tại `T−72h` nhưng vẫn còn trống 1 ghế, hệ thống có thể cấu hình cờ `allow_post_confirm_late_booking` để cho phép đặt ghế vét không hoàn hủy từ `T−72h` đến `T−24h`).*

## 2.3. Quy tắc tự động xác định Nội đô (`URBAN`) và Liên tỉnh (`INTERCITY`) kèm xử lý biên không gian (`[ACCEPTED]` — D-20, D-50)

Người dùng không phải tự phân biệt chuyến đi của mình là nội đô hay liên tỉnh. Hệ thống sử dụng các đa giác địa lý trong PostGIS (`service_areas`) kết hợp khoảng cách để tự động phân loại và xử lý triệt để các trường hợp biên:

1. **Định nghĩa các vùng địa lý:**
   - `total_service_area`: Đa giác bao phủ toàn bộ vùng phục vụ của nền tảng (Thành phố Hà Nội và các tỉnh lân cận trong bán kính đường bộ tối đa `150 km`).
   - `urban_service_area`: Đa giác vùng phục vụ nội đô Hà Nội (bao gồm các quận nội thành và các khu đô thị vệ tinh liền kề như Hà Đông, Yên Nghĩa, Dương Nội, An Khánh, Mỹ Đình, Gia Lâm, Đông Anh).
2. **Thuật toán phân loại không gian 3 bước:**
   ```text
   Bước 1 (Kiểm tra phạm vi toàn hệ thống):
       Nếu pickup ∉ total_service_area HOẶC dropoff ∉ total_service_area:
           → Từ chối yêu cầu với mã lỗi OUT_OF_SERVICE_AREA.

   Bước 2 (Kiểm tra nội đô và vùng đệm giáp ranh — chống lỗi chuyến ngắn cắt biên):
       Nếu (pickup ∈ urban_service_area VÀ dropoff ∈ urban_service_area):
           → mode = URBAN
       Ngược lại, nếu ((pickup ∈ urban_service_area HOẶC dropoff ∈ urban_service_area)
                      VÀ direct_distance_km(pickup, dropoff) <= urban_boundary_buffer_km):
           → mode = URBAN   (với urban_boundary_buffer_km = 15.0 km)

   Bước 3 (Kiểm tra liên tỉnh hợp lệ):
       Nếu (pickup ∈ urban_service_area HOẶC dropoff ∈ urban_service_area)
           VÀ direct_distance_km(pickup, dropoff) > urban_boundary_buffer_km:
           → mode = INTERCITY
       Ngược lại (cả hai điểm đều nằm ngoài urban_service_area, ví dụ đi nội tỉnh Hưng Yên):
           → Từ chối với mã lỗi UNSUPPORTED_INTER_PROVINCE_ROUTE
             (Đồ án chỉ phục vụ các tuyến liên tỉnh có 1 đầu gắn với vùng Hà Nội).
   ```
- **Ý nghĩa của quy tắc vùng đệm (`urban_boundary_buffer_km = 15.0 km`):** Trong Revision 8, nếu khách đi từ Đại học Phenikaa (Hà Đông — trong vùng nội đô) sang La Phù / An Khánh (Hoài Đức — nếu nằm ngay sát ngoài ranh giới đa giác nội đô) với quãng đường chỉ `5,0 km`, công thức cứng nhắc sẽ biến chuyến 5 km này thành `INTERCITY` (cấm xe máy, cấm taxi ghép nội đô và áp giá mở cửa liên tỉnh 150.000 đ). Quy tắc Bước 2 đảm bảo mọi chuyến đi ngắn `<= 15 km` kết nối vùng ven đô với nội thành đều được phục vụ mượt mà bằng các dịch vụ `URBAN` (đúng như chính ví dụ chuẩn Phenikaa – La Phù ở Mục 16).

## 2.4. Cơ chế tìm xe và điều phối theo từng dịch vụ

| Dịch vụ | Cơ chế tìm phương tiện / kế hoạch | Có bước gửi Offer cho tài xế? | Thời gian chờ Offer |
|---|---|---|---|
| `BIKE_URBAN`, `CAR_URBAN_PRIVATE` | Tìm tài xế đúng loại xe đang rảnh và trực tuyến gần điểm đón nhất. | Có | `20 giây` / lần (tối đa 3 lần) |
| `CAR_URBAN_POOL` | Thử chèn vào các kế hoạch taxi ghép đang mở (kể cả xe đang chạy) + tìm tài xế taxi đang rảnh bật chế độ Pool; kết hợp ghép theo lô định kỳ (S4). | Có (đối với tài xế nhận booking khởi tạo kế hoạch; tự động thêm đối với khách ghép sau thuộc ngưỡng đã khai) | `20 giây` / lần (tối đa 3 lần) |
| `CAR_INTERCITY_PRIVATE` | Tìm tài xế taxi đã bật "Nhận liên tỉnh" (bán kính 5 km nếu đi ngay; kiểm tra lịch trống cả chiều đi lẫn chiều về nếu hẹn trước). | Có | `60 giây` / lần (tối đa 3 lần) |
| `CAR_INTERCITY_POOL` | Tìm kiếm trên tập **các chuyến ghép liên tỉnh (`scheduled_trips`) do tài xế đã đăng lịch trước**. | **Không:** Tài xế chủ động đăng chuyến kèm vùng đón/trả đồng nghĩa với việc cam kết nhận mọi khách đặt ghế hợp lệ. | Không áp dụng (`0 giây`) |

---

# 3. CÁC VAI TRÒ VÀ QUYỀN HẠN TRONG HỆ THỐNG

1. **Hành khách (`PASSENGER`):**
   - Tạo `Trip Intent`, tùy chọn loại phương tiện (`BIKE | CAR | ANY`) và hình thức đi (`PRIVATE | POOL | ANY`).
   - Xem danh sách gợi ý `Top-K` đa phương tiện kèm giải thích minh bạch (đối với `CAR_URBAN_POOL` hiển thị rõ giá ghép dự kiến, trần giá nếu ghép được `Quote_i`, và trần giá tối đa nếu không ghép được `Unmatched_i`).
   - Thực hiện đặt chuyến, ký quỹ, theo dõi vị trí và trạng thái ghép theo thời gian thực, trả lời đề nghị góp thêm (với chuyến liên tỉnh thiếu khách), chia sẻ hành trình, kích hoạt SOS, hủy chuyến theo chính sách và đánh giá tài xế sau chuyến đi.
2. **Tài xế xe máy (`DRIVER` — `vehicle_type = BIKE`):**
   - Bật/tắt trạng thái sẵn sàng nhận chuyến nội đô, cập nhật vị trí định kỳ.
   - Nhận hoặc từ chối offer trong vòng 20 giây, thực hiện đón khách, bắt đầu chuyến và hoàn thành chuyến.
3. **Tài xế taxi (`DRIVER` — `vehicle_type = CAR4`):**
   - Bật/tắt độc lập 3 chế độ: nhận chuyến nội đô (`accepts_urban`), nhận ghép khách nội đô (`pool_enabled`), và nhận chuyến liên tỉnh (`accepts_intercity` — yêu cầu `kyc_status = VERIFIED`).
   - Khai báo ngưỡng chấp nhận đi vòng tối đa của tài xế (`max_driver_detour_km`, `max_driver_detour_min`) và số điểm đón phát sinh tối đa (`max_additional_pickups`).
   - Đăng lịch chuyến ghép liên tỉnh (`scheduled_trip`), theo dõi số ghế đã đặt, và đưa ra quyết định chạy dưới ngưỡng hoặc hủy chuyến trước mốc `T−60h` nếu chuyến thiếu khách.
   - Xem bảng kê thu nhập chi tiết tách bạch giữa doanh thu cước chuyến, khoản bù từ Quỹ bảo đảm ghép, và phí hoa hồng nền tảng.
4. **Quản trị viên (`ADMIN`):**
   - Quản lý hồ sơ người dùng, phương tiện và phê duyệt trạng thái KYC (`VERIFIED / REJECTED`).
   - Giám sát toàn bộ các chỉ số vận hành theo thời gian thực: tỉ lệ ghép thành công `p_actual` so với điểm hòa vốn `p*`, sổ cái Quỹ bảo đảm (`fund_ledger`), hiệu năng mô hình AI (`LTR`, `P(match)`, `P(fulfill)`), các lượt giải bài toán ghép theo lô, trạng thái chốt chuyến liên tỉnh, và phân xử các giao dịch ký quỹ tranh chấp (`DISPUTED`).

---

# 4. LUỒNG NGHIỆP VỤ TỔNG QUÁT THEO TỪNG NHÓM DỊCH VỤ

## 4.1. Luồng đặt xe Nội đô (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`)

```text
[1] Hành khách gửi Trip Intent
    ↓
[2] Hệ thống xác định mode = URBAN và lọc tập dịch vụ hợp lệ (Mục 6)
    ↓
[3] Sinh ứng viên song song cho các dịch vụ được phép (Mục 35):
    - BIKE_URBAN        : lọc tài xế xe máy rảnh trong bán kính R (chỉ khi 1 khách, không hành lý lớn)
    - CAR_URBAN_PRIVATE : lọc tài xế taxi rảnh trong bán kính R
    - CAR_URBAN_POOL    : thử chèn điểm đón/trả vào các kế hoạch Pool đang mở (kể cả xe đang chạy)
                          + khởi tạo kế hoạch Pool mới từ các tài xế taxi đang rảnh bật Pool
    ↓
[4] Kiểm tra 11 Ràng buộc cứng (Mục 7) + Điều kiện Shareability & Sinh lời tài xế (Mục 14)
    (Với CAR_URBAN_POOL: kiểm tra lại cho MỌI hành khách đang có trong kế hoạch)
    ↓
[5] Tính giá (Mục 10–18) + Dự báo xác suất P(match) (Mục 45) và P(fulfill) (Mục 39)
    ↓
[6] Xếp hạng Top-K đa phương tiện bằng Baseline hoặc LTR (Mục 40, 44)
    (Đảm bảo giữ ít nhất 1 ứng viên đại diện cho mỗi dịch vụ hợp lệ có xe)
    ↓
[7] Khách chọn ứng viên → Kiểm tra plan_version → Tạo Per-Offer Seat Hold (TTL 35s)
    → Gửi Offer cho tài xế (20s), chuyển tiếp tối đa 3 lần cùng dịch vụ nếu bị từ chối (Mục 41)
    ↓
[8] Tài xế nhận (hoặc tự động ghép vào kế hoạch đang chạy thỏa ngưỡng tài xế đã khai):
    → Booking chuyển sang ride_status = CONFIRMED
    → Kích hoạt ký quỹ mức trần quoted_price_cap lên Blockchain (Mục 80)
    ↓
[9] Đón khách (Kiểm tra cổng escrow_status == DEPOSITED) → ride_status = RIDE_STARTED:
    - Với CAR_URBAN_POOL: tiếp tục mở cửa sổ nhận thêm khách ghép (trực tuyến hoặc theo lô 30s)
      cho đến khi từng hành khách chạm pool_lock_point của riêng mình
    → Tại pool_lock_point: chốt price_status = MATCHED_LOCKED | UNMATCHED_LOCKED,
      khóa final_price và gọi lệnh hoàn phần ký quỹ chênh lệch (cap - final_price)
    ↓
[10] Trả khách → ride_status = COMPLETED → Giải ngân on-chain (Tài xế / Nền tảng / Quỹ bảo đảm)
     → Cập nhật sổ cái fund_ledger và ghi log huấn luyện cho AI
```

## 4.2. Luồng đặt Taxi bao xe liên tỉnh (`CAR_INTERCITY_PRIVATE`)

```text
[1] Hành khách gửi Trip Intent → Hệ thống xác định mode = INTERCITY, chọn bao xe
    ↓
[2] Tìm nguồn cung tài xế taxi có accepts_intercity = true và kyc_status = VERIFIED:
    - Nếu đặt đi ngay (NOW): lọc tài xế đang rảnh trong bán kính R = 5 km quanh điểm đón
    - Nếu hẹn trước (SCHEDULED, tối đa 7 ngày): lọc tài xế có lịch trống toàn bộ khung giờ
      (tính cả thời gian chạy chiều đi + thời gian nghỉ + thời gian quay về dự kiến)
    ↓
[3] Tính giá cố định IntercityPrivateFare (Mục 25.2) → Kiểm tra B_max → Xếp hạng Top-K
    ↓
[4] Khách chọn → Tạo Per-Offer Seat Hold (TTL 75s) → Gửi Offer cho tài xế (chờ tối đa 60 giây,
    cascade tối đa 3 lần cùng dịch vụ)
    ↓
[5] Tài xế nhận → ride_status = CONFIRMED, price_status = FIXED_LOCKED → Ký quỹ 100% giá chuyến
    ↓
[6] Đón khách (cổng escrow_status == DEPOSITED) → RIDE_STARTED → COMPLETED → Giải ngân 85% / 15%
```

## 4.3. Luồng đặt Taxi ghép liên tỉnh (`CAR_INTERCITY_POOL`)

```text
[1] Trước từ 3 đến 7 ngày: Tài xế taxi (VERIFIED) đăng chuyến ghép (scheduled_trip)
    gồm hành lang tuyến, giờ khởi hành, khung lệch ±30 phút, số ghế bán (tối đa 4),
    giá ghế trong khung ±10% SeatReference, vùng đón/trả miễn phí, ngưỡng min_seats_to_run = 3
    ↓
[2] Hành khách tạo Trip Intent (mode = INTERCITY, đặt trước trong khoảng [72 giờ, 7 ngày])
    → Hệ thống tìm các chuyến OPEN_FOR_BOOKING khớp tuyến, khung giờ và còn đủ ghế trống
    → Tính giá cố định lúc đặt (SeatPrice × seat_count + DoorSurcharge) → Hiển thị Top-K
    ↓
[3] Khách chọn chuyến → Khóa dòng scheduled_trip (kiểm tra plan_version) → Giữ ghế & trừ ghế trống
    → Chuyển ngay sang ride_status = CONFIRMED (không cần gửi offer cho tài xế) → Ký quỹ
    ↓
[4] Tại mốc T−72h (Bắt buộc chạy bằng scheduled_job): ĐÓNG ĐẶT CHỖ CHUẨN & KIỂM TRA NGƯỠNG
    ├── Trường hợp A (seats_booked >= min_seats_to_run):
    │     → Chuyến chuyển sang CONFIRMED, khóa trạng thái chạy chắc chắn
    └── Trường hợp B (seats_booked < min_seats_to_run — thiếu khách):
          1. Thử GỘP CHUYẾN tự động với chuyến cùng hành lang lệch <= 60 phút (S5, Mục 30)
          2. Nếu không gộp được: Gửi đề nghị GÓP THÊM tự nguyện cho khách trong 6 giờ (S5, Mục 29)
             - Nếu 100% khách trên chuyến đồng ý và nạp thêm ký quỹ (topUp) → CONFIRMED_TOPUP
          3. Nếu hết hạn góp thêm mà không đủ 100% đồng ý: Tài xế quyết định trước mốc T−60h:
             - Tài xế chọn vẫn chạy dưới ngưỡng → CONFIRMED_UNDER_MIN (khách giữ nguyên giá ghế cũ)
             - Tài xế chọn hủy (hoặc quá hạn T−60h) → CANCELLED_LOW_DEMAND:
               Hoàn trả 100% ký quỹ cho mọi khách, không phạt tài xế, tự động gợi ý khách
               chuyển sang đặt CAR_INTERCITY_PRIVATE cùng giờ hoặc chuyến ghép khác
    ↓
[5] Tại mốc T−24h: Giải bài toán tối ưu hoán vị điểm đón (Mục 31), chốt thứ tự đón (PICKUP_ORDER_FIXED)
    và gửi thông báo giờ đón chính xác cho từng hành khách
    ↓
[6] Tại mốc T: Khởi hành (DEPARTED / RIDE_STARTED) → Hoàn thành (COMPLETED) → Giải ngân on-chain
```

---

# 5. KIẾN TRÚC HỆ THỐNG MỨC CAO (MODULAR MONOLITH)

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ Giao diện Web (Next.js + TypeScript + MapLibre): Khách | Tài xế | Admin   │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │ REST API (Idempotent) + WebSocket
┌─────────────────────────────────────▼─────────────────────────────────────┐
│ Ứng dụng Backend FastAPI — KIẾN TRÚC MODULAR MONOLITH (16 Module)         │
│                                                                           │
│  [identity]      [trip]          [driver]        [routing]                │
│  [candidate]     [pooling]       [batch_matcher] [intercity]              │
│  [pricing]       [fund]          [booking]       [ride]                   │
│  [recommendation][ml_models]     [escrow_adapter][jobs (DB Scheduler)]    │
└─────────┬───────────────────────────┬──────────────────────────┬──────────┘
          │                           │                          │
┌─────────▼──────────┐     ┌──────────▼─────────┐     ┌──────────▼──────────┐
│ PostgreSQL+PostGIS │     │ Redis              │     │ OSRM Local Engine   │
│ (Dữ liệu nghiệp vụ,│     │ (Vị trí tài xế,    │     │ - Profile: car      │
│  sổ cái quỹ, bảng  │     │  cache ma trận,    │     │ - Profile: motorbike│
│  scheduled_jobs)   │     │  rate-limit)       │     │ (Bản đồ OSM VN)     │
└─────────┬──────────┘     └────────────────────┘     └─────────────────────┘
          │
┌─────────▼───────────────────────────┐    ┌────────────────────────────────┐
│ Lưu trữ Offline (Parquet + Artifacts│    │ Mạng Blockchain Testnet (EVM)  │
│ mô hình LTR / P(match) / P(fulfill))│    │ Hợp đồng thông minh Ký quỹ     │
└─────────────────────────────────────┘    └────────────────────────────────┘
```

**Nguyên tắc kiến trúc cốt lõi (`[ACCEPTED]` — D-31):**
- Toàn bộ hệ thống vận hành trong một tiến trình ứng dụng hợp nhất (kèm tiến trình worker đọc bảng `scheduled_jobs`), tuyệt đối không tách Microservices hay dựng Kafka/RabbitMQ để tránh chi phí vận hành phân tán không cần thiết cho phạm vi đồ án.
- Mỗi module chỉ được phép giao tiếp với module khác thông qua lớp dịch vụ (Python Service Interface) đã định nghĩa rõ kiểu dữ liệu đầu vào/đầu ra, và không truy vấn trực tiếp vào bảng CSDL thuộc quyền sở hữu của module khác (xem chi tiết tại Mục 54).

---

# PHẦN II — QUY TẮC NGHIỆP VỤ CHUNG, RÀNG BUỘC CỨNG VÀ VÒNG ĐỜI TRẠNG THÁI

# 6. TRIP INTENT VÀ QUY TẮC SUY DIỄN TẬP DỊCH VỤ HỢP LỆ

Mỗi nhu cầu di chuyển của hành khách được biểu diễn chuẩn hóa thành đối tượng `Trip Intent` $R$:

```text
R = (
    vehicle_preference,           BIKE | CAR | ANY
    ride_preference,              PRIVATE | POOL | ANY
    P_start, P_destination,       Tọa độ (lat, lon) + văn bản địa chỉ → suy ra mode = URBAN | INTERCITY
    passenger_count,              Số lượng hành khách đi cùng trong 1 booking (số ghế yêu cầu)
    T_preferred,                  Thời điểm khởi hành mong muốn
    T_earliest, T_latest,         Khung thời gian đón chấp nhận được [T_earliest, T_latest]
    B_min, B_max,                 Ngân sách ưa thích (mềm) và ngân sách trần tối đa (cứng)
    max_passenger_detour_ratio,   Tỉ lệ quãng đường đi vòng tối đa chấp nhận được (mặc định 0.30)
    max_in_vehicle_time,          Thời gian ngồi trên xe tối đa (tùy chọn; có công thức mặc định)
    latest_arrival,               Thời điểm đến đích muộn nhất (tùy chọn)
    max_walk_m,                   Quãng đi bộ tối đa ra điểm đón gặp nhau (C9; mặc định 0 = đón tận nơi)
    has_luggage,                  Có mang hành lý lớn/cồng kềnh hay không (true/false)
    numeric_preferences,          Vector trọng số tự khai (nếu có): price / time / comfort / quality / pooling
    categorical_preferences       Tùy chọn ranh giới cứng, ví dụ: {"same_gender_coride": true}
)
```

## Quy tắc suy diễn tập dịch vụ hợp lệ (`allowed_service_codes`)

Từ bộ tham số `(mode, vehicle_preference, ride_preference, passenger_count, has_luggage, T_preferred - now)`, hệ thống lọc ra danh sách các dịch vụ hợp lệ theo bảng điều kiện cần và đủ dưới đây:

| Mã dịch vụ | Điều kiện `mode` | Điều kiện `vehicle_preference` | Điều kiện `ride_preference` | Điều kiện số khách & hành lý | Điều kiện thời gian đặt (`ΔT = T_preferred - now`) |
|---|---|---|---|---|---|
| `BIKE_URBAN` | `URBAN` | `BIKE` hoặc `ANY` | `PRIVATE` hoặc `ANY` | `passenger_count == 1` VÀ `has_luggage == false` | `0 <= ΔT <= 12 giờ` |
| `CAR_URBAN_PRIVATE` | `URBAN` | `CAR` hoặc `ANY` | `PRIVATE` hoặc `ANY` | `1 <= passenger_count <= 4` | `0 <= ΔT <= 12 giờ` |
| `CAR_URBAN_POOL` | `URBAN` | `CAR` hoặc `ANY` | `POOL` hoặc `ANY` | `1 <= passenger_count <= 2` | `0 <= ΔT <= 12 giờ` |
| `CAR_INTERCITY_PRIVATE` | `INTERCITY` | `CAR` hoặc `ANY` | `PRIVATE` hoặc `ANY` | `1 <= passenger_count <= 4` | `0 <= ΔT <= 7 ngày (168 giờ)` |
| `CAR_INTERCITY_POOL` | `INTERCITY` | `CAR` hoặc `ANY` | `POOL` hoặc `ANY` | `1 <= passenger_count <= 4` | `72 giờ <= ΔT <= 7 ngày (168 giờ)` |

- **Giải thích minh bạch khi dịch vụ bị loại:** Với mỗi dịch vụ không thỏa mãn điều kiện, hệ thống trả về kèm một mã lý do cụ thể (`rejection_reasons`) để giao diện hiển thị ngay cho khách hàng (ví dụ: *"Xe máy không khả dụng do bạn mang hành lý lớn hoặc đi từ 2 người"*, hoặc *"Đi ghép liên tỉnh cần đặt trước tối thiểu 3 ngày (72 giờ); bạn có thể chọn Taxi bao xe liên tỉnh để đi ngay"*).

---

# 7. HỆ THỐNG 11 RÀNG BUỘC CỨNG (HARD CONSTRAINTS)

Mọi ứng viên (Candidate) trước khi được đưa vào tính điểm xếp hạng hoặc hiển thị cho người dùng bắt buộc phải thỏa mãn đồng thời **tất cả 11 ràng buộc cứng** sau đây (`[ACCEPTED]` — D-02, D-04, D-05, D-24):

```text
Ràng buộc 1 (Phương tiện & Tài xế hợp lệ):
    - Tài xế đang trực tuyến, phương tiện hoạt động, đúng loại xe của dịch vụ.
    - Nếu dịch vụ là CAR_URBAN_POOL, CAR_INTERCITY_PRIVATE hoặc CAR_INTERCITY_POOL:
      bắt buộc driver.kyc_status == VERIFIED (S7).

Ràng buộc 2 (Tồn tại lộ trình hợp lệ):
    - OSRM tìm được đường đi hợp lệ giữa toàn bộ chuỗi điểm dừng theo đúng profile của loại xe
      (profile motorbike cấm đi vào đường cao tốc dành riêng cho ô tô).

Ràng buộc 3 (Khung giờ đón của hành khách):
    - T_earliest <= planned_pickup_time <= T_latest.

Ràng buộc 4 (Sức chứa theo từng đoạn hành trình — Segment Capacity Invariant):
    - Trên mọi chặng đường (segment) giữa hai điểm dừng liên tiếp (S_m, S_{m+1}) trong kế hoạch:
      ghế_đang_dùng(m, m+1) + passenger_count_mới <= vehicle.capacity
      (với BIKE: capacity = 1; với CAR4: capacity = 4).

Ràng buộc 5 (Tỉ lệ đi vòng tối đa của hành khách — Passenger Detour Ratio):
    - Áp dụng cho CAR_URBAN_POOL:
      detour_i = (quãng_thực_đi_trên_xe_i - quãng_đi_thẳng_i) / quãng_đi_thẳng_i
      Bắt buộc: detour_i <= max_passenger_detour_ratio_i (mặc định 0.30).

Ràng buộc 6 (Thời gian ngồi trên xe tối đa & Giờ đến muộn nhất):
    - Thời gian ngồi trên xe thực tế (từ lúc đón i đến lúc trả i):
      in_vehicle_time_i <= max_in_vehicle_time_i
      (Nếu khách không tự nhập, ngưỡng mặc định cho taxi ghép nội đô là:
       max_in_vehicle_time_i = direct_duration_i × 1.5 + 10 phút).
    - Nếu khách có khai báo latest_arrival:
      planned_dropoff_time_i <= latest_arrival_i.

Ràng buộc 7 (Giới hạn đi vòng và số điểm dừng thêm của tài xế):
    - Độ tăng thêm về quãng đường/thời gian của kế hoạch không vượt quá ngưỡng tài xế đã khai báo
      (max_driver_detour_km, max_driver_detour_min).
    - Số điểm đón phát sinh không vượt quá max_additional_pickups của tài xế, và tổng số điểm dừng
      trong một kế hoạch không vượt quá k_max_stops = 8.

Ràng buộc 8 (Trần ngân sách cứng — Budget Cap):
    - mức_giá_tối_đa_có_thể_thu_của_khách <= B_max.
      + Với các dịch vụ giá cố định: Fare_charged <= B_max.
      + Với CAR_URBAN_POOL: Unmatched_i (giá tối đa nếu không ghép được) <= B_max.

Ràng buộc 9 (Luật thời gian đặt của dịch vụ):
    - Thời điểm tạo yêu cầu và thời điểm khởi hành thỏa mãn bảng Mục 2.2.

Ràng buộc 10 (Giới hạn đi bộ ra điểm đón gặp nhau — C9):
    - walk_distance_m <= max_walk_m (nếu C9 tắt hoặc khách chọn đón tận nơi thì max_walk_m = 0).

Ràng buộc 11 (Ràng buộc tương thích xã hội / loại trừ):
    - Nếu khách i (hoặc bất kỳ khách j nào đã có trên xe) bật tùy chọn same_gender_coride = true,
      thì toàn bộ hành khách có đoạn hành trình chồng lấp trên xe phải có cùng giới tính xác thực.
```

> **Quy tắc bảo toàn ràng buộc toàn cục khi chèn khách động:** Đối với `CAR_URBAN_POOL`, khi thử chèn một hành khách mới vào một kế hoạch đang có sẵn các hành khách $j \in \{1, \dots, m\}$, các **Ràng buộc 3, 4, 5, 6, 8, 11** kèm theo **Ràng buộc bảo vệ giá (Mục 15.5)** bắt buộc phải được **kiểm tra lại cho toàn bộ các hành khách $j$ đã có trong kế hoạch**, không chỉ kiểm tra cho hành khách mới. Chỉ cần một hành khách cũ bị vi phạm bất kỳ ràng buộc nào, phương án chèn đó lập tức bị loại bỏ. Мо hình AI tuyệt đối không có quyền ghi đè hay nới lỏng bất kỳ ràng buộc nào trong 11 ràng buộc trên.

---

# 8. QUY TẮC NGÂN SÁCH (CỨNG VÀ MỀM)

```text
Ngân sách cứng (B_max) : Mức chi trả tối đa tuyệt đối của hành khách.
                         Ứng viên có mức thu tối đa > B_max bị loại ngay ở bước lọc cứng.
Ngân sách mềm (B_min)  : Mốc chi phí kỳ vọng hợp lý của hành khách.
                         Ứng viên có giá <= B_min đạt điểm PriceScore tối đa (= 1.0) trong hàm Baseline;
                         ứng viên có giá dưới B_min hoàn toàn hợp lệ, không bị loại hay trừ điểm.
```

---

# 9. HỆ THỐNG MÁY TRẠNG THÁI TRỰC GIAO (ORTHOGONAL STATE MACHINES)

Trong Revision 8, việc đặt trạng thái `PRICE_LOCKED` và `RIDE_STARTED` vào cùng một chuỗi trạng thái tuyến tính của `Booking` gây ra xung đột: đối với `CAR_URBAN_POOL`, xe có thể bắt đầu chạy (`RIDE_STARTED`) trước rồi mới đến điểm khóa giá (`pool_lock_point` → `PRICE_LOCKED`), khiến trạng thái mới ghi đè làm mất thông tin xe đang chạy.

Để giải quyết triệt để vấn đề này, Revision 9 tách trạng thái của một `Booking` thành **ba trục trạng thái trực giao (độc lập nhưng có điều kiện đồng bộ tại các cổng chuyển tiếp)** (`[ACCEPTED]` — D-46):

## 9.1. Trục 1 — Trạng thái hành trình của Booking (`ride_status`)

```text
HELD ──(Tài xế nhận offer / Đặt ghế liên tỉnh thành công)──► CONFIRMED
  │                                                              │
  │ (Hết hạn giữ ghế /                                           │ (Cổng kiểm tra trước khi đón:
  │  3 lần offer thất bại)                                       │  escrow_status == DEPOSITED)
  ▼                                                              ▼
EXPIRED                                                     RIDE_STARTED
                                                                 │
                                                                 ▼
                                                             COMPLETED

Các nhánh kết thúc sớm (từ HELD hoặc CONFIRMED, hoặc sự cố khi RIDE_STARTED):
├── CANCELLED_BY_PASSENGER   (Khách chủ động hủy)
├── CANCELLED_BY_DRIVER      (Tài xế hủy hoặc báo sự cố phương tiện)
├── CANCELLED_BY_SYSTEM      (Hủy do chuyến liên tỉnh thiếu khách T−60h, hoặc lỗi ký quỹ quá hạn)
└── NO_SHOW                  (Khách không có mặt tại điểm đón sau thời gian chờ quy định)
```

## 9.2. Trục 2 — Trạng thái ghép và chốt giá của Booking (`price_status`)

- **Đối với 4 dịch vụ giá cố định lúc đặt (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_INTERCITY_PRIVATE`, `CAR_INTERCITY_POOL`):**
  ```text
  QUOTED ──(Khi ride_status chuyển sang CONFIRMED)──► FIXED_LOCKED
           ├── (Riêng CAR_INTERCITY_POOL nếu gộp vào chuyến rẻ hơn tại T−72h) ──► MERGED_REDUCED_LOCKED
           └── (Riêng CAR_INTERCITY_POOL nếu mọi khách đồng ý góp thêm)       ──► TOPUP_LOCKED
  ```
- **Đối với dịch vụ Taxi ghép nội đô (`CAR_URBAN_POOL`):**
  ```text
  QUOTED ──(Khi CONFIRMED)──► POOL_SEARCHING (Mở cửa sổ ghép trước và trong khi xe chạy)
                                    │
                   (Khi hành khách chạm pool_lock_point của mình)
                                    ├── Có >= 1 booking độc lập khác đi chung ít nhất 1 đoạn
                                    │       ──► MATCHED_LOCKED (final_price = Fare_charged <= Quote_i)
                                    └── Không có booking độc lập nào đi chung
                                            ──► UNMATCHED_LOCKED (final_price = Unmatched_i,
                                                hoặc = Quote_i nếu do tài xế từ chối khách ghép)
  ```

## 9.3. Trục 3 — Trạng thái ký quỹ Blockchain (`escrow_status`)

Gắn kết 1–1 với mỗi `booking_id` (xem chi tiết tại Mục 80):

```text
NONE ──(Khi booking CONFIRMED, gửi lệnh ký quỹ mức trần)──► DEPOSIT_PENDING
                                                                │
                   ┌──(Giao dịch lỗi quá hạn retry)─────────────┼──(On-chain xác nhận)
                   ▼                                            ▼
             ESCROW_FAILED                                  DEPOSITED(cap)
     (Tự động hủy booking nếu chưa chạy)                        │
                                           ┌────────────────────┼────────────────────┐
                                  (Khi price_status     (Khi khách liên tỉnh  (Khi hủy chuyến)
                                   chốt < cap)           nạp thêm topUp)             │
                                           ▼                    ▼                    ▼
                                     LOCKED(final)        TOPPED_UP(new_final)   REFUNDED
                                           │                    │           (Toàn phần / Trừ phí)
                                           └─────────┬──────────┘
                                                     │ (Khi ride_status == COMPLETED
                                                     │  hoặc autoRelease sau X giờ)
                                                     ▼
                                                 RELEASED (Chia: Tài xế / Nền tảng / Quỹ)
                                                 (Hoặc DISPUTED ──► RESOLVED bởi Admin)
```

**Cổng đồng bộ bắt buộc giữa 3 trục trạng thái (`[ACCEPTED]` — D-49):**
1. **Cổng khởi hành (`RIDE_STARTED` Gate):** Một booking không được phép chuyển từ `ride_status = CONFIRMED` sang `RIDE_STARTED` nếu `escrow_status` chưa đạt `DEPOSITED` (hoặc `LOCKED` / `TOPPED_UP`). Nếu sau `escrow_deposit_timeout_s = 120 giây` kể từ lúc `CONFIRMED` mà giao dịch ký quỹ vẫn thất bại, hệ thống chuyển `ride_status = CANCELLED_BY_SYSTEM` để bảo vệ tài xế không chạy chuyến không có tiền bảo đảm.
2. **Cổng hoàn thành (`COMPLETED` Gate):** Một booking `CAR_URBAN_POOL` không được phép chuyển sang `ride_status = COMPLETED` nếu `price_status` chưa chuyển sang trạng thái khóa (`MATCHED_LOCKED` hoặc `UNMATCHED_LOCKED`). Khi xe đến cách điểm trả `< 3 km` (hoặc ngay tại điểm trả nếu chặng đi `< 3 km`), sự kiện khóa giá phải được thực thi trước hoặc đồng thời với sự kiện hoàn thành chuyến.
3. **Cổng giải ngân (`RELEASED` Gate):** Chỉ được phép gọi giải ngân `releasePayment` cho tài xế khi `ride_status == COMPLETED` VÀ `price_status` đã ở trạng thái `*_LOCKED`.
4. **Hành trình khi booking bị hủy (`CANCELLED_*` / `NO_SHOW`):** Khi `ride_status` chuyển sang một trong các trạng thái hủy, `price_status` đóng băng ngay tại trạng thái hiện hành và `escrow_status` chuyển sang `REFUNDED` (nếu phí hủy = 0%) hoặc giải ngân phần phí phạt hủy theo đúng Khung chính sách hủy tại Mục 18.7.
5. **Ánh xạ sang các biến huấn luyện AI (Mục 66):** Khi vòng đời của một booking kết thúc (ở `COMPLETED`, `CANCELLED_*`, `NO_SHOW` hoặc `EXPIRED`), hệ thống trích xuất trạng thái cuối cùng từ cả 3 trục để ghi bản ghi huấn luyện bất biến cho các mô hình `LTR`, `P(match)` và `P(fulfill)`.

---

# PHẦN III — NỘI ĐÔ: XE MÁY, TAXI BAO XE, TAXI GHÉP VÀ MÔ HÌNH ĐỊNH GIÁ – KINH TẾ

# 10. BA DỊCH VỤ NỘI ĐÔ VÀ CƠ CHẾ TOP-K ĐA PHƯƠNG TIỆN

**Quy ước thuật ngữ trong PHẦN III:** Cụm từ *"xe đơn"* (hoặc *"giá xe đơn"*) nghĩa là dịch vụ **taxi bao xe nội đô (`CAR_URBAN_PRIVATE`)** tính trên lộ trình đi thẳng của hành khách. Đây là mốc tham chiếu gốc để xác định mức tiết kiệm và các ngưỡng chặn của dịch vụ taxi ghép nội đô.

## 10.1. Xe máy nội đô (`BIKE_URBAN`) — Chạy 1:1

```text
Phạm vi    : Chỉ trong nội đô (mode = URBAN), đúng 1 hành khách, không hành lý lớn, không ghép
Tìm xe     : Tài xế xe máy rảnh gần điểm đón nhất → gửi offer (chờ tối đa 20 giây)
Định tuyến : OSRM profile motorbike (cấm đường cao tốc, tốc độ giờ cao điểm cao hơn ô tô)
Công thức giá cố định lúc đặt:
    BikeFare_raw = BIKE_BASE + BIKE_PER_KM × direct_km_bike + BIKE_PER_MIN × direct_min_bike
    BikeFare     = floor(BikeFare_raw / 1.000) × 1.000

Tham số cấu hình minh họa:
    BIKE_BASE      = 10.000 đ
    BIKE_PER_KM    =  4.500 đ/km
    BIKE_PER_MIN   =    250 đ/phút
    c_bike         = 20% (hoa hồng nền tảng = 0.20 × BikeFare; tài xế nhận = 0.80 × BikeFare)
```

Xe máy dùng chung bộ máy điều phối "xe đơn" với taxi bao xe nội đô, chỉ khác loại phương tiện (`BIKE`), sức chứa (`capacity = 1`), profile định tuyến và bảng tham số cước.

## 10.2. Taxi bao xe nội đô (`CAR_URBAN_PRIVATE`)

Phục vụ nhóm từ `1–4` hành khách thuê nguyên chuyến xe, không ghép thêm người lạ. Giá được tính theo công thức Mục 12.1 và khóa cố định ngay khi đặt (`FIXED_LOCKED`).

## 10.3. Taxi ghép nội đô (`CAR_URBAN_POOL`)

Phục vụ các booking có `1–2` hành khách muốn chia sẻ chuyến xe với các booking độc lập khác cùng hướng đi để giảm chi phí. Toàn bộ mô hình nghiệp vụ, toán học và kinh tế được quy định chi tiết từ Mục 11 đến Mục 24.

## 10.4. Ví dụ đối sánh ba dịch vụ nội đô trên cùng một nhu cầu di chuyển

Xét Hành khách A đi một mình (`passenger_count = 1`), không mang hành lý lớn, từ Đại học Phenikaa (Yên Nghĩa, Hà Đông) đến Đống Đa vào khung giờ cao điểm sáng:

| Dịch vụ | Quãng đường & Thời gian (minh họa OSRM) | Giá khách trả (`Fare_charged`) | Thu nhập tài xế | Đặc tính kinh tế – vận hành |
|---|---|---:|---:|---|
| **Xe máy (`BIKE_URBAN`)** | `14,0 km`, `35 phút` (profile motorbike) | **81.000 đ** *(từ 81.750 đ)* | `64.800 đ` | Rẻ nhất và nhanh nhất trong giờ cao điểm, nhưng phụ thuộc thời tiết (mưa/nắng) và kém an toàn/thoải mái hơn ô tô. |
| **Taxi bao xe (`CAR_URBAN_PRIVATE`)** | `14,0 km`, `40 phút` (profile car) | **194.000 đ** | `155.200 đ` | Thoải mái, riêng tư và đi thẳng không chờ đợi, nhưng chi phí cao gấp ~2,4 lần xe máy. |
| **Taxi ghép — Khi ghép thành công (`CAR_URBAN_POOL` với khách B, Mục 16)** | Thực đi trên xe `17,5 km`, `52 phút` | **143.000 đ** *(tiết kiệm 26,3%)* | Chia theo tổng chuyến (`210.800 đ` cho cả chuyến A+B) | Tiết kiệm `51.000 đ` so với bao xe; đổi lại phải chịu đi vòng 25% (+3,5 km, +12 phút) qua điểm đón/trả của khách B. |
| **Taxi ghép — Khi không ghép được ai (Mục 18)** | Đi thẳng `14,0 km`, `40 phút` | Tối đa **174.000 đ** *(tiết kiệm 10,3%)* | `155.200 đ` *(147.900 đ từ khách + 7.300 đ từ Quỹ)* | Khách không phải đi vòng và vẫn trả rẻ hơn bao xe `20.000 đ`; tài xế được Quỹ bảo đảm bù để thu nhập bằng đúng chạy bao xe. |

## 10.5. Cơ chế xếp hạng Top-K đa phương tiện (`[ACCEPTED]` — D-40)

Khi hành khách đi 1 mình, không hành lý lớn và chọn `vehicle_preference = ANY, ride_preference = ANY`, hệ thống trộn các ứng viên hợp lệ của cả ba dịch vụ (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`) vào **cùng một danh sách xếp hạng Top-K**. Đây là bài toán cốt lõi nơi mô hình Learning-to-Rank (LTR) phát huy giá trị vượt trội so với hàm trọng số tuyến tính cố định (kiểm định tại Giả thuyết **H9** — mức **MUST**):
- Cùng một hành khách nhưng vào ngày trời mưa (`is_raining = true`), LTR tự động hạ bậc xe máy và đẩy taxi ghép / taxi bao xe lên đầu.
- Với nhóm sinh viên nhạy cảm về giá và đi quãng dài (> 12 km) trong khung giờ cao điểm có `P(match)` cao, LTR ưu tiên đẩy taxi ghép lên vị trí đề xuất số 1.
- Với người dùng có lịch sử ưu tiên tốc độ và khung giờ đón hẹp (`T_latest - T_earliest` nhỏ), LTR đẩy xe máy hoặc taxi bao xe gần nhất lên đầu.

**Ràng buộc bảo toàn đa dạng hiển thị (Service Diversity Constraint):** Danh sách `Top-K` trả về cho giao diện luôn bảo đảm giữ lại **ít nhất một ứng viên tốt nhất của mỗi dịch vụ hợp lệ** (nếu dịch vụ đó có ít nhất 1 ứng viên vượt qua 11 ràng buộc cứng), để hành khách luôn có quyền trực tiếp đối sánh giá và thời gian giữa các phương thức.

---

# 11. HÌNH THỨC ĐẶT, CỬA SỔ GHÉP ĐỘNG VÀ ĐIỂM KHÓA GIÁ (`pool_lock_point`)

Dịch vụ `CAR_URBAN_POOL` hỗ trợ hai hình thức khởi tạo:
- `NOW` (Đặt đi ngay): Thời gian đón dự kiến trong khoảng `5–20 phút`.
- `SCHEDULED` (Hẹn giờ trước trong ngày): Đặt trước tối đa `12 giờ`, mở rộng cửa sổ gom khách cho bộ ghép theo lô (Mục 37).

Vì hệ thống cho phép **chèn thêm khách ghép mới ngay cả khi xe đang chạy trên đường (`ride_status = RIDE_STARTED`)**, cửa sổ tìm người ghép của một hành khách $i$ không đóng lại ở thời điểm đón khách, mà kéo dài cho đến **điểm khóa giá cá nhân (`pool_lock_point`)** của hành khách đó (`[ACCEPTED]` — D-08):

```text
pool_lock_point của booking i
= thời điểm sớm nhất xảy ra một trong bốn sự kiện sau:
    1. Quãng đường còn lại trên lộ trình hiện tại tới điểm trả của i < pool_lock_remaining_km (3,0 km)
       (Nếu tổng quãng đi thẳng của i <= 3,0 km, pool_lock_point kích hoạt ngay khi xe đón i
        hoặc khi đi được 50% quãng đường của i).
    2. Ngân sách đi vòng còn lại của i (max_passenger_detour_ratio_i - detour_hiện_tại_i) < 0,02 (đã cạn).
    3. Xe đã kín toàn bộ ghế (4/4 ghế) trên tất cả các đoạn đường còn lại từ vị trí hiện tại tới điểm trả của i.
    4. Xe đến điểm trả của i (trường hợp biên).
```

**Quy tắc chuyển trạng thái tại `pool_lock_point` của booking $i$:**
- Hệ thống kiểm tra xem trong suốt hành trình của $i$ (từ lúc $i$ lên xe cho đến điểm trả của $i$), có tồn tại **ít nhất một booking độc lập khác** ($j \ne i$) cùng ngồi trên xe với $i$ trên ít nhất một đoạn đường (co-riding segment overlap $\ge 1$) hay không:
  - Nếu **CÓ**: `price_status` của $i$ chuyển sang **`MATCHED_LOCKED`**, giá cuối cùng `final_price_i` được khóa cố định bằng mức giá ghép hiện hành `Fare_charged_i` ($\le \text{Quote}_i$).
  - Nếu **KHÔNG**: `price_status` của $i$ chuyển sang **`UNMATCHED_LOCKED`**, giá cuối cùng `final_price_i` được khóa bằng `Unmatched_i` (hoặc bằng `Quote_i` nếu nguyên nhân không ghép được là do tài xế từng từ chối một khách ghép hợp lệ — xem Mục 18.5).
- Một nhóm 2 hành khách đi chung trong **cùng một booking** (`passenger_count = 2`) vẫn chỉ là **một booking đơn lẻ**; chỉ khi ghép thêm được với ít nhất một booking độc lập khác thì mới được tính là `MATCHED_LOCKED`.

---

# 12. GIÁ THAM CHIẾU TAXI BAO XE NỘI ĐÔ VÀ HỆ SỐ GHẾ CHO NHÓM 2 KHÁCH

## 12.1. Công thức giá Taxi bao xe nội đô (`CAR_URBAN_PRIVATE`)

Với lộ trình đi thẳng từ điểm đón $P_{\text{start}}(i)$ đến điểm trả $P_{\text{dest}}(i)$ có quãng đường $D_{\text{direct}}(i)$ (km) và thời gian $T_{\text{direct}}(i)$ (phút) lấy từ OSRM (`profile = car`):

```text
PrivateFare_raw(i) = BASE + PER_KM × D_direct(i) + PER_MIN × T_direct(i)
PrivateFare(i)     = floor(PrivateFare_raw(i) / 1.000) × 1.000   (khi đặt dịch vụ CAR_URBAN_PRIVATE)
```

Tham số cấu hình minh họa (xe 4 chỗ):

```text
BASE               = 20.000 đ
PER_KM             = 11.000 đ/km
PER_MIN            =    500 đ/phút
commission_private = 20% (0.20)
```

*(Lưu ý: Trong ví dụ chuẩn Mục 16, với $D_{\text{direct}}$ nguyên hoặc bán nguyên và $T_{\text{direct}}$ chẵn, $\text{PrivateFare\_raw}(i)$ đã là bội số tròn nghìn đồng).*

## 12.2. Quy tắc định giá Booking 2 ghế (`seat_count = 2`) trong Taxi ghép nội đô không mâu thuẫn với chính sách giá (`[ACCEPTED]` — D-45b / O-04)

- **Bài toán thiết kế và Ràng buộc chính sách giá:**
  Ở dịch vụ `CAR_URBAN_PRIVATE`, một nhóm 1 người hay 2 người đi chung đều có quyền gọi một chiếc taxi bao xe đi riêng với đúng mức giá `PrivateFare(i)` (ví dụ `194.000 đ`) và tài xế nhận `0,80 × PrivateFare(i)` (`155.200 đ`). Đồng thời, chính sách giá cốt lõi của nền tảng (Mục 0.1, Mục 14.1, Mục 18.2, Quyết định `D-10`, `D-12`, `D-16` và Cổng đúng đắn `G05, G07` tại Mục 70) quy định bất biến cho **mọi booking `CAR_URBAN_POOL`**:
  1. Khi ghép thành công (`MATCHED_LOCKED`), tổng số tiền thu của booking $i$ luôn giảm ít nhất $d_{\min} = 20\%$ so với tự gọi một chuyến bao xe riêng: $\text{Fare\_charged}(i) \le \text{Quote}_i \le \text{PrivateFare}(i) \times (1 - d_{\min})$.
  2. Khi không tìm được người ghép (`UNMATCHED_LOCKED`), số tiền tối đa khách phải trả luôn rẻ hơn tự gọi bao xe riêng: $\text{Unmatched}_i < \text{PrivateFare}(i)$, và thu nhập mục tiêu của tài xế bằng đúng chạy bao xe đơn: $\text{TargetDriverPayout}(i) = (1 - c_{\text{private}}) \times \text{PrivateFare}(i)$.
- **Tại sao không được nhân hệ số $(1 + \gamma_{\text{seat}})$ trực tiếp vào `Cap_i`, `Quote_i` và `Unmatched_i`?**
  Nếu đặt giá tham chiếu trần $P_i = \text{PrivateFare}(i) \times (1 + \gamma_{\text{seat}}(s_i - 1))$ với $\gamma_{\text{seat}} > 0$ rồi thay trực tiếp vào công thức `Quote_i` và `Unmatched_i`, thì với booking 2 ghế ($s_i = 2$):
  - Với $\gamma_{\text{seat}} = 0,35$: $\text{Cap}_i = 0,80 \times 1,35 \times \text{PrivateFare}(i) = 1,08 \times \text{PrivateFare}(i) > \text{PrivateFare}(i)$ và $\text{Unmatched}_i = 1,215 \times \text{PrivateFare}(i) > \text{PrivateFare}(i)$.
  - Ngay cả với $\gamma_{\text{seat}} = 0,20$: $\text{Quote}_i = 0,96 \times \text{PrivateFare}(i) > 0,80 \times \text{PrivateFare}(i)$ (vi phạm cam kết giảm tối thiểu $d_{\min} = 20\%$ tại Cổng `G07`), và nếu tính $\text{Gap}_i = P_i - \text{Quote}_i = 0,24 \times \text{PrivateFare}(i)$ thì $\text{Unmatched}_i = 1,08 \times \text{PrivateFare}(i) > \text{PrivateFare}(i)$ (vi phạm `D-10`: nhóm 2 người đi ghép lại phải trả đắt hơn tự gọi một chiếc taxi bao xe đi riêng!).
- **Giải pháp chuẩn hóa nhất quán 100% trong Revision 9 (Tách biệt Giá tham chiếu trần `PrivateFare(i)` và Hệ số chiếm ghế `seat_occupancy_factor`):**
  Với mỗi booking $i$ trong `CAR_URBAN_POOL` có số ghế yêu cầu $s_i \in \{1, 2\}$ (`seat_count_i`):
  ```text
  1. Giá tham chiếu độc lập (Standalone Reference Fare):
       P_i = PrivateFare(i)      (giữ nguyên cho cả s_i = 1 và s_i = 2)
     → Dùng thống nhất cho Cổng Shareability (Mục 14.1), Cận trên Cap_i = (1 - d_min) × P_i,
       Quote_i, Gap_i = P_i - Quote_i, Unmatched_i và TargetDriverPayout(i) = 0,80 × P_i (Mục 18.3).
     → Bảo đảm tuyệt đối: Fare_charged(i) <= Quote_i <= 0,80 × PrivateFare(i) < Unmatched_i < PrivateFare(i)
       cho MỌI booking (kể cả s_i = 2)!

  2. Hệ số phụ trội chiếm ghế thứ hai (Seat Occupancy Factor — áp dụng khi phân bổ tiết kiệm Mục 15.2 & 15.3):
       seat_factor(i) = 1 + γ_seat × (s_i - 1)
       (Tham số cấu hình chuẩn đã phê duyệt: party_seat_surcharge_gamma = γ_seat = 0,35 ∈ [0.00, 0.50] — [ACCEPTED] D-45b)
     → Khi chia phần tiết kiệm S của chuyến ghép (Mục 15.2), trọng số nhận tiết kiệm w_i của booking i
       được chia cho seat_factor(i), và cận dưới Floor_i (Mục 15.3) được nhân với seat_factor(i) (kẹp không vượt Cap_i):
         w_i     = [ P_i × (1 + λ × detour_i + μ × walk_ratio_i) ] / [ 1 + γ_seat × (s_i - 1) ]
         Floor_i = min( EffectiveCap_i, max( BASE, P_i × (1 - d_max) × [ 1 + γ_seat × (s_i - 1) ] ) )
  ```
  - **Hệ quả toán học hoàn hảo:**
    - Khi booking đi **1 người ($s_i = 1$)**: `seat_factor(i) = 1,0` — **giữ nguyên 100% mọi công thức và con số của tất cả các ví dụ 1 khách**.
    - Khi booking đi **2 người ($s_i = 2$)**: Vì chiếm 2/4 ghế của xe, `seat_factor(i) = 1,35` làm giảm trọng số nhận tiết kiệm $w_i$ của nhóm 2 người đi $1,35$ lần và nâng sàn tối thiểu `Floor_i` từ $0,40 P_i$ lên $0,54 P_i$. Do đó, trên cùng một lộ trình và cùng mức bất tiện, **booking 2 ghế luôn trả cao hơn booking 1 ghế** (ví dụ ở Mục 16.1: nếu A đi 2 ghế ghép với B đi 1 ghế, giá thu của A tăng từ `143.000 đ` lên `148.000 đ`, còn giá thu của B giảm từ `105.000 đ` xuống `99.000 đ`), nhưng **vẫn luôn nằm dưới trần cam kết `Cap_A = 155.200 đ` (`Quote_A = 155.000 đ`) và `Unmatched_A = 174.000 đ < PrivateFare(A) = 194.000 đ`**!

---

# 13. GIÁ CỦA CẢ CHUYẾN GHÉP (`PlanFare`)

Một kế hoạch ghép nội đô bao gồm một chuỗi điểm dừng hợp lệ $S_0 \to S_1 \to \dots \to S_k$ phục vụ tập các booking độc lập $N = \{1, 2, \dots, n\}$ ($n \ge 2$). Tổng chi phí của cả kế hoạch chung (`PlanFare`) được tính dựa trên **quãng đường thực tế $D_{\text{plan}}$ và thời gian thực tế $T_{\text{plan}}$ của chiếc xe từ điểm đón đầu tiên $S_0$ đến điểm trả cuối cùng $S_k$**, cộng với phụ phí điểm dừng phát sinh:

```text
PlanFare
= BASE
+ PER_KM × D_plan
+ PER_MIN × T_plan
+ STOP_FEE × extra_stops
```

Trong đó:
```text
STOP_FEE    = 5.000 đ / điểm dừng phát sinh
extra_stops = k_total_stops - 2   (với mỗi booking gồm 1 điểm đón + 1 điểm trả,
                                   nếu không trùng tọa độ thì n bookings có 2n điểm dừng
                                   → extra_stops = 2n - 2)
```

Khoản `STOP_FEE` bù đắp trực tiếp chi phí thời gian giảm tốc, tấp lề và khởi hành lại của tài xế tại mỗi điểm đón/trả tăng thêm.

---

# 14. ĐIỀU KIỆN KHẢ NĂNG CHIA SẺ (SHAREABILITY) VÀ RÀNG BUỘC SINH LỜI TÀI XẾ

Không phải hai hay nhiều hành khách nào đi cùng hướng cũng nên ghép chung xe. Để một kế hoạch ghép được phép sinh làm ứng viên hợp lệ, kế hoạch đó bắt buộc phải vượt qua **hai cổng điều kiện kinh tế** đặt ngay sau 11 ràng buộc cứng:

## 14.1. Cổng 1 — Điều kiện lợi ích tối thiểu của hành khách (Passenger Shareability Condition — `[ACCEPTED]` D-16)

Tổng chi phí của kế hoạch chung phải nhỏ hơn hoặc bằng tổng giá tham chiếu của các khách sau khi đã trừ đi mức giảm giá cam kết tối thiểu $d_{\min}$:

```text
PlanFare <= (1 - d_min) × Σ_{i ∈ N} P_i
```
Với tham số mặc định:
```text
d_min = 0,20   (Cam kết: khi ghép thành công, mỗi booking được giảm ít nhất 20% so với P_i)
```

## 14.2. Cổng 2 — Điều kiện bảo toàn tốc độ sinh lời của tài xế tính trên Khoản Payout thực tế sau làm tròn (`[ACCEPTED]` D-45a / O-03)

- **Lý do bổ sung và Đồng bộ cơ sở tính sau làm tròn:**
  1. Trong Revision 8, Mục 17 và Mục 71 đặt ra bất biến: `thu_nhập_giờ(ghép thành công) >= thu_nhập_giờ(xe đơn cùng tuyến)`. Tuy nhiên, bất biến này không tự động thỏa mãn nếu chỉ dùng Cổng 1 (Mục 14.1): khi ghép thêm một khách đi chặng ngắn làm phát sinh thêm `8 phút` dừng đón/trả mà chỉ tăng `0,2 km` quãng đường, kế hoạch vẫn vượt qua Cổng 1 nhưng thu nhập theo giờ của tài xế bị tụt xuống dưới mức chạy đơn (`223.125 đ/giờ < 232.800 đ/giờ`).
  2. **Đồng bộ tuyệt đối với khoản Payout thực tế sau làm tròn (Mục 17.2 — `D-51`):** Tại Mục 16.1 và Mục 17.2, khoản tiền tài xế thực sự nhận được khi hoàn thành chuyến ghép được tính trên **tổng tiền thực thu sau khi đã làm tròn xuống `1.000 đ` của từng hành khách**:
     $$\text{DriverPayout}(\text{Plan}) = \sum_{i \in N} \text{driver\_base\_amount}(i) = (1 - c_{\text{pool}}) \times \sum_{i \in N} \text{Fare\_charged}(i)$$
     *(Ví dụ ở Mục 16.1: `PlanFare = 248.500 đ`, tổng thực thu sau làm tròn là `Σ Fare_charged = 143.000 + 105.000 = 248.000 đ`, và tài xế thực nhận `0,85 × 248.000 = 210.800 đ`, tương ứng tốc độ `210.800 / (52/60) = 243.231 đ/giờ`).* Nếu Cổng 2 lại tính trên `0,85 × PlanFare` trước làm tròn (`211.225 đ`), một kế hoạch nằm sát biên có thể vượt qua Cổng 2 trước làm tròn nhưng sau khi làm tròn xuống `Fare_charged(i)` lại tụt xuống dưới ngưỡng `DriverHourlyRate_Private(i)` và vi phạm Cổng `G09` ở Mục 70!
- **Quy tắc chuẩn hóa trong Revision 9:** Cổng 2A và Cổng 2B bắt buộc được kiểm tra **sau bước tính `Fare_charged(i)` (Mục 15.4)** và sử dụng **chính xác khoản payout thực tế sau làm tròn**:

```text
Định nghĩa đại lượng Payout và Thu nhập/giờ thực tế sau làm tròn:
    DriverPayout(Plan)          = (1 - c_pool) × Σ_{i ∈ N} Fare_charged(i)
    DriverPayout_Private(i)     = (1 - c_private) × PrivateFare(i)

    DriverHourlyRate(Plan)      = DriverPayout(Plan) / (T_plan / 60)              (đơn vị: VND/giờ)
    DriverHourlyRate_Private(i) = DriverPayout_Private(i) / (T_direct(i) / 60)    (đơn vị: VND/giờ)

Điều kiện Cổng 2A (Bất biến tổng thu nhập thực nhận của chuyến — Bắt buộc 100%):
    DriverPayout(Plan) >= max_{i ∈ N} DriverPayout_Private(i)

Điều kiện Cổng 2B (Bảo toàn tốc độ thu nhập thực nhận theo giờ — Cấu hình mặc định bật):
    DriverHourlyRate(Plan) >= (1 - ε_hourly) × max_{i ∈ N} DriverHourlyRate_Private(i)
    ⇔ [ (1 - c_pool) × Σ_{i ∈ N} Fare_charged(i) ] / (T_plan / 60)
       >= (1 - ε_hourly) × max_{i ∈ N} [ (1 - c_private) × PrivateFare(i) / (T_direct(i) / 60) ]
    (với ε_hourly = 0.00 ở cấu hình baseline để bảo đảm 0 vi phạm tại Cổng G09 Mục 70)
```

Nếu một phương án chèn điểm không thỏa mãn Cổng 1 (trước phân bổ) hoặc Cổng 2A/2B (sau phân bổ và làm tròn), phương án đó bị loại bỏ ngay lập tức (`POOL_SHAREABILITY_REJECTED`).

---

# 15. MÔ HÌNH PHÂN BỔ GIÁ GHÉP THEO TRỌNG SỐ BẤT TIỆN CÓ CHẶN HAI ĐẦU (`Floor_i` & `Cap_i`) VÀ CHÈN KHÁCH ĐỘNG

Đây là một trong những đóng góp toán học trọng tâm của đề tài, đã được hoàn thiện trong Revision 9 để khắc phục triệt để phản ví dụ nghiệm âm (`Fare_i < 0`) và xung đột khóa giá khi chèn khách động của Revision 8.

## 15.1. Năm nguyên tắc định giá công bằng đã hiệu chỉnh (`[ACCEPTED]`)

```text
N1 (Bảo toàn chi phí kế hoạch):
    Tổng giá chính xác trước làm tròn của tất cả các booking trong kế hoạch bằng đúng PlanFare:
    Σ_{i ∈ N} Fare_exact(i) == PlanFare.

N2 (Miền giá hợp lệ có chặn hai đầu — Bounded Savings Guarantee):
    Mỗi booking ghép thành công luôn được giảm ít nhất d_min (20%) và không giảm vượt quá d_max (60%)
    (trừ khi cả chuyến tiết kiệm vượt d_max), đồng thời không bao giờ thấp hơn giá mở cửa BASE:
    Floor_i <= Fare_exact(i) <= Cap_i.

N3 (Tính đơn điệu có điều kiện theo quy mô chuyến — Conditional Monotonicity):
    Với hai hành khách có cùng mức độ bất tiện (detour_i == detour_j và walk_ratio_i == walk_ratio_j),
    hành khách có giá tham chiếu P_i lớn hơn (đi xa hơn / nhiều ghế hơn) luôn trả mức giá lớn hơn.
    (Khi một khách đi xa hơn chút ít nhưng phải chịu đi vòng và đi bộ lớn hơn hẳn người kia,
     khoản bù đắp bất tiện có thể giúp họ trả thấp hơn — phản ánh đúng sự công bằng theo mức hy sinh).

N4 (Đơn điệu theo mức độ bất tiện — Inconvenience Compensation):
    Với cùng quy mô chuyến P_i và giữ nguyên PlanFare, hành khách chịu tỉ lệ đi vòng (detour_i)
    hoặc tỉ lệ đi bộ (walk_ratio_i) lớn hơn sẽ nhận được phần giảm giá lớn hơn (trả ít tiền hơn).

N5 (Bảo vệ giá khi cập nhật động — Dynamic Non-Increasing & Freeze Protection):
    - Khi một hành khách đã chạm pool_lock_point (price_status = MATCHED_LOCKED), mức giá của họ
      được đóng băng hoàn toàn, không thay đổi khi xe chèn thêm khách mới ở đoạn sau.
    - Đối với hành khách đang ở trạng thái POOL_SEARCHING, việc chèn thêm một khách mới vào xe
      không được làm tăng mức giá dự kiến hiện hành của họ (Fare_new(i) <= Fare_current(i)),
      và không bao giờ vượt quá trần giá tối đa đã báo lúc đặt (quoted_price_cap).
```

## 15.2. Công thức trọng số bất tiện (có điều chỉnh theo số ghế) và phân bổ cơ sở

Tổng phần tiết kiệm của cả kế hoạch ghép so với đi riêng lẻ (với $P_i \equiv \text{PrivateFare}(i)$ theo Mục 12.2):
```text
S = Σ_{i ∈ N} P_i - PlanFare     (Theo Mục 14.1, luôn có S >= d_min × Σ_{i ∈ N} P_i > 0)
```

Tỉ lệ đi vòng trên xe và tỉ lệ đi bộ ra điểm đón của từng booking $i$:
```text
detour_i     = (D_actual_in_vehicle(i) - D_direct(i)) / D_direct(i)
walk_ratio_i = D_walk(i) / D_direct(i)     (bằng 0 nếu đón tận nơi; bật khi dùng C9 ở Mục 23)
```

Trọng số nhận phần tiết kiệm $w_i$ của từng booking $i$ (`[ACCEPTED]` D-17 & D-45b):
```text
w_i = [ P_i × (1 + λ × detour_i + μ × walk_ratio_i) ] / [ 1 + γ_seat × (s_i - 1) ]
Tham số mặc định: λ = 1,0 ; μ = 2,0 ; γ_seat = 0,35 (với s_i ∈ {1, 2} là số ghế của booking i)
```
*Giải thích ý nghĩa kinh tế:*
- Khi $s_i = 1$ (booking 1 ghế): mẫu số bằng $1$, công thức giữ nguyên tuyệt đối $w_i = P_i \times (1 + \lambda \cdot \text{detour}_i + \mu \cdot \text{walk\_ratio}_i)$. Phần tiết kiệm chung $S$ được phân chia tỷ lệ thuận với quy mô chuyến đi ($P_i$) và nhân khuếch đại theo mức độ bất tiện đi vòng ($\lambda = 1,0$) và đi bộ ($\mu = 2,0$).
- Khi $s_i = 2$ (booking 2 ghế): vì nhóm 2 người chiếm 2/4 ghế của xe, trọng số nhận tiết kiệm của booking đó được chia cho $(1 + \gamma_{\text{seat}}) = 1,35$, giúp booking 2 ghế đóng góp phần chi phí lớn hơn vào `PlanFare` mà không làm thay đổi trần giá độc lập $P_i = \text{PrivateFare}(i)$.

Công thức phân bổ chưa kẹp biên:
```text
Fare_unbounded(i) = P_i - S × (w_i / Σ_{j ∈ N} w_j)
```

## 15.3. Cận trên (`Cap_i`), Cận dưới (`Floor_i`), Điều kiện khả thi và Thuật toán phân bổ hai cận chính xác (`[ACCEPTED]` — D-43)

### 15.3.1. Tại sao bắt buộc phải có cả Cận trên (`Cap_i`) và Cận dưới (`Floor_i`)?
- Nếu chỉ dùng công thức không chặn `Fare_unbounded(i)`:
  1. Một hành khách $B$ không phải đi vòng ($\text{detour}_B = 0$) đi chung với một hành khách $A$ đi vòng nhiều ($\text{detour}_A = 0.30$) khi tổng tiết kiệm $S$ vừa sát ngưỡng $20\%$ sẽ nhận phần tiết kiệm nhỏ hơn $20\%$, dẫn đến $\text{Fare}_B > (1 - d_{\min}) P_B$ (vi phạm cam kết giảm ít nhất $20\%$). Do đó cần **Cận trên `Cap_i`**.
  2. Ngược lại: khi chuyến có $3–4$ khách mà tổng tiết kiệm $S$ lớn, một khách đi chặng rất ngắn ($P_1 = 45.000$ đ) nhưng có hệ số bất tiện cao đi cùng $3$ khách đi chặng dài ($P_{2,3,4} = 205.000$ đ) có thể được chia phần tiết kiệm lớn hơn hoặc gần bằng $P_1$, làm giá rơi xuống dưới mức mở cửa tối thiểu `BASE = 20.000 đ` hoặc thậm chí **âm tiền (`Fare_1 < 0`)**. Do đó bắt buộc phải có **Cận dưới `Floor_i`**.

### 15.3.2. Định nghĩa Cận trên hiệu dụng (`EffectiveCap_i`) và Cận dưới (`Floor_i`)
Với mỗi booking $i$ trong tập cần phân bổ $U$:
```text
1. Cận trên chuẩn (Standard Cap):
     Cap_i = P_i × (1 - d_min)                               (với d_min = 0,20 → Cap_i = 0,80 × P_i)
   - Khi phân bổ kế hoạch mới (chưa có giá cũ): EffectiveCap_i = Cap_i.
   - Khi phân bổ lại lúc chèn khách động (Mục 15.5): EffectiveCap_i = DynamicCap_i = min(Cap_i, Fare_exact_old(i)).

2. Cận dưới có bảo vệ thứ tự biên (Valid Individual Floor):
     RawFloor_i = max( BASE, P_i × (1 - d_max) × [ 1 + γ_seat × (s_i - 1) ] )
     Floor_i    = min( EffectiveCap_i, RawFloor_i )
     (với d_max = 0,60, BASE = 20.000 đ; với s_i = 1 và P_i >= 25.000 đ thì Floor_i = max(20.000, 0,40 × P_i))
```
*(Việc lấy `min(EffectiveCap_i, RawFloor_i)` bảo đảm toán học rằng với mọi $i \in U$, miền giá cá nhân $[\text{Floor}_i, \text{EffectiveCap}_i]$ luôn khác rỗng: $\text{Floor}_i \le \text{EffectiveCap}_i$).*

### 15.3.3. Điều kiện cần và đủ để tồn tại nghiệm (Feasibility Theorem) & Xử lý khi vô nghiệm
Cho tập khách cần phân bổ $U \ne \emptyset$, tổng chi phí mục tiêu cần chia $\text{TargetFare}_U > 0$, trọng số $w_i > 0$ và cặp cận $[\text{Floor}_i, \text{EffectiveCap}_i]$ cho từng $i \in U$.

**Định lý tồn tại và duy nhất nghiệm:**
Hệ phương trình và bất phương trình phân bổ hai cận:
$$\sum_{i \in U} \text{Fare\_exact}(i) = \text{TargetFare}_U \quad \text{và} \quad \text{Floor}_i \le \text{Fare\_exact}(i) \le \text{EffectiveCap}_i, \; \forall i \in U$$
**có nghiệm khi và chỉ khi đồng thời thỏa mãn 3 điều kiện khả thi `(F1)`, `(F2)`, `(F3)` sau đây:**
```text
(F1 — Tính hợp lệ biên cá nhân) : Floor_i <= EffectiveCap_i,                    ∀ i ∈ U
(F2 — Điều kiện khả thi cận dưới): Σ_{i ∈ U} Floor_i <= TargetFare_U
(F3 — Điều kiện khả thi cận trên): TargetFare_U <= Σ_{i ∈ U} EffectiveCap_i
```

**Quy định xử lý tất định khi không tồn tại nghiệm (Infeasibility Handling Rules):**
Trước khi chạy vòng lặp phân bổ, hệ thống kiểm tra nghiêm ngặt `(F1)`, `(F2)`, `(F3)`:
1. **Trường hợp 1 — Vi phạm cận trên tổng (`TargetFare_U > Σ_{i ∈ U} EffectiveCap_i`) hoặc `U == ∅`:**
   - **Không tồn tại nghiệm** nào giúp mọi khách được giảm ít nhất $d_{\min}$ (hoặc không tăng giá khách cũ khi chèn động).
   - Hệ thống trả về mã trạng thái **`INFEASIBLE_UPPER_BOUND` (`None`)** và **TỪ CHỐI ngay phương án ghép / vị trí chèn điểm này** (ghi nhận sự kiện `POOL_ALLOCATION_INFEASIBLE_CAP`).
2. **Trường hợp 2 — Vi phạm cận dưới tổng (`TargetFare_U < Σ_{i ∈ U} Floor_i`):**
   - Xảy ra khi 3–4 chuyến ghép trùng tuyến gần như tuyệt đối khiến tổng chi phí `TargetFare_U` còn nhỏ hơn cả tổng mức sàn tối thiểu $\sum_{i \in U} \text{Floor}_i$ (tức tổng tiết kiệm của chuyến vượt quá mức trần giảm giá $d_{\max}$). Khi đó **không tồn tại nghiệm nằm trong miền $[\text{Floor}_i, \text{EffectiveCap}_i]$**.
   - Hành vi của hệ thống được điều khiển tất định bởi tham số cấu hình `on_lower_bound_infeasible` (Phụ lục B & `MVP_CONFIG_BASELINE_V1.md`):
     - **Chế độ mặc định Baseline (`on_lower_bound_infeasible = "REJECT"` — `[ACCEPTED]` cho kiểm thử cổng `G06`):** Trả về **`INFEASIBLE_LOWER_BOUND` (`None`)** và **TỪ CHỐI phương án ghép** (`POOL_ALLOCATION_INFEASIBLE_FLOOR`). Chế độ này bảo đảm tuyệt đối 100% không có bất kỳ booking nào trong hệ thống có `Fare_exact(i) < Floor_i` (Cổng `G06` đạt 0 vi phạm tuyệt đối).
     - **Chế độ tùy chọn mở rộng (`on_lower_bound_infeasible = "CLAMP_TO_BASE"` — `[PROPOSED]`):** Nếu muốn giữ lại các chuyến siêu tiết kiệm có $\text{TargetFare}_U \ge |U| \times \text{BASE}$, hệ thống hạ sàn cá nhân từ $\text{Floor}_i$ về sàn mở cửa $\text{Floor}^{\text{base}}_i = \text{BASE} = 20.000\text{ đ}$ rồi chạy lại phân bổ trên $[\text{BASE}, \text{EffectiveCap}_i]$ (nếu $\text{TargetFare}_U < |U| \times \text{BASE}$ thì vẫn từ chối tuyệt đối).

### 15.3.4. Thuật toán phân bổ hai cận chính xác theo Điểm gãy đơn điệu (Exact Piecewise-Linear Breakpoint Water-Filling)
Khi cả 3 điều kiện khả thi `(F1)`, `(F2)`, `(F3)` đã thỏa mãn ($\sum_{i \in U} \text{Floor}_i \le \text{TargetFare}_U \le \sum_{i \in U} \text{EffectiveCap}_i$), xét hàm giá kẹp hai đầu theo tham số mức tiết kiệm trên mỗi đơn vị trọng số $\tau \in \mathbb{R}$:
$$f_i(\tau) = \min\Big(\text{EffectiveCap}_i,\; \max\big(\text{Floor}_i,\; P_i - \tau \cdot w_i\big)\Big), \qquad \Phi(\tau) = \sum_{i \in U} f_i(\tau)$$
- Vì $w_i > 0$ và $\text{Floor}_i \le \text{EffectiveCap}_i$, mỗi hàm $f_i(\tau)$ là hàm liên tục, tuyến tính từng khúc (piecewise-linear) và đơn điệu không tăng theo $\tau$, có đúng 2 điểm gãy (breakpoints):
  $$\tau^{\text{cap}}_i = \frac{P_i - \text{EffectiveCap}_i}{w_i} \le \tau^{\text{floor}}_i = \frac{P_i - \text{Floor}_i}{w_i}$$
- Tại $\tau_{\min} = \min_{i \in U} \tau^{\text{cap}}_i$, ta có $\Phi(\tau_{\min}) = \sum_{i \in U} \text{EffectiveCap}_i \ge \text{TargetFare}_U$.
- Tại $\tau_{\max} = \max_{i \in U} \tau^{\text{floor}}_i$, ta có $\Phi(\tau_{\max}) = \sum_{i \in U} \text{Floor}_i \le \text{TargetFare}_U$.
- Khác với cách lặp gán cứng tuần tự từng phía (có thể bị lệch tổng nếu trong cùng một bước có 1 khách chạm `Cap` và 1 khách khác chạm `Floor` đồng thời), thuật toán duyệt qua mảng tối đa $2|U| \le 8$ điểm gãy đã sắp xếp để tìm đoạn $[t_k, t_{k+1}]$ chứa nghiệm $\tau^*$ **luôn tìm được nghiệm chính xác tuyệt đối 100% trong thời gian $O(|U| \log |U|)$**:

```text
Thuật toán: AllocateTwoSidedBounded(U, TargetFare_U, P, w, Floor, EffectiveCap)
--------------------------------------------------------------------------------
1. Kiểm tra điều kiện khả thi (F1, F2, F3):
   - Nếu U == ∅: Return (None, "EMPTY_SET").
   - Với mỗi i ∈ U: Nếu Floor[i] > EffectiveCap[i] + 1e-9: Return (None, "INFEASIBLE_INDIVIDUAL_BOUNDS").
   - SumFloor = Σ_{i ∈ U} Floor[i] ; SumCap = Σ_{i ∈ U} EffectiveCap[i].
   - Nếu TargetFare_U > SumCap + 1e-9: Return (None, "INFEASIBLE_UPPER_BOUND").
   - Nếu TargetFare_U < SumFloor - 1e-9: Return (None, "INFEASIBLE_LOWER_BOUND").
   - Nếu |TargetFare_U - SumCap| <= 1e-9: Return (EffectiveCap, "OK").
   - Nếu |TargetFare_U - SumFloor| <= 1e-9: Return (Floor, "OK").

2. Tạo tập điểm gãy đã sắp xếp tăng dần B (tối đa 2 × |U| <= 8 điểm):
   B = sorted( unique( { (P[i] - EffectiveCap[i]) / w[i] : i ∈ U }
                     ∪ { (P[i] - Floor[i]) / w[i]        : i ∈ U } ) )

3. Tìm đoạn [t_k, t_{k+1}] liên tiếp trong B sao cho Φ(t_{k+1}) <= TargetFare_U <= Φ(t_k):
   (Trong đó Φ(t) = Σ_{i ∈ U} min(EffectiveCap[i], max(Floor[i], P[i] - t × w[i])) là hàm tuyến tính trên [t_k, t_{k+1}])
   - Nội suy tuyến tính chính xác trên đoạn [t_k, t_{k+1}]:
       tau_star = t_k + [ (Φ(t_k) - TargetFare_U) / (Φ(t_k) - Φ(t_{k+1})) ] × (t_{k+1} - t_k)
   - Với mỗi i ∈ U:
       Fare_exact[i] = min( EffectiveCap[i], max( Floor[i], P[i] - tau_star × w[i] ) )
   - Return (Fare_exact, "OK").
```
*(Ghi chú tương đương: Khi chỉ có một phía biên bị chạm — như trong mọi kịch bản 2 khách hoặc kịch bản 1 khách chạm sàn — nghiệm nội suy điểm gãy $\tau^*$ trùng khớp hoàn toàn đến từng chữ số thập phân với phép lặp gán `Fixed` và chia lại `RemFare` theo tỷ lệ $w_i / W_{\text{rem}}$, đồng thời xử lý chính xác tuyệt đối cả trường hợp hai biên chạm cùng lúc!).*

## 15.4. Quy tắc làm tròn tiền thu của hành khách (`[ACCEPTED]` — D-18)

```text
Fare_charged(i)      = floor( Fare_exact(i) / 1.000 ) × 1.000
rounding_absorbed(i) = Fare_exact(i) - Fare_charged(i)     (0 <= rounding_absorbed(i) < 1.000 đ)
```
Làm tròn xuống đến bội số `1.000 đ` bảo đảm không có bất kỳ hành khách nào phải trả vượt quá con số toán học `Fare_exact(i)` hay vượt trần `Cap_i` sau khi làm tròn.

## 15.5. Hệ điều kiện đầy đủ và Quy trình định giá khi chèn thêm khách động lúc xe đang chạy (`[ACCEPTED]` — D-44 / O-02)

Khi một kế hoạch ghép đang vận hành trên đường và hệ thống xét chèn thêm một booking mới $c_{\text{new}}$ vào kế hoạch hiện có $N_{\text{old}}$, tập hành khách trong kế hoạch mới $N_{\text{new}} = N_{\text{old}} \cup \{c_{\text{new}}\}$ được chia thành 3 nhóm tách biệt:
1. **Nhóm $L$ (Đã khóa giá — `price_status == MATCHED_LOCKED`):** Là các hành khách đã đi qua `pool_lock_point` của mình (hoặc đã xuống xe ở các điểm dừng trước đó trong cùng `ride_plan`).
2. **Nhóm $U_{\text{old}}$ (Đang tìm ghép — `price_status == POOL_SEARCHING`):** Là các hành khách đang ngồi trên xe (hoặc chờ đón) nhưng chưa chạm `pool_lock_point`, hiện đang có mức giá chính xác trước khi chèn là $\text{Fare\_exact}_{\text{old}}(i) \in [\text{Floor}_i, \text{Cap}_i]$.
3. **Khách mới $c_{\text{new}}$:** Hành khách đang được thử chèn vào kế hoạch.

**Tại sao điều kiện đơn lẻ $\Delta\text{PlanFare} \le \text{Cap}_{c_{\text{new}}}$ là CHƯA ĐỦ khi đã có khách khóa giá?**
- Trước khi chèn $c_{\text{new}}$, bảo toàn tổng cho kế hoạch cũ là $\text{PlanFare}_{\text{old}} = \sum_{k \in L} \text{Fare\_exact}_{\text{old}}(k) + \sum_{i \in U_{\text{old}}} \text{Fare\_exact}_{\text{old}}(i)$.
- Khi đóng băng nhóm $L$, tổng chi phí cần phân bổ cho tập khách chưa khóa $U = U_{\text{old}} \cup \{c_{\text{new}}\}$ là $\text{TargetFare}_U = \text{PlanFare}_{\text{new}} - \sum_{k \in L} \text{Fare\_exact}_{\text{old}}(k) = \sum_{i \in U_{\text{old}}} \text{Fare\_exact}_{\text{old}}(i) + \Delta\text{PlanFare}$.
- Bất đẳng thức $\Delta\text{PlanFare} \le \text{Cap}_{c_{\text{new}}}$ mới chỉ đảm bảo **điều kiện khả thi cận trên `(F3)`** ($\text{TargetFare}_U \le \sum_{i \in U_{\text{old}}} \text{DynamicCap}_i + \text{Cap}_{c_{\text{new}}}$). Nó **chưa đảm bảo**:
  1. Tập $U_{\text{old}}$ khác rỗng và có đoạn hành trình đi chung thực sự với $c_{\text{new}}$ (nếu $U_{\text{old}} = \emptyset$, tức mọi khách cũ đều đã chạm `pool_lock_point`, thì kế hoạch đã đóng `PLAN_CLOSED_TO_NEW` theo Mục 22; nếu vẫn chèn $c_{\text{new}}$ thì $U = \{c_{\text{new}}\}$ chỉ có 1 người và ép $\text{Fare\_exact}(c_{\text{new}}) = \Delta\text{PlanFare}$, có thể nhỏ hơn $\text{Floor}_{c_{\text{new}}}$!).
  2. **Điều kiện khả thi cận dưới `(F2)` trên tập $U$:** Nếu các khách $i \in U_{\text{old}}$ hiện đã có giá sát mức sàn $\text{Floor}_i$ và chi phí tăng thêm $\Delta\text{PlanFare}$ rất nhỏ (ví dụ đón/trả $c_{\text{new}}$ ngay trên đường chỉ tốn thêm `10.000 đ` $< \text{Floor}_{c_{\text{new}}} = 25.600$ đ), thì $\text{TargetFare}_U$ có thể nhỏ hơn $\sum_{i \in U_{\text{old}}} \text{Floor}_i + \text{Floor}_{c_{\text{new}}}$, dẫn tới vô nghiệm trên miền $[\text{Floor}_m, \text{DynamicCap}_m]$!
  3. **Điều kiện Cổng 2A & 2B sau làm tròn:** Sau khi phân bổ lại và làm tròn xuống `1.000 đ` cho tập $U$ (trong khi nhóm $L$ giữ nguyên `final_price(k)`), tổng thu nhập thực nhận theo giờ của tài xế trên toàn kế hoạch $N_{\text{new}}$ phải tiếp tục thỏa mãn Mục 14.2.

**Hệ 6 điều kiện cần và đủ cho việc chèn khách động (`Dynamic Insertion Complete Conditions D1–D6`):**
Việc chèn khách mới $c_{\text{new}}$ vào kế hoạch đang có $N_{\text{old}} = L \cup U_{\text{old}}$ được chấp nhận **khi và chỉ khi thỏa mãn đầy đủ cả 6 điều kiện `D1` đến `D6` sau đây**:
```text
D1 (Kế hoạch đang mở & Có đồng hành thực tế):
    ride_plan.status == PLAN_OPEN_SEARCHING, tập khách chưa khóa U_old != ∅,
    và đoạn hành trình [Pickup(c_new), Dropoff(c_new)] có giao khác rỗng với ít nhất 1 khách đang trên xe.

D2 (Đóng băng nhóm đã khóa giá L và xác lập biên động trên U = U_old ∪ {c_new}):
    - Với mọi k ∈ L     : Fare_exact_new(k) = Fare_exact_old(k) ; Fare_charged_new(k) = final_price(k) (không đổi).
    - Với mọi i ∈ U_old : DynamicCap_i = min(Cap_i, Fare_exact_old(i)) = Fare_exact_old(i) (vì Fare_exact_old(i) <= Cap_i);
                          Floor_i      = min(DynamicCap_i, RawFloor_i).
    - Với khách mới c_new: DynamicCap_{c_new} = Cap_{c_new} = (1 - d_min) × P_{c_new};
                          Floor_{c_new}      = min(Cap_{c_new}, RawFloor_{c_new}).
    - Chi phí mục tiêu cần chia cho U:
        TargetFare_U = PlanFare_new - Σ_{k ∈ L} Fare_exact_old(k)
                     = Σ_{i ∈ U_old} Fare_exact_old(i) + (PlanFare_new - PlanFare_old).

D3 (Điều kiện khả thi cận trên trên U — Bảo đảm không tăng giá khách cũ U_old và giảm >= d_min cho c_new):
    TargetFare_U <= Σ_{i ∈ U_old} DynamicCap_i + Cap_{c_new}
    ⇔ ΔPlanFare = (PlanFare_new - PlanFare_old) <= Cap_{c_new} = (1 - d_min) × P_{c_new}.

D4 (Điều kiện khả thi cận dưới trên U — Bảo đảm không thủng sàn Floor_m):
    TargetFare_U >= Σ_{i ∈ U_old} Floor_i + Floor_{c_new}
    ⇔ ΔPlanFare >= Floor_{c_new} - Σ_{i ∈ U_old} (Fare_exact_old(i) - Floor_i).
    (Nếu vi phạm D4 và on_lower_bound_infeasible == "REJECT" → Từ chối phép chèn).

D5 (Phân bổ hai cận, làm tròn và kiểm tra Cổng 1 & Cổng 2 sau làm tròn trên toàn kế hoạch N_new):
    - Chạy AllocateTwoSidedBounded(U, TargetFare_U, P, w, Floor, DynamicCap) (Mục 15.3.4) thu được Fare_exact_new(m)
      và làm tròn Fare_charged_new(m) = floor(Fare_exact_new(m) / 1.000) × 1.000 với mọi m ∈ U.
    - Kiểm tra với mọi i ∈ U_old: Fare_exact_new(i) <= Fare_exact_old(i) VÀ Fare_charged_new(i) <= Fare_charged_old(i).
    - Kiểm tra Cổng 1 (Mục 14.1): PlanFare_new <= (1 - d_min) × Σ_{m ∈ N_new} P_m.
    - Kiểm tra Cổng 2A & 2B sau làm tròn (Mục 14.2):
        DriverPayout_new = (1 - c_pool) × [ Σ_{k ∈ L} final_price(k) + Σ_{m ∈ U} Fare_charged_new(m) ]
        DriverPayout_new >= max_{m ∈ N_new} [ (1 - c_private) × P_m ]
        [ DriverPayout_new / (T_plan_new / 60) ] >= (1 - ε_hourly) × max_{m ∈ N_new} [ (1 - c_private) × P_m / (T_direct(m) / 60) ].

D6 (Kiểm tra trần ngân sách của khách mới c_new):
    Unmatched_{c_new} <= B_max(c_new).
```

---

# 16. KIỂM CHỨNG ĐỊNH LƯỢNG: VÍ DỤ CHUẨN PHENIKAA → ĐỐNG ĐA VÀ CÁC KỊCH BẢN BIÊN

> Mọi con số dưới đây đã được kiểm chứng độc lập và dùng làm bộ kiểm thử hồi quy cố định (Regression Test Suite) tại Mục 71.

## 16.1. Kịch bản chuẩn 2 hành khách: Phenikaa → Đống Đa ghép với La Phù → Nguyễn Trãi

| Thông số | Hành khách A | Hành khách B |
|---|---|---|
| Điểm đón (`pickup`) | Đại học Phenikaa (Yên Nghĩa, Hà Đông) | La Phù (Hoài Đức) |
| Điểm trả (`destination`) | Đống Đa | Nguyễn Trãi (Thanh Xuân) |
| Số khách (`seat_count`) | `1` ghế | `1` ghế |
| Quãng đường & Thời gian đi thẳng (`CAR`) | `14,0 km`, `40 phút` | `9,0 km`, `28 phút` |
| Giới hạn đi vòng tối đa khai báo | `30%` (`0,30`) | `30%` (`0,30`) |

### Lộ trình kế hoạch ghép (`S_0 → S_1 → S_2 → S_3`):
```text
S_0: Đón A tại Đại học Phenikaa (km 0,0)
  ──(5,0 km)──► S_1: Đón B tại La Phù (km 5,0)
  ──(9,0 km)──► S_2: Trả B tại Nguyễn Trãi (km 14,0)
  ──(3,5 km)──► S_3: Trả A tại Đống Đa (km 17,5)

Tổng quãng đường kế hoạch (D_plan) : 17,5 km
Tổng thời gian kế hoạch (T_plan)   : 52 phút (đã gồm thời gian dừng đón/trả)
Tổng số điểm dừng                  : 4 điểm → extra_stops = 4 - 2 = 2 điểm phát sinh
```
- Hành khách A ngồi trên xe từ `S_0` đến `S_3`: thực đi `17,5 km` so với đi thẳng `14,0 km` → **Tỉ lệ đi vòng $\text{detour}_A = (17,5 - 14,0) / 14,0 = 0,25$ ($25\% \le 30\%$ ✓)**. Thời gian ngồi trên xe của A = `52 phút` $\le 40 \times 1,5 + 10 = 70$ phút ✓.
- Hành khách B ngồi trên xe từ `S_1` đến `S_2`: thực đi `9,0 km` đúng bằng đi thẳng `9,0 km` → **Tỉ lệ đi vòng $\text{detour}_B = 0,00$ ($0\%$ ✓)**. Thời gian ngồi trên xe của B $\le 28 \times 1,5 + 10 = 52$ phút ✓.

### Bước 1 — Tính giá xe đơn tham chiếu ($P_A, P_B$):
```text
P_A = PrivateFare(A) = 20.000 + 11.000 × 14,0 + 500 × 40 = 20.000 + 154.000 + 20.000 = 194.000 đ
P_B = PrivateFare(B) = 20.000 + 11.000 ×  9,0 + 500 × 28 = 20.000 +  99.000 + 14.000 = 133.000 đ
Tổng hai xe đơn (P_A + P_B)                                                          = 327.000 đ
```

### Bước 2 — Tính `PlanFare` và Kiểm tra 2 cổng Mục 14:
```text
PlanFare = 20.000 + 11.000 × 17,5 + 500 × 52 + 5.000 × 2
         = 20.000 + 192.500 + 26.000 + 10.000
         = 248.500 đ

- Kiểm tra Cổng 1 (Shareability, d_min = 0,20):
  (1 - 0,20) × 327.000 = 261.600 đ
  Vì 248.500 đ <= 261.600 đ → THỎA CỔNG 1 (Tổng tiết kiệm S = 327.000 - 248.500 = 78.500 đ, tức 24,01%).

- Kiểm tra Cổng 2 (Tốc độ sinh lời theo giờ của tài xế):
  + Chạy đơn chở A: 155.200 đ / (40/60 giờ) = 232.800 đ/giờ.
  + Chạy đơn chở B: 106.400 đ / (28/60 giờ) = 228.000 đ/giờ.
  + Chạy ghép A+B : (0,85 × 248.000 đ) / (52/60 giờ) = 210.800 / (52/60) = 243.231 đ/giờ >= 232.800 đ/giờ → THỎA CỔNG 2.
```

### Bước 3 — Phân bổ giá theo trọng số bất tiện (Mục 15.2 – 15.4):
```text
Cận trên (Cap_i, d_min = 0,20)  : Cap_A   = 0,80 × 194.000 = 155.200 đ ; Cap_B   = 0,80 × 133.000 = 106.400 đ
Cận dưới (Floor_i, d_max = 0,60): Floor_A = 0,40 × 194.000 =  77.600 đ ; Floor_B = 0,40 × 133.000 =  53.200 đ

Trọng số (λ = 1,0, walk_ratio = 0):
    w_A = 194.000 × (1 + 1,0 × 0,25) = 242.500
    w_B = 133.000 × (1 + 1,0 × 0,00) = 133.000
    Σw  = 242.500 + 133.000          = 375.500

Phần tiết kiệm được chia:
    Giảm_A = 78.500 × (242.500 / 375.500) = 50.695,74 đ
    Giảm_B = 78.500 × (133.000 / 375.500) = 27.804,26 đ

Giá chính xác (Fare_exact) và kiểm tra biên [Floor_i, Cap_i]:
    Fare_exact(A) = 194.000 - 50.695,74 = 143.304,26 đ  ∈ [77.600, 155.200] ✓
    Fare_exact(B) = 133.000 - 27.804,26 = 105.195,74 đ  ∈ [53.200, 106.400] ✓
    Tổng Fare_exact = 143.304,26 + 105.195,74 = 248.500,00 đ == PlanFare ✓

Làm tròn xuống 1.000 đ (Fare_charged):
    Fare_charged(A) = 143.000 đ   (rounding_absorbed(A) = 304,26 đ)
    Fare_charged(B) = 105.000 đ   (rounding_absorbed(B) = 195,74 đ)
```

### Bảng tổng hợp kết quả Mục 16.1:

| Hành khách | Giá xe đơn ($P_i$) | Giá chính xác (`Fare_exact`) | `%` giảm (trước làm tròn) | Giá thực thu (`Fare_charged`) | `%` giảm (sau làm tròn) |
|---|---:|---:|---:|---:|---:|
| **Khách A (Phenikaa → Đống Đa, đi vòng 25%)** | `194.000 đ` | `143.304,26 đ` | `-26,13%` | **143.000 đ** | **-26,29%** |
| **Khách B (La Phù → Nguyễn Trãi, đi vòng 0%)** | `133.000 đ` | `105.195,74 đ` | `-20,91%` | **105.000 đ** | **-21,05%** |
| **Tổng cộng** | **327.000 đ** | **248.500,00 đ** | `-24,01%` | **248.000 đ** | *(Lệch làm tròn: `500 đ`)* |

### So sánh với hai phương pháp chia giá đối chứng (Dùng cho Khảo sát S1 / Giả thuyết H4):

| Phương pháp phân bổ | Giá chính xác Khách A (`%` giảm) | Giá chính xác Khách B (`%` giảm) | Nhận xét & Đánh giá cơ chế |
|---|---:|---:|---|
| **1. Tỉ lệ thuần theo giá xe đơn** (`w_i = P_i`) | `147.428 đ (-24,01%)` | `101.072 đ (-24,01%)` | Đơn giản nhưng bất công với A: A phải chịu đi vòng thêm 25% quãng đường để đón/trả B nhưng tỷ lệ giảm giá lại bằng hệt B (`24,01%`). |
| **2. Giá trị Shapley 2 người** *(tương đương chia đều tiết kiệm `S/2 = 39.250 đ`)* | `154.750 đ (-20,23%)` | `93.750 đ (-29,51%)` | Phản ánh đóng góp chi phí biên nhưng tạo nghịch lý tâm lý: người chịu đi vòng 25% (A) chỉ được giảm `20,2%`, trong khi người đi thẳng 0% (B) lại được giảm tới `29,5%`. |
| **3. Trọng số bất tiện đề xuất (`λ = 1,0`)** | **`143.304 đ (-26,13%)`** | **`105.196 đ (-20,91%)`** | Cả hai cùng vượt mức cam kết `20%`, đồng thời A được bù đắp thêm `~5,2 điểm %` giảm giá nhờ chấp nhận đi vòng qua La Phù. |

## 16.2. Kiểm chứng Kịch bản biên #1: Tác dụng của Cận dưới `Floor_i` và Điều kiện khả thi `(F2)` trong chuyến 4 khách chênh lệch lớn

Xét tổ hợp 4 hành khách đi ghép (mỗi người 1 ghế, $s_i = 1$):
- **Khách 1 (chặng ngắn, chịu đi vòng & đi bộ):** `P_1 = 45.000 đ`, chịu `detour_1 = 0,30` và đi bộ `walk_ratio_1 = 0,20` $\implies 1 + 1,0 \times 0,30 + 2,0 \times 0,20 = 1,70 \implies w_1 = 45.000 \times 1,70 = 76.500$.
- **Khách 2, 3, 4 (chặng dài, đi thẳng):** Mỗi người có `P_i = 205.000 đ`, `detour_i = 0`, `walk_ratio_i = 0` $\implies w_{2,3,4} = 205.000$.
- Tổng $\sum_{i=1}^4 P_i = 660.000$ đ, tổng trọng số $\sum_{j=1}^4 w_j = 691.500$.
- Biên cá nhân với $d_{\min} = 0,20, d_{\max} = 0,60, \text{BASE} = 20.000$ đ:
  - Khách 1: $\text{Floor}_1 = \max(20.000, 0,40 \times 45.000) = \mathbf{20.000\text{ đ}}$, $\text{Cap}_1 = 0,80 \times 45.000 = \mathbf{36.000\text{ đ}}$.
  - Khách 2, 3, 4: $\text{Floor}_{2,3,4} = \max(20.000, 0,40 \times 205.000) = \mathbf{82.000\text{ đ}}$, $\text{Cap}_{2,3,4} = 0,80 \times 205.000 = \mathbf{164.000\text{ đ}}$.
  - Tổng cận dưới: $\sum_{i=1}^4 \text{Floor}_i = 20.000 + 3 \times 82.000 = \mathbf{266.000\text{ đ}}$; Tổng cận trên: $\sum_{i=1}^4 \text{Cap}_i = 36.000 + 3 \times 164.000 = \mathbf{528.000\text{ đ}}$.

1. **Trường hợp 16.2A — Khả thi trong miền hai cận ($\text{PlanFare} = 280.000\text{ đ} \in [266.000, 528.000]$):**
   - Tổng tiết kiệm $S = 660.000 - 280.000 = 380.000$ đ.
   - Nếu không có cận dưới `Floor_1`: Khách 1 bị phân bổ $\text{Fare\_unbounded}(1) = 45.000 - 380.000 \times \frac{76.500}{691.500} = 45.000 - 42.039,05 = \mathbf{2.960,95\text{ đ}} < \text{BASE} = 20.000$ đ (và nếu hệ số bất tiện của Khách 1 là $2,00$ thì $\text{Fare\_unbounded}(1) = \mathbf{-3.510,64\text{ đ}} < 0$!).
   - Khi chạy Thuật toán phân bổ hai cận Mục 15.3.4:
     - Điều kiện khả thi `(F1, F2, F3)` thỏa mãn nghiêm ngặt: $266.000 \le 280.000 \le 528.000$ ✓.
     - Khách 1 được kẹp ở đúng cận dưới $\text{Fare\_exact}(1) = \text{Floor}_1 = \mathbf{20.000,00\text{ đ}} \to \text{thu }\mathbf{20.000\text{ đ}}$ (giảm $55,56\%$).
     - Phần chi phí còn lại $\text{RemFare} = 280.000 - 20.000 = 260.000$ đ được chia đều cho Khách 2, 3, 4: mỗi người có $\text{Fare\_exact}(2,3,4) = \mathbf{86.666,67\text{ đ}} \in [\text{Floor}_{2,3,4} = 82.000, \; \text{Cap}_{2,3,4} = 164.000] \to \text{thu }\mathbf{86.000\text{ đ}}$.
     - Tổng $\sum_{i=1}^4 \text{Fare\_exact}(i) = 20.000 + 3 \times 86.666,67 = 280.000,00\text{ đ} == \text{PlanFare}$, và mọi hành khách đều nằm nghiêm ngặt trong $[\text{Floor}_i, \text{Cap}_i]$ ✓!

2. **Trường hợp 16.2B — Minh họa trường hợp không tồn tại nghiệm trong $[\text{Floor}_i, \text{Cap}_i]$ ($\text{PlanFare} = 220.000\text{ đ} < \sum \text{Floor}_i = 266.000\text{ đ}$):**
   - Nếu $\text{PlanFare} = 220.000$ đ (như phản ví dụ gốc của Revision 8 làm $\text{Fare\_unbounded}(1) = -3.676,79$ đ), ta có $\text{TargetFare} = 220.000\text{ đ} < \sum_{i=1}^4 \text{Floor}_i = 266.000$ đ (vi phạm điều kiện khả thi cận dưới `(F2)` vì ngay cả khi cả 4 khách cùng trả mức sàn $\text{Floor}_i$ thì tổng tiền đã là $266.000\text{ đ} > 220.000$ đ).
   - Theo quy tắc tất định tại Mục 15.3.3:
     - Ở chế độ mặc định Baseline (`on_lower_bound_infeasible = "REJECT"`), thuật toán trả về **`INFEASIBLE_LOWER_BOUND`** và loại bỏ ứng viên này để bảo toàn tuyệt đối Cổng `G06` ($\text{Fare\_exact}(i) \ge \text{Floor}_i$).
     - Nếu chủ dự án bật chế độ tùy chọn `on_lower_bound_infeasible = "CLAMP_TO_BASE"` (cho phép hạ sàn về `BASE = 20.000 đ` khi chuyến siêu tiết kiệm), thuật toán kẹp Khách 1 ở `20.000 đ` và chia cho Khách 2, 3, 4 mỗi người `66.666,67 đ` (`thu 66.000 đ`).

## 16.3. Kiểm chứng Kịch bản biên #2: Chèn khách C khi khách B đã khóa giá (`pool_lock_point`)

Tiếp nối ví dụ Mục 16.1: Xe đón A (km 0), đón B (km 5). Tại km 11,5 (còn 2,5 km < 3 km là tới Nguyễn Trãi), **Khách B chạm `pool_lock_point`**:
- Hệ thống khóa `price_status(B) = MATCHED_LOCKED` với `Fare_exact(B) = 105.195,74 đ` và `final_price(B) = 105.000 đ` (gọi lệnh hoàn chênh lệch ký quỹ cho B trên chuỗi khối).
- Tại km 12,0, trong khi Khách A vẫn còn `5,5 km` (> 3 km, nên A vẫn ở trạng thái `POOL_SEARCHING` với `Fare_exact_old(A) = 143.304,26 đ`), hệ thống xét chèn thêm **Khách C** (đi từ Ngã Tư Sở đến Láng Hạ, `P_C = 64.000 đ`, `Cap_C = 0,80 × 64.000 = 51.200 đ`).
- Giả sử việc đón/trả C làm `PlanFare` toàn chuyến tăng từ `248.500 đ` lên `288.500 đ` ($\Delta \text{PlanFare} = +40.000 \text{ đ} \le \text{Cap}_C = 51.200 \text{ đ}$ ✓).
- Áp dụng **Hệ 6 điều kiện đầy đủ `D1–D6` tại Mục 15.5**:
  1. **Kiểm tra `D1` & `D2`:** Kế hoạch đang ở `PLAN_OPEN_SEARCHING`, $U_{\text{old}} = \{A\} \ne \emptyset$, đoạn đi của C giao với A. Đóng băng B ($L = \{B\}$): $\text{Fare\_exact}(B) = 105.195,74$ đ, $\text{final\_price}(B) = 105.000$ đ. Chi phí mục tiêu cần chia cho tập chưa khóa $U = \{A, C\}$ là:
     $$\text{TargetFare}_U = 288.500 - 105.195,74 = 183.304,26\text{ đ}$$
  2. **Kiểm tra `D3` (Khả thi cận trên) & `D4` (Khả thi cận dưới) trên $U = \{A, C\}$:**
     - Cận trên động: $\text{DynamicCap}_A = 143.304,26$ đ, $\text{Cap}_C = 51.200$ đ $\implies \sum_{m \in U} \text{DynamicCap}_m = 194.504,26\text{ đ} \ge \text{TargetFare}_U = 183.304,26$ đ (tương đương $\Delta\text{PlanFare} = 40.000 \le \text{Cap}_C = 51.200$ đ) ✓.
     - Cận dưới: $\text{Floor}_A = 77.600$ đ, $\text{Floor}_C = \max(20.000, 0,40 \times 64.000) = 25.600$ đ $\implies \sum_{m \in U} \text{Floor}_m = 103.200\text{ đ} \le \text{TargetFare}_U = 183.304,26$ đ ✓.
  3. **Kiểm tra `D5` (Phân bổ hai cận, làm tròn và kiểm tra Cổng 2 sau làm tròn):**
     - Tổng giá tham chiếu trên $U$ là $P_A + P_C = 194.000 + 64.000 = 258.000$ đ $\implies S_U = 258.000 - 183.304,26 = 74.695,74$ đ.
     - Với $\text{detour}_A = 0,28, \text{detour}_C = 0,05$: $w_A = 248.320, w_C = 67.200 \implies \text{Fare\_exact}^{\text{new}}(A) = 135.228,10 \text{ đ} \in [77.600, 143.304,26]$ (giá thu của A giảm tiếp từ `143.000 đ` xuống **`135.000 đ`**!) và $\text{Fare\_exact}^{\text{new}}(C) = 48.076,16 \text{ đ} \in [25.600, 51.200]$ (C thu **`48.000 đ`**, giảm $25\%$!).
     - Bảo toàn tổng trước làm tròn: $105.195,74 + 135.228,10 + 48.076,16 = 288.500,00 \text{ đ} == \text{PlanFare\_new}$ ✓.
     - Tổng thực thu sau làm tròn: $\sum \text{Fare\_charged} = 105.000 + 135.000 + 48.000 = 288.000$ đ $\implies \text{DriverPayout}(\text{Plan}') = 0,85 \times 288.000 = 244.800$ đ (với $T_{\text{plan}}' = 60$ phút $\implies \text{DriverHourlyRate} = 244.800\text{ đ/giờ} \ge 232.800\text{ đ/giờ}$ ✓).

---

# 17. THU NHẬP TÀI XẾ KHI GHÉP, QUY TẮC LÀM TRÒN VÀ ĐỐI SOÁT PHẦN LẺ

## 17.1. Biểu phí hoa hồng và đóng góp Quỹ bảo đảm

```text
Taxi bao xe nội đô (CAR_URBAN_PRIVATE) : Hoa hồng nền tảng c_private = 20% (Tài xế nhận 80%)
Taxi ghép nội đô (CAR_URBAN_POOL)      : Hoa hồng gộp c_pool        = 15% (Tài xế nhận 85%)
                                         Trong 15% đó:
                                           - 12% là doanh thu ròng của nền tảng (platform_net_fee)
                                           -  3% chuyển vào Quỹ bảo đảm ghép (fund_contribution)
```

## 17.2. Quy tắc hạch toán hoa hồng trên Tổng tiền thực thu sau làm tròn (`[ACCEPTED]` — D-51 / O-05)

- **Làm rõ mâu thuẫn của Revision 8:** Trong Revision 8, Mục 15.4 ghi *"Phần lẻ làm tròn nền tảng chịu"*, nhưng ở Mục 17 con số tài xế nhận trong ví dụ ghép A+B lại là `210.800 đ` — tức được tính bằng $85\% \times (\text{Fare\_charged}_A + \text{Fare\_charged}_B) = 85\% \times 248.000 \text{ đ}$ (chứ không phải $85\% \times \text{PlanFare } 248.500 \text{ đ} = 211.225 \text{ đ}$).
- **Quy tắc chuẩn hóa thống nhất trong Revision 9 (`[ACCEPTED]`):**
  Để đồng nhất 100% giữa bảng số liệu Mục 17, sổ cái CSDL (`driver_payouts`, `fund_ledger`) và hàm `releasePayment` trên hợp đồng thông minh (nơi hợp đồng chỉ nắm giữ đúng số tiền thực thu `Fare_charged(i)` sau khi đã hoàn phần chênh lệch cho khách), **mọi tỷ lệ phân chia doanh thu (85% tài xế, 12% nền tảng, 3% Quỹ bảo đảm) đều được tính trực tiếp trên số tiền thực thu đã làm tròn `Fare_charged(i)` của từng booking**:

  ```text
  Với mỗi booking i ghép thành công (MATCHED_LOCKED):
      driver_base_amount(i)  = 0,85 × Fare_charged(i)
      platform_net_amount(i) = 0,12 × Fare_charged(i)
      fund_contribution(i)   = 0,03 × Fare_charged(i)
      Tổng cộng              = 1,00 × Fare_charged(i)   (Khớp 100% số nguyên đồng Việt Nam!)
  ```
  - **Ưu điểm tuyệt đối của quy tắc này:** Vì `Fare_charged(i)` luôn là bội số nguyên của `1.000 đ`, khi nhân với `0,85`, `0,12` và `0,03`, kết quả **luôn là một số nguyên chẵn chục đồng** (ví dụ: với `Fare_charged(A) = 143.000 đ` $\implies$ Tài xế: `121.550 đ`, Nền tảng: `17.160 đ`, Quỹ: `4.290 đ`; với `Fare_charged(B) = 105.000 đ` $\implies$ Tài xế: `89.250 đ`, Nền tảng: `12.600 đ`, Quỹ: `3.150 đ`). Không bao giờ xuất hiện số thập phân lẻ xu nào trên cả PostgreSQL lẫn Smart Contract!
  - Khoản chênh lệch làm tròn `rounding_absorbed(i) = Fare_exact(i) - Fare_charged(i)` (tổng `500 đ` trong ví dụ A+B) là phần giảm trực tiếp từ `PlanFare` xuống tổng thực thu, được ghi nhận vào cột `rounding_absorbed` của bảng `ride_participants` để phục vụ kiểm toán đối soát:
    $$\sum_{i \in N} \text{Fare\_charged}(i) + \sum_{i \in N} \text{rounding\_absorbed}(i) == \text{PlanFare}$$

## 17.3. Bảng đối sánh thu nhập của tài xế (Ví dụ chuẩn Mục 16.1)

| Phương án vận hành của tài xế | Tổng tiền thu từ khách | Tài xế thực nhận | Thời gian chạy | Thu nhập / giờ | Thu nhập / km |
|---|---:|---:|---:|---:|---:|
| **Chỉ chở riêng Khách A (Bao xe đơn)** | `194.000 đ` | **155.200 đ** *(80%)* | `40 phút` | `232.800 đ/giờ` | `11.086 đ/km` |
| **Chỉ chở riêng Khách B (Bao xe đơn)** | `133.000 đ` | **106.400 đ** *(80%)* | `28 phút` | `228.000 đ/giờ` | `11.822 đ/km` |
| **Chạy ghép Khách A + Khách B** | `248.000 đ` *(143k + 105k)* | **210.800 đ** *(85%)* | `52 phút` | **243.231 đ/giờ** | **12.046 đ/km** |

Nhờ Cổng kiểm tra 2A & 2B tại Mục 14.2, mọi kế hoạch ghép hợp lệ được sinh ra đều bảo đảm hai bất biến cho tài xế:
1. **Bất biến tổng thu nhập chuyến:** `DriverPayout(ghép) > max_i DriverPayout(xe đơn i)` (`210.800 đ > 155.200 đ`, tăng thêm `+35,8%` thu nhập chuyến).
2. **Bất biến tốc độ thu nhập theo giờ:** `DriverHourlyRate(ghép) >= max_i DriverHourlyRate(xe đơn i)` (`243.231 đ/giờ >= 232.800 đ/giờ`).

---

# 18. CƠ CHẾ CHIA SẺ RỦI RO BA BÊN KHI KHÔNG GHÉP ĐƯỢC, CHỐNG PHÁ GHÉP VÀ KHUNG CHÍNH SÁCH HỦY

## 18.1. Lý do loại bỏ mô hình phụ phí cố định +20% cũ

Trong các thiết kế thế hệ cũ (như Rev5), khi chuyến ghép không tìm được người đi cùng, hành khách bị thu thêm phụ phí cố định +20% trên giá ghép và chuyển toàn bộ cho tài xế. Cơ chế đó có ba khuyết tật nghiêm trọng:
1. **Đẩy 100% rủi ro thị trường sang hành khách:** Việc không tìm được khách thứ hai phụ thuộc vào mật độ cung – cầu của nền tảng, nhưng khách lại phải gánh toàn bộ chi phí.
2. **Khuyến khích ngược (Perverse Incentive / Moral Hazard):** Nếu tài xế nhận được khoản thưởng phụ phí mà không phải rẽ vòng hay dừng đón thêm người thứ hai, tài xế sẽ có động cơ tìm cách né tránh hoặc từ chối khách ghép.
3. **Không gắn với chi phí cơ hội thực tế:** Phụ phí phần trăm cứng có thể làm tài xế nhận cao hơn hoặc thấp hơn thu nhập chạy xe đơn.

## 18.2. Năm nguyên tắc của cơ chế chia sẻ rủi ro ba bên (`[ACCEPTED]` — D-09 đến D-15)

```text
P1 (Bảo toàn thu nhập cơ hội của tài xế):
    Khi không có khách ghép do yếu tố thị trường, tài xế nhận tổng cộng ĐÚNG BẰNG thu nhập chạy bao xe đơn
    trên cùng lộ trình của khách đó (không bị lỗ, nhưng tuyệt đối không được lời hơn chạy đơn).
P2 (Chia sẻ rủi ro công bằng cho khách):
    Khách chỉ chịu một phần (α = 0,50) khoảng chênh giữa giá trần ghép và giá xe đơn;
    mức giá tối đa khi không ghép được (Unmatched_i) luôn rẻ hơn giá bao xe đơn.
P3 (Nền tảng đồng hành chịu rủi ro):
    Nền tảng chịu phần còn lại thông qua việc giữ mức hoa hồng thấp (15% thay vì 20%)
    và trích Quỹ bảo đảm ghép để bù phần thiếu hụt cho tài xế.
P4 (Trách nhiệm theo hành vi — Fault-based Attribution):
    Bên nào chủ động gây ra việc không ghép được (tài xế từ chối khách ghép hợp lệ, hoặc khách hủy muộn)
    thì bên đó phải gánh chịu thiệt hại tài chính tương ứng.
P5 (Minh bạch tuyệt đối trước khi đặt):
    Cả hai mức trần (Quote_i nếu ghép được và Unmatched_i nếu không ghép được) đều được hiển thị
    và dùng để khóa ký quỹ ngay từ trước khi khách xác nhận đặt xe.
```

## 18.3. Công thức tính `Quote_i`, `Gap_i`, `Unmatched_i` và Khoản bù bảo đảm

Với mỗi booking $i$ có giá tham chiếu $P_i$:

```text
Quote_i     = floor( P_i × (1 - d_min) / 1.000 ) × 1.000       (Trần giá tối đa nếu ghép thành công)
Gap_i       = P_i - Quote_i                                    (Khoảng chênh giữa xe đơn và trần ghép)
Unmatched_i = floor( (Quote_i + α × Gap_i) / 1.000 ) × 1.000   (Giá thu nếu kết thúc ở UNMATCHED_LOCKED)

Tham số mặc định: d_min = 0,20 ; α = 0,50 (khách chịu một nửa khoảng chênh)
```

Hạch toán cho tài xế và Quỹ bảo đảm khi booking $i$ kết thúc ở trạng thái không có người ghép do thị trường (`unmatched_cause == NO_COMPATIBLE`):
```text
TargetDriverPayout(i) = P_i × (1 - c_private)                   = 0,80 × P_i
DriverFromPassenger(i)= Unmatched_i × (1 - c_pool)              = 0,85 × Unmatched_i
PlatformCommission(i) = Unmatched_i × c_pool                    = 0,15 × Unmatched_i (không trích 3% vào Quỹ)
GuaranteePayout(i)    = max( 0, TargetDriverPayout(i) - DriverFromPassenger(i) )
TotalDriverPayout(i)  = DriverFromPassenger(i) + GuaranteePayout(i) == TargetDriverPayout(i)
```

## 18.4. Ví dụ định lượng: Khách A đặt Taxi ghép nội đô nhưng không có khách ghép tương thích

Với Khách A (Phenikaa → Đống Đa, `14 km, 40 phút`, $P_A = 194.000$ đ):
```text
Quote_A              = floor( 194.000 × 0,80 / 1.000 ) × 1.000 = floor(155.200 / 1.000) × 1.000 = 155.000 đ
Gap_A                = 194.000 - 155.000                                                        =  39.000 đ
Unmatched_A          = floor( (155.000 + 0,50 × 39.000) / 1.000 ) × 1.000 = floor(174.500)      = 174.000 đ
TargetDriverPayout   = 194.000 × 0,80                                                           = 155.200 đ
DriverFromPassenger  = 174.000 × 0,85                                                           = 147.900 đ
GuaranteePayout      = 155.200 - 147.900                                                        =   7.300 đ
PlatformCommission   = 174.000 × 0,15                                                           =  26.100 đ
```

| Chủ thể | Số tiền thu / chi trong kịch bản Unmatched | So sánh với kịch bản chạy Bao xe đơn (`194.000 đ`) |
|---|---|---|
| **Hành khách A** | Trả **174.000 đ** *(được hoàn lại `0 đ` từ mức trần ký quỹ `174.000 đ`)* | Rẻ hơn bao xe đơn **20.000 đ (-10,31%)**; chỉ trả thêm `19.000 đ` so với trần giá ghép `155.000 đ`. |
| **Tài xế** | Nhận `147.900 đ` từ khách + **7.300 đ** từ Quỹ bảo đảm = **155.200 đ** | **Bằng chính xác 100%** thu nhập chạy bao xe đơn (`155.200 đ`). |
| **Nền tảng & Quỹ** | Thu hoa hồng `26.100 đ`, Quỹ chi bảo đảm `7.300 đ` → Ròng giữ lại `18.800 đ` | Giảm thu `20.000 đ` so với mức hoa hồng bao xe đơn (`38.800 đ`). |

Khoảng chênh `Gap_A = 39.000 đ` được phân bổ minh bạch: **Khách chịu `19.000 đ`, Nền tảng & Quỹ chịu `20.000 đ`, Tài xế chịu `0 đ`**.

## 18.5. Ma trận quy kết trách nhiệm theo nguyên nhân (`unmatched_cause`)

| Tình huống thực tế | Mã `unmatched_cause` | Giá Khách A trả | Tài xế nhận từ khách | Quỹ bảo đảm chi | Tổng Tài xế nhận & Hệ quả |
|---|---|---|---|---:|---|
| **1. Không có khách ghép tương thích trên thị trường** | `NO_COMPATIBLE` | **174.000 đ** (`Unmatched_A`) | `147.900 đ` | **7.300 đ** | **155.200 đ** (Bằng xe đơn; rủi ro thị trường chia ba bên). |
| **2. Tài xế từ chối khách ghép tương thích không có lý do an toàn** | `DRIVER_DECLINED` | **155.000 đ** (`Quote_A`, không thu phụ phí) | `131.750 đ` *(85% × 155k)* | **0 đ** *(Cắt bảo đảm)* | **131.750 đ** (Tài xế **thiệt 23.450 đ** so với chạy đơn → triệt tiêu hoàn toàn động cơ phá ghép). |
| **3. Khách ghép B hủy TRƯỚC khi A chạm `pool_lock_point`** | `CORIDER_CANCELLED_EARLY` | Tính lại theo thực tế tại `pool_lock_point` của A ($\le 174.000$ đ) | Theo kết quả chốt tại `pool_lock_point` | Theo kết quả chốt | Khách B chịu phí hủy (Mục 18.7); tiền phạt hủy của B được nạp vào Quỹ bảo đảm để bù rủi ro cho chuyến của A. |
| **4. Khách ghép B hủy SAU khi A đã chạm `pool_lock_point` (`MATCHED_LOCKED`)** | `CORIDER_CANCELLED_LATE` | **Giữ nguyên giá đã khóa** (ví dụ `143.000 đ`) | `85% × 143.000 = 121.550 đ` + phần phạt hủy của B | Quỹ bù phần thiếu để tài xế đạt tối thiểu `155.200 đ` | Không bao giờ đẩy rủi ro hủy muộn của B sang cho A đã khóa giá. |
| **5. Khách A tự ý từ chối đi chung với B (ngoài tùy chọn đã khai ở Mục 6)** | `PASSENGER_REJECTED_POOL` | **174.000 đ** (`Unmatched_A`) | `147.900 đ` | **7.300 đ** | **155.200 đ** (Coi như A tự nguyện chuyển sang đi một mình ở mức trần Pool). |

## 18.6. Cơ chế chống phá ghép: Nhận chuyến Pool là cam kết tự động nhận khách tương thích

Khi tài xế bật `pool_enabled = true` và bấm nhận một booking khởi tạo kế hoạch `CAR_URBAN_POOL`, tài xế đã đồng ý về mặt giao thức rằng hệ thống **được quyền tự động chèn thêm (`CORIDER_AUTO_ADDED`)** các booking ghép tiếp theo mà không cần chờ tài xế bấm `ACCEPT` lại, miễn là kế hoạch sau khi chèn thỏa mãn toàn bộ ngưỡng tài xế đã tự khai báo (`max_additional_pickups`, `max_driver_detour_km`, `max_driver_detour_min`, `vehicle.capacity`) và thỏa mãn Cổng sinh lời Mục 14.2.

Nếu tài xế chủ động bấm từ chối khách ghép vừa được thêm qua API `POST /api/rides/{id}/coriders/{booking_id}/decline`, hệ thống kiểm tra `reason_code`:
- Chỉ các mã lý do bất khả kháng có xác nhận (`VEHICLE_BREAKDOWN`, `PASSENGER_SAFETY_VIOLATION`, `OVER_LUGGAGE_LIMIT`) mới được miễn trừ (nhưng xe cũng phải đóng nhận khách mới).
- Mọi lý do khác đều bị ghi nhận sự kiện `DRIVER_DECLINED_COMPATIBLE_CORIDER` và áp dụng ngay dòng thứ 2 của **bảng Mục 18.5** (khách đang trên xe chỉ trả tối đa `Quote_i`, tài xế bị cắt 100% khoản bù từ Quỹ bảo đảm).

## 18.7. Khung tham số Chính sách hủy chuyến và Khách không đến (`Cancellation & No-Show Policy` — `[ACCEPTED]` D-52)

Để các luồng hoàn tiền trong Mục 18.5, Mục 27, Mục 29 và hàm `cancelRide` / `refundPayment` trên hợp đồng thông minh (Mục 80.2) hoạt động hoàn toàn xác định ngay trong phạm vi MUST (M5, M12), hệ thống quy định bảng tham số phí hủy chuẩn như sau:

| Nhóm dịch vụ | Thời điểm hủy / Sự kiện | Mức phí phạt hủy (`CancelFee`) | Phân bổ khoản phí phạt hủy | Xử lý ký quỹ On-chain (`escrow_status`) |
|---|---|---|---|---|
| **Nội đô (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`)** | Trước khi tài xế nhận offer (`HELD`) hoặc trong `120 giây` đầu sau `CONFIRMED` (khi tài xế chưa đến điểm đón) | `0 đ` (`0%`) | Không phát sinh | Hoàn `100%` số tiền ký quỹ (`REFUNDED`). |
| **Nội đô (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`)** | Sau `120 giây` từ khi `CONFIRMED` HOẶC khách không đến (`NO_SHOW` sau 5 phút tài xế chờ tại điểm đón) | `min(20.000 đ, 20% × Fare_charged)` | `80%` cho Tài xế (bù xăng/thời gian di chuyển đến đón), `20%` cho Nền tảng | Giải ngân `CancelFee` cho Tài xế/Nền tảng, hoàn phần dư `deposited - CancelFee` cho khách. |
| **Taxi ghép nội đô (`CAR_URBAN_POOL`)** | Hủy muộn sau `120 giây` từ khi `CONFIRMED` hoặc `NO_SHOW` | `20% × Quote_i` (ví dụ `31.000 đ` với khách A) | Nếu xe chưa có khách khác: `85%` cho Tài xế, `15%` vào **Quỹ bảo đảm**.<br>Nếu xe đang có khách khác: `50%` cho Tài xế, `50%` nạp vào **Quỹ bảo đảm** (để bù giá cho khách còn lại theo dòng 3–4 bảng 18.5). | Khấu trừ `CancelFee` từ tiền ký quỹ của người hủy, hoàn phần còn lại. |
| **Taxi bao xe liên tỉnh (`CAR_INTERCITY_PRIVATE`)** | Trước giờ đón `> 2 giờ` (với hẹn trước) hoặc trong `120 giây` đầu (với đặt đi ngay) | `0 đ` (`0%`) | Không phát sinh | Hoàn `100%` ký quỹ. |
| **Taxi bao xe liên tỉnh (`CAR_INTERCITY_PRIVATE`)** | Trong vòng `<= 2 giờ` trước giờ đón hoặc `NO_SHOW` | `20% × IntercityPrivateFare` | `85%` cho Tài xế, `15%` cho Nền tảng | Khấu trừ `20%`, hoàn `80%` cho khách. |
| **Taxi ghép liên tỉnh (`CAR_INTERCITY_POOL`)** | Trước mốc chốt chuyến `T−72h` (hoặc hủy trong 2 giờ sau khi bị gộp chuyến ở Mục 30) | `0 đ` (`0%` — Hủy miễn phí) | Không phát sinh | Hoàn `100%` ký quỹ (`REFUNDED`). |
| **Taxi ghép liên tỉnh (`CAR_INTERCITY_POOL`)** | Sau khi chuyến đã chốt: từ `T−72h` đến `T−24h` | `50% × BookingPrice` | `90%` khoản phạt chuyển cho Tài xế chuyến đó (để bù ghế trống giúp chuyến **vẫn tiếp tục chạy** mà không hủy các khách còn lại), `10%` cho Nền tảng. | Khấu trừ `50%`, hoàn `50%` cho khách hủy. |
| **Taxi ghép liên tỉnh (`CAR_INTERCITY_POOL`)** | Sau mốc chốt thứ tự đón `T−24h` đến giờ khởi hành `T` hoặc `NO_SHOW` | `100% × BookingPrice` | `90%` cho Tài xế, `10%` cho Nền tảng (chuyến xe vẫn khởi hành bình thường cho các khách còn lại). | Giải ngân như ghế đã chạy, hoàn `0 đ`. |
| **Mọi dịch vụ — Lỗi do Tài xế hủy (`CANCELLED_BY_DRIVER`)** | Tài xế tự hủy sau khi đã `CONFIRMED` hoặc gặp sự cố kỹ thuật giữa đường | Khách chịu `0 đ` (`0%`) | Tài xế bị trừ điểm độ tin cậy (`driver_reliability_stats`) trừ trường hợp sự cố có xác nhận của Admin. | Hoàn `100%` ký quỹ cho mọi hành khách bị ảnh hưởng (`REFUNDED`). |

---

# 19. QUỸ BẢO ĐẢM GHÉP: CÔNG THỨC HÒA VỐN TỔNG QUÁT VÀ PHÂN TÍCH ĐỘ NHẠY

## 19.1. Nguồn thu, Nguồn chi và Đơn vị thống kê chuẩn (`[ACCEPTED]` — D-19)

Quỹ bảo đảm ghép (`fund_ledger`) là một sổ cái tài chính độc lập (được phản ánh đồng bộ vào biến trạng thái `guaranteeFundBalance` trên hợp đồng thông minh ở Mục 80.3):
- **Đơn vị hạch toán cơ sở:** Tính theo từng **`booking` của dịch vụ `CAR_URBAN_POOL` hoàn thành chuyến đi** (không đánh đồng với số chuyến xe `ride_plan`, vì 1 chuyến xe ghép thành công chứa từ $2$ đến $4$ bookings cùng đóng góp vào Quỹ).
- **Nguồn thu (`CONTRIBUTION`):** Trích `fund_rate = 3%` từ giá thu thực tế `Fare_charged(i)` của mỗi booking kết thúc ở trạng thái `MATCHED_LOCKED` (lấy từ 15% tổng hoa hồng ghép của nền tảng). Ngoài ra Quỹ còn nhận phần phí phạt hủy từ các booking Pool hủy muộn (Mục 18.7).
- **Nguồn chi (`GUARANTEE_PAYOUT`):** Chi trả khoản bù `GuaranteePayout(i)` cho tài xế đối với mỗi booking kết thúc ở trạng thái `UNMATCHED_LOCKED` có nguyên nhân `unmatched_cause == NO_COMPATIBLE`.

## 19.2. Công thức điều kiện hòa vốn tổng quát theo kỳ vọng quần thể (`p*_booking` vs `p*_ride`)

Gọi:
- $p_{\text{booking}} \in [0, 1]$ là **tỷ lệ booking `CAR_URBAN_POOL` kết thúc ở trạng thái ghép thành công (`MATCHED_LOCKED`)** trên tổng số booking Pool hoàn thành.
- $\mathbb{E}[\text{Thu}] = \text{fund\_rate} \times \mathbb{E}[\text{Fare\_charged} \mid \text{MATCHED}]$ là số tiền đóng góp trung bình vào Quỹ của một booking ghép thành công.
- $\mathbb{E}[\text{Chi}] = \mathbb{E}[\text{GuaranteePayout} \mid \text{UNMATCHED, NO\_COMPATIBLE}]$ là số tiền Quỹ phải chi bù trung bình cho một booking không ghép được.

Điều kiện để Quỹ bảo đảm tự cân bằng (không âm trong dài hạn) là:
```text
p_booking × E[Thu] >= (1 - p_booking) × E[Chi]

⇒ Ngưỡng tỷ lệ booking ghép thành công tối thiểu (p*_booking):
   p*_booking = E[Chi] / ( E[Chi] + E[Thu] )
```

**Quan hệ chuyển đổi sang tỷ lệ chuyến xe ghép thành công (`p*_ride`):**
Nếu trung bình một chuyến xe ghép thành công phục vụ $\bar{m}$ bookings độc lập ($\bar{m} \ge 2$, ví dụ $\bar{m} = 2,15$), trong khi một chuyến xe không ghép được chỉ chứa $1$ booking, thì tỷ lệ **chuyến xe Pool** cần tìm được người ghép (`p*_ride`) để Quỹ hòa vốn thấp hơn đáng kể so với `p*_booking`:
```text
p*_ride = E[Chi] / ( E[Chi] + m_bar × E[Thu] )
(Với m_bar = 2,0: p*_booking = 2 × p*_ride / (1 + p*_ride))
```

### Đối chiếu số học trên ví dụ chuẩn (Khách A = `194.000 đ`, Khách B = `133.000 đ`):
1. **Nếu tính riêng cho phân khúc chuyến dài như Khách A** ($\mathbb{E}[\text{Chi}_A] = 7.300$ đ) kết hợp với mức thu trung bình của cặp A+B ($\mathbb{E}[\text{Fare\_charged}] = (143.000 + 105.000)/2 = 124.000 \text{ đ} \implies \mathbb{E}[\text{Thu}] = 3\% \times 124.000 = 3.720$ đ):
   ```text
   p*_booking (chỉ xét Chi của A) = 7.300 / (7.300 + 3.720) = 66,24% (~66,2%)
   ```
2. **Nếu tính đồng nhất trên cùng quần thể gồm 50% khách loại A (`194.000 đ`) và 50% khách loại B (`133.000 đ`):**
   - Nếu B không ghép được: $\text{Quote}_B = 106.000$ đ, $\text{Gap}_B = 27.000$ đ, $\text{Unmatched}_B = 119.000$ đ; tài xế nhận từ B = $0,85 \times 119.000 = 101.150$ đ; mục tiêu xe đơn của B = $0,80 \times 133.000 = 106.400$ đ $\implies \text{Chi}_B = 106.400 - 101.150 = 5.250$ đ.
   - Chi trung bình quần thể: $\mathbb{E}[\text{Chi}_{AB}] = (7.300 + 5.250) / 2 = \mathbf{6.275\text{ đ/booking}}$.
   - Thu trung bình quần thể: $\mathbb{E}[\text{Thu}_{AB}] = 3\% \times 124.000 = \mathbf{3.720\text{ đ/booking}}$.
   - Khi đó:
     ```text
     p*_booking (đồng nhất quần thể A+B) = 6.275 / (6.275 + 3.720) = 62,78% (~62,8%)
     p*_ride    (tính theo chuyến, m=2)  = 6.275 / (6.275 + 2 × 3.720) = 45,75% (~45,8%)
     ```
   *Kết luận:* Chỉ cần khoảng **45,8% số chuyến xe Pool khởi tạo tìm được người ghép chung** (tương đương **62,8% số booking Pool được ghép**), Quỹ bảo đảm sẽ tự cân bằng hoàn toàn mà không cần nền tảng bù lỗ!

## 19.3. Phân tích độ nhạy và Đòn bẩy điều hành khi mật độ nhu cầu thấp

Khi vận hành ở các khu vực ngoại thành hoặc khung giờ thấp điểm có tỷ lệ ghép thực tế $p_{\text{actual}} < p^*$, nền tảng có 3 đòn bẩy tham số (`d_min`, `α`, `fund_rate`) để giảm mức chi bảo đảm và hạ điểm hòa vốn `p*`:

| Kịch bản cấu hình `(d_min, α, fund_rate)` | `Quote_A` (Ghép tối đa) | `Unmatched_A` (Không ghép) | Chi bảo đảm `Chi_A` / `E[Chi_AB]` | Thu Quỹ TB `E[Thu_AB]` | Điểm hòa vốn `p*_booking` (theo A / theo AB) | Điểm hòa vốn `p*_ride` (AB, `m=2`) |
|---|---|---|---|---:|---|---|
| **Cấu hình chuẩn (`20%`, `0.50`, `3%`)** | `155.000 đ` | `174.000 đ` | `7.300 đ` / `6.275 đ` | `3.720 đ` | **66,2%** *(A)* / **62,8%** *(AB)* | **45,8%** |
| **Hạ cam kết giảm giá (`15%`, `0.50`, `3%`)** | `164.000 đ` | `179.000 đ` | `3.050 đ` / `2.450 đ` | `3.930 đ` | **43,7%** *(A)* / **38,4%** *(AB)* | **23,8%** |
| **Hạ cam kết giảm giá (`10%`, `0.50`, `3%`)** | `174.000 đ` | `184.000 đ` | `0 đ` / `0 đ` *(vì 85%×184k > 155,2k)* | `4.170 đ` | **0,0%** *(Quỹ luôn dương)* | **0,0%** |
| **Tăng chia sẻ của khách (`20%`, `0.65`, `3%`)** | `155.000 đ` | `180.000 đ` | `2.200 đ` / `2.025 đ` | `3.720 đ` | **37,2%** *(A)* / **35,2%** *(AB)* | **21,4%** |
| **Tăng trích lập Quỹ (`20%`, `0.50`, `5%`)** | `155.000 đ` | `174.000 đ` | `7.300 đ` / `6.275 đ` | `6.200 đ` | **54,1%** *(A)* / **50,3%** *(AB)* | **33,6%** |

**Hệ quả thiết kế nối với mô hình AI `P(match)` (PHẦN VI):**
- Ở phạm vi **MUST**: Hệ thống giữ cố định cấu hình chuẩn `(d_min = 0.20, α = 0.50, fund_rate = 0.03)` và ghi nhận trung bình trượt thực nghiệm của `E[Thu]`, `E[Chi]`, `p_actual` so với `p*` trên Dashboard Admin (Mục 62, 63).
- Ở phạm vi **COULD (C3)**: Hệ thống dùng đầu ra của mô hình `P(match)` theo `(zone × khung giờ)` để tự động điều chỉnh chính sách: khung giờ có `P(match) >= 0.65` mở gói cam kết cao `d_min = 20%`; khung giờ có `0.35 <= P(match) < 0.65` áp dụng `d_min = 15%` (điểm hòa vốn chỉ cần `38,4%`); khung giờ vắng có `P(match) < 0.35` áp dụng `d_min = 10%` hoặc chỉ hiển thị xe máy và taxi bao xe.

---

# 20. TRẢI NGHIỆM HIỂN THỊ GIÁ MINH BẠCH VÀ VÒNG ĐỜI GIÁ CỦA BOOKING POOL

## 20.1. Minh họa giao diện thẻ gợi ý Top-K cho Hành khách A

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ [Nhanh nhất · Rẻ nhất]  XE MÁY (BIKE_URBAN)                   81.000 đ  │
│ Đón dự kiến: 07:24 · Đến nơi: ~07:59 (35 phút) · Đi thẳng 1:1           │
├─────────────────────────────────────────────────────────────────────────┤
│ [Đề xuất AI]            TAXI GHÉP NỘI ĐÔ (CAR_URBAN_POOL)  143k – 174k  │
│ • Giá dự kiến khi ghép được : ~143.000 đ (Cam kết tối đa: 155.000 đ)    │
│ • Giá tối đa nếu không ai ghép: 174.000 đ (Vẫn rẻ hơn bao xe 20.000 đ)  │
│ • Đón: 07:26 · Đến tối đa: ~08:20 · Đi vòng tối đa: <= 30%              │
│ • Khả năng ghép thành công ở khung giờ này: CAO                         │
├─────────────────────────────────────────────────────────────────────────┤
│ [Thoải mái nhất]        TAXI BAO XE (CAR_URBAN_PRIVATE)      194.000 đ  │
│ Đón dự kiến: 07:28 · Đến nơi: ~08:08 (40 phút) · Xe 4 chỗ đi riêng      │
└─────────────────────────────────────────────────────────────────────────┘
```

## 20.2. Quy tắc tính Giá ghép dự kiến (`Fare_matched_est`) cho hai loại ứng viên Pool (`[ACCEPTED]` — D-50b)

Khi hiển thị thẻ `CAR_URBAN_POOL` trong Top-K và khi tính `ExpectedPrice` ở Mục 40, hệ thống phân biệt rõ hai trường hợp của ứng viên:
1. **Trường hợp 1 — Ứng viên là kế hoạch Pool đang mở đã có sẵn ít nhất 1 hành khách khác trên xe:**
   - Hệ thống đã chạy thuật toán chèn điểm (Mục 36) và thuật toán phân bổ giá (Mục 15.3) với các hành khách cụ thể đang có trong kế hoạch.
   - Khi đó, `Fare_matched_est(i)` chính là mức giá thu thực tế `Fare_charged(i)` vừa tính được (ví dụ: `143.000 đ` khi ghép A vào kế hoạch của B).
2. **Trường hợp 2 — Ứng viên là một xe taxi đang rảnh (khởi tạo kế hoạch Pool mới, hiện mới chỉ có khách $i$):**
   - Tại thời điểm báo giá, chưa có hành khách thứ hai cụ thể nên chưa có `PlanFare` của 2 người.
   - Hệ thống ước lượng mức giá ghép kỳ vọng điển hình `Fare_matched_est(i)` dựa trên tỷ lệ tiết kiệm trung bình lịch sử của hành lang `(origin_zone, dest_zone, hour_bucket)` (ký hiệu là $\bar{d}_{\text{matched}}$, mặc định cấu hình $\bar{d}_{\text{matched}} = 0,25 \in [d_{\min}, d_{\max}]$):
     ```text
     Fare_matched_est(i) = floor( P_i × (1 - d_matched_typical) / 1.000 ) × 1.000
     (Ví dụ với P_A = 194.000 đ và d_matched_typical = 0,25 → Fare_matched_est(A) = 145.000 đ,
      kèm ghi chú rõ "Trần tối đa nếu ghép được: 155.000 đ").
     ```

## 20.3. Vòng đời các trường giá trên bản ghi `Booking`

```text
pool_quote_price        = Quote_i            (155.000 đ — Trần giá cam kết nếu ghép thành công)
quoted_price_cap        = Unmatched_i        (174.000 đ — Trần nghĩa vụ tài chính tối đa & số tiền ký quỹ)
current_estimated_price : Khởi tạo bằng Fare_matched_est; tự động cập nhật giảm xuống khi ghép được
                          người mới (luôn <= quoted_price_cap)
final_price             : Được khóa bất biến tại thời điểm chạm pool_lock_point (MATCHED_LOCKED
                          hoặc UNMATCHED_LOCKED), dùng để hoàn chênh lệch ký quỹ và giải ngân
```

---

# 21. ĐỘNG CƠ KINH TẾ CỦA TÀI XẾ THAY CHO HẠN NGẠCH QUOTA 4:1

Thay vì ép buộc tài xế phải chạy 1 chuyến ghép sau mỗi 4 chuyến đơn (cơ chế `Quota 4:1` thường dẫn tới việc tài xế tắt ứng dụng hoặc nhận chuyến một cách đối phó), nền tảng sử dụng hệ thống **5 đòn bẩy tương thích khuyến khích (Incentive-Compatible Levers)**:

| Cơ chế khuyến khích | Tác động kinh tế & hành vi đối với tài xế |
|---|---|
| **1. Ưu đãi hoa hồng (`15%` so với `20%`)** | Tài xế giữ lại `85%` doanh thu trên các chuyến ghép thay vì `80%` như chạy đơn. |
| **2. Bảo toàn thu nhập/giờ và tăng thu nhập chuyến (Cổng Mục 14.2)** | Mỗi chuyến ghép hợp lệ luôn mang lại tổng tiền thực nhận và tốc độ thu nhập/giờ cao hơn hoặc bằng chạy xe đơn cùng tuyến. |
| **3. Bảo hiểm rủi ro 100% khi vắng khách (Mục 18.3)** | Nếu thị trường không có người ghép cùng, Quỹ bảo đảm bù phần thiếu để tài xế nhận đúng bằng chạy xe đơn (`155.200 đ`) — nhận Pool hoàn toàn không có rủi ro lỗ. |
| **4. Chế tài cắt bảo đảm khi từ chối khách tương thích (Mục 18.5)** | Nếu tài xế cố tình từ chối khách ghép nằm trong ngưỡng đã khai, tài xế mất bảo đảm và chỉ nhận `131.750 đ` (lỗ `23.450 đ` so với chạy đơn). |
| **5. Điểm thưởng ưu tiên điều phối nhẹ (COULD)** | Tài xế duy trì bật chế độ Pool ổn định được cộng điểm chất lượng hiển thị trong mô hình xếp hạng. |

Chính sách `Quota 4:1` chỉ được giữ lại như một kịch bản đối chứng trong Simulator (hạng mục **C6**, kiểm định Giả thuyết **H8**) để chứng minh bằng số liệu rằng cơ chế động cơ kinh tế tự nguyện mang lại tỷ lệ hoàn thành cao hơn và ít hủy chuyến hơn.

---

# 22. MÁY TRẠNG THÁI CHI TIẾT CỦA TAXI GHÉP NỘI ĐÔ

Kết hợp chặt chẽ với 3 trục trạng thái trực giao ở Mục 9, vòng đời của một kế hoạch ghép (`ride_plans.status`) và trạng thái giá của từng hành khách (`bookings.price_status`) vận hành như sau:

```text
[Trạng thái của Kế hoạch xe ghép — ride_plans.status]
PLAN_CREATED (Có booking đầu tiên CONFIRMED)
  ──► PLAN_OPEN_SEARCHING (Trước khi chạy và đang chạy, còn ghế trống & còn khách chưa khóa)
        ├── (Khi mọi khách trên xe đã chạm pool_lock_point hoặc đủ k_max_stops) ──► PLAN_CLOSED_TO_NEW
        └── (Khi trả xong hành khách cuối cùng S_k)                             ──► PLAN_COMPLETED

[Trạng thái chốt giá của từng Booking thành viên — bookings.price_status]
QUOTED (Lúc tạo ứng viên)
  ──(Khi booking CONFIRMED)──► POOL_SEARCHING
                                  ├── (Tại pool_lock_point: có >= 1 booking độc lập đi chung đoạn)
                                  │       ──► MATCHED_LOCKED (Khóa final_price = Fare_charged_i)
                                  └── (Tại pool_lock_point: không có booking độc lập nào đi chung)
                                          ──► UNMATCHED_LOCKED (Khóa final_price = Unmatched_i,
                                              hoặc = Quote_i nếu do DRIVER_DECLINED)
```

---

# 23. ĐIỂM ĐÓN GẶP NHAU (MEETING POINTS — COULD C9)

## 23.1. Động cơ vận trù học
Tại Hà Nội, việc xe ô tô phải rẽ sâu vào các ngõ nhỏ, phố cụt hoặc quay đầu ở các nút giao phức tạp để đón tận cửa (`door-to-door`) thường làm mất thêm `4–8 phút` và `0,8–1,5 km` đi vòng, khiến kế hoạch ghép dễ bị trượt Cổng Shareability (Mục 14.1) hoặc Cổng thu nhập/giờ của tài xế (Mục 14.2). Nếu hành khách đồng ý đi bộ một quãng ngắn (`100–300 m`) ra điểm đón trên đường trục chính, thời gian kế hoạch $T_{\text{plan}}$ giảm mạnh, giúp tăng tỷ lệ ghép thành công (kiểm định tại Giả thuyết **H7**).

## 23.2. Thuật toán sinh điểm đón ứng viên
```text
Với mỗi hành khách khai báo max_walk_m > 0 (trong khoảng [100 m, 400 m]):
    1. Truy vấn PostGIS tìm các nút/đoạn đường thuộc mạng lưới đường trục chính
       (OSM highway ∈ {primary, secondary, tertiary}) trong bán kính max_walk_m quanh điểm đón gốc.
    2. Lọc an toàn: chỉ giữ các điểm có vỉa hè/điểm dừng đỗ hợp lệ, không nằm giữa cầu vượt, hầm chui,
       hoặc nút giao cấm dừng đỗ.
    3. Chọn tối đa 2 điểm đón trên đường trục có khoảng cách đi bộ ngắn nhất + giữ lại 1 điểm gốc (walk_m = 0).
    → Tối đa 3 điểm đón ứng viên cho mỗi hành khách.
```

## 23.3. Bù đắp công sức đi bộ trong công thức giá và Quy tắc an toàn
- Trọng số phân bổ tiết kiệm ở Mục 15.2 tự động cộng thêm thành phần $\mu \times \text{walk\_ratio}_i$ (với $\mu = 2,0$ và $\text{walk\_ratio}_i = D_{\text{walk}}(i) / D_{\text{direct}}(i)$), đảm bảo người chấp nhận đi bộ ra đường lớn giúp cả chuyến xe tiết kiệm thời gian sẽ được nhận lại mức giảm giá lớn hơn (và vẫn được bảo vệ bởi chặn dưới `Floor_i` ở Mục 15.3).
- **Quy tắc an toàn bắt buộc:** Hệ thống tự động vô hiệu hóa tính năng gợi ý điểm đón đi bộ (`max_walk_m` bị ép về `0`) trong khung giờ ban đêm từ **`22:00` đến `05:00` sáng**, hoặc khi thời tiết đang có mưa lớn (`is_raining == true`), hoặc khi khách mang theo hành lý (`has_luggage == true`).

---

# 24. CHUYẾN QUEN LẶP LẠI HẰNG NGÀY (RECURRING TRIPS — COULD C4)

Nhiều hành khách đô thị có lịch trình đi học, đi làm cố định theo các ngày trong tuần (ví dụ: sinh viên đi từ Phenikaa đến Đống Đa lúc `07:30` từ thứ Hai đến thứ Sáu).
- Bảng `recurring_trip_templates` lưu cấu hình mẫu: `(user_id, pickup, destination, active_weekdays, preferred_departure_time, window_minutes, vehicle_preference, ride_preference, budget_max, max_walk_m, is_active)`.
- Mỗi ngày, đúng vào thời điểm `preferred_departure_time − 12 giờ`, tác vụ định thời trong bảng `scheduled_jobs` (Mục 55) tự động sinh ra một yêu cầu `Trip Intent` ở chế độ `SCHEDULED` (tuân thủ đúng luật đặt trước tối đa 12 giờ của dịch vụ nội đô). Hành khách nhận thông báo và có thể bấm tạm dừng/hủy cho ngày hôm sau nếu đổi lịch.
- Nhờ biết trước tập nhu cầu buổi sáng từ tối hôm trước, bộ ghép theo lô (`batch_matcher` — Mục 37) có thể gom các hành khách đi cùng hành lang một cách ổn định, tạo ra nguồn cung ứng viên ghép có xác suất `P(match)` cao nhất cho toàn mạng lưới.

---

# PHẦN IV — LIÊN TỈNH: TAXI BAO XE VÀ TAXI GHÉP THEO LỊCH TRÌNH

# 25. TAXI BAO XE LIÊN TỈNH (`CAR_INTERCITY_PRIVATE`)

## 25.1. Quy tắc đặt chuyến và Tìm nguồn cung
- **Khung thời gian đặt:** Hỗ trợ cả **Đặt đi ngay trong ngày (`NOW` — đón trong vòng `15–45 phút`)** phục vụ nhu cầu đi tỉnh khẩn cấp, và **Hẹn trước (`SCHEDULED` — tối đa `7 ngày`)** (`[ACCEPTED]` — D-36).
- **Số lượng khách:** `1–4` hành khách thuê nguyên xe 4 chỗ.
- **Điều kiện nguồn cung tài xế:** Tài xế taxi có `accepts_intercity = true` và `kyc_status = VERIFIED` (S7).
  - Với đặt đi ngay (`NOW`): Lọc các tài xế đang rảnh trong bán kính `now_search_radius_km = 5,0 km` quanh điểm đón.
  - Với hẹn trước (`SCHEDULED`): Lọc các tài xế không có chuyến đi nào trùng lặp trong khoảng `[planned_pickup_time - 30 phút, planned_dropoff_time + estimated_return_time + 30 phút]`.
- **Chuỗi gửi Offer:** Thời gian chờ mỗi lần offer là **`60 giây`** (dài hơn mức 20 giây của nội đô để tài xế kịp cân nhắc kế hoạch đi đường dài), kèm `Per-Offer Seat Hold` có `TTL = 75 giây`, chuyển tiếp tối đa `3 lần` cho các tài xế cùng dịch vụ.

## 25.2. Công thức giá Taxi bao xe liên tỉnh

Vì tài xế chạy bao xe liên tỉnh theo yêu cầu đột xuất của khách thường phải đối mặt với rủi ro chạy rỗng chiều quay về, đơn giá theo km (`INTERCITY_PER_KM`) kết hợp với mức cước cơ sở cao (`INTERCITY_BASE`) được thiết kế để bù đắp chi phí hai chiều:

```text
IntercityPrivateFare_raw = INTERCITY_BASE + INTERCITY_PER_KM × D_route_km
IntercityPrivateFare     = floor( IntercityPrivateFare_raw / 1.000 ) × 1.000
```

Tham số cấu hình minh họa:
```text
INTERCITY_BASE   = 150.000 đ
INTERCITY_PER_KM =   7.500 đ/km
c_private        = 15% (0,15 — Hoa hồng nền tảng 15%, thấp hơn nội đô để khuyến khích tài xế đi tỉnh)
```

**Ví dụ chuẩn: Tuyến Hà Đông → TP Hưng Yên (Quãng đường OSRM minh họa `65,0 km`):**
```text
IntercityPrivateFare_raw = 150.000 + 7.500 × 65 = 150.000 + 487.500 = 637.500 đ
IntercityPrivateFare     = floor(637.500 / 1.000) × 1.000            = 637.000 đ
Thu nhập tài xế (85%)    = 637.000 × 0,85                            = 541.450 đ
Hoa hồng nền tảng (15%)  = 637.000 × 0,15                            =  95.550 đ
```
Giá đặt đi ngay (`NOW`) và hẹn trước (`SCHEDULED`) được giữ như nhau (không áp dụng nhân giá surge).

---

# 26. TAXI GHÉP LIÊN TỈNH (`CAR_INTERCITY_POOL`): TÀI XẾ ĐĂNG CHUYẾN VÀ QUẢN LÝ NGƯỠNG

Khác với nội đô (nơi hệ thống ghép động theo từng phút), dịch vụ `CAR_INTERCITY_POOL` vận hành theo mô hình **Tài xế công bố chuyến trước (`Driver-Published Scheduled Trip`)**:

```text
Đối tượng scheduled_trip:
  - corridor_id          : Mã hành lang tuyến liên tỉnh chuẩn (ví dụ: HN_HADONG__HY_TP)
  - origin_anchor, dest_anchor : Tọa độ điểm neo đầu đi và đầu đến của hành lang
  - departure_time       : Thời điểm khởi hành dự kiến T (cách lúc đăng từ 72 giờ đến 7 ngày)
  - departure_flex_min   : Biên độ dịch chuyển giờ khởi hành cho phép khi gộp/đón (mặc định ±30 phút)
  - seats_total          : Số ghế mở bán (tối đa = vehicle.capacity = 4 ghế)
  - seats_booked         : Số ghế hiện đã có khách đặt và giữ chỗ thành công (0..4)
  - min_seats_to_run     : Ngưỡng số ghế tối thiểu để chuyến chắc chắn khởi hành (khóa chuẩn = 3)
  - seat_price           : Giá bán 1 ghế do tài xế chọn trong biên độ [0.9, 1.1] × SeatReference
  - pickup_zone_ids      : Danh sách các zone đón khách miễn phí phụ phí ở đầu đi
  - dropoff_zone_ids     : Danh sách các zone trả khách miễn phí phụ phí ở đầu đến
```

**Quy tắc khóa ngưỡng tham chiếu để chống thao túng (`[ACCEPTED]` — P2-01):**
- Trong Revision 8, nếu cho phép tài xế tùy ý đặt `min_seats_to_run = 4`, giá ghế tham chiếu sẽ giảm ảo để hút khách rồi đến `T−72h` tài xế ép khách phải góp thêm (`topUp`) hoặc hủy chuyến mà không bị phạt.
- Do đó, trong Revision 9, đối với xe 4 chỗ (`CAR4`), ngưỡng chuẩn để tính giá ghế tham chiếu `SeatReference` được **khóa cố định ở mức nền tảng là `min_seats_ref = 3`**. Tài xế chỉ được cấu hình ngưỡng chấp nhận tự động chạy của riêng mình `min_seats_to_run` trong tập `{2, 3}` (mặc định `= 3`).
- Việc tài xế đăng chuyến lên hệ thống đồng nghĩa với cam kết tự động nhận mọi lượt đặt ghế hợp lệ thỏa mãn vùng đón/trả và số ghế trống, vì vậy **không có bước gửi Offer chờ tài xế duyệt từng khách**.

---

# 27. CÁC MỐC THỜI GIAN VÒNG ĐỜI CHUYẾN GHÉP LIÊN TỈNH (`T−7 NGÀY` → `T`)

```text
T − 7 ngày (168h)   MỞ ĐẶT CHỖ (OPEN_FOR_BOOKING)
                    - Hành khách tìm chuyến, chọn số ghế (1–4), khóa ký quỹ theo giá đã đặt.
                    - Hành khách được phép hủy miễn phí 100% trong suốt giai đoạn [T−7 ngày, T−72h).

T − 72 giờ (3 ngày) ĐÓNG ĐẶT CHỖ CHUẨN & KÍCH HOẠT QUY TRÌNH CHỐT CHUYẾN (Mục 29)
                    - Tác vụ định thời tự động kiểm tra điều kiện ghế đã đặt (seats_booked >= min_seats_to_run).
                    - Từ sau mốc T−72h, nếu chuyến đã CONFIRMED mà khách tự ý hủy sẽ chịu phí phạt (Mục 18.7).
                    - Nếu chuyến thiếu khách: kích hoạt Gộp chuyến (T−72h → T−70h) hoặc Đề nghị góp thêm (đến T−66h).

T − 60 giờ (2,5 ngày) HẠN CUỐI MỌI QUYẾT ĐỊNH ĐỐI VỚI CHUYẾN THIẾU KHÁCH
                    - Trước mốc này, mọi kết quả (Gộp chuyến, Khách góp thêm, hoặc Tài xế quyết định
                      chạy dưới ngưỡng / hủy chuyến) bắt buộc phải hoàn tất.
                    - Nếu bị hủy (CANCELLED_LOW_DEMAND), khách được hoàn 100% ký quỹ và còn trọn vẹn 2,5 ngày
                      để đặt lại chuyến ghép ngày khác hoặc chuyển sang đặt Taxi bao xe liên tỉnh.

T − 24 giờ (1 ngày) CHỐT THỨ TỰ ĐÓN VÀ GIỜ ĐÓN CHÍNH XÁC (PICKUP_ORDER_FIXED — Mục 31)
                    - Đóng hoàn toàn việc đặt ghế vét (nếu có bật cờ O-08).
                    - Giải bài toán tối ưu thứ tự đón (4! = 24 hoán vị) và gửi giờ đón cố định cho từng khách.

T (0 giờ)           KHỞI HÀNH (DEPARTED / RIDE_STARTED) ──► HOÀN THÀNH (COMPLETED) & GIẢI NGÂN
```

Toàn bộ các mốc chuyển trạng thái tại `T−72h`, `T−70h`, `T−66h`, `T−60h` và `T−24h` đều được lập lịch và thực thi tự động bởi bảng `scheduled_jobs` trong PostgreSQL (Mục 55).

---

# 28. MÔ HÌNH GIÁ GHẾ SUY NGƯỢC TỪ NGƯỠNG KHỞI HÀNH VÀ CÔNG THỨC PHỤ PHÍ NGOÀI VÙNG (`DoorSurcharge`)

## 28.1. Công thức Giá ghế tham chiếu (`SeatReference`) (`[ACCEPTED]` — D-38)

**Nguyên tắc kinh tế cốt lõi:** Giá một ghế ghép liên tỉnh được thiết kế sao cho **ngay khi chuyến xe bán đạt ngưỡng khởi hành chuẩn (`min_seats_ref = 3` ghế), khoản thu nhập thực nhận của tài xế xấp xỉ bằng đúng (100%) thu nhập khi chạy một chuyến bao xe riêng trên cùng hành lang tuyến đó**. Nhờ vậy, tài xế hoàn toàn không bị thiệt khi đăng chạy ghép, và nếu bán được ghế thứ 4 thì toàn bộ ghế thứ 4 là phần thu nhập tăng thêm (+33% vượt bao xe)!

```text
SeatReference_exact = [ IntercityPrivateFare × (1 - c_private) ] / [ min_seats_ref × (1 - c_seat) ]
SeatReference       = floor( SeatReference_exact / 1.000 ) × 1.000

Tham số cấu hình:
    min_seats_ref = 3 ghế
    c_private     = 15% (0,15 — Hoa hồng bao xe liên tỉnh)
    c_seat        = 10% (0,10 — Hoa hồng ghép ghế liên tỉnh, ưu đãi thấp hơn 5 điểm % cho tài xế)
```

Tài xế khi đăng chuyến được phép đặt giá bán mỗi ghế (`SeatPrice`) nằm trong biên độ $\pm 10\%$ quanh `SeatReference` (làm tròn đến `1.000 đ`):
```text
0,90 × SeatReference <= SeatPrice <= 1,10 × SeatReference
```

## 28.2. Kiểm chứng định lượng trên tuyến Hà Đông → TP Hưng Yên (`65 km`)

Từ Mục 25.2, ta có `IntercityPrivateFare = 637.000 đ` và thu nhập tài xế chạy bao xe là `541.450 đ`:
```text
SeatReference_exact = 541.450 / (3 × (1 - 0,10)) = 541.450 / 2,7 = 200.537,04 đ
SeatReference       = floor(200.537,04 / 1.000) × 1.000          = 200.000 đ / ghế
Khung giá tài xế được phép đặt (±10%)                            : 180.000 đ – 220.000 đ / ghế
Mức tiết kiệm của hành khách đi 1 ghế (200.000 đ so với 637.000 đ): Tiết kiệm 437.000 đ (-68,60%)!
```

Bảng đối sánh thu nhập của tài xế theo số ghế bán được (với `SeatPrice = SeatReference = 200.000 đ/ghế`):

| Số ghế đã đặt (`seats_booked`) | Tổng tiền thu từ khách | Hoa hồng nền tảng (`10%`) | Tài xế thực nhận (`90%`) | Tỷ lệ thu nhập tài xế so với chạy Bao xe (`541.450 đ`) |
|---:|---:|---:|---:|---:|
| `1 ghế` *(Dưới ngưỡng)* | `200.000 đ` | `20.000 đ` | `180.000 đ` | `33,24%` |
| `2 ghế` *(Dưới ngưỡng)* | `400.000 đ` | `40.000 đ` | `360.000 đ` | `66,49%` |
| **`3 ghế` (Đạt ngưỡng chuẩn)** | **600.000 đ** | **60.000 đ** | **540.000 đ** | **99,73%** *(Lệch 0,27% chỉ do làm tròn xuống SeatReference)* |
| **`4 ghế` (Kín xe)** | **800.000 đ** | **80.000 đ** | **720.000 đ** | **132,98%** *(Tài xế lãi thêm +178.550 đ so với bao xe!)* |

## 28.3. Công thức tất định tính Phụ phí đón/trả ngoài vùng miễn phí (`DoorSurcharge` — `[ACCEPTED]` P1-02)

- **Vấn đề cần giải quyết:** Khi hành khách đặt ghế ở thời điểm `T−5 ngày`, chưa biết toàn bộ những hành khách khác trên chuyến là ai và thứ tự đón chỉ được chốt ở `T−24h` (Mục 31). Tuy nhiên, giá của booking phải được chốt cố định ngay lúc đặt để khóa ký quỹ. Do đó, công thức tính `DoorSurcharge` bắt buộc phải **tất định (deterministic) và chỉ phụ thuộc vào tọa độ của chính hành khách đó so với vùng phục vụ của chuyến xe**, không phụ thuộc vào tọa độ của các hành khách khác.
- **Công thức chuẩn hóa trong Revision 9:**
  Mỗi chuyến ghép liên tỉnh có tập đa giác vùng đón miễn phí `pickup_zone_ids` (gắn với điểm neo đầu đi `origin_anchor`) và tập đa giác vùng trả miễn phí `dropoff_zone_ids` (gắn với điểm neo đầu đến `dest_anchor`).
  ```text
  1. Khoảng cách vượt ranh giới đầu đón (extra_pickup_km):
     - Nếu P_start ∈ pickup_zone_ids: extra_pickup_km = 0
     - Ngược lại: gọi B_pick là điểm chiếu gần nhất trên đường biên của pickup_zone_ids tới P_start.
       Kiểm tra: nếu direct_distance_km(P_start, B_pick) > max_corridor_deviation_km (10,0 km)
                 → Từ chối ứng viên (nằm quá xa hành lang đón của chuyến).
       Nếu hợp lệ: extra_pickup_km = OSRM_car_distance_km(P_start, B_pick).

  2. Khoảng cách vượt ranh giới đầu trả (extra_dropoff_km):
     - Nếu P_dest ∈ dropoff_zone_ids: extra_dropoff_km = 0
     - Ngược lại: gọi B_drop là điểm chiếu gần nhất trên đường biên của dropoff_zone_ids tới P_dest.
       Kiểm tra: nếu direct_distance_km(B_drop, P_dest) > max_corridor_deviation_km (10,0 km)
                 → Từ chối ứng viên.
       Nếu hợp lệ: extra_dropoff_km = OSRM_car_distance_km(B_drop, P_dest).

  3. Phụ phí đón/trả ngoài vùng (DoorSurcharge) cho booking (tính 1 lần trên mỗi điểm đón/trả của booking):
     DoorSurcharge = floor( (DOOR_SURCHARGE_PER_KM × (extra_pickup_km + extra_dropoff_km)) / 1.000 ) × 1.000
     (với DOOR_SURCHARGE_PER_KM = 4.000 đ/km).
  ```

## 28.4. Tổng giá một Booking ghép liên tỉnh

Với một booking đặt $s_j$ ghế (`seat_count`) trên chuyến có giá ghế `SeatPrice`:
```text
BookingPrice(j) = SeatPrice × s_j + DoorSurcharge(j)
```
Khoản `DoorSurcharge(j)` cũng chịu cùng mức hoa hồng với chuyến đi (`c_seat = 10%`, tài xế nhận `90%` phụ phí để bù xăng rẽ ra ngoài vùng đón trả). Giá `BookingPrice(j)` được cố định ngay từ lúc đặt, không bao giờ tăng lên do chuyến vắng khách — ngoại trừ trường hợp hành khách **chủ động bấm đồng ý góp thêm (`CONFIRMED_TOPUP`)** ở Mục 29.

---

# 29. QUY TRÌNH CHỐT CHUYẾN TẠI `T−72H`, GÓP THÊM TỰ NGUYỆN (`CONFIRMED_TOPUP`) VÀ XỬ LÝ THIẾU KHÁCH

Đúng vào thời điểm `T−72h` trước giờ khởi hành, job định thời khóa việc đặt chỗ mới thông thường (`BOOKING_CLOSED`) và kiểm tra tổng số ghế đã đặt $S_{\text{booked}} = \sum_{j} s_j$:

```text
TRƯỜNG HỢP 1: Đạt ngưỡng khởi hành (S_booked >= min_seats_to_run)
    → Chuyến chuyển ngay sang trạng thái CONFIRMED.
    → Gửi thông báo xác nhận chắc chắn khởi hành cho tài xế và toàn bộ hành khách.
    → Ký quỹ của các booking trên chuyến chuyển sang trạng thái khóa chờ chạy.

TRƯỜNG HỢP 2: Thiếu khách (0 < S_booked < min_seats_to_run)
    Hệ thống thực thi tuần tự chuỗi 3 bước cứu chuyến trong khung thời gian [T−72h, T−60h]:

    Bước 2.1 — Thử GỘP CHUYẾN tự động (T−72h đến T−70h, hạng mục SHOULD S5 — Mục 30):
        - Tìm chuyến ghép tương thích cùng hành lang để gộp khách sang.
        - Nếu gộp thành công và sau cửa sổ xác nhận 2 giờ (tại T−70h) chuyến nhận vẫn đủ ghế >= min_seats_to_run:
          → Chuyến nhận: CONFIRMED; Chuyến bị gộp: MERGED (giải phóng tài xế chuyến bị gộp).

    Bước 2.2 — Đề nghị GÓP THÊM tự nguyện (T−70h đến T−64h, hoặc T−72h đến T−66h nếu không có chuyến gộp — S5):
        - Hệ thống tính mức giá mỗi ghế nếu chia đều chi phí bao xe liên tỉnh cho số ghế hiện có:
              TopupSeatPrice = floor( (IntercityPrivateFare / S_booked) / 1.000 ) × 1.000
        - Với mỗi booking j đang đặt s_j ghế (đã trả phần ghế ban đầu là SeatPrice × s_j):
              topup_amount(j) = (TopupSeatPrice - SeatPrice) × s_j
              (Giữ nguyên DoorSurcharge(j) nếu có).
        - Gửi đề nghị góp thêm tới tất cả các booking trên chuyến (hạn trả lời 6 giờ):
          + Nếu 100% booking trên chuyến bấm ACCEPT và hoàn tất giao dịch nạp thêm ký quỹ (topUp):
            → Chuyến chuyển sang trạng thái CONFIRMED_TOPUP (chắc chắn khởi hành như một chuyến bao xe chia tiền).
          + Nếu có bất kỳ 1 booking nào bấm DECLINE hoặc hết hạn 6 giờ không phản hồi:
            → Hủy đề nghị góp thêm, giữ nguyên mức giá ghế ban đầu và chuyển sang Bước 2.3.

    Bước 2.3 — Tài xế quyết định chạy dưới ngưỡng hoặc hủy chuyến (Hạn cuối tại T−60h — MUST M7):
        - Tài xế được quyền chọn 1 trong 2 phương án trước mốc T−60h:
          + Chọn RUN (Chạy dù dưới ngưỡng):
            → Chuyến chuyển sang CONFIRMED_UNDER_MIN. Hành khách giữ nguyên mức giá ghế cũ đã đặt;
              tài xế nhận 90% tổng tiền ghế thực tế đã đặt (không có trợ giá từ Quỹ bảo đảm nội đô).
          + Chọn CANCEL (hoặc không phản hồi khi đến mốc T−60h):
            → Chuyến chuyển sang CANCELLED_LOW_DEMAND.
            → Hoàn trả 100% tiền ký quỹ cho toàn bộ hành khách (REFUNDED).
            → Tài xế không bị trừ điểm độ tin cậy.
            → Hệ thống tự động gửi thông báo kèm đường dẫn 1-chạm gợi ý hành khách chuyển sang đặt
              CAR_INTERCITY_PRIVATE cùng giờ hoặc chọn chuyến ghép của khung giờ/ngày lân cận.

TRƯỜNG HỢP 3: Không có khách nào đặt ghế tại T−72h (S_booked == 0)
    → Chuyến tự động chuyển ngay sang CANCELLED_LOW_DEMAND tại T−72h, giải phóng lịch cho tài xế.
```

## Quy tắc chuẩn hóa hoa hồng khi chuyển sang `CONFIRMED_TOPUP` (`[ACCEPTED]` — P0-04)
- Khi một chuyến ghép liên tỉnh được cứu thành công bằng cơ chế góp thêm (`status == CONFIRMED_TOPUP`), bản chất kinh tế của chuyến đi lúc này là các hành khách cùng nhau góp tiền để **thuê bao nguyên chuyến xe** theo đúng biểu giá `IntercityPrivateFare`.
- Để thu nhập của tài xế khớp với thu nhập chạy bao xe liên tỉnh (và khớp tuyệt đối với bảng kiểm thử hồi quy tại Mục 72), khi trạng thái chuyến là `CONFIRMED_TOPUP`, hệ thống **áp dụng mức hoa hồng của dịch vụ bao xe liên tỉnh `c_private = 15%` (tài xế nhận `85%`)** thay vì mức `c_seat = 10%`:

| Tổng số ghế đã đặt ($S_{\text{booked}}$) | Giá mỗi ghế sau góp thêm (`TopupSeatPrice`) | Số tiền góp thêm mỗi ghế (`topup_amount / ghế`) | Tổng tiền thu của chuyến | Hoa hồng nền tảng (`c_private = 15%`) | Tài xế thực nhận (`85%`) |
|---:|---:|---:|---:|---:|---:|
| **2 ghế** *(trên chuyến giá gốc 200k/ghế)* | **318.000 đ** *(từ `floor(637.000 / 2)`)* | **+118.000 đ / ghế** | `636.000 đ` | `95.400 đ` | **540.600 đ** *(Bằng 99,84% bao xe)* |
| **1 ghế** *(trên chuyến giá gốc 200k/ghế)* | **637.000 đ** *(từ `floor(637.000 / 1)`)* | **+437.000 đ / ghế** | `637.000 đ` | `95.550 đ` | **541.450 đ** *(Bằng 100,00% bao xe)* |

*Nhận xét:* Khi chuyến có 2 ghế, mỗi hành khách sau khi góp thêm trả `318.000 đ` — vẫn tiết kiệm được **50,1% (`319.000 đ`)** so với việc chuyến bị hủy rồi phải tự đặt một chuyến bao xe riêng (`637.000 đ`). Do đó, góp thêm là một lựa chọn kinh tế hoàn toàn tự nguyện và có lợi cho cả hai phía.

---

# 30. THUẬT TOÁN VÀ QUY TẮC GỘP CHUYẾN LIÊN TỈNH (`POOL_TRIP_MERGED` — SHOULD S5)

Tại mốc `T−72h`, trước khi làm phiền hành khách bằng đề nghị góp thêm tiền, hệ thống kiểm tra xem có thể dồn các hành khách của hai chuyến thiếu ngưỡng vào chung một xe hay không (`[ACCEPTED]` — P2-02):

## 30.1. Điều kiện tương thích để gộp Chuyến nguồn $Y$ (bị gộp) vào Chuyến đích $X$ (nhận khách)
1. **Cùng hành lang tuyến và cùng chiều di chuyển:** `X.corridor_id == Y.corridor_id`.
2. **Độ lệch thời gian khởi hành nằm trong ngưỡng cho phép:**
   `|X.departure_time - Y.departure_time| <= merge_max_departure_gap_min` (`60 phút`).
3. **Đủ sức chứa:** `X.seats_booked + Y.seats_booked <= X.seats_total` (`4 ghế`), và ưu tiên cặp gộp giúp tổng số ghế sau gộp `>= X.min_seats_to_run` (`3 ghế`).
4. **Thỏa mãn ràng buộc thời gian của mọi hành khách:** Giờ khởi hành điều chỉnh của chuyến nhận $X$ (nằm trong giao khoảng linh hoạt `departure_flex_min` của $X$ và khung giờ `[T_earliest, T_latest]` của tất cả hành khách trên cả $X$ và $Y$) tồn tại một thứ tự đón hợp lệ (kiểm tra bằng thuật toán Mục 31).

## 30.2. Quy tắc bảo vệ giá, Ký quỹ và Cửa sổ xác nhận gộp chuyến (`[ACCEPTED]` — P2-02)
- **Quy tắc giá không bao giờ tăng (Non-Increasing Merge Price Rule):**
  - Hành khách gốc của chuyến nhận $X$ giữ nguyên mức giá đã đặt trên $X$.
  - Hành khách chuyển từ chuyến bị gộp $Y$ sang chuyến $X$ được áp mức giá ghế mới:
    ```text
    NewSeatPrice(khách từ Y) = min( Y.seat_price, X.seat_price )
    ```
    Nếu `X.seat_price < Y.seat_price` (chuyến nhận có giá ghế rẻ hơn chuyến cũ), hành khách từ $Y$ được giảm xuống bằng giá của $X$, và phần chênh lệch `(Y.seat_price - X.seat_price) × seat_count` được hoàn trả tự động về ví của khách qua hàm `lockFinalPrice` trên hợp đồng thông minh! Ngược lại, nếu `X.seat_price > Y.seat_price`, khách từ $Y$ vẫn chỉ trả mức giá cũ `Y.seat_price` (tài xế $X$ đồng ý nhận thêm ghế lấp chỗ trống theo giá của $Y$ vì vẫn giúp chuyến $X$ vượt ngưỡng khởi hành).
- **Xử lý cửa sổ 2 giờ hủy miễn phí sau khi gộp (`MERGE_PENDING_CONFIRMATION`):**
  - Khi gộp tại `T−72h`, khách của chuyến $Y$ nhận thông báo đổi tài xế/biển số xe và giờ khởi hành mới, đồng thời có quyền bấm **Hủy miễn phí 100%** trong vòng `2 giờ` (từ `T−72h` đến `T−70h`) nếu không đồng ý với sự thay đổi.
  - Để tránh lỗi chuyến $X$ vừa chuyển sang `CONFIRMED` thì khách từ $Y$ bấm hủy làm số ghế tụt lại xuống dưới ngưỡng `< 3`, chuyến $X$ mang trạng thái trung gian **`MERGE_PENDING_CONFIRMATION`** trong suốt 2 giờ đó:
    - Tại mốc `T−70h`: Nếu tổng số ghế còn lại vẫn `>= min_seats_to_run` $\implies$ Chuyến $X$ chính thức chuyển sang **`CONFIRMED`**.
    - Nếu có khách từ $Y$ hủy trong 2 giờ đó làm tổng ghế của $X$ tụt xuống `< min_seats_to_run` $\implies$ Chuyến $X$ tự động chuyển tiếp sang **Bước 2.2 (Đề nghị góp thêm từ `T−70h` đến `T−64h`)** ở Mục 29.
- **Tiêu chí ưu tiên khi có nhiều cặp chuyến có thể gộp:** Tối đa hóa số chuyến đạt ngưỡng khởi hành $\to$ Ưu tiên tài xế nhận có điểm tin cậy cao hơn $\to$ Tối thiểu hóa tổng độ lệch giờ khởi hành của hành khách.

---

# 31. TỐI ƯU HÓA THỨ TỰ ĐÓN TẠI `T−24H`

Tại mốc `T−24h`, mọi chuyến ghép liên tỉnh đã ở trạng thái xác nhận chạy (`CONFIRMED`, `CONFIRMED_TOPUP`, hoặc `CONFIRMED_UNDER_MIN`) có từ $m = 1$ đến $4$ bookings ($m \le 4$). Hệ thống xác định thứ tự đón tối ưu tại đầu đi và thứ tự trả tối ưu tại đầu đến:
- Vì số lượng booking tối đa trên xe 4 chỗ là $m \le 4$, số hoán vị thứ tự đón tối đa chỉ là $4! = 24$ và số hoán vị thứ tự trả tối đa là $4! = 24$ (tổng cộng tối đa $24 \times 24 = 576$ chuỗi hành trình khả dĩ, hoặc $24$ hoán vị đón nếu điểm trả dùng chung/cố định dọc trục).
- Hệ thống gọi **1 lệnh `RoutingProvider.matrix()` duy nhất** lấy ma trận thời gian/khoảng cách cỡ $(2m) \times (2m)$ từ OSRM, sau đó duyệt vét cạn (Exhaustive Search) toàn bộ các hoán vị hợp lệ để chọn ra lộ trình có **tổng thời gian di chuyển ngắn nhất** đồng thời thỏa mãn:
  1. Giờ đón dự kiến của từng khách nằm trong khung `[T_earliest, T_latest]` đã cam kết.
  2. Thời gian ngồi trên xe của hành khách được đón đầu tiên không vượt quá giới hạn `max_in_vehicle_time`.
- Bài toán có kích thước hằng số nhỏ nên luôn tìm được **nghiệm tối ưu toàn cục chính xác 100%** trong thời gian `< 5 ms` mà không cần dùng thuật toán xấp xỉ. Sau khi chốt, trạng thái chuyến chuyển sang `PICKUP_ORDER_FIXED` và gửi thông báo giờ đón cố định tới từng khách.

---

# 32. MÁY TRẠNG THÁI CHI TIẾT CỦA CHUYẾN GHÉP LIÊN TỈNH

```text
PUBLISHED (Tài xế vừa đăng chuyến)
  ──► OPEN_FOR_BOOKING (Mở nhận đặt ghế trong cửa sổ [T−7 ngày, T−72h))
        │
        ▼ (Tại mốc T−72h: Đóng đặt chỗ chuẩn)
      BOOKING_CLOSED
        ├── (Đủ ghế >= min_seats_to_run) ────────────────────────────────────────► CONFIRMED
        ├── (Thiếu ghế, ghép thử sang chuyến khác từ T−72h đến T−70h):
        │     ├── Chuyến bị gộp (nguồn) ─────────────────────────────────────────► MERGED (Kết thúc)
        │     └── Chuyến nhận khách     ──► MERGE_PENDING_CONFIRMATION (2 giờ)
        │                                     ├── (Sau 2h vẫn đủ ghế) ───────────► CONFIRMED
        │                                     └── (Khách hủy làm thiếu ghế) ─────► TOPUP_OFFERED
        └── (Thiếu ghế, không có chuyến gộp) ────────────────────────────────────► TOPUP_OFFERED (6 giờ)
                                                                                     ├── (100% khách ACCEPT & topUp) ──► CONFIRMED_TOPUP
                                                                                     └── (Có khách từ chối / hết 6h) ──► UNDER_MIN_DRIVER_DECISION (đến T−60h)
                                                                                                                           ├── (Tài xế chọn RUN) ───────► CONFIRMED_UNDER_MIN
                                                                                                                           └── (Tài xế chọn CANCEL/quá hạn) ► CANCELLED_LOW_DEMAND
Các trạng thái chạy (CONFIRMED | CONFIRMED_TOPUP | CONFIRMED_UNDER_MIN):
  ──(Tại mốc T−24h)──► PICKUP_ORDER_FIXED ──(Tại mốc T)──► DEPARTED ──► COMPLETED
```

---

# 33. CÁC MỞ RỘNG LIÊN TỈNH (COULD — C10, C11)

1. **C10 — Mô hình dự báo xác suất chuyến đủ ghế `P(fill)` và Danh sách chờ (`Intercity Waitlist`):**
   - Dự báo xác suất một `scheduled_trip` đang ở trạng thái `OPEN_FOR_BOOKING` sẽ đạt `seats_booked >= min_seats_to_run` tại thời điểm `T−72h` (chi tiết đặc trưng và mô hình tại Mục 52). Hiển thị cho khách dưới dạng nhãn *"Khả năng chuyến khởi hành: Cao / Trung bình / Thấp"*.
   - Nếu khách tìm kiếm mà chưa có chuyến đăng sẵn phù hợp, khách có thể đăng ký vào bảng `intercity_waitlist` `(corridor_id, date, time_window, seat_count)`. Giao diện tài xế tổng hợp nhu cầu đang chờ theo từng tuyến và ngày để tài xế chủ động mở chuyến mới đón đầu nhu cầu.
2. **C11 — Gợi ý ghép chiều về (`Backhaul Matching`):**
   - Ngay khi tài xế đăng một chuyến ghép chiều đi (ví dụ Hà Nội → Hưng Yên khởi hành lúc 08:00), hệ thống gợi ý tạo nhanh chuyến ghép chiều về (Hưng Yên → Hà Nội khởi hành lúc 14:00 hoặc 16:00 cùng ngày).
   - Đối với tài xế vừa hoàn thành một chuyến bao xe liên tỉnh (`CAR_INTERCITY_PRIVATE`), hệ thống tự động ưu tiên phân phối các yêu cầu đặt xe chiều ngược lại xuất phát từ tỉnh đích về lại Hà Nội.

---

# PHẦN V — THUẬT TOÁN ĐỊNH TUYẾN, SINH ỨNG VIÊN, GHÉP XE VÀ KIỂM SOÁT ĐỒNG THỜI

# 34. ĐỊNH TUYẾN OSRM HAI PROFILE, KHÔNG GIAN POSTGIS VÀ CHIẾN LƯỢC GỌI MA TRẬN ĐƠN LẺ

```text
Dữ liệu bản đồ : OpenStreetMap (OSM) bản trích khu vực Việt Nam / miền Bắc.
Động cơ Routing: Hai tiến trình OSRM chạy local qua Docker:
                 1. osrm-car       : sử dụng profile ô tô chuẩn, cho phép đi cao tốc và cầu vượt ô tô.
                 2. osrm-motorbike : sử dụng profile Lua tùy chỉnh cho xe máy tại Việt Nam
                                     (cấm đường cao tốc `highway=motorway`, tốc độ lưu thông trung bình
                                      trong đường nội đô cao hơn ô tô 15–20% vào giờ cao điểm).
Không gian     : PostgreSQL + PostGIS lưu trữ hình học (POINT, POLYGON, LINESTRING) với chỉ mục GIST.
Giao diện chuẩn: RoutingProvider.route(profile, origin, destination, waypoints=[])
                 RoutingProvider.matrix(profile, sources, destinations)
Bộ nhớ đệm     : Redis lưu cache kết quả truy vấn theo khóa (profile, origin_geohash_7, dest_geohash_7, time_bucket).
```

## Quy tắc tối ưu hiệu năng: Một cuộc gọi ma trận OSRM duy nhất cho mỗi luồng sinh ứng viên (`[ACCEPTED]` — P2-04)
- **Giới hạn kỹ thuật:** Để đạt chỉ tiêu độ trễ `p95 <= 800 ms` cho toàn bộ quá trình gợi ý 3 dịch vụ nội đô (Mục 77), hệ thống **tuyệt đối không gọi hàm `RoutingProvider.route()` tuần tự bên trong vòng lặp thử chèn điểm $O(k^2)$ của 20 kế hoạch ghép** (việc gọi hàng trăm request HTTP tới OSRM sẽ làm độ trễ vọt lên 1.500–3.000 ms).
- **Chiến lược thực thi:** Trong mỗi lần sinh ứng viên `CAR_URBAN_POOL`, hệ thống gom toàn bộ các tọa độ liên quan (vị trí hiện tại của 20 xe ứng viên, các điểm dừng chưa đi qua của 20 kế hoạch đó, và điểm đón/trả $P, Q$ của khách mới — tổng cộng tối đa $\sim 60–100$ điểm tọa độ) vào **một cuộc gọi `RoutingProvider.matrix(profile='car', all_points, all_points)` duy nhất** tới dịch vụ `table` của OSRM (thời gian phản hồi của OSRM `table` cho 100 điểm trên mạng nội bộ chỉ từ `5–15 ms`). Sau khi có bảng ma trận khoảng cách $D[u][v]$ và thời gian $T[u][v]$ trong bộ nhớ RAM, toàn bộ vòng lặp kiểm tra chèn điểm ở Mục 36 chỉ thực hiện phép cộng tra bảng $O(1)$ thuần túy trong Python (tốn `< 3 ms` cho cả 20 kế hoạch).

---

# 35. THUẬT TOÁN SINH ỨNG VIÊN CHO NĂM DỊCH VỤ VÀ QUY TẮC TRỘN TOP-K

## 35.1. Xe máy nội đô (`BIKE_URBAN`) và Taxi bao xe nội đô (`CAR_URBAN_PRIVATE`)

```text
Đầu vào : Trip Intent R, dịch vụ s ∈ {BIKE_URBAN, CAR_URBAN_PRIVATE}
Thực thi:
  1. Lọc tài xế đang trực tuyến, trạng thái rảnh (IDLE), đúng loại xe (BIKE hoặc CAR4),
     đã bật accepts_urban = true.
  2. Truy vấn không gian PostGIS (ST_DWithin trên GIST index): lấy các tài xế trong bán kính R_urban (5 km)
     quanh điểm đón P_start.
  3. Ước lượng sơ bộ thời gian tiếp cận bằng khoảng cách Haversine chia tốc độ trung bình;
     giữ lại Top-N_single (tối đa 15 tài xế gần nhất).
  4. Gọi 1 lệnh OSRM matrix(profile, [driver_1..N, P_start], [P_start, P_dest]) để lấy chính xác
     thời gian đón (pickup ETA) và lộ trình đi thẳng (D_direct, T_direct).
  5. Kiểm tra 11 ràng buộc cứng (Mục 7) → Tính giá cố định (Mục 10.1 / 12.1) → Tính P(fulfill) (Mục 39).
Đầu ra  : Danh sách ứng viên hợp lệ của dịch vụ s.
```

## 35.2. Taxi ghép nội đô (`CAR_URBAN_POOL`)

```text
Đầu vào : Trip Intent R (với passenger_count <= 2)
Thực thi:
  Nhánh A — Ứng viên chèn vào kế hoạch ghép đang mở (PLAN_OPEN_SEARCHING):
    1. Lọc các kế hoạch đang mở (cả xe chờ chạy và xe đang chạy RIDE_STARTED) của tài xế có
       pool_enabled = true, kyc_status = VERIFIED, trong bán kính R_pool quanh P_start.
    2. Lọc sơ bộ theo hướng di chuyển (góc lệch vector < 60 độ hoặc hộp bao bounding box giao nhau)
       và còn ít nhất 1 đoạn có ghế trống >= passenger_count.
    3. Chọn Top-N_pool (tối đa 20 kế hoạch) → Sinh điểm đón gặp nhau nếu max_walk_m > 0 (C9, Mục 23).
    4. Gọi 1 lệnh OSRM matrix(profile='car') cho toàn bộ tập điểm dừng của 20 kế hoạch + điểm P, Q mới.
    5. Chạy Thuật toán chèn điểm động có nhận biết trạng thái xe (Mục 36):
       - Kiểm tra 11 ràng buộc cứng cho MỌI khách trong kế hoạch.
       - Kiểm tra Cổng 1 (Shareability) và Cổng 2 (Tốc độ sinh lời tài xế) tại Mục 14.
       - Chạy Thuật toán phân bổ giá kẹp hai đầu & bảo vệ giá khách cũ (Mục 15.3, 15.5).

  Nhánh B — Ứng viên khởi tạo kế hoạch ghép mới từ tài xế taxi đang rảnh:
    1. Lấy các tài xế taxi đang rảnh (tương tự 35.1) có pool_enabled = true, kyc_status = VERIFIED.
    2. Tính Quote_i, Unmatched_i (Mục 18.3) và giá ghép dự kiến điển hình Fare_matched_est (Mục 20.2).
    3. Kiểm tra trần ngân sách: Unmatched_i <= B_max.

  6. Với mọi ứng viên hợp lệ từ Nhánh A và Nhánh B: gọi mô hình dự báo P(match) (Mục 45) và P(fulfill) (Mục 39).
Đầu ra  : Danh sách ứng viên CAR_URBAN_POOL hợp lệ.
```

## 35.3. Taxi bao xe liên tỉnh (`CAR_INTERCITY_PRIVATE`)

```text
Đầu vào : Trip Intent R (mode = INTERCITY)
Thực thi:
  1. Lọc tài xế taxi có accepts_intercity = true, kyc_status = VERIFIED.
  2. Nếu đặt đi ngay (NOW): lọc tài xế đang rảnh trong bán kính now_search_radius_km = 5 km quanh P_start.
     Nếu hẹn trước (SCHEDULED): lọc tài xế không có lịch bận giao cắt với
     [T_earliest - 30m, T_latest + 2 × T_direct + 60m] (tính cả thời gian quay về).
  3. Gọi OSRM (profile='car') lấy quãng đường và thời gian → Kiểm tra 11 ràng buộc cứng
     → Tính giá IntercityPrivateFare (Mục 25.2) → Tính P(fulfill).
```

## 35.4. Taxi ghép liên tỉnh (`CAR_INTERCITY_POOL`)

```text
Đầu vào : Trip Intent R (mode = INTERCITY, 72h <= T_preferred - now <= 7 ngày)
Thực thi:
  1. Truy vấn bảng scheduled_trips có status == OPEN_FOR_BOOKING.
  2. Lọc hành lang tuyến: P_start nằm trong pickup_zone_ids (hoặc cách ranh giới <= 10 km)
     VÀ P_dest nằm trong dropoff_zone_ids (hoặc cách ranh giới <= 10 km).
  3. Lọc thời gian và sức chứa:
     - departure_time ± departure_flex_min giao với [T_earliest, T_latest] của khách.
     - seats_total - seats_booked >= R.passenger_count.
  4. Tính DoorSurcharge và BookingPrice (Mục 28.3, 28.4) → Kiểm tra BookingPrice <= B_max.
  5. Tính xác suất chuyến đủ ghế khởi hành (từ mốc Beta-smoothed hoặc mô hình P(fill) C10) → P(fulfill).
```

## 35.5. Quy tắc gộp và bảo toàn đa dạng trong Top-K (`[ACCEPTED]` — D-40)
- Tất cả ứng viên hợp lệ của các dịch vụ thuộc `allowed_service_codes` được đưa vào một tập hợp chung và chấm điểm bằng hàm mục tiêu Baseline (Mục 40) hoặc mô hình `LGBMRanker` (Mục 44).
- **Thuật toán chọn Top-K có bảo toàn đại diện dịch vụ (Diversity-Preserving Top-K Selection):**
  1. Sắp xếp toàn bộ ứng viên theo điểm xếp hạng giảm dần.
  2. Với mỗi dịch vụ $s \in \text{allowed\_service\_codes}$ có ít nhất 1 ứng viên hợp lệ, trích ra ứng viên có điểm cao nhất của dịch vụ $s$ đưa vào tập hạt giống `SeedSet` (tối đa 3 phần tử ở nội đô hoặc 2 phần tử ở liên tỉnh).
  3. Điền nốt các vị trí còn lại của `Top-K` ($K = 5$ hoặc $K = 6$) bằng các ứng viên có điểm cao nhất tiếp theo trong danh sách chung, sau đó sắp xếp lại `Top-K` theo điểm số và gắn nhãn giải thích (`Đề xuất`, `Rẻ nhất`, `Nhanh nhất`, `Thoải mái nhất`, `Ít đi vòng nhất`).

---

# 36. THUẬT TOÁN CHÈN ĐIỂM ĐÓN/TRẢ ĐỘNG CÓ NHẬN BIẾT TRẠNG THÁI XE ĐANG CHẠY

Trong Revision 8, mã giả ở Mục 36 duyệt `for i in 0..k` trên toàn bộ chuỗi điểm dừng mà không phân biệt các điểm dừng đã đi qua khi xe đang chạy (`RIDE_STARTED`), dẫn tới nguy cơ chèn điểm đón mới vào quá khứ hoặc tính sai quãng đường thực đi của khách đang ngồi trên xe. Revision 9 chuẩn hóa hoàn toàn thuật toán này (`[ACCEPTED]` — P1-01):

```text
Đầu vào:
  - Kế hoạch hiện tại Plan có chuỗi điểm dừng S_0 → S_1 → ... → S_k.
  - Chỉ số r là điểm dừng cuối cùng xe đã hoàn thành (completed_stop_index):
    + Nếu xe chưa xuất phát (CONFIRMED): r = -1, nút gốc xuất phát là vị trí tài xế hiện tại.
    + Nếu xe đang chạy (RIDE_STARTED)  : r >= 0, các điểm S_0..S_r đã đi qua và bị đóng băng;
      tạo nút gốc ảo hiện tại S_curr tại tọa độ GPS hiện hành của xe ở thời điểm t_now.
  - Với mỗi hành khách cũ m đang trên xe: đã lưu quãng đường thực tế đã đi được từ lúc lên xe
    đến vị trí hiện tại là traveled_km(m) và thời điểm lên xe thực tế là actual_pickup_time(m).
  - Yêu cầu mới c_new có điểm đón P (hoặc tập tối đa 3 điểm đón ứng viên từ C9), điểm trả Q,
    số ghế yêu cầu s_new = passenger_count.
  - Ma trận khoảng cách D_mat và thời gian T_mat từ 1 lệnh gọi OSRM Table duy nhất (Mục 34).

Thực thi:
  best_plan = None
  best_incremental_cost = +∞

  # Chỉ duyệt các vị trí chèn nằm ở PHÍA TRƯỚC vị trí hiện tại của xe (sau S_r / S_curr):
  Define chuỗi điểm dừng phía trước: F = [S_curr, S_{r+1}, S_{r+2}, ..., S_k] (độ dài m_f = k - r + 1)

  For p_idx in 0 .. (m_f - 1):              # Chèn điểm đón P ngay sau F[p_idx]
      For q_idx in p_idx .. (m_f - 1):      # Chèn điểm trả Q ngay sau F[q_idx] (và sau P)
          1. Tạo chuỗi hành trình mới Plan' = [S_0 .. S_r] + F_with_P_and_Q.
             Nếu tổng số điểm dừng của Plan' > k_max_stops (8) HOẶC số điểm đón thêm > driver.max_additional_pickups:
                 Continue (Bỏ qua).

          2. Cập nhật thời gian đến dự kiến (ETA) và tải trọng ghế cho từng đoạn từ S_curr đến cuối Plan'
             bằng phép tra bảng OSRM (D_mat, T_mat) + thời gian dừng tại mỗi trạm (dwell_time = 60s):
             - Kiểm tra Ràng buộc 4 (Sức chứa theo đoạn): nếu có bất kỳ đoạn nào > vehicle.capacity (4):
                 Continue.

          3. Kiểm tra lại toàn bộ ràng buộc thời gian và đi vòng cho MỌI hành khách m ∈ (Plan ∪ {c_new}):
             - Với hành khách chưa lên xe (gồm cả c_new): kiểm tra T_earliest(m) <= ETA(Pickup_m) <= T_latest(m).
             - Với hành khách đã lên xe: tổng quãng đường thực đi = traveled_km(m) + remaining_km_in_Plan'(m).
             - Kiểm tra Ràng buộc 5 (detour_m <= max_passenger_detour_ratio_m) và
               Ràng buộc 6 (in_vehicle_time_m <= max_in_vehicle_time_m, ETA(Dropoff_m) <= latest_arrival_m).
             - Kiểm tra Ràng buộc 7 (đi vòng của tài xế <= ngưỡng tài xế khai báo).
             Nếu bất kỳ hành khách nào hoặc tài xế bị vi phạm: Continue.

          4. Tính PlanFare_new (Mục 13) và kiểm tra điều kiện khả thi trước phân bổ (Cổng 1 & Điều kiện D1–D4 Mục 15.5):
             - Cổng 1 (Shareability): PlanFare_new <= (1 - d_min) × Σ_{m ∈ N_new} P_m (với P_m = PrivateFare(m)).
             - Điều kiện D1 (Còn khách chưa khóa U_old != ∅ và có giao đoạn đường thực tế với c_new).
             - Điều kiện khả thi hai cận trên tập chưa khóa U = U_old ∪ {c_new} (D2, D3, D4):
                 TargetFare_U = PlanFare_new - Σ_{k ∈ L} Fare_exact_old(k)
                 Σ_{m ∈ U} Floor_m <= TargetFare_U <= Σ_{i ∈ U_old} DynamicCap_i + Cap(c_new).
             Nếu bất kỳ điều kiện nào không thỏa: Continue (Bỏ qua).

          5. Chạy Thuật toán phân bổ hai cận chính xác (Mục 15.3.4), làm tròn tiền thu (Mục 15.4) và kiểm tra Cổng 2 sau làm tròn (D5, D6):
             - Tính Fare_exact_new(m) ∈ [Floor_m, DynamicCap_m] và Fare_charged_new(m) = floor(Fare_exact_new(m)/1000)×1000 cho mọi m ∈ U
               (giữ nguyên Fare_charged_new(k) = final_price(k) cho mọi k ∈ L).
             - Kiểm tra mọi khách cũ chưa khóa i ∈ U_old: Fare_exact_new(i) <= Fare_exact_old(i) VÀ Fare_charged_new(i) <= Fare_charged_old(i).
             - Kiểm tra Cổng 2A & 2B tính trên khoản Payout thực tế sau làm tròn (Mục 14.2):
                 DriverPayout(Plan')     = (1 - c_pool) × Σ_{m ∈ N_new} Fare_charged_new(m)
                 DriverHourlyRate(Plan') = DriverPayout(Plan') / (T_plan_new / 60)
                 DriverPayout(Plan') >= max_{m ∈ N_new} DriverPayout_Private(m)
                 DriverHourlyRate(Plan') >= (1 - ε_hourly) × max_{m ∈ N_new} DriverHourlyRate_Private(m).
             - Kiểm tra ngân sách cứng của khách mới c_new: Unmatched(c_new) <= B_max(c_new).
             Nếu bất kỳ điều kiện nào không thỏa: Continue.

          6. Tính chi phí tăng thêm ΔCost = PlanFare_new - PlanFare_old:
             Nếu ΔCost < best_incremental_cost:
                 best_incremental_cost = ΔCost
                 best_plan = Plan' (kèm bảng phân bổ giá mới)

Đầu ra: best_plan (hoặc None nếu không tồn tại vị trí chèn hợp lệ).
```

**Độ phức tạp tính toán:** Với $k_{\max} = 8$, số điểm dừng phía trước tối đa là $m_f \le 8$, số cặp vị trí chèn $(p_{\text{idx}}, q_{\text{idx}})$ tối đa chỉ là $\frac{8 \times 9}{2} = 36$ phép thử. Tại mỗi phép thử, việc cộng dồn ETA và kiểm tra ràng buộc trên mảng 8 phần tử tốn $O(k)$. Tổng số phép toán cơ sở cho mỗi kế hoạch là $\sim 36 \times 8 \approx 288$ phép toán số học trong bộ nhớ, đảm bảo thời gian thực thi cho cả 20 kế hoạch ứng viên luôn dưới `5 ms` sau khi có ma trận OSRM.

---

# 37. THUẬT TOÁN GHÉP THEO LÔ (BATCH MATCHING CP-SAT TRÊN ĐỒ THỊ RTV RÚT GỌN — SHOULD S4)

## 37.1. Phạm vi áp dụng trong luồng đặt xe
Cơ chế ghép theo lô định kỳ mỗi $\Delta = 30\text{ giây}$ **không làm thay đổi hay trì hoãn việc hiển thị danh sách gợi ý Top-K cho khách hàng**, mà vận hành ở tầng tìm người ghép nền:
1. Sau khi hành khách chọn một ứng viên `CAR_URBAN_POOL` khởi tạo kế hoạch mới (hoặc chọn chế độ `SCHEDULED` giao cho hệ thống xếp xe), booking đó đi vào trạng thái `price_status = POOL_SEARCHING`.
2. Cứ mỗi $\Delta = 30\text{ giây}$, job `batch_matcher` gom toàn bộ các yêu cầu/booking đang ở trạng thái chờ ghép để giải bài toán phân bổ toàn cục một lần, giúp tránh sự thiên lệch "ai đến trước chiếm chỗ trước" của thuật toán tham lam tuần tự (kiểm định tại Giả thuyết **H6**).

## 37.2. Mô hình hóa chính xác bằng Đồ thị Yêu cầu – Chuyến khả thi – Phương tiện (RTV-Graph CP-SAT — `[ACCEPTED]` P1-08)

- **Khắc phục lỗ hổng mô hình hóa của Revision 8:** Trong Revision 8, Mục 37.2 mô tả việc xây dựng đồ thị hai phía Yêu cầu – Kế hoạch (`RV`) rồi cho phép *"mỗi kế hoạch nhận tối đa 2 yêu cầu mới mỗi vòng"* bằng cách cộng tuyến tính hai cạnh độc lập `(r1, v)` và `(r2, v)`. Cách mô hình hóa đó bị lỗi: việc `r1` chèn hợp lệ vào `v` và `r2` chèn hợp lệ vào `v` một cách độc lập **không hề đảm bảo** rằng chèn đồng thời cả `{r1, r2}` vào `v` sẽ thỏa mãn sức chứa 4 ghế, khung giờ đón hay giới hạn đi vòng, và phần tiết kiệm của tổ hợp `(v, r1, r2)` cũng không bằng tổng tiết kiệm của hai phép chèn đơn lẻ!
- **Mô hình đồ thị RTV rút gọn (theo chuẩn Alonso-Mora et al., 2017) trong Revision 9:**
  Tại mỗi chu kỳ giải $\Delta = 30\text{ giây}$, tập đầu vào gồm tập các yêu cầu/booking đang chờ ghép $R = \{r_1, \dots, r_m\}$ và tập các xe/kế hoạch ghép đang mở $V = \{v_1, \dots, v_n\}$.

  ```text
  Bước 1 — Sinh tập các Tổ hợp ghép khả thi (Candidate Bundled Trips T):
      Với mỗi kế hoạch/xe v ∈ V:
        - Thử chèn từng yêu cầu đơn lẻ {r_a} (a ∈ R) vào v bằng Thuật toán Mục 36:
          Nếu hợp lệ → Tạo nút chuyến ứng viên t = (v, {r_a}) với lợi ích kinh tế:
          Gain(t) = S_new(v ∪ {r_a}) - S_old(v)   (phần tiết kiệm tăng thêm thực tế của kế hoạch).
        - Với các cặp {r_a, r_b} mà cả r_a và r_b đều chèn đơn lẻ hợp lệ vào v (và tổng ghế <= ghế trống):
          Thử chèn đồng thời cả hai yêu cầu {r_a, r_b} vào v bằng Thuật toán Mục 36:
          Nếu hợp lệ qua toàn bộ 11 ràng buộc cứng + 2 cổng Mục 14 + bảo vệ giá Mục 15.5:
          → Tạo nút chuyến ứng viên kép t = (v, {r_a, r_b}) với lợi ích kinh tế chính xác:
            Gain(t) = S_new(v ∪ {r_a, r_b}) - S_old(v).
      Gọi T(v) là tập mọi chuyến ứng viên hợp lệ gắn với xe v, và T(r) là tập mọi chuyến ứng viên có chứa yêu cầu r.

  Bước 2 — Giải bài toán Quy hoạch nguyên (Set Packing ILP) bằng OR-Tools CP-SAT:
      Biến quyết định nhị phân:
        - x_t ∈ {0, 1} với mỗi chuyến ứng viên hợp lệ t ∈ T (x_t = 1 nếu chọn thực thi phương án t).
        - u_r ∈ {0, 1} với mỗi yêu cầu r ∈ R (u_r = 1 nếu yêu cầu r chưa được ghép trong vòng này).

      Hàm mục tiêu (Tối đa hóa tổng tiết kiệm toàn mạng lưới trừ chi phí phạt không ghép được):
          Maximize   Σ_{t ∈ T} Gain(t) × x_t  -  Σ_{r ∈ R} P_unassigned × u_r
          (với P_unassigned = 50.000 đ để ưu tiên ghép tối đa số yêu cầu hợp lệ).

      Hệ ràng buộc tuyến tính chặt chẽ:
        1. Mỗi xe/kế hoạch v chỉ được chọn tối đa 1 phương án nâng cấp lộ trình duy nhất:
               Σ_{t ∈ T(v)} x_t <= 1,     ∀ v ∈ V
        2. Mỗi yêu cầu r hoặc được ghép vào đúng 1 phương án t, hoặc được đánh dấu chưa ghép (u_r = 1):
               Σ_{t ∈ T(r)} x_t + u_r == 1,     ∀ r ∈ R

  Bước 3 — Giới hạn thời gian và Phương án dự phòng (Fallback):
      - Đặt solver_time_limit_s = 3,0 giây cho CP-SAT.
      - Nếu CP-SAT trả về nghiệm OPTIMAL hoặc FEASIBLE trong 3 giây → lấy nghiệm đó.
      - Nếu quá 3 giây chưa có nghiệm (trường hợp cực hiếm): chạy thuật toán Tham lam (Greedy)
        duyệt các phần tử t ∈ T theo thứ tự Gain(t) giảm dần, chọn t nếu xe v và các yêu cầu trong t chưa bị đánh dấu.

  Bước 4 — Ghi nhận kết quả an toàn đồng thời (Transactional Commit):
      - Với mỗi phương án t = (v, R_t) được chọn (x_t == 1), mở transaction khóa dòng ride_plan v,
        kiểm tra v.plan_version == snapshot_version(v); nếu khớp thì cập nhật lộ trình, giá và tăng plan_version += 1.
  ```

Nhờ mọi nút $t \in \mathcal{T}$ đều đã được kiểm chứng trọn vẹn qua Mục 36 trước khi đưa vào CP-SAT, **100% nghiệm đầu ra của bộ giải đều đảm bảo khả thi tuyệt đối về mặt vật lý và tài chính**, loại bỏ hoàn toàn nguy cơ sinh kế hoạch lỗi.

---

# 38. TỔNG HỢP THUẬT TOÁN ĐỊNH GIÁ TOÀN HỆ THỐNG

```text
1. BIKE_URBAN:
     BikeFare = floor( (BIKE_BASE + BIKE_PER_KM × D + BIKE_PER_MIN × T) / 1.000 ) × 1.000    (Mục 10.1)

2. CAR_URBAN_PRIVATE:
     PrivateFare = floor( (BASE + PER_KM × D + PER_MIN × T) / 1.000 ) × 1.000                 (Mục 12.1)

3. CAR_URBAN_POOL:
     - Giá tham chiếu độc lập: P_i = PrivateFare(i) (giữ nguyên cho cả s_i ∈ {1, 2})            (Mục 12.2)
     - Hệ số phụ trội ghế thứ hai: seat_factor(i) = 1 + γ_seat × (s_i - 1)                     (Mục 12.2)
     - Chi phí kế hoạch chung: PlanFare = BASE + PER_KM×D_plan + PER_MIN×T_plan + STOP_FEE×(k-2) (Mục 13)
     - Kiểm tra Cổng 1 (Shareability): PlanFare <= (1 - d_min) × Σ_{i ∈ N} P_i                 (Mục 14.1)
     - Kiểm tra điều kiện khả thi hai cận (F1, F2, F3) & Điều kiện chèn động D1–D4:
         Σ_{m ∈ U} Floor_m <= TargetFare_U <= Σ_{m ∈ U} EffectiveCap_m                         (Mục 15.3, 15.5)
     - Phân bổ hai cận chính xác [Floor_i, EffectiveCap_i] với trọng số w_i / seat_factor(i)   (Mục 15.2, 15.3.4)
     - Làm tròn tiền thu: Fare_charged(i) = floor(Fare_exact(i) / 1.000) × 1.000               (Mục 15.4)
     - Kiểm tra Cổng 2A & 2B trên khoản Payout thực tế sau làm tròn:
         DriverPayout(Plan) = (1 - c_pool) × Σ_{i ∈ N} Fare_charged(i)
         DriverHourlyRate(Plan) = DriverPayout(Plan) / (T_plan / 60) >= (1 - ε_hourly) × max_i Rate_Private(i) (Mục 14.2)
     - Trần báo giá: Quote_i = floor(P_i × (1 - d_min) / 1.000) × 1.000                        (Mục 18.3)
     - Giá tối đa không ghép: Unmatched_i = floor((Quote_i + α × (P_i - Quote_i)) / 1.000) × 1.000 (< P_i)

4. CAR_INTERCITY_PRIVATE:
     IntercityPrivateFare = floor( (INTERCITY_BASE + INTERCITY_PER_KM × D) / 1.000 ) × 1.000  (Mục 25.2)

5. CAR_INTERCITY_POOL:
     - Giá ghế tham chiếu: SeatReference = floor( [IntercityPrivateFare × (1 - c_private)]
                                                  / [min_seats_ref × (1 - c_seat)] / 1.000 ) × 1.000
     - Giá đặt ban đầu: BookingPrice(j) = SeatPrice × s_j + DoorSurcharge(j)                  (Mục 28.4)
     - Góp thêm tại T−72h (nếu 100% khách đồng ý):
       TopupSeatPrice = floor((IntercityPrivateFare / S_booked) / 1.000) × 1.000              (Mục 29)
       (Khi chạy ở chế độ CONFIRMED_TOPUP: áp dụng hoa hồng c_private = 15%).

Mọi dịch vụ:
     - Kiểm tra ngân sách cứng: max_possible_charge <= B_max.
     - Lưu bản ghi truy vết: pricing_version, service_code, và chi tiết các thành phần cấu thành giá.
```

---

# 39. MÔ HÌNH XÁC SUẤT HOÀN THÀNH CHUYẾN (`p_fulfill`) THEO CÂY SỰ KIỆN TUẦN TỰ

Trong Revision 8, công thức `p_fulfill` tách rời sự kiện "tài xế không hủy" và "khách không hủy" thành hai xác suất nối tiếp nhau nhưng trên dữ liệu thực tế hai sự kiện này cạnh tranh nhau theo thời gian (Competing Risks — ai hủy trước thì chuyến kết thúc ngay và không quan sát được hành vi của người kia), đồng thời chưa làm rõ nguồn xác suất chốt chuyến tại `T−72h` cho dịch vụ ghép liên tỉnh khi không làm hạng mục C10.

Revision 9 chuẩn hóa `p_fulfill` theo **Cây sự kiện tuần tự không chồng lấp (Sequential Non-Censored Event Tree)** (`[ACCEPTED]` — P1-06):

## 39.1. Đối với các dịch vụ có bước gửi Offer (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`, `CAR_INTERCITY_PRIVATE`)

Vòng đời từ lúc khách chọn ứng viên đến lúc hoàn thành chuyến đi qua **3 cổng sự kiện tuần tự rõ ràng**:
1. **Cổng 1 — Tài xế chấp nhận chuyến (`E_accept = 1`):**
   - Với ứng viên xe đơn hoặc khởi tạo kế hoạch Pool mới: xác suất có ít nhất 1 tài xế nhận trong chuỗi Offer Cascade $P(\text{accepted} \mid x)$.
   - Với ứng viên chèn tự động vào kế hoạch Pool đang chạy (`CORIDER_AUTO_ADDED`): xác suất tài xế không bấm từ chối khách ghép $P(\text{not\_declined\_corider} \mid x)$.
2. **Cổng 2 — Không bên nào hủy trước khi đón và khách lên xe thành công (`E_start = 1` | `E_accept = 1`):**
   - Thay vì tách hai mô hình cạnh tranh bị ẩn nhãn (censored), hệ thống mô hình hóa trực tiếp sự kiện hợp nhất trên tập các booking đã được tài xế nhận (`E_accept == 1`):
     $$P(\text{ride\_started} \mid \text{accepted}, x) = 1 - P(\text{cancelled\_by\_driver} \cup \text{cancelled\_by\_passenger} \cup \text{no\_show} \mid \text{accepted}, x)$$
   - Nhờ vậy, nhãn huấn luyện trên tập `accepted == 1` là nhị phân hoàn toàn xác định (`1` nếu đạt `RIDE_STARTED`, `0` nếu rơi vào bất kỳ nhánh hủy/`NO_SHOW` nào trước khi đón)!
3. **Cổng 3 — Hoàn thành hành trình sau khi đã lên xe (`E_complete = 1` | `E_start = 1`):**
   - Xác suất chuyến đi không bị gián đoạn giữa đường (sự cố xe / tranh chấp): $P(\text{completed} \mid \text{ride\_started}, x)$ (thường đạt $\ge 0,99$).

**Công thức tổng hợp chuẩn cho nhóm có Offer:**
```text
p_fulfill(i) = P(accepted | x) × P(ride_started | accepted, x) × P(completed | ride_started, x)
```

## 39.2. Đối với dịch vụ Taxi ghép liên tỉnh (`CAR_INTERCITY_POOL`)

Vì tài xế đã đăng chuyến trước nên không có bước gửi Offer ($P(\text{accepted}) = 1$), nhưng chuyến đi phải vượt qua cổng chốt ngưỡng tại `T−72h` (`trip_confirmed ∈ {CONFIRMED, CONFIRMED_TOPUP, CONFIRMED_UNDER_MIN}`):
```text
p_fulfill_intercity_pool(i)
= P(trip_confirmed_at_T72 | x)
× P(ride_started | trip_confirmed_at_T72, x)
× P(completed | ride_started, x)
```
- **Nguồn tính $P(\text{trip\_confirmed\_at\_T72} \mid x)$ theo cấp độ triển khai:**
  - Ở cấp độ **MUST / SHOULD** (khi chưa bật mô hình học máy C10): Sử dụng **Mốc thực nghiệm làm mượt Beta (Beta-smoothed Empirical Fill Rate)** tra cứu theo `(corridor_id, current_seats_booked_plus_request)`:
    $$P_{\text{Beta}}(\text{confirmed} \mid \text{corridor}, s_{\text{after}}) = \frac{\text{số\_chuyến\_đạt\_xác\_nhận}(\text{corridor}, s_{\text{after}}) + \alpha_0}{\text{tổng\_số\_chuyến}(\text{corridor}, s_{\text{after}}) + \alpha_0 + \beta_0}$$
    *(Đặc biệt, nếu số ghế hiện đã đặt cộng số ghế khách đang muốn đặt $s_{\text{after}} \ge \text{min\_seats\_to\_run}$, thì xác suất đạt ngưỡng tại `T−72h` tiệm cận $\approx 0,95–1,00$!).*
  - Ở cấp độ **COULD (khi bật C10 — Mục 52)**: Thay thế trực tiếp bằng xác suất dự báo đã hiệu chỉnh từ mô hình LightGBM `P(fill)`.

## 39.3. Xử lý khởi đầu lạnh (Cold Start) cho tài xế mới
Với mọi thành phần phụ thuộc lịch sử tài xế, hệ thống áp dụng làm mượt Bayes với phân phối tiên nghiệm Beta (`prior Beta(a, b)`):
```text
p_driver_stat = (số_lần_thành_công + a) / (tổng_số_lần_quan_sát + a + b)
```

---

# 40. HÀM MỤC TIÊU GỢI Ý BASELINE CÓ GIẢI THÍCH

Trước khi kích hoạt mô hình học máy LTR (hoặc dùng làm đối chứng trực tiếp cho Giả thuyết **H1, H9**), hệ thống sử dụng hàm tiện ích trọng số tuyến tính chuẩn hóa `U_base`:

```text
U_base(i)
= w_price   × PriceScore(i)
+ w_time    × TimeScore(i)
+ w_detour  × DetourScore(i)
+ w_quality × QualityScore(i)
+ w_pool    × PoolScore(i)
+ w_comfort × ComfortScore(i)
```

Trong đó các điểm thành phần đều được chuẩn hóa về đoạn $[0, 1]$:
- **Điểm thoải mái phương tiện (`ComfortScore`):**
  - `CAR_URBAN_PRIVATE`, `CAR_INTERCITY_PRIVATE`: `1,00`
  - `CAR_URBAN_POOL`, `CAR_INTERCITY_POOL`: `0,70`
  - `BIKE_URBAN`: `0,30` khi thời tiết bình thường (`is_raining == false`), và giảm về **`0,00` khi trời mưa (`is_raining == true`)**.
- **Giá đại diện dùng để chấm điểm (`EffectivePrice`):**
  - Với các dịch vụ giá cố định: `EffectivePrice(i) = Fare_charged(i)`.
  - Với `CAR_URBAN_POOL`: sử dụng **Giá kỳ vọng toán học (`ExpectedPrice`)** kết hợp đầu ra từ mô hình `P(match)` (Mục 45) và giá ghép dự kiến `Fare_matched_est` (Mục 20.2):
    ```text
    ExpectedPrice(i) = P(match_i) × Fare_matched_est(i) + (1 - P(match_i)) × Unmatched_i
    ```
- **Điểm giá (`PriceScore`):**
  ```text
  PriceScore(i) = 1,0                                                      nếu EffectivePrice(i) <= B_min
                = 1,0 - (EffectivePrice(i) - B_min) / (B_max - B_min)      nếu B_min < EffectivePrice(i) <= B_max
                = 0,0                                                      nếu EffectivePrice(i) > B_max
  ```
- **Hạn chế cố hữu của Baseline (Cơ sở cho Giả thuyết H1, H2, H9):** Bộ trọng số `(w_price, w_time, ...)` của Baseline là cố định và cộng tính tuyến tính, không thể tự động thay đổi độ dốc theo từng phân khúc khách hàng hay học được các tương tác bậc cao (như *Xe máy × Trời mưa × Quãng đường dài > 10 km*).

---

# 41. CHUỖI GỬI OFFER (OFFER CASCADE) VÀ CƠ CHẾ GIỮ GHẾ THEO TỪNG BƯỚC (`Per-Offer Seat Hold`)

Cơ chế chuỗi gửi Offer áp dụng cho 4 dịch vụ: `BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL` (khi khởi tạo kế hoạch mới) và `CAR_INTERCITY_PRIVATE`. Dịch vụ `CAR_INTERCITY_POOL` không cần gửi Offer (Mục 26).

## Khắc phục lỗi xung đột TTL giữa `seat_hold` và `offer_cascade` của Revision 8 (`[ACCEPTED]` — P0-05, D-47)
- **Lỗi trong Revision 8:** Đặt một `seat_hold` duy nhất có `TTL = 60 giây` (nội đô) và `90 giây` (liên tỉnh) cho cả chuỗi 3 lần offer. Vì 3 lần offer nội đô mất $3 \times 20\text{s} = 60\text{s}$ (liên tỉnh mất $3 \times 60\text{s} = 180\text{s} > 90\text{s}$) và 3 ứng viên trong Top-K thuộc về **3 chiếc xe / kế hoạch (`ride_plan`) hoàn toàn khác nhau**, cách làm của Revision 8 vừa giữ khóa nhầm xe, vừa làm `seat_hold` hết hạn ngay trước khi tài xế thứ 2 hoặc thứ 3 bấm nhận!
- **Quy trình chuẩn hóa `Per-Offer Seat Hold` trong Revision 9:**

```text
Khi hành khách bấm chọn Ứng viên ưu tiên #1 (thuộc dịch vụ S_chosen) trong danh sách Top-K:
  Hệ thống trích xuất danh sách tối đa M = 3 ứng viên hàng đầu CÙNG DỊCH VỤ S_chosen: [Cand_1, Cand_2, Cand_3]
  (Tuyệt đối không tự ý chuyển đổi từ Taxi sang Xe máy hay ngược lại — D-41).

  For attempt k = 1 to min(3, len(Candidates_same_service)):
      Ứng viên hiện tại C_k gắn với kế hoạch/xe P_k (có source_plan_version V_k):

      1. Mở Transaction kiểm tra và cấp phát Per-Offer Seat Hold cho riêng C_k:
         - Khóa dòng P_k (SELECT ... FOR UPDATE).
         - Kiểm tra P_k.version == V_k VÀ kiểm tra lại 11 ràng buộc cứng tại thời điểm hiện tại.
           (Nếu P_k đã thay đổi version nhưng kiểm tra lại toàn bộ ràng buộc cứng + bảo vệ giá vẫn thỏa mãn,
            cập nhật sang version mới; nếu không còn thỏa mãn → bỏ qua C_k, chuyển ngay sang k+1).
         - Tạo bản ghi seat_hold_k gắn với P_k có thời gian sống (TTL):
               TTL_hold = offer_timeout_s + hold_buffer_s
               + Nội đô    : offer_timeout_s = 20s, hold_buffer_s = 15s → TTL_hold_urban     = 35 giây.
               + Liên tỉnh : offer_timeout_s = 60s, hold_buffer_s = 15s → TTL_hold_intercity = 75 giây.
         - Tăng P_k.version += 1; tạo bản ghi offer_k (expires_at = now + offer_timeout_s) + scheduled_job.
         - COMMIT Transaction.

      2. Chờ phản hồi của tài xế xe P_k (tối đa offer_timeout_s giây):
         - Nhánh A — Tài xế bấm ACCEPT trước khi offer_k hết hạn:
             + Trong 1 Transaction: kiểm tra seat_hold_k còn hiệu lực, chuyển seat_hold_k → CONSUMED,
               chuyển booking sang ride_status = CONFIRMED, cập nhật lộ trình P_k, tăng P_k.version += 1.
             + Kích hoạt lệnh ký quỹ Blockchain bất đồng bộ (Mục 80).
             + KẾT THÚC THÀNH CÔNG chuỗi Offer (Trả kết quả về cho hành khách).

         - Nhánh B — Tài xế bấm REJECT hoặc job hết hạn offer_k (Timeout):
             + Trong 1 Transaction: giải phóng ngay lập tức seat_hold_k (status = RELEASED) trên xe P_k,
               ghi nhận sự kiện OFFER_REJECTED / OFFER_EXPIRED (làm nhãn huấn luyện cho mô hình P(accepted | x)),
               và lặp sang ứng viên tiếp theo k + 1.

  Nếu cả 3 lần thử đều thất bại:
      → Chuyển phiên đặt xe sang EXPIRED, tự động làm mới danh sách ứng viên và thông báo cho khách.
```

---

# 42. KIỂM SOÁT ĐỒNG THỜI BẰNG `plan_version`, KHÓA DÒNG VÀ TÍNH LŨY ĐẲNG (`Idempotency-Key`)

Để đảm bảo tuyệt đối các cổng đúng đắn `0 oversell ghế theo đoạn` và `0 booking trùng khi retry` (Mục 70) dưới tải đồng thời cao, hệ thống áp dụng 3 lớp bảo vệ kỹ thuật (`[ACCEPTED]` — D-03, D-25):

1. **Snapshot bất biến và Kiểm soát lạc quan kết hợp Khóa bi quan (`source_plan_version` + `SELECT ... FOR UPDATE`):**
   - Mọi ứng viên (`ride_candidates`) sinh ra đều lưu `source_plan_version` của `ride_plans` (nội đô) hoặc `scheduled_trips` (liên tỉnh) tại thời điểm tính toán.
   - Mọi thao tác làm thay đổi thành phần chuyến (khách bấm chọn ứng viên, tài xế nhận offer, vòng ghép theo lô `batch_matcher` áp kết quả, khách đặt ghế liên tỉnh, hoặc job chốt chuyến `T−72h`) đều bắt buộc thực thi trong một giao dịch CSDL PostgreSQL có câu lệnh:
     ```sql
     SELECT id, plan_version, status, seats_booked ...
     FROM ride_plans (hoặc scheduled_trips)
     WHERE id = :target_id
     FOR UPDATE;
     ```
   - **Giải quyết triệt để tranh chấp tại mốc `T−72h`:** Khi một hành khách bấm đặt ghế cuối cùng vào đúng mili-giây mà worker chạy job chốt chuyến `T−72h`, khóa dòng `FOR UPDATE` trên dòng `scheduled_trips` buộc hai giao dịch phải xếp hàng tuần tự:
     - Nếu giao dịch của khách vào khóa trước: ghế được đặt thành công, `seats_booked` tăng lên, `plan_version += 1`, sau đó job `T−72h` vào khóa đọc thấy số ghế mới và chốt `CONFIRMED`.
     - Nếu job `T−72h` vào khóa trước: `status` của chuyến đã chuyển sang `BOOKING_CLOSED` (hoặc `CONFIRMED`), giao dịch của khách vào sau thấy `status != OPEN_FOR_BOOKING` sẽ bị từ chối sạch sẽ. Không bao giờ tồn tại trạng thái lửng (Race Condition).
2. **Tính lũy đẳng ở tầng API (`Idempotency-Key`):**
   - Mọi endpoint thay đổi trạng thái (`POST /select`, `/book`, `/accept`, `/reject`, `/cancel`, `/topup/respond`, `/under-min-decision`) bắt buộc phải có header `Idempotency-Key`.
   - Hệ thống lưu cặp `(user_id, idempotency_key, request_payload_hash, response_status, response_body_json)` với `TTL = 24 giờ`:
     - Nếu gọi lặp lại với cùng `Idempotency-Key` và cùng `request_payload_hash`: trả về ngay kết quả đã lưu mà không thực thi lại logic nghiệp vụ.
     - Nếu gọi lặp lại với cùng `Idempotency-Key` nhưng khác `request_payload_hash`: trả về lỗi `422 IDEMPOTENCY_KEY_PAYLOAD_MISMATCH`.
3. **Tính lũy đẳng ở tầng Tác vụ định thời và Blockchain:**
   - Bảng `scheduled_jobs` có ràng buộc `UNIQUE (idempotency_key)`; trước khi thực thi tác vụ, worker kiểm tra trạng thái hiện tại của thực thể đích (ví dụ: nếu chuyến liên tỉnh đã ở trạng thái `!= OPEN_FOR_BOOKING` thì job `T−72h` tự động đánh dấu `COMPLETED_NOOP` và thoát an toàn).
   - Trên hợp đồng thông minh và `escrow_adapter`, mọi giao dịch đều gắn khóa `bytes32 bookingId` duy nhất; gọi nạp tiền hoặc giải ngân lần thứ hai cho cùng một `bookingId` sẽ bị hợp đồng từ chối.

---

# PHẦN VI — TRÍ TUỆ NHÂN TẠO (AI/ML), SIMULATOR VÀ PHƯƠNG PHÁP NGHIÊN CỨU

# 43. VAI TRÒ, RANH GIỚI AN TOÀN VÀ CÁC BÀI TOÁN AI TRONG HỆ THỐNG

Để đảm bảo hệ thống vừa mang tính ứng dụng thực tế vừa có giá trị khoa học chặt chẽ, thiết kế AI tuân thủ nghiêm ngặt **3 nguyên tắc ranh giới an toàn (`[ACCEPTED]` — D-26, D-27, D-28)**:

```text
Nguyên tắc 1 — Khả thi vật lý & Kinh tế ≠ Gợi ý xếp hạng:
    AI KHÔNG BAO GIỜ được dùng để quyết định xem xe có đủ ghế không, lộ trình có thỏa mãn khung giờ không,
    có vượt trần ngân sách B_max không, hay giá tiền là bao nhiêu. Toàn bộ các quyết định đó thuộc về
    bộ lọc 11 Ràng buộc cứng (Mục 7) và Thuật toán định giá tất định (Mục 38).
    AI chỉ xếp hạng các ứng viên ĐÃ HỢP LỆ và dự báo các đại lượng xác suất chưa chắc chắn.

Nguyên tắc 2 — Sở thích của hành khách ≠ Khả năng hoàn thành chuyến đi:
    Xác suất hành khách thích và bấm chọn một ứng viên (P(select | shown)) được tách bạch hoàn toàn khỏi
    xác suất chuyến đi đó thực sự diễn ra thành công đến đích (P(fulfill)). Một ứng viên có giá rất rẻ
    nhưng tài xế hay hủy chuyến sẽ bị điều chỉnh giảm điểm ở bước kết hợp cuối cùng (Mục 47).

Nguyên tắc 3 — Biến ẩn của Simulator ≠ Dữ liệu đầu vào của Mô hình học máy:
    Các tham số tiện ích ẩn của từng hành khách (theta_price, rain_aversion_bike, ...) và xác suất thật
    bên trong Simulator tuyệt đối không bao giờ được xuất hiện trong bảng đặc trưng huấn luyện (Zero Leakage).
```

## Tổng hợp các mô hình AI/ML trong kiến trúc

| Mô hình AI/ML | Bài toán giải quyết & Đầu ra | Cấp độ ưu tiên | Giả thuyết kiểm định |
|---|---|---|---|
| **1. `LGBMRanker` (LambdaMART LTR)** | Xếp hạng chung các ứng viên hợp lệ của mọi dịch vụ trong một danh sách `Top-K` theo sở thích ngữ cảnh của hành khách. | **MUST (M11)** | **H1, H2, H9** *(tất cả đều thuộc MUST)* |
| **2. Mô hình `P(match)`** | Dự báo xác suất một booking `CAR_URBAN_POOL` kết thúc ở trạng thái ghép thành công (`MATCHED_LOCKED` = 1 vs `UNMATCHED_LOCKED` = 0). | **MUST (M11)** | **H3 (MUST)** |
| **3. Tổ hợp mô hình `P(fulfill)`** | Dự báo xác suất chuyến đi hoàn thành tới đích (`COMPLETED` = 1) theo cây sự kiện tuần tự 3 cổng (Mục 39). | **SHOULD (S2)** | **H5 (SHOULD)** |
| **4. Hiệu chỉnh xác suất (`Calibration`)** | Hiệu chỉnh điểm LTR (Temperature Scaling) và hiệu chỉnh xác suất `P(match)`, `P(fulfill)` (Isotonic / Platt). | **MUST (cho `P(match)`) / SHOULD (S3 cho LTR)** | **H3, H5** |
| **5. Dự báo nhu cầu Pool theo vùng (`Demand Forecast`)** | Dự báo số lượng yêu cầu `CAR_URBAN_POOL` phát sinh trong mỗi `(zone × 15 phút)` tiếp theo. | **COULD (C2)** | Bổ trợ đặc trưng cho `P(match)` |
| **6. Mô hình `P(fill)` liên tỉnh** | Dự báo xác suất một chuyến ghép liên tỉnh đạt ngưỡng `min_seats_to_run` tại mốc `T−72h`. | **COULD (C10)** | **H11 (COULD)** |
| **7. Chatbot LLM Trip Intent** | Trích xuất cấu trúc JSON `Trip Intent` từ câu yêu cầu tiếng Việt tự nhiên của hành khách. | **COULD (C1)** | Đánh giá độ chính xác trích xuất slot (Slot F1) |

---

# 44. MÔ HÌNH LEARNING-TO-RANK (LTR) XẾP HẠNG ĐA PHƯƠNG TIỆN VÀ THIẾT KẾ CHẨN ĐOÁN 2×2

## 44.1. Định nghĩa Đơn vị truy vấn (Query Group), Ứng viên (Item) và Nhãn huấn luyện (Label)
- **Một nhóm truy vấn (`query_group` = `request_id`):** Tương ứng với một lần hành khách gửi `Trip Intent` và hệ thống sinh ra danh sách $M$ ứng viên hợp lệ ($M \ge 2$). Trong phân khúc nội đô 1 khách, cùng một `query_group` chứa hỗn hợp các ứng viên của cả `BIKE_URBAN`, `CAR_URBAN_PRIVATE` và `CAR_URBAN_POOL`.
- **Nhãn huấn luyện (`label`):** Nhị phân `selected ∈ {0, 1}` (`1` cho ứng viên được hành khách chọn trong danh sách hiển thị, `0` cho các ứng viên được hiển thị cùng lần nhưng không được chọn).
- **Thuật toán học:** `LightGBM LGBMRanker` với hàm mất mát `lambdarank` (LambdaMART), tối ưu hóa trực tiếp chỉ số `NDCG@5`.

## 44.2. Danh mục Đặc trưng đầu vào (Feature Schema — Chỉ dùng thông tin quan sát được tại thời điểm xếp hạng)

```text
1. Nhóm đặc trưng Dịch vụ & Phương tiện (Service & Mode Features):
   - service_code (categorical), vehicle_type (BIKE / CAR4), is_pool (0/1), mode (URBAN / INTERCITY),
     booking_type (NOW / SCHEDULED), candidate_source_type (EXISTING_POOL_PLAN vs NEW_SINGLE_VEHICLE).

2. Nhóm đặc trưng Ngữ cảnh & Thời tiết (Context Features):
   - hour_of_day (mã hóa sin/cos và bucket cao điểm sáng/chiều/đêm), day_of_week, is_weekend,
     is_raining (0/1), has_luggage (0/1), origin_zone_id, dest_zone_id.

3. Nhóm đặc trưng Yêu cầu chuyến đi (Trip Request Features):
   - direct_distance_km, direct_duration_min, passenger_count,
     pickup_window_width_min (T_latest - T_earliest), budget_min, budget_max,
     lead_time_hours (T_preferred - now), max_passenger_detour_ratio, max_walk_m.

4. Nhóm đặc trưng Ứng viên & Giá (Candidate & Pricing Features):
   - effective_price (Fare_charged cho xe cố định; ExpectedPrice cho CAR_URBAN_POOL),
     pool_quote_price (Quote_i), pool_unmatched_price (Unmatched_i), fare_matched_est,
     savings_vs_car_private_pct, price_to_budget_max_ratio (effective_price / B_max),
     planned_pickup_eta_min, schedule_deviation_min (|planned_pickup - T_preferred|),
     in_vehicle_duration_min, detour_ratio, extra_stops_count, walk_distance_m (C9),
     driver_rating_bayesian, seats_currently_occupied, p_match_oof_est, p_fulfill_oof_est.

5. Nhóm đặc trưng Tương tác phi tuyến thiết kế (Engineered Interaction Features):
   - is_bike × is_raining                           (Tương tác xe máy gặp trời mưa)
   - is_bike × direct_distance_km                   (Mức độ mỏi khi đi xe máy quãng dài)
   - is_pool × detour_ratio × (1 / pickup_window_width_min) (Tương tác đi vòng khi khách đang vội)
   - (effective_price - B_min) / (B_max - B_min)    (Vị trí giá trong khoảng ngân sách)

6. Nhóm đặc trưng Lịch sử hành vi người dùng (Historical User Aggregates — tính strictly trước thời điểm t):
   - user_hist_trip_count, user_hist_bike_share, user_hist_pool_share, user_hist_private_share,
     user_hist_avg_paid_per_km, user_hist_cancel_rate (làm mượt Beta cho người dùng mới).
```

## 44.3. Báo cáo phân tách theo phân khúc (Segmented Evaluation) và Nâng `H9` lên MUST (`[ACCEPTED]` — P0-08)

Để chứng minh thuyết phục rằng mô hình LTR thực sự học được sự đánh đổi đa phương thức chứ không chỉ ăn may nhờ các chuyến đơn giản, kết quả đánh giá bắt buộc phải báo cáo cả **Toàn cục (Overall)** và **Tách theo 3 phân khúc chuẩn**:
1. **Phân khúc 1 (Trọng tâm của Giả thuyết H9 — MUST):** Nội đô, 1 hành khách, không hành lý lớn (`Top-K` trộn cả `BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`).
2. **Phân khúc 2:** Nội đô, nhóm 2+ hành khách hoặc có hành lý lớn (`Top-K` chỉ gồm `CAR_URBAN_PRIVATE` và `CAR_URBAN_POOL`).
3. **Phân khúc 3:** Liên tỉnh (`CAR_INTERCITY_PRIVATE` và `CAR_INTERCITY_POOL`).

## 44.4. Ma trận thực nghiệm Chẩn đoán 2×2 (2×2 Ablation Diagnostic — Giả thuyết H2)

| Мо hình \ Tập đặc trưng | **Cấu hình A: Đặc trưng thô (Raw Features — Nhóm 1, 2, 3, 4, 6)** | **Cấu hình B: Đầy đủ đặc trưng tương tác (Raw + Nhóm 5 Engineered Interactions)** |
|---|---|---|
| **Mô hình Tuyến tính (`Conditional Logit / Linear Ranker`)** | Ô `(1, 1)`: Tuyến tính trên đặc trưng thô | Ô `(1, 2)`: Tuyến tính có đặc trưng tương tác thiết kế tay |
| **Mô hình Phi tuyến cây quyết định (`LightGBM LambdaMART`)** | Ô `(2, 1)`: LTR tự học tương tác từ đặc trưng thô | Ô `(2, 2)`: LTR trên tập đặc trưng đầy đủ |

Ma trận 2×2 này giúp hội đồng khoa học nhìn thấy rõ: phần cải thiện chất lượng xếp hạng đến từ khả năng tự học cấu trúc phi tuyến/ngưỡng của cây quyết định (`Ô (2,1)` vs `Ô (1,1)`) hay đến từ việc thiết kế đặc trưng miền ứng dụng (`Ô (1,2)` vs `Ô (1,1)`).

---

# 45. MÔ HÌNH DỰ BÁO XÁC SUẤT GHÉP THÀNH CÔNG `P(MATCH)` VÀ QUY TRÌNH HUẤN LUYỆN OUT-OF-FOLD

## 45.1. Định nghĩa Bài toán và Nhãn quan sát
- **Quần thể quan sát:** Toàn bộ các booking thuộc dịch vụ `CAR_URBAN_POOL` đã được xác nhận (`ride_status` đạt ít nhất `CONFIRMED` và đi tới điểm khóa giá `pool_lock_point`).
- **Nhãn nhị phân (`y_match`):**
  - `y_match = 1` nếu tại `pool_lock_point`, `price_status == MATCHED_LOCKED` (có ít nhất 1 booking độc lập khác cùng ngồi trên xe tối thiểu 1 chặng).
  - `y_match = 0` nếu tại `pool_lock_point`, `price_status == UNMATCHED_LOCKED` (với `unmatched_cause == NO_COMPATIBLE`).

## 45.2. Đặc trưng đầu vào (Strictly Point-in-Time tại thời điểm báo giá $t_{\text{quote}}$)
```text
- Không gian & Thời gian: origin_zone_id, dest_zone_id, corridor_direction_bucket, hour_of_day, day_of_week, is_raining.
- Trạng thái ứng viên tại t_quote:
  + is_existing_plan (1 nếu ứng viên là xe đang có sẵn khách khác trên xe → P(match) = 1,00 tất định!;
                      0 nếu ứng viên là xe rảnh khởi tạo kế hoạch Pool mới).
  + active_pool_requests_15m_in_origin_zone (số yêu cầu Pool phát sinh quanh điểm đón trong 15 phút vừa qua).
  + open_pool_plans_same_direction_in_radius (số kế hoạch Pool đang mở cùng hướng trong bán kính R).
- Đặc tính chuyến đi của khách:
  + direct_distance_km (chuyến càng dài thì thời gian cửa sổ mở trước khi chạm 3 km cuối càng lớn!),
  + max_passenger_detour_ratio, pickup_window_width_min, seat_count (1 ghế dễ ghép hơn 2 ghế),
  + booking_type (SCHEDULED có thời gian gom khách dài hơn NOW),
  + accepts_meeting_point (max_walk_m > 0, nếu bật C9),
  + zone_demand_forecast_next_15m (nếu bật C2).
```
*(Lưu ý quan trọng: Nếu ứng viên đang xét thuộc Nhánh A ở Mục 35.2 — tức chèn trực tiếp vào một kế hoạch đang mở đã có sẵn hành khách khác trên xe — thì ngay khi chèn, booking này đã có người đi chung, do đó xác suất ghép với người hiện hữu tiệm cận $1,00$ trừ xác suất người kia hủy sớm; mô hình ML `P(match)` chủ yếu giải quyết sự bất định cho các ứng viên Nhánh B khởi tạo kế hoạch Pool mới từ xe rảnh).*

## 45.3. Các mốc đối chứng (Baselines), Hiệu chỉnh và Quy trình Out-of-Fold chống rò rỉ (`[ACCEPTED]` — P1-07)
- **Mốc 1 (Global Baseline):** Tỷ lệ ghép thành công trung bình toàn cục trên tập `train`.
- **Mốc 2 (Spatio-Temporal Empirical Baseline):** Tỷ lệ ghép thành công lịch sử theo bảng tra `(origin_zone_id, dest_zone_id, hour_bucket)` có làm mượt Beta.
- **Mô hình học máy:** `Logistic Regression` và `LightGBM Classifier`, sau đó đi qua bộ **Hiệu chỉnh xác suất Isotonic Regression (hoặc Platt Scaling)** khớp trên tập `validation` để đảm bảo xác suất đầu ra phản ánh đúng tần suất thực tế (đo bằng `Brier Score`, `Log-Loss`, `ROC-AUC` và `ECE — Expected Calibration Error <= 0.05`).
- **Quy trình huấn luyện Out-of-Fold (OOF Cross-Fitting) bắt buộc để chống rò rỉ sang LTR (`[ACCEPTED]` — P1-07):**
  Vì đầu ra `p_match_est` (và `ExpectedPrice`) là đặc trưng đầu vào của mô hình xếp hạng `LGBMRanker` (Mục 44), nếu huấn luyện `P(match)` trên tập `Train` rồi dùng chính mô hình đó dự đoán in-sample trên tập `Train` cho `LGBMRanker`, `p_match_est` trên tập `Train` sẽ có độ chính xác cao giả tạo so với tập `Test` (gây Distribution Shift). Do đó:
  1. Trên tập `Train`, chia thành $K = 5$ folds theo khối thời gian; với mỗi fold $k$, huấn luyện `P(match)` trên $4$ folds còn lại để sinh dự đoán Out-of-Fold `p_match_oof_est` cho fold $k$.
  2. Huấn luyện một mô hình `P(match)_full` trên toàn bộ tập `Train` (hiệu chỉnh trên `Validation`) để dùng lúc suy luận trên tập `Test` và vận hành trực tuyến.

---

# 46. MÔ HÌNH HOÀN THÀNH CHUYẾN CÓ ĐIỀU KIỆN VÀ XỬ LÝ RỦI RO CẠNH TRANH (SHOULD S2)

Tuân thủ cấu trúc Cây sự kiện tuần tự 3 cổng đã chuẩn hóa tại Mục 39.1 & 39.2:
1. **Mô hình Cổng 1 — $P(\text{accepted} \mid x)$:** Huấn luyện trên tập tất cả các `offers` đã gửi đi (`driver_accepted ∈ {0, 1}`), sử dụng đặc trưng khoảng cách tiếp cận của tài xế tới điểm đón, thu nhập dự kiến/giờ của chuyến, thời tiết mưa, và lịch sử nhận chuyến làm mượt Beta của tài xế.
2. **Mô hình Cổng 2 — $P(\text{ride\_started} \mid \text{accepted}, x)$:** Huấn luyện trên tập con các booking có `driver_accepted == 1` (hoặc các chuyến liên tỉnh đã xác nhận tại `T−72h`). Nhãn là `1` nếu đạt `RIDE_STARTED`, `0` nếu bị hủy bởi tài xế, hủy bởi khách, hoặc `NO_SHOW`. Việc gộp chung các nhánh thất bại trước khi đón vào một bộ phân loại có điều kiện duy nhất giúp loại bỏ hoàn toàn hiện tượng ẩn nhãn do rủi ro cạnh tranh (Competing Risks censoring).
3. **Mô hình Cổng 3 — $P(\text{completed} \mid \text{ride\_started}, x)$:** Sử dụng tỷ lệ hoàn thành làm mượt Beta (do tỷ lệ hoàn thành sau khi khách đã lên xe đạt $> 99\%$).
4. **Mốc đối chứng trong thí nghiệm H5:** So sánh xếp hạng chỉ dùng `p_hat_i` (không xét `p_fulfill`) với xếp hạng nhân `p_hat_i × p_fulfill_i` (dùng mô hình học máy so với mốc Beta-smoothed và trần thông tin hoàn hảo Oracle của Simulator).

---

# 47. HIỆU CHỈNH XÁC SUẤT (CALIBRATION) VÀ CÔNG THỨC ĐIỂM XẾP HẠNG CUỐI CÙNG

Điểm số đầu ra thô $s_i = \text{LGBMRanker}(x_i) \in (-\infty, +\infty)$ của mô hình LambdaMART chỉ mang ý nghĩa thứ tự tương đối trong cùng một nhóm truy vấn, **không phải là xác suất**.

Để kết hợp một cách có cơ sở toán học với xác suất hoàn thành chuyến $p_{\text{fulfill}}(i) \in [0, 1]$, hệ thống thực hiện chuẩn hóa Softmax có tham số nhiệt độ $T > 0$ (Temperature Scaling — hạng mục **S3**):

```text
p_hat_select(i) = exp( s_i / T ) / Σ_{j ∈ CandidateGroup} exp( s_j / T )
```
Tham số nhiệt độ $T$ được tối ưu hóa bằng cách cực tiểu hóa hàm `Negative Log-Likelihood (NLL)` theo nhóm trên tập `Validation`.

**Quy tắc hợp nhất điểm xếp hạng cuối cùng (`FinalScore_i`):**
```text
- Khi ở cấu hình MUST (chưa bật S2/S3) : FinalScore(i) = s_i (Xếp hạng trực tiếp theo điểm LTR, trong đó
                                          LTR đã sử dụng ExpectedPrice tính từ P(match) đã hiệu chỉnh).
- Khi bật đầy đủ S2 và S3 (ECE <= 0.05): FinalScore(i) = p_hat_select(i) × p_fulfill(i)
                                          (Tối đa hóa xác suất kỳ vọng khách vừa chọn vừa hoàn thành chuyến!).
```
*Quy tắc hiển thị trung thực trên UI:* Hệ thống tuyệt đối không hiển thị các con số phần trăm vô căn cứ kiểu *"95% phù hợp với bạn"* trên giao diện; đối với khả năng ghép thành công `P(match)`, giao diện hiển thị nhãn định tính 3 mức (`Cao` khi $P \ge 0.65$, `Trung bình` khi $0.35 \le P < 0.65$, `Thấp` khi $P < 0.35$), và chỉ hiển thị con số xác suất trong trang giám sát của Admin sau khi qua cổng kiểm định ECE.

---

# 48. THIẾT KẾ SIMULATOR 5 DỊCH VỤ TÁI LẬP ĐƯỢC VÀ CƠ CHẾ CHỐNG RÒ RỈ BIẾN ẨN

Vì các tập dữ liệu chuyến đi công khai trên thế giới (như NYC TLC hay Chicago TNP) chỉ ghi nhận chuyến đi đã thực hiện mà **không chứa danh sách các ứng viên thay thế (unchosen alternatives) hiển thị trên màn hình lúc người dùng đặt xe**, việc xây dựng một bộ Simulator đa tác tử (Multi-Agent Discrete-Event Simulator) được hiệu chỉnh từ khảo sát lựa chọn người thật (S1) là phương pháp chuẩn mực trong nghiên cứu hệ thống gợi ý giao thông (McFadden, 1974; Train, 2009; Alonso-Mora et al., 2017).

## 48.1. Mô hình hành vi lựa chọn ẩn của Hành khách (Heterogeneous Non-Linear Passenger Utility)

Mỗi tác tử hành khách $u$ trong Simulator mang một vector tham số sở thích cá nhân ẩn $\boldsymbol{\theta}_u$ được lấy mẫu từ phân phối đa biến đã hiệu chỉnh qua khảo sát S1 (Mục 65):
```text
Vector biến ẩn của hành khách u (TUYỆT ĐỐI KHÔNG LỘ CHO MÔ HÌNH ML):
  - theta_price_u        : Độ nhạy cảm với giá cước (phân phối Log-Normal theo nhóm thu nhập: sinh viên vs đi làm)
  - price_gamma_u        : Số mũ độ cong phi tuyến đối với giá (γ > 1: phạt nặng khi giá tiến sát B_max)
  - theta_time_u         : Giá trị thời gian (Value of Time — đ/phút)
  - wait_threshold_u     : Ngưỡng kiên nhẫn chờ xe đón (vượt ngưỡng này điểm tiện ích bị phạt bậc hai)
  - theta_detour_u       : Mức độ ghét phải ngồi đi vòng
  - theta_comfort_u      : Mức độ ưu tiên sự thoải mái / riêng tư của ô tô so với xe máy
  - rain_aversion_bike_u : Hệ số phạt tương tác đặc biệt khi đi xe máy dưới trời mưa (tăng theo quãng đường)
  - pooling_aversion_u   : Tâm lý ngại đi chung xe với người lạ
  - walk_tolerance_m_u   : Quãng đi bộ tối đa thực sự chấp nhận (C9)
  - plan_ahead_tendency_u: Xu hướng lập kế hoạch sớm (quyết định hành vi đặt liên tỉnh trước >= 3 ngày)
  - noise_scale_u        : Phương sai nhiễu cực trị Gumbel (Extreme Value Type I noise ε_{u,i})
```

Hàm tiện ích thực ẩn $U^*_{\text{true}}(u, i)$ của hành khách $u$ đối với ứng viên $i$ chứa đầy đủ **các thành phần phi tuyến, điểm gãy ngưỡng (threshold kink) và tương tác bậc ba** (như $\text{is\_bike}_i \times \text{is\_raining} \times D_{\text{direct}}^{1.2}$, hoặc kỳ vọng phi tuyến theo cảm nhận rủi ro không ghép được). Hành khách chọn ứng viên $i^* = \arg\max_{i \in \text{TopK} \cup \{\text{OutsideOption}\}} [U^*_{\text{true}}(u, i) + \varepsilon_{u,i}]$. Thiết kế này đảm bảo hàm sinh dữ liệu phức tạp hơn hẳn hàm tuyến tính của Baseline, tạo ra bài kiểm tra công bằng xem LTR có khôi phục được quy luật lựa chọn ẩn từ dữ liệu quan sát hay không.

## 48.2. Cơ chế mô phỏng mạng lưới Nội đô (3 dịch vụ)
- **Quá trình sinh nhu cầu:** Quá trình Poisson không thuần nhất theo thời gian ($\lambda(z, t)$ thay đổi theo từng khung 15 phút), sử dụng ma trận Origin–Destination (OD) thực tế giữa các quận/huyện Hà Nội, tăng trọng số các hành lang hướng tâm (Hà Đông / Hoài Đức / Thanh Trì $\to$ Thanh Xuân / Đống Đa / Cầu Giấy) vào cao điểm sáng (06:30–09:00) và chiều ngược lại vào cao điểm chiều (16:30–19:00).
- **Quá trình thời tiết:** Chuỗi Markov hai trạng thái (`DRY` $\leftrightarrow$ `RAIN`) theo giờ, cấu hình tỷ lệ giờ mưa `rain_share ∈ {0.10, 0.30}`.
- **Động lực học ghép xe thật 100%:** Simulator **không tung đồng xu giả lập việc ghép thành công**, mà gọi trực tiếp vào **chính engine sinh ứng viên, chèn điểm động (Mục 36), ghép theo lô (Mục 37) và phân bổ giá (Mục 15) của hệ thống thật**! Một booking `CAR_URBAN_POOL` chỉ đạt `MATCHED_LOCKED` trong Simulator khi thực sự có một tác tử hành khách khác trong Simulator đặt chuyến tương thích và được thuật toán ghép chung vào cùng `ride_plan` trước khi xe chạy qua `pool_lock_point`.
- **Hành vi tài xế chiến lược:** Một tỷ lệ tài xế (`strategic_driver_share ∈ {0.0, 0.1, 0.3}`) được lập trình hành vi thử từ chối khách ghép khi thấy bất lợi để kiểm chứng hiệu lực của chế tài cắt bảo đảm tại Mục 18.5.

## 48.3. Cơ chế mô phỏng mạng lưới Liên tỉnh (2 dịch vụ)
- Trên 5–10 hành lang liên tỉnh mẫu (Hà Nội đi Hưng Yên, Bắc Ninh, Hải Dương, Hà Nam, Vĩnh Phúc):
  - Tài xế đăng lịch chuyến ghép theo phân phối tuần từ `D−7` đến `D−3`.
  - Các tác tử hành khách phát sinh nhu cầu theo đường cong thời gian đặt trước từ `D−7` đến `D−0`: những hành khách có nhu cầu phát sinh sớm ($\ge 72\text{h}$) có cả 2 lựa chọn `CAR_INTERCITY_POOL` và `CAR_INTERCITY_PRIVATE`; những hành khách phát sinh nhu cầu sát ngày ($< 72\text{h}$) bị luật Mục 2.2 chặn `CAR_INTERCITY_POOL` và phải quyết định giữa việc đặt `CAR_INTERCITY_PRIVATE` hoặc từ bỏ chuyến đi (`OutsideOption`).
  - Tại mốc `T−72h` và `T−60h` trong đồng hồ mô phỏng, Simulator thực thi đúng quy trình Gộp chuyến, Đề nghị góp thêm (hành khách trả lời `ACCEPT`/`DECLINE` dựa trên việc `TopupSeatPrice` có nhỏ hơn ngưỡng sẵn lòng chi trả ẩn của họ hay không) và Hủy hoàn tiền.

## 48.4. Cơ chế Tái lập kết quả (Deterministic Reproducibility) và Tường lửa Chống rò rỉ
- Toàn bộ bộ sinh số ngẫu nhiên (`numpy.random.Generator` / `PCG64`) của nhu cầu, thời tiết, vị trí khởi tạo tài xế và nhiễu lựa chọn Gumbel đều được dẫn xuất tất định từ một `master_seed` duy nhất. Chạy lại cùng một `master_seed` trên cùng cấu hình phải cho ra bộ dữ liệu có mã băm `SHA-256` trùng khớp 100%.
- **Tường lửa xuất dữ liệu (`Feature Export Firewall`):** Module xuất bảng dữ liệu huấn luyện Parquet chỉ có quyền đọc từ các bảng giao dịch quan sát được (`trip_requests`, `ride_candidates`, `recommendation_items`, `bookings`), hoàn toàn không có tham chiếu bộ nhớ tới đối tượng `SimulatedPassengerHiddenState`.

---

# 49. XỬ LÝ KHỞI ĐẦU LẠNH (COLD START) VÀ THIÊN LỆCH VỊ TRÍ HIỂN THỊ (POSITION BIAS)

- **Khởi đầu lạnh cho tài xế và người dùng mới:** Mọi đặc trưng thống kê lịch sử (điểm đánh giá tài xế, tỷ lệ nhận offer, tỷ lệ chọn xe ghép của khách) đều được tính qua công thức làm mượt Beta với prior bằng trung bình toàn cục. Ở hạng mục mở rộng **C5**, hệ thống dành tối đa 1 vị trí trong `Top-K` (với xác suất $\epsilon = 0.10$) cho tài xế mới có ít hơn 10 chuyến đi (`shown_reason = NEW_DRIVER_EXPLORATION`).
- **Ghi log chống thiên lệch vị trí (`Position Bias Logging`):** Người dùng có xu hướng bấm chọn vị trí #1 và #2 nhiều hơn do vị trí hiển thị. Mọi bản ghi trong `recommendation_items` đều lưu bắt buộc `shown_position` ($1..K$), `shown_reason` và xác suất hiển thị `exposure_propensity` để phục vụ trọng số nghịch đảo `Inverse Propensity Scoring (IPS)` khi mở rộng C5.

---

# 50. CHATBOT CHUYỂN ĐỔI NGÔN NGỮ TỰ NHIÊN THÀNH TRIP INTENT (COULD C1)

- **Kiến trúc an toàn (Human-in-the-loop Structured Extraction):** Khi người dùng nhập câu tự nhiên (ví dụ: *"Thứ Bảy tuần sau mình muốn về TP Hưng Yên từ Hà Đông lúc 8h sáng, đi ghép 1 người, có 1 vali to, ngân sách dưới 300k"*), mô hình LLM trích xuất chuỗi JSON tuân thủ nghiêm ngặt Pydantic Schema của `Trip Intent` (Mục 6):
  ```json
  {
    "vehicle_preference": "CAR",
    "ride_preference": "POOL",
    "pickup_text": "Hà Đông, Hà Nội",
    "destination_text": "TP Hưng Yên",
    "passenger_count": 1,
    "preferred_departure": "2026-10-31T08:00:00+07:00",
    "budget_max": 300000,
    "has_luggage": true
  }
  ```
- Kết quả JSON đi qua bước phân giải tọa độ (Geocoding) và điền sẵn vào biểu mẫu `K1` trên màn hình để **hành khách kiểm tra và bấm xác nhận**, sau đó vẫn phải đi qua đúng bộ kiểm tra luật thời gian đặt và 11 ràng buộc cứng ở Mục 6–7. Chatbot tuyệt đối không bao giờ tự động đặt xe hay tự động khóa ký quỹ mà không có thao tác xác nhận của người dùng.

---

# 51. DỰ BÁO NHU CẦU TAXI GHÉP THEO KHU VỰC × 15 PHÚT (COULD C2)

- **Định nghĩa bài toán:** Dự báo số lượng yêu cầu `CAR_URBAN_POOL` phát sinh tại mỗi ô khu vực `zone_id` trong khung 15 phút kế tiếp $\hat{y}_{z, t+1}$.
- **Đặc trưng đầu vào:** `zone_id`, khung giờ, thứ trong tuần, trạng thái mưa `is_raining`, chuỗi trễ số lượng yêu cầu trong `15 / 30 / 45 / 60 phút` vừa qua tại chính `zone_id` đó và tại các `zone` lân cận giáp ranh, cùng trung bình trượt của cùng khung giờ ở các tuần trước.
- **Mô hình & Mốc so sánh:** So sánh `LightGBM Regressor` (hàm mất mát Poisson / Tweedie) với mốc `Seasonal Naive` (lấy giá trị cùng khung giờ tuần trước) theo chỉ số `MAE` và `WAPE` (tách riêng nhóm zone trung tâm đông đúc và nhóm zone ven đô).
- **Ứng dụng:** (1) Cung cấp đặc trưng `zone_demand_forecast_next_15m` cho mô hình `P(match)` (Mục 45); (2) Hiển thị bản đồ nhiệt nhu cầu trên màn hình tài xế `T6`.

---

# 52. MÔ HÌNH DỰ BÁO XÁC SUẤT ĐỦ GHẾ LIÊN TỈNH `P(FILL)` (COULD C10)

- **Định nghĩa bài toán:** Tại thời điểm truy vấn $t \in [T-7\text{ ngày}, T-72\text{h})$, dự báo xác suất một chuyến ghép liên tỉnh `scheduled_trip` sẽ đạt `seats_booked >= min_seats_to_run` trước khi đóng sổ tại mốc `T−72h` (kiểm định tại Giả thuyết **H11**).
- **Đặc trưng đầu vào tại thời điểm $t$:** Số ghế hiện đã đặt `seats_booked(t)`, số ghế còn thiếu `max(0, min_seats_to_run - seats_booked(t))`, tốc độ đặt ghế trong 24 giờ gần nhất, thời gian còn lại tới mốc khóa sổ `(T - 72h) - t`, mã hành lang `corridor_id`, thứ và khung giờ khởi hành, tỷ lệ giá ghế của chuyến so với `SeatReference` (`seat_price / SeatReference`), số chuyến ghép cạnh tranh cùng hành lang trong khoảng $\pm 60$ phút, và số lượng khách đang nằm trong `intercity_waitlist` của tuyến đó.
- **Mô hình & Đánh giá:** `Logistic Regression` và `LightGBM Classifier` kèm hiệu chỉnh Isotonic, so sánh với mốc tỷ lệ lấp ghế lịch sử làm mượt Beta theo `(corridor_id, seats_booked)` trên các chỉ số `Brier Score`, `ROC-AUC` và `ECE`.

---

# PHẦN VII — KIẾN TRÚC PHẦN MỀM, CƠ SỞ DỮ LIỆU, API, BẢO MẬT, AN TOÀN VÀ PHÁP LÝ

# 53. NGĂN XẾP CÔNG NGHỆ (TECHNOLOGY STACK)

```text
Frontend        : Next.js (App Router), TypeScript, Tailwind CSS, MapLibre GL / Leaflet, WebSocket
Backend         : Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async/Sync), Alembic
Cơ sở dữ liệu   : PostgreSQL 16 + PostGIS 3.4 (Lưu dữ liệu giao dịch, hình học không gian, sổ cái, bảng job)
Bộ nhớ đệm/Khóa : Redis 7 (Lưu tọa độ thời gian thực của tài xế, cache ma trận OSRM, rate-limiting)
Động cơ Routing : OSRM Local (2 container Docker: profile car + profile motorbike) trên dữ liệu OSM Việt Nam
AI / Học máy    : Polars / Pandas, scikit-learn, LightGBM (LGBMRanker, Classifier, Regressor), IsotonicRegression
Tối ưu tổ hợp   : Google OR-Tools CP-SAT (Giải bài toán ghép theo lô trên đồ thị RTV rút gọn)
Lưu trữ Offline : Apache Parquet (Dataset huấn luyện, log hiển thị, model artifacts theo phiên bản)
Chuỗi khối      : Nền tảng Hợp đồng thông minh EVM hiện có (Solidity + Hardhat, mạng thử nghiệm Testnet)
Hạ tầng đóng gói: Docker Compose (Khởi chạy toàn bộ hệ sinh thái bằng 1 lệnh duy nhất)
```

---

# 54. PHÂN RÃ MODULE VÀ RANH GIỚI GIAO TIẾP TRONG MODULAR MONOLITH

Hệ thống được tổ chức thành 16 module nghiệp vụ có ranh giới sở hữu dữ liệu rõ ràng (`[ACCEPTED]` — D-31):

| Tên Module | Trách nhiệm cốt lõi | Bảng CSDL sở hữu chính (Write Ownership) |
|---|---|---|
| `identity` | Đăng ký, đăng nhập, cấp phát JWT + Refresh Token, kiểm soát RBAC (`PASSENGER`, `DRIVER`, `ADMIN`). | `users`, `user_preferences` |
| `driver` | Hồ sơ tài xế, quản lý phương tiện (`BIKE`, `CAR4`), trạng thái trực tuyến, cấu hình Pool/liên tỉnh, duyệt KYC mock (S7). | `driver_profiles`, `vehicles`, `driver_locations`, `driver_reliability_stats` |
| `trip` | Tiếp nhận `Trip Intent`, phân loại `URBAN / INTERCITY` có vùng đệm (Mục 2.3), kiểm tra luật thời gian đặt, quản lý mẫu chuyến quen (C4). | `trip_requests`, `service_areas`, `recurring_trip_templates` |
| `routing` | Giao tiếp với 2 container OSRM (`car`, `motorbike`), quản lý cache ma trận trên Redis, sinh điểm đón gặp nhau (C9). | `pickup_points` |
| `candidate` | Điều phối luồng sinh ứng viên cho 5 dịch vụ, kiểm tra 11 ràng buộc cứng (Mục 7), bảo toàn đa dạng dịch vụ trong Top-K (Mục 35.5). | `ride_candidates` |
| `pooling` | Quản lý vòng đời kế hoạch ghép nội đô (`ride_plans`), thuật toán chèn điểm động (Mục 36), theo dõi và kích hoạt `pool_lock_point`. | `ride_plans`, `ride_stops`, `ride_participants` |
| `batch_matcher` | Gom các yêu cầu `POOL_SEARCHING` mỗi $\Delta = 30\text{s}$, xây dựng đồ thị RTV rút gọn và giải bằng CP-SAT (Mục 37). | `batch_match_runs` |
| `intercity` | Đăng chuyến ghép liên tỉnh, đặt ghế, thực thi quy trình chốt chuyến `T−72h`, gộp chuyến (Mục 30), góp thêm (Mục 29), tối ưu thứ tự đón `T−24h` (Mục 31). | `scheduled_trips`, `seat_bookings`, `trip_topup_offers`, `intercity_waitlist` |
| `pricing` | Thực thi toàn bộ công thức định giá 5 dịch vụ, phân bổ kẹp hai đầu `[Floor_i, Cap_i]` (Mục 15.3), đóng băng giá đã khóa (Mục 15.5) và tính phí hủy (Mục 18.7). | `pricing_configs` |
| `fund` | Quản lý sổ cái Quỹ bảo đảm ghép (`CONTRIBUTION`, `GUARANTEE_PAYOUT`, `CANCEL_FEE_INFLOW`), tính điểm hòa vốn thực nghiệm `p*` và đối soát thu nhập tài xế. | `fund_ledger`, `driver_payouts` |
| `booking` | Quản lý `Per-Offer Seat Hold`, điều phối chuỗi `Offer Cascade` (Mục 41), chuyển trạng thái trực giao (`ride_status`, `price_status`), kiểm tra `Idempotency-Key`. | `bookings`, `seat_holds`, `offers`, `idempotency_records` |
| `ride` | Điều khiển hành trình thực tế (`RIDE_STARTED` có kiểm tra cổng ký quỹ, cập nhật GPS, `COMPLETED`, `abort` sự cố, đánh giá 2 chiều, SOS). | `ride_events`, `ride_ratings`, `safety_incidents` |
| `recommendation` | Chấm điểm Baseline (Mục 40) hoặc gọi `ml_models` lấy điểm LTR + xác suất, ghi log hiển thị (`shown_position`, `propensity`). | `recommendation_runs`, `recommendation_items` |
| `ml_models` | Quản lý vòng đời huấn luyện Offline (OOF `P(match)`, `P(fulfill)`, `LGBMRanker`, `P(fill)`, `Demand Forecast`) và nạp model artifacts theo phiên bản lúc suy luận. | `model_registry`, `zone_demand_forecasts`, `survey_responses` |
| `escrow_adapter` | Tương tác bất đồng bộ với hợp đồng thông minh trên Testnet (ký quỹ mức trần, hoàn chênh lệch, nạp thêm `topUp`, giải ngân 3 bên, đồng bộ sự kiện). | `escrow_transactions` |
| `jobs` | Quản lý bảng tác vụ định thời `scheduled_jobs` và tiến trình worker quét thực thi bằng khóa `FOR UPDATE SKIP LOCKED`. | `scheduled_jobs` |

---

# 55. THIẾT KẾ BẢNG TÁC VỤ ĐỊNH THỜI (`scheduled_jobs`) VÀ CƠ CHẾ THỰC THI AN TOÀN

Toàn bộ các mốc chuyển trạng thái theo thời gian trong hệ thống — bao gồm: (1) hết hạn `seat_hold`, (2) hết hạn `offer` 20s/60s, (3) kiểm tra quá hạn ký quỹ `120s`, (4) chu kỳ ghép theo lô $\Delta = 30\text{s}$, (5) sinh yêu cầu từ mẫu chuyến quen lúc `T−12h`, (6) đóng đặt chỗ và kiểm tra ngưỡng liên tỉnh lúc `T−72h`, (7) hết cửa sổ xác nhận gộp chuyến lúc `T−70h`, (8) hết hạn trả lời góp thêm lúc `T−66h`/`T−64h`, (9) hạn cuối quyết định của tài xế lúc `T−60h`, (10) chốt thứ tự đón lúc `T−24h`, và (11) tự động giải ngân ký quỹ (`autoRelease`) sau khi hoàn thành chuyến — đều được lưu trữ bền vững trong bảng `scheduled_jobs` của PostgreSQL:

```text
Bảng scheduled_jobs:
  id               BIGSERIAL PRIMARY KEY
  job_type         VARCHAR(64) NOT NULL
  target_id        UUID NOT NULL
  run_at           TIMESTAMPTZ NOT NULL
  status           VARCHAR(24) NOT NULL DEFAULT 'PENDING'
                   -- PENDING | PROCESSING | COMPLETED | COMPLETED_NOOP | FAILED_RETRY | DEAD_LETTER
  attempts         INT NOT NULL DEFAULT 0
  max_attempts     INT NOT NULL DEFAULT 5
  last_error       TEXT
  idempotency_key  VARCHAR(128) NOT NULL UNIQUE
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
```

Tiến trình Worker lấy các tác vụ đến hạn bằng câu lệnh nguyên tử:
```sql
SELECT id, job_type, target_id, idempotency_key, attempts
FROM scheduled_jobs
WHERE status IN ('PENDING', 'FAILED_RETRY')
  AND run_at <= now()
ORDER BY run_at ASC
FOR UPDATE SKIP LOCKED
LIMIT 50;
```
- **Ưu điểm vượt trội:** Việc tạo bản ghi `scheduled_job` nằm trong **cùng một giao dịch CSDL (ACID Transaction)** với thao tác nghiệp vụ sinh ra nó (ví dụ: tạo `offer` đồng thời tạo job `OFFER_TIMEOUT` sau 20 giây). Hệ thống không bao giờ bị mất tác vụ khi khởi động lại container và không cần duy trì hạ tầng Celery/RabbitMQ. Nếu một worker bị dừng đột ngột khi đang giữ `status = 'PROCESSING'` quá `visibility_timeout = 60 giây`, cơ chế thu hồi (reaper) tự động đẩy job về `FAILED_RETRY` kèm backoff hàm mũ.

---

# 56. THIẾT KẾ CƠ SỞ DỮ LIỆU, RÀNG BUỘC TOÀN VẸN (CONSTRAINTS) VÀ CHỈ MỤC (INDEXES)

## 56.1. Cập nhật Schema các bảng cốt lõi trong Revision 9

So với Revision 8, Revision 9 chuẩn hóa lại các bảng sau để phản ánh đúng Máy trạng thái trực giao (Mục 9), Quy tắc bảo vệ giá (Mục 15.5) và Đơn vị ký quỹ nguyên `1 VND` (Mục 80):

```text
1. vehicles
   id, driver_id, vehicle_type (BIKE | CAR4), license_plate (UNIQUE),
   capacity (BIKE = 1, CAR4 = 4), is_active

2. driver_profiles
   user_id (PK, FK → users.id), kyc_status (NONE | PENDING | VERIFIED | REJECTED),
   accepts_urban, pool_enabled, accepts_intercity,
   max_additional_pickups (0..3), max_driver_detour_km, max_driver_detour_min

3. trip_requests
   id (UUID PK), user_id (FK), mode (URBAN | INTERCITY),
   vehicle_preference (BIKE | CAR | ANY), ride_preference (PRIVATE | POOL | ANY),
   allowed_service_codes (TEXT[]), rejection_reasons_json (JSONB),
   booking_type (NOW | SCHEDULED), passenger_count (1..4), has_luggage (BOOL),
   pickup_geom (GEOMETRY(Point, 4326)), dropoff_geom (GEOMETRY(Point, 4326)),
   pickup_zone_id (INT), dropoff_zone_id (INT),
   preferred_departure, earliest_departure, latest_departure, latest_arrival,
   budget_min (BIGINT), budget_max (BIGINT),
   max_passenger_detour_ratio (FLOAT), max_in_vehicle_time_s (INT), max_walk_m (INT),
   categorical_preferences_json (JSONB), recurring_template_id (UUID NULL)

4. ride_plans (Kế hoạch vận hành của xe nội đô — đặc biệt là CAR_URBAN_POOL)
   id (UUID PK), driver_id (FK), vehicle_id (FK), service_code,
   status (PLAN_CREATED | PLAN_OPEN_SEARCHING | PLAN_CLOSED_TO_NEW | PLAN_COMPLETED | PLAN_ABORTED),
   completed_stop_index (INT DEFAULT -1),
   total_distance_km (FLOAT), total_duration_min (FLOAT), extra_stops_count (INT),
   plan_fare_vnd (BIGINT), driver_hourly_rate_vnd (BIGINT),
   plan_version (INT NOT NULL DEFAULT 1)

5. ride_candidates
   id (UUID PK), request_id (FK), service_code,
   candidate_source_type (NEW_SINGLE_VEHICLE | EXISTING_POOL_PLAN | SCHEDULED_INTERCITY_TRIP),
   target_plan_id (UUID NULL), scheduled_trip_id (UUID NULL), source_plan_version (INT),
   seat_count (INT), pickup_point_id (UUID NULL), walk_m (INT DEFAULT 0),
   private_fare_ref_vnd (BIGINT), effective_private_fare_vnd (BIGINT),
   pool_quote_price_vnd (BIGINT), pool_unmatched_price_vnd (BIGINT),
   fare_matched_est_vnd (BIGINT), expected_price_vnd (BIGINT), door_surcharge_vnd (BIGINT DEFAULT 0),
   shareability_ratio (FLOAT), p_match_est (FLOAT), p_fulfill_est (FLOAT), p_fill_est (FLOAT),
   model_versions_json (JSONB)

6. bookings (Tách 3 trục trạng thái trực giao: ride_status, price_status, escrow_status)
   id (UUID PK), request_id (FK), user_id (FK), driver_id (FK),
   service_code, booking_type (NOW | SCHEDULED), seat_count (INT NOT NULL DEFAULT 1),
   ride_plan_id (UUID NULL FK), scheduled_trip_id (UUID NULL FK),
   ride_status (HELD | CONFIRMED | RIDE_STARTED | COMPLETED | EXPIRED
                | CANCELLED_BY_PASSENGER | CANCELLED_BY_DRIVER | CANCELLED_BY_SYSTEM | NO_SHOW),
   price_status (QUOTED | FIXED_LOCKED | POOL_SEARCHING | MATCHED_LOCKED | UNMATCHED_LOCKED
                 | MERGED_REDUCED_LOCKED | TOPUP_LOCKED),
   escrow_status (NONE | DEPOSIT_PENDING | DEPOSITED | LOCKED | TOPPED_UP
                  | RELEASED | REFUNDED | ESCROW_FAILED | DISPUTED | RESOLVED),
   pool_quote_price_vnd (BIGINT), quoted_price_cap_vnd (BIGINT),
   current_estimated_price_vnd (BIGINT), final_price_vnd (BIGINT NULL),
   cancellation_fee_vnd (BIGINT DEFAULT 0),
   pool_lock_at (TIMESTAMPTZ NULL),
   unmatched_cause (NONE | NO_COMPATIBLE | DRIVER_DECLINED | CORIDER_CANCELLED_EARLY
                    | CORIDER_CANCELLED_LATE | PASSENGER_REJECTED_POOL),
   escrow_tx_deposit (VARCHAR), escrow_tx_lock_or_topup (VARCHAR), escrow_tx_settle (VARCHAR)

7. ride_participants (Chi tiết phân bổ giá và quãng đường của từng booking trong ride_plan)
   id (UUID PK), ride_plan_id (FK), booking_id (FK UNIQUE),
   seat_count (INT), private_fare_vnd (BIGINT), effective_private_fare_vnd (BIGINT),
   floor_fare_vnd (BIGINT), cap_fare_vnd (BIGINT), dynamic_cap_fare_vnd (BIGINT),
   traveled_km_before_last_replan (FLOAT DEFAULT 0),
   detour_ratio (FLOAT), walk_ratio (FLOAT), allocation_weight (FLOAT),
   fare_exact_vnd (NUMERIC(12, 2)), fare_charged_vnd (BIGINT), rounding_absorbed_vnd (NUMERIC(10, 2)),
   is_price_frozen (BOOL DEFAULT FALSE)

8. scheduled_trips (Chuyến ghép liên tỉnh do tài xế đăng)
   id (UUID PK), driver_id (FK), vehicle_id (FK), corridor_id (VARCHAR),
   departure_time (TIMESTAMPTZ), departure_flex_min (INT DEFAULT 30),
   seats_total (INT DEFAULT 4), seats_booked (INT DEFAULT 0),
   min_seats_ref (INT DEFAULT 3), min_seats_to_run (INT DEFAULT 3),
   seat_reference_vnd (BIGINT), seat_price_vnd (BIGINT),
   pickup_zone_ids (INT[]), dropoff_zone_ids (INT[]),
   status (PUBLISHED | OPEN_FOR_BOOKING | BOOKING_CLOSED | MERGE_PENDING_CONFIRMATION
           | CONFIRMED | TOPUP_OFFERED | CONFIRMED_TOPUP | UNDER_MIN_DRIVER_DECISION
           | CONFIRMED_UNDER_MIN | MERGED | CANCELLED_LOW_DEMAND | PICKUP_ORDER_FIXED
           | DEPARTED | COMPLETED),
   merged_into_trip_id (UUID NULL FK),
   plan_version (INT NOT NULL DEFAULT 1)

9. seat_bookings (Gắn kết booking với scheduled_trip)
   id (UUID PK), scheduled_trip_id (FK), booking_id (FK UNIQUE),
   seat_count (INT), pickup_geom (GEOMETRY(Point, 4326)), dropoff_geom (GEOMETRY(Point, 4326)),
   extra_pickup_km (FLOAT), extra_dropoff_km (FLOAT), door_surcharge_vnd (BIGINT),
   pickup_order (INT NULL), dropoff_order (INT NULL), planned_pickup_time (TIMESTAMPTZ NULL)

10. driver_payouts & fund_ledger
    - driver_payouts: id, booking_id (FK UNIQUE), driver_id (FK), gross_fare_charged_vnd (BIGINT),
                      driver_base_amount_vnd (BIGINT), guarantee_amount_vnd (BIGINT DEFAULT 0),
                      total_driver_payout_vnd (BIGINT), commission_rate (FLOAT),
                      platform_net_amount_vnd (BIGINT), fund_contribution_vnd (BIGINT DEFAULT 0)
    - fund_ledger   : id (BIGSERIAL PK), entry_type (CONTRIBUTION | GUARANTEE_PAYOUT | CANCEL_FEE_INFLOW | INITIAL_SEED),
                      booking_id (UUID NULL FK), amount_signed_vnd (BIGINT), balance_after_vnd (BIGINT),
                      onchain_tx_hash (VARCHAR NULL), created_at (TIMESTAMPTZ)
```

## 56.2. Ràng buộc toàn vẹn (Integrity Constraints) và Chỉ mục (Indexes) bắt buộc (`[ACCEPTED]` — P2-06)

1. **Ràng buộc kiểm tra miền giá trị (`CHECK Constraints`):**
   - Trên `scheduled_trips`:
     - `CHECK (seats_booked >= 0 AND seats_booked <= seats_total AND seats_total <= 4)`
     - `CHECK (min_seats_to_run IN (2, 3) AND min_seats_ref = 3)`
     - `CHECK (seat_price_vnd >= seat_reference_vnd * 9 / 10 AND seat_price_vnd <= seat_reference_vnd * 11 / 10)`
   - Trên `ride_participants`:
     - `CHECK (fare_exact_vnd >= floor_fare_vnd - 0.01 AND fare_exact_vnd <= cap_fare_vnd + 0.01)`
     - `CHECK (fare_charged_vnd >= 0 AND fare_charged_vnd <= cap_fare_vnd)`
   - Trên `bookings`:
     - `CHECK (final_price_vnd IS NULL OR final_price_vnd <= quoted_price_cap_vnd OR price_status = 'TOPUP_LOCKED')`
2. **Ràng buộc duy nhất chống trùng lặp (`UNIQUE Constraints`):**
   - `idempotency_records`: `UNIQUE (user_id, idempotency_key)`
   - `scheduled_jobs`: `UNIQUE (idempotency_key)`
   - `seat_holds`: Partial Unique Index ngăn 1 hành khách giữ 2 ghế đồng thời cho cùng 1 yêu cầu:
     `CREATE UNIQUE INDEX idx_active_hold_per_request ON seat_holds (request_id) WHERE status = 'ACTIVE';`
3. **Chỉ mục không gian và truy vấn nóng (`Spatial & Performance Indexes`):**
   - Chỉ mục không gian PostGIS (`GIST`):
     - `CREATE INDEX idx_driver_locations_geom ON driver_locations USING GIST (geom);`
     - `CREATE INDEX idx_service_areas_geom ON service_areas USING GIST (geom);`
     - `CREATE INDEX idx_pickup_points_geom ON pickup_points USING GIST (geom);`
   - Chỉ mục quét tác vụ định thời:
     - `CREATE INDEX idx_scheduled_jobs_due ON scheduled_jobs (run_at) WHERE status IN ('PENDING', 'FAILED_RETRY');`
   - Chỉ mục tìm chuyến liên tỉnh:
     - `CREATE INDEX idx_scheduled_trips_search ON scheduled_trips (corridor_id, departure_time) WHERE status = 'OPEN_FOR_BOOKING';`

---

# 57. ĐẶC TẢ GIAO DIỆN API VÀ QUY TẮC XỬ LÝ LỖI / ĐỒNG THỜI

```text
# 1. Hành khách — Luồng chung & Đặt xe
POST /api/trip-requests                         → Tạo Trip Intent; trả về mode, allowed_service_codes, rejection_reasons
GET  /api/trip-requests/{id}/recommendations    → Sinh ứng viên, lọc cứng, định giá, xếp hạng Top-K đa phương tiện
POST /api/recommendations/{run_id}/select       → Chọn ứng viên [Yêu cầu Header: Idempotency-Key];
                                                  khởi chạy Per-Offer Seat Hold + Offer Cascade
GET  /api/bookings/{id}                         → Xem trạng thái 3 trục (ride_status, price_status, escrow_status)
GET  /api/bookings/{id}/price-breakdown         → Xem giải thích giá chi tiết (P_i, detour_i, w_i, Floor_i, Cap_i, Quote_i)
POST /api/bookings/{id}/cancel                  → Hủy booking theo chính sách Mục 18.7 [Idempotency-Key]
POST /api/bookings/{id}/sos                     → Kích hoạt cảnh báo an toàn SOS (S9)
POST /api/bookings/{id}/share-link              → Tạo token chia sẻ hành trình trực tiếp cho người thân (S9)

# 2. Hành khách — Mở rộng Nội đô & Liên tỉnh
GET  /api/pickup-points?lat=&lon=&max_walk_m=   → Lấy điểm đón gặp nhau trên đường trục chính (C9)
POST /api/recurring-trips                       → Tạo/cập nhật mẫu chuyến quen hằng ngày (C4)
GET  /api/intercity/pool-trips?corridor=&date=&seats= → Tìm chuyến ghép liên tỉnh đã đăng
POST /api/intercity/pool-trips/{id}/book        → Đặt ghế chuyến ghép liên tỉnh [Idempotency-Key]
POST /api/intercity/topup-offers/{id}/respond   → Trả lời đề nghị góp thêm: ACCEPT | DECLINE (S5) [Idempotency-Key]
POST /api/intercity/waitlist                    → Đăng ký danh sách chờ khi chưa có chuyến (C10)

# 3. Tài xế
PUT  /api/driver/settings                       → Cập nhật accepts_urban, pool_enabled, accepts_intercity,
                                                  max_additional_pickups, giới hạn đi vòng
PUT  /api/driver/location                       → Cập nhật tọa độ GPS hiện hành (và đẩy qua WebSocket)
POST /api/offers/{id}/accept                    → Nhận offer [Idempotency-Key]
POST /api/offers/{id}/reject                    → Từ chối offer [Idempotency-Key]
POST /api/rides/{id}/start                      → Bắt đầu chuyến (Kiểm tra cổng escrow_status == DEPOSITED) [Idempotency-Key]
POST /api/rides/{id}/stops/{stop_id}/complete   → Xác nhận hoàn thành điểm dừng đón/trả; kích hoạt kiểm tra pool_lock_point
POST /api/rides/{id}/complete                   → Hoàn thành chuyến đi; kích hoạt giải ngân [Idempotency-Key]
POST /api/rides/{id}/abort                      → Báo sự cố xe / tài xế hủy chuyến kèm reason_code (Mục 18.7) [Idempotency-Key]
POST /api/rides/{id}/coriders/{booking_id}/decline → Từ chối khách ghép tự động kèm reason_code (Mục 18.6) [Idempotency-Key]
POST /api/driver/pool-trips                     → Đăng lịch chuyến ghép liên tỉnh (kiểm tra T >= now + 72h)
GET  /api/driver/pool-trips                     → Danh sách chuyến ghép liên tỉnh của tài xế
POST /api/driver/pool-trips/{id}/under-min-decision → Quyết định trước T−60h: RUN | CANCEL [Idempotency-Key]
GET  /api/driver/earnings                       → Bảng kê thu nhập (tách cước chuyến, tiền bảo đảm Quỹ, hoa hồng)
GET  /api/driver/demand-heatmap                 → Bản đồ nhiệt dự báo nhu cầu Pool theo vùng (C2)
GET  /api/driver/intercity-demand               → Thống kê danh sách chờ liên tỉnh theo hành lang (C10)

# 4. Quản trị viên (Admin)
GET  /api/admin/fund                            → Số dư Quỹ bảo đảm, lịch sử fund_ledger, p_actual vs p*_booking / p*_ride
GET  /api/admin/metrics                         → Toàn bộ chỉ số vận hành theo dịch vụ (Mục 63)
GET  /api/admin/models                          → Phiên bản model artifacts đang active và bảng chỉ số đánh giá
POST /api/admin/drivers/{id}/kyc-review         → Duyệt trạng thái KYC mock: VERIFIED | REJECTED (S7)
GET  /api/admin/batch-runs                      → Lịch sử các vòng giải ghép theo lô CP-SAT (S4)
GET  /api/admin/pool-trips                      → Giám sát các chuyến ghép liên tỉnh theo trạng thái chốt
POST /api/admin/disputes/{booking_id}/resolve   → Phân xử tranh chấp và gọi resolveDispute on-chain

# 5. Đồng bộ Blockchain
POST /api/escrow/webhook                        → Nhận sự kiện xác nhận giao dịch từ listener/relayer nội bộ (Xác thực HMAC)
```

---

# 58. DANH MỤC SỰ KIỆN HỆ THỐNG (DOMAIN & AUDIT EVENTS)

```text
# Sự kiện Nội đô & Ghép xe
POOL_SHAREABILITY_REJECTED          (Bị loại ở Cổng 1 hoặc Cổng 2 Mục 14)
CORIDER_AUTO_ADDED                  (Tự động chèn khách ghép mới vào kế hoạch đang mở)
DRIVER_DECLINED_COMPATIBLE_CORIDER  (Tài xế từ chối khách ghép không có lý do an toàn → cắt bảo đảm)
POOL_LOCK_POINT_REACHED             (Hành khách chạm điểm khóa giá < 3 km / hết ngân sách đi vòng / kín ghế)
DYNAMIC_REPRICE_APPLIED             (Cập nhật giảm giá cho khách đang trên xe khi chèn thêm người mới)
GUARANTEE_PAID                      (Quỹ bảo đảm chi bù cho tài xế ở chuyến UNMATCHED_LOCKED)
FUND_CONTRIBUTION_RECORDED          (Trích 3% từ booking MATCHED_LOCKED vào Quỹ)
BATCH_MATCH_RUN_COMPLETED           (Hoàn tất chu kỳ giải CP-SAT 30 giây)
MEETING_POINT_ASSIGNED              (Gán điểm đón đi bộ trên đường trục chính — C9)
RECURRING_REQUEST_GENERATED         (Tự sinh yêu cầu từ mẫu chuyến quen lúc T−12h — C4)

# Sự kiện Liên tỉnh
SERVICE_REJECTED_LEAD_TIME          (Từ chối dịch vụ do vi phạm cửa sổ thời gian đặt Mục 2.2)
POOL_TRIP_PUBLISHED                 (Tài xế đăng chuyến ghép liên tỉnh mới)
POOL_TRIP_BOOKING_CLOSED            (Đóng đặt chỗ chuẩn tại T−72h)
POOL_TRIP_MERGE_PROPOSED / MERGED   (Gộp hai chuyến thiếu ngưỡng tại T−72h — S5)
TOPUP_OFFERED / TOPUP_ACCEPTED / TOPUP_DECLINED (Luồng đề nghị góp thêm tự nguyện — S5)
POOL_TRIP_CONFIRMED / CONFIRMED_TOPUP / CONFIRMED_UNDER_MIN / CANCELLED_LOW_DEMAND
PICKUP_ORDER_FIXED                  (Chốt thứ tự đón tối ưu tại T−24h)

# Sự kiện Ký quỹ Blockchain
ESCROW_DEPOSIT_SUBMITTED / ESCROW_DEPOSITED / ESCROW_DEPOSIT_FAILED
ESCROW_PRICE_LOCKED_PARTIAL_REFUND  (Hoàn phần chênh cap - final_price khi khóa giá)
ESCROW_TOPPED_UP                    (Khách nạp thêm tiền khi đồng ý góp thêm liên tỉnh)
ESCROW_RELEASED_THREE_WAY           (Giải ngân đồng thời cho Tài xế, Nền tảng và Quỹ bảo đảm)
ESCROW_REFUNDED                     (Hoàn tiền khi hủy chuyến)
```

---

# 59. KIẾN TRÚC BẢO MẬT, PHÂN QUYỀN VÀ BẢO VỆ DỮ LIỆU CÁ NHÂN (PRIVACY)

1. **Xác thực và Phân quyền chặt chẽ (Authentication & RBAC):**
   - Mật khẩu băm bằng thuật toán `Argon2id`. Sử dụng cặp `Access Token` ngắn hạn (15 phút) và `Refresh Token` có cơ chế thu hồi.
   - Kiểm tra quyền sở hữu tài nguyên ở mức đối tượng (Object-level Authorization): hành khách chỉ xem/hủy được `booking` của chính mình; tài xế chỉ thao tác được trên `ride_plan`, `offer` và `scheduled_trip` được gán cho chính `driver_id` của mình; mọi thông tin của người đi cùng trên xe ghép (`coriders`) chỉ hiển thị tên viết tắt và giới tính (nếu bật cùng giới), tuyệt đối không trả về số điện thoại hay tọa độ điểm đón/trả chính xác của khách A cho khách B qua API.
2. **Bảo vệ quyền riêng tư vị trí và Dữ liệu huấn luyện (Location Privacy & Anonymization):**
   - Không ghi tọa độ GPS chính xác (`lat`, `lon` 6 chữ số thập phân) vào log văn bản của ứng dụng (`application logs`).
   - Khi xuất dữ liệu sang định dạng Parquet để huấn luyện mô hình AI (Mục 66), toàn bộ tọa độ điểm đi/đến được lượng tử hóa thành `zone_id` hoặc mã lưới `Geohash-6 / Geohash-7`, và định danh người dùng được băm một chiều có muối (`salted SHA-256`).
   - Toàn bộ câu trả lời trong Khảo sát S1 (`survey_responses`) được thu thập hoàn toàn ẩn danh, không gắn với họ tên, email hay mã sinh viên.
3. **Bảo vệ giao tiếp Blockchain và Chống lạm dụng API:**
   - Endpoint `/api/escrow/webhook` chỉ chấp nhận yêu cầu từ tiến trình đồng bộ sự kiện nội bộ hoặc phải có chữ ký `HMAC-SHA256` hợp lệ.
   - Áp dụng giới hạn tần suất (`Rate Limiting` qua Redis) cho các API tốn tài nguyên định tuyến OSRM (`/recommendations`) và API tạo chuyến.

---

# 60. CƠ CHẾ AN TOÀN CHO HÀNH KHÁCH VÀ TÀI XẾ KHI ĐI GHÉP (SHOULD S9)

Tâm lý e ngại về an toàn khi ngồi chung xe với người lạ hoặc đi đường dài liên tỉnh là rào cản lớn nhất của dịch vụ ride-sharing. Hệ thống tích hợp 5 lớp bảo vệ an toàn cụ thể:
1. **Điều kiện tiên quyết `KYC = VERIFIED` đối với tài xế (S7 — Mục 81):** Tài xế bắt buộc phải qua bước xác minh hồ sơ (`VERIFIED`) mới được hệ thống mở khóa quyền nhận `CAR_URBAN_POOL`, `CAR_INTERCITY_PRIVATE` và đăng chuyến `CAR_INTERCITY_POOL`.
2. **Tùy chọn ràng buộc ghép cùng giới (`same_gender_coride`):** Hành khách (đặc biệt là hành khách nữ đi buổi tối hoặc đi liên tỉnh) có thể bật cờ `same_gender_coride = true` trong `Trip Intent`; bộ lọc Ràng buộc cứng #11 (Mục 7) đảm bảo chỉ ghép các hành khách có cùng giới tính vào chung kế hoạch.
3. **Chia sẻ hành trình trực tiếp (`Live Trip Sharing Link`):** Hành khách tạo một đường dẫn có mã thông báo chỉ đọc (read-only token hết hạn ngay khi chuyến kết thúc) gửi cho người thân để theo dõi vị trí xe, biển số xe và các điểm dừng theo thời gian thực.
4. **Nút cảnh báo khẩn cấp (`SOS Button`):** Khi hành khách hoặc tài xế bấm nút SOS trên màn hình chuyến đi đang chạy, hệ thống lập tức ghi bản ghi ưu tiên cao vào bảng `safety_incidents` kèm vị trí GPS hiện tại, đóng băng việc thêm khách mới vào xe và phát cảnh báo tức thời lên màn hình Giám sát của Admin.
5. **Danh mục kiểm tra an toàn xe máy:** Giao diện nhắc tài xế chuẩn bị mũ bảo hiểm đạt chuẩn cho khách và cho phép khách đánh giá tiêu chí an toàn sau chuyến đi.

---

# 61. PHÂN TÍCH RỦI RO PHÁP LÝ TẠI VIỆT NAM VÀ GIẢI PHÁP HỢP ĐỒNG ĐIỆN TỬ ĐỒNG THUÊ CHUYẾN

*(Phân tích dưới đây dựa trên các văn bản quy phạm pháp luật hiện hành tại Việt Nam để làm cơ sở bảo vệ học thuật và định hướng nếu chuyển giao thực tế; không thay thế cho tư vấn pháp lý chính thức của cơ quan quản lý nhà nước — `[NEEDS_EXTERNAL_CONFIRMATION]`).*

## 61.1. Khung pháp lý hiện hành liên quan trực tiếp đến 5 dịch vụ của nền tảng

Theo **[Luật Đường bộ năm 2024 (Số 35/2024/QH15)](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Luat-Duong-bo-2024-588811.aspx)** (Điều 56, có hiệu lực từ ngày 01/01/2025) và **[Nghị định số 158/2024/NĐ-CP của Chính phủ quy định về hoạt động vận tải đường bộ](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-158-2024-ND-CP-quy-dinh-hoat-dong-van-tai-duong-bo-636875.aspx)** (có hiệu lực từ ngày 01/01/2025, được hợp nhất tại **[Văn bản hợp nhất số 58/VBHN-BXD năm 2026](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Van-ban-hop-nhat-58-VBHN-BXD-2026-Nghi-dinh-hoat-dong-van-tai-duong-bo-713058.aspx)**), các loại hình vận tải hành khách trong đề tài chịu sự điều chỉnh khác nhau:

1. **Đối với vận tải hành khách bằng xe taxi (`CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`, `CAR_INTERCITY_PRIVATE`):**
   - Theo Điều 6 [Nghị định 158/2024/NĐ-CP](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-158-2024-ND-CP-quy-dinh-hoat-dong-van-tai-duong-bo-636875.aspx), xe ô tô kinh doanh vận tải hành khách bằng taxi (có phù hiệu *"XE TAXI"*) được phép tính tiền thông qua **phần mềm tính tiền** (phần mềm đặt xe, hủy chuyến, tính cước chuyến đi), với điều kiện thông báo phương thức tính tiền tới Sở Giao thông vận tải / Sở Xây dựng và gửi hóa đơn điện tử của chuyến đi cho hành khách sau khi kết thúc hành trình.
   - Pháp luật hiện hành không cấm hai hay nhiều hành khách thỏa thuận đi chung một chuyến xe taxi tính cước qua phần mềm để chia sẻ chi phí, miễn là phương tiện có giấy phép kinh doanh taxi hợp lệ và tổng cước chuyến đi (`PlanFare`) cùng phần thanh toán của từng người được xuất hóa đơn điện tử minh bạch.
2. **Đối với vận tải hành khách bằng xe hợp đồng và rủi ro của mô hình ghép ghế liên tỉnh (`CAR_INTERCITY_POOL`):**
   - Theo khoản 10 Điều 56 [Luật Đường bộ 2024](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Luat-Duong-bo-2024-588811.aspx) và Điều 7 [Nghị định 158/2024/NĐ-CP](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-158-2024-ND-CP-quy-dinh-hoat-dong-van-tai-duong-bo-636875.aspx), đơn vị kinh doanh vận tải hành khách theo hợp đồng (phù hiệu *"XE HỢP ĐỒNG"*) **chỉ được ký hợp đồng vận tải với người thuê vận tải thuê cả chuyến xe (bao gồm cả người lái xe); nghiêm cấm xác nhận đặt chỗ cho từng hành khách đi xe ngoài hợp đồng đã ký kết, không được bán vé hay thu tiền đối với từng hành khách lẻ đi xe** (nhằm ngăn chặn tình trạng "xe dù, bến cóc" đội lốt xe hợp đồng cạnh tranh bất bình đẳng với xe khách tuyến cố định xuất bến).
   - Như vậy, nếu một chiếc xe đăng ký dưới hình thức *"Xe hợp đồng"* nhưng lại bán lẻ từng ghế rời rạc cho từng khách độc lập và đón khách dọc đường mà không có hợp đồng thuê nguyên chuyến trước khi khởi hành, hoạt động đó sẽ vi phạm trực tiếp [Nghị định 158/2024/NĐ-CP](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-158-2024-ND-CP-quy-dinh-hoat-dong-van-tai-duong-bo-636875.aspx).

## 61.2. Định vị phạm vi đồ án và Giải pháp thiết kế tuân thủ khi chuyển giao thực tế

1. **Phạm vi trong khuôn khổ đồ án tốt nghiệp đại học:**
   - Hệ thống được xây dựng dưới dạng **nguyên mẫu nghiên cứu khoa học và công nghệ (Research & Engineering Prototype)** chạy trên môi trường giả lập và mạng thử nghiệm Blockchain Testnet, không thu tiền thật và không vận hành kinh doanh thương mại.
2. **Giải pháp kiến trúc pháp lý nếu triển khai thương mại thực tế tại Việt Nam:**
   - **Phương án 1 (Hợp tác với các hãng Taxi được cấp phép):** Toàn bộ phương tiện `CAR4` tham gia nền tảng là **Xe Taxi chính quy** (có phù hiệu *"XE TAXI"*), sử dụng mô-đun `pricing` của nền tảng làm phần mềm tính tiền theo thỏa thuận đi chung xe của hành khách.
   - **Phương án 2 (Cơ chế Hợp đồng điện tử đồng thuê chuyến — Multi-Party Co-Charter Electronic Contract tại mốc `T−72h` / `T−24h`):** Nhờ thiết kế đặc thù của `CAR_INTERCITY_POOL` trong đề tài là **đóng sổ hoàn toàn trước khi xe lăn bánh từ 24 đến 72 giờ** (tuyệt đối không bắt khách dọc đường), ngay tại mốc chốt danh sách hành khách (`T−24h`), nền tảng đóng vai trò trung gian công nghệ giúp nhóm hành khách trên chuyến cùng đứng tên chung với tư cách là **Nhóm đồng thuê vận tải (Co-Charterers)** trong **một Hợp đồng vận tải điện tử duy nhất thuê nguyên chuyến xe**, có đầy đủ danh sách hành khách và điểm đón/trả cố định gửi về hệ thống quản lý trước khi xe xuất phát theo đúng quy định về hợp đồng điện tử.

---

# 62. THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG (UI SCREENS & UNIFIED DEMO WORKBENCH)

Để vừa đáp ứng đầy đủ nhu cầu trải nghiệm của cả 3 vai trò (Khách hàng, Tài xế, Admin) cho 5 dịch vụ, vừa đảm bảo nhóm sinh viên không bị quá tải bởi việc cắt ghép 19 trang rời rạc, giao diện Web (Next.js) được thiết kế theo mô hình **Bàn làm việc Demo hợp nhất (`Unified Multi-Role Demo Workbench`)** có thanh chuyển đổi nhanh vai trò ở đầu trang, bao gồm các màn hình chức năng sau:

## 62.1. Phân hệ Hành khách (`PASSENGER VIEW`)
- **`K1` — Biểu mẫu tạo Trip Intent & Chatbot (C1):** Chọn điểm đi/đến trên bản đồ, thời gian khởi hành, số lượng khách (`1–4`), tùy chọn loại xe (`Xe máy / Taxi / Bất kỳ`), hình thức (`Bao xe / Đi ghép / Bất kỳ`), cờ hành lý lớn và ngân sách. Hiển thị tức thời nhãn `URBAN` hoặc `INTERCITY` do hệ thống tự suy diễn kèm lý do nếu có dịch vụ bị ẩn.
- **`K2` — Danh sách gợi ý Top-K đa phương tiện:** Hiển thị các thẻ ứng viên kèm huy hiệu giải thích (`Đề xuất AI`, `Rẻ nhất`, `Nhanh nhất`, `Thoải mái nhất`). Với thẻ `CAR_URBAN_POOL`, hiển thị rõ khoảng giá dự kiến, trần giá nếu ghép được (`Quote_i`), trần giá tối đa nếu không ghép được (`Unmatched_i`), giới hạn đi vòng và nhãn khả năng ghép (`Cao / Trung bình / Thấp`).
- **`K3` — Khám phá & Đặt ghế Chuyến ghép liên tỉnh:** Danh sách các chuyến `scheduled_trips` đã đăng theo hành lang và ngày đi, hiển thị số ghế còn trống (`seats_booked / 4`), ngưỡng khởi hành (`3 ghế`), giá ghế, phụ phí đón/trả ngoài vùng (`DoorSurcharge`), nhãn khả năng chuyến chạy (`P(fill)`) và nút chuyển nhanh sang đặt Taxi bao xe liên tỉnh.
- **`K4` — Xác nhận đặt chuyến & Trạng thái Ký quỹ Blockchain:** Hiển thị số tiền ký quỹ mức trần (`quoted_price_cap`), trạng thái giao dịch on-chain và đồng hồ đếm ngược chờ tài xế nhận offer (20s nội đô / 60s liên tỉnh).
- **`K5` — Theo dõi hành trình trực tiếp & An toàn:** Bản đồ lộ trình thời gian thực, danh sách điểm dừng, thông báo khi hệ thống tự động ghép thêm khách mới và giảm giá dự kiến, thông báo khi chạm `pool_lock_point` (khóa `final_price` và hoàn chênh lệch ký quỹ), nút chia sẻ hành trình và nút cảnh báo SOS.
- **`K6 & K7` — Quản lý chuyến đi của tôi, Phản hồi Góp thêm liên tỉnh, Hủy chuyến & Bảng giải thích giá:** Xem trạng thái chốt chuyến tại `T−72h`, bấm `Đồng ý / Từ chối` đề nghị góp thêm (`topUp`), xem bảng phân tách công thức giá chi tiết sau chuyến đi và đánh giá tài xế.
- **`K8` (COULD) — Quản lý Chuyến quen hằng ngày (C4) & Danh sách chờ liên tỉnh (C10).**

## 62.2. Phân hệ Tài xế (`DRIVER VIEW`)
- **`T1` — Bảng điều khiển trạng thái & Cấu hình nhận chuyến:** Bật/tắt trực tuyến; cấu hình nhận chuyến nội đô, bật chế độ Pool (khai báo giới hạn đi vòng và số điểm đón thêm), bật nhận liên tỉnh (hiển thị trạng thái `KYC = VERIFIED`).
- **`T2` — Hộp thoại nhận Offer (`Offer Popup`):** Đếm ngược 20s (nội đô) hoặc 60s (liên tỉnh), hiển thị điểm đón/trả, loại dịch vụ, thu nhập dự kiến của chuyến và thu nhập/giờ ước tính.
- **`T3` — Điều hành chuyến đi đang chạy (`Active Ride Navigation`):** Danh sách chuỗi điểm dừng $S_0 \to \dots \to S_k$, nút xác nhận hoàn thành từng điểm dừng, thông báo khi có khách ghép mới được chèn tự động (`CORIDER_AUTO_ADDED`), và nút từ chối khách ghép / báo sự cố kèm danh mục `reason_code` bắt buộc.
- **`T4` — Quản lý Chuyến ghép liên tỉnh đã đăng:** Biểu mẫu đăng chuyến mới (tự động tính `SeatReference` và khung giá $\pm 10\%$), theo dõi số ghế đã đặt, và nút quyết định `Chạy dưới ngưỡng (RUN)` hoặc `Hủy chuyến (CANCEL)` trước mốc `T−60h` khi thiếu khách.
- **`T5` — Ví thu nhập & Đối soát tài chính:** Bảng kê từng chuyến hoàn thành, tách rõ: Tiền nhận từ khách (`85%` hoặc `80%`), Tiền bù từ Quỹ bảo đảm ghép (`GuaranteePayout`), Hoa hồng nền tảng và trạng thái giải ngân On-chain (`RELEASED`).
- **`T6` (COULD) — Bản đồ nhiệt nhu cầu Pool (C2) & Nhu cầu danh sách chờ liên tỉnh (C10).**

## 62.3. Phân hệ Quản trị viên (`ADMIN VIEW`)
- **`A1` — Tổng quan vận hành 5 dịch vụ:** Thống kê số yêu cầu, tỷ lệ có ứng viên, tỷ lệ nhận offer, tỷ lệ hoàn thành theo từng dịch vụ.
- **`A2` — Bảng điều khiển Quỹ bảo đảm ghép (`Guarantee Fund Ledger`):** Số dư Quỹ hiện tại (đối chiếu Off-chain DB vs On-chain `guaranteeFundBalance`), biểu đồ dòng tiền `CONTRIBUTION` vs `GUARANTEE_PAYOUT`, so sánh trực tiếp tỷ lệ ghép thực tế `p_actual` với ngưỡng hòa vốn `p*_booking` và `p*_ride`.
- **`A3` — Giám sát Chuyến ghép liên tỉnh & Duyệt KYC (S7):** Tỷ lệ chuyến đạt ngưỡng tại `T−72h`, tỷ lệ gộp chuyến, tỷ lệ khách đồng ý góp thêm, tỷ lệ hủy do thiếu khách; danh sách duyệt nhanh KYC cho tài xế.
- **`A4 & A5` — Giám sát Mô hình AI, Ghép theo lô & Simulator:** Phiên bản các model đang active (`LTR`, `P(match)`, `P(fulfill)`), bảng chỉ số đánh giá (`NDCG`, `HR@1`, `Brier`, `ECE`), lịch sử các vòng giải CP-SAT 30 giây và trình điều khiển kịch bản Simulator.

---

# 63. HỆ THỐNG CHỈ SỐ GIÁM SÁT VẬN HÀNH VÀ KỸ THUẬT (OBSERVABILITY METRICS)

```text
# 1. Chỉ số Kỹ thuật & Độ trễ chung
- candidate_generation_latency_ms (p50, p95, p99 theo từng dịch vụ)
- osrm_matrix_calls_count, osrm_cache_hit_rate (theo profile car / motorbike)
- stale_candidate_version_conflict_rate, per_offer_seat_hold_conflict_rate
- offer_accept_rate, offer_cascade_depth_avg (theo dịch vụ)
- no_candidate_rate (tỷ lệ yêu cầu không tìm được ứng viên nào, tách theo dịch vụ × khu vực × khung giờ)
- service_rejected_lead_time_count (số yêu cầu bị lọc do luật thời gian đặt Mục 2.2)
- recommendation_e2e_latency_p95_ms
- service_mix_shown_pct vs service_mix_chosen_pct (cơ cấu dịch vụ hiển thị so với được chọn)

# 2. Chỉ số chuyên biệt cho Taxi ghép nội đô (CAR_URBAN_POOL)
- dynamic_insertion_attempts_count, shareability_gate1_reject_rate, driver_hourly_gate2_reject_rate
- pool_booking_match_rate (p_actual_booking) và pool_ride_match_rate (p_actual_ride)
  (tách theo zone × khung giờ, NOW vs SCHEDULED)
- fund_balance_vnd, fund_contributions_total_vnd, guarantee_payouts_total_vnd, p_actual vs p_star_breakeven
- driver_declined_compatible_corider_rate (tỷ lệ tài xế từ chối khách ghép bị cắt bảo đảm)
- batch_matching_solve_ms, batch_optimal_rate, batch_fallback_greedy_rate, batch_assigned_requests_share (S4)
- meeting_point_assigned_rate, avg_walk_distance_m (C9)

# 3. Chỉ số chuyên biệt cho Liên tỉnh (CAR_INTERCITY_PRIVATE & CAR_INTERCITY_POOL)
- intercity_private_now_pickup_eta_p50_min, intercity_private_now_pickup_eta_p95_min
- intercity_pool_confirmed_at_T72_rate, intercity_pool_merged_rate (S5),
  topup_offer_full_accept_rate (S5), under_min_driver_run_rate, low_demand_cancel_rate
- avg_seats_filled_per_departed_trip, rebook_to_private_after_cancel_rate

# 4. Chỉ số Đồng bộ Ký quỹ Blockchain
- escrow_deposit_pending_count, escrow_deposit_latency_ms, escrow_failure_timeout_rate
- onchain_vs_offchain_ledger_discrepancy_vnd (Bắt buộc luôn == 0)
```

---

# PHẦN VIII — CHIẾN LƯỢC DỮ LIỆU, THIẾT KẾ KHẢO SÁT VÀ QUẢN LÝ TẬP HUẤN LUYỆN

# 64. CHIẾN LƯỢC NGUỒN DỮ LIỆU ĐA TẦNG

| Nguồn dữ liệu | Mục đích sử dụng trong hệ thống & nghiên cứu | Cấp độ |
|---|---|---|
| **1. OpenStreetMap (OSM) Việt Nam + OSRM** | Tính quãng đường, thời gian di chuyển thực tế theo 2 profile (`car` + `motorbike`), tỉ lệ đi vòng và trích xuất mạng lưới đường trục chính cho điểm đón gặp nhau (C9). | **MUST** |
| **2. Simulator 5 dịch vụ đa tác tử (Mục 48)** | Sinh dữ liệu huấn luyện và kiểm thử quy mô lớn có đầy đủ danh sách ứng viên hiển thị (`Top-K`), lựa chọn của hành khách và kết quả vận hành đóng vòng (Closed-loop). | **MUST** |
| **3. Khảo sát lựa chọn rời rạc (Stated Preference Survey — S1, Mục 65)** | Dùng cho 3 mục tiêu khoa học: (1) Ước lượng phân phối tham số tiện ích ẩn $\boldsymbol{\theta}$ nạp vào Simulator; (2) Làm tập kiểm thử hành vi người thật (qua 5-fold GroupKFold CV); (3) Kiểm định cảm nhận công bằng của 3 công thức chia giá (**H4**). | **SHOULD** *(Khuyến nghị mạnh)* |
| **4. Biểu giá công bố của thị trường tại Hà Nội & Liên tỉnh** | Đối chiếu và hiệu chỉnh bộ tham số cước trong Phụ lục B dựa trên giá thực tế của dịch vụ gọi xe máy/taxi công nghệ trên ~20 cặp điểm tại Hà Nội và giá xe ghép/bao xe trên 5–10 tuyến liên tỉnh. | **SHOULD** |
| **5. Thống kê thời tiết lịch sử Hà Nội** | Hiệu chỉnh xác suất chuyển trạng thái mưa theo tháng và khung giờ trong chuỗi Markov của Simulator. | **COULD** |
| **6. Tập dữ liệu mở quốc tế (NYC TLC HVFHV, Chicago TNP, Grab-Posisi)** | Tham khảo phân phối tỷ lệ ghép thành công, độ dài chuyến đi và hồ sơ tốc độ xe máy/ô tô Đông Nam Á (không dùng làm nhãn gợi ý vì thiếu tập ứng viên thay thế). | **COULD** |

---

# 65. THIẾT KẾ KHẢO SÁT LỰA CHỌN RỜI RẠC (STATED PREFERENCE SURVEY — S1) VÀ PHÂN TẦNG MẪU

Để khắc phục rủi ro thiên lệch mẫu sinh viên (Sample Selection Bias) và hiện tượng khoảng tin cậy quá rộng khi cắt nhỏ tập test được chỉ ra trong Báo cáo thẩm định (`P2-05`), thiết kế khảo sát S1 trong Revision 9 được chuẩn hóa như sau (`[ACCEPTED]` — D-30):

## 65.1. Quy mô và Phân tầng đối tượng khảo sát (Quota Sampling)
- **Quy mô mục tiêu:** `N = 100 – 200` người trả lời hợp lệ.
- **Ràng buộc phân tầng mẫu tối thiểu:**
  - **Nhóm 1 (40% – 60% mẫu):** Sinh viên đại học thường xuyên di chuyển nội đô Hà Nội và về quê các tỉnh lân cận (nhạy cảm về giá, tần suất dùng xe máy và xe ghép cao).
  - **Nhóm 2 (40% – 60% mẫu):** Người đã đi làm, nhân viên văn phòng hoặc người dân thường xuyên đi công tác/về quê liên tỉnh (giá trị thời gian cao hơn, sẵn sàng chi trả cho taxi ghép và taxi bao xe khi trời mưa hoặc đi tỉnh).

## 65.2. Cấu trúc bảng hỏi trực quan (Thời gian hoàn thành ~4–5 phút)
1. **Phần 1A — Tình huống lựa chọn Đa phương tiện Nội đô (`6–8 câu/người`):**
   - Mỗi câu đặt người trả lời vào một ngữ cảnh cụ thể: `(Quãng đường: 6 km / 14 km; Thời tiết: Nắng ráo / Mưa rào; Độ gấp: Đi học/làm đúng giờ / Thong thả)` và hiển thị 3 thẻ lựa chọn trực quan (giống hệt màn hình `K2` ở Mục 20.1):
     - Phương án 1: `Xe máy (BIKE_URBAN)` (thay đổi giá, thời gian đi).
     - Phương án 2: `Taxi ghép (CAR_URBAN_POOL)` (thay đổi khoảng giá dự kiến, giá tối đa nếu không ghép được, thời gian đi vòng, nhãn khả năng ghép `Cao/Trung bình/Thấp`, và quãng đi bộ `0m / 200m`).
     - Phương án 3: `Taxi bao xe (CAR_URBAN_PRIVATE)` (giá cố định, đi thẳng).
2. **Phần 1B — Tình huống lựa chọn Liên tỉnh (`2 câu/người`):**
   - Chọn giữa: (a) Đặt trước `Taxi ghép liên tỉnh` từ 3–5 ngày (thay đổi giá ghế `180k–220k` và khả năng đủ khách chạy), (b) Đặt `Taxi bao xe liên tỉnh` (`637k` đi ngay chủ động), hoặc (c) Phương tiện khác / Không đi.
3. **Phần 2 — Đánh giá cảm nhận công bằng của Công thức chia giá ghép (`3 câu/người` — Kiểm định H4):**
   - Trình bày kịch bản thực tế như Mục 16.1 (Khách A đi 14 km phải đi vòng thêm 25% để đón Khách B đi 9 km không phải đi vòng; tổng chi phí chuyến là `248.500 đ`).
   - Cho người trả lời xem **3 bảng chia tiền ẩn danh** (Phương pháp A: Chia tỷ lệ thuần cùng giảm 24,0%; Phương pháp B: Chia đều tiết kiệm Shapley — A giảm 20,2%, B giảm 29,5%; Phương pháp C: Chia theo trọng số bất tiện đề xuất — A giảm 26,1%, B giảm 20,9%).
   - Yêu cầu chấm điểm mức độ hợp lý/công bằng của từng phương pháp trên thang Likert `1–5` và chọn phương pháp họ sẵn sàng sử dụng nhất.
4. **Phần 3 — Thông tin nhân khẩu học tối thiểu (Hoàn toàn ẩn danh):** Nhóm đối tượng (Sinh viên / Đi làm), tần suất đặt xe công nghệ/tuần, cự ly di chuyển phổ biến, tần suất đi liên tỉnh/tháng.

## 65.3. Phương pháp ước lượng tham số và Đánh giá chéo 5-Fold theo người trả lời (`GroupKFold CV`)
- **Hiệu chỉnh Simulator:** Khớp mô hình `Multinomial Logit / Mixed Logit (MNL)` trên dữ liệu Phần 1A & 1B để ước lượng vector trung bình $\boldsymbol{\mu}_\theta$ và ma trận hiệp phương sai $\boldsymbol{\Sigma}_\theta$ của các tham số sở thích, sau đó nạp vào bộ sinh tác tử hành khách của Simulator (Mục 48.1).
- **Đánh giá mô hình trên tập người thật (Khắc phục lỗi mẫu nhỏ khi chỉ cắt 20%):** Thay vì chỉ cắt cố định 20% số người trả lời (chỉ còn ~30 người), khi đánh giá các giả thuyết **H1, H2, H9** trên dữ liệu khảo sát người thật, hệ thống sử dụng thêm phương pháp **5-Fold GroupKFold Cross-Validation phân tách theo `respondent_id`** (mọi câu trả lời của cùng 1 người luôn nằm trong cùng 1 fold), giúp tận dụng toàn bộ 100% số tình huống khảo sát (`~1.200 – 1.800` nhóm lựa chọn) để kiểm định thống kê với khoảng tin cậy hẹp và độ mạnh kiểm định (Statistical Power) cao.
- **Kiểm định H4:** Sử dụng kiểm định phi tham số cặp **Wilcoxon Signed-Rank Test** (kèm kiểm định Friedman cho 3 phương pháp) trên điểm công bằng 1–5 của Phần 2.

---

# 66. CẤU TRÚC BẢN GHI HUẤN LUYỆN (TRAINING INSTANCE SCHEMA)

Mỗi dòng trong bảng dữ liệu huấn luyện Parquet đại diện cho **một ứng viên $i$ trong một lần hiển thị của một yêu cầu `request_id`**:

```text
Định danh & Phân nhóm:
  request_id (Query Group ID), user_id_hash, candidate_id, timestamp_utc, split_set (TRAIN | VAL | TEST)

Đặc trưng Dịch vụ, Ngữ cảnh, Chuyến đi & Ứng viên:
  service_code, vehicle_type, mode, booking_type, candidate_source_type,
  is_raining, has_luggage, hour_of_day, day_of_week, origin_zone_id, dest_zone_id,
  direct_distance_km, direct_duration_min, passenger_count, pickup_window_width_min, budget_min, budget_max,
  private_fare_ref_vnd, effective_private_fare_vnd, pool_quote_price_vnd, pool_unmatched_price_vnd,
  fare_matched_est_vnd, expected_price_vnd, effective_price_vnd, door_surcharge_vnd,
  planned_pickup_eta_min, schedule_deviation_min, in_vehicle_duration_min, detour_ratio, walk_m,
  driver_rating_bayesian, p_match_oof_est, p_fulfill_oof_est, p_fill_oof_est,
  engineered_interactions_json, user_historical_features_json

Thông tin Hiển thị & Thiên lệch vị trí:
  shown_position (1..K), shown_reason (RANKED_BY_SCORE | DIVERSITY_SEED | NEW_DRIVER_EXPLORATION),
  exposure_propensity (0..1)

Nhãn Quan sát (Observed Labels — Chỉ dùng đúng nhãn của từng bài toán, cấm rò rỉ chéo):
  selected (0/1)                     → Nhãn của bài toán LTR (Mục 44)
  driver_accepted (0/1/NULL)         → Nhãn của Cổng 1 p_fulfill (Mục 39.1)
  trip_confirmed_at_T72 (0/1/NULL)   → Nhãn của P(fill) liên tỉnh (Mục 39.2, 52)
  ride_started (0/1/NULL)            → Nhãn của Cổng 2 p_fulfill (Mục 39.1)
  completed (0/1/NULL)               → Nhãn của Cổng 3 p_fulfill (Mục 39.1)
  pool_final_matched (0/1/NULL)      → Nhãn của mô hình P(match) nội đô (Mục 45)
  unmatched_cause, final_price_vnd

Siêu dữ liệu Truy vết (Lineage Metadata):
  dataset_version, pricing_version, model_versions_json
```

---

# 67. QUY TẮC CHIA TẬP DỮ LIỆU THEO THỜI GIAN VÀ CHỐNG RÒ RỈ THÔNG TIN

```text
1. Chia tập theo trục thời gian nghiêm ngặt (Temporal Split):
   - Toàn bộ chuỗi thời gian mô phỏng (ví dụ 28 ngày) được chia theo thứ tự:
     + Tập Train      : Ngày 1  → Ngày 18 (65%) — Dùng để huấn luyện OOF P(match), P(fulfill) và LGBMRanker.
     + Tập Validation : Ngày 19 → Ngày 22 (15%) — Dùng để dừng sớm (Early Stopping), chọn siêu tham số
                                                   và khớp bộ hiệu chỉnh xác suất (Isotonic / Temperature T).
     + Tập Test       : Ngày 23 → Ngày 28 (20%) — Đóng băng hoàn toàn, chỉ chạy 1 lần để báo cáo kết quả cuối.

2. Toàn vẹn nhóm truy vấn (Query Group Integrity):
   - Tất cả các ứng viên thuộc cùng một `request_id` bắt buộc phải nằm trong cùng một tập (Train, Val hoặc Test).

3. Cấm tuyệt đối rò rỉ thông tin từ tương lai (Strict Point-in-Time Feature Computation):
   - Mọi đặc trưng thống kê lịch sử của người dùng (`user_hist_*`), của tài xế (`driver_reliability_*`) và của khu vực
     tại thời điểm tạo yêu cầu t_req chỉ được phép tổng hợp từ các chuyến đi đã kết thúc TRƯỚC t_req.
   - Kết quả hậu nghiệm của chính chuyến đi đó (`final_price_vnd`, `pool_final_matched`, `completed`) tuyệt đối
     không được đưa vào vector đặc trưng đầu vào của mô hình xếp hạng.
```

---

# 68. QUY MÔ DỮ LIỆU THEO TỪNG CẤP ĐỘ KIỂM THỬ

```text
Cấp độ Smoke Test (Kiểm tra đường ống code) :   1.000 yêu cầu (~6.000 – 10.000 dòng ứng viên)
Cấp độ Prototype (Tinh chỉnh nhanh)         :  10.000 yêu cầu (~80.000 – 120.000 dòng ứng viên)
Cấp độ Thực nghiệm chính (Main Benchmark)   :  50.000 yêu cầu (~400.000 – 750.000 dòng ứng viên)
                                               - Tỷ trọng: ~75% Nội đô (3 dịch vụ), ~25% Liên tỉnh (2 dịch vụ)
                                               - Cân bằng kịch bản: Cao điểm / Thấp điểm, Mưa / Không mưa,
                                                 Mật độ nhu cầu Pool LOW / MEDIUM / HIGH
Cấp độ Stress / Sensitivity                 : 100.000+ yêu cầu trên 10–20 hạt giống ngẫu nhiên (seeds) độc lập
Tập dữ liệu Khảo sát người thật (S1)        : ~1.200 – 1.800 tình huống lựa chọn (120–150 người × 10–12 câu)
```

---

# 69. QUẢN LÝ PHIÊN BẢN VÀ TRUY VẾT DỮ LIỆU – MÔ HÌNH (LINEAGE & REPRODUCIBILITY)

Mọi bộ dữ liệu Parquet và mọi báo cáo thực nghiệm được xuất ra đều đi kèm một tệp manifest JSON bất biến để đảm bảo khả năng tái lập khoa học 100%:

```json
{
  "dataset_version": "rec_v9_001",
  "blueprint_revision": "Revision_9",
  "simulator_scenario_version": "sim_v9_multi_service",
  "osrm_routing_version": "osrm_vn_car_motorbike_2026",
  "pricing_version": "price_v9_two_sided_bounded",
  "pool_policy_version": "guarantee_fund_v2_hourly_gate",
  "survey_calibration_version": "sp_survey_v1",
  "candidate_generator_version": "cg_v9_single_matrix",
  "batch_matcher_version": "bm_v2_rtv_cpsat",
  "master_seed_range": [1000, 1019],
  "git_commit_sha": "..."
}
```

---

# PHẦN IX — KẾ HOẠCH KIỂM THỬ, GIẢ THUYẾT NGHIÊN CỨU VÀ DEFINITION OF DONE

# 70. HỆ THỐNG 18 CỔNG ĐÚNG ĐẮN BẮT BUỘC (`= 0` INVARIANT GATES)

Mọi bản dựng của hệ thống trước khi nghiệm thu bắt buộc phải vượt qua **18 cổng đúng đắn với số lần vi phạm bằng `0` tuyệt đối**:

```text
G01. 0 vi phạm 11 ràng buộc cứng (kiểm tra cho MỌI hành khách trong kế hoạch, không chỉ khách mới).
G02. 0 trường hợp đặt vượt sức chứa ghế theo từng đoạn đường (0 segment capacity oversell).
G03. 0 bản ghi booking hoặc giao dịch ký quỹ bị nhân bản khi gọi retry cùng Idempotency-Key.
G04. 0 ứng viên cũ (stale plan_version) được chấp nhận mà không kiểm tra lại khóa phiên bản.
G05. 0 trường hợp giá thu cuối cùng (final_price) vượt quá trần đã báo lúc đặt (quoted_price_cap),
     trừ trường hợp khách chủ động bấm đồng ý góp thêm liên tỉnh (TOPUP_LOCKED).
G06. 0 trường hợp giá phân bổ của khách ghép âm hoặc thấp hơn cận dưới (0 trường hợp Fare_exact < Floor_i).
G07. 0 hành khách taxi ghép nội đô ghép thành công (MATCHED_LOCKED) phải trả > P_i × (1 - d_min).
G08. 0 hành khách đã chạm pool_lock_point (MATCHED_LOCKED) bị thay đổi giá khi xe chèn thêm khách mới,
     và 0 hành khách đang trên xe bị tăng giá dự kiến khi chèn thêm người thứ 3/thứ 4.
G09. 0 kế hoạch ghép hợp lệ làm tốc độ thu nhập theo giờ của tài xế thấp hơn chạy đơn cùng tuyến (Cổng 2 Mục 14.2).
G10. 0 hành khách đặt dịch vụ bao xe (PRIVATE) bị ghép chung với booking khác.
G11. 0 trường hợp quãng đường đi bộ ra điểm đón vượt quá max_walk_m hoặc gợi ý đi bộ ban đêm 22:00–05:00.
G12. 0 đồng chênh lệch giữa số dư sổ cái Quỹ bảo đảm (fund_ledger) và tổng thu/chi thực tế của các chuyến.
G13. 0 ứng viên xe máy (BIKE_URBAN) được sinh cho chuyến liên tỉnh, nhóm > 1 khách hoặc có hành lý lớn.
G14. 0 lượt đặt ghế ghép liên tỉnh thông thường nằm ngoài cửa sổ [T−7 ngày, T−72h], và 0 chuyến nhận thêm
     khách mới sau khi đã chốt thứ tự đón tại T−24h.
G15. 0 trường hợp giá ghế liên tỉnh của khách bị tăng sau khi đặt (ngoại trừ khách chủ động ACCEPT góp thêm).
G16. 0 chuỗi gửi Offer tự động nhảy sang dịch vụ khác với dịch vụ hành khách đã chọn.
G17. 0 chuyến xe chuyển sang trạng thái RIDE_STARTED khi trạng thái ký quỹ chưa đạt DEPOSITED.
G18. 0 đồng chênh lệch giữa tổng tiền giải ngân/hoàn trả trên Smart Contract (đơn vị 1 VND) và final_price_vnd.
```

---

# 71. ĐẶC TẢ KIỂM THỬ ĐỊNH GIÁ VÀ CÁC BẤT BIẾN TOÁN HỌC (PROPERTY-BASED TESTING SPEC)

## 71.1. Các ca kiểm thử hồi quy cố định (Fixed Regression Vectors)
1. **Ca kiểm thử chuẩn 2 khách ghép thành công (Mục 16.1):**
   - Đầu vào: Khách A (`14,0 km, 40 phút`, $s_A = 1$), Khách B (`9,0 km, 28 phút`, $s_B = 1$); kế hoạch chung `17,5 km, 52 phút`, `2` điểm dừng phát sinh; $\text{detour}_A = 0,25$, $\text{detour}_B = 0,00$.
   - Đầu ra bắt buộc: $P_A = 194.000$ đ, $P_B = 133.000$ đ; $\text{PlanFare} = 248.500$ đ; `shareable = true`; $\text{Fare\_exact}(A) = 143.304,26$ đ $\to$ thu **`143.000 đ`**; $\text{Fare\_exact}(B) = 105.195,74$ đ $\to$ thu **`105.000 đ`**; tổng thu `248.000 đ`, lệch làm tròn `500 đ`; tài xế nhận **`210.800 đ`** (`243.231 đ/giờ`), nền tảng giữ ròng **`29.760 đ`**, trích vào Quỹ bảo đảm **`7.440 đ`** (`4.290 đ` từ A + `3.150 đ` từ B).
2. **Ca kiểm thử không ghép được & Chống phá ghép (Mục 18.4, 18.5):**
   - Đầu vào: Khách A ($P_A = 194.000$ đ) không tìm được khách ghép do thị trường (`NO_COMPATIBLE`).
   - Đầu ra bắt buộc: $\text{Quote}_A = 155.000$ đ, $\text{Gap}_A = 39.000$ đ, $\text{Unmatched}_A = \mathbf{174.000\text{ đ}}$; tài xế nhận từ khách `147.900 đ` + Quỹ bảo đảm chi bù **`7.300 đ`** = **`155.200 đ`**; hoa hồng nền tảng `26.100 đ`.
   - Nếu `unmatched_cause == DRIVER_DECLINED`: Khách A chỉ trả **`155.000 đ`**, Quỹ chi **`0 đ`**, tài xế nhận **`131.750 đ`** (lỗ `23.450 đ`).
3. **Ca kiểm thử biên kẹp cận dưới `Floor_i` và Điều kiện khả thi `(F2)` 4 khách (Mục 16.2):**
   - Đầu vào: $P = [45.000, 205.000, 205.000, 205.000]$, $\text{Floor} = [20.000, 82.000, 82.000, 82.000]$ ($\sum \text{Floor}_i = 266.000$ đ), $\text{Cap} = [36.000, 164.000, 164.000, 164.000]$ ($\sum \text{Cap}_i = 528.000$ đ), $\text{detour} = [0.30, 0, 0, 0]$, $\text{walk\_ratio} = [0.20, 0, 0, 0]$.
   - Nhánh 3A (Khả thi với $\text{PlanFare} = 280.000\text{ đ} \in [266.000, 528.000]$): Khách 1 được kẹp ở đúng cận dưới $\text{Floor}_1 = \mathbf{20.000,00\text{ đ}}$ $\to$ thu **`20.000 đ`**; Khách 2, 3, 4 mỗi người `Fare_exact = 86.666,67 đ` ($\in [82.000, 164.000]$) $\to$ thu **`86.000 đ`**.
   - Nhánh 3B (Vô nghiệm cận dưới với $\text{PlanFare} = 220.000\text{ đ} < \sum \text{Floor}_i = 266.000$ đ): Ở cấu hình baseline `on_lower_bound_infeasible = "REJECT"`, trả về `INFEASIBLE_LOWER_BOUND` (`None`); ở cấu hình tùy chọn `"CLAMP_TO_BASE"`, Khách 1 = `20.000 đ`, Khách 2, 3, 4 = `66.666,67 đ` (`thu 66.000 đ`).
   - Nhánh 3C (Booking 2 ghế với $s_A = 2, s_B = 1$ trên lộ trình Mục 16.1, $\gamma_{\text{seat}} = 0.35$): $P_A = 194.000$ đ, $\text{Quote}_A = 155.000$ đ, $\text{Unmatched}_A = 174.000$ đ ($< 194.000$ đ); $\text{Fare\_exact}(A) = 148.895,75$ đ $\to$ thu **`148.000 đ`** ($> 143.000$ đ của 1 ghế nhưng $\le \text{Quote}_A = 155.000$ đ), $\text{Fare\_exact}(B) = 99.604,25$ đ $\to$ thu **`99.000 đ`**.
4. **Ca kiểm thử chèn động khi đã có khách khóa giá (Mục 16.3):**
   - Đầu vào: B đã khóa ở `105.195,74 đ` (`105.000 đ`), A chưa khóa (`143.304,26 đ`), chèn thêm C ($P_C = 64.000$ đ) với $\text{PlanFare\_new} = 288.500$ đ.
   - Đầu ra bắt buộc: Giá của B giữ nguyên `105.000 đ`, giá của A giảm xuống **`135.000 đ`** ($\le 143.000$ đ), giá của C là **`48.000 đ`** ($\le \text{Cap}_C = 51.200$ đ).

## 71.2. Các bất biến kiểm thử tự động trên dữ liệu sinh ngẫu nhiên (Hypothesis Property-Based Invariants)
Trên 10.000 tổ hợp đầu vào sinh ngẫu nhiên (từ 2 đến 4 bookings, quãng đường 2–30 km, $s_i \in \{1, 2\}$, tỉ lệ đi vòng $0..0.30$, đi bộ $0..0.20$):
```text
1. Bảo toàn tổng chính xác  : | Σ_{i ∈ N} Fare_exact(i) - PlanFare | < 1e-6.
2. Nằm trong biên hai đầu   : Floor_i <= Fare_exact(i) <= Cap_i với mọi i ∈ N.
3. Không vượt trần sau làm tròn: 0 < Fare_charged(i) <= Quote_i < Unmatched_i < P_i.
4. Đơn điệu theo bất tiện   : Giữ nguyên PlanFare và P_j, nếu tăng detour_i hoặc walk_ratio_i của khách i
                              thì Fare_exact(i) không bao giờ tăng.
5. Đơn điệu cùng bất tiện   : Nếu detour_i == detour_j và walk_ratio_i == walk_ratio_j và P_i > P_j
                              thì Fare_exact(i) >= Fare_exact(j).
6. Bảo toàn thu nhập tài xế : Với mọi chuyến UNMATCHED (NO_COMPATIBLE):
                              DriverFromPassenger(i) + GuaranteePayout(i) == 0,80 × P_i.
                              Với mọi kế hoạch ghép hợp lệ qua المục 14:
                              DriverPayout(Plan) > max_i (0,80 × P_i) VÀ DriverHourlyRate(Plan) >= max_i Rate_i.
7. Khớp dòng tiền 100%      : driver_base_amount + platform_net_amount + fund_contribution == Fare_charged.
```

---

# 72. ĐẶC TẢ KIỂM THỬ LUẬT DỊCH VỤ, THỜI GIAN ĐẶT VÀ VÒNG ĐỜI LIÊN TỈNH

1. **Kiểm thử hồi quy giá cố định Nội đô & Liên tỉnh:**
   - Xe máy `14,0 km, 35 phút` $\to$ Giá thu **`81.000 đ`**, tài xế nhận **`64.800 đ`**, nền tảng `16.200 đ`.
   - Taxi bao xe liên tỉnh `65,0 km` $\to$ Giá thu **`637.000 đ`**, tài xế nhận **`541.450 đ`**, nền tảng `95.550 đ`.
   - Giá ghế tham chiếu liên tỉnh (`min_seats_ref = 3`) $\to$ **`200.000 đ/ghế`**, biên độ cho phép **`180.000 – 220.000 đ`**.
   - Thu nhập tài xế ghép liên tỉnh ở 3 ghế: **`540.000 đ`** (`99,73%` bao xe); ở 4 ghế: **`720.000 đ`** (`132,98%` bao xe).
   - Góp thêm liên tỉnh (`CONFIRMED_TOPUP` với hoa hồng `15%`): khi có 2 ghế $\to$ **`318.000 đ/ghế`** (góp thêm `+118.000 đ/ghế`), tài xế nhận **`540.600 đ`**; khi có 1 ghế $\to$ **`637.000 đ`**, tài xế nhận **`541.450 đ`**.
2. **Kiểm thử biên phân loại không gian và thời gian đặt:**
   - Chuyến đi 5,0 km từ Phenikaa (Hà Đông) sang La Phù (Hoài Đức — sát ngoài đa giác nội đô): nhờ quy tắc vùng đệm `15 km` ở Mục 2.3, phải được phân loại là **`URBAN`** (không bị ép thành `INTERCITY`).
   - Chuyến đi 3,0 km có cả 2 đầu nằm trong nội thị TP Hưng Yên: bị từ chối với mã `UNSUPPORTED_INTER_PROVINCE_ROUTE`.
   - Đặt `CAR_INTERCITY_POOL` khi còn `71 giờ 59 phút` $\to$ Từ chối dịch vụ ghép, tự động gợi ý `CAR_INTERCITY_PRIVATE`.
   - Đặt `CAR_INTERCITY_POOL` khi còn đúng `72 giờ 00 phút` $\to$ Hợp lệ.
   - Tài xế đăng chuyến ghép liên tỉnh có giờ khởi hành cách hiện tại `< 72 giờ` hoặc đặt `min_seats_to_run = 4` $\to$ Bị từ chối bởi validation.
3. **Kiểm thử vòng đời chốt chuyến `T−72h` và hủy muộn:**
   - Đủ $\ge 3$ ghế tại `T−72h` $\to$ `CONFIRMED`.
   - Thiếu ghế, gộp sang chuyến khác có giá ghế rẻ hơn $\to$ Khách chuyến bị gộp được giảm giá về mức rẻ hơn và hoàn chênh lệch ký quỹ; sau 2 giờ (`T−70h`) nếu khách từ chuyến bị gộp bấm hủy miễn phí làm tổng ghế $< 3$ thì chuyến nhận chuyển sang `TOPUP_OFFERED` (không bị kẹt ở `CONFIRMED` thiếu ghế).
   - Chuyến đã `CONFIRMED` tại `T−72h` (có 3 ghế), đến `T−36h` có 1 khách bấm hủy $\to$ Khách hủy bị phạt `50%` giá ghế (`90%` khoản phạt chuyển cho tài xế), chuyến xe **vẫn giữ trạng thái chạy** cho 2 khách còn lại.

---

# 73. ĐẶC TẢ KIỂM THỬ ĐỒNG THỜI, STATE MACHINE VÀ BẢO MẬT

```text
1. Tranh chấp đặt ghế cuối cùng (Last-Seat Concurrency Race):
   - Giả lập 20 luồng đồng thời cùng bấm chọn 1 ghế trống cuối cùng của một ride_plan hoặc scheduled_trip:
     Đúng 1 luồng thành công, 19 luồng nhận mã lỗi STALE_CANDIDATE hoặc INSUFFICIENT_SEATS (0 oversell).
2. Tranh chấp tại đúng mốc chốt chuyến T−72h:
   - Luồng đặt ghế của khách và luồng worker chạy job chốt T−72h kích hoạt cùng một mili-giây:
     Khóa SELECT ... FOR UPDATE buộc thực thi tuần tự; không sinh ra booking nằm trên chuyến đã CANCELLED.
3. Kiểm thử Per-Offer Seat Hold trong chuỗi Offer Cascade 3 bước:
   - Tài xế #1 timeout ở giây 20, tài xế #2 timeout ở giây 40, tài xế #3 bấm ACCEPT ở giây thứ 19 của offer #3
     (tổng thời gian đã trôi qua = 59s nội đô hoặc 179s liên tỉnh):
     Booking phải thành công 100% vì mỗi bước offer được cấp một seat_hold mới có TTL riêng (35s / 75s).
4. Kiểm thử tính lũy đẳng (Idempotency):
   - Gửi 5 request song song có cùng Idempotency-Key tới API đặt xe / nhận offer / webhook ký quỹ:
     Chỉ tạo đúng 1 bản ghi và thực thi 1 lần duy nhất.
5. Kiểm thử cổng ký quỹ trước khi khởi hành (RIDE_STARTED Escrow Gate):
   - Tài xế gọi POST /api/rides/{id}/start khi escrow_status đang là DEPOSIT_PENDING hoặc ESCROW_FAILED:
     Hệ thống từ chối chuyển sang RIDE_STARTED với mã lỗi ESCROW_NOT_DEPOSITED.
```

---

# 74. HỆ THỐNG GIẢ THUYẾT NGHIÊN CỨU (`H1–H11`) VÀ MA TRẬN ÁNH XẠ ĐÓNG GÓP

Revision 9 đồng bộ hóa hoàn toàn danh sách **11 giả thuyết nghiên cứu (`H1–H11`)** với 5 đóng góp chính ở Mục 0.1 và tiêu chuẩn hoàn thành ở Mục 78 (trong đó nâng **`H9`** lên mức **MUST** để chứng minh trực tiếp giá trị của xếp hạng đa phương tiện — `[ACCEPTED]` P0-08):

| Mã GT | Phát biểu Giả thuyết nghiên cứu | Đóng góp ánh xạ (Mục 0.1) | Phương pháp & Môi trường kiểm định | Chỉ số đo lường chính | Cấp độ |
|---|---|---|---|---|---|
| **H1** | Mô hình học máy `LGBMRanker` (LTR) đạt chất lượng xếp hạng cao hơn có ý nghĩa thống kê so với hàm Baseline trọng số tuyến tính cố định (Mục 40). | Đóng góp #4 (AI LTR) | Offline trên tập Test của Simulator + 5-fold GroupKFold CV trên tập Khảo sát S1. | `NDCG@5`, `HR@1`, `HR@3`, `MRR`, `Expected Utility Regret`. | **MUST** |
| **H2** | Trong ma trận chẩn đoán 2×2 (Mục 44.4), mô hình cây phi tuyến (`LGBMRanker`) vượt trội hơn mô hình tuyến tính (`Conditional Logit`) ngay cả trên cùng tập đặc trưng nhờ học được ngưỡng và tương tác phi tuyến. | Đóng góp #4 (AI LTR) | Offline Ablation 2×2 trên Simulator Test set. | Chênh lệch $\Delta\text{NDCG@5}$ và $\Delta\text{HR@1}$ giữa 4 ô của ma trận 2×2. | **MUST** |
| **H3** | Mô hình dự báo `P(match)` sau hiệu chỉnh đạt độ chính xác xác suất tốt hơn mốc trung bình theo `(zone × giờ)`, và việc đưa `ExpectedPrice` (tính từ `P(match)`) vào xếp hạng làm giảm tỷ lệ khách chọn Pool rồi bị rơi vào `UNMATCHED` đồng thời cải thiện số dư Quỹ bảo đảm. | Đóng góp #2 & #4 (Quỹ & `P(match)`) | Offline (đánh giá xác suất) + Closed-loop Simulator (đánh giá tác động lên tỷ lệ ghép và Quỹ). | `Brier Score`, `Log-Loss`, `ECE`, `Unmatched Selection Rate`, `Fund Balance`. | **MUST** |
| **H4** | Công thức phân bổ giá ghép theo trọng số bất tiện đi vòng/đi bộ (Mục 15.2–15.3) được người dùng thực tế đánh giá là công bằng hơn có ý nghĩa thống kê so với chia theo tỷ lệ giá xe đơn thuần túy và chia đều tiết kiệm (Shapley 2 người). | Đóng góp #1 (Định giá ghép công bằng) | Khảo sát người thật S1 (Phần 2, thang điểm 1–5), kiểm định cặp Wilcoxon Signed-Rank Test. | Điểm trung vị/trung bình cảm nhận công bằng (1–5), tỷ lệ chọn ưu tiên, $p\text{-value}$. | **SHOULD** |
| **H5** | Kết hợp xác suất hoàn thành chuyến đã hiệu chỉnh (`FinalScore = p_hat_select × p_fulfill`, Mục 47) giúp tăng tỷ lệ chuyến đi hoàn thành thực tế so với chỉ xếp hạng theo sở thích của hành khách (`p_hat_select`). | Đóng góp #4 (Mô hình `p_fulfill`) | Closed-loop Simulator (so sánh có và không có thành phần `p_fulfill`). | `Overall Trip Completion Rate`, `Driver/Passenger Cancellation Rate`. | **SHOULD** |
| **H6** | Thuật toán ghép theo lô mỗi $\Delta = 30\text{s}$ dùng CP-SAT trên đồ thị RTV rút gọn (Mục 37) làm tăng tỷ lệ booking ghép thành công (`p_actual`) và giảm khoản chi bù của Quỹ bảo đảm so với thuật toán chèn tham lam tuần tự, với thời gian chờ tăng thêm nằm trong ngưỡng chấp nhận được. | Đóng góp #2 (Tối ưu hóa ghép & Quỹ) | Closed-loop Simulator trên 3 mức mật độ nhu cầu `LOW / MEDIUM / HIGH`. | `p_actual_booking`, `Total Vehicle-Km`, `Guarantee Payout per Booking`, `Wait Time`. | **SHOULD** |
| **H7** | Cơ chế gợi ý Điểm đón gặp nhau trên đường trục chính (Mục 23 — C9) làm giảm tỷ lệ bị loại ở Cổng Shareability & Cổng thu nhập/giờ (Mục 14) và tăng tỷ lệ ghép thành công với quãng đi bộ trung bình $\le 250\text{ m}$. | Mở rộng Đóng góp #1 & #2 | Closed-loop Simulator (bật/tắt C9). | `Shareability Pass Rate`, `Pool Match Rate`, `Average Walk Distance (m)`. | **COULD** |
| **H8** | Cơ chế động cơ kinh tế tự nguyện kết hợp chế tài cắt bảo đảm khi từ chối khách (Mục 18.5, 21) mang lại tỷ lệ hoàn thành chuyến Pool cao hơn và tỷ lệ tài xế hủy/tắt ứng dụng thấp hơn so với chính sách ép buộc hạn ngạch `Quota 4:1` (C6). | Đóng góp #2 (Cơ chế khuyến khích) | Closed-loop Simulator có tác tử tài xế chiến lược (`strategic_driver_share > 0`). | `Effective Pool Completion Rate`, `Driver Rejection / Churn Rate`. | **COULD** |
| **H9** | **Ở phân khúc nội đô 1 hành khách (`Top-K` trộn chung Xe máy, Taxi bao xe và Taxi ghép), mức độ cải thiện ($\Delta\text{HR@1}$, $\Delta\text{NDCG@5}$, giảm `Regret`) của LTR so với Baseline lớn hơn có ý nghĩa thống kê so với các phân khúc đơn phương thức**, do LTR nắm bắt được sự chuyển dịch lựa chọn theo ngữ cảnh mưa và cự ly chuyến đi. | **Đóng góp #4 (Top-K đa phương tiện)** | **Offline Segmented Evaluation trên Simulator Test set + Khảo sát S1 (5-fold CV).** | **$\Delta\text{HR@1}_{\text{multi-modal}}$ vs $\Delta\text{HR@1}_{\text{single-mode}}$, phân tích tách theo `is_raining`.** | **MUST** *(Nâng từ SHOULD)* |
| **H10** | Quy trình kết hợp Gộp chuyến tự động (Mục 30) và Đề nghị góp thêm tự nguyện (Mục 29) tại mốc `T−72h` làm giảm mạnh tỷ lệ chuyến ghép liên tỉnh bị hủy do thiếu khách (`CANCELLED_LOW_DEMAND`) và tăng tổng số hành khách được phục vụ so với chỉ áp dụng ngưỡng cứng. | Đóng góp #3 (Vòng đời ghép liên tỉnh) | Closed-loop Simulator mạng lưới liên tỉnh trên 3 mức nhu cầu `LOW / MEDIUM / HIGH`. | `Low-Demand Cancellation Rate`, `Served Intercity Seat Share`, `Driver Payout`. | **SHOULD** |
| **H11** | Mô hình học máy `P(fill)` (Mục 52 — C10) dự báo xác suất chuyến ghép liên tỉnh đạt ngưỡng tại `T−72h` có `Brier Score` và `ROC-AUC` tốt hơn mốc trung bình lịch sử theo tuyến. | Mở rộng Đóng góp #3 | Offline trên tập lịch sử `scheduled_trips` của Simulator. | `Brier Score`, `ROC-AUC`, `ECE`. | **COULD** |

---

# 75. THIẾT KẾ PHƯƠNG PHÁP ĐÁNH GIÁ THỰC NGHIỆM VÀ KIỂM ĐỊNH THỐNG KÊ

```text
1. Đánh giá Offline (Cho H1, H2, H3, H9, H11):
   - Thực hiện Paired Bootstrap Resampling theo đơn vị `request_id` (1.000 lần lấy mẫu có hoàn lại trên tập Test).
   - Báo cáo giá trị trung bình, độ lệch chuẩn, khoảng tin cậy 95% (95% Confidence Interval) của mức chênh lệch
     (Δ = Metric_Model - Metric_Baseline) và kích thước hiệu ứng (Cohen's d / Relative Lift %).

2. Đánh giá Đóng vòng trên Simulator (Closed-loop Evaluation cho H3, H5, H6, H7, H8, H10):
   - Chạy tối thiểu 10 hạt giống ngẫu nhiên độc lập (khuyến nghị 20 seeds: master_seed ∈ [1000..1019]).
   - Áp dụng kỹ thuật Common Random Numbers (CRN): cùng một seed sẽ sinh ra cùng một luồng yêu cầu hành khách
     và thời tiết ban đầu cho cả chính sách Baseline lẫn chính sách đề xuất để giảm phương sai khi so sánh cặp.

3. Phân tích độ nhạy đa kịch bản (Multi-Scenario Sensitivity Analysis):
   - Bắt buộc chạy và báo cáo kết quả trên ma trận kịch bản:
     + Mật độ nhu cầu Pool nội đô : LOW (p_actual < p*) / MEDIUM (p_actual ≈ p*) / HIGH (p_actual > p*).
     + Mật độ nhu cầu Liên tỉnh   : LOW / MEDIUM / HIGH.
     + Tỷ lệ thời tiết mưa        : 10% vs 30%.
   - Tuyệt đối không rút ra kết luận tổng quát chỉ từ một điểm cấu hình duy nhất.

4. Đánh giá trên dữ liệu Khảo sát người thật (Cho H1, H4, H9):
   - Sử dụng 5-Fold GroupKFold Cross-Validation theo `respondent_id` cho bài toán lựa chọn (H1, H9).
   - Sử dụng kiểm định phi tham số cặp Wilcoxon Signed-Rank Test (mức ý nghĩa α = 0.05, có hiệu chỉnh Bonferroni
     khi so sánh 3 cặp công thức giá) cho bài toán cảm nhận công bằng (H4).
```

---

# 76. HỆ THỐNG CHỈ SỐ ĐÁNH GIÁ TOÀN DIỆN (EVALUATION METRICS)

- **Chỉ số Vận hành & Di chuyển (`Mobility Metrics` — tách theo 5 dịch vụ):** Tỷ lệ yêu cầu tìm được ứng viên hợp lệ (`Coverage Rate`), số lượng ứng viên trung bình mỗi yêu cầu, thời gian chờ xe đón (`Pickup ETA`), tỷ lệ hoàn thành chuyến (`Completion Rate`), và tổng số km xe chạy trên mỗi hành khách được phục vụ (`Vehicle-Km per Passenger`).
- **Chỉ số Ghép xe nội đô (`Urban Pooling Metrics`):** Tỷ lệ booking ghép thành công (`p_actual_booking`), tỷ lệ chuyến xe ghép thành công (`p_actual_ride`), hệ số lấp đầy ghế trung bình (`Average Occupancy`), tỷ lệ đi vòng trung bình (`Average Detour Ratio`), thời gian ngồi trên xe tăng thêm, và quãng đi bộ trung bình (nếu bật C9).
- **Chỉ số Liên tỉnh (`Intercity Metrics`):** Tỷ lệ chuyến đạt ngưỡng tự nhiên tại `T−72h`, tỷ lệ chuyến được cứu nhờ Gộp chuyến (`Merge Salvage Rate`), tỷ lệ chuyến được cứu nhờ Góp thêm (`Top-up Salvage Rate`), tỷ lệ hủy do thiếu khách (`Low-Demand Cancel Rate`), và tỷ lệ khách bị hủy chuyển đổi thành công sang bao xe.
- **Chỉ số Kinh tế & Quỹ bảo đảm (`Economic Metrics`):** Mức tiết kiệm trung bình (`%` và `VND`) của hành khách đi ghép so với đi riêng, thu nhập bình quân mỗi chuyến và mỗi giờ (`VND/giờ`) của tài xế theo từng dịch vụ, số dư ròng của Quỹ bảo đảm (`Fund Net Balance`), khoảng cách `p_actual - p*`, và chi phí bảo đảm trung bình trên mỗi booking Pool.
- **Chỉ số Chất lượng AI (`AI Ranking & Probabilistic Metrics`):** `Hit Rate@1 (HR@1)`, `HR@3`, `Mean Reciprocal Rank (MRR)`, `NDCG@5`, `Expected Utility Regret` (trong Simulator nơi biết hàm tiện ích thật $U^*_{\text{true}}$); `Brier Score`, `Negative Log-Likelihood (NLL)`, `ROC-AUC` và `Expected Calibration Error (ECE)` cho các mô hình xác suất.
- **Chỉ số Công bằng (`Fairness Metrics`):** Điểm cảm nhận công bằng trung bình của hành khách (từ khảo sát S1), hệ số Gini của phân phối thu nhập tài xế, và tỷ lệ hiển thị (`Exposure Share`) dành cho nhóm tài xế mới.

---

# 77. CHỈ TIÊU HIỆU NĂNG HỆ THỐNG (SLA / LATENCY TARGETS)

```text
1. Luồng gợi ý Nội đô (3 dịch vụ đồng thời):
   - Lọc không gian PostGIS + Gọi 1 ma trận OSRM Table : p95 <= 300 ms
   - Suy luận mô hình P(match) + P(fulfill) + LGBMRanker : p95 <= 100 ms
   - Tổng thời gian phản hồi API /recommendations (E2E)  : p95 <= 800 ms

2. Luồng gợi ý Liên tỉnh (2 dịch vụ):
   - Tìm chuyến ghép đã đăng + Tính giá bao xe liên tỉnh : p95 <= 500 ms (tối đa <= 1.000 ms)

3. Tác vụ nền (Background Workers):
   - Một chu kỳ giải Ghép theo lô CP-SAT (với <= 500 yêu cầu chờ) : <= 5,0 giây (giới hạn solver = 3,0 giây)
   - Xử lý chốt chuyến T−72h cho lô 1.000 chuyến liên tỉnh đến hạn : <= 30,0 giây
```

---

# 78. TIÊU CHUẨN HOÀN THÀNH DỰ ÁN (DEFINITION OF DONE — ĐẠT / TỐT / XUẤT SẮC)

## Mức ĐẠT (Hoàn thành 100% phạm vi MUST — Đủ điều kiện bảo vệ vững chắc)
1. Module `Trip Intent` tự động phân loại chính xác `URBAN / INTERCITY` (kể cả vùng đệm 15 km) và kiểm tra đúng luật thời gian đặt cho cả 5 dịch vụ.
2. Hai container OSRM (`car` + `motorbike`) hoạt động ổn định cho khu vực Hà Nội và các tuyến liên tỉnh demo.
3. Toàn bộ **18 cổng đúng đắn `"= 0"` tại Mục 70** đạt tuyệt đối.
4. Toàn bộ các ca kiểm thử hồi quy cố định và kiểm thử bất biến ngẫu nhiên (Hypothesis) tại Mục 71, 72, 73 chạy đạt 100%.
5. Demo trực tiếp end-to-end trên giao diện Web (Unified Demo Workbench) đầy đủ 6 kịch bản cốt lõi:
   - (a) Đặt và hoàn thành một chuyến Xe máy nội đô (`BIKE_URBAN`).
   - (b) Taxi ghép nội đô (`CAR_URBAN_POOL`): Kịch bản ghép thành công 2 khách (Phenikaa → Đống Đa + La Phù → Nguyễn Trãi), kịch bản chèn thêm khách thứ 3 khi xe đang chạy (bảo vệ giá khách đã qua `pool_lock_point`), và kịch bản không tìm được người ghép (Quỹ bảo đảm chi bù `7.300 đ` cho tài xế).
   - (c) Chế tài chống phá ghép: Tài xế từ chối khách ghép tương thích bị cắt khoản bảo đảm, khách chỉ trả `155.000 đ`.
   - (d) Đặt Taxi bao xe liên tỉnh (`CAR_INTERCITY_PRIVATE`) đi ngay trong ngày.
   - (e) Taxi ghép liên tỉnh (`CAR_INTERCITY_POOL`): Một chuyến đạt ngưỡng $\ge 3$ ghế tại `T−72h` (`CONFIRMED`) và chốt thứ tự đón tại `T−24h`; một chuyến thiếu khách bị hủy tại `T−60h` (`CANCELLED_LOW_DEMAND`) hoàn 100% ký quỹ.
   - (f) Hệ thống từ chối yêu cầu đặt ghép liên tỉnh khi còn $< 72$ giờ và gợi ý chuyển sang bao xe liên tỉnh.
6. Sổ cái Quỹ bảo đảm (`fund_ledger`) và bảng `driver_payouts` khớp 100% đến từng đồng với mọi chuyến đi.
7. Hệ thống gợi ý Baseline và mô hình AI (`LGBMRanker` + `P(match)` Out-of-Fold) hoạt động trên `Top-K` đa phương tiện, xuất đầy đủ báo cáo kiểm định thống kê (kèm 95% Bootstrap CI) cho **4 giả thuyết bắt buộc: H1, H2, H3 và H9**.
8. Simulator 5 dịch vụ tái lập được chính xác theo `master_seed`, chứng minh `0` rò rỉ biến ẩn.
9. Hợp đồng thông minh Ký quỹ trên Testnet (đơn vị `1 VND`) thực hiện trọn vẹn: Ký quỹ mức trần $\to$ Hoàn chênh lệch khi khóa giá $\to$ Kiểm tra cổng trước `RIDE_STARTED` $\to$ Giải ngân 3 bên (Tài xế, Nền tảng, Quỹ bảo đảm on-chain) / Hoàn tiền khi hủy khớp 100% với `final_price_vnd`.
10. Báo cáo đầy đủ số liệu benchmark hiệu năng theo Mục 77.

## Mức TỐT (Hoàn thành MUST + SHOULD — Hướng tới điểm Giỏi / Xuất sắc)
- Hoàn thành Khảo sát lựa chọn S1 (`100–200` người có phân tầng mẫu), hiệu chỉnh tham số Simulator từ khảo sát, và báo cáo kết quả kiểm định trên tập người thật (5-fold GroupKFold CV).
- Có đầy đủ kết quả thực nghiệm và kiểm định thống kê cho các giả thuyết **H4, H5, H6 và H10**.
- Thuật toán Ghép theo lô CP-SAT trên đồ thị RTV rút gọn (S4) và quy trình Gộp chuyến + Góp thêm tự nguyện liên tỉnh kèm hàm `topUp` on-chain (S5) chạy hoàn chỉnh.
- Hoàn thiện quy trình duyệt KYC mock (S7), Dashboard Admin chuyên sâu (S8) và các tính năng an toàn cơ bản (S9: chia sẻ hành trình, nút SOS, ghép cùng giới).

## Mức XUẤT SẮC (Hoàn thành thêm các hạng mục COULD)
- Triển khai và đánh giá thêm một hoặc nhiều tính năng nâng cao: Điểm đón gặp nhau trên đường trục chính (**C9 — kiểm định H7**), Thí nghiệm đối chứng chính sách hạn ngạch `Quota 4:1` (**C6 — kiểm định H8**), Mô hình dự báo `P(fill)` và Danh sách chờ liên tỉnh (**C10 — kiểm định H11**), Chatbot LLM trích xuất Trip Intent (**C1**), Dự báo nhu cầu theo vùng (**C2**), Định giá động theo `P(match)` (**C3**), hoặc Chuyến quen lặp lại (**C4**).

---

# PHẦN X — LỘ TRÌNH TRIỂN KHAI, TÍCH HỢP BLOCKCHAIN ESCROW VÀ QUẢN TRỊ RỦI RO

# 79. LỘ TRÌNH 12 PHASE THEO PHỤ THUỘC KỸ THUẬT VÀ THỨ TỰ CẮT GIẢM AN TOÀN

Lộ trình triển khai được thiết kế chặt chẽ theo quan hệ phụ thuộc kỹ thuật (`Core Domain & Pricing → End-to-End Baseline → Simulator & Survey → AI Models → Blockchain Escrow → Advanced Optimization`), đảm bảo dự án luôn có một bản dựng hoàn chỉnh để bảo vệ ở mỗi mốc lớn:

| Phase | Nội dung công việc trọng tâm | Đầu ra & Tiêu chí nghiệm thu mốc |
|---|---|---|
| **P0** | Khởi tạo Repository, Docker Compose, PostgreSQL/PostGIS, Redis, 2 container OSRM (`car` + `motorbike`) với bản đồ OSM miền Bắc Việt Nam. | `docker compose up` chạy thành công; OSRM trả về ma trận khoảng cách/thời gian `< 50 ms`. |
| **P1** | Cài đặt Schema CSDL (với đầy đủ Constraints/Indexes Mục 56.2), Module `identity`, `driver` (KYC mock S7), `trip` (tự động phân loại `URBAN / INTERCITY` có vùng đệm 15 km, luật thời gian đặt). **Đồng thời phát hành Khảo sát lựa chọn S1.** | Phân loại đúng 100% các ca biên không gian/thời gian; link Khảo sát S1 bắt đầu thu thập dữ liệu. |
| **P2** | Cài đặt Module `routing` (1 lệnh OSRM Table duy nhất), `candidate` (11 ràng buộc cứng cho xe máy & bao xe) và `pooling` (Thuật toán chèn điểm động có nhận biết trạng thái xe Mục 36). | Tập ứng viên sinh ra đạt `0` vi phạm ràng buộc cứng; độ trễ sinh ứng viên `< 300 ms`. |
| **P3** | Cài đặt Module `pricing` (5 biểu giá, phân bổ kẹp hai đầu `[Floor_i, Cap_i]`, đóng băng khách đã khóa, Cổng thu nhập/giờ của tài xế, khung phí hủy Mục 18.7) và Module `fund` (`fund_ledger`, `driver_payouts`). | Vượt qua 100% ca kiểm thử hồi quy cố định và 10.000 mẫu kiểm thử ngẫu nhiên Hypothesis (Mục 71–72). |
| **P4** | Cài đặt Module `booking`, `ride`, `jobs` (`SELECT ... FOR UPDATE SKIP LOCKED`), máy trạng thái trực giao (`ride_status`, `price_status`), chuỗi `Offer Cascade` với `Per-Offer Seat Hold`, `Idempotency-Key` và kích hoạt `pool_lock_point`. | Vượt qua toàn bộ bài test đồng thời (Mục 73): `0 oversell`, chuỗi 3 lần offer không rớt ghế. |
| **P5** | Cài đặt Module `intercity`: bao xe liên tỉnh đi ngay/hẹn trước, tài xế đăng chuyến ghép, khách đặt ghế, job chốt chuyến tại `T−72h`, hạn quyết định `T−60h`, tối ưu hoán vị thứ tự đón tại `T−24h` (Mục 31). | Vòng đời liên tỉnh tự động chuyển trạng thái chính xác qua bảng `scheduled_jobs`. |
| **P6** | Cài đặt gợi ý Baseline có giải thích (`Top-K` đa phương tiện bảo toàn đa dạng dịch vụ — Mục 35.5, 40) và Giao diện Web hợp nhất (`Unified Demo Workbench` — Mục 62). | **MỐC NGHIỆM THU 1 (Milestone 1): Demo End-to-End trọn vẹn cả 5 dịch vụ với Baseline Ranking.** |
| **P7** | Xây dựng Simulator 5 dịch vụ tái lập được theo `master_seed` (Mục 48); ước lượng mô hình MNL từ dữ liệu Khảo sát S1 để hiệu chỉnh tham số hành khách ẩn $\boldsymbol{\theta}$; sinh tập dữ liệu chuẩn 50K yêu cầu. | Dataset Parquet xuất ra khớp mã băm `SHA-256` khi chạy lại cùng seed; chứng minh `0` rò rỉ biến ẩn; kiểm định xong **H4**. |
| **P8** | **Trụ cột AI:** Huấn luyện Out-of-Fold `P(match)` (Mục 45), cây sự kiện tuần tự `P(fulfill)` (Mục 46), `LGBMRanker` (Mục 44), hiệu chỉnh xác suất (Mục 47) và thực hiện chẩn đoán 2×2. | **MỐC NGHIỆM THU 2 (Milestone 2): Báo cáo kiểm định thống kê đầy đủ cho H1, H2, H3, H9 (MUST) và H5 (SHOULD).** |
| **P9** | **Trụ cột Blockchain:** Nâng cấp hợp đồng thông minh (đơn vị `1 VND`, hoàn chênh lệch, `topUp`, biến `guaranteeFundBalance`), tích hợp `escrow_adapter` và cổng chặn trước `RIDE_STARTED` (Mục 80). | **MỐC NGHIỆM THU 3 (Milestone 3): Ký quỹ On-chain đồng bộ 100% với vòng đời giá của cả 5 dịch vụ (`0` lệch tiền).** |
| **P10** | Mở rộng thuật toán tối ưu SHOULD: Cài đặt `batch_matcher` dùng CP-SAT trên đồ thị RTV rút gọn (S4 — Mục 37) và quy trình Gộp chuyến + Góp thêm liên tỉnh (S5 — Mục 29, 30). | Hoàn thành kết quả thực nghiệm và kiểm định thống kê cho **H6** và **H10**. |
| **P11** | Chạy phân tích độ nhạy đa kịch bản (`LOW / MEDIUM / HIGH`, 10–20 seeds), kiểm tra lần cuối 18 cổng `"= 0"` (Mục 70), đóng gói báo cáo khoa học và kịch bản bảo vệ. | Quyển báo cáo khóa luận hoàn chỉnh + Bộ model/dataset artifacts + Demo sẵn sàng bảo vệ. |

## Thứ tự cắt giảm an toàn nếu gặp áp lực tiến độ (`Graceful Scope Degradation`)
Nếu quỹ thời gian thực tế bị thu hẹp, nhóm thực hiện chỉ được phép cắt giảm theo đúng thứ tự từ ngoài vào trong dưới đây (tuyệt đối **không được cắt P8 — AI cốt lõi và P9 — Blockchain Escrow**, cũng như **không được cắt H1, H2, H3, H9**):
1. Cắt toàn bộ các hạng mục **COULD (`C1` đến `C11`)**.
2. Tinh giản **S8 (Dashboard Admin nâng cao)** và **S9 (Tính năng an toàn phụ trợ)** về mức hiển thị bảng số liệu cơ bản trên giao diện Unified Workbench.
3. Cắt **S5 / H10 (Gộp chuyến và Góp thêm liên tỉnh)**: Khi đó tại mốc `T−72h`, chuyến ghép liên tỉnh chỉ rẽ nhánh trực tiếp giữa Đủ ngưỡng (`CONFIRMED`) và Thiếu ngưỡng (Tài xế chọn chạy dưới ngưỡng `CONFIRMED_UNDER_MIN` hoặc hủy hoàn tiền 100% `CANCELLED_LOW_DEMAND`).
4. Cắt **S4 / H6 (Ghép theo lô CP-SAT)**: Giữ thuật toán chèn điểm động tham lam trực tuyến (M4 — Mục 36) làm thuật toán ghép duy nhất cho nội đô.
5. Cắt **S2 / S3 / H5 (Mô hình ML cho `p_fulfill` và Temperature Scaling)**: Sử dụng trực tiếp điểm `LGBMRanker` có đầu vào `ExpectedPrice` từ `P(match)` làm điểm xếp hạng cuối.

---

# 80. THIẾT KẾ KIẾN TRÚC KÝ QUỸ BLOCKCHAIN (ESCROW LIFECYCLE, ĐƠN VỊ TIỀN TỆ, QUỸ ON-CHAIN & XỬ LÝ LỖI)

*Lưu ý về giới hạn hiện trạng:* Thiết kế dưới đây đặc tả kiến trúc mục tiêu ở cấp độ giao thức và nghiệp vụ để tích hợp với nền tảng hợp đồng thông minh (Solidity + Hardhat) của dự án. Tài liệu không giả định mã nguồn hợp đồng cũ đã có sẵn các hàm mới; Mục 80.3 liệt kê chính xác các giao diện và bất biến cần bổ sung/kiểm định trên hợp đồng thông minh ở Phase 9.

## 80.1. Bốn nguyên tắc kiến trúc của lớp Ký quỹ Blockchain (`[ACCEPTED]` — D-33, D-34, D-48, D-49)

1. **Tách khỏi đường găng đặt xe nhưng khóa chặt ở cổng khởi hành (`Asynchronous Deposit, Synchronous Start Gate`):**
   - Khi tài xế nhận offer (hoặc khách đặt ghế liên tỉnh), `booking` được xác nhận ngay lập tức trong PostgreSQL (`ride_status = CONFIRMED`, `escrow_status = DEPOSIT_PENDING`) để giao diện phản hồi dưới `200 ms`, không bắt người dùng chờ thời gian tạo block của mạng Blockchain.
   - Tiến trình `escrow_adapter` gửi giao dịch ký quỹ bất đồng bộ lên mạng Testnet.
   - Tuy nhiên, để ngăn chặn rủi ro khách đi xe xong nhưng giao dịch ký quỹ thất bại (không có tiền giải ngân cho tài xế), hệ thống đặt **Cổng kiểm tra bắt buộc tại thời điểm bắt đầu chuyến đi (`RIDE_STARTED` Gate)**: API `POST /api/rides/{id}/start` chỉ cho phép chuyển sang `RIDE_STARTED` khi `escrow_status` đã đạt `DEPOSITED` (hoặc `LOCKED` / `TOPPED_UP`). Nếu sau `120 giây` kể từ lúc `CONFIRMED` mà giao dịch ký quỹ vẫn thất bại sau khi retry, job định thời tự động hủy booking (`CANCELLED_BY_SYSTEM`, lý do `ESCROW_TIMEOUT`).
2. **Quy ước đơn vị tiền tệ nguyên `1 VND` trên hợp đồng thông minh (`1 Base Unit = 1 VND` — `[ACCEPTED]` D-48):**
   - Trong Revision 8, quy ước `1 token = 1.000 đ` gây ra mâu thuẫn số học nghiêm trọng vì các khoản thanh toán sau khi trừ hoa hồng 15%/20% hoặc trích quỹ 3% có phần lẻ hàng trăm và hàng chục đồng (như `64.800 đ`, `155.200 đ`, `147.900 đ`, `7.300 đ`, `541.450 đ`, `3.720 đ`), dẫn tới số thập phân `147,9` hay `541,45` không thể biểu diễn bằng kiểu số nguyên `uint256` trên EVM mà không bị cắt cụt.
   - Trong Revision 9, đơn vị nhỏ nhất truyền vào mọi hàm của hợp đồng thông minh (`uint256 amountVnd`) được quy ước chuẩn là **`1 VND` (một đồng Việt Nam nguyên)** (trên giao diện có thể hiển thị kèm quy đổi `1.000 VND = 1 RIDE token` với `decimals = 3`, nhưng ở tầng dữ liệu hợp đồng và CSDL luôn lưu số nguyên đồng Việt Nam như `174000`, `147900`, `7300`, `541450`).
   - Vì mọi mức giá thu `Fare_charged` đều là bội số nguyên của `1.000 VND`, nên `85%`, `80%`, `15%`, `12%`, `10%`, `3%` của `Fare_charged` **luôn luôn là một số nguyên đồng Việt Nam chính xác tuyệt đối**, đảm bảo `0` sai số làm tròn giữa PostgreSQL và Blockchain!
3. **Quan hệ 1–1 giữa `booking_id` và bản ghi ký quỹ (`Per-Booking Escrow Record` — `[ACCEPTED]` P1-05):**
   - Dù một chuyến xe ghép (`ride_plan` hoặc `scheduled_trip`) phục vụ từ 2 đến 4 hành khách, mỗi hành khách có một mức giá trần khác nhau, thời điểm chốt giá khác nhau và quyền hủy chuyến độc lập. Do đó, khóa chính của bản ghi ký quỹ trên hợp đồng thông minh là **`bytes32 bookingId`** (ánh xạ 1–1 với `bookings.id`), có trường tham chiếu `bytes32 tripOrPlanId` và `address driverAddress`.
4. **Mô hình quản lý ví theo cấp độ triển khai (`Custodial Relayer` ở MUST vs `MetaMask` ở COULD):**
   - Ở phạm vi **MUST (M12)**: Để việc chạy kiểm thử tự động end-to-end và demo 5 dịch vụ diễn ra mượt mà không bị phụ thuộc vào thao tác bấm popup trình duyệt ở mỗi bước, hệ thống cấp cho mỗi tài khoản `Passenger` và `Driver` một địa chỉ ví Testnet dẫn xuất từ cây khóa `HD Wallet` do `escrow_adapter` quản lý và tự động ký giao dịch.
   - Ở phạm vi **COULD (C7)**: Người dùng có thể bấm liên kết ví cá nhân `MetaMask` (`bindWallet`) để tự ký giao dịch `depositEscrow` và `topUpEscrow` trực tiếp từ trình duyệt.

## 80.2. Bảng ánh xạ đầy đủ Vòng đời nghiệp vụ sang Giao dịch Hợp đồng thông minh

| Dịch vụ & Sự kiện nghiệp vụ | Hàm gọi trên Hợp đồng thông minh | Số tiền truyền vào (`uint256` đơn vị `1 VND`) | Chuyển trạng thái `escrow_status` |
|---|---|---|---|
| **1. Dịch vụ giá cố định (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_INTERCITY_PRIVATE`): Khi `CONFIRMED`** | `createAndDepositFixed(bookingId, driverAddr, amountVnd)` | Giá cố định lúc đặt (ví dụ: `81000`, `194000`, hoặc `637000` VND) | `NONE → DEPOSIT_PENDING → DEPOSITED` (và khóa giá luôn `FIXED_LOCKED`). |
| **2. Taxi ghép nội đô (`CAR_URBAN_POOL`): Khi `CONFIRMED`** | `createAndDepositPoolCap(bookingId, driverAddr, capVnd, quoteVnd, targetDriverVnd)` | Ký quỹ theo mức trần tối đa `quoted_price_cap` = `Unmatched_i` (ví dụ: `174000` VND cho khách A) | `NONE → DEPOSIT_PENDING → DEPOSITED(174000)`. |
| **3. Taxi ghép nội đô: Khi chạm `pool_lock_point` và ghép thành công (`MATCHED_LOCKED`)** | `lockFinalPriceAndRefundDiff(bookingId, finalPriceVnd, isMatched=true)` | Khóa `finalPriceVnd = 143000`; hợp đồng tự động hoàn trả ngay phần chênh `174000 - 143000 = 31000` VND về ví khách! | `DEPOSITED(174000) → LOCKED(143000)`. |
| **4. Taxi ghép nội đô: Khi chạm `pool_lock_point` mà không có người ghép (`UNMATCHED_LOCKED` do thị trường)** | `lockFinalPriceAndRefundDiff(bookingId, finalPriceVnd, isMatched=false, driverDeclined=false)` | Khóa `finalPriceVnd = 174000` (hoàn chênh = `0` VND; đánh dấu chuyến được hưởng bù từ Quỹ bảo đảm). | `DEPOSITED(174000) → LOCKED(174000)`. |
| **5. Taxi ghép nội đô: Khi `UNMATCHED_LOCKED` do Tài xế từ chối khách ghép (`DRIVER_DECLINED`)** | `lockFinalPriceAndRefundDiff(bookingId, finalPriceVnd=155000, isMatched=false, driverDeclined=true)` | Khóa `finalPriceVnd = Quote_A = 155000`; hoàn trả ngay `174000 - 155000 = 19000` VND về ví khách; đánh dấu cắt bảo đảm của tài xế! | `DEPOSITED(174000) → LOCKED(155000)`. |
| **6. Taxi ghép liên tỉnh (`CAR_INTERCITY_POOL`): Khi khách đặt ghế (`T−7d → T−72h`)** | `createAndDepositIntercityPool(bookingId, tripId, driverAddr, bookingPriceVnd)` | `SeatPrice × seat_count + DoorSurcharge` (ví dụ: `200000` VND cho 1 ghế chuẩn). | `NONE → DEPOSIT_PENDING → DEPOSITED(200000)`. |
| **7. Taxi ghép liên tỉnh: Khi gộp sang chuyến có giá ghế rẻ hơn tại `T−72h` (`MERGED_REDUCED_LOCKED`)** | `lockFinalPriceAndRefundDiff(bookingId, newBookingPriceVnd, ...)` | Hoàn trả phần chênh `(oldSeatPrice - newSeatPrice) × seat_count` về ví khách; cập nhật `driverAddr` sang tài xế chuyến nhận. | `DEPOSITED → LOCKED(newBookingPriceVnd)`. |
| **8. Taxi ghép liên tỉnh: Khi khách đồng ý Góp thêm tại `T−72h..T−64h` (`TOPUP_LOCKED`)** | `topUpEscrow(bookingId, topupAmountVnd)` | Khách nạp thêm `topup_amount` vào bản ghi ký quỹ đang có (ví dụ: `+118000` VND/ghế để nâng từ `200000` lên `318000` VND). | `DEPOSITED(200000) → TOPPED_UP(318000)`. |
| **9. Mọi dịch vụ: Khi hoàn thành chuyến (`ride_status == COMPLETED`) — Giải ngân tự động** | `releasePayment(bookingId)` (hoặc `autoRelease(bookingId)` sau `X = 24 giờ` nếu khách không bấm xác nhận) | Hợp đồng tự động chia số tiền đang khóa về các địa chỉ nhận và cộng/trừ biến `guaranteeFundBalance` trong **1 giao dịch nguyên tử duy nhất**:<br>- *Ghép nội đô thành công (A: `143000`):* Chuyển Tài xế `121550` (`85%`), Nền tảng `17160` (`12%`), cộng vào `guaranteeFundBalance` `+4290` (`3%`).<br>- *Ghép nội đô không ghép được (`174000`, `NO_COMPATIBLE`):* Chuyển Nền tảng `26100` (`15%`); trích từ `guaranteeFundBalance` `7300` cộng với `147900` của khách để chuyển cho Tài xế đúng `155200` VND!<br>- *Ghép nội đô bị tài xế từ chối khách (`155000`):* Chuyển Tài xế `131750` (`85%`), Nền tảng `23250` (`15%`), Quỹ chi `0`.<br>- *Liên tỉnh góp thêm (`CONFIRMED_TOPUP`, 2 ghế = `636000`):* Áp hoa hồng `15%` → Tài xế `540600`, Nền tảng `95400`. | `LOCKED / TOPPED_UP → RELEASED`. |
| **10. Mọi dịch vụ: Khi hủy chuyến (`CANCELLED_*` / `NO_SHOW`)** | `cancelAndRefund(bookingId, cancelFeeVnd, toFundVnd, toDriverVnd, toPlatformVnd)` | Nếu hủy miễn phí (`cancelFeeVnd = 0`, ví dụ chuyến liên tỉnh `CANCELLED_LOW_DEMAND` ở `T−60h` hoặc hủy trước `T−72h`): hoàn `100%` tiền ký quỹ về ví khách.<br>Nếu có phí phạt hủy (Mục 18.7): khấu trừ `cancelFeeVnd` chia cho Tài xế / Quỹ / Nền tảng, hoàn phần dư về ví khách. | `DEPOSITED / LOCKED → REFUNDED`. |
| **11. Tranh chấp (`DISPUTED`)** | `raiseDispute(bookingId)` $\to$ `resolveDispute(bookingId, passengerRefundVnd, driverPayoutVnd, platformVnd)` (`onlyArbiter`) | Đóng băng giải ngân tự động cho đến khi Admin gọi `resolveDispute` phân xử. | `LOCKED → DISPUTED → RESOLVED`. |

## 80.3. Đặc tả Quỹ bảo đảm nội bộ trên Hợp đồng thông minh (`onChainGuaranteeFundBalance` — `[ACCEPTED]` P1-05)
- Thay vì để Quỹ bảo đảm nằm ở một ví cá nhân bên ngoài (External Owned Account — EOA) khiến mỗi lần chi trả bảo đảm `7.300 đ` phải ký thêm một giao dịch thứ hai và đối mặt với rủi ro mất khóa ví Quỹ, hợp đồng thông minh Ký quỹ quản lý trực tiếp biến trạng thái **`uint256 public guaranteeFundBalance`**:
  1. Khi triển khai hợp đồng lên Testnet ở Phase 9, Admin nạp một khoản vốn mồi ban đầu (`seedFund(uint256 initialSeedVnd)`, ví dụ `5.000.000 VND`) vào `guaranteeFundBalance` để Quỹ không bị thiếu hụt thanh khoản ở những chuyến đầu tiên.
  2. Mỗi khi một booking `CAR_URBAN_POOL` ghép thành công gọi `releasePayment`, hợp đồng tự động giữ lại `3%` (`fund_contribution`) cộng thẳng vào `guaranteeFundBalance` và phát sự kiện `FundContributionRecorded(bookingId, amountVnd, newFundBalance)`.
  3. Mỗi khi một booking `UNMATCHED_LOCKED` (`NO_COMPATIBLE`) gọi `releasePayment`, hợp đồng tự động trích `guaranteeAmountVnd` từ `guaranteeFundBalance` cộng vào khoản thanh toán cho tài xế và phát sự kiện `GuaranteePayoutRecorded(bookingId, driverAddr, guaranteeAmountVnd, newFundBalance)`.
  4. Nhờ cơ chế này, số dư `guaranteeFundBalance` trên chuỗi khối và cột `balance_after_vnd` trong bảng `fund_ledger` của PostgreSQL **luôn đối khớp 1–1 theo từng giao dịch**.

## 80.4. Cơ chế Đợi xác nhận, Thử lại (Retry) và Đối soát bất đồng bộ
- Mọi lệnh gọi từ `escrow_adapter` lên mạng Testnet đều lưu `tx_hash` và tạo một `scheduled_job` kiểm tra biên nhận giao dịch (`tx_receipt`).
- Nếu nút RPC của Testnet bị nghẽn hoặc giao dịch bị rơi khỏi mempool, `escrow_adapter` thực hiện thử lại (retry với cùng `bookingId` lũy đẳng và tăng nhẹ `gasPrice` theo cấp số nhân, tối đa 5 lần).
- Định kỳ mỗi 5 phút, tác vụ đối soát chạy kiểm tra tổng số dư và trạng thái giữa bảng `bookings` / `fund_ledger` với trạng thái trên hợp đồng thông minh để đảm bảo cổng `G18` (`0` lệch tiền) luôn thỏa mãn.

---

# 81. QUY TRÌNH XÁC MINH TÀI XẾ KYC MOCK (SHOULD S7)

```text
Trường trạng thái : driver_profiles.kyc_status ∈ {NONE, PENDING, VERIFIED, REJECTED}
Luồng thực hiện   :
  1. Tài xế đăng ký tài khoản và gửi thông tin giấy phép lái xe / đăng ký xe giả lập → kyc_status = PENDING.
  2. Khi đang ở NONE, PENDING hoặc REJECTED:
     - Tài xế xe máy vẫn có thể chạy BIKE_URBAN trong môi trường thử nghiệm cơ bản (hoặc yêu cầu duyệt tùy cấu hình).
     - Tài xế taxi CHỈ được bật nhận CAR_URBAN_PRIVATE; hệ thống khóa cứng (disable) các công tắc:
       pool_enabled = false, accepts_intercity = false, và chặn API đăng chuyến ghép liên tỉnh (trả lỗi 403 KYC_REQUIRED).
  3. Admin kiểm tra trên màn hình A3 và bấm phê duyệt → kyc_status = VERIFIED:
     - Mở khóa toàn bộ quyền nhận CAR_URBAN_POOL, CAR_INTERCITY_PRIVATE và đăng chuyến CAR_INTERCITY_POOL.
```

---

# 82. BẢNG QUẢN TRỊ RỦI RO KỸ THUẬT, NGHIÊN CỨU VÀ VẬN HÀNH

| Nhóm rủi ro | Mô tả rủi ro cụ thể | Mức độ ảnh hưởng | Giải pháp giảm thiểu đã tích hợp trong Revision 9 |
|---|---|---|---|
| **1. Phạm vi triển khai rộng (5 dịch vụ + AI + Blockchain)** | Không kịp hoàn thành toàn bộ tính năng trước hạn nộp đồ án. | Cao | Tái sử dụng chung bộ máy "xe đơn" cho 3 dịch vụ (`BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_INTERCITY_PRIVATE`); thiết kế giao diện `Unified Demo Workbench` (Mục 62); quy định rõ thứ tự cắt giảm an toàn tại Mục 79. |
| **2. Nghiệm biên bất thường trong công thức giá ghép** | Phát sinh giá âm (`Fare_i < 0`), thay đổi giá đã khóa tại `pool_lock_point`, hoặc làm giảm thu nhập/giờ của tài xế. | Rất cao (Đã xử lý triệt để) | Đã bổ sung cận dưới `Floor_i` (Mục 15.3), quy tắc đóng băng giá đã khóa & không tăng giá khách cũ (Mục 15.5), và Cổng lọc tốc độ thu nhập/giờ của tài xế (Mục 14.2). |
| **3. Khảo sát S1 ít người trả lời hoặc lệch mẫu sinh viên** | Kiểm định H4 yếu, phân phối tham số Simulator thiếu tính đại diện cho nhóm đi làm/liên tỉnh. | Trung bình | Phát hành khảo sát ngay từ Phase 1 (Tuần 2); rút gọn bảng hỏi còn 4–5 phút; áp dụng phân tầng mẫu Quota Sampling (sinh viên + người đi làm) và đánh giá chéo `5-Fold GroupKFold CV` để tận dụng 100% mẫu (Mục 65). |
| **4. Mật độ nhu cầu Pool nội đô thấp làm âm Quỹ bảo đảm** | Tỷ lệ ghép thực tế `p_actual` thấp hơn điểm hòa vốn `p*` (`62,8%` theo booking / `45,8%` theo chuyến). | Trung bình | Cấp vốn mồi ban đầu (`INITIAL_SEED`) cho Quỹ; kết hợp ghép theo lô 30s (S4), chuyến quen (C4) và điểm đón gặp nhau (C9); báo cáo phân tích độ nhạy theo đòn bẩy `d_min` (15%, 10%) và `α` (0,65) tại Mục 19.3. |
| **5. Dịch vụ Xe máy cạnh tranh hút khách của Taxi ghép** | Khi trời đẹp và đi ngắn, khách đi 1 mình chọn hết `BIKE_URBAN`, làm giảm số khách đặt `CAR_URBAN_POOL`. | Thấp (Có giá trị nghiên cứu) | Biến hiện tượng này thành kết quả phân tích khoa học đắt giá của Giả thuyết **H9**: định lượng sự dịch chuyển cơ cấu lựa chọn giữa Xe máy và Taxi ghép khi thời tiết chuyển sang mưa (`is_raining = true`) hoặc cự ly tăng lên $> 12\text{ km}$. |
| **6. Chuyến ghép liên tỉnh vắng khách tại mốc `T−72h`** | Nhiều chuyến không đủ 3 ghế bị hủy gây trải nghiệm kém. | Trung bình | Chuỗi cứu chuyến 3 tầng tại `T−72h` (Gộp chuyến S5 $\to$ Góp thêm tự nguyện S5 $\to$ Tài xế quyết định chạy dưới ngưỡng) và tự động điều hướng khách sang `CAR_INTERCITY_PRIVATE` (khách vẫn còn trọn 3 ngày chuẩn bị). |
| **7. Độ trễ gọi OSRM hoặc Solver CP-SAT chạy chậm** | Vượt ngưỡng SLA `800 ms` của API gợi ý hoặc làm trễ vòng ghép theo lô. | Trung bình | Gom toàn bộ điểm dừng vào **1 lệnh gọi `OSRM Table (matrix)` duy nhất** (Mục 34); xây dựng đồ thị RTV rút gọn (tối đa 2 yêu cầu mới/xe) và đặt `solver_time_limit_s = 3,0s` kèm fallback tham lam cho CP-SAT (Mục 37.2). |
| **8. Nghẽn mạng / Lỗi RPC trên Blockchain Testnet** | Làm treo luồng đặt xe hoặc lệch tiền giữa DB và hợp đồng. | Trung bình | Đưa ký quỹ ra ngoài đường găng lúc `CONFIRMED` nhưng chặn tại cổng `RIDE_STARTED` (Mục 80.1); dùng đơn vị nguyên `1 VND` và quản lý Quỹ ngay trong biến trạng thái của hợp đồng (`guaranteeFundBalance`). |
| **9. Câu hỏi phản biện về tính hợp pháp của xe ghép** | Hội đồng hỏi về quy định cấm xe hợp đồng bán vé lẻ theo [Nghị định 158/2024/NĐ-CP](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-158-2024-ND-CP-quy-dinh-hoat-dong-van-tai-duong-bo-636875.aspx). | Thấp | Đã phân tích rõ tại Mục 61 kèm giải pháp áp dụng loại hình Xe Taxi có phần mềm tính tiền (nội đô) và Hợp đồng điện tử đồng thuê chuyến (Co-Charter Contract) chốt trước 24–72h (liên tỉnh). |

---

# 83. TỔNG KẾT THIẾT KẾ REVISION 9

Bản đặc tả Tiền dự án **Revision 9** đã hoàn thiện một kiến trúc sản phẩm và nghiên cứu khép kín, nhất quán về mặt toán học và khả thi về mặt kỹ thuật cho nền tảng đặt xe thông minh 5 dịch vụ:
1. **Về mặt cơ chế định giá & kinh tế:** Giải quyết trọn vẹn bài toán chia sẻ chi phí và rủi ro cho cả nội đô lẫn liên tỉnh; mọi công thức phân bổ đều đã được chứng minh sự tồn tại nghiệm duy nhất trong miền chặn hai đầu `[Floor_i, Cap_i]`, bảo toàn tổng tiền kế hoạch, bảo vệ giá đã khóa tại `pool_lock_point`, bảo đảm tốc độ thu nhập theo giờ của tài xế và cân bằng dòng tiền đến từng đồng Việt Nam.
2. **Về mặt thuật toán & kỹ thuật hệ thống:** Kiến trúc Modular Monolith kết hợp máy trạng thái trực giao 3 trục (`ride_status`, `price_status`, `escrow_status`), cơ chế giữ ghế theo từng bước offer (`Per-Offer Seat Hold`), kiểm soát phiên bản `plan_version` và đồ thị RTV rút gọn cho CP-SAT giúp hệ thống vận hành chính xác, không xảy ra tranh chấp đồng thời hay sinh kế hoạch lỗi.
3. **Về mặt nghiên cứu AI & Blockchain:** Thiết lập quy trình huấn luyện Out-of-Fold không rò rỉ dữ liệu cho `P(match)` và cây sự kiện tuần tự cho `p_fulfill`, nối kết chặt chẽ 5 đóng góp chính với 11 giả thuyết nghiên cứu (`H1–H11`, trong đó `H1, H2, H3, H9` thuộc MUST) và đồng bộ hoàn toàn với hợp đồng thông minh Ký quỹ theo đơn vị nguyên `1 VND`.

---

# 84. HƯỚNG PHÁT TRIỂN SAU ĐỒ ÁN

- Mở rộng đội xe lên phân khúc xe 7 chỗ (`CAR7`) và xe điện cho dịch vụ ghép liên tỉnh, nâng ngưỡng tối ưu từ 3/4 ghế lên 5/7 ghế.
- Nghiên cứu thuật toán Học tăng cường đa tác tử (Multi-Agent Reinforcement Learning — MARL) để điều phối xe rỗng đón đầu nhu cầu dự báo (C2) và tối ưu hóa động ngưỡng `d_min`, `α` theo thời gian thực (C3).
- Tích hợp cổng thanh toán ngân hàng/ví điện tử thật song song với lớp đối soát Blockchain Layer-2 phí thấp, kết hợp định danh điện tử eKYC chính thức.
- Triển khai thử nghiệm thực địa (Field Pilot) quy mô nhỏ cho sinh viên và giảng viên trên hành lang Đại học Phenikaa (Hà Đông) $\leftrightarrow$ Trung tâm Hà Nội.

---

# PHỤ LỤC A — DECISION REGISTER CẬP NHẬT (`D-01` ĐẾN `D-52`)

Bảng đăng ký quyết định kiến trúc và nghiệp vụ dưới đây tổng hợp toàn bộ các quyết định từ các phiên bản trước (`D-01` đến `D-42`) và **10 quyết định bổ sung mới của Revision 9 (`D-43` đến `D-52`)**, đi kèm nhãn trạng thái chuẩn hóa (`ACCEPTED`, `PROPOSED`, `NEEDS_VALIDATION`, `NEEDS_EXTERNAL_CONFIRMATION`):

| ID | Nội dung Quyết định thiết kế | Phiên bản | Trạng thái | Mục tham chiếu |
|---|---|---|---|---|
| **D-01** | Khung thời gian đặt xe dùng `T_preferred` kết hợp cửa sổ `[T_earliest, T_latest]`. | Giữ (Rev5) | `ACCEPTED` | Mục 6, 7 |
| **D-02** | Lọc ràng buộc cứng và Matching luôn thực hiện trước bước xếp hạng AI Recommendation. | Giữ (Rev5) | `ACCEPTED` | Mục 7, 43 |
| **D-03** | Mỗi ứng viên (`ride_candidate`) là một bản chụp bất biến gắn với `source_plan_version`. | Giữ (Rev5) | `ACCEPTED` | Mục 42, 56 |
| **D-04** | Sức chứa phương tiện được kiểm tra theo từng đoạn hành trình giữa 2 điểm dừng liên tiếp. | Giữ (Rev5) | `ACCEPTED` | Mục 7, 36 |
| **D-05** | Giới hạn đi vòng của hành khách và giới hạn đi vòng của tài xế được tách riêng và kiểm tra độc lập. | Giữ (Rev5) | `ACCEPTED` | Mục 7, 36 |
| **D-06** | Chèn điểm đón/trả động dùng duyệt có giới hạn ($k_{\max}=8$), kiểm tra lại ràng buộc cho mọi khách đang trên xe. | Sửa (Rev9) | `ACCEPTED` | Mục 7, 36 |
| **D-07** | Năm dịch vụ trên một lõi chung: `BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`, `CAR_INTERCITY_PRIVATE`, `CAR_INTERCITY_POOL`. | Giữ (Rev8) | `ACCEPTED` | Mục 2.1 |
| **D-08** | Taxi ghép nội đô nhận khách cả khi đang chạy; chốt trạng thái `MATCHED_LOCKED` / `UNMATCHED_LOCKED` tại `pool_lock_point`. | Giữ (Rev7) | `ACCEPTED` | Mục 11, 22 |
| **D-09** | Khi không ghép được do thị trường: chia khoảng chênh `Gap_i` ba bên với hệ số khách chịu $\alpha = 0,50$. | Giữ (Rev7) | `ACCEPTED` | Mục 18.3 |
| **D-10** | Mức giá tối đa khi không ghép được (`Unmatched_i`) luôn nhỏ hơn giá bao xe đơn ($P_i$). | Giữ (Rev7) | `ACCEPTED` | Mục 18.3, 71 |
| **D-11** | Ứng viên `CAR_URBAN_POOL` phải thỏa mãn trần ngân sách cứng với mức giá tối đa: `Unmatched_i <= B_max`. | Giữ (Rev7) | `ACCEPTED` | Mục 7, 20 |
| **D-12** | Tài xế `CAR_URBAN_POOL` được Quỹ bảo đảm bù để nhận đúng bằng thu nhập chạy xe đơn khi không có khách ghép tương thích. | Giữ (Rev7) | `ACCEPTED` | Mục 18.3, 18.4 |
| **D-13** | Động cơ kinh tế tự nguyện thay cho hạn ngạch cứng `Quota 4:1`; `Quota 4:1` chỉ dùng làm kịch bản thí nghiệm đối chứng (C6/H8). | Giữ (Rev7) | `ACCEPTED` | Mục 21, 74 |
| **D-14** | Tài xế bật và nhận chuyến Pool đồng nghĩa với việc đồng ý để hệ thống tự động chèn thêm khách ghép nằm trong ngưỡng đã khai. | Giữ (Rev7) | `ACCEPTED` | Mục 18.6 |
| **D-15** | Tài xế từ chối khách ghép tương thích không vì lý do an toàn/sự cố bị cắt 100% bảo đảm, khách đang trên xe chỉ trả tối đa `Quote_i`. | Giữ (Rev7) | `ACCEPTED` | Mục 18.5, 18.6 |
| **D-16** | Cổng kiểm tra khả năng chia sẻ (Shareability Gate 1): `PlanFare <= (1 - d_min) × Σ P_i` (với `d_min = 0,20`). | Giữ (Rev7) | `ACCEPTED` | Mục 14.1 |
| **D-17** | Chia phần tiết kiệm $S$ theo trọng số bất tiện: $w_i = P_i \times (1 + \lambda \cdot \text{detour}_i + \mu \cdot \text{walk\_ratio}_i)$ ($\lambda=1, \mu=2$). | Giữ (Rev7) | `ACCEPTED` | Mục 15.2, 23.3 |
| **D-18** | Tiền thu của mỗi khách (`Fare_charged`) làm tròn xuống đến bội số `1.000 đ`. | Giữ (Rev7) | `ACCEPTED` | Mục 15.4 |
| **D-19** | Quỹ bảo đảm ghép trích `3%` từ `Fare_charged` của mỗi booking ghép thành công (lấy từ `15%` tổng hoa hồng ghép); sổ cái `fund_ledger` là MUST. | Giữ (Rev7) | `ACCEPTED` | Mục 17, 19 |
| **D-20** | Phân loại `URBAN` / `INTERCITY` do hệ thống tự động suy diễn từ đa giác PostGIS kết hợp vùng đệm khoảng cách `15 km`. | Sửa (Rev9) | `ACCEPTED` | Mục 2.3 |
| **D-21** | Ghép theo lô cho taxi ghép nội đô mỗi $\Delta = 30\text{s}$ dùng OR-Tools CP-SAT trên đồ thị RTV rút gọn (tối đa 2 yêu cầu mới/xe) kèm dự phòng tham lam. | Sửa (Rev9) | `ACCEPTED` | Mục 37.2 |
| **D-22** | Điểm đón gặp nhau trên đường trục chính (`Meeting Points` — C9) xếp ở mức COULD, tắt vào ban đêm `22:00–05:00` và khi trời mưa. | Giữ (Rev8) | `ACCEPTED` | Mục 23 |
| **D-23** | Mẫu chuyến quen lặp lại hằng ngày (`Recurring Trips` — C4) tự sinh yêu cầu `SCHEDULED` ở mốc `T−12h`. | Giữ (Rev7) | `ACCEPTED` | Mục 24 |
| **D-24** | Thời gian ngồi trên xe tối đa (`max_in_vehicle_time`, mặc định `1,5 × T_direct + 10 phút`) là ràng buộc cứng. | Giữ (Rev7) | `ACCEPTED` | Mục 7 |
| **D-25** | Kiểm soát đồng thời kết hợp khóa dòng `SELECT ... FOR UPDATE`, `plan_version` và header `Idempotency-Key`. | Giữ (Rev7) | `ACCEPTED` | Mục 42 |
| **D-26** | Tách biệt mô hình sở thích của hành khách (`LTR`) và mô hình xác suất hoàn thành chuyến (`p_fulfill`). | Giữ (Rev5) | `ACCEPTED` | Mục 39, 43, 47 |
| **D-27** | Điểm đầu ra thô của LTR không mặc định là xác suất; chỉ nhân với `p_fulfill` sau khi qua bước hiệu chỉnh Temperature Scaling (S3). | Giữ (Rev5) | `ACCEPTED` | Mục 47 |
| **D-28** | Cấm tuyệt đối việc đưa biến ẩn (`theta`, `gamma`, xác suất thật) của Simulator vào tập đặc trưng huấn luyện. | Giữ (Rev5) | `ACCEPTED` | Mục 43, 48.4, 67 |
| **D-29** | Mô hình `P(match)` được huấn luyện theo quy trình Out-of-Fold (OOF) để tính `ExpectedPrice` đưa vào xếp hạng mà không gây rò rỉ nhãn. | Sửa (Rev9) | `ACCEPTED` | Mục 40, 45.3 |
| **D-30** | Khảo sát lựa chọn rời rạc (S1: 100–200 người, phân tầng sinh viên & người đi làm) dùng để hiệu chỉnh Simulator, đánh giá 5-fold GroupKFold CV và kiểm định H4. | Sửa (Rev9) | `NEEDS_VALIDATION` | Mục 65, 75 |
| **D-31** | Kiến trúc Modular Monolith trên FastAPI + bảng tác vụ định thời `scheduled_jobs` trong PostgreSQL (`FOR UPDATE SKIP LOCKED`). | Giữ (Rev7) | `ACCEPTED` | Mục 5, 54, 55 |
| **D-32** | Thứ tự ưu tiên triển khai: Core $\to$ AI $\to$ Blockchain $\to$ Mở rộng thuật toán ghép; KYC thực hiện dạng mock (S7). | Giữ (Rev7) | `ACCEPTED` | Mục 79, 81 |
| **D-33** | Số tiền ký quỹ ban đầu luôn bằng mức trần nghĩa vụ tài chính tối đa (`quoted_price_cap`); chỉ hoàn bớt tại `PRICE_LOCKED` hoặc nạp thêm khi khách đồng ý `topUp`. | Giữ (Rev8) | `ACCEPTED` | Mục 80.1, 80.2 |
| **D-34** | Giao dịch ký quỹ thực hiện bất đồng bộ lúc `CONFIRMED` để không chặn luồng đặt xe, nhưng có cổng kiểm tra đồng bộ trước khi `RIDE_STARTED`. | Sửa (Rev9) | `ACCEPTED` | Mục 9.3, 80.1 |
| **D-35** | Xe máy (`BIKE_URBAN`) chỉ chạy 1:1 trong nội đô, đúng 1 khách, không mang hành lý lớn. | Giữ (Rev8) | `ACCEPTED` | Mục 2.1, 10.1 |
| **D-36** | Taxi bao xe liên tỉnh (`CAR_INTERCITY_PRIVATE`) cho phép cả đặt đi ngay trong ngày (đón `15–45 phút`) và hẹn trước tối đa `7 ngày` (để đón khách từ chuyến ghép bị hủy ở `T−72h`). | Chốt (Rev9) | `ACCEPTED` | Mục 2.2, 25.1 |
| **D-37** | Taxi ghép liên tỉnh (`CAR_INTERCITY_POOL`) mở đặt chỗ trong cửa sổ `[T−7 ngày, T−72h]`, đóng đặt chỗ chuẩn và kích hoạt chốt chuyến tại `T−72h`. | Giữ (Rev8) | `ACCEPTED` | Mục 2.2, 27, 29 |
| **D-38** | Giá ghế tham chiếu liên tỉnh `SeatReference = floor(IntercityPrivateFare × (1 - c_private) / (min_seats_ref × (1 - c_seat)))` với `min_seats_ref = 3` khóa cố định, biên độ đặt giá $\pm 10\%$. | Sửa (Rev9) | `ACCEPTED` | Mục 26, 28.1 |
| **D-39** | Chuyến ghép liên tỉnh thiếu ngưỡng tại `T−72h` xử lý theo chuỗi 3 bước: Gộp chuyến (`T−72h..T−70h`) $\to$ Góp thêm tự nguyện (6 giờ) $\to$ Tài xế quyết định chạy/hủy trước `T−60h`. | Sửa (Rev9) | `ACCEPTED` | Mục 29, 30 |
| **D-40** | Danh sách gợi ý `Top-K` đa phương tiện luôn giữ ít nhất 1 ứng viên đại diện cho mỗi dịch vụ hợp lệ có xe; nâng giả thuyết **`H9`** lên mức **MUST**. | Sửa (Rev9) | `ACCEPTED` | Mục 10.5, 35.5, 74 |
| **D-41** | Chuỗi gửi Offer (`Offer Cascade`) chỉ chuyển tiếp giữa các ứng viên thuộc cùng dịch vụ mà hành khách đã chọn. | Giữ (Rev8) | `ACCEPTED` | Mục 41 |
| **D-42** | Taxi ghép liên tỉnh không có bước gửi Offer cho từng khách (tài xế đăng chuyến là đã cam kết nhận khách hợp lệ). | Giữ (Rev6) | `ACCEPTED` | Mục 2.4, 26 |
| **D-43** | **Bổ sung cận dưới `Floor_i = min(EffectiveCap_i, max(BASE, P_i(1 - d_max)(1 + γ_seat(s_i - 1))))`, điều kiện khả thi `Σ Floor_i <= TargetFare_U <= Σ EffectiveCap_i`, thuật toán điểm gãy hai cận và quy tắc xử lý vô nghiệm (`on_lower_bound_infeasible = "REJECT"`).** | **Mới (Rev9)** | `ACCEPTED` | Mục 15.3, Phụ lục E (O-01) |
| **D-44** | **Hệ 6 điều kiện đầy đủ (`D1–D6`) khi chèn khách động: đóng băng nhóm đã khóa giá ($L$), kiểm tra đồng thời cả cận trên ($\Delta\text{PlanFare} \le \text{Cap}_{c_{\text{new}}}$) lẫn cận dưới ($\text{TargetFare}_U \ge \sum_{m \in U} \text{Floor}_m$) trên tập chưa khóa $U$, và kiểm tra Cổng 2 sau làm tròn.** | **Mới (Rev9)** | `ACCEPTED` | Mục 15.5, 36, Phụ lục E (O-02) |
| **D-45a**| **Bổ sung Cổng 2A & 2B kiểm tra tốc độ thu nhập theo giờ của tài xế tính trực tiếp trên khoản Payout thực tế sau làm tròn (`0,85 × Σ Fare_charged(i) / (T_plan/60) >= (1 - ε_hourly) × max_i Rate_Private(i)`).** | **Mới (Rev9)** | `ACCEPTED` | Mục 14.2, 17, Phụ lục E (O-03) |
| **D-45b**| **Giữ nguyên `P_i = PrivateFare(i)` cho `Cap_i, Quote_i, Gap_i, Unmatched_i` (đảm bảo `Fare_charged <= Quote_i < Unmatched_i < PrivateFare(i)` cho cả booking 2 ghế) và áp dụng hệ số ghế thứ hai $\gamma_{\text{seat}} = 0,35$ vào trọng số chia tiết kiệm $w_i$ và cận dưới `Floor_i`.** | **Mới (Rev9)** | `ACCEPTED` | Mục 12.2, 15.2, Phụ lục E (O-04) |
| **D-46** | **Tách máy trạng thái của `Booking` thành 3 trục trực giao: `ride_status`, `price_status` và `escrow_status`.** | **Mới (Rev9)** | `ACCEPTED` | Mục 9, 22, 56 |
| **D-47** | **Cấp phát `seat_hold` riêng theo từng bước của chuỗi Offer (`Per-Offer Seat Hold`, TTL = `35s` nội đô / `75s` liên tỉnh) trên đúng `ride_plan` của ứng viên đó.** | **Mới (Rev9)** | `ACCEPTED` | Mục 41 |
| **D-48** | **Chuẩn hóa đơn vị tiền tệ trên Smart Contract là `1 VND` (`uint256` nguyên) và quản lý số dư Quỹ bảo đảm ngay trong biến trạng thái hợp đồng (`guaranteeFundBalance`).** | **Mới (Rev9)** | `ACCEPTED` | Mục 80.1, 80.3, Phụ lục E (O-05) |
| **D-49** | **Đặt cổng kiểm tra bắt buộc `escrow_status == DEPOSITED` trước khi cho phép chuyển chuyến đi sang `RIDE_STARTED` (timeout hủy tự động sau `120s`).** | **Mới (Rev9)** | `ACCEPTED` | Mục 9.3, 80.1, Phụ lục E (O-06) |
| **D-50** | **Định nghĩa công thức tất định cho phụ phí ngoài vùng `DoorSurcharge` (theo khoảng cách OSRM tới biên `pickup_zone_ids`/`dropoff_zone_ids`) và công thức `Fare_matched_est` khi xe chưa có khách thứ 2.** | **Mới (Rev9)** | `ACCEPTED` | Mục 20.2, 28.3 |
| **D-51** | **Thống nhất tính hoa hồng `15%` (`12%` nền tảng + `3%` Quỹ) và phần tài xế nhận `85%` trực tiếp trên số tiền thực thu đã làm tròn `Fare_charged(i)`; áp dụng hoa hồng `15%` (`c_private`) cho chuyến liên tỉnh `CONFIRMED_TOPUP`.** | **Mới (Rev9)** | `ACCEPTED` | Mục 17.2, 29 |
| **D-52** | **Đưa khung tham số Chính sách phí hủy cơ bản (`Cancellation & No-Show Policy`) vào Phụ lục B ngay trong phạm vi MUST để phục vụ đối soát và Smart Contract.** | **Mới (Rev9)** | `ACCEPTED` | Mục 18.7, Phụ lục B |

---

# PHỤ LỤC B — BẢNG THAM SỐ CẤU HÌNH CHUẨN (YAML SPECIFICATION)

Toàn bộ các con số dưới đây được nạp từ tệp cấu hình (và lưu theo phiên bản trong bảng `pricing_configs`), tuyệt đối không gán cứng (hardcode) trong mã nguồn:

```yaml
pricing_version: price_v9_two_sided_bounded

spatial_and_service_areas:
  max_total_service_radius_km: 150.0
  urban_boundary_buffer_km: 15.0        # Chuyến <= 15 km có 1 đầu trong nội đô được tính là URBAN (D-20)

bike_urban:
  base_vnd: 10000
  per_km_vnd: 4500
  per_min_vnd: 250
  commission_rate: 0.20
  rounding_step_vnd: 1000               # Làm tròn xuống (floor)
  capacity: 1
  now_pickup_window_min: [3, 15]
  max_ahead_hours: 12

car_urban:                              # Dùng chung cho CAR_URBAN_PRIVATE và CAR_URBAN_POOL
  base_vnd: 20000
  per_km_vnd: 11000
  per_min_vnd: 500
  extra_stop_fee_vnd: 5000
  stop_dwell_time_s: 60
  commission_private: 0.20
  commission_pool_total: 0.15           # Tài xế nhận 85% của Fare_charged
  platform_net_pool_rate: 0.12          # Nền tảng giữ ròng 12%
  fund_contribution_rate: 0.03          # Trích vào Quỹ bảo đảm 3%
  d_min: 0.20                           # Cam kết giảm tối thiểu 20% khi ghép thành công (Cap_i = 0.80 * PrivateFare_i)
  d_max: 0.60                           # Giảm tối đa 60% trước khi chạm sàn (Floor_i = min(EffectiveCap_i, max(BASE, 0.40*PrivateFare_i*(1+gamma*(s_i-1))))) (D-43)
  on_lower_bound_infeasible: "REJECT"   # Xử lý khi TargetFare_U < Σ Floor_i: "REJECT" (mặc định Gate G06) | "CLAMP_TO_BASE" (PROPOSED)
  allow_dynamic_insertion_after_partial_lock: true # Cho phép chèn khách mới khi có khách đã khóa nhưng U_old != ∅ (D-44 PROPOSED)
  d_matched_typical: 0.25               # Tỷ lệ giảm kỳ vọng điển hình khi xe chưa có khách thứ 2 (D-50)
  party_seat_surcharge_gamma: 0.35      # Hệ số ghế thứ 2 trong Pool: giảm trọng số tiết kiệm w_i / (1 + 0.35*(s_i-1)) & nâng Floor_i (D-45b PROPOSED)
  detour_weight_lambda: 1.0
  walk_weight_mu: 2.0
  unmatched_passenger_share_alpha: 0.50
  enforce_driver_hourly_rate_gate: true # Bật Cổng 2 bảo toàn thu nhập/giờ của tài xế tính trên 0.85 * Σ Fare_charged(i) (D-45a PROPOSED)
  driver_hourly_rate_tolerance_eps: 0.00
  rounding_step_vnd: 1000
  capacity: 4
  max_party_seats_pool: 2
  pool_lock_remaining_km: 3.0
  k_max_stops: 8
  n_pool_max_candidates: 20
  now_pickup_window_min: [5, 20]
  max_ahead_hours: 12

car_intercity_private:
  base_vnd: 150000
  per_km_vnd: 7500                      # Đã tính chi phí rủi ro chạy rỗng chiều về
  commission_rate: 0.15
  rounding_step_vnd: 1000
  now_pickup_window_min: [15, 45]
  now_search_radius_km: 5.0
  max_ahead_days: 7                     # Chốt = 7 ngày để đón khách chuyển sang từ chuyến ghép hủy ở T-72h (D-36)

car_intercity_pool:
  commission_seat: 0.10                 # Hoa hồng khi chạy ghép ghế thông thường (tài xế nhận 90%)
  commission_topup: 0.15                # Hoa hồng khi chạy CONFIRMED_TOPUP như bao xe chia tiền (tài xế nhận 85%) (D-51)
  min_seats_ref: 3                      # Khóa cứng ở mức nền tảng để tính SeatReference (P2-01)
  allowed_driver_min_seats: [2, 3]
  default_min_seats_to_run: 3
  seat_price_band: [0.90, 1.10]
  door_surcharge_per_km_vnd: 4000
  max_corridor_deviation_km: 10.0
  rounding_step_vnd: 1000
  booking_open_days: 7
  booking_close_hours: 72               # T-72h: Đóng đặt chỗ chuẩn và kiểm tra ngưỡng
  allow_post_confirm_late_booking: false # Tùy chọn O-08: đặt true nếu cho đặt ghế vét từ T-72h đến T-24h trên chuyến đã CONFIRMED
  merge_confirmation_window_hours: 2    # T-72h đến T-70h: Cửa sổ khách chuyến bị gộp xác nhận/hủy miễn phí
  topup_response_window_hours: 6        # Thời gian khách trả lời đề nghị góp thêm
  driver_decision_deadline_hours: 60    # T-60h: Hạn cuối tài xế quyết định RUN hoặc CANCEL
  pickup_order_fix_hours: 24            # T-24h: Chốt thứ tự đón bằng duyệt hoán vị 4!
  merge_max_departure_gap_min: 60

booking_and_concurrency:
  offer_timeout_s_urban: 20
  offer_timeout_s_intercity: 60
  per_offer_hold_buffer_s: 15           # TTL của Per-Offer Seat Hold = offer_timeout_s + 15s (35s nội đô / 75s liên tỉnh) (D-47)
  offer_cascade_max_attempts: 3
  idempotency_key_ttl_hours: 24
  escrow_deposit_timeout_s: 120         # Quá 120s từ lúc CONFIRMED chưa DEPOSITED thì hủy tự động (D-49)
  escrow_auto_release_after_hours: 24
  escrow_base_unit: "VND"               # 1 đơn vị nguyên trên Smart Contract = 1 VND (D-48)
  initial_guarantee_fund_seed_vnd: 5000000

cancellation_policy:                    # Khung tham số phí hủy chuẩn (Mục 18.7, D-52)
  urban_free_cancel_grace_s: 120
  urban_no_show_wait_min: 5
  urban_single_cancel_fee_rate: 0.20
  urban_single_cancel_fee_cap_vnd: 20000
  urban_pool_cancel_fee_rate_on_quote: 0.20
  intercity_private_free_cancel_lead_h: 2.0
  intercity_private_late_cancel_fee_rate: 0.20
  intercity_pool_free_cancel_before_h: 72
  intercity_pool_cancel_fee_rate_72h_to_24h: 0.50
  intercity_pool_cancel_fee_rate_after_24h: 1.00

batch_matching:                         # Hạng mục SHOULD S4
  interval_s: 30
  max_new_requests_per_plan: 2
  solver: "ORTOOLS_CP_SAT_RTV"
  solver_time_limit_s: 3.0
  unassigned_penalty_vnd: 50000

meeting_points:                         # Hạng mục COULD C9
  max_walk_m_range: [100, 400]
  max_candidates_per_rider: 3
  allowed_osm_highway_classes: ["primary", "secondary", "tertiary"]
  disabled_night_hours: ["22:00", "05:00"]
  disable_when_raining: true

in_vehicle_time_default:
  direct_duration_multiplier: 1.5
  additive_buffer_min: 10

simulator_and_evaluation:
  scenario_version: "sim_v9_multi_service"
  urban_pool_density_levels: ["LOW", "MEDIUM", "HIGH"]
  intercity_pool_demand_levels: ["LOW", "MEDIUM", "HIGH"]
  rain_share_levels: [0.10, 0.30]
  now_booking_share_levels: [0.50, 0.70, 0.90]
  recurring_user_share_levels: [0.00, 0.20, 0.40]
  strategic_driver_share_levels: [0.00, 0.10, 0.30]
  closed_loop_seeds_count: 20
  oof_cross_fitting_folds: 5
  survey_group_kfold_splits: 5
```

---

# PHỤ LỤC C — TỪ ĐIỂN THUẬT NGỮ VÀ KÝ HIỆU TOÁN HỌC

| Thuật ngữ / Ký hiệu | Định nghĩa chuẩn trong Revision 9 |
|---|---|
| `service_code` | Mã định danh một trong 5 dịch vụ: `BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`, `CAR_INTERCITY_PRIVATE`, `CAR_INTERCITY_POOL`. |
| `mode` (`URBAN` / `INTERCITY`) | Phạm vi không gian của chuyến đi, do hệ thống tự động suy diễn từ đa giác `urban_service_area` kết hợp vùng đệm `15 km` (Mục 2.3). |
| `PrivateFare(i)` | Giá cước đi thẳng của chuyến taxi bao xe nội đô (`CAR_URBAN_PRIVATE`) trên lộ trình của booking $i$. |
| `P_i` (`PrivateFare(i)`) & `seat_factor(i)` | Trong `CAR_URBAN_POOL`, giá tham chiếu độc lập của booking $i$ giữ nguyên $P_i = \text{PrivateFare}(i)$ cho cả $s_i \in \{1, 2\}$ để tính `Cap_i, Quote_i, Gap_i, Unmatched_i`; hệ số chiếm ghế $\text{seat\_factor}(i) = 1 + \gamma_{\text{seat}}(s_i - 1)$ dùng để chia trọng số tiết kiệm $w_i$ và nhân vào `Floor_i`. |
| `PlanFare` | Tổng chi phí của cả kế hoạch ghép nội đô tính trên quãng đường thực $D_{\text{plan}}$, thời gian thực $T_{\text{plan}}$ của xe và phụ phí điểm dừng phát sinh `STOP_FEE`. |
| $S$ (`Total Savings`) | Tổng phần tiết kiệm của kế hoạch ghép so với tổng giá tham chiếu đi riêng: $S = \sum_{i \in N} P_i - \text{PlanFare}$. |
| $d_{\min}, d_{\max}$ | Tỷ lệ giảm giá cam kết tối thiểu (`20%`) và tỷ lệ giảm giá tối đa trước khi chạm sàn (`60%`) khi ghép thành công. |
| `Cap_i`, `EffectiveCap_i`, `Floor_i` | Cận trên chuẩn ($\text{Cap}_i = (1 - d_{\min}) P_i$), cận trên hiệu dụng khi chèn động ($\text{EffectiveCap}_i = \min(\text{Cap}_i, \text{Fare\_exact}_{\text{old}}(i))$) và cận dưới ($\text{Floor}_i = \min(\text{EffectiveCap}_i, \max(\text{BASE}, (1 - d_{\max}) P_i (1 + \gamma_{\text{seat}}(s_i - 1))))$) của `Fare_exact(i)`. |
| `Quote_i` | Trần giá tối đa hiển thị cho khách nếu ghép thành công: $\text{Quote}_i = \lfloor P_i (1 - d_{\min}) / 1000 \rfloor \times 1000$. |
| `Unmatched_i` (`quoted_price_cap`) | Mức giá thu nếu kết thúc ở `UNMATCHED_LOCKED` (do thị trường): $\text{Unmatched}_i = \lfloor (\text{Quote}_i + \alpha (P_i - \text{Quote}_i)) / 1000 \rfloor \times 1000$; đồng thời là số tiền khóa ký quỹ ban đầu. |
| `pool_lock_point` | Thời điểm khóa giá cá nhân của booking $i$ trong `CAR_URBAN_POOL` (khi còn cách điểm trả $< 3\text{ km}$, hết ngân sách đi vòng, hoặc xe kín ghế mọi đoạn còn lại). |
| `p*_booking`, `p*_ride` | Điểm hòa vốn của Quỹ bảo đảm ghép tính theo tỷ lệ booking ghép thành công (`~62,8%`) và tính theo tỷ lệ chuyến xe ghép thành công (`~45,8%`). |
| `SeatReference` | Giá ghế tham chiếu của chuyến ghép liên tỉnh sao cho tại ngưỡng `min_seats_ref = 3` ghế, tài xế nhận xấp xỉ `100%` thu nhập chạy bao xe liên tỉnh. |
| `DoorSurcharge` | Phụ phí đón/trả ngoài vùng miễn phí của chuyến ghép liên tỉnh, tính tất định theo khoảng cách OSRM từ điểm đón/trả tới đường biên vùng miễn phí. |
| `Per-Offer Seat Hold` | Cơ chế cấp phát khóa giữ ghế riêng cho từng bước trong chuỗi `Offer Cascade` với `TTL = offer_timeout_s + 15s`. |
| `RTV-Graph` | Đồ thị 3 tầng (Request – Trip – Vehicle) trong đó mỗi nút Trip là một tập con 1 hoặc 2 yêu cầu đã được kiểm tra chèn đồng thời trước khi đưa vào CP-SAT. |
| `ride_status`, `price_status`, `escrow_status` | Ba trục máy trạng thái trực giao của một `Booking` (Mục 9). |

---

# PHỤ LỤC D — TÀI LIỆU THAM KHẢO HỌC THUẬT VÀ PHÁP LÝ

## A. Tài liệu học thuật quốc tế (Optimization, Game Theory & Machine Learning)
1. Cordeau, J.-F., & Laporte, G. (2007). *The Dial-a-Ride Problem: Models and Algorithms*. Annals of Operations Research, 153(1), 29–46.
2. Alonso-Mora, J., Samaranayake, S., Wallar, A., Frazzoli, E., & Rus, D. (2017). *On-demand high-capacity ride-sharing via dynamic trip-vehicle assignment*. Proceedings of the National Academy of Sciences (PNAS), 114(3), 462–467. (Cơ sở mô hình hóa đồ thị RTV rút gọn tại Mục 37.2).
3. Santi, P., Resta, G., Szell, M., Sobolevsky, S., Strogatz, S. H., & Ratti, C. (2014). *Quantifying the benefits of vehicle pooling with shareability networks*. Proceedings of the National Academy of Sciences (PNAS), 111(37), 13290–13294.
4. Shapley, L. S. (1953). *A Value for n-Person Games*. In Contributions to the Theory of Games (Vol. 2, pp. 307–317). Princeton University Press. (Cơ sở đối chứng phân chia tiết kiệm tại Mục 16.1 & Giả thuyết H4).
5. Luxen, D., & Vetter, C. (2011). *Real-time routing with OpenStreetMap data*. In Proceedings of the 19th ACM SIGSPATIAL International Conference on Advances in Geographic Information Systems (pp. 513–516).
6. Burges, C. J. (2010). *From RankNet to LambdaRank to LambdaMART: An Overview*. Microsoft Research Technical Report MSR-TR-2010-82.
7. Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. Advances in Neural Information Processing Systems (NeurIPS), 30.
8. Joachims, T., Swaminathan, A., & Schnabel, T. (2017). *Unbiased Learning-to-Rank with Biased Feedback*. In Proceedings of the Tenth ACM International Conference on Web Search and Data Mining (WSDM) (pp. 781–789).
9. McFadden, D. (1974). *Conditional Logit Analysis of Qualitative Choice Behavior*. In P. Zarembka (Ed.), Frontiers in Econometrics (pp. 105–142). Academic Press.
10. Train, K. E. (2009). *Discrete Choice Methods with Simulation* (2nd ed.). Cambridge University Press. (Cơ sở thiết kế Khảo sát lựa chọn rời rạc S1 và Simulator tại Mục 48, 65).
11. Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). *On Calibration of Modern Neural Networks*. In Proceedings of the 34th International Conference on Machine Learning (ICML) (pp. 1321–1330).
12. Gelman, A., Carlin, J. B., Stern, H. S., Dunson, D. B., Vehtari, A., & Rubin, D. B. (2013). *Bayesian Data Analysis* (3rd ed.). CRC Press.
13. Nguồn dữ liệu mở tham chiếu: OpenStreetMap (Geofabrik Vietnam Extract); NYC Taxi & Limousine Commission (TLC) High-Volume For-Hire Vehicle Trip Records; Chicago Transportation Network Providers (TNP) Dataset; Grab-Posisi SEA Trajectory Dataset.

## B. Văn bản quy phạm pháp luật Việt Nam (Tham chiếu tại Mục 61)
14. Quốc hội nước CHXHCN Việt Nam (2024). *[Luật Đường bộ số 35/2024/QH15](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Luat-Duong-bo-2024-588811.aspx)*, ban hành ngày 27/06/2024, có hiệu lực từ ngày 01/01/2025 (Điều 56 quy định về các loại hình kinh doanh vận tải bằng xe ô tô).
15. Quốc hội nước CHXHCN Việt Nam (2024). *[Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15](https://luatvietnam.vn/an-ninh-trat-tu/luat-trat-tu-an-toan-giao-thong-duong-bo-2024-so-36-2024-qh15-360844-d1.html)*, ban hành ngày 27/06/2024, có hiệu lực từ ngày 01/01/2025.
16. Chính phủ nước CHXHCN Việt Nam (2024). *[Nghị định số 158/2024/NĐ-CP quy định về hoạt động vận tải đường bộ](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-158-2024-ND-CP-quy-dinh-hoat-dong-van-tai-duong-bo-636875.aspx)*, ban hành ngày 18/12/2024, có hiệu lực từ ngày 01/01/2025 (Điều 6 về kinh doanh vận tải hành khách bằng xe taxi sử dụng phần mềm tính tiền; Điều 7 về kinh doanh vận tải hành khách theo hợp đồng).
17. Bộ Xây dựng / Bộ Giao thông vận tải (2026). *[Văn bản hợp nhất số 58/VBHN-BXD năm 2026 hợp nhất Nghị định quy định về hoạt động vận tải đường bộ](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Van-ban-hop-nhat-58-VBHN-BXD-2026-Nghi-dinh-hoat-dong-van-tai-duong-bo-713058.aspx)*, ban hành ngày 02/07/2026.

---

# PHỤ LỤC E — HỒ SƠ PHÂN TÍCH CÁC QUYẾT ĐỊNH MỞ VÀ ĐÁNH ĐỔI THIẾT KẾ (`O-01` ĐẾN `O-08`)

Tuân thủ nguyên tắc minh bạch thiết kế (không tự coi một phương án đề xuất là quyết định đã được phê duyệt tuyệt đối nếu còn sự đánh đổi giữa các mục tiêu), phụ lục này trình bày chi tiết **8 hồ sơ quyết định mở (`O-01` đến `O-08`)** theo cấu trúc 6 phần: *(1) Vấn đề cần giải quyết, (2) Các phương án khả thi, (3) Ưu/nhược điểm và tác động, (4) Phương án khuyến nghị trong Revision 9, (5) Căn cứ lựa chọn, và (6) Trạng thái quyết định*.

---

## O-01: Chọn ngưỡng cận dưới (`Floor_i`) và hàm trọng số trong phân bổ giá ghép nội đô (Mục 15.3 — `D-43`)
1. **Vấn đề phải giải quyết:** Công thức tuyến tính $w_i = P_i(1 + \lambda d_i + \mu \omega_i)$ khi ghép 3–4 khách có độ dài chuyến rất chênh lệch có thể phân bổ phần giảm giá vượt quá $P_i$ của khách đi ngắn, gây ra giá âm (`Fare_i < 0`).
2. **Các phương án khả thi:**
   - *Phương án A (Linear Weight + Two-sided Clamp):* Giữ nguyên công thức trọng số tuyến tính và bổ sung cận dưới $\text{Floor}_i = \max(\text{BASE}, (1 - d_{\max}) P_i)$ với $d_{\max} = 0,60$ vào vòng lặp kẹp biên.
   - *Phương án B (Saturating Sub-linear Weight):* Thay hàm tuyến tính bằng hàm bão hòa lõm $w_i = P_i (1 + \tanh(\lambda d_i + \mu \omega_i))$ kết hợp sàn $\text{Floor}_i = \text{BASE}$.
   - *Phương án C (Strict Proportional Savings Cap):* Giới hạn hệ số nhân bất tiện tối đa $\lambda d_i + \mu \omega_i \le 0,35$.
3. **Ưu/nhược điểm & Tác động:**
   - Phương án A giữ nguyên 100% tính dễ hiểu của công thức tuyến tính ở Mục 15.2, không làm thay đổi bất kỳ con số nào của các chuyến 2 khách thông thường, đồng thời đối xứng toán học với $\text{Cap}_i = (1 - d_{\min}) P_i$. Nhược điểm duy nhất là cần chọn hằng số $d_{\max}$ (ví dụ $0,50$ hay $0,60$).
   - Phương án B làm thay đổi toàn bộ các con số trong ví dụ chuẩn Mục 16.1 và khó giải thích cho hành khách phổ thông vì sao có hàm $\tanh(\cdot)$.
4. **Phương án khuyến nghị:** **Phương án A** với $d_{\max} = 0,60$ và sàn tuyệt đối `BASE = 20.000 đ`.
5. **Căn cứ lựa chọn:** Vừa bảo toàn toàn bộ kết quả kiểm thử hồi quy 2 khách của Revision 8, vừa đảm bảo tồn tại nghiệm dương duy nhất cho mọi tổ hợp 3–4 khách.
6. **Trạng thái quyết định:** **`[ACCEPTED]`** (Đã phê duyệt chốt `d_max = 0.60` và `on_lower_bound_infeasible = "REJECT"` trong `MVP_CONFIG_BASELINE_V1.md`).

---

## O-02: Xử lý xung đột giữa Chèn khách động khi xe đang chạy và Giá của hành khách đã qua `pool_lock_point` (Mục 15.5 — `D-44`)
1. **Vấn đề phải giải quyết:** Khi hành khách B trên xe đã chạm `pool_lock_point` (khóa `final_price`), trong khi hành khách A vẫn còn $> 3\text{ km}$ và xe nhận thêm khách C, hoặc khi việc chèn C làm dịch chuyển tỷ trọng đi vòng khiến giá của B tăng lên.
2. **Các phương án khả thi:**
   - *Phương án A (Frozen Locked Fare + Pareto Non-Increasing Reprice):* Cho phép chèn C với điều kiện đóng băng giá của các khách đã khóa ($L$), và chỉ chấp nhận phương án chèn nếu $\Delta\text{PlanFare} \le \text{Cap}_C$ sao cho giá của các khách đang trên xe ($U_{\text{old}}$) không tăng ($\text{Fare}^{\text{new}}_i \le \text{Fare}^{\text{old}}_i$).
   - *Phương án B (Plan-level Lock Point):* Đóng băng toàn bộ kế hoạch `ride_plan` (không nhận thêm khách mới C) ngay khi có **bất kỳ một hành khách nào** trên xe chạm `pool_lock_point`.
3. **Ưu/nhược điểm & Tác động:**
   - Phương án A cho phép chiếc xe ghép liên tục dạng chuỗi gối đầu (A đi với B, B sắp xuống thì đón thêm C đi tiếp với A), tối đa hóa hiệu suất lấp đầy ghế và doanh thu tài xế.
   - Phương án B đơn giản hơn khi cài đặt nhưng làm giảm khoảng 15–25% cơ hội ghép nối tiếp trên các hành lang dài.
4. **Phương án khuyến nghị:** **Phương án A** (đã đặc tả đầy đủ tại Mục 15.5 và Mục 36).
5. **Căn cứ lựa chọn:** Giải quyết triệt để mâu thuẫn toán học mà không làm giảm tỷ lệ ghép của hệ thống.
6. **Trạng thái quyết định:** **`[ACCEPTED]`** (Đã phê duyệt chốt Phương án A — `allow_dynamic_insertion_after_partial_lock = true` trong `MVP_CONFIG_BASELINE_V1.md`).

---

## O-03: Xử lý Bất biến tốc độ thu nhập theo giờ của tài xế khi ghép (`DriverHourlyRate` — Mục 14.2 & 17 — `D-45a`)
1. **Vấn đề phải giải quyết:** Cổng Shareability `PlanFare <= 0,80 × Σ P_i` không ngăn được trường hợp ghép thêm khách chặng ngắn làm tăng thời gian dừng/chờ nhiều hơn quãng đường, dẫn tới thu nhập/giờ của tài xế khi ghép thấp hơn chạy đơn (`223.125 đ/giờ < 232.800 đ/giờ`). Đồng thời, cơ sở tính thu nhập/giờ ở Cổng 2 phải khớp tuyệt đối với khoản Payout thực tế sau làm tròn (`0,85 × Σ Fare_charged(i)`) ở Mục 17.2.
2. **Các phương án khả thi:**
   - *Phương án A (Strict Post-Rounding Hourly Rate Gate):* Bổ sung điều kiện lọc cứng `[0,85 × Σ_{i ∈ N} Fare_charged(i)] / (T_plan / 60) >= (1 - ε_hourly) × max_i [0,80 × PrivateFare(i) / (T_direct_i / 60)]` (với `ε_hourly = 0.00`) ngay sau bước tính `Fare_charged(i)` tại Mục 14.2 & Mục 36.
   - *Phương án B (Relaxed Gate + Increase Stop Fee):* Đặt `ε_hourly = 0.05` (cho phép dung sai 5%) hoặc tăng `STOP_FEE` từ `5.000 đ` lên `10.000 đ/điểm dừng`.
3. **Ưu/nhược điểm & Tác động:**
   - Phương án A đảm bảo bất biến ở Mục 17 và Mục 71 đúng **100% về mặt toán học trên chính số tiền thực nhận sau làm tròn** mà không phải sửa `STOP_FEE = 5.000 đ` (giữ nguyên toàn bộ con số của ví dụ chuẩn Mục 16.1 vì `210.800 / (52/60) = 243.231 >= 232.800 đ/giờ`). Nhược điểm là có thể từ chối một số cặp ghép chặng rất ngắn vào giờ tắc đường.
4. **Phương án khuyến nghị:** **Phương án A** (với `driver_hourly_rate_tolerance_eps = 0.00` làm mặc định trong `MVP_CONFIG_BASELINE_V1.md`, cho phép khảo sát độ nhạy ở mức `0.05` trong Simulator).
5. **Căn cứ lựa chọn:** Giữ vững tính nhất quán tuyệt đối cho cổng kiểm thử `G09` ở Mục 70–71.
6. **Trạng thái quyết định:** **`[ACCEPTED]`** (Đã phê duyệt chốt `enforce_driver_hourly_rate_gate = true` và `driver_hourly_rate_tolerance_eps = 0.00` trong `MVP_CONFIG_BASELINE_V1.md`).

---

## O-04: Hệ số phụ trội ghế thứ hai ($\gamma_{\text{seat}}$) cho Booking đặt 2 khách trong `CAR_URBAN_POOL` (Mục 12.2 & 15.2 — `D-45b`)
1. **Vấn đề phải giải quyết:** Một booking đặt `passenger_count = 2` chiếm 2/4 ghế của xe taxi ghép nhưng nếu dùng cùng trọng số như 1 ghế thì chỉ trả tiền ngang bằng 1 khách đi lẻ. Tuy nhiên, nếu nhân hệ số $(1 + \gamma_{\text{seat}})$ trực tiếp vào `PrivateFare(i)` khi tính `Cap_i`, `Quote_i`, `Gap_i` và `Unmatched_i`, thì với $\gamma_{\text{seat}} \in [0.20, 0.35]$, `Quote_i` sẽ vượt quá $0,80 \times \text{PrivateFare}(i)$ (vi phạm cam kết giảm tối thiểu $20\%$ tại Cổng `G07`) và `Unmatched_i` sẽ vượt quá $1,00 \times \text{PrivateFare}(i)$ (vi phạm `D-10`: đi ghép không ghép được lại đắt hơn tự gọi một chiếc taxi bao xe đi riêng!).
2. **Các phương án khả thi:**
   - *Phương án A (Chuẩn hóa trong Revision 9 — Giữ nguyên `P_i = PrivateFare(i)` cho trần giá và đưa $\gamma_{\text{seat}}$ vào trọng số chia tiết kiệm $w_i$ & cận dưới `Floor_i`):*
     - Giữ nguyên $P_i = \text{PrivateFare}(i)$, $\text{Cap}_i = (1 - d_{\min}) P_i$, $\text{Quote}_i$, $\text{Gap}_i = P_i - \text{Quote}_i$, $\text{Unmatched}_i$ và $\text{TargetDriverPayout}(i) = 0,80 P_i$.
     - Đưa hệ số chiếm ghế $\text{seat\_factor}(i) = 1 + \gamma_{\text{seat}}(s_i - 1)$ vào giảm trọng số nhận tiết kiệm $w_i = \frac{P_i(1 + \lambda d_i + \mu \omega_i)}{1 + \gamma_{\text{seat}}(s_i - 1)}$ và nâng cận dưới $\text{Floor}_i = \min(\text{EffectiveCap}_i, \max(\text{BASE}, P_i(1 - d_{\max})(1 + \gamma_{\text{seat}}(s_i - 1))))$.
   - *Phương án B:* Không phân biệt số ghế trong công thức chia tiền ($\gamma_{\text{seat}} = 0,00$), chỉ trừ 2 ghế về mặt sức chứa.
3. **Ưu/nhược điểm & Tác động:**
   - Phương án A bảo toàn **100% không mâu thuẫn** với mọi bất biến chính sách giá (`Fare_charged(i) <= Quote_i <= 0,80 × PrivateFare(i) < Unmatched_i < PrivateFare(i)` và `TargetDriverPayout = 0,80 × PrivateFare(i)`), đồng thời đảm bảo nhóm 2 ghế luôn trả cao hơn nhóm 1 ghế trên cùng tuyến khi ghép thành công (ví dụ Mục 16.1: nếu A đi 2 ghế thì A trả `148.000 đ` thay vì `143.000 đ`, và người đi cùng B được giảm từ `105.000 đ` xuống `99.000 đ`).
4. **Phương án khuyến nghị:** **Phương án A** với giá trị mặc định baseline `party_seat_surcharge_gamma = 0.35` (miền hợp lệ `[0.00, 0.50]`).
5. **Trạng thái quyết định:** **`[ACCEPTED]`** (Đã phê duyệt chốt `party_seat_surcharge_gamma = 0.35` trong `MVP_CONFIG_BASELINE_V1.md`).

---

## O-05: Hạch toán phần lẻ làm tròn xuống `1.000 đ` và Đơn vị cơ sở trên Smart Contract (Mục 17.2 & 80.1 — `D-48, D-51`)
1. **Vấn đề phải giải quyết:** Khớp số liệu giữa tuyên bố Mục 15.4 (*"phần lẻ nền tảng chịu"*), phép tính Mục 17 (`210.800 đ = 85% × 248.000 đ`) và đơn vị token trên hợp đồng thông minh (Mục 80).
2. **Phương án khuyến nghị & Đã chuẩn hóa:**
   - Tínhtoán hoa hồng `15%` (`12%` nền tảng + `3%` Quỹ) và phần tài xế nhận `85%` trực tiếp trên tổng tiền thực thu sau làm tròn `Fare_charged(i)` (giữ đúng con số `210.800 đ` của Mục 17).
   - Quy ước đơn vị tiền tệ trên Smart Contract là **`1 VND` (`uint256` nguyên)**.
3. **Căn cứ lựa chọn:** Vì `Fare_charged(i)` là bội số của `1.000 VND`, mọi phép nhân `85%`, `12%`, `3%`, `80%`, `20%`, `90%`, `10%` đều cho kết quả nguyên tuyệt đối theo đơn vị `1 VND`, giúp PostgreSQL và Smart Contract khớp nhau 100% không lệch 1 xu.
4. **Trạng thái quyết định:** **`[ACCEPTED]`**.

---

## O-06: Cổng kiểm tra ký quỹ trước `RIDE_STARTED` và Mô hình ví ở phạm vi MUST (Mục 9.3 & 80.1 — `D-34, D-49`)
1. **Vấn đề phải giải quyết:** Ký quỹ bất đồng bộ giúp không làm chậm bước `CONFIRMED`, nhưng nếu xe bắt đầu chạy và hoàn thành khi giao dịch ký quỹ bị lỗi thì không thể giải ngân; đồng thời tính năng liên kết ví cá nhân MetaMask (C7) lại nằm ở mức COULD.
2. **Phương án khuyến nghị:**
   - Đặt cổng chặn bắt buộc `escrow_status == DEPOSITED` tại API `POST /api/rides/{id}/start` (timeout tự động hủy sau `120s` nếu ký quỹ lỗi).
   - Ở mức MUST (M12), `escrow_adapter` sử dụng ví Testnet dẫn xuất từ `HD Wallet` của hệ thống để ký tự động cho từng tài khoản; ở mức COULD (C7) mở thêm giao diện ký trực tiếp qua MetaMask.
3. **Trạng thái quyết định:** **`[ACCEPTED]`** cho cổng chặn `RIDE_STARTED` và chế độ ví `CUSTODIAL_HD_RELAYER` ở mức MUST; việc đối chiếu ABI hợp đồng cũ trước Phase 9 được theo dõi tại `EXT-02` (`[NEEDS_EXTERNAL_CONFIRMATION]`).

---

## O-07: Lựa chọn tên đề tài chính thức và Phân tầng mẫu Khảo sát S1 (Mục 0.1 & 65 — `D-30`)
1. **Vấn đề phải giải quyết:** Chốt tên đề tài đăng ký với Khoa và đảm bảo dữ liệu khảo sát S1 đủ độ tin cậy thống kê cho cả 5 dịch vụ.
2. **Phương án khuyến nghị:**
   - Trình giảng viên hướng dẫn phê duyệt 1 trong 3 phương án tên đề tài ở Mục 0.1 (khuyến nghị Phương án 1 hoặc Phương án 3).
   - Khảo sát S1 thu thập `100–200` người với tỷ lệ phân tầng tối thiểu `40%` người đã đi làm / hay đi tỉnh và dùng `5-Fold GroupKFold CV` khi đánh giá mô hình.
3. **Trạng thái quyết định:** Tên đề tài là **`[NEEDS_EXTERNAL_CONFIRMATION]`** (từ giảng viên hướng dẫn); kết quả khảo sát S1 là **`[NEEDS_VALIDATION]`** (khi thu thập dữ liệu thực tế).

---

## O-08: Cho phép hay đóng cứng việc đặt ghế vét trên chuyến ghép liên tỉnh đã `CONFIRMED` trong khoảng `[T−72h, T−24h]` (Mục 2.2 & 27)
1. **Vấn đề phải giải quyết:** Một chuyến ghép liên tỉnh đã đạt ngưỡng `3/4 ghế` tại `T−72h` và đã chuyển sang `CONFIRMED` (chắc chắn chạy) vẫn còn trống `1 ghế` trong suốt 2 ngày từ `T−72h` đến `T−24h` (trước khi chốt thứ tự đón).
2. **Các phương án khả thi:**
   - *Phương án A (Strict T−72h Cutoff — Mặc định hiện tại):* Đóng cứng toàn bộ việc đặt ghế mới tại `T−72h` cho mọi chuyến để đơn giản hóa kiểm thử cổng `G14`.
   - *Phương án B (Late Seat Booking on Confirmed Trips):* Chỉ đóng các chuyến chưa đủ ngưỡng tại `T−72h`; riêng các chuyến **đã `CONFIRMED` tại `T−72h` và còn ghế trống** được phép nhận thêm khách đặt ghế vét (không hoàn hủy) cho đến mốc chốt thứ tự đón `T−24h`.
3. **Phương án khuyến nghị:** Trong phạm vi MUST giữ mặc định `allow_post_confirm_late_booking: false` (Phương án A) để khớp 100% với các ca kiểm thử ở Mục 72; cung cấp sẵn cờ cấu hình `allow_post_confirm_late_booking: true` (Phương án B) như một cải tiến tùy chọn.
4. **Trạng thái quyết định:** **`[ACCEPTED]`** (Đã phê duyệt chốt mặc định `allow_post_confirm_late_booking: false` trong `MVP_CONFIG_BASELINE_V1.md`).
