# Ride-Sharing Platform (Revision 9)

Nền tảng đặt xe thông minh đa dịch vụ — `BIKE_URBAN`, `CAR_URBAN_PRIVATE`, `CAR_URBAN_POOL`,
`CAR_INTERCITY_PRIVATE`, `CAR_INTERCITY_POOL` — kiến trúc **Modular Monolith** (FastAPI),
định giá ghép có chặn hai đầu, AI Learning-to-Rank và Blockchain Escrow.

> **Trạng thái hiện tại:** P0 `PHASE_0_CONDITIONAL__REVIEW_REQUIRED` (SF-06 mở) —
> [báo cáo P0](docs/implementation/PHASE_0_COMPLETION_REPORT.md).
> **Phase 1 đang triển khai** (schema, identity, driver/KYC mock, Trip Intent, vùng phục vụ ứng viên,
> khảo sát S1 nháp) — [báo cáo tiến độ P1](docs/implementation/PHASE_1_PROGRESS_REPORT.md).
> Chưa có pricing, booking, AI, escrow.

## Tài liệu chuẩn (đã khóa — không sửa)

| Tài liệu | Vai trò |
|---|---|
| [docs/pre/mvp_config_baseline_v1.md](docs/pre/mvp_config_baseline_v1.md) | Nguồn chuẩn cho tham số, đơn vị, phiên bản cấu hình MVP |
| [docs/pre/bao_cao_tien_du_an_ride_sharing_revision_9.md](docs/pre/bao_cao_tien_du_an_ride_sharing_revision_9.md) | Nguồn chuẩn cho nghiệp vụ, công thức, kiến trúc, thuật toán, nghiệm thu |
| [docs/pre/revision_9_decision_register.md](docs/pre/revision_9_decision_register.md) | Truy nguyên quyết định `D-01..D-52` |
| [docs/pre/revision_8_to_revision_9_changelog.md](docs/pre/revision_8_to_revision_9_changelog.md) | Lịch sử thay đổi (không ghi đè Revision 9) |

Đề xuất thay đổi nghiệp vụ/tham số: tạo ghi chú riêng trong `docs/implementation/` nêu mã quyết định
liên quan — **không** sửa tài liệu trong `docs/pre/`.

## Cấu trúc repository

```
backend/                 FastAPI app (Phase 0: settings, config loader, /health)
  app/core/              settings, config_baseline loader, dependency probes
  app/api/               HTTP routers
  tests/                 pytest (config drift guard, health)
config/
  mvp_config_baseline_v1.yaml   bản sao nguyên văn khối YAML của baseline (KHÔNG sửa tay)
infra/
  osm-tools/Dockerfile   osmium-tool + curl (Debian) để tải/cắt bản đồ
  osrm/profiles/motorbike.lua   profile xe máy VN (kế thừa car.lua của OSRM)
scripts/
  osm/fetch_and_clip.sh  tải Geofabrik Vietnam (kiểm MD5) + cắt bbox miền Bắc
  osrm/prepare.sh        osrm-extract + osrm-contract (CH) cho một profile
  p0_smoke_check.py      kiểm tra nghiệm thu P0 (chạy lại được)
  osrm_benchmark.py      benchmark OSRM có seed cố định
docs/pre/                tài liệu tiền dự án đã khóa
docs/implementation/     báo cáo nghiệm thu từng Phase, benchmark, ghi chú
docker-compose.yml
```

Các module nghiệp vụ (`identity`, `trip`, `driver`, … — Mục 54) sẽ được tạo trong `backend/app/modules/`
đúng Phase của chúng. Frontend Next.js được dựng ở Phase 6 (Mục 79).

## Yêu cầu

- Docker Desktop (WSL2 backend trên Windows) với Docker Compose v2. VM Docker nên có ≥ 4 GB RAM.
- Python ≥ 3.11 trên host (chỉ để chạy test và các script kiểm tra; script dùng stdlib).
- ~3 GB dung lượng trống cho image + dữ liệu bản đồ (trong Docker volume).

## Khởi động lần đầu

```bash
# 1. Biến môi trường (đặt mật khẩu thật, .env bị git-ignore)
cp .env.example .env        # rồi thay mọi giá trị "change-me"

# 2. Chuẩn bị dữ liệu bản đồ + đồ thị OSRM (chạy một lần; idempotent)
docker compose --profile osrm-prep build osm-fetch
docker compose --profile osrm-prep run --rm osm-fetch            # tải ~316 MB, cắt còn ~110 MB
docker compose --profile osrm-prep run --rm osrm-prep-car        # extract + contract (CH)
docker compose --profile osrm-prep run --rm osrm-prep-motorbike

# 3. Chạy toàn bộ hệ thống
docker compose up -d --build
docker compose ps            # mọi service phải "healthy"

# 4. Kiểm tra nghiệm thu
python scripts/p0_smoke_check.py --restart-test
python scripts/osrm_benchmark.py                     # từ host (qua port forward)
```

Benchmark trong mạng Docker (đường gọi thực tế của backend):

```bash
docker run --rm --network ridesharing_backend -v "$PWD/scripts:/s:ro" python:3.12-slim \
  python -I /s/osrm_benchmark.py --in-network
# Git Bash trên Windows: thêm MSYS_NO_PATHCONV=1 ở đầu lệnh và dùng "$(pwd -W)" thay cho "$PWD".
```

> Lưu ý đo đạc: `osrm-routed` v5.27.1 trả lời request nhỏ trên kết nối **keep-alive** chậm ~40 ms
> (tương tác delayed-ACK), dù thời gian xử lý thật ~1 ms. Benchmark mặc định dùng kết nối mới cho mỗi
> request (`--connection close`); client routing của backend (P2) cần lưu ý điều này.

Các bước chuẩn bị bỏ qua phần việc đã làm (so khớp MD5 của bản đồ, profile và phiên bản OSRM).
Ép làm lại: `docker compose --profile osrm-prep run --rm -e FORCE=1 <service>`.
Cập nhật bản đồ mới: chạy `osm-fetch` với `FORCE=1`, sau đó hai bước `osrm-prep-*` sẽ tự build lại.

## Dịch vụ

| Service | Image | Cổng host (127.0.0.1) | Health check |
|---|---|---|---|
| `postgres` | `postgis/postgis:16-3.4` | 5432 | `pg_isready` qua TCP + `SELECT postgis_version()` |
| `redis` | `redis:7.4-alpine` (AOF bật, có mật khẩu) | 6379 | `redis-cli ping` = `PONG` |
| `osrm-car` | `ghcr.io/project-osrm/osrm-backend:v5.27.1` | 5000 | `/nearest` tại Hoàn Kiếm trả `"code":"Ok"` |
| `osrm-motorbike` | như trên, profile `motorbike.lua` | 5001 | như trên |
| `backend` | build `./backend` (Python 3.12) | 8000 | `/health/live`; phụ thuộc: `/health/ready` |

- `GET /health/live` — tiến trình API đang phục vụ.
- `GET /health/ready` — truy vấn thật tới Postgres/PostGIS, Redis, hai OSRM và nạp config baseline;
  trả `503` nếu một phụ thuộc lỗi.
- Dữ liệu bền vững nằm trong named volumes: `pgdata`, `redisdata`, `osm_data`, `osrm_car_data`,
  `osrm_motorbike_data`. `docker compose down` giữ nguyên volume; **`down -v` xóa toàn bộ dữ liệu**.

## Phase 1 — schema, dữ liệu cấu hình, vùng phục vụ

```bash
# Migration (Alembic) và seed bảng pricing_configs (idempotent, bất biến)
docker compose run --rm --no-deps backend alembic upgrade head
docker compose run --rm --no-deps backend python -m app.modules.pricing.seed

# Tạo tài khoản ADMIN (admin không tự đăng ký được)
docker compose run --rm --no-deps -e ADMIN_PASSWORD=... backend \
  python -m app.modules.identity.cli create-admin --email admin@example.com

# Vùng phục vụ ỨNG VIÊN (P1-D1/D3) — kết quả là CANDIDATE, cần Chủ dự án phê duyệt
docker compose --profile osrm-prep run --rm --no-deps --entrypoint sh osm-fetch \
  /scripts/export_service_area_sources.sh          # Git Bash: thêm MSYS_NO_PATHCONV=1
docker compose --profile osrm-prep run --rm --no-deps --entrypoint sh osm-fetch \
  /scripts/export_historic_boundaries.sh           # ranh giới trước 2025 (bằng chứng, rules v3)
docker compose build backend                       # service-area-build dùng chung ảnh ridesharing-backend:local
docker compose --profile service-area run --rm service-area-build \
  python -m app.modules.trip.service_area_build --rules /app/config/service_area_rules.candidate.v5.yaml
  # v5 = v4 + thị trấn Đông Anh cũ (U4); v4 vẫn build được làm phương án thay thế
# Phê duyệt có điều kiện (chỉ ghi APPROVED khi 8 cổng kiểm đều PASS; v5 đã duyệt 2026-10-28):
docker compose --profile service-area run --rm service-area-build sh -c   'python -m app.modules.trip.boundary_eval --version sa-cand-0d5347b4294e --report-name <TÊN_MỚI> &&
   python -m app.modules.trip.service_area_build --rules /app/config/service_area_rules.candidate.v5.yaml --out /tmp/repro &&
   python -m app.modules.trip.service_area_approve --version sa-cand-0d5347b4294e --eval-report <TÊN_MỚI>      --reimport-dir /tmp/repro/sa-cand-0d5347b4294e --reference "<căn cứ phê duyệt>"'
docker compose --profile service-area run --rm service-area-build \
  python -m app.modules.trip.boundary_eval --version <service_area_version>
docker compose --profile service-area run --rm service-area-build \
  python -m app.modules.trip.service_area_compare --old <version> --new <version>
# Git Bash: thêm MSYS_NO_PATHCONV=1 trước các lệnh có đường dẫn /app/...
# Bundle đã tồn tại không bị ghi đè; chạy lại một phiên bản: thêm --out /tmp/<dir>
```

Vùng phục vụ hai lớp (GEO-03/04, GEO-C/E): lớp 1 là vùng bao ứng viên (v4: đơn vị có điểm gần nhất ≤ 150 km
đường thẳng) trừ lớp `EXCLUDED`; lớp 2 kiểm tra từng điểm đón/trả bằng một request OSRM `/table` (snap ≤ `max_snap_m`,
có tuyến từ điểm gốc, ≤ 150 km, không đi phà). Vùng bao **không** phải lời hứa phục vụ. Phiên bản không có lớp 2
(`v1`, `v2`) bị Trip API từ chối (503). Công cụ báo cáo: `app.modules.trip.pickup_survey` (tỷ lệ từ chối trên điểm
đón thực tế, cần `scripts/osm/export_pickup_candidates.sh`), `app.modules.trip.historic_sources` (đối chiếu ranh giới
Đông Anh cũ). Sau khi dừng một container build, kết thúc cả truy vấn PostgreSQL của nó (`pg_terminate_backend`).

Khảo sát S1 (bản nháp, chỉ môi trường development, dữ liệu `TEST`): mở `http://127.0.0.1:8000/survey/s1`;
admin export `GET /api/admin/survey/s1/export/{respondents|choices|fairness_h4}?dataset=TEST`. Tập `RESEARCH`
bị từ chối cho đến khi Chủ dự án phát hành (`SURVEY_S1_RELEASED`). Bảng kịch bản:
`python -I scripts/survey/scenario_table.py`; kiểm tra nhận dạng thí nghiệm: `python -I scripts/survey/identifiability_check.py`. Diễn tập backup/restore (CSDL tạm):
`MSYS_NO_PATHCONV=1 sh scripts/survey/backup_restore_drill.sh`. Phương án HTTPS công khai (chưa triển khai):
[docs/implementation/survey/SURVEY_S1_DEPLOYMENT_PLAN.md](docs/implementation/survey/SURVEY_S1_DEPLOYMENT_PLAN.md).

Bundle trình duyệt nằm ở `docs/implementation/service_area/<version>/REVIEW.md`. Phân loại chuyến
(`POST /api/trip-requests`) dùng `SERVICE_AREA_VERSION`; nó trả `503` khi chưa cấu hình hoặc
phiên bản chưa được phê duyệt (`ALLOW_CANDIDATE_SERVICE_AREA=true` chỉ dành cho phát triển).

API P1: `/api/auth/{register,login,refresh,logout}`, `/api/users/me`, `/api/driver/{profile,vehicles,
kyc/submit,settings,location}`, `/api/admin/drivers/{id}/kyc-review`, `/api/trip-requests`.

## Phát triển backend

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate     # Linux/macOS: . .venv/bin/activate
pip install -e ".[dev]"
pytest          # test có marker `db`/`osrm` dùng stack compose (DB test riêng `ridesharing_test`)
```

Lưu ý khi repo nằm trong OneDrive: nên đặt virtualenv ngoài thư mục đồng bộ.

## Quy ước

- Không hardcode tham số nghiệp vụ; đọc từ `config/mvp_config_baseline_v1.yaml`
  (từ Phase 1: bảng `pricing_configs` có phiên bản). Test `test_config_baseline.py` đảm bảo file YAML
  trùng khớp với tài liệu baseline đã khóa.
- Tiền tệ: số nguyên VND (`BIGINT` / `uint256`), làm tròn xuống 1.000 đ theo baseline.
- Mỗi module chỉ giao tiếp qua service interface, không truy vấn bảng của module khác (D-31).
- Không commit `.env`, khóa, dữ liệu bản đồ, dataset hay model artifact.
