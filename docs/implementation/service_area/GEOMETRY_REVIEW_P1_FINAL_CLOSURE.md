# Rà soát hình học — PHASE 1 FINAL CLOSURE (GEO-01 … GEO-06)

- **Phiên bản mới:** `sa-cand-7da7fbe2e01b` — **CANDIDATE, không phải GEOMETRY_APPROVED.** Bundle: [`sa-cand-7da7fbe2e01b/`](sa-cand-7da7fbe2e01b/REVIEW.md)
- Giữ nguyên, không sửa: `sa-cand-3873dfbee116` (v1), `sa-cand-acce13159a8c` (v2) — DB và bundle.
- Quy tắc: [`config/service_area_rules.candidate.v3.yaml`](../../../config/service_area_rules.candidate.v3.yaml); bảng chính thức: [`config/official/hanoi_units_qd19_nq1656.csv`](../../../config/official/hanoi_units_qd19_nq1656.csv); kiểm chứng nguồn: [`OFFICIAL_SOURCE_VERIFICATION.md`](OFFICIAL_SOURCE_VERIFICATION.md).
- So sánh: [`COMPARE_sa-cand-acce13159a8c_vs_sa-cand-7da7fbe2e01b.md`](COMPARE_sa-cand-acce13159a8c_vs_sa-cand-7da7fbe2e01b.md), [`COMPARE_sa-cand-3873dfbee116_vs_sa-cand-7da7fbe2e01b.md`](COMPARE_sa-cand-3873dfbee116_vs_sa-cand-7da7fbe2e01b.md). Đánh giá phân loại thực: [`sa-cand-7da7fbe2e01b/TRIP_CLASSIFICATION_EVAL.md`](sa-cand-7da7fbe2e01b/TRIP_CLASSIFICATION_EVAL.md).

## 1. Diện tích, thành phần, đơn vị

| | v1 `3873dfbee116` | v2 `acce13159a8c` | **v3 `7da7fbe2e01b`** |
|---|---|---|---|
| URBAN | 511,166 km², 2 phần | 484,116 km², 7 phần | **340,034 km², 6 phần** |
| TOTAL (đa giác hành chính gốc) | 26.349,323 km², 222 phần | 38.618,767 km², 332 phần | **42.275,390 km², 335 phần** |
| EXCLUDED (không phục vụ được) | — | — | **29,158 km², 324 phần** |
| Vùng chấp nhận lớp 1 (TOTAL − EXCLUDED) | — | — | **42.246,232 km²** |
| Lớp 2 (từng điểm) | không | không | **có** (snap ≤ 300 m, có tuyến từ anchor, ≤ 150 km) |

v2 → v3: URBAN **−144,083 km²** (bỏ Xã Đông Anh, Phường Chương Mỹ, Phường Tùng Thiện, Phường Sơn Tây; không thêm đơn vị); 24 node `place=*` rời nội đô, 0 vào. TOTAL gốc **+3.656,622 km²** (35 đơn vị thêm theo quy tắc điểm mẫu, 0 đơn vị bị bỏ); 96 node vào vùng tổng.
Nội đô v3 = 48 phường (NQ1656 k1–k48) + Xã Gia Lâm (k109) + 7 polygon U3 An Khánh/Splendora. 0 km² nội đô nằm trong EXCLUDED.

## 2. GEO-01 Đông Anh

| Kiểm tra | Kết quả |
|---|---|
| Phạm vi tra cứu Thư Lâm / Đông Anh / Phúc Thịnh (k113 / k114 / k115, đọc từ PDF NQ1656) | Đã dùng; **không** đưa nguyên xã nào vào nội đô (bỏ quy tắc U2 `Xã Đông Anh` của v2) |
| Ranh giới thị trấn Đông Anh cũ trong snapshot | Có `relation/17627914` (`boundary=historic`, admin_level 8): 9 way, gộp thành **1 chuỗi hở, hai đầu cách nhau 1.885,6 m** → không dựng được vùng. Không tự khép |
| Polygon khu dân cư/đô thị có tên gắn với thị trấn cũ | **Không có.** Trong khung 105,80–105,90 E × 21,09–21,19 N chỉ có 6 polygon `landuse=residential` có tên: 3 thôn (Hương Trầm, Biểu Khê, Ngọc Giang) và 3 phân khu của khu đô thị mới **Global Gate** (Thịnh Vượng, Cát Tường, Tinh Hoa) — không phải thị trấn cũ. Bằng chứng còn lại chỉ là điểm: 3 địa chỉ `addr:subdistrict=Thị trấn Đông Anh`, tên cũ của 2 trường học, trạm xe buýt "Thị trấn Đông Anh" |
| Phương án cho Chủ dự án (chưa áp dụng) | (a) giữ PENDING; (b) dùng polygon Global Gate làm "khu đô thị vệ tinh" kiểu U3 (không phải thị trấn cũ); (c) Chủ dự án cung cấp ranh giới thị trấn cũ có nguồn |
| Kết luận | **`PENDING_GEOMETRY_EVIDENCE`** — Đông Anh không thuộc nội đô v3 |
| Hệ quả (đánh giá thực) | Node thị trấn Đông Anh → Hoàn Kiếm: **INTERCITY (19,678 km > 15 km)** — **trái kỳ vọng Mục 2.3** (Đông Anh là nội đô). Cần Chủ dự án quyết định (SF-P1-14) |

## 3. GEO-02 Tùng Thiện và danh sách có kiểm soát

Danh sách 49 đơn vị, mỗi dòng có mã QĐ19 + khoản NQ1656 (REVIEW.md §12), pipeline đối chiếu với bảng chính thức (0 sai lệch). Không còn quy tắc "mọi phường".

| Đơn vị | Khoản | Thành phần (NQ1656) | v3 |
|---|---|---|---|
| Phường Tùng Thiện (09604) | k51 | phường/xã của thị xã Sơn Tây cũ | **Loại** (quyết định GEO-02); vẫn trong TOTAL. Xuân Khanh → Hoàn Kiếm = INTERCITY (47,377 km) |
| Phường Sơn Tây (09574) | k50 | thị xã Sơn Tây cũ | Loại (không phải quận nội thành, không có tên ở Mục 2.3) — **chờ xác nhận** |
| Phường Chương Mỹ (10015) | k49 | phường Biên Giang + phần còn lại Đồng Mai (quận Hà Đông cũ) + thị trấn Chúc Sơn + 5 xã huyện Chương Mỹ | Loại — **chờ Chủ dự án** |

## 4. GEO-03 Giới hạn 150 km — hai lớp

Quyết định triển khai bổ sung của Chủ dự án, **không phải công thức Revision 9**. Anchor: node 74132064 (105,854041; 21,0283334).

- **Lớp 1 (polygon):** đơn vị vào TOTAL nếu điểm đại diện **hoặc** một trong 16 điểm mẫu (dải ±30 km, `ST_GeneratePoints` seed 1) ≤ 150 km đường bộ; trừ lớp EXCLUDED.
- **Lớp 2 (từng pickup/dropoff, một request OSRM `/table`):** snap ≤ 300 m (**tham số triển khai chờ xác nhận**), có tuyến từ anchor, ≤ 150 km (đúng 150 km được nhận; test 150,000 → nhận, 150,001 → từ chối), pickup → dropoff có tuyến (không thì `ROUTE_NOT_FOUND`). Lỗi trả `OUT_OF_SERVICE_AREA` kèm `details.reason`.
- **Xem lại 47 / 32 đơn vị của v2:** 47/47 đơn vị "được chọn, một phần > 150 km" vẫn trong polygon — điểm vượt 150 km nay bị lớp 2 chặn. 28/32 đơn vị "bị loại, một phần ≤ 150 km" nay vào polygon nhờ quy tắc điểm mẫu (+7 đơn vị mới do lấy mẫu dày hơn; tổng thêm 35). **4/32 không vào** (Phường Hàm Rồng, Xã Vĩnh Lộc — Thanh Hóa; Xã Bao La — Phú Thọ; Xã Yên Bình — Lào Cai): mẫu v3 không trúng phần mép ≤ 150 km (v2 thấy 1–2/12 điểm ở 147,8–149,6 km) → điểm hợp lệ ở mép các xã này bị từ chối (SF-P1-15).
- **Điểm trong polygon nhưng không phục vụ được:** 3.339 điểm mẫu A4 trong đơn vị được chọn: phục vụ 1.876, `NO_ROAD_ACCESS` 1.082, `BEYOND_MAX_ROAD_DISTANCE` 381. Mẫu ngẫu nhiên đều theo diện tích (400 điểm, seed 1) trên toàn vùng chấp nhận: phục vụ 263, `NO_ROAD_ACCESS` 118, `BEYOND_MAX_ROAD_DISTANCE` 19. Mẫu đều theo diện tích đặt nhiều điểm vào ruộng/rừng; điểm đón thực tế tập trung gần đường — nhưng ngưỡng 300 m có ảnh hưởng đáng kể ở nông thôn (SF-P1-16).

## 5. GEO-04 Đảo / mảnh không có đường

Polygon gốc giữ nguyên; không xóa / lấp / nối. Thăm dò mỗi thành phần không phải khối chính tại `ST_PointOnSurface` + 4 điểm seed: có đường ô tô bên trong khi một điểm snap vào vị trí đường **nằm trong** thành phần; có tuyến khi vị trí đó định tuyến được từ anchor.

| Kết quả | Số thành phần | Diện tích |
|---|---|---|
| EXCLUDED — không có đường định tuyến bên trong (mảnh đảo 314 + mảnh nghi chồng lớp 10) | **324** | **29,158 km²** (lớn nhất 5,117 km², Phường Hà An) |
| EXCLUDED — có đường nhưng không có tuyến từ anchor | 0 | 0 |
| Giữ — có đường và có tuyến (Đặc khu Cát Hải 167,06 km² ở 141,5 km, Xã Hưng Phú, Phường Tuần Châu, …) | 10 | — |

Phân bố EXCLUDED theo đơn vị: Đặc khu Cát Hải 211, Phường Bãi Cháy 56, Phường Tuần Châu 36, Phường Hà An 17, Xã Rạng Đông 2, Xã Đồng Châu 1, Xã Vạn Lộc 1. Danh sách đầy đủ + lý do: `components.csv` (`serviceable = False`), hình học `excluded.geojson`. So với v2: 312 mảnh đảo của v2 nay 314 (do thêm đơn vị). **Lưu ý:** profile car của OSRM cho phép phà (`route=ferry`) — tuyến tới Cát Bà có thể đi qua phà (SF-P1-17).

## 6. GEO-05 Splendora / An Khánh / La Phù

- Splendora = Bắc An Khánh **theo tên** (quyết định GEO-05). Tên dự án không được coi là bằng chứng ranh giới.
- Vị trí chủ đầu tư công bố (`splendora.vn`): "Km10+600 Đại lộ Thăng Long, **Sơn Đồng**", quy mô 81,2 ha; 3 polygon OSM Splendora nằm trong **Xã Sơn Đồng** (k104 nhận một phần xã An Khánh cũ) → **nhất quán về vị trí**. Diện tích OSM 32,0 ha ≈ 39% quy mô công bố → nội đô chỉ gồm phần đã có polygon (thận trọng). Báo chí (thứ cấp) ghi km 8+400–10+700, 245 ha — không khớp số liệu chủ đầu tư.
- Ranh giới lịch sử: **Xã La Phù** `relation/11367506` dựng được (3,510 km²): 0 km² chồng U3; 7,8% nằm trong nội đô (phần thuộc Phường Dương Nội theo k44 — đúng NQ1656). Node La Phù ngoài nội đô → Phenikaa → La Phù = **URBAN qua nhánh 2b (5,977 km)** ✔. **Xã An Khánh** cũ `relation/11367508`: vòng hở 1.200,6 m → `PENDING_GEOMETRY_EVIDENCE`.
- Đối chiếu khác: Thị trấn Trâu Quỳ cũ 95,6% trong Xã Gia Lâm (nội đô), 4,4% trong Xã Bát Tràng — khớp k109/k111. Mỹ Đình 1/2 cũ: 100% trong nội đô (Phường Từ Liêm + Cầu Giấy) — khớp k25/k35.

## 7. Ca kiểm thử địa danh (đánh giá thực, sản phẩm phân loại + OSRM)

| Ca | Kết quả v3 | Ghi chú |
|---|---|---|
| Phenikaa → La Phù (72.2) | URBAN, 2b, 5,977 km — PASS | |
| ~3 km trong TP Hưng Yên (72.2) | UNSUPPORTED (3b) — PASS | |
| Vùng đệm 14,992 / 15,321 km | URBAN 2b / INTERCITY 3a — PASS | |
| Giới hạn 149,984 / 150,024 km | INTERCITY / OUT_OF_SERVICE_AREA (lớp 2: `BEYOND_MAX_ROAD_DISTANCE`) — PASS | |
| Đông Anh → Hoàn Kiếm | **INTERCITY 19,678 km — FAIL so với Mục 2.3** | GEO-01 PENDING |
| An Khánh (Splendora) → Hoàn Kiếm | URBAN 2a — PASS | |
| La Phù → Hoàn Kiếm | INTERCITY 17,191 km (thông tin) | |
| Tùng Thiện → Hoàn Kiếm | INTERCITY 47,377 km — PASS | GEO-02 |
| Phố Hiến → Hoàn Kiếm | INTERCITY 56,379 km — PASS | |
| Điểm trong polygon > 150 km | OUT_OF_SERVICE_AREA (154,347 km) — PASS | lớp 2 |
| Điểm trong polygon xa đường | OUT_OF_SERVICE_AREA (snap 373,1 m) — PASS | lớp 2 |
| Điểm trong mảnh EXCLUDED lớn nhất | OUT_OF_SERVICE_AREA (`UNSERVICEABLE_COMPONENT`) — PASS | lớp 1 |

"Nghiệm thu = NOT_VERIFIED" cho mọi ca vì hình học chưa được phê duyệt.

## 8. Tái lập, phiên bản, checksum

- Version = `sa-cand-` + 12 hex SHA-256 của MANIFEST export, quy tắc, giới hạn, anchor, danh sách đơn vị/polygon. `MANIFEST_HISTORIC` tách riêng nên id v1/v2 không đổi.
- **v2 tái lập bằng mã mới:** cùng id `sa-cand-acce13159a8c`, `unchanged (ST_Equals)`, GeoJSON SHA-256 trùng (`d3e27cdc…f232f` / `115295ba…52609`), ghi ra thư mục tạm (bundle v2 không bị chạm).
- **v3 import lần 2:** URBAN / TOTAL / EXCLUDED đều `unchanged (ST_Equals)`.
- SHA-256 v3: `urban.geojson` `4a86d3ab…d539`, `total.geojson` `0c91cc6c…b7a4`, `excluded.geojson` `ba34ecc6…564e` (đầy đủ trong `CHECKSUMS.sha256`).
- Chống ghi đè: pipeline từ chối ghi vào bundle đã tồn tại (`ensure_new_bundle`, có test). Bundle v3 được tạo lại một lần trong phiên này, trước khi có ai rà soát, để sửa chẩn đoán khoảng hở vòng ranh giới (lần đầu chỉ đo khoảng hở giữa các chuỗi khác nhau nên ghi `None`); hình học không đổi (`unchanged`).
- Sự cố đã khắc phục: `service-area-build` từng dùng ảnh Docker riêng (cũ 41 giờ) → lần chạy đầu dùng mã cũ, đã dừng trước khi ghi DB; nay hai service dùng chung tag `ridesharing-backend:local`.
