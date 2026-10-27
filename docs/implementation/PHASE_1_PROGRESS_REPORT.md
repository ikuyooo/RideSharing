# PHASE 1 — BÁO CÁO TIẾN ĐỘ (chưa phải báo cáo hoàn thành)

- **Cập nhật:** 2026-10-28 (sau "P1 FINAL HARDENING & APPROVAL GATES").
- **Trạng thái P1: `PHASE_1_IN_PROGRESS__APPROVAL_REQUIRED`.** `PHASE_1_COMPLETION_REPORT.md` **không được tạo** — còn blocker (mục 8).
- Giữ nguyên: `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`; SF-06 = OPEN; Revision 9 và Baseline v1 không bị sửa; không chuyển sang P2.
- Tài liệu chi tiết: `service_area/GEOMETRY_REVIEW_P1_HARDENING.md`, `survey/SURVEY_S1_DESIGN_REVIEW.md` §13, `survey/SURVEY_S1_PRICE_VARIATION_DESIGN.md`, `P1_DESIGN_DECISIONS.md` §5, `SPEC_FINDINGS_P1.md`.

## 1. Quyết định đã thực hiện

| Mã | Kết quả |
|---|---|
| GEO-A | 4 nguồn đối chiếu (OSM snapshot, lịch sử OSM v1–v9, GADM 4.1, HDX COD-AB/GSO); không nguồn có thẩm quyền → `PENDING_GEOMETRY_EVIDENCE` giữ nguyên; không nối, không thay thế, không sửa kết quả phân loại |
| GEO-B | Sơn Tây, Chương Mỹ ngoài URBAN trong MVP, vẫn trong TOTAL |
| GEO-C | Lớp 1 = cận dưới trắc địa (không thể từ chối nhầm); lớp 2 bắt buộc; đọc đúng phần tử ma trận; ≤ 150 km |
| GEO-D | `max_snap_m = 300` ngưỡng tạm thời MVP; khảo sát điểm đón thực tế |
| GEO-E | `exclude=ferry` trên graph hiện có (không build lại OSRM); 0 chặng phà |
| GEO-F | Ứng viên mới `sa-cand-9bd44393e699`; v1/v2/v3 nguyên vẹn |
| SURVEY-01…07 | Draft 3: trần cam kết trên thẻ ghép, 19/16 phút & 6 phút đi vòng là giả định khảo sát, khả năng ghép 3 mức chữ, D2–D4 mới (không bắt buộc), cờ `FAST_RESPONSE_REVIEW`, quy tắc dữ liệu R1–R5, kiểm tra nhận dạng thí nghiệm |

## 2. Ứng viên vùng phục vụ

| | v3 `7da7fbe2e01b` | **v4 `9bd44393e699`** |
|---|---|---|
| URBAN | 340,034 km², 6 phần | 340,034 km², 6 phần (không đổi) |
| TOTAL thô (vùng bao lớp 1) | 42.275,390 km², 913 đơn vị | 68.374,523 km², 1.140 đơn vị |
| EXCLUDED | 29,158 km², 324 phần | 488,167 km², 1.770 phần |
| Lớp 2 | snap 300 m, ≤ 150 km | + không đi phà |

SHA-256 v4: urban `fc11eb3e…f268`, total `bf7047cb…4a43`, excluded `295585b5…1bc5`; import lại: `unchanged (ST_Equals)` cả 3 lớp, hash trùng.

## 3. Phân loại thực tế trên v4 (mã sản phẩm + OSRM, hai lớp)

| Ca | Kết quả | So với v3 |
|---|---|---|
| Phenikaa → La Phù | URBAN 2b, 5,977 km — PASS | như cũ |
| ~3 km TP Hưng Yên | UNSUPPORTED 3b — PASS | như cũ |
| Đệm 14,992 / 15,321 km | URBAN / INTERCITY — PASS | như cũ |
| Giới hạn 149,984 / 150,024 km | INTERCITY / OUT_OF_SERVICE_AREA (lớp 2) — PASS | như cũ |
| **Đông Anh → Hoàn Kiếm** | **INTERCITY 19,678 km — FAIL so với Mục 2.3** | như cũ (blocker) |
| An Khánh (Splendora) / Tùng Thiện / Phố Hiến → Hoàn Kiếm | URBAN 2a / INTERCITY / INTERCITY — PASS | như cũ |
| Điểm > 150 km / xa đường / trong EXCLUDED / đúng biên polygon | OUT_OF_SERVICE_AREA (lớp 2 / lớp 2 / lớp 1 / lớp 2) — PASS | biên polygon: mới |
| Hà Nội → Cát Bà | không đi phà → không có tuyến | mới (trước: 150,577 km qua phà 2,015 km) |

Nghiệm thu mọi ca = NOT_VERIFIED vì hình học chưa phê duyệt.

## 4. Số liệu kiểm thử thực tế (2026-10-28)

| Bộ | Kết quả |
|---|---|
| Backend pytest | **131 passed, 0 failed, 0 skipped** (architecture 2, config 4, driver 6, health 2, identity 11, official units 4, routing 8, schema 24, service-area versioning 7, survey 16, trip API 23, trip rules 24) |
| Migration | DB chính `0004 (head)`; CSDL tạm: head → **base** → head → `alembic check` không lệch |
| 150 km | Unit: 149,98 / 150,00 nhận; 150,001 / 150,02 từ chối; thực tế: 149,984 nhận, 150,024 từ chối |
| Snap 300 m | Unit: 300,0 nhận / 300,1 từ chối; thực tế: điểm đón 3.296 mẫu → 1,3% từ chối do xa đường (Hà Nội 0%) |
| Phà | Test OSRM thật Hà Nội → Cát Bà; 412 đích trên v4: 0 chặng phà khi áp chính sách |
| Khảo sát & export | 16 test (thiết kế, giá/thời gian hiển thị, D2–D4 tùy chọn, cờ, quota, rate limit, xóa, TEST/RESEARCH, export gồm `quote_cap_vnd`, `duration_s`) |
| Backup / restore | Diễn tập PASS (3 người / 30 câu trả lời, hash nội dung trùng) |
| Smoke check P0 (`--restart-test`) | **18/18 PASS** — `evidence/p0_smoke_check_p1_hardening.json` |

## 5. Khảo sát S1 — giá và thời gian hiển thị (draft 3)

| Ngữ cảnh | Xe máy | Taxi bao xe | Taxi ghép: dự kiến / trần cam kết / tối đa nếu không ghép / đi vòng thêm |
|---|---|---|---|
| 14 km | 81.000 đ · 35 phút | 194.000 đ · 40 phút | 145.000 / 155.000 / 174.000 đ · +12 phút |
| 6 km | 41.000 đ · 16 phút | 95.000 đ · 19 phút | 71.000 / 76.000 / 85.000 đ · +6 phút |
| Liên tỉnh (Hà Đông → TP Hưng Yên) | — | 637.000 đ | ghép: giá ghế 180.000 / 220.000 đ, đặt trước 3–5 ngày |

Khả năng ghép: Cao / Trung bình / Thấp (giả định, không phần trăm). Đi bộ 0 / 200 m (không giảm giá). 143.000 đ không xuất hiện trên thẻ (chỉ thuộc kịch bản A Mục 16.1).
Bảng kịch bản 52 dòng: 42 đã quyết định, 6 chờ duyệt (mức "đủ khách" 1B, ghép 1B, quy tắc dữ liệu R1–R4), 4 đề xuất không kích hoạt (d 0,20 / 0,35, giá ±10%, thời gian ±20%).

## 6. Thiết kế thí nghiệm

Thiết kế đang chạy **không nhận dạng được** (hạng 7/9 — giá và thời gian chỉ đổi theo quãng đường). Đề xuất D (d ghép, giá ±10%, thời gian ±20% riêng từng phương tiện): hạng 9/9, VIF lớn nhất 5,3, khả thi 48/48 theo cận Baseline — **chờ duyệt, chưa kích hoạt**.

## 7. HTTPS / công khai

`PREPARED — NOT DEPLOYED`: thiếu domain, quyền máy chủ, bộ câu hỏi cuối được duyệt, thời hạn lưu trữ. Đã kiểm: Caddy config hợp lệ, rate limit (Redis thật), consent nháp, backup/restore, tách TEST/RESEARCH. TLS chưa thể kiểm (chưa có domain). Không thu dữ liệu thật qua localhost; DB chính 0 câu trả lời.

## 8. Blocker và tiêu chí đóng P1

| Tiêu chí | Trạng thái |
|---|---|
| Schema, Identity, Driver/KYC mock | ĐẠT |
| Trip Intent đúng mọi ca biên trên hình học **đã phê duyệt** | **CHƯA** — Đông Anh (SF-P1-14); `sa-cand-9bd44393e699` chưa phê duyệt |
| S1 phát hành và thu thập | **CHƯA** — thiết kế không nhận dạng được (SF-P1-21), 6 dòng chờ duyệt, chưa có domain / máy chủ |
| `PHASE_1_COMPLETION_REPORT.md` | **Không tạo** |
