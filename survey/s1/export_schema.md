# Survey S1 — export schema (draft)

Target consumers: MNL / mixed-logit estimation and 5-fold GroupKFold CV by `respondent_id`
(Phase 7–8, Revision 9 Section 65.3), Wilcoxon / Friedman tests for H4.
Format: one CSV per table (UTF-8, header row); Parquet export is added in Phase 7 when the
data stack (Polars/Pandas) is introduced. Status: DRAFT 5 (questionnaire `draft_version` 5, design D2 active for the local TEST survey), not released.

## `respondents.csv` — one row per completed response
| Column | Type | Notes |
|---|---|---|
| respondent_id | UUID | random v4, server-generated; no link to any identity |
| questionnaire_version | text | e.g. `s1-draft-5` |
| design_block | int | rotation block assigned at start (Part 1A design) |
| group | enum | `STUDENT` \| `WORKER` |
| ride_hailing_trips_per_week | enum / empty | `0`, `1`, `2-3`, `4-6`, `7+` (optional, SURVEY-04) |
| usual_trip_distance | enum / empty | `LT3`, `3-LT6`, `6-LT10`, `10-LT20`, `20+` (optional) |
| intercity_trips_per_month | enum / empty | `0`, `1`, `2-3`, `4+` (optional) |
| started_at_utc / completed_at_utc | timestamp | truncated to the minute |
| duration_s | int | submit − start in whole seconds, from an HMAC-signed start token |
| quality_flags | text | `|`-joined flags: `FAST_RESPONSE_REVIEW`, `QC3_SAME_POSITION_ALL_1A`, `QC4_SAME_LIKERT_ALL_METHODS` (flags only, never exclusions) |

## `choices.csv` — long format, one row per alternative per task (Parts 1A and 1B)
| Column | Type | Notes |
|---|---|---|
| respondent_id | UUID | grouping key for GroupKFold |
| part | enum | `1A` \| `1B` |
| task_index | int | order shown to the respondent (1-based) |
| task_id | text | design id, e.g. `1A-d14-rain-urgent` |
| distance_km / weather / urgency | context | Part 1A only |
| alternative | enum | `BIKE_URBAN`, `CAR_URBAN_POOL`, `CAR_URBAN_PRIVATE`, `CAR_INTERCITY_POOL`, `CAR_INTERCITY_PRIVATE`, `OTHER` |
| position | int | on-screen position (1-3) for position-bias checks |
| price_vnd | int | shown price (pool: expected price) |
| quote_cap_vnd | int / null | pool only: committed cap if matched (`Quote_i`, R9 18.3) |
| max_price_if_unmatched_vnd | int / null | pool only (`Unmatched_i`) |
| travel_min / max_detour_min | int / null | |
| match_likelihood / fill_likelihood | enum / null | `HIGH` \| `MEDIUM` \| `LOW` — hypothetical survey levels, not forecasts |
| walk_m | int / null | pool only |
| chosen | 0/1 | exactly one 1 per (respondent_id, task_id) |

## `fairness_h4.csv` — Part 2, one row per method per respondent
| Column | Type | Notes |
|---|---|---|
| respondent_id | UUID | |
| method | enum | `A_PROPORTIONAL` \| `B_SHAPLEY` \| `C_INCONVENIENCE_WEIGHTED` (true identity) |
| display_label | enum | `X` \| `Y` \| `Z` (what the respondent saw) |
| display_position | int | 1–3 |
| likert_fairness | int | 1–5 |
| preferred | 0/1 | exactly one 1 per respondent |

No column may contain names, e-mail, phone, student id, IP address, precise location or free text.

## Monitoring (ADMIN, not export tables) — rules R1 / R3
- `GET /api/admin/survey/s1/quota?dataset=` — completed per group (quota), plus `started`, `started_by_group`
  and `completion_rate_by_group` (R1: drop-out is reported, sessions without a submission are still never exported).
- `GET /api/admin/survey/s1/rejections?days=` — 422 counts per UTC day and error code (R3), aggregate only:
  no address, no request content; Redis keys expire after 90 days.
