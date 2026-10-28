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

## 9. Cập nhật 2026-10-28 (sau báo cáo hardening) — xử lý blocker Đông Anh: ứng viên v5 `sa-cand-0d5347b4294e`

**Phát hiện:** quan hệ OSM `relation/17627914` **không thực sự hở**. Điểm đầu của way 1412300270 nằm đúng trên way 1412300271 (khoảng cách 0,0 m — nút chữ T), và way 1412300271 cắt way 1286471120. Khoảng "hở 1.885 m" chỉ là do way 1412300271 **chạy quá** nút giao 2,25 km (một đường ranh xã khác được đưa nguyên vào quan hệ), khiến osmium không ghép được vòng. Ghép bằng `ST_Polygonize(ST_Node(member ways))` — chỉ dùng các đường đã có trong OSM, **không thêm, không nối, không dịch chuyển đường nào** — cho 2 mặt kề nhau.

| Cách đọc | km² | IoU với GADM | Hausdorff tới GADM | Chứa node thị trấn | Phân bố Thư Lâm / Phúc Thịnh / Đông Anh (km²) |
|---|---|---|---|---|---|
| **Hợp 2 mặt** | **4,344** | **0,855** | **222 m** | **có** | **2,303 / 1,487 / 0,554** — cả 3 xã như NQ1656 k113–k115; GADM: 2,37 / 1,566 / 0,609 |
| Chỉ mặt 1 | 3,042 | 0,597 | 1.787 m | không | gần như thiếu Phúc Thịnh |
| Chỉ mặt 2 | 1,303 | 0,275 | 4.097 m | có | chỉ Phúc Thịnh |

Chỉ cách đọc "hợp 2 mặt" nhất quán với cả GADM (độc lập) và văn bản chính thức NQ1656 (thị trấn chia cho 3 xã). Phần không dùng: 2.251 m đuôi thừa của way 1412300271.

**Ứng viên v5** (`service_area_rules.candidate.v5.yaml` = v4 + quy tắc U4 `include_historic_areas`): nội đô thêm polygon thị trấn Đông Anh cũ 4,347 km² — **không** lấy nguyên 3 xã, **không** dùng Global Gate.

| | v4 `9bd44393e699` | **v5 `0d5347b4294e`** |
|---|---|---|
| URBAN | 340,034 km², 6 phần | **344,381 km², 7 phần** (+4,347) |
| TOTAL / EXCLUDED | 68.374,523 / 488,167 km² | không đổi |
| Node `place=*` đổi trạng thái | — | 1: node/13799910539 Đông Anh vào URBAN |
| Đông Anh → Hoàn Kiếm | INTERCITY 19,678 km — FAIL | **URBAN (2a) — PASS** |
| Ca biên R9 + ca GEO (15 ca) | 14 PASS, 1 FAIL | **15/15 PASS** (nghiệm thu: NOT_VERIFIED vì chưa phê duyệt) |

SHA-256 v5: urban `33ca5346…0307`, total `c3de995a…6353`, excluded `dcb26c8f…82cf` (TOTAL/EXCLUDED cùng hình học với v4; hash khác vì thuộc tính `service_area_version` trong GeoJSON).

**Trạng thái:** bằng chứng hình học đã có (OSM + đối chiếu GADM + NQ1656), nhưng **không nguồn nào là bản đồ ranh giới có thẩm quyền** → đây là `PENDING_OWNER_APPROVAL`, không phải GEOMETRY_APPROVED. Chủ dự án chọn: phê duyệt v5 (Đông Anh nội đô theo thị trấn cũ) hoặc giữ v4 (Đông Anh chưa nội đô).

## 10. Phê duyệt có điều kiện v5 — kết quả 8 cổng kiểm (OWNER APPROVAL §2, 2026-10-28)

Thực hiện bằng `app.modules.trip.service_area_approve` — chỉ ghi trạng thái khi **mọi** cổng PASS; bằng chứng: `sa-cand-0d5347b4294e/APPROVAL_GATES.json` (đánh giá mới `APPROVAL_GATE_EVAL.md` / `approval_gate_eval.json`, không ghi đè bằng chứng cũ).

| Cổng | Nội dung | Kết quả |
|---|---|---|
| G1 | 3 lớp có trong DB, đang CANDIDATE; 13 tệp trong `CHECKSUMS.sha256` băm lại khớp; hình học lưu trong DB (`ST_AsGeoJSON` 6 chữ số) = GeoJSON của bundle. SHA-256 đầy đủ: urban `33ca5346a75e065a5af883ac6e2097b6deaae3bb81b8fe8d7b5bcf77fdb80307`, total `c3de995abbcd80a6ab6935887e802462d0503a2f5f4c417bd2e5ebf446946353`, excluded `dcb26c8f860047c8ed77b11b20b3523f86892610d0c5b0b1b00f6471952782cf` | PASS |
| G2 | Bằng chứng ứng viên: U4 `relation/17627914` ghép bằng polygonize; hợp 2 mặt IoU 0,855 với GADM, chứa node thị trấn, chia 3 xã | PASS |
| G3 | Đánh giá chạy lại (15 ca) — tất cả PASS | PASS |
| G4 | Đông Anh → Hoàn Kiếm = URBAN (2a) | PASS |
| G5 | Phenikaa → La Phù = URBAN qua vùng đệm (2b), 5,977 km | PASS |
| G6 | Điểm ngoài 150 km bị từ chối (lớp 2): 150,024 km và 256,43 km → `BEYOND_MAX_ROAD_DISTANCE` | PASS |
| G7 | Snap 1.576,6 m → `NO_ROAD_ACCESS`; điểm trong EXCLUDED → `UNSERVICEABLE_COMPONENT`; phà: 412 đích, 0 chặng phà khi áp chính sách, Cát Bà `NoRoute` | PASS |
| G8 | Import lại vào thư mục tạm: 3 lớp `unchanged (ST_Equals)`, SHA-256 trùng; bundle đã có bị từ chối ghi đè | PASS |

**Kết quả:** `sa-cand-0d5347b4294e` — 3 lớp `status = APPROVED`, `approved_at` có giá trị, `approval_reference = "GEOMETRY_APPROVED_FOR_MVP | Owner conditional approval 2026-10-28 … academic MVP scope only - NOT a legal certification of administrative boundaries; Dong Anh former-town boundary reconstructed from OSM relation 17627914 (member ways polygonized, no line added), compared with GADM 4.1 and HDX COD-AB; no state boundary certification"`. v1–v4 giữ nguyên (CANDIDATE / RETIRED). Cấu hình chạy cục bộ: `SERVICE_AREA_VERSION = sa-cand-0d5347b4294e`, `ALLOW_CANDIDATE_SERVICE_AREA = false`.

**Phạm vi:** phê duyệt cho MVP học thuật — **không** phải chứng nhận độ chính xác pháp lý của địa giới.

**Rủi ro còn lại về địa giới Đông Anh**
1. Ranh giới thị trấn cũ là **tái dựng từ dữ liệu cộng đồng** (OSM), được hai nguồn không có thẩm quyền (GADM) và một văn bản (NQ1656, chỉ mô tả bằng lời) xác nhận — chưa có bản đồ địa giới của cơ quan nhà nước.
2. Đoạn ranh giữa 2 mặt và đuôi thừa 2,25 km thuộc way 1412300271: cách đọc "hợp 2 mặt" là suy luận (được GADM ủng hộ, IoU 0,855); sai lệch biên tới GADM tới 222 m (Hausdorff) → điểm đón trong dải vài trăm mét quanh ranh có thể bị phân loại khác thực tế.
3. Diện tích 4,344 km² so với GADM 4,544 km² (−4,4%) — phần GADM nằm ngoài vùng OSM (≈10%) không thuộc nội đô.
4. "Đông Anh" của Mục 2.3 được hiểu là thị trấn cũ (không phải cả huyện) — các xã khác của huyện Đông Anh cũ (Cổ Loa, Uy Nỗ, Vĩnh Ngọc, Global Gate…) vẫn ngoài nội đô; chuyến từ đó vào trung tâm > 15 km là INTERCITY.
5. Dữ liệu OSM có thể đổi: phiên bản khóa theo snapshot 2026-10-23; cập nhật bản đồ sau này cần build + kiểm cổng lại.
