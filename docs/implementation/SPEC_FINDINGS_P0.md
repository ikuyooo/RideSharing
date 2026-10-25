# Ghi nhận không nhất quán giữa các tài liệu chuẩn (phát hiện trong Phase 0)

Tài liệu này **không** thay đổi đặc tả. Mọi mục dưới đây cần Chủ dự án xác nhận trước khi
áp dụng vào phần bị ảnh hưởng. Không mục nào chặn Phase 0.

Quy tắc áp dụng tạm thời (theo thứ tự ưu tiên nguồn sự thật): giá trị và tên khóa lấy từ
khối YAML của `MVP_CONFIG_BASELINE_V1.md` §4 (đã sao nguyên văn vào `config/mvp_config_baseline_v1.yaml`).

| ID | Phát hiện | Bằng chứng | Ảnh hưởng | Đề xuất xử lý | Phase bị ảnh hưởng |
|---|---|---|---|---|---|
| SF-01 | Khóa `osrm_table_max_candidates` có trong bảng tham số nhưng **không có** trong khối YAML; YAML lại có `car_urban.n_pool_max_candidates` (cùng giá trị 20). | Baseline §3.1 (nhóm `spatial_and_service_areas`, mã P2-04) vs Baseline §4 / Báo cáo Phụ lục B (`car_urban.n_pool_max_candidates: 20`). | Thấp: cùng giá trị 20, chỉ khác tên/vị trí khóa. Module `routing`/`candidate` cần một tên khóa duy nhất. | Dùng `car_urban.n_pool_max_candidates` (khóa có trong YAML) làm khóa chuẩn; xin xác nhận và, nếu cần, phát hành bản baseline sửa lỗi văn bản. | P2 |
| SF-02 | Phụ lục B của báo cáo còn ghi chú `PROPOSED` cho D-44, D-45a, D-45b và `CLAMP_TO_BASE`, trong khi Decision Register và Baseline ghi `ACCEPTED`. | Báo cáo dòng 3587–3594 vs Register (D-44, D-45a, D-45b `ACCEPTED`) và Baseline §3.3. | Không ảnh hưởng giá trị (giá trị trùng khớp). Chỉ là nhãn chú thích cũ. | Coi trạng thái `ACCEPTED` là chuẩn. | — |
| SF-03 | Phụ lục B thiếu `require_escrow_deposited_before_start`, `escrow_wallet_mode_must`, `calibration_max_ece_threshold` (có trong Baseline YAML). | Báo cáo Phụ lục B vs Baseline §4. | Không xung đột giá trị; Baseline là nguồn chuẩn cho tham số. | Dùng Baseline YAML. | P8, P9 |
| SF-04 | Baseline tham chiếu `REVISION_9_OPEN_ISSUES.md` nhưng tài liệu này không được cung cấp. | Baseline dòng 10. | Không rõ; Baseline §6.1 đã tóm tắt V-01..V-04, EXT-01..03. | Đề nghị bổ sung file vào `docs/pre/` nếu còn nội dung chưa được tóm tắt. | — |
| SF-05 | Đặc tả mô tả xe máy "nhanh hơn ô tô 15–20% trong nội đô giờ cao điểm", nhưng OSRM là định tuyến tốc độ tự do (free-flow) không có khái niệm giờ cao điểm. Bảng tốc độ tạm thời của profile `motorbike` (V-03) cho thời gian xe máy **dài hơn** ô tô trên đường trục ở điều kiện tự do. | Báo cáo Mục 10.1 (dòng 722), Mục 34 (dòng 1907–1909); `infra/osrm/profiles/motorbike.lua`. | Trung bình: ảnh hưởng `T_direct` của `BIKE_URBAN` (định giá theo phút, ràng buộc thời gian, xếp hạng Top-K). | Giữ nguyên trạng thái `NEEDS_VALIDATION (V-03)`. Hiệu chỉnh bằng ~20 cặp điểm Hà Nội trong P0–P2; nếu cần mô hình giờ cao điểm, đề xuất hệ số theo `time_bucket` ở module `routing` (khóa cache đã có `time_bucket`, Mục 34) — cần quyết định trước P2. | P2, P3 |
| SF-06 | Chỉ tiêu P0 "OSRM trả ma trận `< 50 ms`" không nêu kích thước ma trận. | Báo cáo Mục 79, dòng 3369; Mục 34 nêu ~60–100 điểm. | Thấp. | Benchmark báo cáo cả 10/25/50/100 điểm; đánh giá theo p95 ở 100×100 (trường hợp xấu nhất Mục 34). | P0 |
| SF-07 | Thư viện bản đồ frontend: Mục 5 ghi MapLibre, Mục 53 ghi "MapLibre GL / Leaflet". | Báo cáo dòng 486, 2587. | Thấp. | Chọn MapLibre GL (khớp sơ đồ kiến trúc Mục 5) khi dựng frontend ở P6, trừ khi có quyết định khác. | P6 |

---

## Trạng thái xử lý sau audit Phase 0 (2026-10-24)

Bảng trên được giữ nguyên. Mục này chỉ bổ sung trạng thái và bằng chứng; **không có phê duyệt nào của
Chủ dự án được ghi nhận** cho các mục dưới đây.

| ID | Trạng thái | Bằng chứng / việc đã làm | Cần Chủ dự án phê duyệt | Phase đích |
|---|---|---|---|---|
| SF-01 | `PENDING_OWNER_CONFIRMATION_FOR_P2` | YAML khóa không bị sửa (test `test_config_file_matches_locked_document_exactly` PASS). Chưa có module nào đọc khóa này trong P0. | Có — chốt tên khóa chuẩn. | P2 |
| SF-02 | Sai lệch chú thích tài liệu, không phải lỗi runtime | Register + Baseline đều ghi `ACCEPTED`; giá trị trùng khớp. Không sửa tài liệu nguồn. | Tùy chọn — sửa văn bản Phụ lục B khi phát hành bản sau. | — |
| SF-03 | Đã xử lý kỹ thuật (giữ khóa Baseline) | Ba khóa có trong `config/mvp_config_baseline_v1.yaml` (test drift PASS). Không triển khai nghiệp vụ AI/Blockchain. | Không. | P8, P9 |
| SF-04 | `SOURCE_NOT_AVAILABLE` | Tìm `*OPEN_ISSUES*` trong toàn bộ OneDrive: không có. Tiêu chí P0 được đánh giá độc lập theo Mục 79. Giới hạn: không thể xác nhận tệp đó không chứa blocker P0. | Có — cung cấp tệp hoặc xác nhận Baseline §6.1 là đầy đủ. | — |
| SF-05 | `NEEDS_VALIDATION (V-03)` — giữ nguyên | Profile motorbike đã kiểm chứng tránh motorway / `motorcycle=no` bằng đối chiếu cạnh OSM (0/5.073 cạnh vi phạm). Không áp hệ số giờ cao điểm. Thực đo: Phenikaa→Đống Đa car 17,6 phút, motorbike 18,3 phút. Dữ liệu cần thu cho V-03: ~20 cặp OD Hà Nội có thời gian xe máy quan sát được theo khung giờ (nguồn: đo thực địa/GPS trace/dịch vụ bản đồ có giấy phép), ghi kèm thời điểm, thời tiết; so với `/route` của cả hai profile. | Có — chọn hướng mô hình giờ cao điểm (hệ số theo `time_bucket` hay không) trước P2. | P2 (P3 phụ thuộc) |
| SF-06 | `P0_PERFORMANCE_REVIEW_REQUIRED` — **OPEN, không resolved** (giữ trong danh sách rủi ro hiệu năng) | Benchmark 10/25/50/100 điểm × 2 profile × 5 lượt chạy (`docs/implementation/evidence/osrm_bench_*.json`; 2.000 request bảng có đo thời gian, 0 lỗi). Số trường hợp đạt p95 < 50 ms: 10×10 10/10, 25×25 9/10, 50×50 3/10, 100×100 0/10 (p50 62–98 ms, p95 69,6–200,9 ms). Không nới ngưỡng, không đổi thuật toán. *(Bản trước ghi "50×50 dao động quanh ngưỡng"; đã đính chính theo JSON.)* | Đã có quyết định ngày 2026-10-24 (xem dưới). Mọi đề xuất đổi tiêu chí P0 hoặc phần cứng phải trình riêng. | P0 (rủi ro mở), P2 |
| SF-07 | Chuyển P6 | Không có frontend trong P0. | Có (tại P6). | P6 |

### Quyết định của Chủ dự án về SF-06 (2026-10-24)

Đây là quyết định được phê duyệt, không phải kết quả kiểm chứng kỹ thuật.

1. Workload benchmark đại diện là **100×100** (Mục 34); không hạ xuống 25×25.
2. Giữ `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`.
3. Cho phép triển khai P1 dưới dạng **ngoại lệ nghiệm thu P0**.
4. Không đổi Revision 9, Baseline v1, thuật toán CH, ngưỡng hiệu năng.
5. Trước khi nghiệm thu phần sinh ứng viên/ghép xe ở P2: benchmark lại workload thực tế và kiểm tra riêng chỉ tiêu đầu-cuối Mục 77. Đổi tiêu chí P0 hoặc phần cứng phải trình phương án riêng.
6. SF-06 **không** được đánh dấu resolved; SLA **không** được tuyên bố là đạt.

Hệ quả: SF-06 đánh giá ở 100×100 là **chưa đạt** (0/10). Chi tiết ở
`PHASE_0_COMPLETION_REPORT.md` §10.14–10.15.
