# GEO-06 — Kiểm chứng nguồn hành chính chính thức

Ngày kiểm: 2026-10-27. Phạm vi: mọi mã / khoản dùng trong `config/service_area_rules.candidate.v3.yaml` và bảng
`config/official/hanoi_units_qd19_nq1656.csv`.

## 1. Nguồn đã đọc trực tiếp (bản gốc, chữ ký số, cổng Chính phủ)

| Văn bản | Tệp gốc | MD5 tệp tải về | Cách đọc | Phần đã đọc |
|---|---|---|---|---|
| Quyết định 19/2025/QĐ-TTg (30/06/2025, hiệu lực 01/07/2025) — Bảng danh mục mã số đơn vị hành chính | `https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/19ttg.signed.pdf` (143 trang, bản quét) | `13C91AB4E9381A0D449FF4397A74796C` | Trích ảnh từng trang (pypdf), đọc trực quan | Trang 1–5 (quyết định), **Phụ lục II trang 6–10: toàn bộ 126 đơn vị Thành phố Hà Nội** ("Tổng số đơn vị hành chính cấp xã: 126, gồm 75 xã, 51 phường") |
| Nghị quyết 1656/NQ-UBTVQH15 (16/06/2025) — sắp xếp ĐVHC cấp xã của Hà Nội | `https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/6/1656-nq.signed.pdf` (17 trang, bản quét) | `E256FF94146F3050A20CDF32CDCF5B6B` | Trích ảnh từng trang, đọc trực quan | Trang 1–8 (Điều 1 khoản 1–54: **51 phường k1–k51**, xã k52–k54), trang 13–15 (khoản 97–120) |

## 2. Kết quả

| Nội dung | Kết quả | Mức |
|---|---|---|
| 126 mã + tên đơn vị Hà Nội (51 phường, 75 xã) | Chép vào `hanoi_units_qd19_nq1656.csv`; không trùng mã; tổng khớp tiêu đề phụ lục | **OFFICIALLY_VERIFIED** (QĐ19 PDF) |
| Khoản NQ1656 của 51 phường (k1–k51) | Đọc từng khoản; tên phường mới khớp tên trong QĐ19 | **OFFICIALLY_VERIFIED** (NQ1656 PDF) |
| Khoản của các xã dùng trong ánh xạ: Thanh Trì k52, Đại Thanh k53, Sơn Đồng k104, An Khánh k105, Đan Phượng k106, Ô Diên k107, Liên Minh k108, Gia Lâm k109, Thuận An k110, Bát Tràng k111, Phù Đổng k112, Thư Lâm k113, Đông Anh k114, Phúc Thịnh k115 | Đọc từng khoản | **OFFICIALLY_VERIFIED** |
| Khoản của 61 xã còn lại | Không chép (không dùng trong quy tắc) | Không kiểm (không cần) |
| Mã các đơn vị v2 đã dùng (`00070`, `09556`, `09562`, `09886`, `00166`, `00592`, `00634`, `09871`, `09877`, `00565`, `00577`, `00454`, `00475`, `00466`) | **Trùng khớp** bản chính thức (trước đây lấy từ bảng tra cứu thứ cấp) | Nâng lên OFFICIALLY_VERIFIED |
| Nội dung khoản v2 đã dùng (k25, k35, k37, k43–k45, k104, k105, k109, k111, k113–k115) | **Trùng khớp** nội dung đọc từ PDF (trước đây đọc qua công cụ tóm tắt) | Nâng lên OFFICIALLY_VERIFIED |
| Đối chiếu snapshot OSM đã khóa (`source.osm.pbf` MD5 `bdf51651…`) | Pipeline: 126/126 tên đơn vị OSM `admin_level=6` trong Hà Nội khớp tên chính thức; 0 thừa, 0 thiếu. OSM **không** có thẻ mã chính thức (`ref`) → đối chiếu theo tên (chuẩn hóa NFC + vị trí dấu thanh) | **Khớp theo tên** (OSM là dữ liệu cộng đồng, không phải nguồn chính thức) |

## 3. Nguồn thứ cấp còn lại

| Nội dung | Nguồn | Ghi chú |
|---|---|---|
| Ranh giới hình học của đơn vị (polygon) | OpenStreetMap (snapshot khóa) | Văn bản pháp lý không kèm bản đồ số; hình học là OSM |
| Ranh giới lịch sử trước 2025 (Đông Anh, An Khánh, La Phù, Trâu Quỳ, Mỹ Đình 1/2) | OSM `boundary=historic` | Bằng chứng hình học, không phải nguồn pháp lý |
| Vị trí dự án Splendora | Website chủ đầu tư `splendora.vn` (địa chỉ "Km10+600 Đại lộ Thăng Long, Sơn Đồng"; quy mô 81,2 ha); báo chí (km 8+400–10+700; 245 ha) | Nguồn chủ đầu tư/báo chí, **không** phải văn bản quy hoạch |
| "Quận nội thành" trước 2025 (cơ sở danh sách nội đô) | Thành phần các khoản k1–k48 của NQ1656 (đọc trực tiếp) liệt kê phường của các quận cũ | Đây là suy luận từ thành phần khoản, không phải một danh mục "nội đô" chính thức |
