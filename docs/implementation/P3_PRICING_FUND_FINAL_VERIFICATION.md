# KIỂM CHỨNG TOÁN HỌC VÀ BẤT BIẾN TÀI CHÍNH PHASE 3
## (P3_PRICING_FUND_FINAL_VERIFICATION)

- **Dự án:** Ride_Sharing
- **Phạm vi thẩm định:** Toàn bộ thuật toán định giá, phân bổ chi phí hai phía, khung chặn giá, báo giá ghép, phí hủy và sổ cái Quỹ bảo đảm.
- **Tiêu chuẩn đối chiếu:** Đặc tả Revision 9 (Mục 10–20, 25–29, 38, 70–72, Phụ lục B) và file cấu hình gốc `config/mvp_config_baseline_v1.yaml`.
- **Mã nguồn thẩm tra:** `backend/app/modules/pricing/` và `backend/app/modules/fund/`.

---

## 1. Đối Chiếu Tham Số Định Giá Cốt Lõi Từ `config/mvp_config_baseline_v1.yaml`

| Tham số Baseline | Khóa Cấu hình YAML | Giá trị Xác Thực Thực Tế | Vị trí Sử dụng Trong Mã Nguồn |
|---|---|---|---|
| Chiết khấu ghép tối thiểu | `car_urban.d_min` | **0.20** ($20\%$) | `pool.py:cap`, `pool.py:gate1`, `tariff.py:pool_quote_for` |
| Chiết khấu ghép tối đa | `car_urban.d_max` | **0.60** ($60\% \Rightarrow 1 - d_{\max} = 0.40$) | `pool.py:raw_floor` |
| Phụ phí khách đi 2 ghế | `car_urban.party_seat_surcharge_gamma` | **0.35** ($\gamma_{\text{seat}} = 0.35$) | `pool.py:seat_factor` |
| Hệ số ghế cho 1 người | $\text{SeatFactor}(1) = 1 + \gamma \times (1 - 1)$ | **1.00** | `pool.py:seat_factor` |
| Hệ số ghế cho 2 người | $\text{SeatFactor}(2) = 1 + \gamma \times (2 - 1)$ | **1.35** | `pool.py:seat_factor` |
| Cước cơ sở xe hơi đô thị | `car_urban.base_vnd` | **20.000 VNĐ** | `pool.py:raw_floor`, `pool.py:plan_fare` |
| Bước làm tròn tiền tệ | `car_urban.rounding_step_vnd` | **1.000 VNĐ** | `tariff.py:floor_step`, `pool.py:_charged` |
| Dung sai thu nhập theo giờ Gate 2B | `car_urban.driver_hourly_rate_tolerance_eps` | **0.00** ($\varepsilon_{\text{hourly}} = 0$) | `pool.py:gate2` |
| Ngưỡng khoảng cách khóa giá | `booking_and_concurrency.pool_lock_remaining_km`| **3.0 km** (còn lại tới điểm trả) | Baseline YAML & Revision 9 §11 |

---

## 2. Kiểm Chứng Công Thức Định Giá & Phân Bổ Chi Phí Hai Phía

### 2.1. Gate 1 — Hiệu Quả Chi Phí Gộp
*Mã nguồn thực tế tại [backend/app/modules/pricing/pool.py:128-129](file:///C:/RideSharing/backend/app/modules/pricing/pool.py#L128-L129):*
```python
def gate1(p: CarUrbanParams, fare: Fraction, privates: Iterable[int]) -> bool:
    return fare <= (1 - p.d_min) * sum(privates)
```
Với $d_{\min} = 0.20$: $\text{PlanFare} \le 0.80 \times \sum_{i} P_i$.

### 2.2. Trọng Số Phân Bổ Chi Phí Nhánh ($w_i$)
*Mã nguồn thực tế tại [backend/app/modules/pricing/pool.py:108-109](file:///C:/RideSharing/backend/app/modules/pricing/pool.py#L108-L109):*
```python
def weight(p: CarUrbanParams, r: PoolRider) -> Fraction:
    return r.private_fare * (1 + p.lam * r.detour + p.mu * r.walk_ratio) / seat_factor(p, r.seats)
```
*   `seat_factor(p, r.seats)` nằm ở **MẪU SỐ**.
*   Với $s=1$: $\text{seat\_factor} = 1.00$.
*   Với $s=2$: $\text{seat\_factor} = 1 + 0.35 \times 1 = 1.35$.

### 2.3. Khung Chặn Biên Floor và Cap
*Mã nguồn thực tế tại [backend/app/modules/pricing/pool.py:112-117, 210](file:///C:/RideSharing/backend/app/modules/pricing/pool.py#L112-L117):*
```python
def cap(p: CarUrbanParams, r: PoolRider) -> Fraction:
    return r.private_fare * (1 - p.d_min)

def raw_floor(p: CarUrbanParams, r: PoolRider) -> Fraction:
    return max(Fraction(p.base_vnd), r.private_fare * (1 - p.d_max) * seat_factor(p, r.seats))
```
Và kẹp biên tại dòng 210:
```python
floor = {r.ref: min(caps[r.ref], raw_floor(p, r)) for r in riders}
```
**Công thức toán học đầy đủ:**
$$\text{Cap}_i = (1 - d_{\min}) \times P_i = 0.80 \times P_i$$
$$\text{raw\_floor}_i = \max\left(\text{BASE}, P_i \times (1 - d_{\max}) \times \text{SeatFactor}(s_i)\right)$$
$$\text{Floor}_i = \min\left(\text{Cap}_i, \text{raw\_floor}_i\right)$$
*Chú ý quan trọng:* Vì $d_{\max} = 0.60$, hệ số nhân là $1 - d_{\max} = 1 - 0.60 = \mathbf{0.40}$ (không phải $0.60$).

---

## 3. Kiểm Chứng 5 Vector Điển Hình Với Số Liệu Thực Tế

```text
====================================================================================================
Vector 1: 1 khách, 1 ghế (Vector chuẩn §71.1 #1 - tests/test_pricing_regression.py:27)
P = 194.000 đ, s = 1 -> SeatFactor(1) = 1.00
- Cap = 194.000 * (1 - 0.20) = 155.200 đ
- raw_floor = max(20.000, 194.000 * 0.40 * 1.0) = max(20.000, 77.600) = 77.600 đ
- Floor = min(155.200, 77.600) = 77.600 đ  (Khớp 100% dòng 27: assert A.floor == 77600)
- Fare_exact = 143.304,26 đ -> Fare_charged (làm tròn xuống 1.000đ) = 143.000 đ
====================================================================================================
Vector 2: Nhóm 2 ghế (Vector chuẩn §71.1 #3C - tests/test_pricing_regression.py:48)
P = 194.000 đ, s = 2 -> SeatFactor(2) = 1 + 0.35 * 1 = 1.35
- Cap = 194.000 * 0.80 = 155.200 đ
- raw_floor = max(20.000, 194.000 * 0.40 * 1.35) = max(20.000, 104.760) = 104.760 đ
- Floor = min(155.200, 104.760) = 104.760 đ  (Khớp 100% dòng 48: assert A.floor == 104760)
- Fare_exact = 148.895,75 đ -> Fare_charged = 148.000 đ (khách 2 ghế trả nhiều hơn 1 ghế)
====================================================================================================
Vector 3: Giá sàn cơ sở chi phối (Chặng ngắn P = 25.000 đ, s = 1)
- Cap = 25.000 * 0.80 = 20.000 đ
- raw_floor = max(20.000, 25.000 * 0.40 * 1.0) = max(20.000, 10.000) = 20.000 đ
- Floor = min(20.000, 20.000) = 20.000 đ (Sàn bằng trần do giá BASE 20.000đ chi phối)
====================================================================================================
Vector 4: Floor vượt Cap (Chặng cực ngắn P = 22.000 đ, s = 1)
- Cap = 22.000 * 0.80 = 17.600 đ
- raw_floor = max(20.000, 22.000 * 0.40 * 1.0) = max(20.000, 8.800) = 20.000 đ
- Floor_used = min(17.600, 20.000) = 17.600 đ (Kẹp tự động về Cap, bảo đảm bài toán luôn khả thi)
====================================================================================================
Vector 5: Chèn động khi khách B đã khóa giá (§71.1 #4)
- Khách B đã khóa: FinalPrice = 105.000 đ (Đóng băng tuyệt đối, D-44 / G08)
- Chèn thêm khách C vào nhóm mở U = {A, C}:
  Target_U = PlanFare_new - 105.000 đ = 288.000 - 105.000 = 183.000 đ
  EffectiveCap của A = min(Cap_A, Fare_exact_old_A) = 143.304,26 đ
- Kết quả: Giá A giảm từ 143.000 đ -> 135.000 đ; C trả 48.000 đ; B giữ nguyên 105.000 đ.
====================================================================================================
```

---

## 4. Kiểm Chứng Báo Giá Ghép Trước (`pool_quote_for`)

*Mã nguồn thực tế tại [backend/app/modules/pricing/tariff.py:69-72](file:///C:/RideSharing/backend/app/modules/pricing/tariff.py#L69-L72):*
```python
def pool_quote_for(p: CarUrbanParams, private: int) -> PoolQuote:
    quote = floor_step(private * (1 - p.d_min), p.step)
    gap = private - quote
    return PoolQuote(private_fare=private, quote=quote, gap=gap, unmatched=floor_step(quote + p.alpha * gap, p.step))
```
- Khi $P_i = 194.000$ VNĐ, $\alpha = 0.50$, $d_{\min} = 0.20$:
  $$\text{Quote} = \lfloor 194.000 \times 0.80 \rfloor = 155.000 \text{ VNĐ}$$
  $$\text{Gap} = 194.000 - 155.000 = 39.000 \text{ VNĐ}$$
  $$\text{Unmatched} = \lfloor 155.000 + 0.50 \times 39.000 \rfloor = 174.000 \text{ VNĐ}$$
- Vì $174.000 < 194.000$, bất biến D-10 bảo toàn 100% (hành khách luôn được giảm giá so với đi riêng ngay cả khi không ghép được bạn đi cùng).

---

## 5. Bảng Chuẩn Hóa Toàn Diện Chính Sách Phí Hủy & Vắng Mặt (D-52)

Đối soát trực tiếp từ mã nguồn thực thi [backend/app/modules/pricing/cancellation.py:86-140](file:///C:/RideSharing/backend/app/modules/pricing/cancellation.py#L86-L140) và cấu hình gốc `config/mvp_config_baseline_v1.yaml` (dòng 40–50):

| Dịch vụ | Ngữ cảnh Hủy / Vắng mặt | Công thức Phí Hủy (`Fee`) | Tỷ lệ Tài xế (`to_driver`) | Tỷ lệ Nền tảng (`to_platform`) | Tỷ lệ Quỹ (`to_fund`) | Test Case Kiểm Chứng |
|---|---|---|---|---|---|---|
| **Mọi dịch vụ** | Hủy bởi Tài xế hoặc Hệ thống (`DRIVER` / `SYSTEM`) | **0 VNĐ** (Hoàn tiền 100%) | 0% | 0% | 0% | `test_driver_or_system_cancellation_is_free_everywhere` |
| **`BIKE_URBAN`** | Hủy sớm ($\le 120$s sau CONFIRMED, tài xế chưa đến, hoặc HELD) | **0 VNĐ** (Miễn phí) | 0% | 0% | 0% | `test_urban_single[BIKE_URBAN]` |
| **`BIKE_URBAN`** | Hủy muộn ($> 120$s / tài xế đã đến) hoặc `NO_SHOW` (tài xế chờ $\ge 5$p) | $\min(20.000, 20\% \times \text{Fare})$ | **80%** ($1 - c_{\text{bike}}$) | **20%** | **0%** | `test_bike_fee_is_below_the_cap_and_private_fee_is_capped` |
| **`CAR_URBAN_PRIVATE`** | Hủy sớm ($\le 120$s sau CONFIRMED, tài xế chưa đến, hoặc HELD) | **0 VNĐ** (Miễn phí) | 0% | 0% | 0% | `test_urban_single[CAR_URBAN_PRIVATE]` |
| **`CAR_URBAN_PRIVATE`** | Hủy muộn ($> 120$s / tài xế đã đến) hoặc `NO_SHOW` (chờ $\ge 5$p) | $\min(20.000, 20\% \times \text{Fare})$ | **85%** ($1 - c_{\text{priv}}$) | **15%** | **0%** | `test_bike_fee_is_below_the_cap_and_private_fee_is_capped` |
| **`CAR_URBAN_POOL`** | Hủy sớm ($\le 120$s sau CONFIRMED, tài xế chưa đến, hoặc HELD) | **0 VNĐ** (Miễn phí — SF-P3-06) | 0% | 0% | 0% | `test_urban_pool` |
| **`CAR_URBAN_POOL`** | Hủy muộn / `NO_SHOW` khi **xe chưa có khách khác** trên xe | $20\% \times \text{Quote}_i$ | **85%** ($1 - c_{\text{pool}}$) | **0%** | **15%** (Nộp Quỹ) | `test_urban_pool` |
| **`CAR_URBAN_POOL`** | Hủy muộn / `NO_SHOW` khi **xe đang có khách khác** trên xe | $20\% \times \text{Quote}_i$ | **50%** (R9 §18.7) | **0%** | **50%** (Nộp Quỹ) | `test_urban_pool` |
| **`CAR_INTERCITY_PRIVATE`**| Hủy sớm (Đặt trước $> 2$h; Đi ngay $\le 120$s; hoặc HELD) | **0 VNĐ** (Miễn phí) | 0% | 0% | 0% | `test_intercity_private` |
| **`CAR_INTERCITY_PRIVATE`**| Hủy muộn ($\le 2$h trước đón) hoặc `NO_SHOW` | $20\% \times \text{PrivateFare}$ | **85%** ($1 - c_{\text{ic\_priv}}$)| **15%** | **0%** | `test_intercity_private` |
| **`CAR_INTERCITY_POOL`** | Hủy sớm ($> 72$h trước giờ khởi hành $T$, hoặc trong merge window)| **0 VNĐ** (Miễn phí) | 0% | 0% | 0% | `test_intercity_pool_windows` |
| **`CAR_INTERCITY_POOL`** | Hủy từ $24$h đến $72$h trước khởi hành ($24\text{h} \le t \le 72\text{h}$) | $50\% \times \text{BookingPrice}$ | **90%** ($1 - c_{\text{seat}}$) | **10%** | **0%** | `test_intercity_pool_windows` |
| **`CAR_INTERCITY_POOL`** | Hủy sát giờ ($< 24$h trước khởi hành) hoặc `NO_SHOW` | $100\% \times \text{BookingPrice}$ | **90%** ($1 - c_{\text{seat}}$) | **10%** | **0%** | `test_intercity_pool_windows` |

### Phân tích tài chính quan trọng:
1. **Phần chia vào Quỹ bảo đảm:** Duy nhất dịch vụ `CAR_URBAN_POOL` chuyển phần phí phạt không thuộc về tài xế vào **Quỹ bảo đảm (`to_fund`)** để bù đắp rủi ro cho kế hoạch ghép xe. Tất cả các dịch vụ khác chuyển phần này vào **Doanh thu nền tảng (`to_platform`)**.
2. **Xe đang có khách khác:** Khi xe ghép đang chở người khác mà một khách hủy, tài xế nhận $50\%$ cước phạt và Quỹ bảo đảm nhận $50\%$ (khớp nguyên văn bảng §18.7 và hằng số `POOL_SHARED_DRIVER_SHARE` trong code).
3. **Hiệu chỉnh số liệu lịch sử:** Các tài liệu kiểm toán cũ ghi nhận sai mức phí phạt đô thị là 30% và trần 50.000đ. Thực tế cấu hình đã khóa trong `mvp_config_baseline_v1.yaml` (dòng 42-44) và mã nguồn thực thi xác lập chính xác là **20%** và trần **20.000 VNĐ**. 13/13 ca kiểm thử trong `test_pricing_cancellation.py` đã tái lập và xác minh hoàn hảo giá trị này.
