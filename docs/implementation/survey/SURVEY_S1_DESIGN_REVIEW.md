# SURVEY_S1_DESIGN_REVIEW — Khảo sát S1 (bản trình duyệt)

- **Trạng thái:** `DRAFT 2 — EXPERIMENT_VALUES_PARTLY_PENDING_APPROVAL`. **Chưa phát hành — không phải `SURVEY_S1_RELEASED`.** Không có link thu thập công khai nào. Bản nháp biểu mẫu/API chạy trên môi trường development.
- **Cập nhật 2026-10-27 (quyết định "PHASE 1 FINAL CLOSURE"):** giá trị hiện hành nằm ở `questionnaire.draft.yaml` draft 2 và [bảng kịch bản đầy đủ](SURVEY_S1_SCENARIO_TABLE.md) (mục 12). Các bảng giá trị ở mục 2 bên dưới là bản draft 1, giữ để truy vết.
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

## 9. Rà soát 8 điểm chờ phê duyệt (cập nhật 2026-10-26, quyết định "P1: GEOGRAPHY & S1 CLOSURE" §C)

Đối chiếu lại với Revision 9 Mục 65 và các công thức đã khóa. **Không giá trị nào dưới đây được coi là đã duyệt.**

| # | Mục | Giá trị đề xuất | Nguồn | Phương pháp tạo | Đánh giá | Cần quyết định |
|---|---|---|---|---|---|---|
| 1 | Ngữ cảnh 6 km (Phần 1A) | Xe máy 40.000 đ / 15 phút; bao xe 94.000 đ / 17 phút; ghép dự kiến 70.000 đ, tối đa 84.000 đ, đi vòng +5 phút | Revision 9 không có số liệu 6 km | Phương pháp B: công thức Baseline (`bike_urban`, `car_urban`, `Quote`/`Unmatched` Baseline §2.1, `Fare_matched_est` Mục 20.2) với thời gian tỷ lệ thuận ví dụ 14 km (40/14, 35/14, 12/14 phút/km) | Đã kiểm chứng: cùng phương pháp tái tạo đúng 5 con số 14 km của Revision 9. Hạn chế: thời gian là ngoại suy tuyến tính, không mô hình giờ cao điểm (liên quan SF-05/V-03) | Chấp nhận phương pháp B hay cung cấp số khác |
| 2 | Giá ghép dự kiến 14 km | 143.000 đ (hoặc 145.000 đ) | Mục 10.4 / 16.1 (143k, ghép cụ thể với khách B); Mục 20.2 (145k = `Fare_matched_est`, xe rảnh) | Lấy trực tiếp | Cả hai có nguồn; thẻ Mục 20.1 dùng ~143k. Bản nháp đang hiển thị 143k | Chọn 143k hay 145k |
| 3 | Biến thiên giá độc lập | TBD | Mục 65.2 yêu cầu "thay đổi giá, thời gian đi" nhưng không cho mức | — | Thiếu → hệ số giá MNL trùng lặp với quãng đường (chỉ biến thiên 6/14 km) | Bộ mức biến thiên (hoặc chấp nhận hạn chế) |
| 4 | Giá khi đi bộ 200 m | Giữ nguyên giá hiển thị | Mục 23.3: μ = 2,0 tác động **trọng số phân bổ** `w_i`, không phải phụ phí cộng thẳng; C9 là COULD | Không suy ra giá mới | Hiển thị giá đã bù đi bộ cần một kế hoạch ghép cụ thể (P3) | Giữ nguyên hay hiển thị chú thích |
| 5 | Khả năng đủ khách (Phần 1B) | TBD (bản nháp hiển thị "chờ duyệt") | Mục 65.2 nêu thuộc tính, không nêu mức | — | Không tự đặt mức | Mức (ví dụ dùng chung Cao/Trung bình/Thấp?) |
| 6 | Khoảng lựa chọn D2–D4 | TBD (API chỉ chấp nhận `null`) | Mục 65.2 liệt kê câu hỏi, không cho khoảng | — | Không tự đặt khoảng | Các khoảng lựa chọn |
| 7 | QC2 thời gian tối thiểu; QC5 câu chú ý | TBD; QC3/QC4 đã hiện thực (chỉ gắn cờ) | Mục 65.2 "~4–5 phút" | QC3: cùng vị trí ở cả 8 câu 1A; QC4: cùng điểm cho 3 phương pháp | Gắn cờ, không tự loại | Ngưỡng QC2; có dùng QC5 |
| 8 | Cỡ mẫu, kênh, nơi triển khai | 100–200; kênh/nơi triển khai: đề xuất ở mục 10 | Mục 65.1 | — | Cần địa chỉ công khai | Chốt cỡ mẫu, kênh, hạ tầng, thời hạn lưu trữ |

## 10. Đề xuất phát hành (chờ quyết định)

| Hạng mục | Đề xuất | Lý do / phương án khác |
|---|---|---|
| Nền tảng công khai | **Tự lưu trữ biểu mẫu + API nháp hiện có** trên một máy chủ của dự án (VPS hoặc máy chủ trường), sau reverse proxy HTTPS; **chỉ mở** `/survey/s1` và `/api/survey/s1/*`; endpoint admin (export, quota) chỉ truy cập qua mạng nội bộ / SSH tunnel | Giữ dữ liệu trong PostgreSQL của dự án, giữ được thiết kế ngẫu nhiên theo người + xoay khối. Công cụ ngoài (Google/Microsoft Forms) khó làm thiết kế theo khối và đưa dữ liệu cho bên thứ ba — không khuyến nghị (P1-D5) |
| Cấu hình phát hành | `SURVEY_DATASET=RESEARCH`, `SURVEY_S1_RELEASED=true` **chỉ đặt trên máy chủ phát hành sau khi được duyệt**; môi trường dev luôn `TEST` | Tách tuyệt đối dữ liệu thử và dữ liệu nghiên cứu |
| Lưu trữ | Dữ liệu ẩn danh trong PostgreSQL dự án; file export lưu nơi giới hạn truy cập nhóm dự án; đề xuất giữ dữ liệu nghiên cứu đến hết bảo vệ đồ án + thời hạn do Chủ dự án quyết định, sau đó xóa hoặc chỉ giữ số liệu tổng hợp | Không có PII theo thiết kế (Mục 59.2) |
| Chia sẻ link | **Một link chung** (kèm QR) cho mọi nhóm; nhóm xác định bằng câu D1; phân phát qua kênh sinh viên và kênh người đi làm | Link riêng theo nhóm dễ gây lệch tự chọn và lộ nhóm qua URL |
| Theo dõi tỷ lệ nhóm | `GET /api/admin/survey/s1/quota?dataset=RESEARCH` (đã có) — số hoàn thành theo nhóm và tỷ lệ; theo dõi hằng ngày | Khi một nhóm chạm trần 60% của cỡ mẫu mục tiêu: cần bổ sung cơ chế đóng nhóm (chưa hiện thực, phụ thuộc cỡ mẫu) |

## 11. Trạng thái bản nháp phát triển (development only)

- Đã có: biểu mẫu `/survey/s1` (HTML tĩnh, dải cảnh báo BẢN NHÁP, `noindex`), API phiên/nộp bài, bảng `survey_respondents` + `survey_responses` (migration `0002`, module `ml_models`), export CSV 3 bảng theo `export_schema.md`, quota.
- Rào chắn: `dataset` do cấu hình máy chủ quyết định (`TEST`); `RESEARCH` bị từ chối khi chưa phát hành; không tài khoản ứng dụng, không cột định danh, không FK tới `users`; trường lạ bị từ chối; IP bị xóa khỏi log truy cập của đường dẫn khảo sát; mốc thời gian làm tròn đến phút.
- Kiểm thử: `backend/tests/test_survey_s1.py` — 9/9 PASS.
- Chỉ chạy trên `127.0.0.1`; DB chính **0** câu trả lời. **Chưa phát hành, chưa thu dữ liệu thật. Không phải `SURVEY_S1_RELEASED`.**

## Tóm tắt các điểm cần Chủ dự án quyết định
1. Chấp nhận phương pháp B (mục 3.1) cho ngữ cảnh 6 km, hoặc cung cấp số liệu khác.
2. Chọn giá dự kiến taxi ghép 14 km: 143.000 đ (ghép cụ thể, Mục 16.1) hay 145.000 đ (`Fare_matched_est`, Mục 20.2).
3. Bộ mức biến thiên giá độc lập (mục 3.3).
4. Cách thể hiện giá khi đi bộ 200 m (mục 3.4).
5. Mức "khả năng đủ khách" cho Phần 1B.
6. Các khoảng lựa chọn cho D2–D4.
7. Ngưỡng QC2 và việc có dùng câu kiểm tra chú ý (QC5).
8. Cỡ mẫu mục tiêu, kênh phát hành, nơi triển khai công khai.

---

## 12. Quyết định "PHASE 1 FINAL CLOSURE" (2026-10-27) — hiện thực (draft 2)

Bảng kịch bản đầy đủ (44 dòng, trường `scenario_id, attributes, options, displayed_values, source, derivation, experimental_status, approval_status`): [`SURVEY_S1_SCENARIO_TABLE.md`](SURVEY_S1_SCENARIO_TABLE.md) / `survey/s1/scenario_table.csv`, sinh tự động từ chính tệp bộ câu hỏi API dùng. Không tham số nghiên cứu nào được ghi vào `pricing_configs` (có test).

| # | Quyết định | Hiện thực | Cơ sở đủ / chưa đủ |
|---|---|---|---|
| 1 | Ngữ cảnh 6 km: giá theo công thức khóa + ETA có nguồn | Giá: Baseline (`bike_urban`, `car_urban`, Quote / Unmatched / `Fare_matched_est`) → xe máy **41.000 đ**, bao xe **95.000 đ**, ghép dự kiến **71.000 đ**, tối đa nếu không ghép **85.000 đ**. ETA: OSRM v5.27.1 trên 150 node nội đô (seed 1): trung vị 6 km ô tô 8,80 phút / xe máy 9,57 phút; vì OSRM là dòng tự do (14 km: 18,32 / 20,63 phút so với 40 / 35 phút của Mục 10.4), ETA được **hiệu chỉnh theo tỷ lệ của ví dụ 14 km** → ô tô **19 phút**, xe máy **16 phút** (giá trị OSRM thô 9 / 10 phút ghi làm phương án thay thế). Đi vòng tối đa 6 km = 0,30 × 19,21 = **6 phút** (cùng quy tắc cho 12 phút ở 14 km) | Giá: **đủ** (công thức khóa). ETA: **có nguồn nhưng phương pháp hiệu chỉnh chờ duyệt** (`PENDING_OWNER_APPROVAL`) — SF-P1-18 |
| 2 | 143.000 đ chỉ cho kịch bản A Mục 16.1 | Thẻ chung 14 km hiển thị **145.000 đ** (`Fare_matched_est`, Mục 20.2); 143.000 đ không xuất hiện trên thẻ | **Đủ** (OWNER_DECIDED) |
| 3 | Ma trận biến thiên giá + khả thi; mức chưa chứng minh không dùng làm giá thật | Miền khả thi theo Baseline: `Fare_matched ∈ [0,40P; 0,80P]`, trần không ghép `0,90P` (14 km: 77.600–155.200 đ; 6 km: 38.000–76.000 đ). Đề xuất: d = 0,20 (155k / 76k), d = 0,25 (đang dùng), d = 0,35 (126k / 61k); xe máy / bao xe ±10% không suy ra được từ công thức | d = 0,25: đủ. **Các mức khác `EXPERIMENT_REVIEW_REQUIRED`, `NOT_ACTIVE_PROPOSAL` — không hiển thị** |
| 4 | Đi bộ 200 m là thuộc tính riêng, không tự giảm giá | Giữ nguyên giá; thuộc tính `walk_m` 0 / 200 m xoay vòng | **Đủ** |
| 5 | "Khả năng đủ khách" liên tỉnh là giá trị kịch bản giả định | HIGH: "Đã có 2/3 hành khách tối thiểu đặt chỗ…", LOW: "Chưa có hành khách nào trong 3 hành khách tối thiểu…" (mẫu số 3 = `default_min_seats_to_run` Baseline); thẻ ghi "(giả định)"; ghép 2 giá ghế × 2 mức cân bằng qua 6 khối | `HYPOTHETICAL_SCENARIO`; **câu chữ chờ duyệt** |
| 6 | D2–D4 khoảng rõ ràng, không chồng lấn | D2: 0 / 1–2 / 3–5 / 6–10 / ≥11 lần/tuần; D3: <3 / [3,7) / [7,15) / [15,30) / ≥30 km; D4: 0 / 1 / 2–3 / 4–7 / ≥8 lần/tháng; API chỉ nhận mã định sẵn | **Chờ duyệt khoảng cụ thể** |
| 7 | Không tự loại bài làm nhanh; được gắn cờ với quy tắc công bố trước | `QC2_FAST_COMPLETION` khi thời lượng < 120 s (½ của 4 phút); thời lượng tính từ start token ký HMAC nên CSDL chỉ lưu `duration_s` + mốc thời gian theo phút (migration `0004`); QC3/QC4 gắn cờ; QC5 không dùng | Cơ chế: đủ; **ngưỡng 120 s chờ duyệt** |
| 8 | Mục tiêu 150 hợp lệ (75/75), mỗi nhóm 40–60% | Câu D1 hỏi **trước** khi bắt đầu phiên; nhóm đủ `floor(0,60 × 150) = 90` câu trả lời hợp lệ thì phiên mới của nhóm bị từ chối (409 `QUOTA_FULL_FOR_GROUP`); quota admin hiển thị trần và nhóm đã đóng | **Đủ** (OWNER_DECIDED) |

Hạ tầng phát hành: [`SURVEY_S1_DEPLOYMENT_PLAN.md`](SURVEY_S1_DEPLOYMENT_PLAN.md) — `PREPARED — NOT DEPLOYED` (thiếu domain, máy chủ, phê duyệt bộ câu hỏi cuối). Thông báo quyền riêng tư nháp: `survey/s1/PRIVACY_NOTICE.draft.md`.

Kiểm thử khảo sát (`backend/tests/test_survey_s1.py`): thiết kế tất định, xoay khối + ghép 1B, ràng buộc schema / không PII, start token giả mạo bị từ chối, QC2 theo thời lượng ký số, quota đóng nhóm, rate limit + khóa không chứa địa chỉ, xóa theo yêu cầu (ADMIN), tách TEST / RESEARCH, toàn vẹn export, tham số nghiên cứu không vào `pricing_configs`. DB chính: **0** câu trả lời khảo sát.

---

## 13. Quyết định "P1 FINAL HARDENING & APPROVAL GATES" (2026-10-28) — draft 3

| Mã | Quyết định | Hiện thực | Trạng thái |
|---|---|---|---|
| SURVEY-01 | Giữ giá 6 km theo Baseline; 145k (Mục 20.2, ước tính khi chưa có khách thứ hai) ≠ 143k (Mục 16.1, booking A ghép cụ thể với B); mọi thẻ ghép thể hiện giá dự kiến, **trần cam kết**, giá tối đa nếu không ghép | Thẻ taxi ghép thêm "Trần cam kết nếu ghép được" = `Quote_i` (Mục 18.3): **155.000 đ** (14 km), **76.000 đ** (6 km); 143.000 đ không xuất hiện ở thẻ nào; export thêm cột `quote_cap_vnd` | Đã làm |
| SURVEY-02 | 19 phút ô tô / 16 phút xe máy (6 km) là giả định giờ cao điểm của thí nghiệm; 6 phút đi vòng | Ghi `OWNER_DECIDED`; câu chữ "Thời gian đi vòng thêm tối đa (đón/trả khách khác): +6 phút" — diễn đạt bằng **phút**, không phải giới hạn quãng đường (giới hạn detour 30% theo quãng đường của Mục 6 không hiển thị); dòng giới thiệu: "giá trị giả định cho khảo sát (thời gian theo giờ cao điểm), không phải giá chính thức của ứng dụng". Không ghi vào OSRM / Baseline / thuật toán giá | Đã làm |
| SURVEY-03 | Khả năng ghép 3 mức giả định, không quy đổi phần trăm | Thẻ: "Khả năng ghép (tình huống giả định): Cao / Trung bình / Thấp"; dòng giới thiệu nói rõ không phải dự báo của hệ thống | Đã làm |
| SURVEY-04 | D2: 0; 1; 2–3; 4–6; ≥7 · D3: <3; 3–<6; 6–<10; 10–<20; ≥20 km · D4: 0; 1; 2–3; ≥4 — không bắt buộc | Schema chỉ nhận đúng các mã này hoặc bỏ trống (lưu `null`); biểu mẫu ghi "(không bắt buộc)" | Đã làm + test |
| SURVEY-05 | 120 s chỉ gắn cờ `FAST_RESPONSE_REVIEW`; không câu kiểm tra chú ý; quy tắc dữ liệu thiếu / trùng / không hợp lệ xác định trước | Cờ đổi tên `FAST_RESPONSE_REVIEW`; QC5 không dùng; `analysis_rules` R1–R5 trong bộ câu hỏi (thiếu: không có bài nộp dở; trùng: 1 bài/phiên + rate limit, không ghép danh tính; không hợp lệ: API từ chối; cờ: phân tích chính giữ tất cả + phân tích độ nhạy bỏ bài gắn cờ; TEST không trộn) | Cơ chế xong; **R1–R4 chờ duyệt** |
| SURVEY-06 | Không kích hoạt mức chưa duyệt; kiểm tra tính nhận dạng; ma trận biến thiên riêng | [`SURVEY_S1_PRICE_VARIATION_DESIGN.md`](SURVEY_S1_PRICE_VARIATION_DESIGN.md): thiết kế đang chạy **không nhận dạng được** (hạng 7/9 — giá và thời gian chỉ đổi theo quãng đường); đề xuất D (d ghép, giá ±10%, thời gian ±20% riêng từng phương tiện) đạt hạng 9/9, VIF lớn nhất 5,3, khả thi 48/48 | **Blocker phát hành — chờ duyệt ma trận D** |
| SURVEY-07 | 150 hợp lệ (75/75), 40–60%; một link HTTPS + QR; không triển khai khi thiếu domain / máy chủ | Quota trần 90/nhóm (đã có); phương án HTTPS [`SURVEY_S1_DEPLOYMENT_PLAN.md`](SURVEY_S1_DEPLOYMENT_PLAN.md) | `PREPARED — NOT DEPLOYED` |

Bảng kịch bản (draft 3): 52 dòng — xem [`SURVEY_S1_SCENARIO_TABLE.md`](SURVEY_S1_SCENARIO_TABLE.md).
