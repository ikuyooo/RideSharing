# DISTURBED — không dùng làm số đo hiệu năng P2

- Lượt chạy hoàn tất (exit 0) nhưng **chạy song song** với việc cài lại môi trường Python (`pip install`, tải nặng I/O + CPU trên cùng máy) và hai lần chạy pytest. Lượt đầu tiên sau khi Docker Desktop vừa khởi động (OSRM nguội): cấu hình `50x0` có 1 `RoutingTimeout`.
- Mã được nạp lúc 17:10:07Z là mã P2 + dòng đo phạm vi 1 (chưa có thay đổi P3 trong các module được import) — nhưng điều kiện đo vi phạm quy trình SF-P2-16.
- Giữ nguyên làm bằng chứng lịch sử; **không** dùng cho kết luận nghiệm thu. Số đo hợp lệ: các lượt `acceptance-final-*` chạy trên worktree tách biệt tại commit khóa P2.
