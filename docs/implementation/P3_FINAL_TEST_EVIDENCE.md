# BẰNG CHỨNG KIỂM THỬ VÀ BENCHMARK HIỆU NĂNG CHUẨN TẮC
## (P3_FINAL_TEST_EVIDENCE)

- **Dự án:** Ride_Sharing
- **Commit thẩm định thực tế:** `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`
- **Thời điểm lập:** 2026-11-10
- **Nguyên tắc báo cáo:** Phân biệt rành mạch giữa các bài test đã thực thi mới trực tiếp, các bài test kiểm toán qua bằng chứng lịch sử, và các điều kiện môi trường thực tế. Tuyệt đối không suy diễn test PASS khi chưa chạy.

---

## 1. Khảo Sát Môi Trường Thực Thi Thực Tế Trên Máy Chủ Windows Host

Kiểm tra bằng lệnh terminal:
```powershell
PS C:\RideSharing> python --version; python -m pip --version; python -m pip show pytest hypothesis sqlalchemy
Python 3.12.10
pip 25.0.1 from C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\Lib\site-packages\pip (python 3.12)
WARNING: Package(s) not found: hypothesis, pytest, sqlalchemy

PS C:\RideSharing> docker --version
docker : The term 'docker' is not recognized as the name of a cmdlet...
```

### Kết luận về môi trường:
1. Máy chủ Windows Host hiện tại chỉ có Python thuần `3.12.10`.
2. **Không có sẵn `pytest`, `hypothesis`, `sqlalchemy`** trên môi trường global của Python Host.
3. **Không có sẵn `docker`** trên hệ điều hành Host.
4. Do đó, các bài test phụ thuộc pytest CLI, hypothesis CLI và Docker/PostgreSQL 16 **không thể chạy lệnh trực tiếp từ shell Host** mà phải được phân loại và kiểm chứng minh bạch như dưới đây.

---

## 2. Kiểm Kê Toàn Bộ Test Suite Trong Kho Mã Nguồn

Sử dụng bộ phân tích cú pháp trừu tượng (Python AST Parser) quét toàn bộ 23 file kiểm thử tại thư mục `backend/tests/`:
- **Tổng số file test:** **23 file** (`test_*.py`)
- **Tổng số hàm test định nghĩa AST (`def test_*`):** **210 hàm test**
- **Tổng số ca kiểm thử mở rộng (Pytest Parametrized Items):** **291 test items** (theo collection lịch sử khi có đủ dependencies).

---

## 3. Kết Quả Kiểm Thử Thực Thi Trực Tiếp (Live Host Execution)

Do môi trường Host không cài `pytest`, toàn bộ logic của các test thuần Python đã được thực thi trực tiếp bằng Python script harness gọi hàm độc lập, nhập mock context cần thiết. Kết quả được lưu trữ chính thức tại:
- File log chi tiết: `docs/implementation/evidence/p3_acceptance/test_pure_python.log` (SHA256: `61c60d66af7f01f78830685288c822402bee1cbce8aef927df45a362635d4844`)
- File JUnit XML: `docs/implementation/evidence/p3_acceptance/pytest_pure.xml` (SHA256: `cf38d85200149813576acb3bdfe50e07a53243e1310c61dd414aef401cbdac8a`)
- Manifest nghiệm thu: `docs/implementation/evidence/p3_acceptance/P3_TEST_EXECUTION_MANIFEST.json`

```text
====================================================================================================
LIVE TEST EXECUTION AUDIT (Python 3.12.10 Standard Library - 2026-11-10)
====================================================================================================
1. test_config_baseline.py:
   - Thực thi: 4 items -> PASS 100% (0.021s)
   - Xác minh: Bất biến của file config/mvp_config_baseline_v1.yaml và drift guard.

2. test_pricing_regression.py:
   - Thực thi: 13 items -> PASS 100% (0.012s)
   - Xác minh: Cước 4 dịch vụ đơn vị, số học phân số (Rational Money), các vector chuẩn §71.1.

3. test_pricing_cancellation.py:
   - Thực thi: 17 parametrized items -> PASS 100% (0.001s)
   - Xác minh: Toàn bộ ma trận phí hủy D-52 của 5 dịch vụ (khớp bảng Section 5 của P3_PRICING_FUND: 20%, trần 20.000đ).

4. test_pricing_pool.py:
   - Thực thi: 30 parametrized items -> PASS 100% (0.006s)
   - Xác minh: Gate 1 (0.80 * sum P_i), phân bổ hai phía, cận trên/dưới, làm tròn 1000đ, Gate 2A/2B.

5. test_candidate_constraints.py:
   - Thực thi: 24 parametrized items -> 23 PASSED, 1 SKIPPED (thiếu live fastapi/sqlalchemy) (0.005s)
   - Xác minh: 11 Hard Constraints (HC01 - HC11), xử lý xe bận/rảnh, ghép cùng giới tính, ràng buộc tài xế.

6. test_pooling_insertion.py:
   - Thực thi: 22 parametrized items -> PASS 100% (4.45s)
   - Xác minh: Thuật toán chèn điểm dừng Section 36, bảo toàn giá nhóm F, không tăng giá nhóm U, độ trễ và tối ưu.

7. test_trip_rules.py:
   - Thực thi: 27 parametrized items -> 26 PASSED, 1 SKIPPED (thiếu live httpx) (0.002s)
   - Xác minh: Ranh giới đô thị/liên tỉnh, thời gian đặt trước tối đa 7 ngày, quy tắc lọc dịch vụ và nhóm khách.

8. test_pricing_properties.py:
   - Trạng thái trên Host: HISTORICAL_EVIDENCE_ONLY (thiếu thư viện hypothesis trên host).
   - Bằng chứng lịch sử: 32 profiles passing trong môi trường compose CI.
====================================================================================================
TỔNG CỘNG KIỂM THỬ LIVE TRÊN HOST: 137 TEST CASES (135 PASSED, 0 FAILED, 2 SKIPPED)
====================================================================================================
```

---

## 4. Bằng Chứng Kiểm Thử Cơ Sở Dữ Liệu & Container (Historical Evidence)

Các bài test phụ thuộc cơ sở dữ liệu (`test_fund_and_price_protection.py`, `test_candidate_generation.py`, `test_schema.py`):
- **Trạng thái trên Host:** `NOT_EXECUTED_ON_HOST` (Do máy chủ Host thiếu Docker và PostgreSQL 16/PostGIS).
- **Trạng thái kiểm toán:** `HISTORICAL_EVIDENCE_ONLY`.
- **Nguồn chứng thư lịch sử:** Log thực thi ngày 2026-11-05 tại commit `f97a509` trong container Docker:
  - `test_fund_and_price_protection.py`: **12/12 test functions PASS**. Kiểm chứng tính toàn vẹn của Quỹ bảo đảm, trigger chống sửa xóa `trg_fund_ledger_guard`, trigger đóng băng giá `trg_bookings_locked_pool_price`, và bất biến chi trả tài xế.

---

## 5. Bằng Chứng Benchmark Hiệu Năng & Hậu Kiểm Ứng Viên

### 5.1. Bằng chứng Độ trễ Sinh Ứng viên (Sử dụng các lượt chạy SẠCH: a4, a5, a6)
*Lưu ý bắt buộc:* File `docs/implementation/evidence/p3_runs/20261105T054653Z-p3-integrated-verify/LATENCY_DISTURBED.md` đã ghi nhận lượt `verify` bị gián đoạn do máy chủ bị suspend (khoảng trống từ 06:15:20Z đến 06:48:01Z). Do đó, **tuyệt đối không sử dụng độ trễ của lượt `verify` cho kết luận**.

Độ trễ sinh ứng viên ghép xe tích hợp định giá Phase 3 được đo đạc chính thức từ 3 lượt chạy sạch `a4`, `a5`, `a6` trên kịch bản tải nặng nhất (**1000 tài xế x 20 kế hoạch mở**):

| Run ID | Nguồn File Bằng Chứng | Workload | $p50$ (ms) | $p95$ (ms) | $p99$ (ms) | Đánh giá SLA Revision 9 ($p95 < 300\text{ ms}$) |
|---|---|---|---|---|---|---|
| **a4** | `20261105T053415Z-p3-integrated-a4/result.json` | 1000x20 | **88.70 ms** | **150.78 ms** | 201.44 ms | **ĐẠT XUẤT SẮC** |
| **a5** | `20261105T053903Z-p3-integrated-a5/result.json` | 1000x20 | **88.83 ms** | **162.78 ms** | 216.99 ms | **ĐẠT XUẤT SẮC** |
| **a6** | `20261105T054312Z-p3-integrated-a6/result.json` | 1000x20 | **67.56 ms** | **109.76 ms** | 128.40 ms | **ĐẠT XUẤT SẮC** |

**Kết luận về độ trễ:** Độ trễ sinh ứng viên thực tế $p95$ dao động từ **$109.76\text{ ms}$ đến $162.78\text{ ms}$**, thấp hơn gần gấp đôi so với ngưỡng giới hạn $300\text{ ms}$ của Revision 9 Mục 79.

---

### 5.2. Bằng chứng Tính Đúng Đắn (Hậu kiểm 64.698 Ứng viên từ Lượt `verify`)
Mặc dù độ trễ của lượt `verify` bị gián đoạn, kết quả phán quyết kiểm chứng logic (`verification`) không phụ thuộc thời gian và vẫn giữ nguyên giá trị:
- **Tổng số ứng viên được kiểm tra độc lập:** **64.698 ứng viên** qua 7 cấu hình (mỗi cấu hình 200 requests = 1.400 requests).
- **Số vi phạm ràng buộc định giá/Hard Constraints trên ma trận `/table`:** **`0` vi phạm**.

### 5.3. Phát hiện Rủi ro Tuyến Đường OSRM `/table` vs `/route` (Bàn Giao Quan Trọng Cho Phase 4)
Kiểm tra chi tiết mục `sf_p2_15_default_routing` trong `verify/result.json`:
- Trong tổng số 17.640 ứng viên ghép xe (`pool_candidates`):
  - Có **204 ứng viên** có nguy cơ vi phạm ràng buộc cứng (chiếm $1.16\%$) nếu kiểm tra lại bằng OSRM `/route` chi tiết thay vì ma trận `/table`.
  - Phân loại vi phạm tiềm ẩn: **61 trường hợp vi phạm HC03** (vượt trần Detour) và **143 trường hợp vi phạm HC05** (vượt trần thời gian di chuyển).
- **Ý nghĩa kỹ thuật bàn giao Phase 4:** Không được giả định rằng toàn bộ ứng viên do Phase 2 sinh ra đều an toàn 100% để phát hành lời mời (Offer). **Phase 4 bắt buộc phải có bước recheck tuyến đường với OSRM `/route` trước khi tạo Seat Hold hoặc gửi Offer Cascade cho tài xế.**
