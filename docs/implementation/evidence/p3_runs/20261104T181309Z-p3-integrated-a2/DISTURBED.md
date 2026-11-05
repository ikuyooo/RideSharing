# DISTURBED — máy chủ bị tạm dừng (suspend) giữa lượt đo

- `docker_stats.jsonl` có khoảng trống 18:15:07Z → 18:48:45Z (~33 phút không có mẫu): máy host bị suspend trong lúc cấu hình `200x20` đang chạy.
- Các độ trễ của cấu hình `200x20` (p95 260 ms, p99 308 ms) có thể chứa thời gian tạm dừng; **không** dùng cho kết luận hiệu năng. Các cấu hình chạy trọn trước hoặc sau khoảng trống được giữ làm tham khảo, không làm bằng chứng chính.
