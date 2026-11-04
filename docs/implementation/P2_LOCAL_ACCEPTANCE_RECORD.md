# HỒ SƠ NGHIỆM THU LOCAL — PHASE 2 (routing · candidate · pooling)

- **Quyết định Chủ dự án (2026-11-04):** `PHASE_2_LOCAL_ACCEPTED__KNOWN_LIMITATIONS`.
- **Ý nghĩa:** nghiệm thu kỹ thuật P2 trong phạm vi kiểm chứng **local** mô tả dưới đây. **Không** phải production readiness. **Không** tuyên bố HC10, nhánh xác thực của HC11, hay mọi rủi ro định tuyến đã được chứng minh đầy đủ.
- **Giữ nguyên:** P0 `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`; SF-06 `OPEN`; ngoại lệ DEVELOPMENT FIRST; Revision 9 và Baseline v1 không thay đổi.
- Hồ sơ chi tiết: `P2_PROGRESS_REPORT.md`, `P2_IMPLEMENTATION_PLAN.md` (§10, §10a), `SPEC_FINDINGS_P2.md`.

## 1. Phạm vi kiểm chứng

| Hạng mục | Đã kiểm | Không nằm trong phạm vi |
|---|---|---|
| 11 ràng buộc cứng | Kiểm chứng độc lập `final-verify` (2026-10-31): **65.662** ứng viên, **0** vi phạm; 3.635 lần loại xe đơn đều đúng; 4.735 kiểm tra kế hoạch, 0 bỏ sót (SQL riêng, OSRM `/route` trực tiếp, duyệt vét cạn `tests/p2_reference.py`) | HC10 thực tế (chưa có điểm đón C9: `walk_m = 0` — SF-P2-18). Nhánh "cùng giới **đã xác thực** → được ghép" của HC11 chỉ có unit test (CSDL không cho `VERIFIED` — SF-P2-10, fail-closed) |
| Thuật toán chèn §36 | 10.000 kịch bản ngẫu nhiên khớp duyệt vét cạn (0 vi phạm, chi phí tối ưu) | Bước 4–5 (định giá) thuộc P3 |
| Định tuyến | 1 request `/table` mỗi profile (OD-P2-01); bảng chữ nhật tương đương bảng vuông (SF-P2-02, có test chứng minh) | Khác biệt `/table` – `/route` (§4) |
| Ứng viên `PENDING_P3` | 822 ứng viên, **0** qua `offerable()` | — |
| Kiểm thử | 215 backend test PASS (2026-10-31) + 4 test bảo vệ mới (OD-P2-03, OD-P2-06) PASS 2026-11-04; migration head 0005, `alembic check` sạch; smoke P0 18/18 PASS | Máy chủ thật (`EXTERNAL_VALIDATION_DEFERRED`) |
| Dữ liệu | SYNTHETIC (tài xế, chuyến, kế hoạch sinh ngẫu nhiên, seed 20261029) | Dữ liệu người dùng thật, kẹt xe thật |

## 2. Quyết định đã duyệt

| Mã | Quyết định | Ghi chú |
|---|---|---|
| OD-P2-01 | APPROVED | 1 request mỗi profile |
| OD-P2-02 | APPROVED | Không cache ma trận kiểm RB |
| OD-P2-03 | **APPROVED_FOR_MVP** | Cửa sổ theo dịch vụ; RB 9 kiểm luật đặt trước; không đón trước giờ khách chọn (`test_scheduled_pickup_never_before_the_chosen_time`) |
| OD-P2-04 | APPROVED | Chỉ `COMPLETE` mới được chào |
| OD-P2-05 | **APPROVED_AS_P2_BASELINE** | 5 km; false negative chuyển cổng chất lượng gợi ý P6 |
| OD-P2-06 | **APPROVED_WITH_SAFEGUARDS** | NULL ≠ 0; mọi ràng buộc khác vẫn bắt buộc (`test_null_detour_limit_is_not_zero`) |
| OD-P2-07 | APPROVED_FOR_LOCAL | `location_stale_s = 120` |
| SF-P2-02 | APPROVED | Ma trận chữ nhật có kiểm chứng tương đương |
| SF-P2-15 | **APPROVED_MITIGATION_FOR_P4** | Chưa hiện thực → **chưa** `RESOLVED` |

## 3. Bằng chứng benchmark — ba phạm vi đo riêng biệt

**Quy trình (SF-P2-16 + bài học 2026-11-04):** chạy trong mạng compose; `--analyze`; lấy mẫu `docker stats` 10 s; 200 yêu cầu SYNTHETIC mỗi cấu hình; 3 lượt tuần tự; **trên worktree tách biệt tại commit `a1927de`** (mã đo không thể bị sửa giữa chừng). `git_dirty_files` = 0 / 1 / 2 là chính các thư mục bằng chứng của lượt trước trong worktree. Trong lúc đo không chạy test; chỉ có thao tác soạn tệp ở thư mục dự án chính.

Lượt: `20261104T173000Z-acceptance-final-a1`, `…173631Z-…-a2`, `…174053Z-…-a3`. Đơn vị ms, p95 từng lượt.

| Workload | (1) PostGIS + OSRM Table | (2) Sinh ứng viên trước persist — **chỉ tiêu §79 < 300** | (3) Sinh ứng viên + persist | p99 của (2) | Lỗi |
|---|---|---|---|---|---|
| 50 × 0 | 60,1 / 56,7 / 36,7 | 77,7 / 73,3 / 42,2 | 198,0 / 148,4 / 93,0 | 93 / 81 / 79 | 0 |
| 200 × 0 | 67,9 / 74,1 / 42,2 | 94,3 / 112,4 / 61,4 | 282,4 / 292,5 / 160,8 | 122 / 136 / 78 | 0 |
| 1.000 × 0 | 121,6 / 87,4 / 48,3 | 182,4 / 124,7 / 68,8 | 456,1 / 303,1 / 171,6 | 226 / 168 / 96 | 0 |
| 200 × 10 | 141,0 / 160,1 / 71,9 | 186,6 / 200,9 / 90,1 | 449,1 / 410,2 / 201,6 | 230 / 283 / 138 | 0 |
| 200 × 20 | 231,2 / 79,5 / 97,8 | **297,9** / 99,3 / 118,9 | **808,1** / 189,9 / 205,6 | **397** / 129 / 138 | 0 |
| 1.000 × 20 | 192,2 / 95,9 / 90,3 | 239,9 / 122,1 / 122,4 | 420,5 / 203,0 / 221,3 | 276 / 191 / 136 | 0 |
| 200 × 20-HC | 117,7 / 116,6 / 97,3 | 153,4 / 148,7 / 130,9 | 255,0 / 255,2 / 227,0 | 246 / 244 / 163 | 0 |

OSRM: 2 request / lượt ở mọi lượt (1 mỗi profile).

**Đánh giá trung thực:**
- Phạm vi (2) — đúng phạm vi của §79 / §77 — đạt p95 < 300 ms ở **mọi** lượt và mọi workload. Nhưng lượt a1 ở 200 × 20 chỉ còn **2,1 ms** biên (297,9 ms) và p99 397 ms; a2 / a3 cùng mã cho 99–119 ms. Phương sai giữa các lượt trên máy local là lớn và **chưa xác định được nguyên nhân** của lượt chậm (lượt a1 chạy ngay sau khi tạo worktree; dữ liệu `docker_stats.jsonl` đi kèm). Biên an toàn của SLA trên máy này là **rủi ro**, không phải đã chứng minh.
- So với `final-a1..a3` (2026-10-30, p95 ≤ 188,5 ms) thì lượt a1 hôm nay chậm hơn rõ rệt trên cùng mã thuật toán; kết luận hiệu năng P2 dựa trên nhiều lượt, không dựa trên lượt đẹp nhất.
- Phạm vi (3) gồm ghi CSDL (`persist` p95 ~114 ms, trung vị 3 lượt): p95 tới **808 ms**. Không thuộc chỉ tiêu §79 P2, nhưng là chi phí thật khi P4 ghi ứng viên — chuyển thành rủi ro P4 / P6 (§5).
- Ba lượt khác ngày 2026-11-04 (`acceptance-scopes`, `-a1`, `-a2`) **không hợp lệ** (tải đồng thời / mã bị sửa khi đang đo) — giữ làm bằng chứng lịch sử, có tệp `DISTURBED.md` / `INVALID.md` / `INTERRUPTED.md`.

## 4. Khác biệt OSRM `/table` và `/route` (SF-P2-15)

- `/table` tính từng cặp điểm độc lập (cho phép quay đầu tại điểm dừng); `/route` qua nhiều điểm với profile car (`continue_straight_at_waypoint = true`, `u_turn_penalty = 20 s`) thì không.
- Đo trên 18.415 ứng viên ghép (`final-verify`): **349 (1,9 %)** sẽ vi phạm HC03 / HC05 / HC06 nếu đi theo `/route` mặc định; tỷ lệ quãng chuỗi p99 1,12–1,21, max 2,04.
- Quyết định: **P4 phải** xác minh chuỗi điểm dừng cuối bằng `/route` trước khi chào, kiểm lại mọi ràng buộc cứng bị ảnh hưởng, không bỏ qua lỗi định tuyến. Đến khi đó, việc chào ứng viên ghép ở P4 bị chặn bởi yêu cầu này.

## 5. Rủi ro chuyển giai đoạn

| Sang | Rủi ro / việc phải làm |
|---|---|
| P3 | SF-P2-09 (`T_plan` / `PlanFare`) — đã chuyển P3; định giá nhánh A (`PENDING_P3` → `COMPLETE` chỉ khi mọi cổng qua) |
| P4 | SF-P2-15 (`/route` trước khi chào); khóa `plan_version` (§42); ghi `direct_distance_m / direct_duration_s` khi đặt; chi phí persist (phạm vi 3) |
| P6 | False negative bán kính 5 km (OD-P2-05); biên SLA trên phần cứng thật; đuôi p99 |
| C9 | Kiểm thử tích hợp HC10 với điểm đón gặp nhau (SF-P2-18) |
| Xác thực giới tính | HC11 nhánh đã xác thực (SF-P2-10), giữ fail-closed |

## 6. Hạn chế HC10 / HC11

- **HC10:** generator luôn có `walk_m = 0` vì chưa có C9. Vi phạm HC10 chỉ được kiểm bằng unit test (`test_each_violation`); kiểm chứng độc lập không bao gồm HC10 thực tế.
- **HC11:** 3.301 phương án bị loại vì khách bật cùng giới mà không có giới tính đã xác thực, 0 vi phạm. Nhánh chấp nhận (cùng giới đã xác thực) chưa thể chạy trên CSDL.

## 7. SF-06

Vẫn **OPEN**: không tuyên bố đạt `100 × 100 < 50 ms`.

## 8. Git

| Commit | Nội dung |
|---|---|
| `b3412ba` | P2 routing / candidate / pooling (giữ nguyên) |
| `a048732` | P2 hardening + kiểm chứng độc lập (giữ nguyên) |
| `a1927de` | Ghi nhận quyết định Chủ dự án, test bảo vệ, đo ba phạm vi; bằng chứng lượt không hợp lệ |
| (commit khóa hồ sơ này) | Hồ sơ nghiệm thu + bằng chứng `acceptance-final-a1..a3` |

Không rewrite lịch sử; không push remote. Working tree khi tạo commit khóa: chỉ chứa thay đổi P3 đang làm (không stage vào commit P2).
