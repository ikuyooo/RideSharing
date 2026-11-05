# PHASE 3 — BÁO CÁO TIẾN ĐỘ (pricing · fund)

- **Cập nhật:** 2026-11-05 (bổ sung kết quả benchmark a4–a6 + kiểm chứng).
- **Trạng thái P3: `PHASE_3_IN_PROGRESS` — chưa đủ điều kiện tạo `PHASE_3_COMPLETION_REPORT.md`.** Lý do ở §5.
- **Mã P3 chưa được commit.** Chỉ thị chỉ cho phép commit hồ sơ khóa P2 (`a1927de`, `d9a2a32`). Toàn bộ thay đổi P3 nằm trong working tree, chờ Chủ dự án cho phép commit.
- Revision 9 và Baseline v1 không bị sửa. Không push remote.
- Hồ sơ liên quan: `P3_IMPLEMENTATION_PLAN.md`, `P3_DESIGN_DECISIONS.md`, `SPEC_FINDINGS_P3.md`.

**Ý nghĩa các trạng thái:** `IMPLEMENTED` (đã có mã) · `LOCAL_VERIFIED` (đã kiểm bằng test / chạy local, có bằng chứng) · `REPORTED` (đã báo cáo phát hiện, chờ quyết định) · `DEFERRED` (thuộc phase sau) · `FAILED` (không đạt).

## 1. Hạng mục bắt buộc (chỉ thị mục IV)

| # | Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1 | Biểu giá 5 dịch vụ | `LOCAL_VERIFIED` | `tariff.py`; `test_72_1_fixed_fares`, `test_10_4_…`, `test_71_1_vector_1…` |
| 2 | `PlanFare` | `LOCAL_VERIFIED` | `pool.plan_fare`; vector 1 (248.500), vector 4 (288.500) |
| 3 | Cổng 1 | `LOCAL_VERIFIED` | `test_gate1_boundary_is_inclusive`, `test_gate1_rejects…` |
| 4 | Phân bổ theo trọng số bất tiện | `LOCAL_VERIFIED` | vector 1, 3C; Hypothesis bất biến 4–5 |
| 5 | `Floor_i` / `Cap_i` | `LOCAL_VERIFIED` | vector 3A; `test_floor_cap_and_seat_factor`; Hypothesis bất biến 2 |
| 6 | Vô nghiệm (`REJECT`; `CLAMP_TO_BASE` chỉ khi cấu hình) | `LOCAL_VERIFIED` | vector 3B; `test_allocation_feasibility_conditions`; `test_d3…`, `test_d4…` |
| 7 | Làm tròn VND | `LOCAL_VERIFIED` | `test_rounding_never_rounds_up`; Hypothesis bất biến 3; §17.2 (`Σ charged + Σ rounding = PlanFare`) |
| 8 | Bảo vệ giá khách đã khóa (D1–D6) | `LOCAL_VERIFIED` | vector 4; `test_d1…` → `test_d6…`; Hypothesis G08 (1.244 lần chèn có khách khóa); trigger CSDL `test_frozen_participant_and_locked_booking_cannot_change` |
| 9 | Cổng 2A / 2B | `LOCAL_VERIFIED` (kèm `REPORTED` SF-P3-16) | `test_gate2a_payout_and_2b_hourly_rate_boundaries`; Hypothesis bất biến 6 |
| 10 | Quote, Unmatched, GuaranteePayout | `LOCAL_VERIFIED` | vector 2; `test_19_2…`; Hypothesis bất biến 3, 6 |
| 11 | Sổ cái Quỹ và payout | `LOCAL_VERIFIED` | `test_settlements_write_payout_and_fund_entries_and_reconcile`, `test_ledger_is_append_only_and_chained`, `test_guarantee_never_drives_the_fund_negative`, `test_payouts_are_immutable_and_must_add_up` |
| 12 | Phí hủy §18.7 | `LOCAL_VERIFIED` (diễn giải SF-P3-05..07 `REPORTED`) | `tests/test_pricing_cancellation.py` (mọi dòng bảng, biên thời gian); `test_cancellation_fee_flows_to_the_fund` |
| 13 | Tích hợp `PoolPricingCheck` | `LOCAL_VERIFIED` | `test_branch_a_with_traffic_speeds_is_priced_complete` (COMPLETE, offerable), `test_branch_a_inserts_into_a_running_vehicle` (OSRM thật: loại với mã chính xác), `test_branch_a_plan_without_pricing_state…` |
| — | Đồng bộ blockchain | `DEFERRED` (P9) | Chỉ có giao diện `fund/chain.py`; không giả lập giao dịch |
| — | Hình học `DoorSurcharge`, vòng đời liên tỉnh | `DEFERRED` (P5) | Công thức tất định đã có và được test |

## 2. Kiểm thử (chỉ thị mục V)

| # | Yêu cầu | Kết quả |
|---|---|---|
| 1–9 | Biểu giá, Floor / Cap, vô nghiệm, rounding, khách đã khóa, hourly rate, quỹ / payout, hủy, tích hợp | Đạt — §1 |
| 10 | Kịch bản chuẩn §16.1–16.3 | Đạt **từng giá trị**; riêng 2 số trung gian in trong §16.3 lệch công thức → SF-P3-01 (đầu ra bắt buộc vẫn khớp) |
| 11 | Hồi quy cố định §71–72 | Đạt: 4 vector §71.1 (mọi nhánh 3A / 3B / 3C) và §72.1 |
| 12 | ≥ 10.000 mẫu Hypothesis | **10.000 mẫu**, deterministic (`derandomize`), đếm mẫu và đòi hỏi đủ mọi nhánh: phân bổ được 7.643, vô nghiệm cận dưới 1.176, cận trên 1.181, kế hoạch qua mọi cổng 2.352, chèn động có khách khóa 1.244. Mỗi mẫu so với **bộ giải tham chiếu độc lập** (liệt kê tập hoạt động). Bất biến 1 kiểm bằng **đẳng thức chính xác** |

**Toàn bộ test (P1 + P2 + P3):** 290 passed + test Hypothesis 1 passed (chạy riêng 99 s) = **291 passed, 0 failed**. Gồm cả 10.000 kịch bản chèn của P2, nay so `ΔCost` với bộ tham chiếu đã thống nhất `T_plan` (DD-P3-04).

**Trong quá trình kiểm thử phát hiện và sửa:**
- Bộ giải tham chiếu ban đầu của test Hypothesis chấp nhận một nghiệm "mọi khách đều chạm biên" không nhất quán với một τ duy nhất (lỗi của **test**, không phải của thuật toán; Hypothesis tìm ra với 2 khách giống hệt). Đã sửa test.
- Test hồi quy §16.1 phương pháp tỷ lệ: R9 in 147.428 đ (làm tròn tới đồng), test ban đầu đoán sai phần thập phân. Đã sửa test cho khớp R9.

**CSDL / hạ tầng:**
- Migration 0006 đã áp lên CSDL local (`alembic_version = 0006`). `alembic check` trên CSDL trống chỉ có PostGIS: **sạch**; downgrade 0006 → 0005 → upgrade: sạch. (`alembic check` trên CSDL chính báo các bảng `postgis_tiger_geocoder` / `postgis_topology` do image PostGIS tạo — không thuộc ứng dụng.)
- Smoke P0 `--restart-test`: **18/18 PASS** — `evidence/p0_smoke_check_p3_20261105.json`.
- Image backend được build lại để dịch vụ đang chạy khớp schema 0006.

## 3. Hiệu năng và kiểm chứng sau khi tích hợp P3

Đo trên worktree tại `d9a2a32` + đúng diff P3 chưa commit (mã giống hệt working tree, chỉ khác ký tự xuống dòng; `SNAPSHOT.md` ghi sha256). `git_dirty_files` 33–39 là chính diff P3 và các thư mục bằng chứng của lượt trước. Bằng chứng: `evidence/p3_runs/`.

| Lượt | Tình trạng |
|---|---|
| `p3-integrated-a1` (04/11) | Hợp lệ (tham khảo) |
| `p3-integrated-a2`, `-a3` (04/11) | `DISTURBED` / `INTERRUPTED` — host suspend |
| **`p3-integrated-a4`, `-a5`, `-a6` (05/11)** | **Hợp lệ — 3 lượt liên tiếp, không có khoảng trống trong `docker_stats.jsonl`** |
| `p3-integrated-verify` (05/11) | Kiểm chứng **hợp lệ**; độ trễ **không hợp lệ** (host suspend 06:15–06:48Z, `LATENCY_DISTURBED.md`) |

**Ba phạm vi đo, p95 từng lượt a4 / a5 / a6 (ms):**

| Workload | PostGIS + OSRM Table | Trước persist (§79 < 300) | + persist | p99 trước persist | Tra trạng thái giá kế hoạch | Lỗi |
|---|---|---|---|---|---|---|
| 50 × 0 | 55,9 / 33,7 / 41,0 | 63,7 / 44,4 / 50,9 | 122,2 / 108,1 / 103,3 | 121 / 79 / 62 | — | 0 |
| 200 × 0 | 54,1 / 46,4 / 66,2 | 75,8 / 70,3 / 104,6 | 206,2 / 175,1 / 290,1 | 92 / 117 / 145 | — | 0 |
| 1.000 × 0 | 69,1 / 62,1 / 46,2 | 93,8 / 84,2 / 57,5 | 218,9 / 205,1 / 148,8 | 191 / 124 / 88 | — | 0 |
| 200 × 10 | 85,9 / 84,0 / 61,0 | 115,4 / 117,6 / 84,3 | 229,6 / 254,2 / 173,4 | 132 / 167 / 118 | 14,2 / 14,4 / 9,9 | 0 |
| 200 × 20 | 98,7 / 88,4 / 69,8 | 140,4 / 129,1 / 97,2 | 242,4 / 232,7 / 192,9 | 165 / 162 / 139 | 17,2 / 16,6 / 10,5 | 0 |
| 1.000 × 20 | 110,4 / 111,6 / 80,9 | 150,8 / 162,8 / 109,8 | 271,5 / 255,3 / 182,8 | 201 / 217 / 128 | 18,6 / 16,9 / 10,5 | 0 |
| 200 × 20-HC | 85,9 / 75,3 / 56,4 | 121,0 / 111,2 / 78,6 | 238,2 / 218,1 / 158,8 | 174 / 144 / 118 | 14,0 / 13,6 / 9,5 | 0 |

- Tiêu chí §79 P2 (sinh ứng viên p95 < 300 ms) **vẫn đạt** sau tích hợp P3 ở cả 3 lượt; cao nhất 162,8 ms (p99 cao nhất 217 ms). Đây là số đo local, dữ liệu SYNTHETIC — không phải số đo máy chủ thật.
- Chi phí mới: tra trạng thái giá kế hoạch 10–19 ms p95 (2 truy vấn + đọc booking) khi có kế hoạch mở — ứng viên tối ưu sau.

**Kiểm chứng độc lập (`p3-integrated-verify`):**

| Workload | Ứng viên kiểm | Vi phạm RB | Loại xe đơn đúng | Kế hoạch: đúng (không chèn được) | Kế hoạch: RB cho phép nhưng cổng giá loại | Lý do loại P3 |
|---|---|---|---|---|---|---|
| 50 × 0 / 200 × 0 / 1.000 × 0 | 4.507 / 9.949 / 10.735 | **0** | 388 / 440 / 218 | — | — | — |
| 200 × 10 | 10.038 | **0** | 493 | 567 | 67 | D1 67, Cổng 1 3 |
| 200 × 20 | 10.009 | **0** | 491 | 997 | 263 | D1 249, Cổng 1 34, Cổng 2B 4 |
| 1.000 × 20 | 10.298 | **0** | 333 | 1.068 | 245 | D1 238, Cổng 1 18, Cổng 2B 2 |
| 200 × 20-HC | 9.162 | **0** | 1.352 | 413 | 247 | D1 247, Cổng 1 9 |

- **0 vi phạm** 11 ràng buộc cứng trên 64.698 ứng viên; mọi lần loại xe đơn đều đúng; **0** kế hoạch bị bỏ sót (`missed`) và **0** lệch chi phí: mọi phương án mà bộ vét cạn độc lập (chỉ RB) cho là khả thi nhưng generator không chào đều bị cổng giá P3 loại với mã chính xác (`rejected_by_pricing_gates`).
- **0 ứng viên nhánh A được định giá `COMPLETE` trên thế giới benchmark SYNTHETIC.** Lý do chính là D1 (không có đoạn ngồi chung): trên các kế hoạch sinh ngẫu nhiên, phương án qua RB chủ yếu là đón khách mới **sau** khi khách cũ đã xuống (chở nối tiếp, không phải ghép) — R9 §11 / §15.5 D1 không coi là ghép. Phần còn lại bị Cổng 1 / Cổng 2B (SF-P3-16). Kết quả này **không** đo được tỷ lệ ghép thực tế (thế giới benchmark không mô phỏng nhu cầu cùng hướng), nhưng xác nhận rằng không có ứng viên nào được chào khi chưa qua đủ cổng. Đường `COMPLETE` được kiểm bằng `test_branch_a_with_traffic_speeds_is_priced_complete`.
- Workload HC khác P2: kế hoạch ≥ 2 khách phải có phân bổ hợp lệ; 11 / 20 không định giá được nên không được tạo.

## 4. Phát hiện cần Chủ dự án quyết định

Chi tiết: `SPEC_FINDINGS_P3.md`.

| Ưu tiên | Mã | Nội dung |
|---|---|---|
| Cao | SF-P3-16 | Cổng 2B (`ε = 0`) loại gần như mọi phương án ghép khi dùng thời gian OSRM không kẹt xe → tỷ lệ ghép thực tế sẽ rất thấp (P6–P8) |
| Cao | SF-P3-02 | Định nghĩa `T_plan` (gồm dwell và thời gian chờ) — ảnh hưởng trực tiếp SF-P3-16 |
| Trung bình | SF-P3-10 | Quỹ không đủ chi bảo đảm: hiện từ chối, số dư không âm |
| Trung bình | SF-P3-04, 05, 06, 07, 12, 13 | Diễn giải bảng 18.5 / 18.7, D1, lần ghép đầu |
| Thấp | SF-P3-01, 03, 09, 14 | Lỗi in / phát biểu bất biến / biên `>` vs `≥` / gộp điểm dừng |

## 5. Vì sao chưa tạo `PHASE_3_COMPLETION_REPORT.md`

1. ~~Tiêu chí 5 (hiệu năng sau tích hợp)~~ — **đạt** ngày 05/11 (3 lượt hợp lệ a4–a6 + kiểm chứng độc lập, §3).
2. SF-P3-16 là rủi ro chất lượng lớn của chính sản phẩm định giá P3; cần Chủ dự án quyết định trước khi coi P3 hoàn tất.
3. Mã P3 chưa được commit (chờ cho phép).

## 6. Việc tiếp theo

1. ~~Chạy lại benchmark P3~~ — xong (§3).
2. Chủ dự án quyết định SF-P3-16 / SF-P3-02 / SF-P3-10 và các diễn giải `LOCAL_PROVISIONAL`.
3. Khi được cho phép: commit P3 (sau khi rà staged diff và quét secrets).
