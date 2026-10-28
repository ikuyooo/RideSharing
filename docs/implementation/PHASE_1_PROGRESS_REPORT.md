# PHASE 1 — BÁO CÁO TIẾN ĐỘ (chưa phải báo cáo hoàn thành)

- **Cập nhật:** 2026-10-28 (sau "P1 OWNER APPROVAL & FINAL CLOSURE GATES").
- **Trạng thái P1: `PHASE_1_IN_PROGRESS__APPROVAL_REQUIRED`.** `PHASE_1_COMPLETION_REPORT.md` **không được tạo**: khảo sát S1 chưa phát hành, chưa thu dữ liệu thật (mục 8).
- Giữ nguyên: `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`; SF-06 = OPEN; Revision 9 và Baseline v1 không bị sửa; không chuyển sang P2.
- Lịch sử các vòng trước: `P1_DESIGN_DECISIONS.md` §1–6, `SPEC_FINDINGS_P1.md`, `service_area/GEOMETRY_REVIEW_P1_FINAL_CLOSURE.md`, `service_area/GEOMETRY_REVIEW_P1_HARDENING.md`.

## 1. Hình học vùng phục vụ — `GEOMETRY_APPROVED_FOR_MVP`

`sa-cand-0d5347b4294e` (rules v5) đạt **8/8 cổng kiểm** của Chủ dự án (`service_area/sa-cand-0d5347b4294e/APPROVAL_GATES.json`) và được ghi `status = APPROVED`, `approval_reference = GEOMETRY_APPROVED_FOR_MVP | … academic MVP scope only - NOT a legal certification …`. Cấu hình chạy: `SERVICE_AREA_VERSION = sa-cand-0d5347b4294e`, `ALLOW_CANDIDATE_SERVICE_AREA = false`. v1–v4 giữ nguyên.

| | Giá trị |
|---|---|
| URBAN | 344,381 km², 7 phần — 48 phường k1–k48 + Xã Gia Lâm + 7 polygon An Khánh / Splendora + thị trấn Đông Anh cũ (tái dựng từ OSM) |
| TOTAL (vùng bao sàng lọc) / EXCLUDED / vùng chấp nhận lớp 1 | 68.374,523 / 488,167 / 67.886,357 km² |
| Lớp 2 bắt buộc | OSRM car từng điểm: snap ≤ 300 m, có tuyến từ anchor, ≤ 150 km, không đi phà |
| SHA-256 | urban `33ca5346…0307`, total `c3de995a…6353`, excluded `dcb26c8f…82cf` |

Rủi ro địa giới Đông Anh còn lại: `GEOMETRY_REVIEW_P1_HARDENING.md` §10 (không có bản đồ địa giới nhà nước; biên lệch GADM tới 222 m; 9,9% diện tích GADM ngoài polygon OSM).

## 2. Ca biên địa lý trên hình học đã duyệt (đánh giá mới `APPROVAL_GATE_EVAL`)

| Ca | Kết quả |
|---|---|
| Phenikaa → La Phù | URBAN (2b), 5,977 km |
| ~3 km TP Hưng Yên | UNSUPPORTED_INTER_PROVINCE_ROUTE (3b) |
| Đệm 14,992 / 15,321 km | URBAN / INTERCITY |
| Giới hạn 149,984 / 150,024 km | INTERCITY / OUT_OF_SERVICE_AREA (lớp 2) |
| Đông Anh → Hoàn Kiếm | **URBAN (2a)** |
| An Khánh / Tùng Thiện / Phố Hiến / La Phù → Hoàn Kiếm | URBAN / INTERCITY / INTERCITY / INTERCITY |
| Điểm > 150 km (256,4 km), snap 1.576,6 m, điểm trong EXCLUDED, điểm đúng biên polygon | đều OUT_OF_SERVICE_AREA đúng lớp |
| Phà: 412 đích, Hà Nội → Cát Bà | 0 chặng phà; Cát Bà `NoRoute` |

15/15 PASS. Đánh giá chạy lại **sau** khi phê duyệt (`sa-cand-0d5347b4294e/POST_APPROVAL_EVAL.md`): cột nghiệm thu = **PASS** cả 15 ca.

## 3. Khảo sát S1 (draft 4) — chưa phát hành

- Câu hỏi: 145.000 đ (xe chưa có người thứ hai) và 143.000 đ (phân bổ A+B) tách bạch; 19/16 phút, +6 phút, giá ±10% là giả định thí nghiệm; khả năng đủ khách liên tỉnh 3 mức Thấp / Trung bình / Cao, xoay trực giao với giá ghế; `FAST_RESPONSE_REVIEW` chỉ gắn cờ; quota 150 (40–60%).
- Ma trận D: `APPROVED_FOR_TEST_PILOT_ONLY`, công tắc trong tệp vẫn **tắt**. Kiểm định (`survey/SURVEY_S1_PRICE_VARIATION_DESIGN.md` §5): hạng 11/11, VIF lớn nhất 5,42 ("5,3" trước đây là VIF trên đặc tả 9 cột), condition number 151 / 241, D0 1,34 / Dp 4,68; **mức thời gian xe máy lệch; hệ số thời gian không ước lượng được ở N = 150 (|t| kỳ vọng 1,1)** → đề xuất **D2** (cân bằng, |t| thời gian 2,7 với đặc tả gọn, condition number 98 / 115) — chờ duyệt.
- Pilot TEST 150 người (75/75) qua API → DB → export → ước lượng: chuỗi đúng (mọi tham số trong 3,5 SE), giá ước lượng tốt, `pricing_configs` không đổi, RESEARCH rỗng.
- R1–R4: bảng đánh giá ở `SURVEY_S1_DESIGN_REVIEW.md` §14 — **chưa ACCEPTED**; khuyến nghị: R1, R2, R3 chấp nhận có điều chỉnh; R4 chấp nhận.

## 4. HTTPS / quyền riêng tư

`PREPARED — NOT DEPLOYED` (thiếu domain, máy chủ). Kiểm thử phát hành cục bộ qua HTTPS (`scripts/survey/staging_e2e.sh`): TLS (CA nội bộ Caddy), HSTS, CSP, chỉ mở route khảo sát, 1 câu trả lời TEST đi hết quy trình, log không có IP, CSDL staging TEST = 1 / CSDL chính 0 — **PASS**, đã dọn sạch. Lưu trữ đề xuất 12 tháng sau khi đóng khảo sát (không phải thời hạn luật định), backup 30 ngày, `purge_survey.sh` đã thử trên CSDL tạm.

## 5. Kiểm thử (2026-10-28, sau thay đổi)

| Bộ | Kết quả |
|---|---|
| Backend pytest | **136 passed, 0 failed, 0 skipped** (architecture 2, config 4, driver 6, health 2, identity 11, official units 5, routing 8, schema 24, service-area versioning 7, survey pilot 3, survey 17, trip API 23, trip rules 24) |
| Migration | DB chính `0004 (head)`; CSDL tạm head → base → head → `alembic check` |
| Cổng phê duyệt v5 | 8/8 PASS |
| Pilot TEST (D, D_bal, D2) | 3/3 PASS |
| HTTPS staging | PASS |
| Purge / backup-restore | PASS (CSDL tạm) |
| Smoke check P0 (`--restart-test`) | **18/18 PASS** — `evidence/p0_smoke_check_p1_owner_gates.json`; sau restart v5 vẫn APPROVED |

## 6. Còn chờ Chủ dự án

1. Chọn D hay D2 cho pilot tiếp theo; chốt đặc tả MNL chính.
2. Duyệt R1–R4 (và các điều chỉnh đề xuất: thống kê tỷ lệ hoàn thành, nâng giới hạn phiên/IP, bộ đếm 422).
3. Duyệt thông báo đồng ý + thời hạn lưu trữ 12 tháng + đầu mối liên hệ.
4. Cung cấp domain/subdomain và quyền máy chủ.

## 7. Điều kiện cuối cùng trước khi đóng P1

| Điều kiện | Trạng thái |
|---|---|
| Schema, Identity/RBAC, Driver/KYC mock | ĐẠT |
| Trip Intent đúng mọi ca biên trên hình học đã duyệt | **ĐẠT (MVP)** — v5 `GEOMETRY_APPROVED_FOR_MVP` |
| Thiết kế thí nghiệm S1 ước lượng được các tham số chính | **CHƯA** — chờ D2 / đặc tả MNL |
| Quy tắc dữ liệu R1–R4, thông báo đồng ý, lưu trữ | **CHƯA** — chờ duyệt |
| HTTPS công khai: domain, TLS hợp lệ, truy cập từ thiết bị ngoài, QR | **CHƯA** — chờ hạ tầng |
| Một câu trả lời thử qua hệ thống công khai không làm bẩn dữ liệu nghiên cứu | **CHƯA** trên domain thật (đã đạt ở staging cục bộ) |
| S1 phát hành (`SURVEY_S1_RELEASED`) và bắt đầu thu dữ liệu thật | **CHƯA** |
| `PHASE_1_COMPLETION_REPORT.md` | Không tạo |
