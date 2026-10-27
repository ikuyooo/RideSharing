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

## 3. Chờ Chủ dự án

1. Duyệt (hoặc sửa) ma trận D — đến khi duyệt, các mức ≠ cơ sở giữ `EXPERIMENT_REVIEW_REQUIRED` / `NOT_ACTIVE_PROPOSAL`.
2. Sau khi duyệt: hiện thực xoay mức trong `survey_design.py`, chạy lại kiểm tra nhận dạng trên thiết kế sinh thật, nâng `draft_version`.
