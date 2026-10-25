# PHASE 0 — BÁO CÁO NGHIỆM THU

- **Dự án:** Ride-Sharing Platform — Revision 9 / `MVP_CONFIG_BASELINE_V1`
- **Phạm vi:** Phase 0 (Mục 79): repository, Docker Compose, PostgreSQL/PostGIS, Redis, 2 container OSRM.
- **Ngày audit/kiểm thử:** 2026-10-24 (UTC). Mọi số liệu trong báo cáo đều lấy từ lệnh đã chạy;
  bằng chứng máy đọc được nằm trong [evidence/](evidence/).
- **Quy ước trạng thái:** `DIRECTLY_VERIFIED` · `REPORTED` · `NOT_VERIFIED` · `FAILED` · `NOT_APPLICABLE`.

---

## 10.1. Executive Summary

**Kết luận: `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`**

Toàn bộ chức năng hạ tầng P0 hoạt động và đã kiểm chứng trực tiếp:
- 5 service healthy, healthcheck thăm dò API thật.
- Smoke check **18/18 PASS**, gồm cả restart toàn stack và kiểm chứng xe máy không đi motorway bằng dữ liệu cạnh OSM.
- Backend test **6/6 PASS**.
- Config baseline khớp tài liệu khóa.
- Không có bí mật trong các file sẽ được git theo dõi.

Lý do **chưa** thể dùng `PHASE_0_COMPLETE__VERIFIED`: chỉ tiêu "OSRM trả ma trận `< 50 ms`" (Mục 79) không nêu kích thước ma trận (SF-06). Kết quả thực đo:

| Kích thước ma trận | Kết quả so với p95 < 50 ms |
|---|---|
| 10×10, 25×25 | **Đạt** |
| 50×50 | **Đạt 3/10** trường hợp (5 lượt × 2 profile) |
| 100×100 (trường hợp xấu nhất của Mục 34) | **Không đạt** ở mọi lượt đo (p50 62–98 ms) |

Cần Chủ dự án phân xử workload dùng để nghiệm thu (`P0_PERFORMANCE_REVIEW_REQUIRED`).

> **Cập nhật 2026-10-24 — Quyết định của Chủ dự án (chi tiết ở 10.14):**
> - Workload nghiệm thu là **100×100**. Với workload này SF-06 **chưa đạt**.
> - Trạng thái giữ nguyên `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`; P0 **chưa được nghiệm thu đầy đủ**.
> - Cho phép chuyển sang P1 theo **ngoại lệ nghiệm thu P0** do Chủ dự án phê duyệt.

**Quyết định cần phê duyệt**

| # | Nội dung | Liên quan |
|---|---|---|
| 1 | Kích thước ma trận nghiệm thu "< 50 ms" | SF-06 |
| 2 | Tên khóa candidates | SF-01, trước P2 |
| 3 | Hướng hiệu chỉnh tốc độ xe máy / giờ cao điểm | SF-05 / V-03, trước P2 |
| 4 | Cung cấp `REVISION_9_OPEN_ISSUES.md` hoặc xác nhận Baseline §6.1 là đủ | SF-04 |
| 5 | Cho phép commit đầu tiên | Chưa commit theo chỉ thị |

**Rủi ro chính**
- Phần cứng yếu: i5-5200U, 2 nhân vật lý. Build CH mất 103 phút (car) và 40 phút (motorbike).
- Hiệu năng `/table` lớn bị giới hạn bởi CPU.
- `osrm-routed` có độ trễ ~40 ms trên kết nối keep-alive (xem 10.11).

---

## 10.2. Implementation Inventory

Chỉ liệt kê file thực sự tồn tại. **Chưa có module nghiệp vụ nào của P1–P11.**

| Đường dẫn | Mục đích | Trạng thái |
|---|---|---|
| `docker-compose.yml` | 5 service mặc định + 3 job chuẩn bị dữ liệu (profile `osrm-prep`); named volumes; cổng chỉ bind 127.0.0.1 | DIRECTLY_VERIFIED |
| `.env.example` / `.env` (ignored) | Biến môi trường; `.env` thật chứa mật khẩu sinh ngẫu nhiên, bị git-ignore | DIRECTLY_VERIFIED |
| `.gitignore`, `.gitattributes` | Loại secrets/dữ liệu/cache; giữ LF cho file chạy trong container | DIRECTLY_VERIFIED |
| `config/mvp_config_baseline_v1.yaml` | Bản sao nguyên văn khối YAML Baseline §4 (trích bằng script) | DIRECTLY_VERIFIED |
| `backend/` (`app/main.py`, `app/api/health.py`, `app/core/{settings,config_baseline,health}.py`, `Dockerfile`, `pyproject.toml`) | Skeleton FastAPI: settings, nạp config baseline chỉ đọc, `/health/live`, `/health/ready` | DIRECTLY_VERIFIED |
| `backend/tests/test_config_baseline.py`, `test_health.py` | Chống trôi config; health endpoints | DIRECTLY_VERIFIED |
| `infra/osm-tools/Dockerfile` | Debian 12.11 + osmium-tool + curl (gói Debian chính thức) | DIRECTLY_VERIFIED |
| `infra/osrm/profiles/motorbike.lua` | Profile xe máy kế thừa `/opt/car.lua` (OSRM v5.27.1) | DIRECTLY_VERIFIED |
| `scripts/osm/fetch_and_clip.sh` | Tải Geofabrik (kiểm MD5) + cắt bbox; idempotent | DIRECTLY_VERIFIED |
| `scripts/osrm/prepare.sh` | `osrm-extract` + `osrm-contract` (CH); stamp + manifest MD5; idempotent | DIRECTLY_VERIFIED |
| `scripts/p0_smoke_check.py` | 18 kiểm tra nghiệm thu, `--restart-test`, `--json-out` | DIRECTLY_VERIFIED |
| `scripts/osrm_benchmark.py` | Benchmark có seed cố định, `--in-network`, `--connection` | DIRECTLY_VERIFIED |
| `README.md` | Hướng dẫn khởi động, quy ước | DIRECTLY_VERIFIED |
| `docs/implementation/SPEC_FINDINGS_P0.md` | SF-01..SF-07 + trạng thái xử lý | DIRECTLY_VERIFIED |
| `docs/implementation/evidence/*.json` | Kết quả smoke check và 5 lượt benchmark | DIRECTLY_VERIFIED |
| `frontend/` | Không tạo — dựng ở P6 (Mục 79) | NOT_APPLICABLE |

---

## 10.3. Runtime Environment

| Thành phần | Giá trị thực tế | Nguồn bằng chứng |
|---|---|---|
| Host | Windows 10 Pro 19045, Intel Core i5-5200U (2 nhân / 4 luồng), RAM 11,9 GB | `Win32_Processor`, `Win32_OperatingSystem` |
| Docker | Engine 29.8.0, Compose 5.6.1, Docker Desktop (WSL2) | `docker version`, `docker compose version` |
| Docker VM | 4 CPU, 5,739 GiB RAM | `docker info` |
| PostgreSQL / PostGIS | 16.4 / 3.4.3 (`postgis/postgis:16-3.4`) | smoke check |
| Redis | 7.4.11 (`redis:7.4-alpine`), AOF bật, có mật khẩu | smoke check |
| OSRM | v5.27.1 (`ghcr.io/project-osrm/osrm-backend:v5.27.1`), `--algorithm ch`, `--max-table-size 200` | `osrm-routed --version`, compose |
| Backend | Python 3.12-slim, FastAPI 0.115.12 | image build |
| RAM khi chạy | osrm-car ~1,0–1,15 GiB; osrm-motorbike ~1,0–1,3 GiB; postgres ~25–100 MiB; backend ~56 MiB; redis ~9 MiB | `docker stats` |
| Restart count | 0 cho cả 5 container trước audit | `docker inspect` |
| Volumes | `pgdata`, `redisdata`, `osm_data`, `osrm_car_data`, `osrm_motorbike_data` (tổng 3,87 GB) | `docker system df` |
| Ổ C: | còn trống 40 GB | `df` |

---

## 10.4. OSM Dataset Provenance

| Mục | Giá trị (DIRECTLY_VERIFIED — MD5 tính lại trong audit) |
|---|---|
| Nguồn | `https://download.geofabrik.de/asia/vietnam-latest.osm.pbf` |
| Thời điểm dữ liệu | `osmosis_replication_timestamp = 2026-10-23T20:20:51Z` |
| File nguồn | 331.456.690 byte, MD5 `bdf516510a27fab5223bee468f79c79a` (khớp `.md5` của Geofabrik) |
| Vùng cắt | bbox `104.30,19.60,107.50,22.50` (Hà Nội + bán kính dịch vụ 150 km), `osmium extract --strategy complete_ways` |
| File vùng | 112.701.529 byte, MD5 `c9d1afd9a82fe03b01834120ea0a36d3` |
| Profile car | `/opt/car.lua` của image; MD5 `0d215c039f788d15e7001953ae9a6640` (trùng nguồn GitHub tag v5.27.1) |
| Profile motorbike | `infra/osrm/profiles/motorbike.lua`; MD5 `824bd7b07b1499170fc204e3cb82d7b8` |
| Khóa build (stamp) | car `profile_md5=1b24ed9a…` · motorbike `profile_md5=c0190a5d…` — tính lại trên host khớp 100% |
| Thuật toán | Contraction Hierarchies (extract → contract; serve `--algorithm ch`) cho cả hai profile |
| Thời gian build | car 6.153 s (102 phút 48 giây) · motorbike 2.412 s (40 phút 24 giây) |
| Artifacts | 24 file `region.osrm.*` mỗi profile, ở hai volume riêng; `hsgr` car 460,8 MB / motorbike 473,4 MB |

**Khi nào phải chạy lại:**

| Thay đổi | Việc cần làm |
|---|---|
| Bản đồ mới | Chạy `osm-fetch` với `FORCE=1` |
| `motorbike.lua`, ảnh OSRM hoặc `region.osm.pbf` đổi | Khóa stamp đổi theo, nên `osrm-prep-*` sẽ tự build lại |
| Artifact bị thiếu hoặc hỏng | Manifest MD5 phát hiện, nên `osrm-prep-*` sẽ tự build lại |

---

## 10.5. OSRM Functional Verification

Nguồn: [evidence/p0_smoke_check.json](evidence/p0_smoke_check.json) (lượt chạy 18/18 PASS).

| Kiểm tra | Car | Motorbike |
|---|---|---|
| `/nearest` Hoàn Kiếm | PASS — snap 33,8 m, (105.85388, 21.02850) | PASS — như car |
| `/route` Phenikaa → Đống Đa | PASS — 12,77 km, 17,6 phút, geometry 303 điểm, TB 43,6 km/h | PASS — 12,77 km, 18,3 phút, geometry 291 điểm, TB 41,8 km/h |
| `/table` 3×3 (kích thước, đường chéo = 0, đơn vị m/s, tốc độ hợp lý 5–120 km/h) | PASS — hàng 0: [0, 6642, 12774] m / [0, 646, 1055] s | PASS — [0, 6642, 12766] m / [0, 724, 1098] s |
| Tuyến tới điểm gần biên bbox (Thanh Hóa, Hạ Long, Tuyên Quang, Lạng Sơn) | PASS — 4/4 có tuyến, snap ≤ 200 m | PASS — 4/4 |
| Lỗi / ngoài vùng phủ | PASS — tọa độ sai → HTTP 400 `InvalidValue`; điểm Vinh (ngoài extract) snap xa 94 km | PASS — như car |
| Ma trận benchmark tới 100×100 | 0 ô null; 1.000 request bảng có đo thời gian (5 lượt × 4 kích thước × 50) | 0 ô null; 1.000 request |
| **Xe máy tránh motorway** | — | **PASS** (xem dưới) |

**Phương pháp kiểm chứng motorway (Mục 34)**
1. Trích từ chính `region.osm.pbf` bằng osmium: 24.879 cạnh (cặp node OSM) thuộc way `highway=motorway|motorway_link`, và 13.617 cạnh thuộc way `motorcycle=no`.
2. Lấy chuỗi node OSM của tuyến (`annotations=nodes`) cho 4 cặp OD.
3. Đối chiếu từng cạnh của tuyến với hai tập cạnh trên.

| Cặp OD | Car: cạnh motorway / tổng cạnh | Motorbike: cạnh vi phạm / tổng cạnh |
|---|---|---|
| Hoàn Kiếm → Ninh Bình | 432 / 784 | 0 / 1.357 |
| Hoàn Kiếm → Hải Phòng | 290 / 895 | 0 / 1.291 |
| Hà Đông → TP Hưng Yên | 173 / 743 | 0 / 947 |
| Hoàn Kiếm → Thái Nguyên | 0 / 1.469 | 0 / 1.478 |

Car dùng motorway ở 3 tuyến, chứng tỏ bộ test có tính phân biệt. Motorbike có 0 cạnh vi phạm trên tổng 5.073 cạnh.

**Giới hạn**
- Đây là kiểm chứng trên mẫu 4 tuyến, không phải chứng minh cho mọi tuyến.
- Tính đúng đắn tổng quát dựa trên cơ chế của profile: `profile.avoid` chứa `motorway`/`motorway_link`, và `WayHandlers.avoid_ways` loại các way này khi extract (đã đọc mã nguồn v5.27.1).
- Phát hiện cho P2: OSRM luôn snap, kể cả điểm ngoài vùng phủ (Vinh snap xa 94 km). Module `routing`/`trip` phải từ chối khi khoảng cách snap lớn, và phân loại vùng theo Mục 2.3.

---

## 10.6. OSRM Performance Benchmark

**Phân biệt bốn lớp thông tin**
1. **Chỉ tiêu gốc (Mục 79):** "OSRM trả về ma trận khoảng cách/thời gian `< 50 ms`". Tài liệu không nêu kích thước ma trận, không nêu percentile.
2. **Phương pháp đề xuất (SF-06, chưa được phê duyệt):** đo 10/25/50/100 điểm, đánh giá theo p95; 100×100 là trường hợp xấu nhất của Mục 34.
3. **Kết quả thực đo:** các bảng dưới.
4. **Kết luận nghiệm thu:** chưa đủ căn cứ (`P0_PERFORMANCE_REVIEW_REQUIRED`).

**Phương pháp**
- 100 điểm sinh đều trong bbox nội đô Hà Nội `105.70,20.93,105.92,21.10` với seed `20261024`, sau đó snap lên mạng đường của từng profile bằng `/nearest`. Khoảng cách snap: p50 ~19 m, max 462 m.
- Mỗi kích thước: 5 lượt warm-up, sau đó 50 lượt đo; `annotations=duration,distance`.
- Một request chỉ được tính là thành công khi trả HTTP 200, `code = "Ok"` và ma trận N×N đầy đủ không có ô null.
- Số request bảng có đo thời gian: **2.000** (5 lượt × 2 profile × 4 kích thước × 50), tất cả thành công, 0 thất bại. Thêm 200 request warm-up không tính giờ và không được kiểm tra hợp lệ. Thêm 500 request `/route` có đo thời gian. Số liệu đếm lại trực tiếp từ 5 file JSON.
- Chỉ đo trạng thái **warm**, không đo cold.
- CPU/RAM: chỉ có ở 3 lượt chạy từ host (run1, run2, run5), chụp bằng `docker stats` trước và giữa các pha đo, không phải trong lúc request đang chạy. Ở các lượt này OSRM dùng ~1 GiB mỗi container, **không có áp lực bộ nhớ**.
- **Không có** số liệu CPU/RAM cho 2 lượt chạy trong mạng Docker (run3, run4). Container đo không có Docker CLI, nên file JSON chỉ ghi lỗi.
- Nguồn gốc nhãn chế độ kết nối: run4 và run5 có trường `connection_mode` trong file. run1–run3 được tạo trước khi có trường này; nhãn "keep-alive" và "TCP_NODELAY" của chúng lấy từ nhật ký phiên làm việc (REPORTED), còn tên file do tôi đặt lại sau khi chạy.

**Lượt chính — trong mạng Docker, kết nối mới mỗi request**

Đây là đường backend sẽ gọi OSRM. Nguồn: [evidence/osrm_bench_innet_close_run4.json](evidence/osrm_bench_innet_close_run4.json). Đơn vị ms; định dạng p50 / p95 / mean / max.

| Profile | 10×10 | 25×25 | 50×50 | 100×100 | `/route` 1 cặp |
|---|---|---|---|---|---|
| car | 8,17 / 9,35 / 8,38 / 11,86 | 21,58 / 34,03 / 23,72 / 62,42 | 41,12 / **76,61** / 45,11 / 103,82 | 62,78 / **69,61** / 64,43 / 132,89 | 3,04 / 4,13 |
| motorbike | 10,11 / 16,45 / 10,96 / 22,08 | 17,67 / 20,56 / 18,21 / 22,46 | 33,23 / 46,98 / 34,78 / 50,80 | 68,89 / **118,01** / 75,63 / 140,73 | 2,92 / 3,62 |

**Toàn bộ 5 lượt đo** (p95 ms của `/table`; mỗi ô 50 lượt đo thành công)

| Lượt | Kết nối | Vị trí client | car 10 / 25 / 50 / 100 | motorbike 10 / 25 / 50 / 100 |
|---|---|---|---|---|
| run1 | keep-alive | host | 23,57 / 44,96 / 59,28 / 200,87 | 20,12 / 32,66 / 50,33 / 157,90 |
| run2 | keep-alive + TCP_NODELAY | host | 14,51 / 54,53 / 50,04 / 109,82 | 15,62 / 35,06 / 85,08 / 96,15 |
| run3 | keep-alive + TCP_NODELAY | trong mạng Docker | 8,41 / 22,28 / 33,17 / 102,92 | 8,36 / 34,31 / 42,86 / 117,52 |
| run4 | close | trong mạng Docker | 9,35 / 34,03 / 76,61 / 69,61 | 16,45 / 20,56 / 46,98 / 118,01 |
| run5 | close | host | 17,88 / 43,81 / 62,71 / 87,13 | 26,25 / 44,25 / 55,46 / 121,47 |

**Thời gian xử lý phía server** (OSRM tự ghi log, run1; ms; định dạng p50 / p95)

| Profile | `/route` | 10×10 | 25×25 | 50×50 | 100×100 |
|---|---|---|---|---|---|
| car | 1,14 / 1,53 | 8,74 / 15,15 | 19,02 / 39,53 | 32,30 / 70,57 | 93,33 / 191,56 |
| motorbike | 1,08 / 1,57 | 8,40 / 15,23 | 19,48 / 29,54 | 31,33 / 43,85 | 65,27 / 94,50 |

**Đối chiếu với chỉ tiêu**

| Kích thước | Kết quả p95 qua 5 lượt × 2 profile |
|---|---|
| 10×10 | Đạt ở cả 10/10 trường hợp |
| 25×25 | Đạt ở 9/10 (car run2 = 54,53 ms) |
| 50×50 | Đạt ở 3/10 (p95 từ 33,17 đến 85,08 ms) |
| 100×100 | Đạt ở 0/10 (p95 từ 69,6 đến 200,9 ms) |

Đối chiếu thêm Mục 77: chỉ tiêu "Lọc PostGIS + 1 ma trận OSRM Table p95 ≤ 300 ms" của luồng gợi ý (áp dụng từ P2) **được đáp ứng** ở 100×100 trong mọi lượt (p95 xấu nhất 200,9 ms). Đây chỉ là thông tin tham khảo cho P2, không thay thế chỉ tiêu P0.

**Phân tích nguyên nhân (E4)**

| Yếu tố | Đánh giá |
|---|---|
| Cách đo (benchmark) | Đã phát hiện và loại bỏ nhiễu ~40 ms do keep-alive (xem 10.11). Nhiễu này chỉ làm sai số `/route`, không giải thích được độ trễ `/table` vì thời gian server ≈ thời gian client. |
| Mạng / port forward | Trong mạng Docker nhanh hơn từ host ~3–5 ms; không phải nguyên nhân chính. |
| Bộ nhớ | Không có áp lực (~1 GiB / 5,7 GiB mỗi container). |
| CPU | Nguyên nhân chính: CH many-to-many trên đồ thị ~4,4 triệu node, xử lý trên CPU i5-5200U (2 nhân, 2,2 GHz) trong VM của Docker Desktop. Độ phân tán giữa các lượt lớn (máy laptop). |
| Thuật toán / cấu hình | Đã dùng CH, là lựa chọn nhanh nhất của OSRM cho `/table`. Không đổi thuật toán, không nới ngưỡng. |

**Lựa chọn khả thi** (cần phê duyệt, chưa thực hiện):
- (a) Chốt kích thước ma trận nghiệm thu P0 ở ≤ 25 điểm, phù hợp luồng `BIKE`/`PRIVATE` của Mục 35.1.
- (b) Giữ 100×100 và chạy lại trên phần cứng mạnh hơn.
- (c) Thu hẹp vùng cắt bản đồ. Lựa chọn này ảnh hưởng `max_total_service_radius_km`, nên **không khuyến nghị** nếu chưa có quyết định.

---

## 10.7. Backend, PostgreSQL và Redis Verification

| Kiểm tra | Kết quả | Trạng thái |
|---|---|---|
| Postgres version + PostGIS | PostgreSQL 16.4, PostGIS 3.4.3 | DIRECTLY_VERIFIED |
| Truy vấn không gian (bảng tạm + chỉ mục GIST, `ST_DWithin`, `ST_Distance` geography) | `la_phu,phenikaa` trong 5 km; Phenikaa–Hoàn Kiếm 14.597 m | DIRECTLY_VERIFIED |
| Redis | `PONG`; SET/GET với TTL 59 s; version 7.4.11 | DIRECTLY_VERIFIED |
| `/health/live` | 200 `{"status":"ok"}` | DIRECTLY_VERIFIED |
| `/health/ready` | 200; postgres, redis, osrm_car, osrm_motorbike, config_baseline đều `ok`; `MVP_CONFIG_BASELINE_V1` / `price_v9_two_sided_bounded` | DIRECTLY_VERIFIED |
| Hợp đồng readiness khi phụ thuộc lỗi | 503 + `degraded` (test `test_ready_reports_unreachable_dependencies`) | DIRECTLY_VERIFIED |
| **Restart toàn stack** (`docker compose restart` 5 service; không dùng `down`, không đụng volume) | Cả 5 service healthy sau 22 s. Marker còn nguyên trong Postgres và Redis (AOF). Stamp OSRM không đổi; route trả lời mà không cần preprocess lại. Probe đã được dọn sạch. | DIRECTLY_VERIFIED |
| Healthcheck phản ánh API thật | Log health của osrm-car: probe thất bại (`Connection refused`) khi graph đang nạp, chỉ pass khi API trả `Ok` | DIRECTLY_VERIFIED |
| Backend test suite | 6 tests: 6 PASS, 0 FAIL, 0 SKIP, exit code 0 (1 DeprecationWarning của starlette) | DIRECTLY_VERIFIED |

---

## 10.8. Configuration Integrity

| Bằng chứng | Kết quả |
|---|---|
| `test_config_file_matches_locked_document_exactly`: so sánh dữ liệu YAML đã parse của file với khối YAML duy nhất trong `docs/pre/mvp_config_baseline_v1.md` | PASS |
| Kiểm thử âm: sửa `d_max: 0.61` trên **bản sao** trong scratchpad | Bị phát hiện là khác tài liệu khóa (`False`); file thật không bị chạm vào |
| MD5 file config trong repo và trong container backend (mount `:ro`) | Cả hai là `5f143a1e43626e26e734e3eb7522dd18` |
| Loader trả mapping chỉ đọc; từ chối sai version, sai status, thiếu file | PASS (3 test) |
| Tài liệu khóa trong `docs/pre/` | Không bị sửa |

---

## 10.9. Specification Findings

Chi tiết và bằng chứng: [SPEC_FINDINGS_P0.md](SPEC_FINDINGS_P0.md).

| ID | Phân loại | Ảnh hưởng P0 | Phase đích |
|---|---|---|---|
| SF-01 | Đang chờ phê duyệt (`PENDING_OWNER_CONFIRMATION_FOR_P2`) | Không | P2 |
| SF-02 | Đã xác minh — sai lệch chú thích tài liệu | Không | — |
| SF-03 | Đã xử lý kỹ thuật (giữ khóa Baseline) | Không | P8, P9 |
| SF-04 | `SOURCE_NOT_AVAILABLE` — đang chờ | Giới hạn kiểm chứng (không chặn) | — |
| SF-05 | `NEEDS_VALIDATION (V-03)`; ràng buộc motorway đã kiểm chứng | Không | P2 (P3) |
| SF-06 | `P0_PERFORMANCE_REVIEW_REQUIRED` | **Có — lý do kết luận CONDITIONAL** | P0, P2 |
| SF-07 | Chuyển phase | Không | P6 |

---

## 10.10. Security and Repository Audit

| Kiểm tra | Kết quả |
|---|---|
| Git | Đã `git init`, nhánh `main`, **chưa có commit nào** (không commit/push theo chỉ thị). 36 file sẽ được theo dõi. |
| `.env` | Bị ignore (`git check-ignore`); không xuất hiện trong danh sách file sẽ track |
| Quét giá trị mật khẩu thật trong file sẽ track và file bằng chứng | 0 kết quả |
| Quét mẫu private key / GitHub token / AWS key / khóa hex 64 ký tự | 0 kết quả |
| Dữ liệu lớn | OSM/OSRM nằm trong Docker volume; file lớn nhất sẽ track là tài liệu đặc tả 404 KB |
| Cache/build | `__pycache__`, `.pytest_cache`, `*.egg-info` bị ignore |
| Cổng dịch vụ | Chỉ bind `127.0.0.1` |
| Mật khẩu | Postgres và Redis lấy từ `.env` (bắt buộc qua `${VAR:?}`); không hardcode |
| Container | Backend chạy user không phải root (uid 10001) |

---

## 10.11. Problems Encountered and Fixes

| # | Vấn đề | Nguyên nhân gốc (bằng chứng) | Sửa | Kiểm thử lại |
|---|---|---|---|---|
| 1 | Docker Engine không khởi động (phiên trước) | Log Docker Desktop: `Virtual Machine Platform not enabled`. Ảo hóa firmware đã bật, Windows thiếu feature WSL2/VMP | Chủ dự án tự cài (cần quyền admin + reboot); không tự thay đổi máy | Engine 29.8.0 chạy |
| 2 | `osrm-car` báo `unhealthy` dù API trả 200 | `docker inspect`: `Health check exceeded timeout (5s)`. OSRM giữ keep-alive, body không có newline cuối, nên `grep` chờ tới timeout | Thêm header `Connection: close` vào healthcheck (`docker-compose.yml`) | healthy sau ~15 s; probe thất bại đúng khi API chưa sẵn sàng |
| 3 | `prepare.sh` bỏ qua build chỉ dựa vào stamp | Đọc mã: không kiểm tra file artifact | Thêm manifest `ARTIFACTS.md5` + kiểm tra file lõi; build cũ được ghi manifest mà không build lại | Chạy lại: skip + "artifacts verified". Volume nháp có stamp nhưng thiếu `hsgr`: script phát hiện và build lại. Volume nháp đã xóa |
| 4 | `fetch_and_clip.sh` bỏ qua tải/cắt mà không kiểm lại checksum | Đọc mã | Kiểm lại MD5 nguồn khi skip (sai thì dừng, yêu cầu `FORCE=1`); kiểm `region_md5` trước khi skip bước cắt | Chạy lại: "MD5-verified, skipping" cả hai bước |
| 5 | Smoke check còn thiếu kiểm tra; motorway chỉ dựa vào `classes` của step | Đọc mã đối chiếu yêu cầu | Thêm `/nearest`, geometry, ma trận (đường chéo/đơn vị), tuyến gần biên, lỗi/ngoài vùng phủ, kiểm chứng motorway bằng cạnh OSM; restart cả 5 service + so stamp OSRM | 18/18 PASS |
| 6 | Smoke check lỗi `UnicodeDecodeError` | `subprocess` dùng cp1252 trên Windows; OPL OSM có tên đường UTF-8 | `encoding="utf-8", errors="replace"` | 18/18 PASS |
| 7 | `/route` đo được ~44 ms trong khi server chỉ ~1 ms | So sánh trực tiếp cùng request: keep-alive 44,02 ms, kết nối mới 3,49 ms. `TCP_NODELAY` phía client không khắc phục được. Kết luận: delayed-ACK trên keep-alive của `osrm-routed` v5.27.1 | Benchmark thêm `--connection close` (mặc định) và `--in-network`; giữ toàn bộ số liệu cũ trong evidence | route 3,04 ms (trong mạng Docker). **Lưu ý cho P2:** client routing không nên dùng keep-alive tới OSRM, hoặc phải xử lý vấn đề này |
| 8 | Benchmark dừng cả lượt khi gặp một request lỗi; điểm chưa snap; thiếu CPU/RAM | Đọc mã | Đếm thành công/thất bại, kiểm tra ma trận đầy đủ, snap bằng `/nearest`, chụp `docker stats` | 5 lượt, 2.000/2.000 request bảng có đo thời gian hợp lệ |

**Không thực hiện:** sửa Baseline, đổi CH sang thuật toán khác, nới ngưỡng 50 ms, sửa bảng tốc độ xe máy, xóa volume, `down -v`, prune, commit/push.

---

## 10.12. Phase 0 Acceptance Matrix

| Requirement | Source | Evidence | Result | Status |
|---|---|---|---|---|
| Repository có cấu trúc rõ ràng và hướng dẫn khởi động | Master prompt §8, Mục 79 | README, mục 10.2 | Có | DIRECTLY_VERIFIED |
| `docker compose up` chạy thành công | Mục 79 P0 | `docker compose config`; 5 service healthy, restart 0 | Đạt | DIRECTLY_VERIFIED |
| PostgreSQL 16 + PostGIS 3.4 sẵn sàng, truy vấn không gian chạy được | Mục 53, 79 | smoke check | Đạt | DIRECTLY_VERIFIED |
| Redis 7 sẵn sàng | Mục 53, 79 | smoke check | Đạt | DIRECTLY_VERIFIED |
| Hai OSRM (`car` + `motorbike`) với bản đồ OSM miền Bắc, trả kết quả thật | Mục 34, 79; M2 | 10.4, 10.5 | Đạt | DIRECTLY_VERIFIED |
| Profile xe máy cấm đường cao tốc | Mục 34, Mục 7 | Đối chiếu cạnh OSM, 0/5.073 vi phạm | Đạt (trên mẫu 4 tuyến) | DIRECTLY_VERIFIED |
| OSRM trả ma trận khoảng cách/thời gian `< 50 ms` | Mục 79 P0 | 10.6 | 10: 10/10; 25: 9/10; 50: 3/10; 100: 0/10 (đạt p95 < 50 ms) | **REVIEW_REQUIRED (SF-06)** — workload nghiệm thu = 100×100 (Chủ dự án quyết định 2026-10-24): **chưa đạt** |
| Healthcheck dựa trên API thật | Master prompt §6.2 | 10.7, 10.11 #2 | Đạt | DIRECTLY_VERIFIED |
| Dữ liệu bền vững sau restart | Master prompt §6.4 | restart test | Đạt | DIRECTLY_VERIFIED |
| Chuẩn bị dữ liệu bản đồ chạy riêng, tái lập, không tải lại mỗi lần restart | Master prompt §6.2 | Idempotency test, 10.11 #3–4 | Đạt | DIRECTLY_VERIFIED |
| Config baseline từ đúng khối YAML, không hardcode | Master prompt §6.3 | 10.8 | Đạt | DIRECTLY_VERIFIED |
| Biến môi trường được tài liệu hóa; `.env` bị loại khỏi Git | Master prompt §6.2 | `.env.example`, 10.10 | Đạt | DIRECTLY_VERIFIED |
| Không có secrets trong Git | Master prompt §8 | 10.10 | Đạt | DIRECTLY_VERIFIED |
| Các lệnh kiểm tra chạy lại được | Master prompt §8 | `p0_smoke_check.py`, `osrm_benchmark.py` | Đạt | DIRECTLY_VERIFIED |
| Backend health endpoint | Master prompt §6.4 | 10.7 | Đạt | DIRECTLY_VERIFIED |
| Hiệu chỉnh tốc độ xe máy (V-03) | Baseline §6.1 | — | Chưa thực hiện (dữ liệu thực địa) | NOT_VERIFIED (NEEDS_VALIDATION, P0–P2) |

---

## 10.13. Phase 0 Final Verdict

### `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`

- **Cơ sở đạt:** mọi tiêu chí chức năng P0 đã kiểm chứng trực tiếp và đạt (mục 10.12).
- **Điều kiện còn mở (blocker duy nhất của P0):** phân xử SF-06 — chọn kích thước ma trận cho chỉ tiêu "< 50 ms".
  - Nếu Chủ dự án chốt ≤ 25 điểm: kết quả hiện có đã đạt (9/10 trường hợp p95 < 50 ms, 10/10 ở 10 điểm). Cần chạy lại một lượt xác nhận, rồi có thể chuyển sang `PHASE_0_COMPLETE__VERIFIED`.
  - Nếu chốt 100×100: hệ thống hiện tại **không đạt** trên phần cứng này. Cần phần cứng mạnh hơn hoặc một quyết định thiết kế khác; không tự thực hiện.

**Sau quyết định 2026-10-24:** Chủ dự án đã chốt 100×100. Trạng thái **vẫn là
`PHASE_0_CONDITIONAL__REVIEW_REQUIRED`**. SF-06 **không** được đánh dấu resolved, và SLA **không** được
tuyên bố là đạt. Việc chuyển sang P1 là **ngoại lệ nghiệm thu P0 do Chủ dự án phê duyệt** (10.14),
không phải kết quả nghiệm thu đầy đủ.

---

## 10.14. Owner Decision Record — SF-06 (2026-10-24)

Nguồn: quyết định Chủ dự án gửi trong phiên làm việc ngày 2026-10-24 ("OWNER DECISION — RIDE_SHARING P0 / SF-06").
Nội dung dưới đây ghi lại quyết định đó; không phải kết quả kiểm chứng kỹ thuật.

| # | Quyết định đã phê duyệt | Cách áp dụng trong hồ sơ |
|---|---|---|
| 1 | Giữ ma trận **100×100** làm workload benchmark đại diện cho ghép động (Mục 34); không hạ xuống 25×25 để đạt < 50 ms | Tiêu chí P0 "< 50 ms" được đánh giá ở 100×100, cho kết quả **chưa đạt** (0/10 trường hợp; p95 từ 69,6 đến 200,9 ms) |
| 2 | Giữ `PHASE_0_CONDITIONAL__REVIEW_REQUIRED`; không đổi sang `PHASE_0_COMPLETE__VERIFIED` | Giữ nguyên ở 10.1 và 10.13 |
| 3 | Cho phép triển khai P1 dưới dạng **ngoại lệ nghiệm thu P0** | Ghi ở 10.1, 10.13, mục 11; không ghi là đã nghiệm thu đầy đủ |
| 4 | Không thay đổi Revision 9, Baseline v1, thuật toán CH, ngưỡng hiệu năng | Không file nào trong số đó bị sửa |
| 5 | SF-06 giữ trong danh sách rủi ro hiệu năng. Trước nghiệm thu sinh ứng viên/ghép xe ở P2: benchmark lại workload thực tế và kiểm tra riêng chỉ tiêu đầu-cuối Mục 77. Đổi tiêu chí P0 hoặc phần cứng phải trình phương án riêng | Thêm vào điều kiện vào/ra của P2 (mục 11) và `SPEC_FINDINGS_P0.md` |
| 6 | Kiểm tra lại số request benchmark so với 5 file JSON; không làm đẹp số liệu | Đã thực hiện; các sai lệch được đính chính ở 10.15 |
| 7 | Cập nhật báo cáo này và `SPEC_FINDINGS_P0.md`, bảo toàn bằng chứng gốc | Các file JSON trong `evidence/` không bị sửa |
| 8 | Không tuyên bố SLA đạt; không đánh dấu SF-06 resolved | Tuân thủ |

---

## 10.15. Errata — đính chính sau khi đối chiếu với 5 file JSON (2026-10-24)

Số liệu đếm lại trực tiếp từ `evidence/osrm_bench_*.json`. Các file JSON không bị sửa; chỉ văn bản báo cáo được đính chính.

| Vị trí | Bản trước ghi | Dữ liệu thực tế | Xử lý |
|---|---|---|---|
| 10.6 (phương pháp), 10.11 #8 | "4.000 request bảng" | **2.000** request bảng có đo thời gian (5 lượt × 2 profile × 4 kích thước × 50), 2.000 ok / 0 lỗi; thêm 200 warm-up không tính giờ; thêm 500 request `/route` có đo thời gian | Đã sửa |
| 10.5 | "500 request/profile" | **1.000** request bảng có đo thời gian mỗi profile | Đã sửa |
| 10.6 (đối chiếu chỉ tiêu) | 50×50 "Đạt ở 4/10" | **3/10** (run3 car 33,17; run3 motorbike 42,86; run4 motorbike 46,98 ms). run1 motorbike = 50,33 ms là **không đạt** | Đã sửa |
| 10.6 (phương pháp) | Ngụ ý có CPU/RAM cho mọi lượt | Chỉ có ở run1, run2, run5. run3 và run4 (lượt chính) **không có** — file chỉ ghi lỗi `No such file or directory: 'docker'` | Đã nêu rõ |
| 10.6 (bảng 5 lượt) | Nhãn chế độ kết nối của run1–run3 | Ba file này không có trường `connection_mode`; nhãn lấy từ nhật ký phiên làm việc (REPORTED) | Đã nêu rõ |

Các mục đã kiểm lại và khớp: 10×10 đạt 10/10; 25×25 đạt 9/10; 100×100 đạt 0/10; p50 100×100 từ 61,73 đến 97,61 ms; p95 100×100 từ 69,61 đến 200,87 ms; giá trị p50/p95/mean/max trong các bảng của 10.6.

---

## 11. PHASE_1_READINESS (đánh giá, không triển khai)

| Câu hỏi | Đánh giá |
|---|---|
| PostGIS sẵn sàng cho Schema P1? | Có — 16.4/3.4.3, GIST hoạt động, volume bền vững. |
| Redis ổn định? | Có — AOF, có mật khẩu, qua restart. |
| Hai OSRM dùng được từ backend? | Có — `/health/ready` gọi cả hai qua mạng Docker. Lưu ý keep-alive (10.11 #7) và snap ngoài vùng phủ (10.5) cho P2. |
| Baseline nguyên vẹn? | Có (10.8). |
| Tái dựng được trên máy hiện tại? | Có — theo README; build CH mất ~2,5 giờ trên máy này (chỉ một lần). |
| Đủ căn cứ chấp nhận SLA P0? | **Chưa** — SF-06 chưa đạt ở workload 100×100 do Chủ dự án chốt. |
| Được phép bắt đầu P1? | **Có, theo ngoại lệ nghiệm thu P0** do Chủ dự án phê duyệt ngày 2026-10-24 (10.14). Không phải nghiệm thu P0 đầy đủ. |
| Điều kiện bổ sung cho P2 (từ quyết định #5) | Trước nghiệm thu `candidate`/`pooling`: benchmark lại workload thực tế, kiểm tra riêng chỉ tiêu đầu-cuối Mục 77 (PostGIS + 1 OSRM Table p95 ≤ 300 ms; `/recommendations` p95 ≤ 800 ms). |
| SF chuyển phase | SF-01 → P2; SF-05 → P2/P3; SF-03 → P8/P9; SF-07 → P6; SF-04 chờ tài liệu. |
| Blocker kỹ thuật trước P1? | Không có blocker kỹ thuật cho P1 (P1 không phụ thuộc hiệu năng ma trận OSRM). Blocker thủ tục: nghiệm thu P0 theo SF-06. |

**Checklist P1 theo Mục 79** (chỉ để tham chiếu; **chưa bắt đầu**):
1. Alembic + Schema CSDL đầy đủ Constraints/Indexes Mục 56.1–56.2, gồm bảng `pricing_configs` có phiên bản theo Baseline §5.
2. Module `identity`: JWT + refresh, RBAC `PASSENGER`/`DRIVER`/`ADMIN`.
3. Module `driver`: hồ sơ, phương tiện, KYC mock S7.
4. Module `trip`: Trip Intent, phân loại `URBAN`/`INTERCITY` có vùng đệm 15 km (Mục 2.3), luật thời gian đặt (Mục 2.2); cần đa giác `urban_service_area`/`total_service_area` (dữ liệu chưa có — phải chuẩn bị).
5. Bộ test ca biên không gian/thời gian (Mục 72).
6. Phát hành khảo sát S1 (Mục 65, V-01).
7. Trước P2: chốt SF-01 và SF-05.
