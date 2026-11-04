# INVALID — mã không nhất quán trong lúc đo

- Lượt chạy bắt đầu 17:19:39Z trên thư mục làm việc **đang được sửa** (mount `/repo`). Khi tiến trình khởi động, `pricing/tariff.py` đã được viết lại cho P3 (nhận mét / giây) trong khi `candidate/generator.py` cũ vẫn truyền km / phút: giá dùng cho RB 8 sai, và mỗi lần gọi `pool_quote` dựng lại tham số (bước 3 chậm hơn).
- Kết quả **không phải** số đo của P2 và không phải số đo của P3. Giữ làm bằng chứng lịch sử, không dùng cho kết luận nào.
- Khắc phục quy trình: benchmark chạy trên worktree riêng tại một commit cố định (manifest `git_dirty_files = 0`).
