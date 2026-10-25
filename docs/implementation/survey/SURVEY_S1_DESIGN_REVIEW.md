# SURVEY_S1_DESIGN_REVIEW — Khảo sát S1 (bản trình duyệt)

- **Trạng thái:** `DRAFT — EXPERIMENT_VALUES_PENDING_APPROVAL`. **Chưa phát hành.** Không có link thu thập nào đang hoạt động.
- **Căn cứ:** Revision 9 Mục 65 (thiết kế), 65.1 (phân tầng), 65.3 (phân tích), 59.2 (ẩn danh), 16.1 / 10.4 / 20.1 / 20.2 / 25.2 / 28.2 (số liệu thẻ lựa chọn); quyết định P1-D5 (biểu mẫu web độc lập, không phụ thuộc Frontend Next.js).
- **File máy đọc được:** [`survey/s1/questionnaire.draft.yaml`](../../../survey/s1/questionnaire.draft.yaml) (mỗi giá trị có trường `source`), [`survey/s1/export_schema.md`](../../../survey/s1/export_schema.md).
- **Quy ước nguồn:** `R9:<mục>` = có trong Revision 9 / Baseline · `DERIVED:B` = tính theo phương pháp B ở mục 3 (phương pháp chờ duyệt) · `TBD` = chưa có nguồn, cần Chủ dự án cung cấp.

---

## 1. Toàn bộ câu hỏi

**Lời mở đầu (màn hình 1):** Mục đích nghiên cứu, thời gian ~4–5 phút, hoàn toàn ẩn danh (không thu họ tên, email, mã sinh viên, số điện thoại), có thể dừng bất cứ lúc nào. Nút "Đồng ý tham gia".

**Phần 3 — hỏi trước để gán nhóm phân tầng (R9:65.1):**
- D1. Bạn hiện là: ☐ Sinh viên ☐ Người đã đi làm *(R9:65.1, 65.2)*

**Phần 1A — 8 tình huống đa phương tiện nội đô** *(R9:65.2: 6–8 câu; thiết kế đề xuất 8 = 2×2×2)*
> "Bạn cần đi **{6 km | 14 km}** trong nội đô Hà Nội. Thời tiết: **{Nắng ráo | Mưa rào}**. Mục đích: **{Đi học/làm, cần đúng giờ | Thong thả}**. Bạn sẽ chọn phương án nào?"

Ba thẻ lựa chọn (bố cục theo màn hình K2, R9:20.1) — giá trị ở mục 2. Người trả lời chọn đúng 1 thẻ.

**Phần 1B — 2 tình huống liên tỉnh** *(R9:65.2)*
> "Bạn cần đi từ Hà Đông về TP Hưng Yên (~65 km) vào một ngày cụ thể. Bạn chọn:"
- (a) Đặt trước **Taxi ghép liên tỉnh** 3–5 ngày, giá ghế **{180.000 | 220.000} đ**, khả năng đủ khách để chạy: **{TBD}**
- (b) **Taxi bao xe liên tỉnh** đi ngay, chủ động, **637.000 đ**
- (c) Phương tiện khác / Không đi

**Phần 2 — Cảm nhận công bằng (H4)** *(R9:65.2, 16.1)*
> "Hai hành khách đi chung một xe, tổng chi phí chuyến **248.500 đ**. Khách A đi 14 km và phải đi vòng thêm 25% để đón/trả khách B; khách B đi 9 km, không phải đi vòng. Dưới đây là 3 cách chia tiền:"
- Cách X / Y / Z (thứ tự ngẫu nhiên, nhãn trung tính): A giảm **24,0%** – B giảm **24,0%**; A giảm **20,2%** – B giảm **29,5%**; A giảm **26,1%** – B giảm **20,9%**.
- Câu 2.1–2.3: "Cách {X/Y/Z} hợp lý/công bằng đến mức nào?" thang **1–5** *(R9:65.2)*.
- Câu 2.4: "Bạn sẵn sàng sử dụng cách nào nhất?" chọn 1 *(R9:65.2)*.

**Phần 3 — Nhân khẩu học tối thiểu (còn lại)** *(R9:65.2)*
- D2. Số lần đặt xe công nghệ mỗi tuần — các khoảng lựa chọn: **TBD**
- D3. Cự ly di chuyển phổ biến — các khoảng lựa chọn: **TBD**
- D4. Số lần đi liên tỉnh mỗi tháng — các khoảng lựa chọn: **TBD**

## 2. Thẻ lựa chọn và giá trị thuộc tính

### 2.1. Phần 1A — ngữ cảnh 14 km (toàn bộ từ Revision 9)
| Thẻ | Thuộc tính | Giá trị | Nguồn |
|---|---|---|---|
| Xe máy | Giá / thời gian | 81.000 đ / 35 phút | R9:10.4 |
| Taxi bao xe | Giá / thời gian | 194.000 đ / 40 phút | R9:10.4, 16.1 |
| Taxi ghép | Giá dự kiến khi ghép | ~143.000 đ *(phương án khác: 145.000 đ = `Fare_matched_est`, R9:20.2)* | R9:10.4, 16.1 |
| Taxi ghép | Giá tối đa nếu không ai ghép | 174.000 đ | R9:10.4, 18.4 |
| Taxi ghép | Thời gian đi vòng tối đa | +12 phút | R9:10.4 |
| Taxi ghép | Khả năng ghép | Cao / Trung bình / Thấp (xoay vòng, mục 4) | R9:65.2 |
| Taxi ghép | Quãng đi bộ | 0 m / 200 m (xoay vòng, mục 4) | R9:65.2 |

### 2.2. Phần 1A — ngữ cảnh 6 km (**Revision 9 không có số liệu**; tính theo phương pháp B, chờ duyệt)
| Thẻ | Thuộc tính | Giá trị đề xuất | Nguồn |
|---|---|---|---|
| Xe máy | Giá / thời gian | 40.000 đ / 15 phút | DERIVED:B |
| Taxi bao xe | Giá / thời gian | 94.000 đ / 17 phút | DERIVED:B |
| Taxi ghép | Giá dự kiến khi ghép | 70.000 đ (`Fare_matched_est`, `d_matched_typical` = 0,25) | DERIVED:B |
| Taxi ghép | Giá tối đa nếu không ai ghép | 84.000 đ (`Unmatched_i`, Baseline §2.1) | DERIVED:B |
| Taxi ghép | Thời gian đi vòng tối đa | +5 phút | DERIVED:B |

### 2.3. Phần 1B
| Thẻ | Thuộc tính | Giá trị | Nguồn |
|---|---|---|---|
| Taxi ghép liên tỉnh | Giá ghế | 180.000 đ / 220.000 đ | R9:28.2, 65.2 |
| Taxi ghép liên tỉnh | Đặt trước | 3–5 ngày | R9:65.2 |
| Taxi ghép liên tỉnh | Khả năng đủ khách | **TBD** (Revision 9 không nêu mức) | TBD |
| Taxi bao xe liên tỉnh | Giá | 637.000 đ | R9:25.2, 65.2 |

## 3. Phương pháp sinh giá trị

**3.1. Phương pháp B (đề xuất cho 6 km)** — giữ nguyên công thức giá của Baseline, thay quãng đường bằng 6 km, thời gian bằng **tỷ lệ thuận** với ví dụ 14 km của Revision 9 (ô tô 40/14 phút/km, xe máy 35/14 phút/km, đi vòng 12/14 phút/km):
- Xe máy: `floor((10.000 + 4.500×6 + 250×15) / 1.000)×1.000` = 40.000 đ
- Taxi bao xe `P`: `floor((20.000 + 11.000×6 + 500×17,14) / 1.000)×1.000` = 94.000 đ
- `Quote` = `floor(0,80×P)` = 75.000 đ · `Unmatched` = `floor(Quote + 0,5×(P − Quote))` = 84.000 đ · `Fare_matched_est` = `floor(0,75×P)` = 70.000 đ
- **Kiểm chứng phương pháp:** áp đúng công thức này cho đầu vào 14 km của Revision 9 cho ra 81.000 / 194.000 / 155.000 / 174.000 / 145.000 đ — **trùng khớp 100%** với các con số đã công bố (lệnh kiểm tra đã chạy trong phiên làm việc P1).

**3.2. Phương án thay thế A** — lấy quãng đường/thời gian từ OSRM cho một cặp điểm 6 km thực tế. **Không khuyến nghị lúc này:** OSRM là tốc độ dòng tự do, bảng tốc độ xe máy đang `NEEDS_VALIDATION (V-03)` và cho thời gian xe máy *dài hơn* ô tô — trái giả định "xe máy nhanh hơn giờ cao điểm" của Mục 10.1 (xem SF-05).

**3.3. Biến thiên giá độc lập — CẦN QUYẾT ĐỊNH.** Mục 65.2 yêu cầu "thay đổi giá, thời gian đi" giữa các câu, nhưng không cho mức thay đổi. Nếu chỉ dùng giá suy từ quãng đường, hệ số giá trong MNL sẽ **trùng lặp (confounded)** với quãng đường. Cần Chủ dự án duyệt một bộ mức (ví dụ một tập hệ số nhân giá) — **tôi không tự đặt con số**.

**3.4. Ảnh hưởng của đi bộ 200 m lên giá taxi ghép (C9, Mục 23.3, μ = 2,0)** — chưa quyết định có hiển thị giá đã bù đi bộ hay giữ nguyên. Cần quyết định.

## 4. Phân bổ tình huống
- Mỗi người làm **đủ 8 ngữ cảnh** của Phần 1A (thiết kế giai thừa đầy đủ 2×2×2), **thứ tự ngẫu nhiên** theo người.
- Thuộc tính xoay vòng của taxi ghép (khả năng ghép 3 mức × đi bộ 2 mức = 6 tổ hợp) được gán theo **khối (block)**: người trả lời nhận `design_block = (số thứ tự hoàn thành) mod 3`; mỗi khối là một hoán vị cân bằng để mọi tổ hợp xuất hiện đều qua các ngữ cảnh. Bảng khối cụ thể sẽ sinh tất định và nộp kèm khi các mức ở mục 3.3 được duyệt.
- **Vị trí 3 thẻ** được xáo trộn mỗi câu và ghi lại (`position`) để kiểm tra thiên lệch vị trí.
- Phần 1B: 2 câu = 2 mức giá ghế (180k, 220k); mức "khả năng đủ khách" ghép cặp khi có giá trị (TBD).
- Phần 2: thứ tự và nhãn X/Y/Z của 3 phương pháp ngẫu nhiên theo người.

## 5. Ẩn danh và mã người trả lời
- `respondent_id` = UUID v4 sinh **phía máy chủ** khi bắt đầu, giữ trong `sessionStorage` của trình duyệt để mọi câu trả lời của cùng một người dùng chung mã; không cookie theo dõi.
- **Không thu:** họ tên, email, mã sinh viên, số điện thoại, địa chỉ IP (không ghi log IP), vị trí chính xác, ô nhập tự do.
- Mốc thời gian chỉ lưu ở mức phút (đủ cho kiểm tra thời gian làm bài).
- Dữ liệu khảo sát **không** liên kết với bảng `users` của hệ thống và không chứa giới tính (P1-D6).
- Lưu trữ: bảng thuộc module `ml_models` (Mục 54: `survey_responses`) trong PostgreSQL của dự án — không dùng dịch vụ khảo sát bên ngoài khi chưa được phép (P1-D5).

## 6. Schema xuất dữ liệu
Xem [`survey/s1/export_schema.md`](../../../survey/s1/export_schema.md): 3 bảng `respondents`, `choices` (định dạng dài: một dòng / phương án / câu, phù hợp MNL và GroupKFold theo `respondent_id`), `fairness_h4` (phục vụ Wilcoxon / Friedman).

## 7. Quy tắc kiểm tra chất lượng (đề xuất — ngưỡng cần duyệt)
| Quy tắc | Mô tả | Ngưỡng |
|---|---|---|
| QC1 Hoàn thành | Đủ 8 + 2 câu lựa chọn, 4 câu Phần 2, nhóm D1 | bắt buộc |
| QC2 Thời gian làm bài | Loại nếu nhanh bất thường so với ước tính 4–5 phút | **TBD** |
| QC3 Trả lời một màu | Chọn cùng một vị trí thẻ ở cả 8 câu 1A | gắn cờ, không tự loại |
| QC4 Likert một màu | Cho cùng một điểm cho cả 3 phương pháp | gắn cờ, không tự loại |
| QC5 Câu kiểm tra chú ý | Một câu có phương án trội rõ ràng — **chỉ thêm nếu được duyệt** (làm bài dài hơn) | TBD |
Câu trả lời bị gắn cờ vẫn được lưu; việc loại khỏi phân tích quyết định ở P7–P8 và được báo cáo minh bạch.

## 8. Kế hoạch phát hành và quản lý chỉ tiêu phân tầng
- **Cỡ mẫu:** 100–200 câu trả lời hợp lệ (R9:65.1) — **chốt con số mục tiêu: TBD**.
- **Chỉ tiêu:** mỗi nhóm 40–60%. Bảng theo dõi số câu trả lời hợp lệ theo nhóm; khi một nhóm đạt **60% của mục tiêu** thì đóng nhận nhóm đó (người thuộc nhóm đầy chỉ được cảm ơn, không làm tiếp).
- **Kênh phát hành:** **TBD** (do Chủ dự án quyết định).
- **Hạ tầng phát hành:** biểu mẫu web tĩnh + API ghi dữ liệu trong backend, **cần một địa chỉ truy cập công khai** (hiện hệ thống chỉ chạy `127.0.0.1`) — **cần quyết định nơi triển khai**.
- **Trình tự:** (1) duyệt tài liệu này → (2) dựng biểu mẫu + API + bảng `survey_responses` → (3) chạy thử nội bộ, kiểm tra export → (4) phát hành link → (5) theo dõi chỉ tiêu hằng ngày.

---

## Tóm tắt các điểm cần Chủ dự án quyết định
1. Chấp nhận phương pháp B (mục 3.1) cho ngữ cảnh 6 km, hoặc cung cấp số liệu khác.
2. Chọn giá dự kiến taxi ghép 14 km: 143.000 đ (ghép cụ thể, Mục 16.1) hay 145.000 đ (`Fare_matched_est`, Mục 20.2).
3. Bộ mức biến thiên giá độc lập (mục 3.3).
4. Cách thể hiện giá khi đi bộ 200 m (mục 3.4).
5. Mức "khả năng đủ khách" cho Phần 1B.
6. Các khoảng lựa chọn cho D2–D4.
7. Ngưỡng QC2 và việc có dùng câu kiểm tra chú ý (QC5).
8. Cỡ mẫu mục tiêu, kênh phát hành, nơi triển khai công khai.
