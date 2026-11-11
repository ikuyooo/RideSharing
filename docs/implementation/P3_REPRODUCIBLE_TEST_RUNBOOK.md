# SỔ TAY HƯỚNG DẪN CHẠY KIỂM THỬ TÁI LẬP (REPRODUCIBLE TEST RUNBOOK)
## RIDE_SHARING PHASE 3 ACCEPTANCE & VERIFICATION

**Dự án:** Ride_Sharing  
**Giai đoạn:** Phase 3 (Pricing, Fund Ledger, Candidate Generation & Constraints)  
**Tài liệu tham chiếu:** Revision 9, `mvp_config_baseline_v1.yaml`  
**Commit cơ sở:** `f97a5092ece737d70051d08e6e3604e6a0c6bd1d`

---

## 1. MỤC TIÊU VÀ PHẠM VI

Tài liệu này cung cấp quy trình chuẩn hóa từng bước để bất kỳ kỹ sư kiểm thử, QA Lead, hoặc Project Owner nào cũng có thể chạy lại độc lập và tái lập 100% các bài kiểm thử của Phase 3.

Quy trình hỗ trợ 3 chế độ thực thi (Execution Modes):
- **Chế độ 1 (Mode A - Standalone Host Runner):** Dành cho môi trường Windows/Linux chỉ có Python chuẩn, không cài đặt được package ngoài (không có `pytest`, `sqlalchemy`, `docker`). Chạy kiểm thử toàn bộ 137 ca logic toán học và thuật toán pure-Python.
- **Chế độ 2 (Mode B - Docker Compose Full Stack):** Môi trường khuyến nghị đầy đủ của dự án với PostgreSQL 16 + PostGIS, Redis, OSRM servers. Chạy toàn bộ 23 file test qua CLI `pytest` và kiểm thử tải.
- **Chế độ 3 (Mode C - Local Virtualenv):** Môi trường phát triển cục bộ có kết nối mạng để cài đặt `requirements.txt`.

---

## 2. CHẾ ĐỘ 1: CHẠY KIỂM THỬ THUẦN PYTHON TRÊN HOST (MODE A)

### 2.1. Yêu cầu môi trường
- Hệ điều hành: Windows, macOS hoặc Linux.
- Python: Phiên bản 3.11 trở lên (khuyến nghị 3.12).
- Thư viện cần thiết: `PyYAML` (đã có sẵn trong bộ cài chuẩn của dự án). Không yêu cầu cài thêm package ngoài.

### 2.2. Các bước thực hiện
1. Mở PowerShell hoặc Terminal tại thư mục gốc repository:
   ```powershell
   cd C:\RideSharing
   ```

2. Chạy runner độc lập:
   ```powershell
   python scripts/run_pure_tests.py
   ```
   *(Hoặc sử dụng runner từ thư mục scratch/artifacts nếu scripts chưa được thêm vào Git)*:
   ```powershell
   python "C:\Users\ADMIN\.gemini\antigravity\brain\b62dae9e-3226-4d64-822a-772c9a4d73c2\scratch\run_pure_tests.py"
   ```

3. Kiểm tra kết quả đầu ra:
   - File log chi tiết: `docs/implementation/evidence/p3_acceptance/test_pure_python.log`
   - File JUnit XML: `docs/implementation/evidence/p3_acceptance/pytest_pure.xml`

### 2.3. Tiêu chí đạt chuẩn (Pass Criteria)
- Tổng số test case thực thi: $\ge 135$ test cases.
- Số lượng FAILED: **0**.
- Thời gian thực thi: $< 10\text{ giây}$.

---

## 3. CHẾ ĐỘ 2: CHẠY KIỂM THỬ TOÀN DIỆN QUA DOCKER COMPOSE (MODE B - RECOMMENDED)

### 3.1. Yêu cầu môi trường
- Docker Desktop hoặc Docker Engine trên Linux (hỗ trợ Compose V2).
- Tối thiểu 8 GB RAM và 10 GB dung lượng ổ đĩa trống (cho dữ liệu bản đồ OSRM miền Bắc).

### 3.2. Khởi động hạ tầng dịch vụ
Tại thư mục gốc `C:\RideSharing`:

1. Khởi tạo file cấu hình môi trường:
   ```bash
   cp .env.example .env
   ```

2. Khởi động các container phụ trợ (PostgreSQL/PostGIS, Redis, OSRM Car & Motorbike):
   ```bash
   docker compose up -d db redis osrm-car osrm-motorbike
   ```

3. Đợi các dịch vụ đạt trạng thái healthy:
   ```bash
   docker compose ps
   ```

### 3.3. Thực thi kiểm thử Pytest & Hypothesis
1. Chạy toàn bộ bài test qua container test chuyên dụng:
   ```bash
   docker compose run --rm test
   ```

2. Chạy riêng nhóm kiểm thử định giá hồi quy (Pricing Regression):
   ```bash
   docker compose run --rm test pytest backend/tests/test_pricing_regression.py -v
   ```

3. Chạy riêng kiểm thử thuộc tính sinh mẫu ngẫu nhiên (Hypothesis):
   ```bash
   docker compose run --rm test pytest backend/tests/test_pricing_properties.py -v
   ```

4. Chạy riêng kiểm thử trigger cơ sở dữ liệu và sổ cái quỹ:
   ```bash
   docker compose run --rm test pytest backend/tests/test_schema.py backend/tests/test_fund_and_price_protection.py -v
   ```

### 3.4. Xuất báo cáo nghiệm thu
Kết quả kiểm thử trong container sẽ tự động lưu vào:
- `docs/implementation/evidence/p3_runs/pytest_report.xml`
- `docs/implementation/evidence/p3_runs/p0_smoke_check.json`

---

## 4. CHẾ ĐỘ 3: CHẠY TRONG LOCAL VIRTUALENV (MODE C)

### 4.1. Khởi tạo Virtual Environment
```bash
python -m venv .venv
# Trên Windows:
.venv\Scripts\activate
# Trên Linux/macOS:
source .venv/bin/activate
```

### 4.2. Cài đặt Dependencies
```bash
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt
```

### 4.3. Chạy Pytest CLI
```bash
cd backend
python -m pytest tests/ -v --tb=short
```

---

## 5. XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

1. **Lỗi `ModuleNotFoundError: No module named 'alembic'` khi chạy standalone:**
   - *Nguyên nhân:* `conftest.py` import `alembic` ở đầu file.
   - *Xử lý:* Đảm bảo runner có stubbing tối thiểu cho `alembic` và `sqlalchemy` như trong Mode A trước khi import conftest.

2. **Lỗi `LATENCY_DISTURBED` khi đo benchmark:**
   - *Nguyên nhân:* Máy tính Windows tự động chuyển sang chế độ tiết kiệm pin hoặc sleep/suspend giữa chu kỳ benchmark.
   - *Xử lý:* Cấu hình Power Plan ở mức "High Performance", tắt sleep khi chạy benchmark, và kiểm tra timestamp giữa các request để loại trừ khoảng dừng bất thường.

3. **Lỗi `database "ridesharing_test" does not exist`:**
   - *Nguyên nhân:* User chưa có quyền tạo database hoặc script test chưa chạy alembic migration.
   - *Xử lý:* Chạy `docker compose exec db psql -U postgres -c "CREATE DATABASE ridesharing_test;"` và chạy alembic upgrade head.

