# Ghi nhận không nhất quán / thiếu dữ liệu phát hiện trong Phase 1

Không mục nào dưới đây được tự giải quyết bằng cách sửa đặc tả. Trạng thái: **chờ Chủ dự án**.

| ID | Phát hiện | Bằng chứng | Ảnh hưởng | Đề xuất | Phase |
|---|---|---|---|---|---|
| SF-P1-01 | Dữ liệu OSM (snapshot 2026-10-23) phản ánh cải cách hành chính 2025: 34 đơn vị cấp tỉnh (tỉnh sáp nhập) và cấp xã/phường; **không còn cấp quận/huyện**. Revision 9 Mục 1, 2.3, 72.2 dùng tên đơn vị trước 2025 (Hà Đông, Hoài Đức, Gia Lâm, Đông Anh, Hải Dương, Hà Nam, Vĩnh Phúc, Hòa Bình, "TP Hưng Yên"). | OSM `admin_level=4`: 33 đơn vị dựng được; `admin_level=6`: 3.321 xã/phường; `docs/implementation/service_area/sa-cand-3873dfbee116/REVIEW.md` | Không thể ánh xạ 1-1 tên đặc tả sang đơn vị hiện hành | Phê duyệt bảng ánh xạ (REVIEW.md mục 1) | P1 |
| SF-P1-02 | **An Khánh ↔ La Phù mâu thuẫn**: Mục 2.3 liệt kê An Khánh là vùng nội đô; Mục 72.2 coi La Phù là "sát ngoài đa giác nội đô". Trong dữ liệu hiện hành La Phù (node 12147486706) nằm **trong** Xã An Khánh. | REVIEW.md mục 5; `TRIP_CLASSIFICATION_EVAL.md` (Phenikaa → La Phù ra URBAN qua bước 2a, không phải 2b) | Ca 72.2 cho đúng kết quả nhưng sai đường đi thuật toán | Chọn: (a) giữ Xã An Khánh trong nội đô và chấp nhận 72.2 đi bước 2a; (b) bỏ Xã An Khánh khỏi nội đô; (c) phương án khác | P1 |
| SF-P1-03 | **Mỹ Đình** không có đối tượng `place=*` nào trong dữ liệu OSM | Tra cứu places export | Không kiểm tra được địa danh này | Chủ dự án cung cấp điểm đại diện (hoặc chấp nhận "Phường Từ Liêm" nếu có căn cứ) | P1 |
| SF-P1-04 | **Gia Lâm, Đông Anh**: node địa danh mang tên này nằm trong xã khác (Xã Thuận An, Xã Phúc Thịnh) chứ không trong "Xã Gia Lâm"/"Xã Đông Anh" được chọn | REVIEW.md mục 5 | Quy tắc U2 (chọn xã theo tên) có thể không đại diện đúng "Gia Lâm"/"Đông Anh" của Mục 2.3 | Chủ dự án xác định danh sách xã/phường nội đô | P1 |
| SF-P1-05 | **Điểm gốc 150 km chưa được quy định** (`ANCHOR_DEFINITION_REQUIRED`) | Mục 2.3 chỉ nêu "bán kính đường bộ tối đa 150 km" | Phạm vi vùng tổng phụ thuộc điểm gốc | Đề xuất: node `admin_centre` của quan hệ Hà Nội (node 74132064) | P1 |
| SF-P1-06 | **Phạm vi tỉnh của vùng tổng**: ngoài 6 tỉnh Mục 1 nêu tên, còn 164 xã/phường của Thái Nguyên, Thanh Hóa, Lạng Sơn, Tuyên Quang, Quảng Ninh, Lào Cai, Sơn La nằm trong 150 km đường bộ | REVIEW.md mục 7 | Mục 1 dùng "như" (liệt kê ví dụ?) hay danh sách đóng? | Chủ dự án chọn danh sách đóng hay "mọi tỉnh trong 150 km" | P1 |
| SF-P1-07 | Vùng tổng ứng viên gồm **222 mảnh rời** (213 mảnh < 1 km²); vùng nội đô gồm 2 mảnh (455 km² + 55,9 km²) | REVIEW.md checks; truy vấn `ST_Dump` | Điểm rơi vào khe/mảnh lẻ có thể bị phân loại ngoài vùng | Duyệt có cần lấp lỗ/làm trơn (quy tắc bổ sung) | P1 |
| SF-P1-08 | Mục 6 nêu `max_passenger_detour_ratio` "mặc định 0.30" nhưng **Baseline YAML không có khóa này** | Mục 6; Baseline §4 | P1 lưu NULL khi khách không nhập; giá trị mặc định cần cho ràng buộc cứng #5 ở P2 | Chủ dự án xác nhận nguồn giá trị mặc định | P2 |
| SF-P1-09 | Revision 9 ví dụ "TP Hưng Yên" — trong dữ liệu hiện hành đại diện bằng node `Phố Hiến` (place=city) | REVIEW.md mục 5 | Giả định cần xác nhận | Xác nhận | P1 |
| SF-P1-10 | 1 xã/phường của Hải Phòng nằm ngoài bbox của extract định tuyến (P0) nên bị loại khỏi vùng tổng | REVIEW.md mục 7 | Nhỏ | Chấp nhận, hoặc mở rộng bbox (cần build lại OSRM ~2,5 giờ) | P1 |

---

## Trạng thái sau quyết định "P1: GEOGRAPHY & S1 CLOSURE" (2026-10-26)

Bảng gốc ở trên được giữ nguyên. Phiên bản ứng viên mới: **`sa-cand-acce13159a8c`** (quy tắc `config/service_area_rules.candidate.v2.yaml`); `sa-cand-3873dfbee116` giữ nguyên là CANDIDATE với toàn bộ bằng chứng gốc. So sánh: `docs/implementation/service_area/COMPARE_sa-cand-3873dfbee116_vs_sa-cand-acce13159a8c.md`.

| ID | Quyết định | Đã làm | Trạng thái |
|---|---|---|---|
| SF-P1-01 | A1 | Bảng ánh xạ có mã QĐ 19/2025/QĐ-TTg, khoản NQ 1656/NQ-UBTVQH15, quan hệ OSM, mức chắc chắn (`admin_mapping.csv`, REVIEW.md §1). Kiểm chứng chéo: bảng mã 126 đơn vị (51 phường + 75 xã) khớp 126 đơn vị OSM của Hà Nội, quy tắc U1 chọn đúng 51 phường. Hạn chế: nội dung NQ 1656 đọc qua công cụ tóm tắt; mã QĐ 19 lấy từ bảng tra cứu thứ cấp trích dẫn QĐ 19 | **Đã xử lý ở mức ánh xạ; cần đối chiếu bản PDF chính thức trước phê duyệt cuối** |
| SF-P1-02 | A2 | NQ 1656 k44/k105: La Phù bị chia (một phần vào Phường Dương Nội, phần còn lại vào Xã An Khánh). Không có ranh giới La Phù lịch sử dạng hình học → không vẽ đường ranh. Thay Xã An Khánh nguyên khối bằng **polygon khu đô thị An Khánh có trên OSM** (U3: Nam An Khánh, Vista Lago, The Golden, An Khánh Ecomony, Splendora×3). Kết quả: La Phù **ngoài** nội đô; Phenikaa → La Phù = URBAN qua **nhánh 2b** (5,977 km ≤ 15 km) | **Đạt mục tiêu kiểm thử trên ứng viên**; ranh giới La Phù lịch sử: `PENDING_GEOMETRY_EVIDENCE`; Splendora = Bắc An Khánh là giả định cần xác nhận |
| SF-P1-03 | A3 | NQ 1656 k25/k35: Mỹ Đình 1, 2 chia vào Phường Cầu Giấy + Phường Từ Liêm (cả hai là phường, thuộc nội đô). Điểm kiểm tra: SVĐ Quốc gia Mỹ Đình (way 533838254), Bến xe Mỹ Đình (relation 21430094) → trong nội đô | **Đã xử lý (HIGH)** |
| SF-P1-04 | A3 | Gia Lâm: k109 — Xã Gia Lâm nhận toàn bộ dân số thị trấn Trâu Quỳ; điểm "Khu tái định cư Trâu Quỳ" → trong nội đô (MEDIUM). Đông Anh: thị trấn chia 3 (k113 Thư Lâm, k114 Đông Anh, k115 Phúc Thịnh); node thị trấn nằm ở Phúc Thịnh → **MISMATCH** | Gia Lâm: đã xử lý (MEDIUM). **Đông Anh: PENDING** — cần chọn tập xã đại diện |
| SF-P1-05 | A4 | Đã xác minh trên `source.osm.pbf` (MD5 `bdf51651…`): node 74132064 v96, thành viên `r1903516` vai trò `admin_centre`, `place=city`, `capital=yes`, `wikidata=Q1858`, (105.854041, 21.0283334). Độ nhạy: 201 đơn vị trong ±20 km ngưỡng được lấy 12 điểm mẫu: **47 đơn vị được chọn có một phần vượt 150 km**, **32 đơn vị bị loại có một phần trong 150 km** | Điểm gốc: đạt điều kiện kỹ thuật. **Việc chọn theo điểm đại diện không bảo đảm mọi điểm của đơn vị ≤ 150 km** — cần quyết định (SF-P1-12) |
| SF-P1-06 | A5 | Phạm vi = mọi tỉnh, chọn từng xã/phường (không đưa nguyên tỉnh). Thêm 164 đơn vị của 7 tỉnh | Đã áp dụng trong ứng viên |
| SF-P1-07 | A6 | Không xóa/nối/lấp gì. Phân loại 332 thành phần vùng tổng: 1 khối chính; 312 mảnh đảo **không có đường định tuyến** (Đặc khu Cát Hải 211, Bãi Cháy 56, Tuần Châu 36, Hà An 17… tổng 29,4 km²); 8 mảnh tách rời có đường; 11 mảnh nghi do chồng lớp dữ liệu (< 0,01 km², cách < 10 m); lỗ khối chính: 3 (2 lỗ nhỏ nghi khe ranh giới). Nội đô 7 thành phần: khối chính, Phường Tùng Thiện tách rời, 5 polygon U3 | Đã phân loại (`components.csv`); quyết định xử lý đảo không đường: SF-P1-13 |
| SF-P1-08 | A7 | `max_passenger_detour_ratio` mặc định 0,30 (Mục 6) khi khách không nhập; không thêm vào Baseline; test mặc định/giá trị nhập/biên [0, 1] | **Đã xử lý** |
| SF-P1-09 | A8 | Phố Hiến dùng làm điểm đại diện ứng viên; ca 3 km → UNSUPPORTED ✔. Ngữ cảnh: OSRM Hà Đông → Phố Hiến = 58,055 km so với 65 km minh họa Mục 25.2 (−10,7%) | Dùng làm điểm kiểm thử; **không phải ánh xạ chính thức** |
| SF-P1-10 | A9 | Giữ bbox, không build lại OSRM. Loại 2.045 đơn vị có điểm đại diện ngoài bbox định tuyến (`excluded_units.csv`, lý do ghi từng dòng); 0 đơn vị không định tuyến được; 0 đơn vị được chọn có phần nằm ngoài bbox | Đã xử lý |

### Phát hiện mới

| ID | Phát hiện | Bằng chứng | Đề xuất | Phase |
|---|---|---|---|---|
| SF-P1-11 | Quy tắc U1 ("mọi phường") đưa **Phường Tùng Thiện** (khu vực Sơn Tây cũ, ~55,9 km², tách rời khối chính) vào nội đô; Mục 2.3 nói "quận nội thành và khu đô thị vệ tinh **liền kề**" | `components.csv` (URBAN) | Quyết định giữ hay loại các phường không liền kề | P1 |
| SF-P1-12 | Chọn đơn vị theo điểm đại diện: 47 đơn vị được chọn có phần > 150 km; 32 đơn vị bị loại có phần ≤ 150 km (Thanh Hóa 27, Lạng Sơn 15, Lào Cai 7…) | `sensitivity_150km.csv` | (a) chấp nhận sai lệch ở mức đơn vị; (b) cơ chế kiểm tra điểm đón/trả thực tế: khoảng cách OSRM từ điểm gốc ≤ 150 km tại thời điểm đặt — **là quy tắc nghiệp vụ mới, chưa áp dụng**, cần ghi quyết định | P1/P2 |
| SF-P1-13 | 312 mảnh đảo không có đường định tuyến (29,4 km²) nằm trong vùng tổng; theo A9 không sẵn sàng phục vụ | `components.csv` (NO_ROUTABLE_ROAD_INSIDE) | Loại các mảnh này khỏi vùng tổng (giảm 332 → ~20 thành phần) — **chưa áp dụng**, cần duyệt quy tắc | P1 |
