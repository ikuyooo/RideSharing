# Khảo sát S1 — Phương án triển khai HTTPS tự lưu trữ

- **Trạng thái:** `PREPARED — NOT DEPLOYED`. **Không phải `SURVEY_S1_RELEASED`.** Chưa có link công khai, chưa thu dữ liệu thật.
- **Điều kiện để triển khai (chưa có):** (1) tên miền + bản ghi DNS trỏ về máy chủ khảo sát; (2) quyền truy cập máy chủ (SSH, cổng 80/443); (3) bộ câu hỏi cuối cùng được Chủ dự án phê duyệt (bảng kịch bản `SURVEY_S1_SCENARIO_TABLE.md` còn các dòng `PENDING_OWNER_APPROVAL` / `EXPERIMENT_REVIEW_REQUIRED`); (4) thời hạn lưu trữ do Chủ dự án chốt.
- Căn cứ: quyết định "PHASE 1 FINAL CLOSURE" (hạ tầng khảo sát), P1-D5, Revision 9 Mục 59.2, 65.

## 1. Kiến trúc

```
Người trả lời ──HTTPS──► Caddy (survey-proxy, :443, TLS tự động ACME)
                           │  chỉ chuyển tiếp: GET /survey/s1, POST /api/survey/s1/sessions, POST /api/survey/s1/sessions/*/submit
                           │  mọi đường dẫn khác → 404 (admin, docs, health, API chuyến đi…)
                           ▼
                        backend (FastAPI, chỉ mạng nội bộ + 127.0.0.1:8000)
                           ├── PostgreSQL RIÊNG của máy chủ khảo sát (dataset RESEARCH)
                           └── Redis (bộ đếm chống spam, khóa băm, tự hết hạn)
Quản trị viên ──SSH tunnel──► 127.0.0.1:8000/api/admin/survey/s1/* (export, quota, xóa theo yêu cầu)
```

Tệp đã chuẩn bị: [`infra/survey/Caddyfile`](../../../infra/survey/Caddyfile) (đã kiểm tra bằng `caddy validate` 2.8.4 — *Valid configuration*), [`infra/survey/docker-compose.survey.yml`](../../../infra/survey/docker-compose.survey.yml) (đã kiểm tra `docker compose config`).

## 2. Đối chiếu yêu cầu của Chủ dự án

| Yêu cầu | Cách đáp ứng | Trạng thái |
|---|---|---|
| Domain + TLS | Caddy cấp/gia hạn chứng chỉ ACME cho `SURVEY_DOMAIN`; HSTS | Cấu hình sẵn; **thiếu domain** |
| Link công khai không cần tài khoản Ride_Sharing | Endpoint khảo sát không dùng `users`, không token | Đã có (dev), test `test_storage_has_no_identity_link` |
| Một QR duy nhất | Một URL chung `https://<domain>/survey/s1` cho mọi nhóm; nhóm xác định bằng câu D1 | Tạo QR khi có domain |
| API chỉ nhận schema đã duyệt | Pydantic `extra="forbid"`, mã lựa chọn D2–D4 cố định, phương án phải thuộc thẻ đã hiển thị; Caddy giới hạn body 64 KB | Đã có, có test |
| Mã người trả lời ngẫu nhiên | UUID v4 sinh phía máy chủ | Đã có |
| Quota hai nhóm | Mục tiêu 150 hợp lệ; trần mỗi nhóm `floor(0,60 × 150) = 90`; nhóm đầy bị đóng **khi bắt đầu phiên** (409 `QUOTA_FULL_FOR_GROUP`) | Đã hiện thực + test |
| Rate limiting & chống spam | 10 lần bắt đầu / 20 lần nộp mỗi giờ mỗi client; khóa Redis = HMAC(bí mật, ngày ‖ địa chỉ)[:16], xoay theo ngày, hết hạn theo cửa sổ; Redis lỗi → từ chối (fail closed) | Đã hiện thực + test |
| Phân quyền admin | Export/quota/xóa yêu cầu vai trò ADMIN; không đi qua proxy công khai, chỉ qua SSH tunnel | Đã có |
| Không PII thừa trong app / proxy / analytics | Không cột định danh, không IP; log truy cập uvicorn xóa địa chỉ client cho đường dẫn khảo sát; log Caddy xóa `remote_ip`, `client_ip`, headers, TLS; **không** dùng công cụ analytics / script bên thứ ba (CSP `default-src 'self'`) | Đã có |
| Thông báo / đồng ý / lưu trữ / xóa | Bản nháp [`survey/s1/PRIVACY_NOTICE.draft.md`](../../../survey/s1/PRIVACY_NOTICE.draft.md); màn hình đầu có nút "Đồng ý tham gia"; mã phiên hiển thị khi hoàn thành; admin xóa theo mã (`DELETE /api/admin/survey/s1/respondents/{id}`) | Có bản nháp; **thời hạn lưu trữ chờ Chủ dự án** |
| Backup & restore | `scripts/survey/backup_survey.sh` / `restore_survey.sh` (chỉ 2 bảng khảo sát, SHA-256, đối chiếu số dòng); **diễn tập** `backup_restore_drill.sh` trên 2 CSDL tạm với dữ liệu TEST tổng hợp: **PASS** (3 người / 30 câu trả lời khôi phục giống hệt, hash nội dung `06fa654a…`) | Đã diễn tập |
| Tách TEST / nghiên cứu | Máy chủ khảo sát dùng CSDL riêng; `SURVEY_DATASET` do cấu hình máy chủ quyết định; `RESEARCH` bị từ chối khi `SURVEY_S1_RELEASED=false`; môi trường dev luôn `TEST` | Đã có + test |

## 3. Trình tự triển khai (khi đủ điều kiện)

1. Chủ dự án duyệt bộ câu hỏi + thời hạn lưu trữ → nâng `draft_version`, bỏ dải "BẢN NHÁP".
2. Cấp máy chủ + domain; tạo `infra/survey/survey.env` (không commit) với `SURVEY_DOMAIN`, `ACME_EMAIL`, mật khẩu, `SURVEY_DATASET=TEST`.
3. `docker compose -f docker-compose.yml -f infra/survey/docker-compose.survey.yml --env-file infra/survey/survey.env up -d postgres redis backend survey-proxy`; `alembic upgrade head`.
4. Chạy thử nội bộ trên domain với `TEST` (kiểm tra TLS, 404 cho đường dẫn khác, log không có IP, quota, rate limit, export).
5. Xóa dữ liệu TEST trên máy chủ khảo sát; đặt `SURVEY_DATASET=RESEARCH`, `SURVEY_S1_RELEASED=true` **chỉ sau phê duyệt phát hành**; tạo QR.
6. Backup hằng ngày (`backup_survey.sh`) ra vị trí giới hạn truy cập; theo dõi quota hằng ngày.

## 4. Chưa làm / không được tuyên bố

- Không có domain, không có máy chủ công khai → **không triển khai**, không có link, không có QR.
- Không đặt `SURVEY_S1_RELEASED` ở bất kỳ môi trường nào. Bản chạy trên `127.0.0.1` **không** được coi là phát hành.
