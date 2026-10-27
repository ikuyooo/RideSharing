# Rà soát hình học — P1 FINAL HARDENING (GEO-A … GEO-F)

- **Ứng viên mới:** `sa-cand-9bd44393e699` (quy tắc [`service_area_rules.candidate.v4.yaml`](../../../config/service_area_rules.candidate.v4.yaml)) — **CANDIDATE, không GEOMETRY_APPROVED** (Đông Anh còn blocker).
- Giữ nguyên: `sa-cand-3873dfbee116`, `sa-cand-acce13159a8c`, `sa-cand-7da7fbe2e01b` (DB + bundle; `git status` sạch trên các bundle này).
- So sánh: [`COMPARE_sa-cand-7da7fbe2e01b_vs_sa-cand-9bd44393e699.md`](COMPARE_sa-cand-7da7fbe2e01b_vs_sa-cand-9bd44393e699.md); đánh giá thực: [`sa-cand-9bd44393e699/TRIP_CLASSIFICATION_EVAL.md`](sa-cand-9bd44393e699/TRIP_CLASSIFICATION_EVAL.md); khảo sát điểm đón: `sa-cand-9bd44393e699/PICKUP_SURVEY.json`; Đông Anh: `sa-cand-9bd44393e699/historic_sources_dong_anh.json`.

## 1. GEO-A — Đông Anh: nguồn ranh giới thị trấn cũ

| Nguồn | Loại hình học | Độ đầy đủ | Sai lệch so với OSM `relation/17627914` | Ảnh hưởng Đông Anh → Hoàn Kiếm | Khả năng sử dụng |
|---|---|---|---|---|---|
| OSM snapshot khóa (`relation/17627914` v9, `boundary=historic`) | 9 way, đường ranh | **Không khép**: 1 chuỗi 31,08 km, hai đầu cách 1.885 m | — | Không dựng được vùng → không dùng | Bằng chứng một phần; **không tự nối** |
| Lịch sử chỉnh sửa OSM (API, v1 2024-05-23 → v9 2025-11-25) | 2–10 thành viên | **Chưa phiên bản nào khép kín** (v1–v7: 5 way; v8–v9: 9 way) | — | — | Không có phiên bản đầy đủ để khôi phục |
| GADM 4.1 cấp 3 (`VNM.27.9.5_1` "Thị trấn Đông Anh", SHA-256 tệp `fe29b396…`) | Polygon | **Đầy đủ**, 4,544 km², 54 đỉnh (giản lược) | Từ 1.240 điểm mẫu (25 m) trên đường OSM tới biên GADM: trung vị 23,7 m, p95 184,2 m, tối đa 434,9 m; 0,355 km biên GADM cách OSM > 100 m | Chứa node thị trấn → **nếu** dùng làm nội đô, chuyến này thành URBAN (2a) thay vì INTERCITY 19,678 km | **Không có thẩm quyền** (bộ dữ liệu tổng hợp), giản lược, giấy phép hạn chế phân phối lại (không đưa hình học vào repo). Phân bố trên đơn vị hiện hành: Thư Lâm 2,37 · Phúc Thịnh 1,566 · Đông Anh 0,609 km² — **khớp** NQ1656 k113–k115. Chỉ dùng được nếu Chủ dự án chấp nhận |
| OCHA HDX COD-AB Việt Nam (nguồn GSO, hiệu lực 2025-09-25) | Polygon cấp 0–1 | Chỉ 34 tỉnh sau cải cách | — | — | Không có cấp xã/thị trấn cũ |

**Kết luận:** không có nguồn **có thẩm quyền** cho ranh giới thị trấn cũ → giữ `PENDING_GEOMETRY_EVIDENCE`; không nối đoạn hở, không thay bằng 3 xã hay Global Gate; kết quả phân loại **không** bị chỉnh: Đông Anh → Hoàn Kiếm vẫn **INTERCITY (19,678 km) — FAIL so với Mục 2.3**, là blocker.

## 2. GEO-B — Sơn Tây, Chương Mỹ

Ngoài URBAN trong MVP theo quyết định Chủ dự án (`excluded_review` ghi `OWNER_DECISION_GEO-B (MVP)`); cả hai trong TOTAL. Đánh giá: Sơn Tây (node city) URBAN = False, TOTAL = True — AS_EXPECTED.

## 3. GEO-C — Bộ lọc 150 km

- **Lớp 1 mới — cận dưới trắc địa:** đơn vị vào TOTAL khi điểm **gần nhất** cách anchor ≤ 150 km theo đường thẳng (ellipsoid). Quãng đường bộ không bao giờ ngắn hơn đường thẳng, nên polygon **không thể** từ chối một điểm mà kiểm tra đường bộ sẽ nhận.
- Hàm Rồng, Vĩnh Lộc, Bao La, Yên Bình (bị sót ở v3) nay trong TOTAL (điểm gần nhất 127,7 / 104,2 / 95,2 / 113,2 km đường thẳng).
- **Lớp 2 bắt buộc:** phiên bản thiếu `serviceability` → 503; một request `/table` đọc đúng phần tử `[0][0]` anchor→pickup, `[0][1]` anchor→dropoff, `[1][1]` pickup→dropoff (test so khớp `/route` trực tiếp anchor→dropoff, khác tổng anchor→pickup→dropoff); không fallback đường chim bay; nhận `≤ 150 km`.
- **Hệ quả cần lưu ý:** TOTAL thô của v4 là **vùng bao ứng viên** (68.374,5 km²), **không** phải lời hứa phục vụ — 1.140 đơn vị, nhiều đơn vị chỉ một phần ≤ 150 km đường bộ. Mẫu 400 điểm đều theo diện tích: phục vụ 160, ngoài 150 km 68, xa đường 172. Trip API chỉ trả "phục vụ" sau lớp 2; không công bố polygon này như vùng phục vụ.

## 4. GEO-D — Ngưỡng snap 300 m (điểm đón thực tế)

Điểm OSM có ý nghĩa đón khách (bến xe buýt, trường, chợ, bệnh viện, ngân hàng, bưu điện, cây xăng, UBND, điểm dân cư) trong vùng chấp nhận: 14.027; mẫu ≤ 300/tỉnh (seed 1) = 3.296.

| | Phục vụ | Xa đường > 300 m | > 150 km đường bộ |
|---|---|---|---|
| Tổng | 2.443 | **42 (1,3%)** | 811 |
| Hà Nội / Ninh Bình | 300 / 300 | 0 / 0 | 0 / 0 |
| Hưng Yên / Hải Phòng / Bắc Ninh | 299 / 299 / 297 | 1 / 1 / 3 | 0 |
| Phú Thọ / Thái Nguyên | 289 / 251 | 5 / 1 | 6 / 48 |
| Thanh Hóa / Tuyên Quang / Lào Cai | 89 / 61 / 2 | 13 (4,3%) / 6 (4,0%) / 3 (3,7%) | 198 / 84 / 77 |
| Bến xe buýt (708) | 677 | **0** | 31 |

Khoảng cách snap: p50 16,1 m, p90 52,4 m, p95 85,7 m, p99 397,4 m. Từ chối do xa đường tập trung ở thôn/xóm miền núi. Ngưỡng 300 m giữ nguyên (không tăng để cải thiện tỷ lệ); đánh giá lại trước P2.

## 5. GEO-E — Chính sách phà

- Graph CH hiện có hỗ trợ `exclude=ferry` (profile car v5.27.1 khai báo `excludable` ferry) → **không build lại OSRM**.
- Hà Nội → Cát Bà: mặc định 150,577 km gồm **1 chặng phà 2,015 km**; với `exclude=ferry`: `NoRoute` (route và table) — test tự động trên OSRM thật.
- Kiểm tra trên v4: 412 đích (11 thành phần tách rời được giữ, thị trấn Cát Bà, 400 điểm mẫu): 3 tuyến dùng phà khi mặc định, **0 chặng phà** khi áp chính sách.
- 7 thành phần chỉ tới được bằng phà chuyển sang EXCLUDED (`NOT_ROUTABLE_FROM_ANCHOR`): Đặc khu Cát Hải (Cát Bà 167,06 km² và 0,36 km²), Đặc khu Vân Đồn (72,04; 16,71; 11,82 km²), Phường Đồ Sơn 0,12 km², Phường Bãi Cháy 0,08 km². Các đảo có đường bộ nối liền (cầu) vẫn được giữ.

## 6. Sai khác v3 → v4

| | v3 `7da7fbe2e01b` | v4 `9bd44393e699` |
|---|---|---|
| URBAN | 340,034 km², 6 phần | 340,034 km², 6 phần (**không đổi**; 0 điểm đổi trạng thái) |
| TOTAL thô (vùng bao lớp 1) | 42.275,390 km², 335 phần, 913 đơn vị | 68.374,523 km², 1.782 phần, 1.140 đơn vị (+227: Thanh Hóa 90, Lạng Sơn 30, Sơn La 23, Tuyên Quang 22, Thái Nguyên 22, Lào Cai 22, Quảng Ninh 15, Phú Thọ 2, Nghệ An 1) |
| EXCLUDED | 29,158 km², 324 phần | 488,167 km², 1.770 phần (1.720 đảo không đường — chủ yếu vịnh Hạ Long nay trong vùng bao; 43 mảnh nghi chồng lớp; 7 chỉ tới được bằng phà) |
| Vùng chấp nhận lớp 1 | 42.246,232 km² | 67.886,357 km² |
| Lớp 2 | snap 300 m, ≤ 150 km | + `exclude: [ferry]` |

Kết quả phân loại (cùng ca): mọi ca biên R9 giữ nguyên kết quả (Phenikaa → La Phù URBAN 2b; 3 km Hưng Yên UNSUPPORTED; đệm 14,992 / 15,321 km; 149,984 km INTERCITY / 150,024 km OUT_OF_SERVICE_AREA bởi lớp 2); Đông Anh → Hoàn Kiếm vẫn FAIL; điểm đúng biên polygon qua lớp 1 (bị lớp 2 quyết định).

## 7. Tái lập và bằng chứng

- Import lại v4 vào thư mục tạm: cùng id, URBAN / TOTAL / EXCLUDED `unchanged (ST_Equals)`, SHA-256 trùng: urban `fc11eb3e…f268`, total `bf7047cb…4a43`, excluded `295585b5…1bc5`.
- `boundary_eval` nay từ chối ghi đè **mọi** tệp đánh giá đã có (trước chỉ chặn bundle v1).
- REVIEW.md của v4 do pipeline sinh còn câu "implementation parameter, pending owner confirmation" cho ngưỡng snap — câu này có trước quyết định GEO-D; mã sinh đã sửa cho các lần build sau, bundle v4 không ghi đè.

## 8. Sự cố vận hành trong phiên

- Dừng container build (`docker stop`) **không** dừng truy vấn PostgreSQL của nó: truy vấn mồ côi giữ khóa schema `sa_build` và chặn lần build sau (đã `pg_terminate_backend`; giao dịch chưa commit nên không ghi gì). Quy tắc: sau khi dừng build phải kết thúc backend tương ứng.
- Truy vấn phân loại thành phần chậm khi vùng bao chứa hàng nghìn đảo → chỉ tính khoảng cách cho mảnh cỡ "sliver" + chỉ mục GIST (kết quả phân loại không đổi vì ngưỡng sliver là < 10 m).
- Khảo sát điểm đón ban đầu đếm trùng do snapshot còn quan hệ tỉnh cũ (Hòa Bình VN-14, Yên Bái VN-06, "… cũ") chồng lên tỉnh mới → mỗi điểm nay gán đúng 1 tỉnh (quan hệ lớn nhất, loại "cũ"); tệp sai đã xóa trước khi tạo lại.
