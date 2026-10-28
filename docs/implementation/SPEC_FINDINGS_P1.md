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

## Trạng thái sau quyết định "PHASE 1 FINAL CLOSURE" (2026-10-27) — ứng viên `sa-cand-7da7fbe2e01b`

| Mã | Quyết định | Xử lý | Trạng thái |
|---|---|---|---|
| SF-P1-01 | GEO-06 | Đọc trực tiếp PDF ký số QĐ 19/2025/QĐ-TTg (Phụ lục II, 126 đơn vị Hà Nội) và NQ 1656/NQ-UBTVQH15 (k1–k54, k97–k120); mọi mã/khoản dùng ở v2/v3 trùng khớp; 126/126 tên OSM khớp (`OFFICIAL_SOURCE_VERIFICATION.md`) | **Đã xử lý (OFFICIALLY_VERIFIED cho mã + khoản; hình học vẫn là OSM)** |
| SF-P1-02 | GEO-05 | La Phù lịch sử (`relation/11367506`) dựng được: 0 km² chồng U3; Phenikaa → La Phù = URBAN 2b. Splendora: vị trí chủ đầu tư (Sơn Đồng) khớp polygon OSM | Đạt trên ứng viên; An Khánh lịch sử: vòng hở 1,2 km (PENDING) |
| SF-P1-04 | GEO-01 | Đông Anh: không lấy nguyên xã; không có bằng chứng hình học của thị trấn cũ | **PENDING_GEOMETRY_EVIDENCE** → SF-P1-14 |
| SF-P1-11 | GEO-02 | Tùng Thiện loại khỏi nội đô; danh sách có kiểm soát 49 đơn vị | **Đã xử lý**; Sơn Tây / Chương Mỹ → SF-P1-20 |
| SF-P1-12 | GEO-03 | Hai lớp: polygon (điểm đại diện hoặc điểm mẫu ≤ 150 km) + kiểm tra từng điểm. 47/47 đơn vị vẫn trong polygon (điểm > 150 km bị lớp 2 chặn); 28/32 đơn vị nay vào polygon | Đã xử lý; phần dư → SF-P1-15 |
| SF-P1-13 | GEO-04 | Lớp `EXCLUDED` 324 thành phần / 29,158 km² (không đường bên trong); polygon gốc giữ nguyên | **Đã xử lý** |

### Phát hiện mới

| Mã | Phát hiện | Bằng chứng | Cần quyết định | Ảnh hưởng |
|---|---|---|---|---|
| SF-P1-14 | Mục 2.3 liệt kê **Đông Anh** là nội đô, nhưng không có hình học có căn cứ cho thị trấn cũ (quan hệ lịch sử hở 1.885,6 m) → nội đô v3 không gồm Đông Anh; **Đông Anh → Hoàn Kiếm = INTERCITY (19,678 km)** | `GEOMETRY_REVIEW_P1_FINAL_CLOSURE.md` §2, `TRIP_CLASSIFICATION_EVAL.md` | (a) chấp nhận; (b) polygon Global Gate kiểu U3; (c) ranh giới có nguồn do Chủ dự án cung cấp | P1 |
| SF-P1-15 | Quy tắc điểm mẫu (16 điểm/đơn vị) bỏ sót 4 đơn vị có mép mỏng ≤ 150 km (Hàm Rồng, Vĩnh Lộc, Bao La, Yên Bình; mẫu v2 thấy 147,8–149,6 km) → điểm hợp lệ ở mép bị từ chối | `sensitivity_150km.csv` v2/v3 | Lấy mẫu dày hơn / hợp nhất các lần lấy mẫu / chấp nhận | P1 |
| SF-P1-16 | Ngưỡng snap 300 m (tham số triển khai) từ chối 32% điểm mẫu A4 và 29,5% điểm mẫu đều theo diện tích trong vùng chấp nhận (`NO_ROAD_ACCESS`) | REVIEW.md §13, `TRIP_CLASSIFICATION_EVAL.md` | Xác nhận hoặc đổi `max_snap_m` | P1 |
| SF-P1-17 | Profile car của OSRM cho phép phà: các thành phần đảo có đường (Cát Bà 167 km², 141,5 km) được coi là định tuyến được, có thể qua phà | `components.csv` (serviceable) | Có tính chặng phà là "kết nối đường bộ" không | P1/P2 |
| SF-P1-18 | Thời gian OSRM là dòng tự do: 14 km car 18,3 phút / xe máy 20,6 phút so với 40 / 35 phút ở Mục 10.4 (×2,18 / ×1,70); xe máy chậm hơn ô tô (SF-05, V-03) | `docs/implementation/survey/evidence/s1_6km_eta_osrm.json` | Phương pháp ETA 6 km (hiệu chỉnh theo ví dụ 14 km) | P1 (S1) |
| SF-P1-19 | Splendora: chủ đầu tư công bố 81,2 ha tại Sơn Đồng; polygon OSM 32,0 ha; báo chí 245 ha (km 8+400–10+700, 4 xã cũ) | `GEOMETRY_REVIEW_P1_FINAL_CLOSURE.md` §6 | Chấp nhận phạm vi polygon OSM hiện có | P1 |
| SF-P1-20 | Danh sách nội đô có kiểm soát loại Phường Sơn Tây (k50) và Phường Chương Mỹ (k49, phần lớn từ huyện Chương Mỹ nhưng có phường Biên Giang/Đồng Mai của quận Hà Đông cũ) | REVIEW.md §12 | Xác nhận | P1 |

## Trạng thái sau "P1 FINAL HARDENING & APPROVAL GATES" (2026-10-28) — ứng viên `sa-cand-9bd44393e699`

| Mã | Xử lý | Trạng thái |
|---|---|---|
| SF-P1-14 Đông Anh | Đối chiếu OSM (snapshot + lịch sử v1–v9: chưa từng khép), GADM 4.1 (polygon đầy đủ nhưng không có thẩm quyền, giản lược), HDX COD-AB (chỉ cấp tỉnh sau cải cách). Không nối, không thay thế | **OPEN — blocker** (chờ nguồn có thẩm quyền hoặc quyết định về GADM) |
| SF-P1-15 sót mép 150 km | Lớp 1 = cận dưới trắc địa; 4 đơn vị đã vào; lớp 2 quyết định từng điểm | **Đã xử lý** |
| SF-P1-16 snap 300 m | Chủ dự án chấp nhận tạm thời (GEO-D); điểm đón thực tế: 1,3% bị từ chối do xa đường | Đã xử lý cho MVP; đánh giá lại trước P2 |
| SF-P1-17 phà | `exclude=ferry` trên graph hiện có; 0 chặng phà khi áp chính sách; 7 thành phần chỉ tới được bằng phà vào EXCLUDED | **Đã xử lý** |
| SF-P1-18 ETA 6 km | Chủ dự án chấp nhận 19 / 16 phút làm giả định giờ cao điểm của khảo sát (SURVEY-02) | **Đã xử lý** |
| SF-P1-20 Sơn Tây / Chương Mỹ | Ngoài URBAN trong MVP (GEO-B) | **Đã xử lý** |

### Phát hiện mới

| Mã | Phát hiện | Bằng chứng | Cần quyết định | Ảnh hưởng |
|---|---|---|---|---|
| SF-P1-21 | Thiết kế thí nghiệm S1 đang chạy **không nhận dạng được**: hạng 7/9 (giá, thời gian chỉ đổi theo quãng đường) | `survey/SURVEY_S1_PRICE_VARIATION_DESIGN.md`, `survey/evidence/s1_identifiability.json` | Duyệt ma trận D (hạng 9/9, VIF ≤ 5,3, khả thi 48/48) hoặc phương án khác | **Blocker phát hành S1** |
| SF-P1-22 | Snapshot OSM còn 6 quan hệ cấp tỉnh cũ chồng lên tỉnh mới: `Tỉnh Hòa Bình`, `Tỉnh Yên Bái`, `Tỉnh Quảng Bình`, `Tỉnh An Giang cũ`, `Tỉnh Lào Cai cũ`, `Tỉnh Quảng Trị cũ` | `admin_boundaries.geojsonseq` (39 quan hệ admin_level 4) | Không (đã xử lý trong thống kê; hình học vùng không phụ thuộc) | Thống kê theo tỉnh |
| SF-P1-23 | TOTAL thô v4 là vùng bao ứng viên 68.374 km², lớn hơn nhiều vùng thực sự phục vụ được | `GEOMETRY_REVIEW_P1_HARDENING.md` §3 | Không công bố polygon này như vùng phục vụ | Truyền thông / hiển thị |

## Cập nhật 2026-10-28 — xử lý tiếp 2 blocker

| Mã | Xử lý | Trạng thái |
|---|---|---|
| SF-P1-14 Đông Anh | Quan hệ OSM 17627914 không thực sự hở: way 1412300271 chạy quá nút chữ T 2,25 km. `ST_Polygonize` các way thành viên (không thêm đường) → 4,344 km², IoU 0,855 với GADM, chứa node thị trấn, chia 3 xã đúng NQ1656 k113–k115. Ứng viên v5 `sa-cand-0d5347b4294e` đưa polygon này vào nội đô: Đông Anh → Hoàn Kiếm = URBAN (2a); 15/15 ca PASS trên ứng viên | **Có bằng chứng — chờ Chủ dự án duyệt v5** (không có bản đồ ranh giới có thẩm quyền; v4 giữ làm phương án không có Đông Anh) |
| SF-P1-21 Thiết kế S1 | Thiết kế D hiện thực trong bộ sinh thật, khóa bằng `variation_design.active: false`; trên thiết kế sinh thật: tắt = hạng 7/9 (không nhận dạng), bật = hạng 9/9, VIF ≤ 5,3, 48/48 khả thi | **Sẵn sàng — chờ Chủ dự án duyệt ma trận D** (bật = đổi 1 cờ, không đổi mã) |

## Cập nhật sau "P1 OWNER APPROVAL & FINAL CLOSURE GATES" (2026-10-28)

| Mã | Trạng thái |
|---|---|
| SF-P1-14 Đông Anh | **Đóng cho MVP**: v5 `GEOMETRY_APPROVED_FOR_MVP` (8/8 cổng). Rủi ro còn lại ghi ở `GEOMETRY_REVIEW_P1_HARDENING.md` §10 (không có bản đồ địa giới nhà nước) |
| SF-P1-21 Thiết kế S1 | **Một phần**: D nhận dạng được (hạng 11/11) nhưng hệ số thời gian không ước lượng được ở N = 150 (|t| kỳ vọng 1,1) → đề xuất D2 (|t| 2,7) chờ duyệt |

### Phát hiện mới

| Mã | Phát hiện | Bằng chứng | Cần quyết định |
|---|---|---|---|
| SF-P1-24 | Với β giả định, hệ số đi vòng, chênh "tối đa nếu không ghép" và đi bộ 200 m có |t| kỳ vọng < 1 ở N = 150 kể cả với D2 | `evidence/s1_design_diagnostics.json` | Công bố là phân tích thăm dò, hoặc tăng N / số câu |
| SF-P1-25 | Giới hạn 10 phiên/giờ theo IP băm có thể chặn nhầm nhiều sinh viên dùng chung IP (Wi-Fi trường, NAT) → thiếu mẫu có hệ thống | `SURVEY_S1_DESIGN_REVIEW.md` §14 (R2) | Nâng giới hạn trước khi phát hành |
| SF-P1-26 | Một lần mô phỏng pilot dao động mạnh (t thời gian của D: −1,8 rồi −2,7 với hạt giống khác) → đánh giá phải dựa trên sai số chuẩn kỳ vọng, không dựa trên một lần chạy | `evidence/s1_pilot_*.json` | Không |
