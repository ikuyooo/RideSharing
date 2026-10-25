# SỔ ĐĂNG KÝ QUYẾT ĐỊNH THIẾT KẾ — REVISION 9 (`REVISION_9_DECISION_REGISTER.md`)

**Dự án:** Nền tảng Đặt xe Thông minh Đa dịch vụ tích hợp Định giá ghép công bằng, AI Learning-to-Rank và Ký quỹ Blockchain  
**Phiên bản đặc tả:** Revision 9 (Đã khóa cấu hình với `MVP_CONFIG_BASELINE_V1.md`)  
**Trạng thái sẵn sàng:** **`READY FOR MVP IMPLEMENTATION`**  
**Ngày cập nhật:** 23/10/2026

## Quy ước Nhãn trạng thái Quyết định (Decision Status Taxonomy)

- **`ACCEPTED`**: Quyết định đã có đầy đủ cơ sở toán học, kỹ thuật và nghiệp vụ vững chắc, đã được Chủ dự án phê duyệt chính thức và khóa trong `BAO_CAO_TIEN_DU_AN_RIDE_SHARING_REVISION_9.md` cùng `MVP_CONFIG_BASELINE_V1.md`.
- **`PROPOSED`**: Phương án đề xuất còn chờ phê duyệt (Hiện tại: **`0` quyết định** — toàn bộ các tham số mặc định của MVP đã được Chủ dự án phê duyệt chuyển sang `ACCEPTED`).
- **`NEEDS_VALIDATION`**: Quyết định có khung lý thuyết và giá trị mặc định hợp lý nhưng cần dữ liệu thực nghiệm (Khảo sát người dùng S1, chạy mô phỏng đa kịch bản hoặc benchmark hiệu năng ở Phase 7–8, 10–11) để kiểm định thống kê.
- **`NEEDS_EXTERNAL_CONFIRMATION`**: Quyết định phụ thuộc vào sự xác nhận của giảng viên hướng dẫn (như tên đề tài chính thức), kiểm tra mã nguồn hợp đồng thông minh hiện có trước Phase 9, hoặc tư vấn pháp lý chuyên ngành khi thương mại hóa.

---

## 1. BẢNG TỔNG HỢP TOÀN BỘ QUYẾT ĐỊNH THIẾT KẾ (`D-01` ĐẾN `D-52`)

### Nhóm I — Các quyết định nền tảng được bảo toàn từ Revision 5–8 (`ACCEPTED`)

| Mã QĐ | Tên quyết định | Nội dung cốt lõi | Mục trong Rev 9 | Trạng thái |
|---|---|---|---|---|
| **D-01** | Khung thời gian đặt xe 3 mốc | Sử dụng `T_preferred` kết hợp khoảng chấp nhận `[T_earliest, T_latest]` và tùy chọn `latest_arrival`. | Mục 6, 7 | `ACCEPTED` |
| **D-02** | Tách biệt Matching và Recommendation | Mọi ứng viên phải vượt qua toàn bộ 11 ràng buộc cứng và cổng kinh tế trước khi đưa vào mô hình AI xếp hạng. | Mục 7, 43 | `ACCEPTED` |
| **D-03** | Snapshot ứng viên bất biến | Mỗi ứng viên sinh ra là một bản chụp bất biến gắn với `source_plan_version` của kế hoạch/chuyến xe gốc. | Mục 42, 56 | `ACCEPTED` |
| **D-04** | Kiểm tra sức chứa theo đoạn | Sức chứa phương tiện (`BIKE = 1`, `CAR4 = 4`) được kiểm tra trên từng đoạn giữa hai điểm dừng liên tiếp. | Mục 7, 36 | `ACCEPTED` |
| **D-05** | Tách biệt độ đi vòng Khách và Tài xế | Kiểm tra độc lập tỉ lệ đi vòng của từng hành khách (`max_passenger_detour_ratio`) và giới hạn đi vòng của tài xế. | Mục 7, 36 | `ACCEPTED` |
| **D-07** | Kiến trúc 5 dịch vụ trên 1 lõi chung | Phục vụ `BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`, `CAR_INTERCITY_PRIVATE`, `CAR_INTERCITY_POOL`. | Mục 2.1 | `ACCEPTED` |
| **D-08** | Cửa sổ ghép động và `pool_lock_point` | Taxi ghép nội đô nhận thêm khách cả khi đang chạy; khóa trạng thái `MATCHED_LOCKED` / `UNMATCHED_LOCKED` tại `pool_lock_point`. | Mục 11, 22 | `ACCEPTED` |
| **D-09** | Chia sẻ khoảng chênh ba bên khi không ghép được | Khi không tìm được người ghép do thị trường, khách chịu $\alpha = 0,50$ khoảng chênh `Gap_i = P_i - Quote_i` (với $P_i = \text{PrivateFare}(i)$). | Mục 18.3 | `ACCEPTED` |
| **D-10** | Trần giá không ghép luôn rẻ hơn xe đơn | `Fare_charged(i) <= Quote_i < Unmatched_i < PrivateFare(i)` trong mọi trường hợp hợp lệ (kể cả booking 2 ghế). | Mục 12.2, 18.3, 71 | `ACCEPTED` |
| **D-11** | Kiểm tra ngân sách cứng với giá tối đa | Ứng viên `CAR_URBAN_POOL` phải thỏa mãn `Unmatched_i <= B_max`. | Mục 7, 20 | `ACCEPTED` |
| **D-12** | Bảo đảm thu nhập tài xế khi không ghép được | Khi `UNMATCHED_LOCKED` do thị trường (`NO_COMPATIBLE`), Quỹ bảo đảm chi bù để tài xế nhận đúng bằng chạy xe đơn ($0,80 \times \text{PrivateFare}(i)$). | Mục 18.3, 18.4 | `ACCEPTED` |
| **D-13** | Động cơ kinh tế thay cho hạn ngạch `Quota 4:1` | Không ép buộc tài xế bằng hạn ngạch cứng trong vận hành chuẩn; giữ `Quota 4:1` làm kịch bản đối chứng thí nghiệm (C6/H8). | Mục 21, 74 | `ACCEPTED` |
| **D-14** | Cam kết tự động nhận khách tương thích | Tài xế nhận booking khởi tạo kế hoạch Pool đồng nghĩa với việc cho phép hệ thống tự động chèn khách tương thích nằm trong ngưỡng đã khai. | Mục 18.6 | `ACCEPTED` |
| **D-15** | Chế tài cắt bảo đảm khi phá ghép | Tài xế từ chối khách ghép tương thích không có lý do an toàn bị mất 100% bảo đảm (chỉ nhận $85\% \times \text{Quote}_i$), khách chỉ trả `Quote_i`. | Mục 18.5, 18.6 | `ACCEPTED` |
| **D-16** | Cổng khả năng chia sẻ của khách (Shareability Gate 1) | Kế hoạch ghép phải thỏa mãn `PlanFare <= (1 - d_min) × Σ P_i` với `d_min = 0,20` và $P_i = \text{PrivateFare}(i)$. | Mục 14.1 | `ACCEPTED` |
| **D-17** | Trọng số phân bổ tiết kiệm theo bất tiện | $w_i = P_i \times (1 + \lambda \cdot \text{detour}_i + \mu \cdot \text{walk\_ratio}_i) / (1 + \gamma_{\text{seat}}(s_i - 1))$ với $\lambda = 1,0$ và $\mu = 2,0$. | Mục 15.2, 23.3 | `ACCEPTED` |
| **D-18** | Quy tắc làm tròn xuống `1.000 đ` | Mọi mức giá thu của hành khách (`Fare_charged`) đều làm tròn xuống đến bội số `1.000 đ`. | Mục 15.4 | `ACCEPTED` |
| **D-19** | Cơ chế thu – chi Quỹ bảo đảm ghép | Trích `3%` từ `Fare_charged` của mỗi booking ghép thành công vào `fund_ledger`; báo cáo tách bạch `p*_booking` (`62,8%`) và `p*_ride` (`45,8%`). | Mục 17, 19 | `ACCEPTED` |
| **D-22** | Điểm đón gặp nhau trên đường trục (C9) | Xếp ở mức COULD; tắt tự động từ `22:00–05:00`, khi trời mưa hoặc khi khách có hành lý lớn. | Mục 23 | `ACCEPTED` |
| **D-23** | Mẫu chuyến quen lặp lại hằng ngày (C4) | Tự động sinh yêu cầu `SCHEDULED` ở mốc `T−12h` thông qua bảng `scheduled_jobs`. | Mục 24 | `ACCEPTED` |
| **D-24** | Ràng buộc cứng thời gian ngồi trên xe | Mặc định `max_in_vehicle_time = 1,5 × T_direct + 10 phút` cho taxi ghép nội đô. | Mục 7 | `ACCEPTED` |
| **D-25** | Kiểm soát đồng thời 3 lớp | Kết hợp `SELECT ... FOR UPDATE`, kiểm tra `plan_version` và `Idempotency-Key` (TTL 24 giờ). | Mục 42 | `ACCEPTED` |
| **D-26** | Tách biệt sở thích và khả năng hoàn thành | Mô hình hóa độc lập xác suất khách chọn (`LTR`) và xác suất chuyến đi hoàn thành (`p_fulfill` theo cây sự kiện tuần tự 3 cổng). | Mục 39, 43, 46 | `ACCEPTED` |
| **D-27** | Hiệu chỉnh xác suất điểm LTR | Chỉ nhân `p_hat_select × p_fulfill` sau khi điểm LTR đã qua bước hiệu chỉnh Temperature Scaling đạt `ECE <= 0.05`. | Mục 47 | `ACCEPTED` |
| **D-28** | Tường lửa chống rò rỉ biến ẩn Simulator | Cấm tuyệt đối việc xuất các tham số ẩn $\boldsymbol{\theta}_u$ hoặc xác suất thật của Simulator ra tập dữ liệu huấn luyện. | Mục 43, 48.4, 67 | `ACCEPTED` |
| **D-31** | Kiến trúc Modular Monolith + DB Jobs | Một ứng dụng FastAPI chia 16 module rõ ranh giới + bảng `scheduled_jobs` dùng `FOR UPDATE SKIP LOCKED`. | Mục 5, 54, 55 | `ACCEPTED` |
| **D-32** | Thứ tự ưu tiên triển khai và KYC Mock | Triển khai theo thứ tự `Core → AI → Blockchain → Mở rộng ghép`; duyệt KYC tài xế thực hiện dạng mock bởi Admin. | Mục 79, 81 | `ACCEPTED` |
| **D-33** | Nguyên tắc ký quỹ theo mức giá trần | Luôn khóa ký quỹ bằng mức nghĩa vụ tài chính tối đa (`quoted_price_cap`), sau đó chỉ hoàn bớt khi chốt giá hoặc nạp thêm khi đồng ý `topUp`. | Mục 80.1, 80.2 | `ACCEPTED` |
| **D-35** | Giới hạn dịch vụ Xe máy (`BIKE_URBAN`) | Chỉ chạy 1:1 trong nội đô, đúng 1 hành khách, không mang hành lý lớn. | Mục 2.1, 10.1 | `ACCEPTED` |
| **D-37** | Cửa sổ đặt và chốt chuyến ghép liên tỉnh | Đặt trước từ `72 giờ` đến `7 ngày`; đóng đặt chỗ chuẩn và kích hoạt quy trình chốt chuyến tại `T−72h`. | Mục 2.2, 27, 29 | `ACCEPTED` |
| **D-41** | Giữ nguyên dịch vụ trong chuỗi Offer | Chuỗi `Offer Cascade` chỉ chuyển tiếp giữa các ứng viên thuộc cùng dịch vụ mà hành khách đã chọn. | Mục 41 | `ACCEPTED` |
| **D-42** | Không gửi Offer cho chuyến ghép liên tỉnh | Tài xế đăng chuyến ghép liên tỉnh là đã cam kết nhận mọi lượt đặt ghế hợp lệ trong vùng đón/trả. | Mục 2.4, 26 | `ACCEPTED` |

---

### Nhóm II — Các quyết định được sửa đổi, nâng cấp và phê duyệt khóa trong Revision 9 (`D-06`, `D-20`, `D-21`, `D-29`, `D-30`, `D-34`, `D-36`, `D-38..D-40`, `D-43..D-52`)

| Mã QĐ | Tên quyết định cập nhật / mới | Nội dung chi tiết & Giải pháp kỹ thuật đã khóa | Mục trong Rev 9 | Trạng thái |
|---|---|---|---|---|
| **D-06** *(Sửa)* | Thuật toán chèn điểm động nhận biết trạng thái xe đang chạy | Bổ sung chỉ số `r = completed_stop_index` và nút gốc hiện tại `S_curr` khi `RIDE_STARTED`; chỉ duyệt chèn điểm mới vào phía trước `S_curr` và cộng quãng đường đã đi `traveled_km` cho khách đang trên xe. | Mục 36, 56 | `ACCEPTED` |
| **D-20** *(Sửa)* | Tự động phân loại `URBAN / INTERCITY` có vùng đệm `15 km` | Kết hợp đa giác `urban_service_area` với điều kiện khoảng cách `urban_boundary_buffer_km = 15,0 km` (chuyến ngắn $\le 15\text{ km}$ có 1 đầu trong nội đô được tính là `URBAN`) và kiểm tra `total_service_area` (`150 km`). | Mục 2.3, 72 | `ACCEPTED` |
| **D-21** *(Sửa)* | Ghép theo lô CP-SAT trên Đồ thị RTV rút gọn | Thay thế đồ thị hai phía `RV` cộng tuyến tính bằng **Đồ thị 3 tầng RTV rút gọn**: mỗi biến quyết định $x_t \in \{0,1\}$ đại diện cho một tổ hợp 1 hoặc 2 yêu cầu mới đã được kiểm tra chèn đồng thời qua Mục 36. | Mục 37.2 | `ACCEPTED` |
| **D-29** *(Sửa)* | Huấn luyện `P(match)` theo quy trình Out-of-Fold (OOF) | Bắt buộc dùng dự đoán `5-Fold Out-of-Fold Cross-Fitting` khi tạo đặc trưng `p_match_oof_est` và `ExpectedPrice` trên tập `Train` của `LGBMRanker` để chống rò rỉ nhãn in-sample. | Mục 40, 45.3 | `ACCEPTED` |
| **D-30** *(Sửa)* | Khảo sát S1 phân tầng mẫu & Đánh giá `5-Fold GroupKFold CV` | Phân tầng đối tượng khảo sát (40%–60% sinh viên, 40%–60% người đi làm) và dùng `5-Fold GroupKFold CV` theo `respondent_id` để đánh giá H1/H9 trên toàn bộ 100% mẫu người thật. | Mục 65, 75 | `NEEDS_VALIDATION` |
| **D-34** *(Chốt)* | Ký quỹ bất đồng bộ lúc đặt kết hợp Cổng chặn đồng bộ trước `RIDE_STARTED` | Cho phép xác nhận `CONFIRMED` trước khi giao dịch on-chain hoàn tất để giữ độ trễ thấp, nhưng chặn không cho chuyển sang `RIDE_STARTED` nếu `escrow_status != DEPOSITED` (timeout hủy tự động sau `120s`). | Mục 9.3, 80.1 | `ACCEPTED` |
| **D-36** *(Chốt)* | Giữ giới hạn hẹn trước `max_ahead_days = 7` cho Taxi bao xe liên tỉnh | Cho phép đặt `CAR_INTERCITY_PRIVATE` trước tối đa 7 ngày để hành khách có chuyến ghép liên tỉnh bị hủy tại `T−72h` (còn 3 ngày) chuyển đổi sang đặt bao xe được ngay lập tức. | Mục 2.2, 25.1 | `ACCEPTED` |
| **D-38** *(Sửa)* | Khóa cứng ngưỡng chuẩn `min_seats_ref = 3` khi tính `SeatReference` | Cố định `min_seats_ref = 3` ở mức nền tảng để tính giá ghế tham chiếu (ngăn tài xế đặt ngưỡng = 4 nhằm hạ giá ảo rồi ép khách góp thêm). | Mục 26, 28.1 | `ACCEPTED` |
| **D-39** *(Sửa)* | Bổ sung trạng thái `MERGE_PENDING_CONFIRMATION` (2 giờ) tại `T−72h` | Khi gộp chuyến tại `T−72h`, khách chuyến bị gộp hưởng giá `min(giá_cũ, giá_mới)` và có 2 giờ (`T−72h → T−70h`) để hủy miễn phí; sau 2 giờ nếu vẫn đủ ghế mới chốt `CONFIRMED`, nếu thiếu chuyển sang `TOPUP_OFFERED`. | Mục 29, 30.2, 32 | `ACCEPTED` |
| **D-40** *(Sửa)* | Bảo toàn đa dạng dịch vụ trong `Top-K` và Nâng giả thuyết `H9` lên MUST | Giữ ít nhất 1 ứng viên đại diện cho mỗi dịch vụ hợp lệ có xe trong `Top-K`; nâng kiểm định phân khúc đa phương tiện nội đô 1 khách (`H9`) từ SHOULD lên **MUST**. | Mục 10.5, 35.5, 74 | `ACCEPTED` |
| **D-43** *(Mới)* | Cận dưới `Floor_i`, Điều kiện khả thi `(F1, F2, F3)` và Thuật toán điểm gãy hai cận | Định nghĩa $\text{Floor}_i = \min(\text{EffectiveCap}_i, \max(\text{BASE}, P_i(1 - d_{\max})(1 + \gamma_{\text{seat}}(s_i - 1))))$ với `d_max = 0,60`; quy định điều kiện cần và đủ $\sum_{i \in U} \text{Floor}_i \le \text{TargetFare}_U \le \sum_{i \in U} \text{EffectiveCap}_i$, giải bằng nội suy điểm gãy và từ chối ứng viên (`on_lower_bound_infeasible = "REJECT"`) khi vô nghiệm. | Mục 15.3, 16.2 | `ACCEPTED` |
| **D-44** *(Mới)* | Hệ 6 điều kiện đầy đủ (`D1–D6`) khi chèn khách động lúc giá cũ đã khóa | Bật `allow_dynamic_insertion_after_partial_lock = true`: đóng băng nhóm đã khóa giá ($L$), kiểm tra $U_{\text{old}} \ne \emptyset$ có giao đoạn đường (`D1`), kiểm tra đồng thời cả cận trên ($\Delta\text{PlanFare} \le \text{Cap}_{c_{\text{new}}}$ — `D3`) lẫn cận dưới ($\text{TargetFare}_U \ge \sum_{m \in U} \text{Floor}_m$ — `D4`) trên tập chưa khóa $U$, và kiểm tra Cổng 2 sau làm tròn (`D5`). | Mục 15.5, 16.3, 36 | `ACCEPTED` |
| **D-45a** *(Mới)* | Cổng bảo toàn tốc độ thu nhập/giờ của tài xế tính trên Khoản Payout thực tế sau làm tròn | Bật `enforce_driver_hourly_rate_gate = true` với `ε_hourly = 0,00`: kiểm tra `[0,85 × Σ_{i ∈ N} Fare_charged(i)] / (T_plan / 60) >= (1 - ε_hourly) × max_i [0,80 × PrivateFare(i) / (T_direct(i) / 60)]` ngay sau bước làm tròn `Fare_charged(i)` tại Mục 14.2 và Mục 36. | Mục 14.2, 17, 36, 71 | `ACCEPTED` |
| **D-45b** *(Mới)* | Tách biệt `PrivateFare(i)` cho trần giá và Hệ số ghế thứ hai ($\gamma_{\text{seat}} = 0,35$) trong trọng số $w_i$ & `Floor_i` | Giữ nguyên $P_i = \text{PrivateFare}(i)$ cho `Cap_i, Quote_i, Gap_i, Unmatched_i, TargetDriverPayout(i)` (bảo đảm `Fare_charged <= Quote_i < Unmatched_i < PrivateFare(i)` cho cả booking 2 ghế); áp dụng $\text{seat\_factor}(i) = 1 + 0,35(s_i - 1)$ vào giảm trọng số chia tiết kiệm $w_i$ và nâng `Floor_i`. | Mục 12.2, 15.2, 15.3, Phụ lục E (O-04) | `ACCEPTED` |
| **D-46** *(Mới)* | Máy trạng thái trực giao 3 trục trên bảng `bookings` | Tách cột trạng thái thành 3 trường độc lập: `ride_status`, `price_status` và `escrow_status`. | Mục 9, 22, 56 | `ACCEPTED` |
| **D-47** *(Mới)* | Cơ chế giữ ghế theo từng bước Offer (`Per-Offer Seat Hold`) | Cấp phát và giải phóng `seat_hold` riêng trên từng `ride_plan` ứng viên ở mỗi bước của chuỗi `Offer Cascade` với `TTL = offer_timeout_s + 15s` (`35s` nội đô / `75s` liên tỉnh). | Mục 41, 73 | `ACCEPTED` |
| **D-48** *(Mới)* | Đơn vị tiền tệ nguyên `1 VND` và Quỹ bảo đảm nội bộ trên Smart Contract | Quy ước `1 Base Unit = 1 VND` (`uint256` nguyên) trong mọi hàm hợp đồng thông minh và lưu số dư Quỹ bảo đảm trong biến trạng thái `guaranteeFundBalance` của hợp đồng. | Mục 80.1, 80.2, 80.3 | `ACCEPTED` |
| **D-49** *(Mới)* | Mô hình ví Custodial Relayer ở mức MUST và MetaMask ở mức COULD | Ở mức MUST (M12), `escrow_adapter` dùng ví dẫn xuất từ `HD Wallet` (`CUSTODIAL_HD_RELAYER`) để ký tự động; ở mức COULD (C7) cho phép người dùng tự liên kết ví MetaMask. | Mục 80.1, Phụ lục E (O-06) | `ACCEPTED` |
| **D-50** *(Mới)* | Công thức tất định cho `DoorSurcharge` liên tỉnh và `Fare_matched_est` nội đô | Tính `DoorSurcharge` theo khoảng cách OSRM tới đường biên `pickup_zone_ids`/`dropoff_zone_ids`; tính `Fare_matched_est` cho xe rảnh theo tỷ lệ giảm điển hình `d_matched_typical = 0,25`. | Mục 20.2, 28.3 | `ACCEPTED` |
| **D-51** *(Mới)* | Thống nhất hạch toán hoa hồng trên `Fare_charged` và hoa hồng `15%` cho `CONFIRMED_TOPUP` | Tính `85%` tài xế, `12%` nền tảng, `3%` Quỹ trực tiếp trên số tiền thực thu đã làm tròn `Fare_charged`; áp dụng hoa hồng `c_private = 15%` khi chuyến liên tỉnh chạy ở chế độ góp thêm `CONFIRMED_TOPUP`. | Mục 17.2, 29 | `ACCEPTED` |
| **D-52** *(Mới)* | Khung tham số Chính sách phí hủy chuẩn (`Cancellation Policy`) | Phê duyệt bảng tỷ lệ phí hủy chuẩn và quy tắc phân bổ tiền phạt hủy (giúp bảo vệ chuyến liên tỉnh đã chốt sau `T−72h`) tại Mục 18.7 và Phụ lục B ngay trong phạm vi MUST. | Mục 18.7, Phụ lục B | `ACCEPTED` |
| **O-07** *(Mở)* | Xác nhận tên đề tài chính thức và định hướng pháp lý Hợp đồng đồng thuê chuyến | Trình giảng viên hướng dẫn xác nhận phương án tên đề tài (Mục 0.1) và ghi nhận giải pháp Hợp đồng điện tử đồng thuê chuyến (Co-Charter Contract) theo [Nghị định 158/2024/NĐ-CP](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-158-2024-ND-CP-quy-dinh-hoat-dong-van-tai-duong-bo-636875.aspx). | Mục 0.1, 61, Phụ lục E | `NEEDS_EXTERNAL_CONFIRMATION` |
