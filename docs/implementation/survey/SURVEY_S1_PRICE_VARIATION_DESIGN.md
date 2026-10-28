# Khảo sát S1 — Ma trận thiết kế biến thiên giá / thời gian (SURVEY-06)

- **Trạng thái:** đề xuất — `EXPERIMENT_REVIEW_REQUIRED`, **không kích hoạt**. Bản nháp đang chạy (draft 3) chỉ dùng mức cơ sở.
- **Giá thí nghiệm ≠ giá ứng dụng:** mọi mức dưới đây là giá **giả định cho thí nghiệm lựa chọn**; không ghi vào `pricing_configs`, OSRM hay Baseline; thẻ khảo sát ghi rõ "giá trị giả định cho khảo sát".
- Kiểm tra tái lập: `python -I scripts/survey/identifiability_check.py` → `docs/implementation/survey/evidence/s1_identifiability.json`.

## 1. Vấn đề nhận dạng của thiết kế hiện tại

Mô hình logit có điều kiện chỉ nhận dạng hệ số từ **chênh lệch giữa các phương án trong cùng một câu**. Trong thiết kế đang chạy, giá và thời gian của mọi phương án chỉ đổi theo quãng đường (6 km / 14 km), nên các cột chênh lệch phụ thuộc tuyến tính.

| Thiết kế | Biến thiên | Hạng / 9 cột | VIF lớn nhất | corr(giá, thời gian) | Nhận dạng được? | Khả thi theo Baseline |
|---|---|---|---|---|---|---|
| **A — đang chạy** | chỉ quãng đường | **7** | không tính được (suy biến) | 0,892 | **KHÔNG** | có |
| B | + d ghép {0,20; 0,25; 0,35}, giá bao xe / xe máy ×{0,90; 1,00; 1,10} | 9 | 40,1 | 0,833 | yếu (VIF > 10) | có |
| C | B + một hệ số thời gian chung ×{0,85; 1,00; 1,15} | 9 | 14,7 | 0,826 | yếu (VIF > 10) | có |
| **D — đề xuất** | B + hệ số thời gian **riêng từng phương tiện** ×{0,80; 1,00; 1,20} | 9 | **5,3** | 0,497 | **CÓ** (VIF < 10) | có |

9 cột: hằng số riêng xe máy, hằng số riêng taxi ghép, giá (nghìn đ), thời gian (phút), thời gian đi vòng thêm (phút), chênh "tối đa nếu không ghép − dự kiến" (nghìn đ), khả năng ghép Trung bình, Thấp, đi bộ 200 m. 6 khối × 8 câu × 2 dòng chênh lệch (so với taxi bao xe).

**Kết luận:** với thiết kế A, hệ số giá và hệ số thời gian (giá trị thời gian) **không ước lượng tách bạch được** → không đủ điều kiện phát hành để kiểm định giả thuyết về giá. Cần Chủ dự án duyệt một ma trận biến thiên (đề xuất D) trước khi phát hành.

## 2. Ma trận đề xuất D (chưa kích hoạt)

Mức của mỗi yếu tố được xoay độc lập với quãng đường theo khối (`level = (i + a·k + b) mod 3`, khác hệ số cho từng yếu tố).

| Yếu tố | Mức | Ví dụ 14 km | Ví dụ 6 km | Ràng buộc kiểm tra |
|---|---|---|---|---|
| Mức giảm ghép `d` | 0,20 / 0,25 / 0,35 | 155.000 / 145.000 / 126.000 đ (P = 194.000) | 76.000 / 71.000 / 61.000 đ (P = 95.000) | `d_min 0,20 ≤ d ≤ d_max 0,60` |
| Giá taxi bao xe | ×0,90 / ×1,00 / ×1,10 | 174.000 / 194.000 / 213.000 đ | 85.000 / 95.000 / 104.000 đ | giá ghép, trần, tối đa nếu không ghép **tính lại từ giá bao xe hiển thị** |
| Giá xe máy | ×0,90 / ×1,00 / ×1,10 | 72.000 / 81.000 / 89.000 đ | 36.000 / 41.000 / 45.000 đ | — |
| Thời gian ô tô (kèm đi vòng) | ×0,80 / ×1,00 / ×1,20 | 32 / 40 / 48 phút | 15 / 19 / 23 phút | — |
| Thời gian xe máy | ×0,80 / ×1,00 / ×1,20 | 28 / 35 / 42 phút | 13 / 16 / 19 phút | — |

Kiểm tra khả thi kinh tế cho **mọi** tổ hợp (48 tổ hợp = 6 khối × 8 câu): `floor(0,40 P) ≤ giá ghép dự kiến ≤ Quote = floor(0,80 P) < Unmatched = floor(Quote + 0,5 (P − Quote)) < P` — **đạt 48/48**. Không mức nào vượt cận của Baseline (`d_min`, `d_max`, `unmatched_passenger_share_alpha`).

## 3. Trạng thái hiện thực (2026-10-28)

- Thiết kế D **đã hiện thực** trong bộ sinh thiết kế thật (`backend/app/modules/ml_models/survey_design.py`), điều khiển bằng
  `part_1a.variation_design.active` trong `survey/s1/questionnaire.draft.yaml` — hiện **`false`** (không người trả lời nào thấy mức ≠ cơ sở).
- Mọi giá trên thẻ khi bật được tính lại bằng quy tắc khóa: giá ghép dự kiến `floor((1 − d) P)`, trần cam kết `floor(0,80 P)`,
  tối đa nếu không ghép `floor(Quote + 0,5 (P − Quote))`, với P là giá bao xe hiển thị; mức vi phạm cận Baseline → lỗi, không hiển thị.
- Kiểm tra nhận dạng trên **thiết kế do bộ sinh thật tạo ra** (6 khối × 8 câu):

| Bộ sinh | Hạng | VIF lớn nhất | corr(giá, thời gian) | Nhận dạng | Khả thi |
|---|---|---|---|---|---|
| tắt (đang chạy) | 7/9 | suy biến | 0,892 | KHÔNG | 48/48 |
| bật thiết kế D | 9/9 | 5,3 | 0,497 | CÓ | 48/48 |

- Test: `test_variation_design_is_off_and_valid_when_switched_on` (tắt theo mặc định; khi bật, mọi thẻ đúng cận Baseline, 3 mức giá bao xe trong mỗi quãng đường).

## 4. Chờ Chủ dự án

Một quyết định: **duyệt (hoặc sửa) ma trận D**. Khi duyệt: đặt `active: true`, đổi `approval_status`, nâng `draft_version`, chạy lại
`python -I scripts/survey/identifiability_check.py` và bộ test — không cần thay mã.

## 5. Kiểm định ma trận D theo OWNER APPROVAL §4 (2026-10-28)

Ma trận D được duyệt **chỉ để pilot trên dữ liệu TEST**; thu thập nghiên cứu vẫn đóng. Công cụ: `scripts/survey/design_diagnostics.py` (→ `evidence/s1_design_diagnostics.json`), `backend/app/modules/ml_models/survey_stats.py`, pilot `backend/tests/test_survey_pilot.py` (→ `evidence/s1_pilot_*.json`).

**Đặc tả MNL dùng để kiểm định** (logit có điều kiện, gốc = taxi bao xe, giá theo nghìn đ, thời gian theo phút): `ASC_bike, ASC_pool, price, time, detour (ghép), unmatched − expected (ghép), likelihood MEDIUM / LOW (ghép, gốc HIGH), walk_200 (ghép), rain × ASC_bike, urgent × time` — 11 tham số. Thời gian của taxi ghép = thời gian xe bao (cùng lộ trình); phần thêm là thuộc tính đi vòng. Trần cam kết `Quote = floor(0,80 P)` là hàm xác định của giá bao xe nên không có hệ số riêng.

| # | Yêu cầu | Kết quả |
|---|---|---|
| 1 | "5,3" là chỉ số gì | **VIF lớn nhất** của các cột thuộc tính trong ma trận chênh lệch (so với taxi bao xe), đặc tả 9 cột cũ. **Không phải** condition number. Với đặc tả đầy đủ 11 cột: VIF lớn nhất **5,42** (detour) |
| 2 | Hạng trên đúng ma trận thiết kế MNL | Tắt biến thiên: **9/11** (không nhận dạng). D: **11/11** |
| 3 | VIF, condition number, D-error | D: VIF ≤ 5,42; condition number của ma trận thông tin chuẩn hóa 151 (β = 0) / 241 (β giả định) → chỉ số điều kiện √κ ≈ 12 / 16; D0-error 1,34; Dp-error 4,68 (β giả định — **là giả định minh họa, không phải ước lượng**) |
| 4 | Tương quan giá – thời gian – phương tiện – quãng đường | Mức phương án: giá~thời gian 0,74; giá~quãng đường 0,68; thời gian~quãng đường 0,88; giá~xe máy −0,59. Trong cùng phương tiện vẫn cao (giá~quãng đường 0,95–0,97; giá~thời gian 0,87–0,90) vì 6 km / 14 km lấn át biến thiên ±10–20%. Trong ma trận chênh lệch (cái MNL dùng): VIF giá 1,85, thời gian 1,98 |
| 5 | Cân bằng mức | d, giá bao xe, giá xe máy, thời gian ô tô: 8/8/8 mỗi quãng đường. **`bike_time_mult` lệch** (14 km: 9/9/6; 6 km: 6/9/9) — lỗi xoay vòng |
| 6 | Phương án bị thống trị / quá hiển nhiên / giá trị phi thực tế | Không có thống trị tuyệt đối giữa hai xe ô tô (ghép luôn rẻ hơn, kể cả giá tối đa; bao xe không đi vòng, chắc chắn). Xe máy rẻ hơn và không chậm hơn bao xe ở **33/48** câu (khác biệt còn lại là thoải mái / thời tiết, không phải thống trị tuyệt đối); **18/48** câu có một phương án > 90% xác suất theo β giả định. Tốc độ ngầm 15,7–30 km/h — hợp lý |
| 7 | Pilot nội bộ dữ liệu TEST | 150 người (75/75) qua API thật → DB TEST → export CSV → ước lượng: hội tụ, mọi tham số nằm trong 3,5 SE của giá trị đúng (không lệch chuỗi). **Giá ước lượng tốt (t ≈ −5,8 … −7)**; **thời gian không ổn định** (SE 0,023 so với hệ số giả định 0,025; t dao động −1,8 / −2,7 giữa hai lần mô phỏng); đi vòng, chênh "tối đa nếu không ghép", đi bộ không ước lượng được |
| 8 | 48 tổ hợp, không ghi vào `pricing_configs` | 48/48 trong cận Baseline; pilot so sánh số dòng + `md5(params_json)` của `pricing_configs` trước/sau: không đổi; RESEARCH export rỗng |
| 9 | d 0,20 / 0,25 / 0,35 nhất quán với ngữ cảnh, Quote, Unmatched | 48/48 thẻ: dự kiến = `floor((1 − d) P)`, trần = `floor(0,80 P)`, tối đa = `floor(Quote + 0,5 (P − Quote))` với P là giá bao xe hiển thị |

**Kết luận:** D đạt hạng đầy đủ nhưng **chưa đủ** về thống kê — mức thời gian lệch, và với N = 150 hệ số thời gian (giá trị thời gian) có |t| kỳ vọng chỉ **1,1**. Không kết luận "đạt" chỉ vì hạng 11/11.

### Đề xuất điều chỉnh D2 (chưa kích hoạt — `variation_design_proposals.D2`)

Thay đổi so với D: thời gian ô tô ×0,70 / 1,00 / 1,30; thời gian xe máy ×0,70 / 1,00 / 1,30 với xoay vòng cân bằng; thời gian đi vòng có mức riêng ×0,50 / 1,00 / 1,50 (không còn gắn với thời gian ô tô). Giữ nguyên d và giá ±10%. Đặc tả MNL chính đề xuất: bỏ `urgent × time` (giữ khẩn cấp qua phân tích phụ).

| | D (đã duyệt pilot) | D2 (đề xuất) |
|---|---|---|
| Hạng / VIF lớn nhất | 11/11 / 5,42 | 11/11 / 6,28 |
| Condition number (β = 0 / giả định) | 151 / 241 | **98 / 115** |
| D0-error / Dp-error | 1,34 / 4,68 | **1,00 / 3,47** |
| Cân bằng mức | lệch thời gian xe máy | **8/8/8 mọi yếu tố** |
| Xe máy rẻ hơn và không chậm hơn | 33/48 | **16/48** |
| |t| kỳ vọng N = 150 (đặc tả gọn): giá / thời gian / đi vòng | 6,6 / 1,4 / 0,5 | **7,5 / 2,7 / 0,7** |
| Pilot (1 lần mô phỏng): SE thời gian | 0,0227 | **0,0136** |
| Tốc độ ngầm | 15,7–30 km/h | 14,4–35 km/h |

Hạn chế còn lại kể cả với D2: hệ số đi vòng, chênh giá tối đa, đi bộ 200 m có |t| kỳ vọng < 1 với N = 150 nếu tác động thật nhỏ như giả định → nên công bố là phân tích **thăm dò**; muốn kiểm định chúng cần N lớn hơn (N = 300: thời gian 3,8, đi vòng 1,0) hoặc thêm câu hỏi. Các β dùng ở đây là **giả định minh họa** — pilot với người thật (dữ liệu TEST) sẽ cho β thực để tính lại trước khi phát hành.

**Cần Chủ dự án:** chọn D (giữ) hoặc D2 cho pilot tiếp theo, và chốt đặc tả MNL chính. Không mở thu thập dữ liệu thật.
