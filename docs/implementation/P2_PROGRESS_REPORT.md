# PHASE 2 — BÁO CÁO TIẾN ĐỘ

- **Cập nhật:** 2026-10-31, sau "P2 PERFORMANCE HARDENING & OWNER DECISION". Bản trước: 2026-10-29.
- **Trạng thái P2: `PHASE_2_READY_FOR_OWNER_ACCEPTANCE` (local).**
  - Cả hai tiêu chí kỹ thuật của R9 §79 P2 đạt trên stack local (`LOCAL_VERIFIED`): 0 vi phạm ràng buộc cứng và độ trễ sinh ứng viên p95 < 300 ms ở toàn bộ 6 cấu hình.
  - Việc nghiệm thu thuộc Chủ dự án. Còn 3 quyết định `LOCAL_PROVISIONAL` (OD-P2-03, 05, 06) và 4 phát hiện `OPEN` (SF-P2-09, 10, 15, 18) — xem §8.
  - Hiệu năng trên máy chủ thật: `EXTERNAL_VALIDATION_DEFERRED`. SF-06 vẫn **OPEN**.
  - **P3 chưa bắt đầu.**
- Revision 9, Baseline v1, SLA, `N_single = 15`, `N_pool = 20`, `k_max = 8`, `R_urban = 5 km` và workload benchmark **không đổi**.
- Hồ sơ liên quan:
  - Kế hoạch: `P2_IMPLEMENTATION_PLAN.md` (§10: quyết định OD-P2).
  - Phát hiện: `SPEC_FINDINGS_P2.md` (SF-P2-01..18).
  - Bằng chứng: `evidence/p2_runs/<run_id>/`. Mỗi lượt có `manifest.json` (run id, thời điểm UTC, commit, số file chưa commit, tham số, exit code), `docker_stats.jsonl` (CPU / RAM lấy mẫu 10 s) và `console.log`. Không lượt nào bị ghi đè.

## 1. Lỗi và hạn chế đã xác minh

| # | Phát hiện | Bằng chứng | Xử lý |
|---|---|---|---|
| 1 | Mỗi request OSRM tạo một `httpx.Client` mới, dựng lại SSL context (~10 ms / request, kể cả `http://`) | cProfile `before-cprofile`: `load_verify_locations` 1,54 s / 200 lần; đo nhỏ `osrm-client-microbench`: p50 20,6 → 10,1 ms | Sửa (SF-P2-17) |
| 2 | Bảng `car` khi có kế hoạch ghép là ma trận **vuông**, trong khi thuật toán chèn chỉ đọc ô có đích là điểm dừng phía trước, P, Q | Phân tích mã + `test_insertion_reads_only_stop_destinations` | Sửa (SF-P2-02) |
| 3 | 3 truy vấn tài xế quét cùng một vùng. Không có thống kê bảng thì planner chọn Seq Scan `driver_profiles` lặp 478 lần (75 ms). Truy vấn gộp bản đầu trả 478 dòng sang Python | EXPLAIN `before-explain`, `after-explain`, `final-explain` | Sửa (một truy vấn, `row_number()` trong SQL, ≤ 45 dòng) |
| 4 | Tham số giá đọc lại từ CSDL mỗi lượt (2 câu SQL); `service_windows` / cửa sổ đón / thông tin khách mới tính lại cho **từng tài xế**; tải ghế tính 2 lần mỗi phương án | cProfile | Sửa |
| 5 | Ghi CSDL (`persist`): ORM chèn từng dòng | Thời gian theo giai đoạn | Chuyển sang một lệnh chèn nhiều dòng. Sau đó p95 vẫn ~120–148 ms; nguyên nhân **chưa xác định** (giai đoạn này không nằm trong độ trễ sinh ứng viên của §79 / §77) |
| 6 | Phép đo độ trễ nhạy với điều kiện đo: port proxy Windows, bộ lấy mẫu `docker stats` liên tục, bảng chưa ANALYZE | SF-P2-16; `before-r1`, `before-r2` (`INTERRUPTED.md`) | Quy trình đo sửa lại; ghi đủ lịch sử |
| 7 | SF-P2-15: ngữ nghĩa bảng (quay đầu tại điểm dừng) khác tuyến thật qua nhiều điểm | `final-verify`: 349 / 18.415 ứng viên ghép (1,9%) sẽ vi phạm HC03 / 05 / 06 nếu đi theo `/route` mặc định | **Không** sửa (R9 quy định bảng); đã định lượng, chờ quyết định. Nhận định ngày 29/10 rằng 6 chênh lệch "không phải lỗi thuật toán" được thay bằng số liệu này: đúng với R9, nhưng là rủi ro mô hình thật |
| 8 | Bán kính 5 km gây false negative trên dữ liệu synthetic | `final-radius` (SF-P2-03) | Không đổi (R9); chờ quyết định |
| 9 | Smoke 16/17 ngày 29/10 | Tệp bằng chứng của lần đó đã bị ghi đè ngay sau đó | **Bằng chứng lịch sử không đầy đủ**: không biết mục nào lỗi; **không** được coi là PASS. Smoke mới (§7) ghi ra tệp mới, không xóa lịch sử |

## 2. Thay đổi kỹ thuật và file liên quan

| Thay đổi | File |
|---|---|
| Đo theo giai đoạn: HTTP / JSON / chuyển đổi OSRM, PostGIS tài xế, tra cứu kế hoạch, dữ liệu khách cũ, tham số giá, `check_all`, chèn, dựng ứng viên, ghi CSDL; danh sách tài xế / kế hoạch đã xét (chỉ để kiểm chứng, không ghi CSDL) | `routing/osrm.py`, `pooling/insertion.py`, `candidate/generator.py`, `candidate/service.py` (`persist`) |
| O1 — bảng `car` chữ nhật (vẫn 1 request) | `candidate/generator.py`; test `test_insertion_reads_only_stop_destinations`, `test_branch_a_inserts_into_a_running_vehicle` |
| O2 — một `httpx.Client` / provider, không keep-alive | `routing/osrm.py`; test `test_provider_reuses_one_client_without_keep_alive` |
| P1 — một truy vấn tài xế, top-N mỗi danh sách bằng `row_number()` | `driver/service.py`; test `test_one_spatial_query_returns_the_same_lists_as_one_query_per_list` (so với 3 truy vấn kiểu cũ) |
| P2 — cache tham số giá theo `(version, service)` (dòng bất biến) | `pricing/service.py` |
| Y1–Y3 — tính một lần mỗi dịch vụ / mỗi phương án | `candidate/generator.py`, `pooling/insertion.py` |
| W1 — ghi ứng viên bằng một lệnh chèn nhiều dòng | `candidate/service.py` |
| Cổng `offerable()` cho `PENDING_P3` | `candidate/service.py`; test `test_pending_p3_candidates_are_never_offerable` |
| Test quy tắc cửa sổ đón (OD-P2-03) | `tests/test_candidate_windows.py` |
| Bộ kiểm chứng độc lập (SQL riêng, OSRM gọi trực tiếp, đối chiếu vét cạn) | `scripts/p2_verify.py` |
| Benchmark: run ID, `--verify`, `--analyze`, workload HC, chế độ `explain` / `cprofile` / `radius`; trình chạy giữ bằng chứng; bảng tổng hợp | `scripts/p2_benchmark.py`, `scripts/p2_bench_run.sh`, `scripts/p2_runs_summary.py`; fixture `tests/p2_fixtures.py` (`plan`) |

## 3. Tối ưu đã thực hiện (chỉ dựa trên profiling)

| Khu vực | Trước | Sau | Cách làm |
|---|---|---|---|
| **PostGIS** | 14 câu SQL / lượt. Truy vấn tài xế "ô tô nhận ghép" 75 ms (Seq Scan lặp) | 10–10,7 câu / lượt. Một truy vấn tài xế 5,6–9,4 ms, trả ≤ 45 dòng; dùng GIST + 2 chỉ mục PK | Gộp truy vấn, xếp hạng trong SQL, cache dòng giá bất biến. Không đổi điều kiện lọc; test tương đương với truy vấn cũ |
| **OSRM** | `osrm_car` p95 ~119–122 ms (20 kế hoạch); `osrm_motorbike` ~63–69 ms | `osrm_car` ~64–73 ms; `osrm_motorbike` ~32 ms | O1 (bớt đích không dùng, vẫn 1 request / profile, không cache, không đổi CH / graph); O2 (bỏ dựng SSL context mỗi request) |
| **Python** | Bước 3 (chèn + RB + ứng viên) p95 ~44–47 ms; `check_all` ~7 ms | ~37–39 ms; `check_all` ~4 ms | Y1–Y3. Không cắt nhánh nào; 10.000 kịch bản ngẫu nhiên vẫn khớp duyệt vét cạn |

## 4. Benchmark trước / sau

Đo trong mạng compose, 4 vCPU WSL2, 200 yêu cầu SYNTHETIC mỗi cấu hình, seed 20261029, workload không đổi.

**Ba bộ số "trước":**
- "Trước (29/10)": lượt FAIL đã báo cáo trước đây. Đo khi xen kiểm chứng giữa các yêu cầu, ở điều kiện máy khác.
- "Trước (30/10)": 3 lượt cùng mã chưa tối ưu, quy trình đo mới (`before-s1..s3`), bảng chưa ANALYZE.

**Bộ số "sau":**
- "Sau": 3 lượt có ANALYZE (`final-a1..a3`).
- Kèm 1 lượt không ANALYZE (`final-noanalyze`) và lượt có kiểm chứng (`final-verify`).

| Workload | p50 trước 29/10 | p95 trước 29/10 | p95 trước 30/10 (3 lượt) | p95 sau (3 lượt) | p99 sau (3 lượt) | p95 sau, không ANALYZE | Số ứng viên (kiểm chứng) | Vi phạm HC | OSRM calls / lượt | Kết luận |
|---|---|---|---|---|---|---|---|---|---|---|
| 50 × 0 | 76 | 160 | 150 / 138 / 142 | 78 / 76 / 55 | 124 / 109 / 82 | 58 | 4.507 | **0** | 2 | ĐẠT |
| 200 × 0 | 92 | 201 | 162 / 193 / 188 | 103 / 112 / 83 | 116 / 133 / 114 | 72 | 9.949 | **0** | 2 | ĐẠT |
| 1.000 × 0 | 103 | 230 | 171 / 158 / 167 | 120 / 129 / 92 | 163 / 158 / 130 | 104 | 10.735 | **0** | 2 | ĐẠT |
| 200 × 10 | 133 | 242 | 297 / 205 / 204 | 168 / 111 / 126 | 220 / 180 / 198 | 101 | 10.105 | **0** | 2 | ĐẠT |
| 200 × 20 | 163 | **516** | 279 / 241 / 228 | **188 / 174 / 168** | 265 / 214 / 222 | 135 | 10.272 | **0** | 2 | **ĐẠT** |
| 1.000 × 20 | 165 | **331** | 281 / 256 / 259 | **185 / 168 / 187** | 266 / 291 / 265 | 170 | 10.543 | **0** | 2 | **ĐẠT** |
| 200 × 20-HC (mới) | — | — | — | 188 (lượt kiểm chứng) | 324 | — | 9.551 | **0** | 2 | ĐẠT p95; p99 > 300 |

Ghi chú:
- Đơn vị ms. p95 / p99 của lượt có kiểm chứng (`final-verify`) nằm trong `result.json` của lượt đó: p95 cao nhất 188 ms (HC).
- Lỗi khi sinh ứng viên: **0** ở mọi lượt.
- CPU / RAM của mọi container được lấy mẫu trong cùng lượt: `docker_stats.jsonl`.
- **p95 cao nhất sau tối ưu: 188,5 ms.**
- p99 vẫn có lượt tới 291 ms (chuẩn) và 324 ms (HC). R9 chỉ đặt chỉ tiêu cho p95; đuôi p99 được ghi nhận là rủi ro.

**p95 theo giai đoạn (trung vị 3 lượt, ms):**

| Giai đoạn | 200×20 trước | 200×20 sau | 1000×20 trước | 1000×20 sau |
|---|---|---|---|---|
| PostGIS tài xế | 18,9 | 11,1 | 48,2 | 28,9 |
| Tra cứu kế hoạch | 31,8 | 34,9 | 25,0 | 29,5 |
| Dữ liệu khách cũ | 18,3 | 19,4 | 13,7 | 19,0 |
| Tham số giá | 6,9 | 0,0 | 6,3 | 0,0 |
| OSRM car | 119,0 | 73,2 | 122,0 | 63,7 |
| OSRM motorbike | 68,6 | 32,3 | 62,9 | 32,2 |
| Chuyển đổi ma trận | 2,7 | 0,7 | 3,3 | 0,7 |
| `check_all` | 7,0 | 4,2 | 6,8 | 4,2 |
| Chèn kế hoạch | 8,2 | 12,4 | 12,0 | 9,9 |
| Bước 3 (chèn + RB + ứng viên) | 44,4 | 37,5 | 47,1 | 38,6 |
| Ghi CSDL | 143,8 | 138,9 | 176,0 | 148,2 |
| **Tổng sinh ứng viên** | **240,3** | **168,5** | **255,4** | **183,8** |

## 5. Tính đúng đắn của 11 ràng buộc cứng (`final-verify`)

Bộ kiểm chứng (`scripts/p2_verify.py`) độc lập với generator:
- SQL riêng; OSRM gọi trực tiếp bằng `/route` và các chặng độc lập.
- Tự tính cửa sổ / ngưỡng / giá từ dòng CSDL.
- Đối chiếu vét cạn với `tests/p2_reference.py` trên một `/table` lấy riêng.

| Chỉ số | Kết quả |
|---|---|
| Ứng viên đã kiểm | **65.662** (7 cấu hình × 200 yêu cầu) |
| Vi phạm theo mã HC | **0** cho mọi mã |
| Ca sát biên (trong dung sai 1 s / 1 m mỗi chặng) | **0** |
| Tài xế đơn bị loại — kiểm lại độc lập | 3.635 lần: **3.635 đúng**, 0 bỏ sót |
| Kế hoạch ghép đã xét — đối chiếu vét cạn | 4.735 lần: 3.913 cả hai không tìm được phương án (`correct`), 822 cùng phương án rẻ nhất (`optimal`), **0** bỏ sót / thừa / lệch chi phí |
| Số lần loại theo mã (cấu hình HC kích hoạt chủ động) | HC03 8.145 · HC05 10.690 · HC06 10.208 · **HC07 5.666** (ngưỡng đi vòng tài xế 3 km / 10 phút, 6 km / 15 phút) · **HC08 2.588** (B_max 90.000 / 150.000 đ) · **HC11 3.301** (khách bật cùng giới) |
| Ứng viên `PENDING_P3` | **822**; qua `offerable()`: **0** |
| Chưa kiểm được độc lập | **HC10**: P2 không có điểm đón gặp nhau (C9) nên `walk_m` luôn 0 — chỉ unit test (SF-P2-18). **HC11** nhánh "cùng giới đã xác thực → được ghép": CSDL chưa cho phép `VERIFIED` (P1-D6) — chỉ unit test (SF-P2-10). **HC09** chỉ ở dạng yêu cầu đúng luật; ca sai luật kiểm bằng unit test |
| Hồi quy thuật toán chèn | 10.000 kịch bản ngẫu nhiên vs bộ tham chiếu + 3.000 kịch bản chứng minh bảng chữ nhật: pass |

## 6. Phân tích bán kính 5 km (OD-P2-05, `final-radius`)

Dữ liệu synthetic. ETA lấy từ một `/table` OSRM độc lập. OSRM **không có dữ liệu kẹt xe** nên tài xế xa trông "kịp" hơn thực tế.

| Thế giới | Yêu cầu có case (a): < 15 tài xế kịp trong 5 km, có người kịp ngoài 5 km | Yêu cầu có case (b): ngoài 5 km có người nhanh hơn người chậm nhất của top-15 |
|---|---|---|
| 200 tài xế | 87 / 200 | 164 / 200 |
| 1.000 tài xế | 31 / 200 | 73 / 200 |

Kết luận: bán kính 5 km và cách chọn top-N theo đường chim bay (§35.1) đều gây bỏ sót. Không đổi tham số; quyết định thuộc Chủ dự án.

## 7. Kết quả kiểm thử cuối (2026-10-31)

| Bộ | Kết quả |
|---|---|
| Toàn bộ backend pytest (gồm test kiến trúc, OSRM thật, Redis thật, 10.000 kịch bản chèn) | **215 passed, 0 failed** |
| Migration | Head `0005`. CSDL tạm head → base → head + `alembic check` sạch (30/10, trước commit `b3412ba`); không có thay đổi model nào sau đó. CSDL chính `0005 (head)` |
| Smoke P0 `--restart-test` (restart toàn stack) | **18/18 PASS** — `evidence/p0_smoke_check_p2_hardening_20261031.json` (tệp mới) |
| Kiểm chứng độc lập + benchmark | §4, §5 |

## 8. Blocker và việc còn mở

**Không còn blocker kỹ thuật** cho hai tiêu chí §79 ở môi trường local.

**Cần Chủ dự án quyết định trước khi nghiệm thu:**
1. **OD-P2-03** — quy tắc cửa sổ hẹn giờ.
2. **OD-P2-05** — bán kính 5 km (§6).
3. **OD-P2-06** — ngữ nghĩa NULL của ngưỡng đi vòng tài xế.
4. **SF-P2-15** — rủi ro quay đầu tại điểm dừng (1,9% ứng viên ghép). Đề xuất: P4 kiểm lại chuỗi đã chọn bằng một `/route` trước khi chào.
5. **SF-P2-02** — ghi nhận diễn giải bảng chữ nhật.

**Rủi ro ghi nhận:**
- Đuôi p99 (tới 291 ms chuẩn, 324 ms HC).
- Giai đoạn ghi CSDL p95 ~120–148 ms chưa rõ nguyên nhân — ảnh hưởng chỉ tiêu E2E 800 ms của P6.
- Hiệu năng máy chủ thật chưa đo (`EXTERNAL_VALIDATION_DEFERRED`).
- SF-06 OPEN.

## 9. Phán quyết nghiệm thu P2

| Điều kiện (chỉ thị §10) | Kết quả |
|---|---|
| 0 vi phạm HC trong phạm vi kiểm chứng đã xác định | **ĐẠT** — 65.662 ứng viên; phạm vi và giới hạn (HC10, HC11 nhánh dương) ghi ở §5 |
| p95 < 300 ms ở toàn bộ cấu hình | **ĐẠT** — p95 cao nhất 188,5 ms (5 lượt sau tối ưu) |
| Không có regression quan trọng | **ĐẠT** — 215 test |
| Migration và API hoạt động | **ĐẠT** |
| Ứng viên `PENDING_P3` bị chặn | **ĐẠT** — 0 / 822 offerable |
| Bằng chứng và báo cáo lưu đủ | **ĐẠT** — `evidence/p2_runs/` |

**Phán quyết:** P2 đạt các tiêu chí kỹ thuật ở mức `LOCAL_VERIFIED` và được **đề xuất** Chủ dự án nghiệm thu (`PHASE_2_READY_FOR_OWNER_ACCEPTANCE`). Báo cáo này **không** tự gán P2 COMPLETE: các quyết định ở §8 thuộc Chủ dự án. Chưa bắt đầu P3.
