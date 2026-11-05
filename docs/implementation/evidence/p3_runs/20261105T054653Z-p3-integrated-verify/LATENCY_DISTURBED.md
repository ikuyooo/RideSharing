# Độ trễ không hợp lệ — kết quả kiểm chứng vẫn hợp lệ

- `docker_stats.jsonl` có khoảng trống 06:15:20Z → 06:48:01Z (host suspend) trong lượt này. Mọi số **độ trễ** của lượt `verify` không dùng cho kết luận.
- Các phán quyết **kiểm chứng** (vi phạm RB, `single_rejections`, `plan_checks`) không phụ thuộc thời gian đo: mỗi ứng viên / lần loại được kiểm lại bằng SQL riêng và OSRM `/route` / `/table` độc lập sau khi sinh — giữ nguyên giá trị.
