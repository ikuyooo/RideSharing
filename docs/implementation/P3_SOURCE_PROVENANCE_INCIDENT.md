# BÁO CÁO ĐIỀU TRA SỰ CỐ NGUỒN GỐC MÃ NGUỒN (SOURCE PROVENANCE INCIDENT REPORT)

- **Dự án**: `Ride_Sharing`
- **Ngày điều tra**: `2026-11-09`
- **Thư mục làm việc thực tế**: `C:\RideSharing` (`C:/RideSharing`)
- **Commit HEAD thực tế**: `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`
- **Commit Parent thực tế (`HEAD^`)**: `d9a2a324d7a887ceaeff52a82b8a45bcad6d0ea9`
- **Tree SHA thực tế (`HEAD^{tree}`)**: `2126a22d634e455e28bddf47d0d5fbf699fcc640`
- **Trạng thái đối tượng kiểm toán**: `C:\RideSharing` tại `HEAD = f97a5092ece737d70051d08e6e3604e6a0c6bd1d` **khớp 100%** với bản nén `RideSharing.zip` đã được kiểm tra độc lập trước đó.

---

## 1. Tóm tắt điều hành (Executive Summary)

Báo cáo này điều tra nguyên nhân vì sao 7 tài liệu nghiệm thu Phase 3 được sinh ra ở phiên trước (`P3_SOURCE_BASELINE_VERIFICATION.md`, `P3_CODE_AUDIT_CORRECTIONS.md`, `P3_REQUIREMENT_TRACEABILITY.md`, `P3_TEST_AND_BENCHMARK_VERIFICATION.md`, `P3_OWNER_DECISION_REGISTER.md`, `P3_ACCEPTANCE_ASSESSMENT.md`, `P3_PHASE4_READINESS.md`) lại ghi nhận cùng commit SHA `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` nhưng mô tả một lịch sử commit cha khác (`2dc3da6`), số lượng module khác (`14` thay vì `12`), danh sách migration khác, số lượng test khác (`135` thay vì `23 files / 210 defs / 291 pytest items`), công thức toán học sai lệch (`Gate 1`, `weight()`, `Unmatched_i`), và nội dung `SF-P3-02`, `SF-P3-10`, `SF-P3-16` hoàn toàn sai khác so với file `docs/implementation/SPEC_FINDINGS_P3.md` thực tế trên đĩa.

**Kết luận pháp chứng (Forensic Verdict)**:
1. **Không hề tồn tại repository thứ hai trên máy chủ và không có xung đột SHA-1.** Chỉ có **một repository duy nhất** tại `C:\RideSharing`, và nội dung Git object/tree của nó trùng khớp tuyệt đối với bản `RideSharing.zip`.
2. **Nguyên nhân gốc rễ là sự cố nhiễm bẩn bản tóm tắt ngữ cảnh tự động (`<CONTEXT_SUMMARY>` Hallucination / Context Compaction Contamination)**:
   - Vào lúc `2026-11-09T19:07:21+07:00`, khi cửa sổ ngữ cảnh (context window) đầy và được nén tự động thành khối `<CONTEXT_SUMMARY>`, bộ tóm tắt đã ghi nhận sai rằng toàn bộ các file mã nguồn đã được đọc (`read_file — 100% read`) đồng thời **tự suy diễn/bịa đặt (hallucinate)** các chi tiết cụ thể bên trong (như parent SHA `2dc3da69a2df644280e16859b47152fa7236f99b`, 14 module có `matching`/`dispatch`/`blockchain`, công thức `Gate 1` không nhân `(1 - d_min)`, `SeatFactor` ở tử số của `w_i`, và nội dung giả định của `SF-P3-02`, `SF-P3-10`, `SF-P3-16`).
   - Ngay sau bước nén ngữ cảnh đó, tác tử ở lượt tiếp theo đã **tin tưởng vào `<CONTEXT_SUMMARY>` mà không đọc lại file thực tế trên đĩa (`read_file`)**, dẫn đến việc chép nguyên các chi tiết sai lệch từ `<CONTEXT_SUMMARY>` vào 7 tài liệu nghiệm thu Phase 3.

---

## 2. Bằng chứng Pháp chứng Git trực tiếp (Direct Git Forensics Evidence)

### 2.1. Định danh Repository và Git Objects thực tế

Kết quả chạy lệnh trực tiếp trên `C:\RideSharing`:

| Lệnh kiểm tra | Kết quả thực tế |
|---|---|
| `Get-Location` | `C:\RideSharing` |
| `git rev-parse --show-toplevel` | `C:/RideSharing` |
| `git rev-parse --is-inside-work-tree` | `true` |
| `git rev-parse --show-object-format` | `sha1` |
| `git remote -v` | `origin https://github.com/ikuyooo/Ride_Sharing.git (fetch / push)` |
| `git branch -vv` | `* main f97a509 [origin/main] update` |
| `git rev-parse HEAD` | `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` |
| `git rev-parse HEAD^` | `d9a2a324d7a887ceaeff52a82b8a45bcad6d0ea9` |
| `git rev-parse HEAD^{tree}` | `2126a22d634e455e28bddf47d0d5fbf699fcc640` |
| `git ls-tree -r --name-only HEAD` | `463` files |
| `git ls-files` | `463` files |
| `git diff --name-status HEAD` | *(Rỗng — `0` file tracked bị sửa đổi)* |

### 2.2. Nội dung `git cat-file -p HEAD` nguyên bản

```text
tree 2126a22d634e455e28bddf47d0d5fbf699fcc640
parent d9a2a324d7a887ceaeff52a82b8a45bcad6d0ea9
author ikuyooo <konghieeus2307@gmail.com> 1793898277 +0700
committer ikuyooo <konghieeus2307@gmail.com> 1793898277 +0700

update
```

### 2.3. Lịch sử 10 Commit gần nhất (`git log -10 --format="%H | %P | %ad | %s" --date=iso-strict`)

| STT | Commit SHA (`%H`) | Parent SHA (`%P`) | Thời gian (`%ad`) | Thông điệp (`%s`) |
|---|---|---|---|---|
| 1 | `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` | `d9a2a324d7a887ceaeff52a82b8a45bcad6d0ea9` | `2026-11-06T00:04:37+07:00` | `update` |
| 2 | `d9a2a324d7a887ceaeff52a82b8a45bcad6d0ea9` | `a1927de6398708fc665f20b9f9659e65215151fa` | `2026-11-05T00:45:42+07:00` | `docs(p2): local acceptance record with three-scope evidence from a fixed worktree` |
| 3 | `a1927de6398708fc665f20b9f9659e65215151fa` | `a04873292e7f25308400f34d0fbfcb5cc8c86132` | `2026-11-05T00:29:37+07:00` | `docs(p2): record owner acceptance decisions; add three-scope latency instrumentation` |
| 4 | `a04873292e7f25308400f34d0fbfcb5cc8c86132` | `b3412ba2ce7f836607145345ded0b06250e41d8f` | `2026-10-31T00:23:10+07:00` | `perf(p2): profile-driven hardening of candidate generation; independent HC verification` |
| 5 | `b3412ba2ce7f836607145345ded0b06250e41d8f` | `c68e8812e315ff4a167d7cf470974efb4094a178` | `2026-10-30T21:40:27+07:00` | `feat(p2): implement routing candidate filtering and active pooling insertion` |
| 6 | `c68e8812e315ff4a167d7cf470974efb4094a178` | `b1002a4b35d4f5b4166ac1e0b5040284f37d8bf5` | `2026-10-28T13:04:27+07:00` | `feat(p1): v5 approved for MVP via gates, survey design validation, HTTPS staging (P1 still in progress)` |
| 7 | `b1002a4b35d4f5b4166ac1e0b5040284f37d8bf5` | `5a895ba258331b95f06f9f54a4eb3fb937570c5e` | `2026-10-28T02:03:33+07:00` | `feat(p1): hardening - v4 candidate, ferry policy, survey draft 3 (P1 still in progress)` |
| 8 | `5a895ba258331b95f06f9f54a4eb3fb937570c5e` | `1d62e1f802d5e983afaaa90a132365353eb36bb1` | `2026-10-27T19:35:36+07:00` | `feat(p1): final-closure geography (v3 candidate) and survey S1 draft 2 (P1 still in progress)` |
| 9 | `1d62e1f802d5e983afaaa90a132365353eb36bb1` | `9d0f8d05c73feb740b0eb9aaa002d2c3a845e3b0` | `2026-10-26T01:29:46+07:00` | `feat(p1): geography decisions A1-A9 and draft survey S1 (P1 in progress)` |
| 10 | `9d0f8d05c73feb740b0eb9aaa002d2c3a845e3b0` | `c4051ed7a8edd15602616c542b2ba9155b28fe85` | `2026-10-26T00:39:52+07:00` | `feat(p1): implement verified core modules and draft service area` |

> [!IMPORTANT]
> Commit SHA `2dc3da69a2df644280e16859b47152fa7236f99b` được nêu trong `P3_SOURCE_BASELINE_VERIFICATION.md` **hoàn toàn không tồn tại** trong lịch sử Git của `C:\RideSharing`.

---

## 3. Phân tích 5 Giả thuyết bắt buộc (Mandatory Hypotheses Evaluation)

| Giả thuyết | Đánh giá | Bằng chứng xác minh |
|---|---|---|
| **H1. Đang đọc một bản sao repository khác ở thư mục khác** | **BÁC BỎ (`FALSE`)** | `Get-Location` và `git rev-parse --show-toplevel` đều trả về `C:\RideSharing`. Mọi file trong `C:\RideSharing` thuộc đúng `tree 2126a22d634e455e28bddf47d0d5fbf699fcc640`, khớp 100% với `RideSharing.zip`. |
| **H2. Lịch sử Git đã bị rewrite, rebase, force-push hoặc graft** | **BÁC BỎ (`FALSE`)** | Trong Git (SHA-1), mã băm của một commit (`f97a5092ece737d70051d08e6e3604e6a0c6bd1d`) được tính trực tiếp từ chuỗi byte chứa `tree`, `parent`, `author`, `committer` và `message`. Về mặt mật mã học, không thể có hai commit có cùng SHA-1 `f97a5092ece...` nhưng khác `parent` (`d9a2a32...` vs `2dc3da6...`) hoặc khác `tree`. Do đó, không hề có việc rewrite/rebase tạo ra commit thứ hai cùng SHA. |
| **H3. Working tree có thay đổi chưa commit hoặc đang ở branch/worktree khác** | **BÁC BỎ (`FALSE`)** | `git status --short --branch` xác nhận đang ở `main...origin/main`, `git diff --name-status HEAD` có `0` file tracked thay đổi. Lý do `docs/implementation/P3_PROGRESS_REPORT.md:5` ghi *"Mã P3 chưa được commit"* là vì báo cáo đó được viết ngay trước khi tác giả chạy `git commit -m "update"` tạo ra commit `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` (đưa toàn bộ file P3 vào Git). |
| **H4. Báo cáo trước đã suy diễn từ tài liệu cũ hoặc từ ngữ cảnh không khớp mà không kiểm tra trực tiếp từng file** | **XÁC NHẬN (`CONFIRMED — PRIMARY ROOT CAUSE`)** | Khi cửa sổ ngữ cảnh bị nén lúc `2026-11-09T19:07:21+07:00`, khối `<CONTEXT_SUMMARY>` đã tóm tắt sai và tự sinh ra các chi tiết không có thật. Ở lượt kế tiếp, tác tử đã đọc `<CONTEXT_SUMMARY>` thay vì gọi `read_file` trên đĩa để kiểm tra lại `SPEC_FINDINGS_P3.md`, `pool.py`, `tariff.py`, `settlement.py`, `cancellation.py`, và `git log`. |
| **H5. Có nhiều thư mục/phiên bản RideSharing trên máy và đã mở nhầm** | **BÁC BỎ (`FALSE`)** | Không có thư mục RideSharing thứ hai nào chứa 14 module hay parent `2dc3da6`. Toàn bộ mâu thuẫn chỉ tồn tại trong văn bản của `<CONTEXT_SUMMARY>` và 7 file `.md` được viết từ `<CONTEXT_SUMMARY>` đó. |

---

## 4. Bảng đối chiếu toàn diện giữa Báo cáo cũ (Sai lệch), Báo cáo mới (Phiên trước — Nhiễm `<CONTEXT_SUMMARY>`) và Source Code Thực tế (`C:\RideSharing`)

| Hạng mục | Báo cáo kiểm toán đầu tiên (Audit #1) | Bộ 7 báo cáo nghiệm thu phiên trước (Nhiễm `<CONTEXT_SUMMARY>`) | Source Code Thực tế tại `C:\RideSharing` (`HEAD = f97a5092...`) | Kết luận |
|---|---|---|---|---|
| **Commit HEAD SHA** | `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` | `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` | `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` | Cùng HEAD SHA |
| **Commit Parent SHA (`HEAD^`)** | `d9a2a324d7a887ceaeff52a82b8a45bcad6d0ea9` | `2dc3da69a2df644280e16859b47152fa7236f99b` *(Bịa đặt)* | `d9a2a324d7a887ceaeff52a82b8a45bcad6d0ea9` (`tree 2126a22d...`) | Báo cáo phiên trước sai |
| **Trạng thái commit mã P3** | Ghi nhận theo `P3_PROGRESS_REPORT.md` rằng P3 chưa commit | Ghi nhận P3 đã commit trong `f97a509` nhưng gắn sai message/parent | Mã P3 **đã được commit** trong `f97a509` (`update`); câu *"Mã P3 chưa được commit"* trong `P3_PROGRESS_REPORT.md:5` là câu viết trước lúc tạo commit `f97a509` | Đã làm rõ cả 2 phía |
| **Số lượng module trong `backend/app/modules/`** | `12` modules | `14` modules (thêm `matching`, `dispatch`, `blockchain`, bỏ `candidate`, `pooling`) | **Đúng `12` modules**: `booking`, `candidate`, `driver`, `fund`, `identity`, `intercity`, `jobs`, `ml_models`, `pooling`, `pricing`, `routing`, `trip` | Báo cáo phiên trước sai |
| **Danh sách Migration (`backend/alembic/versions/`)** | `6` files (`0001`..`0006`) | `6` files nhưng đổi tên sai `0002`..`0005` (`0002_p1_trip_and_service_area.py`, v.v.) | **Đúng `6` files**: `0001_p1_core_schema.py`, `0002_p1_survey_s1_draft_storage.py`, `0003_p1_service_area_excluded_layer.py`, `0004_p1_survey_s1_duration.py`, `0005_p2_routing_candidate_pooling.py`, `0006_p3_pricing_fund.py` | Báo cáo phiên trước sai tên file |
| **Số lượng file test và bài kiểm thử** | `23` files, `291` pytest items (`290 + 1 Hypothesis`) | `22` files, `135` test functions | **`23` files `test_*.py`**, chứa **`210` hàm `def test_*`**, mở rộng qua `@pytest.mark.parametrize` thành đúng **`291` pytest items** (`290` chuẩn + `1` Hypothesis 10.000 mẫu) | Đã đối soát khớp tuyệt đối (`210 + 81 = 291`) |
| **Công thức Gate 1 (`pricing/pool.py:128-129`)** | `PlanFare <= (1 - d_min) * sum(P_i)` | `C_plan <= sum(P_i)` (thiếu `1 - d_min = 0.80`) | `fare <= (1 - p.d_min) * sum(privates)` (`PlanFare <= 0.80 * sum(P_i)`) | Báo cáo phiên trước sai |
| **Công thức Trọng số `weight()` (`pricing/pool.py:108-110`)** | Chia cho `seat_factor(p, r.seats)` | Nhân với `SeatFactor` ở tử số | `r.private_fare * (1 + p.lam * r.detour + p.mu * r.walk_ratio) / seat_factor(p, r.seats)` (**`seat_factor` ở mẫu số**) | Báo cáo phiên trước sai |
| **Giá `Quote_i` và `Unmatched_i` cho 2 ghế (`tariff.py:61-73`)** | Giữ nguyên `P_i = PrivateFare(i)` theo `D-45b`, `Unmatched_A = 174.000 < 194.000` | Tuyên bố `pool_quote_for` nhân `SeatFactor = 1.35` làm `Unmatched = 234.000 > 194.000` | `pool_quote_for(p, private)` dùng trực tiếp `private` (`P_i`), **không nhân `seat_factor`**. Với `P_A = 194.000` (`seats=2`), `Quote = 155.000`, `Unmatched = 174.000 < 194.000` (`test_pricing_regression.py:152`) | Báo cáo phiên trước bịa đặt lỗi không tồn tại |
| **Nội dung `SF-P3-02`, `SF-P3-10`, `SF-P3-16`** | Khớp `docs/implementation/SPEC_FINDINGS_P3.md` | Gán sai hoàn toàn ý nghĩa của cả 3 mã finding | `SF-P3-02`: Định nghĩa `T_plan` (`plan_extent`); `SF-P3-10`: Xử lý khi Quỹ bảo đảm không đủ số dư (`FundInsufficient`); `SF-P3-16`: Gate 2B (`eps_hourly = 0`) loại gần hết chuyến ghép khi dùng tốc độ OSRM free-flow (`45–52 km/h`) | Đã khôi phục nguyên văn từ `SPEC_FINDINGS_P3.md` |
| **Phạm vi Phase 4 theo Revision 9 Mục 79** | Module `booking`, `ride`, `jobs`, `Offer Cascade`, `Per-Offer Seat Hold`, `Idempotency-Key`, `pool_lock_point` | Đưa nhầm `intercity` (P5), `Top-K` (P6) và `batch_matcher` (P10) vào Phase 4 | **Mục 79 (dòng 3373)**: Phase 4 gồm `booking`, `ride`, `jobs` (`SELECT ... FOR UPDATE SKIP LOCKED`), máy trạng thái trực giao (`ride_status`, `price_status`), `Offer Cascade` với `Per-Offer Seat Hold`, `Idempotency-Key` và `pool_lock_point`. (`intercity` là P5; `Top-K` + Web Workbench là P6; `batch_matcher` CP-SAT là P10) | Đã hiệu chỉnh đúng theo Mục 79 |

---

## 5. Biện pháp Khắc phục và Quản trị Hồ sơ (Remediation Governance)

1. **Giữ nguyên hiện trạng**: Không xóa và không ghi đè 7 file đã tạo ở phiên trước để lưu vết kiểm toán đầy đủ.
2. **Đánh dấu hiệu lực (`SUPERSEDED`)**: Toàn bộ 7 file của phiên trước (`P3_SOURCE_BASELINE_VERIFICATION.md`, `P3_CODE_AUDIT_CORRECTIONS.md`, `P3_REQUIREMENT_TRACEABILITY.md`, `P3_TEST_AND_BENCHMARK_VERIFICATION.md`, `P3_OWNER_DECISION_REGISTER.md`, `P3_ACCEPTANCE_ASSESSMENT.md`, `P3_PHASE4_READINESS.md`) chính thức bị **thay thế hoàn toàn (`SUPERSEDED`)** bởi bộ 7 hồ sơ hiệu chỉnh mới (`P3_SOURCE_PROVENANCE_INCIDENT.md`, `P3_CANONICAL_SOURCE_INVENTORY.md`, `P3_PRICING_AND_FUND_RECONCILIATION.md`, `P3_SPEC_FINDINGS_RECONCILIATION.md`, `P3_TEST_EVIDENCE_RECONCILIATION.md`, `P3_PHASE4_READINESS_CORRECTED.md`, `P3_ACCEPTANCE_REASSESSMENT.md`).
3. **Quy tắc chống tái diễn**: Mọi số liệu, tên hàm, công thức và mã Finding trong bộ hồ sơ mới đều được trích xuất trực tiếp từ file thật trên đĩa tại commit `f97a5092ece737d70051d08e6e3604e6a0c6bd1d` (`tree 2126a22d634e455e28bddf47d0d5fbf699fcc640`).

