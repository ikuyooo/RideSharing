# BỘ CẤU HÌNH BASELINE ĐÓNG BĂNG CHO MVP — REVISION 9 (`MVP_CONFIG_BASELINE_V1.md`)

**Dự án:** Nền tảng Đặt xe Thông minh Đa dịch vụ (Xe máy, Taxi bao xe, Taxi ghép Nội đô & Liên tỉnh) tích hợp Định giá ghép công bằng, AI Learning-to-Rank và Ký quỹ Blockchain  
**Mã phiên bản cấu hình:** `MVP_CONFIG_BASELINE_V1` (`pricing_version: price_v9_two_sided_bounded`)  
**Trạng thái cấu hình:** **`LOCKED & APPROVED`** (Đã được Chủ dự án phê duyệt toàn bộ tham số mặc định — Ngày 23/10/2026)  
**Trạng thái sẵn sàng của Dự án:** **`READY FOR MVP IMPLEMENTATION`**  
**Tài liệu tham chiếu đồng bộ:**
- `BAO_CAO_TIEN_DU_AN_RIDE_SHARING_REVISION_9.md` (Bản đặc tả Tiền dự án toàn diện — 84 mục & 5 phụ lục)
- `REVISION_9_DECISION_REGISTER.md` (Sổ đăng ký quyết định thiết kế `D-01` đến `D-52`)
- `REVISION_9_OPEN_ISSUES.md` (Danh mục phân loại các vấn đề thực nghiệm & xác nhận bên ngoài)
- `REVISION_8_TO_REVISION_9_CHANGELOG.md` (Nhật ký thay đổi và đối chiếu kiểm toán)

---

## 1. MỤC ĐÍCH VÀ NGUYÊN TẮC QUẢN TRỊ CẤU HÌNH (`CONFIGURATION GOVERNANCE`)

Tài liệu này khóa bộ cấu hình chuẩn (`Baseline v1`) của hệ thống để bắt đầu giai đoạn xây dựng phần mềm, đảm bảo:
1. **Không còn bất kỳ mâu thuẫn toán học hoặc xung đột trạng thái nào** giữa các công thức định giá, đơn vị tiền tệ (`1 VND`), khoản thực nhận của tài xế sau làm tròn (`driver_payouts`), máy trạng thái trực giao 3 trục và các cổng đúng đắn `= 0` (`G01–G18`).
2. **Phân định rõ trạng thái quyết định sau khi Chủ dự án phê duyệt:**
   - **`ACCEPTED` (Đã phê duyệt và khóa cấu hình Baseline v1):** Toàn bộ các quy tắc cơ chế (`D-01` đến `D-29`, `D-31` đến `D-52`) và toàn bộ các tham số mặc định của MVP (bao gồm cả nhóm tham số `O-01..O-06, O-08` vừa được Chủ dự án phê duyệt chính thức) đều đã mang trạng thái **`ACCEPTED`**.
   - **`NEEDS_VALIDATION` (Cần kiểm chứng thực nghiệm trong quá trình chạy Simulator & Khảo sát S1):** Gồm 4 hạng mục thực nghiệm `V-01` đến `V-04` (`D-30`), sẽ được giải quyết bằng dữ liệu ở Phase 0–2 và Phase 7–11.
   - **`NEEDS_EXTERNAL_CONFIRMATION` (Cần xác nhận từ bên liên quan bên ngoài trước khi tích hợp/vận hành):** Gồm `EXT-01` (xác nhận tên đề tài với GVHD), `EXT-02` (đối chiếu tệp `.sol` hiện có trước Phase 9), và `EXT-03` (lưu ý pháp lý nếu thương mại hóa sau đồ án).

---

## 2. TÓM TẮT 4 HIỆU CHỈNH ĐỒNG BỘ ĐÃ KHÓA TRONG CẤU HÌNH (`LOCKED MATHEMATICAL RULES`)

### 2.1. Quy tắc `party_seat_surcharge_gamma` ($\gamma_{\text{seat}} = 0.35$), `Quote_i`, `Gap_i`, `Unmatched_i` cho Booking 2 ghế (`D-45b` / `O-04` — `ACCEPTED`)
- **Công thức chuẩn hóa đã khóa (Mục 12.2, 15.2, 15.3, 18.3):**
  1. **Giữ nguyên Giá tham chiếu độc lập $P_i \equiv \text{PrivateFare}(i)$ cho cả $s_i = 1$ và $s_i = 2$** khi tính:
     - Cổng Shareability 1: $\text{PlanFare} \le (1 - d_{\min}) \sum_{i \in N} P_i$.
     - Trần giá ghép: $\text{Cap}_i = P_i \times (1 - d_{\min})$ và $\text{Quote}_i = \lfloor \text{Cap}_i / 1.000 \rfloor \times 1.000$.
     - Khoảng chênh và giá không ghép: $\text{Gap}_i = P_i - \text{Quote}_i$, $\text{Unmatched}_i = \lfloor (\text{Quote}_i + \alpha \cdot \text{Gap}_i) / 1.000 \rfloor \times 1.000$.
     - Thu nhập mục tiêu của tài xế khi không ghép được: $\text{TargetDriverPayout}(i) = (1 - c_{\text{private}}) \times P_i = 0,80 \times \text{PrivateFare}(i)$.
     $\implies$ **Bảo đảm 100% bất biến:** $\text{Fare\_charged}(i) \le \text{Quote}_i \le 0,80 \times \text{PrivateFare}(i) < \text{Unmatched}_i < \text{PrivateFare}(i)$ cho mọi booking 1 ghế và 2 ghế!
  2. **Áp dụng hệ số chiếm ghế $\text{seat\_factor}(i) = 1 + \gamma_{\text{seat}} \times (s_i - 1)$ (với $\gamma_{\text{seat}} = 0,35$) vào trọng số chia tiết kiệm $w_i$ và cận dưới `Floor_i`:**
     $$w_i = \frac{P_i \times (1 + \lambda \cdot \text{detour}_i + \mu \cdot \text{walk\_ratio}_i)}{1 + \gamma_{\text{seat}} \times (s_i - 1)}, \qquad \text{Floor}_i = \min\Big(\text{EffectiveCap}_i,\; \max\big(\text{BASE},\; P_i (1 - d_{\max}) [1 + \gamma_{\text{seat}}(s_i - 1)]\big)\Big)$$
     $\implies$ Khi $s_i = 1$, mọi con số giữ nguyên 100%. Khi $s_i = 2$, nhóm 2 ghế nhận phần tiết kiệm nhỏ hơn và có sàn cao hơn nên luôn trả nhiều hơn 1 ghế trên cùng lộ trình (ví dụ ở Mục 16.1: nếu A đặt 2 ghế ghép với B 1 ghế, A trả `148.000 đ` thay vì `143.000 đ`, còn B giảm từ `105.000 đ` xuống `99.000 đ`), mà không bao giờ vượt trần `Quote_A = 155.000 đ`!

### 2.2. Điều kiện khả thi cần và đủ của Thuật toán phân bổ hai cận và Xử lý khi vô nghiệm (`D-43` / `O-01` — `ACCEPTED`)
- **Điều kiện cần và đủ (`F1, F2, F3` tại Mục 15.3.3):** Với tập khách chưa khóa $U \ne \emptyset$ và chi phí cần phân bổ $\text{TargetFare}_U$, nghiệm $\text{Fare\_exact}(i) \in [\text{Floor}_i, \text{EffectiveCap}_i]$ thỏa mãn $\sum_{i \in U} \text{Fare\_exact}(i) = \text{TargetFare}_U$ tồn tại **khi và chỉ khi**:
  1. **(F1):** $\text{Floor}_i \le \text{EffectiveCap}_i$ với mọi $i \in U$ (được bảo đảm tự động nhờ định nghĩa $\text{Floor}_i = \min(\text{EffectiveCap}_i, \text{RawFloor}_i)$).
  2. **(F2 — Cận dưới tổng):** $\sum_{i \in U} \text{Floor}_i \le \text{TargetFare}_U$.
  3. **(F3 — Cận trên tổng):** $\text{TargetFare}_U \le \sum_{i \in U} \text{EffectiveCap}_i$.
- **Thuật toán giải chính xác (Mục 15.3.4):** Giải phương trình đơn điệu tuyến tính từng khúc $\Phi(\tau) = \sum_{i \in U} \min(\text{EffectiveCap}_i, \max(\text{Floor}_i, P_i - \tau w_i)) = \text{TargetFare}_U$ trên tối đa $2|U| \le 8$ điểm gãy, tránh hoàn toàn lỗi lệch tổng khi có cả khách chạm `Cap` và khách chạm `Floor` trong cùng một kế hoạch.
- **Quy tắc tất định khi vô nghiệm (`on_lower_bound_infeasible = "REJECT"`):**
  - Nếu $\text{TargetFare}_U > \sum_{i \in U} \text{EffectiveCap}_i$: Trả về `INFEASIBLE_UPPER_BOUND` (`None`) $\to$ **Từ chối ứng viên ghép**.
  - Nếu $\text{TargetFare}_U < \sum_{i \in U} \text{Floor}_i$: Trả về `INFEASIBLE_LOWER_BOUND` (`None`) $\to$ **Từ chối ứng viên ghép** để bảo đảm Cổng `G06` (`0 trường hợp Fare_exact < Floor_i`) đạt tuyệt đối.

### 2.3. Hệ 6 điều kiện đầy đủ (`D1–D6`) khi chèn khách mới lúc giá cũ đã khóa (`D-44` / `O-02` — `ACCEPTED`)
Khi chèn khách mới $c_{\text{new}}$ vào kế hoạch đang chạy $N_{\text{old}} = L \cup U_{\text{old}}$ (`allow_dynamic_insertion_after_partial_lock = true`), phép chèn chỉ hợp lệ khi thỏa mãn đồng thời **cả 6 điều kiện tại Mục 15.5**:
1. **D1:** Kế hoạch đang ở `PLAN_OPEN_SEARCHING`, $U_{\text{old}} \ne \emptyset$, và lộ trình của $c_{\text{new}}$ có đoạn đi chung thực tế với ít nhất 1 khách đang trên xe.
2. **D2:** Đóng băng $\text{Fare\_exact}_{\text{new}}(k) = \text{Fare\_exact}_{\text{old}}(k)$ và $\text{final\_price}(k)$ cho mọi $k \in L$; đặt $\text{DynamicCap}_i = \text{Fare\_exact}_{\text{old}}(i)$ cho $i \in U_{\text{old}}$ và $\text{TargetFare}_U = \text{PlanFare}_{\text{new}} - \sum_{k \in L} \text{Fare\_exact}_{\text{old}}(k)$.
3. **D3 (Khả thi cận trên trên $U = U_{\text{old}} \cup \{c_{\text{new}}\}$):** $\text{TargetFare}_U \le \sum_{i \in U_{\text{old}}} \text{DynamicCap}_i + \text{Cap}_{c_{\text{new}}} \iff \Delta\text{PlanFare} \le \text{Cap}_{c_{\text{new}}}$.
4. **D4 (Khả thi cận dưới trên $U$):** $\text{TargetFare}_U \ge \sum_{i \in U_{\text{old}}} \text{Floor}_i + \text{Floor}_{c_{\text{new}}} \iff \Delta\text{PlanFare} \ge \text{Floor}_{c_{\text{new}}} - \sum_{i \in U_{\text{old}}}(\text{Fare\_exact}_{\text{old}}(i) - \text{Floor}_i)$.
5. **D5 (Kiểm tra sau phân bổ & làm tròn):** Sau khi tìm $\text{Fare\_exact}_{\text{new}}(m)$ và làm tròn xuống `1.000 đ` thành $\text{Fare\_charged}_{\text{new}}(m)$, mọi $i \in U_{\text{old}}$ có $\text{Fare\_charged}_{\text{new}}(i) \le \text{Fare\_charged}_{\text{old}}(i)$, và toàn kế hoạch thỏa mãn Cổng 1 (Mục 14.1) cùng Cổng 2A & 2B sau làm tròn (Mục 14.2).
6. **D6 (Ngân sách khách mới):** $\text{Unmatched}_{c_{\text{new}}} \le B_{\max}(c_{\text{new}})$.

### 2.4. Đồng bộ cơ sở tính Thu nhập/giờ của tài xế theo Khoản Payout thực tế sau làm tròn (`D-45a` / `D-51` — `ACCEPTED`)
- Trên toàn bộ tài liệu (Mục 14.2, 16.1, 17.2, 17.3, 36, 38, 71), khoản tiền tài xế thực nhận và tốc độ thu nhập theo giờ của kế hoạch ghép được tính **sau bước làm tròn `Fare_charged(i)`** (với `enforce_driver_hourly_rate_gate = true`, `driver_hourly_rate_tolerance_eps = 0.00`):
  $$\text{DriverPayout}(\text{Plan}) = (1 - c_{\text{pool}}) \times \sum_{i \in N} \text{Fare\_charged}(i) = 0,85 \times \sum_{i \in N} \text{Fare\_charged}(i)$$
  $$\text{DriverHourlyRate}(\text{Plan}) = \frac{\text{DriverPayout}(\text{Plan})}{T_{\text{plan}} / 60} \ge (1 - \varepsilon_{\text{hourly}}) \times \max_{i \in N} \left( \frac{(1 - c_{\text{private}}) \times \text{PrivateFare}(i)}{T_{\text{direct}}(i) / 60} \right)$$

---

## 3. BẢNG ĐẶC TẢ CHI TIẾT CÁC THAM SỐ BASELINE (`PARAMETER SPECIFICATION TABLES`)

### 3.1. Nhóm Không gian, Vùng phục vụ & Định tuyến (`spatial_and_service_areas`)

| Tham số (YAML Key) | Giá trị mặc định | Đơn vị | Miền hợp lệ (Valid Domain) | Phạm vi (Scope) | Trạng thái & Mã QĐ | Quy tắc thay đổi phiên bản |
|---|---:|---|---|---|---|---|
| `max_total_service_radius_km` | `150.0` | `km` | `[50.0, 300.0]` | MUST (M1) | `ACCEPTED` (D-20) | Đổi giá trị cần tăng `routing_version` / `scenario_version`. |
| `urban_boundary_buffer_km` | `15.0` | `km` | `[0.0, 25.0]` | MUST (M1) | `ACCEPTED` (D-20) | Đặt `= 0.0` nếu muốn quay về kiểm tra đa giác cứng; đổi giá trị cần ghi log `service_area_version`. |
| `osrm_table_max_candidates` | `20` | `plans` | `[5, 50]` | MUST (M2, M4) | `ACCEPTED` (P2-04) | Tham số hiệu năng runtime; không làm đổi `pricing_version`. |

### 3.2. Nhóm Dịch vụ Xe máy Nội đô (`bike_urban` — `BIKE_URBAN`)

| Tham số (YAML Key) | Giá trị mặc định | Đơn vị | Miền hợp lệ (Valid Domain) | Phạm vi (Scope) | Trạng thái & Mã QĐ | Quy tắc thay đổi phiên bản |
|---|---:|---|---|---|---|---|
| `base_vnd` | `10000` | `VND` | `>= 0`, bội số `1000` | MUST (M5) | `ACCEPTED` (D-35) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `per_km_vnd` | `4500` | `VND/km` | `[1000, 20000]` | MUST (M5) | `ACCEPTED` (D-35) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `per_min_vnd` | `250` | `VND/phút` | `[0, 5000]` | MUST (M5) | `ACCEPTED` (D-35) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `commission_rate` | `0.20` | `tỷ lệ` | `[0.05, 0.35]` (`20%` nhân `1000` nguyên) | MUST (M5) | `ACCEPTED` (D-35, D-48) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `rounding_step_vnd` | `1000` | `VND` | `{1000}` (khóa cố định làm tròn xuống) | MUST (M5) | `ACCEPTED` (D-18, D-48) | **Khóa bất biến** để đảm bảo số nguyên đồng trên Smart Contract. |
| `capacity` | `1` | `ghế` | `{1}` (khóa cố định 1:1) | MUST (M1, M3) | `ACCEPTED` (D-35) | **Khóa bất biến** trong phạm vi đề tài. |
| `now_pickup_window_min` | `[3, 15]` | `phút` | `0 < min < max <= 30` | MUST (M1) | `ACCEPTED` (D-07) | Tham số SLA điều phối. |
| `max_ahead_hours` | `12` | `giờ` | `[1, 24]` | MUST (M1) | `ACCEPTED` (D-07) | Luật thời gian đặt dịch vụ nội đô. |

### 3.3. Nhóm Dịch vụ Taxi Nội đô Bao xe & Ghép (`car_urban` — `CAR_URBAN_PRIVATE` & `CAR_URBAN_POOL`)

| Tham số (YAML Key) | Giá trị mặc định | Đơn vị | Miền hợp lệ (Valid Domain) | Phạm vi (Scope) | Trạng thái & Mã QĐ | Quy tắc thay đổi phiên bản |
|---|---:|---|---|---|---|---|
| `base_vnd` | `20000` | `VND` | `[10000, 50000]`, bội số `1000` | MUST (M5) | `ACCEPTED` (D-07) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `per_km_vnd` | `11000` | `VND/km` | `[5000, 25000]` | MUST (M5) | `ACCEPTED` (D-07) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `per_min_vnd` | `500` | `VND/phút` | `[0, 5000]` | MUST (M5) | `ACCEPTED` (D-07) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `extra_stop_fee_vnd` | `5000` | `VND/trạm` | `[0, 20000]`, bội số `1000` | MUST (M5) | `ACCEPTED` (D-16) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `stop_dwell_time_s` | `60` | `giây` | `[30, 180]` | MUST (M3, M4) | `ACCEPTED` (D-06) | Ảnh hưởng $T_{\text{plan}}$ trong thuật toán chèn điểm Mục 36. |
| `commission_private` | `0.20` | `tỷ lệ` | `[0.10, 0.30]` | MUST (M5) | `ACCEPTED` (D-12, D-51) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `commission_pool_total` | `0.15` | `tỷ lệ` | `== platform_net + fund_rate` | MUST (M5) | `ACCEPTED` (D-19, D-51) | Bắt buộc bằng tổng `platform_net_pool_rate + fund_contribution_rate`. |
| `platform_net_pool_rate` | `0.12` | `tỷ lệ` | `[0.05, 0.20]` | MUST (M5) | `ACCEPTED` (D-51) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `fund_contribution_rate` | `0.03` | `tỷ lệ` | `[0.01, 0.08]` | MUST (M5) | `ACCEPTED` (D-19, D-51) | Đổi giá trị cần tăng `pool_policy_version`. |
| `d_min` | `0.20` | `tỷ lệ` | `[0.10, 0.30]`, `< d_max` | MUST (M5) | `ACCEPTED` (D-16) | Cam kết giảm tối thiểu khi ghép; tăng `pricing_version` nếu đổi. |
| `d_max` | `0.60` | `tỷ lệ` | `[0.45, 0.70]`, `> d_min` | MUST (M5) | `ACCEPTED` (D-43 / O-01) | Đã phê duyệt khóa `= 0.60`; đổi giá trị cần tăng `pricing_version`. |
| `on_lower_bound_infeasible` | `"REJECT"` | `enum` | `{"REJECT", "CLAMP_TO_BASE"}` | MUST (M5) | `ACCEPTED` (D-43 / O-01) | Đã phê duyệt khóa `"REJECT"` để bảo đảm Gate `G06` (`Fare_exact >= Floor_i`) đạt 100%. |
| `allow_dynamic_insertion_after_partial_lock` | `true` | `boolean` | `{true, false}` | MUST (M4, M5) | `ACCEPTED` (D-44 / O-02) | Đã phê duyệt khóa `true` (Phương án A: đóng băng khách đã khóa & kiểm tra `D1–D6`). |
| `d_matched_typical` | `0.25` | `tỷ lệ` | `[d_min, d_max]` (`[0.20, 0.40]`) | MUST (M5, M9) | `ACCEPTED` (D-50) | Dùng tính `Fare_matched_est` khi xe rảnh chưa có khách thứ 2 (Mục 20.2). |
| `party_seat_surcharge_gamma` | `0.35` | `hệ số` | `[0.00, 0.50]` | MUST (M5) | `ACCEPTED` (D-45b / O-04) | Đã phê duyệt khóa `= 0.35`; chỉ tác động lên trọng số $w_i$ và `Floor_i` của booking 2 ghế. |
| `detour_weight_lambda` | `1.0` | `hệ số` | `[0.5, 2.0]` | MUST (M5) | `ACCEPTED` (D-17) | Trọng số bù bất tiện đi vòng ($\lambda = 1,0$). |
| `walk_weight_mu` | `2.0` | `hệ số` | `[1.0, 4.0]` | COULD (C9) | `ACCEPTED` (D-17, D-22) | Trọng số bù bất tiện đi bộ ($\mu = 2,0$ khi bật C9; bằng 0 khi đón tận nơi). |
| `unmatched_passenger_share_alpha` | `0.50` | `tỷ lệ` | `[0.30, 0.70]` | MUST (M5) | `ACCEPTED` (D-09) | Tỷ lệ khoảng chênh `Gap_i` khách chịu khi không ghép được ($\alpha = 0,50$). |
| `enforce_driver_hourly_rate_gate` | `true` | `boolean` | `{true, false}` | MUST (M4, M5) | `ACCEPTED` (D-45a / O-03) | Đã phê duyệt khóa `true` (bật Cổng 2B bảo toàn thu nhập/giờ thực nhận sau làm tròn). |
| `driver_hourly_rate_tolerance_eps` | `0.00` | `tỷ lệ` | `[0.00, 0.10]` | MUST (M4, M5) | `ACCEPTED` (D-45a / O-03) | Đã phê duyệt khóa `= 0.00` cho MVP; có thể thử `0.05` trong phân tích độ nhạy Simulator. |
| `rounding_step_vnd` | `1000` | `VND` | `{1000}` | MUST (M5) | `ACCEPTED` (D-18, D-51) | **Khóa bất biến** (làm tròn xuống `1.000 đ`). |
| `capacity` | `4` | `ghế` | `{4}` | MUST (M3) | `ACCEPTED` (D-04, D-07) | Sức chứa ghế hành khách của xe 4 chỗ. |
| `max_party_seats_pool` | `2` | `ghế` | `{1, 2}` | MUST (M1, M3) | `ACCEPTED` (D-07) | Tối đa 2 khách/booking khi đặt `CAR_URBAN_POOL`. |
| `pool_lock_remaining_km` | `3.0` | `km` | `[1.0, 5.0]` | MUST (M4, M6) | `ACCEPTED` (D-08) | Ngưỡng quãng đường còn lại kích hoạt `pool_lock_point`. |
| `k_max_stops` | `8` | `trạm` | `{4, 6, 8}` | MUST (M4) | `ACCEPTED` (D-06) | Số điểm dừng tối đa của một kế hoạch ghép nội đô. |

### 3.4. Nhóm Dịch vụ Liên tỉnh (`car_intercity_private` & `car_intercity_pool`)

| Tham số (YAML Key) | Giá trị mặc định | Đơn vị | Miền hợp lệ (Valid Domain) | Phạm vi (Scope) | Trạng thái & Mã QĐ | Quy tắc thay đổi phiên bản |
|---|---:|---|---|---|---|---|
| `car_intercity_private.base_vnd` | `150000` | `VND` | `[50000, 300000]`, bội số `1000` | MUST (M5, M8) | `ACCEPTED` (D-07) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `car_intercity_private.per_km_vnd` | `7500` | `VND/km` | `[4000, 15000]` | MUST (M5, M8) | `ACCEPTED` (D-07) | Bắt buộc tăng `pricing_version` khi thay đổi. |
| `car_intercity_private.commission_rate` | `0.15` | `tỷ lệ` | `[0.10, 0.25]` | MUST (M5, M8) | `ACCEPTED` (D-38, D-51) | Hoa hồng bao xe liên tỉnh (`15%`, tài xế nhận `85%`). |
| `car_intercity_private.now_pickup_window_min` | `[15, 45]` | `phút` | `5 <= min < max <= 90` | MUST (M8) | `ACCEPTED` (D-36) | Khung giờ đón khi đặt bao xe liên tỉnh đi ngay. |
| `car_intercity_private.now_search_radius_km` | `5.0` | `km` | `[2.0, 15.0]` | MUST (M8) | `ACCEPTED` (D-36) | Bán kính tìm tài xế liên tỉnh đang rảnh. |
| `car_intercity_private.max_ahead_days` | `7` | `ngày` | `{0, 3, 7}` | MUST (M8) | `ACCEPTED` (D-36) | Khóa `= 7 ngày` để đón khách từ chuyến ghép hủy tại `T−72h`. |
| `car_intercity_pool.commission_seat` | `0.10` | `tỷ lệ` | `[0.05, 0.20]` | MUST (M5, M7) | `ACCEPTED` (D-38) | Hoa hồng khi chạy ghép ghế chuẩn (`10%`, tài xế nhận `90%`). |
| `car_intercity_pool.commission_topup` | `0.15` | `tỷ lệ` | `== car_intercity_private.commission_rate` | SHOULD (S5) | `ACCEPTED` (D-51) | Khi chạy `CONFIRMED_TOPUP`, áp dụng hoa hồng bao xe `15%` (khớp bảng Mục 29). |
| `car_intercity_pool.min_seats_ref` | `3` | `ghế` | `{3}` (khóa cố định) | MUST (M5, M7) | `ACCEPTED` (D-38) | **Khóa bất biến `= 3`** khi tính `SeatReference` để chống thao túng giá. |
| `car_intercity_pool.allowed_driver_min_seats` | `[2, 3]` | `ghế` | Tập con của `{2, 3}` | MUST (M7) | `ACCEPTED` (D-38) | Không cho phép tài xế đặt `min_seats_to_run = 4`. |
| `car_intercity_pool.seat_price_band` | `[0.90, 1.10]` | `tỷ lệ` | `[0.80, 1.20]` | MUST (M5, M7) | `ACCEPTED` (D-38) | Biên độ giá ghế tài xế được phép đặt quanh `SeatReference`. |
| `car_intercity_pool.door_surcharge_per_km_vnd`| `4000` | `VND/km` | `[0, 10000]`, bội số `1000` | MUST (M5, M7) | `ACCEPTED` (D-50) | Phụ phí đón/trả ngoài vùng miễn phí theo khoảng cách OSRM tới biên zone. |
| `car_intercity_pool.max_corridor_deviation_km`| `10.0` | `km` | `[3.0, 20.0]` | MUST (M7) | `ACCEPTED` (D-50) | Khoảng cách tối đa từ điểm đón/trả tới biên vùng miễn phí của hành lang. |
| `car_intercity_pool.booking_open_days` | `7` | `ngày` | `{7}` | MUST (M1, M7) | `ACCEPTED` (D-37) | Mở đặt chỗ tối đa 7 ngày trước giờ khởi hành `T`. |
| `car_intercity_pool.booking_close_hours` | `72` | `giờ` | `{72}` | MUST (M1, M7) | `ACCEPTED` (D-37) | Đóng đặt chỗ chuẩn và chốt chuyến tại `T−72h` (3 ngày). |
| `car_intercity_pool.allow_post_confirm_late_booking` | `false` | `boolean` | `{false, true}` | MUST (M7) | `ACCEPTED` (O-08) | Đã phê duyệt khóa `= false` cho MVP (khớp Gate `G14`). |
| `car_intercity_pool.merge_confirmation_window_hours` | `2` | `giờ` | `[1, 4]` | SHOULD (S5) | `ACCEPTED` (D-39) | Cửa sổ `T−72h → T−70h` cho khách chuyến bị gộp hủy miễn phí. |
| `car_intercity_pool.topup_response_window_hours` | `6` | `giờ` | `[2, 8]` | SHOULD (S5) | `ACCEPTED` (D-39) | Thời gian khách phản hồi đề nghị góp thêm trước hạn `T−60h`. |
| `car_intercity_pool.driver_decision_deadline_hours`| `60` | `giờ` | `{60}` | MUST (M7) | `ACCEPTED` (D-39) | Hạn cuối `T−60h` tài xế chọn `RUN` hoặc `CANCEL` khi thiếu ghế. |
| `car_intercity_pool.pickup_order_fix_hours` | `24` | `giờ` | `{24}` | MUST (M7) | `ACCEPTED` (D-37) | Mốc `T−24h` duyệt hoán vị $4! = 24$ chốt thứ tự đón. |

### 3.5. Nhóm Đặt xe, Đồng thời, Ký quỹ Blockchain & Chính sách Phí hủy (`booking_and_concurrency` & `cancellation_policy`)

| Tham số (YAML Key) | Giá trị mặc định | Đơn vị | Miền hợp lệ (Valid Domain) | Phạm vi (Scope) | Trạng thái & Mã QĐ | Quy tắc thay đổi phiên bản |
|---|---:|---|---|---|---|---|
| `offer_timeout_s_urban` | `20` | `giây` | `[15, 45]` | MUST (M6) | `ACCEPTED` (D-47) | Thời gian chờ tài xế phản hồi mỗi bước offer nội đô. |
| `offer_timeout_s_intercity` | `60` | `giây` | `[30, 120]` | MUST (M6, M8) | `ACCEPTED` (D-47) | Thời gian chờ tài xế phản hồi mỗi bước offer bao xe liên tỉnh. |
| `per_offer_hold_buffer_s` | `15` | `giây` | `[10, 30]` | MUST (M6) | `ACCEPTED` (D-47) | `TTL_hold = offer_timeout_s + 15s` (`35s` nội đô / `75s` liên tỉnh) cấp mới cho từng bước offer. |
| `offer_cascade_max_attempts` | `3` | `lần` | `[1, 5]` | MUST (M6) | `ACCEPTED` (D-41, D-47) | Số ứng viên cùng dịch vụ tối đa được thử trong chuỗi Offer Cascade. |
| `idempotency_key_ttl_hours` | `24` | `giờ` | `[12, 72]` | MUST (M6) | `ACCEPTED` (D-25) | Thời gian lưu trữ khóa chống gọi trùng `Idempotency-Key`. |
| `require_escrow_deposited_before_start` | `true` | `boolean` | `{true, false}` | MUST (M12) | `ACCEPTED` (D-34, D-49 / O-06) | Đã phê duyệt khóa `true` (khớp Gate `G17` chặn `RIDE_STARTED` nếu chưa `DEPOSITED`). |
| `escrow_deposit_timeout_s` | `120` | `giây` | `[60, 300]` | MUST (M12) | `ACCEPTED` (D-49 / O-06) | Đã phê duyệt khóa `120s`; quá hạn từ lúc `CONFIRMED` chưa ký quỹ xong thì hủy tự động `ESCROW_TIMEOUT`. |
| `escrow_wallet_mode_must` | `"CUSTODIAL_HD_RELAYER"` | `enum` | `{"CUSTODIAL_HD_RELAYER", "METAMASK_DIRECT"}` | MUST (M12) | `ACCEPTED` (D-49 / O-06) | Đã phê duyệt dùng ví Testnet dẫn xuất từ `HD Wallet` ở mức MUST; mở thêm `METAMASK_DIRECT` ở mức COULD (C7). |
| `escrow_base_unit` | `"VND"` | `đơn vị` | `{"VND"}` (`1 Base Unit = 1 VND`) | MUST (M12) | `ACCEPTED` (D-48) | **Khóa bất biến** (`uint256` nguyên đồng Việt Nam trên Smart Contract). |
| `initial_guarantee_fund_seed_vnd` | `5000000` | `VND` | `>= 1000000` | MUST (M5, M12) | `ACCEPTED` (D-48) | Vốn mồi khởi tạo cho `fund_ledger` và `guaranteeFundBalance` on-chain. |
| `urban_free_cancel_grace_s` | `120` | `giây` | `[60, 300]` | MUST (M5) / SHOULD (S6) | `ACCEPTED` (D-52) | Thời gian hủy miễn phí sau khi `CONFIRMED` ở nội đô. |
| `urban_single_cancel_fee_rate` | `0.20` | `tỷ lệ` | `[0.10, 0.30]` (trần `20.000 VND`) | MUST (M5) / SHOULD (S6) | `ACCEPTED` (D-52) | Phí hủy muộn xe đơn nội đô (`min(20.000, 20% × Fare_charged)`). |
| `urban_pool_cancel_fee_rate_on_quote`| `0.20` | `tỷ lệ` | `[0.10, 0.30]` | MUST (M5) / SHOULD (S6) | `ACCEPTED` (D-52) | Phí hủy muộn Pool nội đô (`20% × Quote_i`). |
| `intercity_pool_cancel_fee_rate_72h_to_24h` | `0.50` | `tỷ lệ` | `[0.30, 0.70]` | MUST (M7) / SHOULD (S6) | `ACCEPTED` (D-52) | Phí hủy sau khi đã chốt chuyến `T−72h..T−24h` (`90%` phạt chuyển cho tài xế để giữ chuyến chạy). |
| `intercity_pool_cancel_fee_rate_after_24h` | `1.00` | `tỷ lệ` | `[0.80, 1.00]` | MUST (M7) / SHOULD (S6) | `ACCEPTED` (D-52) | Phí hủy sau khi đã chốt thứ tự đón `T−24h` hoặc `NO_SHOW`. |

### 3.6. Nhóm Tối ưu hóa mở rộng, AI/ML & Simulator (`batch_matching`, `meeting_points`, `simulator_and_evaluation`)

| Tham số (YAML Key) | Giá trị mặc định | Đơn vị | Miền hợp lệ (Valid Domain) | Phạm vi (Scope) | Trạng thái & Mã QĐ | Quy tắc thay đổi phiên bản |
|---|---:|---|---|---|---|---|
| `batch_matching.interval_s` | `30` | `giây` | `[15, 60]` | SHOULD (S4) | `ACCEPTED` (D-21) | Chu kỳ gom yêu cầu giải ghép theo lô trên đồ thị RTV rút gọn. |
| `batch_matching.max_new_requests_per_plan` | `2` | `requests` | `{1, 2}` | SHOULD (S4) | `ACCEPTED` (D-21) | Giữ kích thước đồ thị RTV nhỏ để giải chính xác trong `< 3 giây`. |
| `batch_matching.solver_time_limit_s` | `3.0` | `giây` | `[1.0, 5.0]` | SHOULD (S4) | `ACCEPTED` (D-21) | Quá hạn tự động chuyển sang fallback Tham lam (`Greedy`). |
| `batch_matching.unassigned_penalty_vnd` | `50000` | `VND` | `[20000, 100000]` | SHOULD (S4) | `ACCEPTED` (D-21) | Trọng số phạt $P_{\text{unassigned}}$ trong hàm mục tiêu CP-SAT. |
| `meeting_points.max_walk_m_range` | `[100, 400]` | `mét` | `[50, 500]` | COULD (C9) | `ACCEPTED` (D-22) | Tự động ép về `0` từ `22:00–05:00`, khi trời mưa hoặc có hành lý lớn. |
| `oof_cross_fitting_folds` | `5` | `folds` | `{5, 10}` | MUST (M11) | `ACCEPTED` (D-29) | Số fold huấn luyện Out-of-Fold cho `P(match)` và `P(fulfill)` trên tập Train. |
| `calibration_max_ece_threshold` | `0.05` | `ECE` | `[0.02, 0.10]` | SHOULD (S2, S3) | `NEEDS_VALIDATION` (D-27 / V-04) | Ngưỡng ECE tối đa trên tập Validation để bật nhân `p_hat_select × p_fulfill`. |
| `survey_group_kfold_splits` | `5` | `folds` | `{5}` | SHOULD (S1) | `NEEDS_VALIDATION` (D-30 / V-01) | Số fold đánh giá chéo theo `respondent_id` trên tập khảo sát người thật. |
| `closed_loop_seeds_count` | `20` | `seeds` | `[10, 30]` (`[1000..1019]`) | MUST (M10, M11)| `ACCEPTED` (Mục 75) | Số hạt giống ngẫu nhiên độc lập dùng cho kiểm định đóng vòng. |

---

## 4. KHỐI CẤU HÌNH YAML CHUẨN ĐÓNG BĂNG (`mvp_config_baseline_v1.yaml`)

```yaml
config_baseline_version: "MVP_CONFIG_BASELINE_V1"
config_status: "LOCKED_AND_APPROVED"
blueprint_revision: "Revision_9"
pricing_version: "price_v9_two_sided_bounded"
pool_policy_version: "guarantee_fund_v2_post_rounding_hourly_gate"

spatial_and_service_areas:
  max_total_service_radius_km: 150.0
  urban_boundary_buffer_km: 15.0

bike_urban:
  base_vnd: 10000
  per_km_vnd: 4500
  per_min_vnd: 250
  commission_rate: 0.20
  rounding_step_vnd: 1000
  capacity: 1
  now_pickup_window_min: [3, 15]
  max_ahead_hours: 12

car_urban:
  base_vnd: 20000
  per_km_vnd: 11000
  per_min_vnd: 500
  extra_stop_fee_vnd: 5000
  stop_dwell_time_s: 60
  commission_private: 0.20
  commission_pool_total: 0.15
  platform_net_pool_rate: 0.12
  fund_contribution_rate: 0.03
  d_min: 0.20
  d_max: 0.60                                       # [ACCEPTED: D-43 / O-01]
  on_lower_bound_infeasible: "REJECT"               # [ACCEPTED: D-43 / O-01]
  allow_dynamic_insertion_after_partial_lock: true  # [ACCEPTED: D-44 / O-02]
  d_matched_typical: 0.25
  party_seat_surcharge_gamma: 0.35                  # [ACCEPTED: D-45b / O-04] Applies to w_i & Floor_i only
  detour_weight_lambda: 1.0
  walk_weight_mu: 2.0
  unmatched_passenger_share_alpha: 0.50
  enforce_driver_hourly_rate_gate: true             # [ACCEPTED: D-45a / O-03] Computed on 0.85 * sum(Fare_charged)
  driver_hourly_rate_tolerance_eps: 0.00            # [ACCEPTED: D-45a / O-03]
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
  per_km_vnd: 7500
  commission_rate: 0.15
  rounding_step_vnd: 1000
  now_pickup_window_min: [15, 45]
  now_search_radius_km: 5.0
  max_ahead_days: 7

car_intercity_pool:
  commission_seat: 0.10
  commission_topup: 0.15
  min_seats_ref: 3
  allowed_driver_min_seats: [2, 3]
  default_min_seats_to_run: 3
  seat_price_band: [0.90, 1.10]
  door_surcharge_per_km_vnd: 4000
  max_corridor_deviation_km: 10.0
  rounding_step_vnd: 1000
  booking_open_days: 7
  booking_close_hours: 72
  allow_post_confirm_late_booking: false            # [ACCEPTED: O-08]
  merge_confirmation_window_hours: 2
  topup_response_window_hours: 6
  driver_decision_deadline_hours: 60
  pickup_order_fix_hours: 24
  merge_max_departure_gap_min: 60

booking_and_concurrency:
  offer_timeout_s_urban: 20
  offer_timeout_s_intercity: 60
  per_offer_hold_buffer_s: 15
  offer_cascade_max_attempts: 3
  idempotency_key_ttl_hours: 24
  require_escrow_deposited_before_start: true       # [ACCEPTED: D-34, D-49 / O-06]
  escrow_deposit_timeout_s: 120                     # [ACCEPTED: D-49 / O-06]
  escrow_wallet_mode_must: "CUSTODIAL_HD_RELAYER"   # [ACCEPTED: D-49 / O-06]
  escrow_auto_release_after_hours: 24
  escrow_base_unit: "VND"
  initial_guarantee_fund_seed_vnd: 5000000

cancellation_policy:                                # [ACCEPTED: D-52]
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

batch_matching:
  interval_s: 30
  max_new_requests_per_plan: 2
  solver: "ORTOOLS_CP_SAT_RTV"
  solver_time_limit_s: 3.0
  unassigned_penalty_vnd: 50000

meeting_points:
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
  calibration_max_ece_threshold: 0.05
  survey_group_kfold_splits: 5
```

---

## 5. QUY TẮC THAY ĐỔI PHIÊN BẢN VÀ CÔ LẬP SNAPSHOT (`VERSIONING & SNAPSHOT ISOLATION RULES`)

1. **Bất biến theo phiên bản trên CSDL (`Immutable Versioned Configs`):**
   - Bảng `pricing_configs (version, service_code, params_json, active_from)` không bao giờ cho phép lệnh `UPDATE` ghi đè lên một `version` đã từng phát sinh `ride_candidates` hoặc `bookings`.
   - Mọi thay đổi đối với các tham số giá, tỷ lệ hoa hồng, tỷ lệ trích Quỹ, hoặc ngưỡng `d_min`, `d_max`, `α`, `λ`, `μ`, `γ_seat` đều bắt buộc phải tạo một dòng cấu hình mới với mã `pricing_version` mới (ví dụ: `price_v9_1_...`).
2. **Cô lập phiên bản cho các chuyến đang mở (`In-Flight Ride Plan Isolation`):**
   - Mỗi `ride_plan` và mỗi `booking` lưu mã `pricing_version` tại thời điểm khởi tạo.
   - Khi một kế hoạch ghép `CAR_URBAN_POOL` đang ở trạng thái `PLAN_OPEN_SEARCHING` và chèn thêm khách mới $c_{\text{new}}$, phép phân bổ lại (Mục 15.5) bắt buộc sử dụng đúng bộ tham số của `ride_plan.pricing_version` để đảm bảo tính nhất quán của `PlanFare` và `TargetFare_U` từ đầu đến cuối chuyến xe.
3. **Truy vết thực nghiệm AI & Simulator (`Experiment Lineage Rule`):**
   - Không được gộp chung dữ liệu huấn luyện sinh từ hai `pricing_version` hoặc hai `scenario_version` khác nhau vào cùng một lần chạy đánh giá `H1–H11` nếu không có cột phân tầng phiên bản.

---

## 6. PHÂN LOẠI 3 NHÓM VẤN ĐỀ CÒN LẠI VÀ KẾT LUẬN TRẠNG THÁI SẴN SÀNG (`READINESS GATE VERDICT`)

### 6.1. Bảng phân loại 3 nhóm vấn đề sau khi Chủ dự án đã phê duyệt cấu hình Baseline v1

| Phân nhóm | Mã Issue / Quyết định | Nội dung & Trạng thái hiện tại | Giới hạn & Thời điểm thực hiện |
|---|---|---|---|
| **NHÓM A — Blocker phải xử lý trước khi code module Core (`Pre-Coding Blockers`)** | **0 Blocker tồn đọng** *(Đã giải quyết và phê duyệt 100%: `O-01..O-06, O-08, D-34, D-43..D-52` đều đã `ACCEPTED`)* | Toàn bộ 4 mâu thuẫn toán học (`F-01..F-04`) và toàn bộ 8 tham số cấu hình đề xuất của MVP đã được Chủ dự án phê duyệt chính thức và khóa trong Mục 4 (`mvp_config_baseline_v1.yaml`). | **ĐÃ ĐÓNG (`0 BLOCKERS`) — Sẵn sàng lập trình ngay từ Phase 0 đến Phase 8.** |
| **NHÓM B — Các vấn đề giải quyết trong giai đoạn Mô phỏng & Đánh giá AI (`[NEEDS_VALIDATION]`)** | **`V-01` (`D-30`)** *(Khảo sát lựa chọn S1 & Giả thuyết H4)* | Thu thập `100–200` mẫu khảo sát phân tầng (sinh viên + người đi làm), ước lượng MNL nạp vào Simulator và chạy `5-Fold GroupKFold CV` + Wilcoxon test. | Phát hành bảng hỏi ở **Phase 1**, phân tích dữ liệu ở **Phase 7–8**. *(Nếu khảo sát thu chậm, Simulator vẫn chạy được ngay bằng bộ phân phối mặc định ở Mục 48.1).* |
| **NHÓM B (tiếp)** | **`V-02` (`D-19`)** *(Điểm hòa vốn Quỹ bảo đảm `p*` & Cạnh tranh Xe máy)* | Đo lường `p_actual` so với `p*_booking = 62,8%` / `p*_ride = 45,8%` trên 3 mức mật độ `LOW / MEDIUM / HIGH` và kiểm chứng đòn bẩy `d_min` / Ghép theo lô CP-SAT (`H6`). | Giải quyết trong **Phase 7 → Phase 11** (Thực nghiệm đóng vòng trên Simulator). |
| **NHÓM B (tiếp)** | **`V-03`** *(Hiệu chỉnh tốc độ `osrm-motorbike`)* & **`V-04` (`D-27`)** *(Hiệu chỉnh xác suất `ECE <= 0.05`)* | Tinh chỉnh bảng tốc độ xe máy OSRM theo ~20 cặp điểm Hà Nội (`V-03`); kiểm định `ECE <= 0.05` trên tập Validation trước khi nhân `p_hat_select × p_fulfill` (`V-04`). | `V-03` tinh chỉnh ở **Phase 0–2**; `V-04` đánh giá ở **Phase 8**. |
| **NHÓM C — Các vấn đề bên ngoài cần xác nhận trước khi tích hợp hoặc vận hành thực tế (`[NEEDS_EXTERNAL_CONFIRMATION]`)** | **`EXT-01` (`O-07`)** *(Tên đề tài)*, **`EXT-02`** *(ABI hợp đồng thông minh hiện có)*, **`EXT-03`** *(Pháp lý vận tải khi thương mại hóa)* | - `EXT-01`: Xin giảng viên hướng dẫn xác nhận 1 trong 3 phương án tên đề tài (Mục 0.1).<br>- `EXT-02`: Đối chiếu mã nguồn `.sol` hiện có của nhóm với danh sách hàm Mục 80.2 trước Phase 9.<br>- `EXT-03`: Giữ tuyên bố nguyên mẫu nghiên cứu và định hướng Hợp đồng đồng thuê chuyến theo [Nghị định 158/2024/NĐ-CP](https://thuvienphapluat.vn/van-ban/Giao-thong-Van-tai/Nghi-dinh-158-2024-ND-CP-quy-dinh-hoat-dong-van-tai-duong-bo-636875.aspx). | `EXT-01` là thủ tục hành chính; `EXT-02` kiểm tra trước **Phase 9** (không ảnh hưởng Phase 0–8); `EXT-03` chỉ áp dụng nếu thương mại hóa sau đồ án. |

---

### 6.2. Kết luận Trạng thái Sẵn sàng Chính thức (`FINAL READINESS VERDICT`)

> ### TRẠNG THÁI KẾT LUẬN CHÍNH THỨC: **`READY FOR MVP IMPLEMENTATION`** *(ĐÃ SẴN SÀNG TRIỂN KHAI XÂY DỰNG HỆ THỐNG MVP)*

**Căn cứ khóa trạng thái `READY FOR MVP IMPLEMENTATION`:**
1. **Không còn bất kỳ mâu thuẫn nào ảnh hưởng đến quy tắc của MVP (`0 Open Blockers`):** Toàn bộ công thức định giá 5 dịch vụ, quy tắc booking 2 ghế (`party_seat_surcharge_gamma = 0.35`), điều kiện khả thi hai cận (`[Floor_i, EffectiveCap_i]`), hệ 6 điều kiện chèn khách động khi đã khóa giá (`D1–D6`), cơ sở tính thu nhập/giờ của tài xế sau làm tròn (`0,85 × Σ Fare_charged`), máy trạng thái trực giao 3 trục, `Per-Offer Seat Hold`, đơn vị tiền tệ `1 VND` trên Smart Contract và khung chính sách phí hủy đã được đồng bộ 100% và được Chủ dự án phê duyệt chính thức.
2. **Ranh giới các công việc thực nghiệm và xác nhận bên ngoài đã được khoanh vùng rõ ràng:** Các công việc thuộc giai đoạn thực nghiệm (`V-01..V-04` tại Phase 7–11) và xác nhận tích hợp hợp đồng thông minh (`EXT-02` tại Phase 9) đều chưa đến phase thực hiện và đã có cơ chế dự phòng/giao diện chuẩn, không cản trở việc bắt đầu xây dựng hệ thống theo lộ trình Phase 0 → Phase 11.
