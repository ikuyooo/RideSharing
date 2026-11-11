# PHASE 3 — SỔ ĐĂNG KÝ HIỆU CHỈNH SAI LỆCH HỒ SƠ NGHIỆM THU
## (P3_FINAL_CORRECTION_REGISTER)

- **Dự án:** Ride_Sharing
- **Mục đích:** Ghi nhận, phân tích nguyên nhân gốc rễ và xác lập phương án hiệu chỉnh cho toàn bộ các sai lệch, nhầm lẫn và thông tin suy diễn xuất hiện trong các báo cáo kiểm toán trước.
- **Commit thẩm định thực tế:** `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`
- **Thời điểm lập:** 2026-11-10
- **Nguyên tắc:** Mọi kết luận phải dựa trên mã nguồn và Git object thực tế tại `C:\RideSharing`, không dựa trên văn bản tóm tắt hoặc suy đoán.

---

## 1. Bảng Tổng Hợp 15 Sai Lệch Được Hiệu Chỉnh Toàn Diện

| STT | Mã Sai Lệch | Mức độ | Tài liệu Bị Ảnh Hưởng | Nội dung Sai Lệch Cũ | Bằng chứng Thực Tế (Source of Truth) | Trạng thái Hiệu chỉnh |
|---|---|---|---|---|---|---|
| 1 | `ERR-PROV-01` | **CRITICAL** | Các báo cáo kiểm toán phiên trước | Khẳng định commit parent là `2dc3da6...` | Lệnh `git cat-file -p HEAD` xác nhận parent thực tế là `d9a2a324d7a887ceaeff52a82b8a45bcad6d0ea9`. Hash `2dc3da6` không tồn tại trong Git database. | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 2 | `ERR-MOD-02` | **HIGH** | `P3_CANONICAL_SOURCE_INVENTORY.md` | Báo cáo danh mục 12 modules gồm: `admin, candidate, common, driver, fund, geo, passenger, payment, pooling, pricing, routing, shared` | 12 thư mục thực tế tại `backend/app/modules/` là: `booking, candidate, driver, fund, identity, intercity, jobs, ml_models, pooling, pricing, routing, trip`. Thư mục `core/`, `api/`, `db/` nằm trực tiếp dưới `backend/app/`. | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 3 | `ERR-API-03` | **HIGH** | `P3_CANONICAL_SOURCE_INVENTORY.md` | Báo cáo danh sách 26 endpoints gồm các route REST ảo của Pricing/Fund như `/pricing/quote`, `/fund/balance` | 26 endpoints thực tế trong `backend/app/main.py` thuộc về: `health` (2), `identity` (6), `driver` (7), `trip` (2), `candidate` (2), `ml_models` (7). Pricing và Fund ở Phase 3 là thư viện nội bộ, chưa expose REST API ra `main.py`. | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 4 | `ERR-MIG-04` | **HIGH** | `P3_CANONICAL_SOURCE_INVENTORY.md` | Liệt kê tên file migration giả: `0002_p1_indexes...`, `0003_p2_spatial...`, `0004_p2_benchmarks...`, `0005_p2_route_cache...` | 6 migration thực tế trên đĩa: `0001_p1_core_schema.py`, `0002_p1_survey_s1_draft_storage.py`, `0003_p1_service_area_excluded_layer.py`, `0004_p1_survey_s1_duration.py`, `0005_p2_routing_candidate_pooling.py`, `0006_p3_pricing_fund.py`. | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 5 | `ERR-TBL-05` | **CRITICAL** | `P3_ACCEPTANCE_REASSESSMENT.md`, `P3_PHASE4_READINESS.md` | Đề xuất Phase 4 phải tạo mới bảng `bookings`, `seat_holds`, `idempotency_records`, `scheduled_jobs` | Cả 4 bảng này **ĐÃ ĐƯỢC TẠO TỪ PHASE 1** trong migration `0001_p1_core_schema.py` (với `bookings` được bổ sung cột và trigger ở `0006`). Phase 4 chỉ ALTER/bổ sung bảng `driver_offers`. | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 6 | `ERR-TRG-06` | **MEDIUM** | Các báo cáo kiểm toán trước | Đưa vào danh sách triggers không tồn tại như `trg_fund_ledger_chain`, `trg_fund_ledger_append_only` | Schema chỉ có **5 trigger functions** và **6 trigger instances**: 2 trigger trên `pricing_configs` (từ 0001) và 4 trigger tại 0006 (`trg_fund_ledger_guard`, `trg_driver_payouts_immutable`, `trg_ride_participants_frozen`, `trg_bookings_locked_pool_price`). | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 7 | `ERR-TRG-07` | **HIGH** | `P3_CANONICAL_SOURCE_INVENTORY.md` | Tuyên bố `fund_ledger_guard` nghiêm cấm tuyệt đối mọi thao tác UPDATE | Code SQL trong `0006:52-56` cho phép UPDATE duy nhất cột `onchain_tx_hash` từ NULL thành NOT NULL phục vụ Phase 9 Blockchain Audit. | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 8 | `ERR-MTH-08` | **HIGH** | Các báo cáo kiểm toán cũ | Ghi công thức Gate 1 là $C_{\text{plan}} \le \sum P_i$ | Code thực tế tại `pool.py:128` là `fare <= (1 - p.d_min) * sum(privates)` ($C_{\text{plan}} \le 0.80 \times \sum P_i$). | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 9 | `ERR-MTH-09` | **MEDIUM** | Các báo cáo kiểm toán cũ | Ghi hệ số ghế `seat_factor` nằm ở tử số của trọng số phân bổ $w_i$ | Code thực tế tại `pool.py:109` là `r.private_fare * (...) / seat_factor(p, r.seats)` (nằm ở **mẫu số**). | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 10 | `ERR-MTH-10` | **HIGH** | Các báo cáo kiểm toán trước | Mô tả đơn giản hóa $\text{Floor}_i = 0.60 \times P_i$ | Code thực tế tại `pool.py:116-210`: `raw_floor = max(base_vnd, P_i * (1 - d_max) * seat_factor)` và `floor_i = min(cap_i, raw_floor)`. Có xét giá sàn cơ sở và hệ số ghế. | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 11 | `ERR-SF-11` | **CRITICAL** | `P3_SPEC_FINDINGS_RECONCILIATION.md`, `P3_ACCEPTANCE_REASSESSMENT.md` | Gán nhầm `SF-P3-05` thành lỗi "thiếu unique constraint `(ride_id, dropoff_order)`" | `SPEC_FINDINGS_P3.md:22` xác nhận `SF-P3-05` là: Tham số `cancellation_policy` và vốn mồi Quỹ trong Baseline YAML không nằm trong bảng `pricing_configs`, thiếu khóa YAML cho tỷ lệ chia phí hủy. Vấn đề ràng buộc dropoff là một Technical Finding mới. | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 12 | `ERR-SF-12` | **CRITICAL** | `P3_ACCEPTANCE_REASSESSMENT.md`, `P3_OWNER_DECISION_REGISTER.md` | Tuyên bố "Current Implementation cho phép ghi sổ âm + `pending_reconciliation`" | Mã nguồn thực tế tại `fund/service.py:75` ném `FundInsufficient` khi số dư không đủ; migration `0006` có CHECK constraint `balance_after_vnd >= 0`. Không có chuỗi ký tự `pending_reconciliation` trong code. | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 13 | `ERR-SF-13` | **HIGH** | Các báo cáo kiểm toán trước | Diễn giải `SF-P3-16` là lỗi báo giá khách đặt 2 ghế | `SPEC_FINDINGS_P3.md:32` xác nhận `SF-P3-16` là Gate 2B loại phương án ghép khi thời gian lấy từ OSRM tốc độ cao (45-52 km/h). Báo giá 2 ghế hoàn toàn chính xác ($174.000 < 194.000$). | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 14 | `ERR-TST-14` | **HIGH** | Các báo cáo kiểm toán cũ | Báo cáo số lượng test là 135 bài test | AST phân tích `backend/tests/` xác nhận có **210 hàm test định nghĩa (`def test_*`)**, mở rộng thành **291 pytest items** (theo collection lịch sử). | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |
| 15 | `ERR-BNC-15` | **MEDIUM** | `P3_TEST_EVIDENCE_RECONCILIATION.md` | Mô tả 64.698 ứng viên benchmark được sinh ra từ duy nhất một kịch bản 1000x20 | File `result.json` tại `20261105T054653Z-p3-integrated-verify` chứng minh 64.698 ứng viên là tổng hợp từ **7 kịch bản kiểm thử độc lập** (mỗi kịch bản 200 requests: `50x0`, `200x0`, `1000x0`, `200x10`, `200x20`, `1000x20`, `200x20-hc`). | **ĐÃ HIỆU CHỈNH TRIỆT ĐỂ** |

---

## 2. Nguyên Nhân Gốc Rễ Của Chuỗi Sai Lệch

1. **Hiệu ứng Lan truyền Ảo giác Ngữ cảnh (Context Summary Contamination):**
   Trong các phiên làm việc trước, bản tóm tắt tự động `<CONTEXT_SUMMARY>` được tạo ra chứa các thông tin suy diễn (parent `2dc3da6`, 14 modules, 135 tests, Gate 1 $C \le \sum P$). Agent ở lượt tiếp theo đã tin tưởng bản tóm tắt mà không thực hiện kiểm tra chéo với filesystem thực tế.
2. **Thiếu Đối chiếu Trực tiếp với File Định nghĩa Gốc:**
   Thay vì đọc trực tiếp file gốc `SPEC_FINDINGS_P3.md`, các báo cáo trung gian đã tự diễn dịch ý nghĩa của các mã finding (như `SF-P3-05` và `SF-P3-16`) dẫn đến việc gán sai lệch hoàn toàn bản chất kỹ thuật của vấn đề.
3. **Đánh đồng Giữa Đề xuất và Hiện thực:**
   Ý tưởng đề xuất xử lý số dư Quỹ âm (`pending_reconciliation`) đã bị báo cáo cũ ghi nhầm thành "Current Implementation", trong khi code thực tế bảo vệ nghiêm ngặt số dư không âm bằng ngoại lệ và DB CHECK constraint.

---

## 3. Danh Mục Các Báo Cáo Cũ Bị Thay Thế (SUPERSEDED)

Các tài liệu sau đây được đánh dấu là **`SUPERSEDED` (ĐÃ BỊ THAY THẾ)** và không còn giá trị pháp lý nghiệm thu:
1. `docs/implementation/P3_FINAL_VERIFICATION_REPORT.md` (Chứa parent ảo, 14 modules).
2. `docs/implementation/P3_SYSTEM_ARCHITECTURE_INVENTORY.md` (Chứa routes Pricing ảo, module sai).
3. `docs/implementation/P3_TECHNICAL_EVIDENCE_DOSSIER.md` (Chứa số liệu test và benchmark không chính xác).
4. `docs/implementation/P3_DESIGN_DECISION_AND_SPEC_FINDING_REGISTER.md` (Gán sai SF-P3-05, SF-P3-16).
5. `docs/implementation/P3_OUTSTANDING_TECHNICAL_DEBT.md` (Mô tả sai nợ kỹ thuật).
6. `docs/implementation/P3_PHASE4_READINESS_ASSESSMENT.md` (Đề xuất tạo lại bảng Phase 1).
7. `docs/implementation/P3_ACCEPTANCE_RECOMMENDATION.md` (Đánh giá trên dữ liệu sai lệch).
8. `docs/implementation/P3_ACCEPTANCE_ASSESSMENT.md` (Chứa các giả định sai của phiên trước).
9. `docs/implementation/P3_ACCEPTANCE_REASSESSMENT.md` (Bản thảo chưa cập nhật các kiểm kê trực tiếp).

**Phiên bản có hiệu lực duy nhất là bộ 7 tài liệu được chuẩn hóa tại phiên này (từ `P3_FINAL_CORRECTION_REGISTER.md` đến `P3_FINAL_ACCEPTANCE_ASSESSMENT.md`).**

