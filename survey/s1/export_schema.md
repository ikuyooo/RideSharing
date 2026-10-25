# Survey S1 — export schema (draft)

Target consumers: MNL / mixed-logit estimation and 5-fold GroupKFold CV by `respondent_id`
(Phase 7–8, Revision 9 Section 65.3), Wilcoxon / Friedman tests for H4.
Format: one CSV per table (UTF-8, header row); Parquet export is added in Phase 7 when the
data stack (Polars/Pandas) is introduced. Status: DRAFT, pending owner approval.

## `respondents.csv` — one row per completed response
| Column | Type | Notes |
|---|---|---|
| respondent_id | UUID | random v4, server-generated; no link to any identity |
| questionnaire_version | text | e.g. `s1-draft-1` |
| design_block | int | rotation block assigned at start (Part 1A design) |
| group | enum | `STUDENT` \| `WORKER` |
| ride_hailing_trips_per_week | enum | bins TBD |
| usual_trip_distance | enum | bins TBD |
| intercity_trips_per_month | enum | bins TBD |
| started_at_utc / completed_at_utc | timestamp | for completion-time quality checks; truncated to the minute |
| quality_flags | text[] | outcomes of the QC rules (empty = passed) |

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
| max_price_if_unmatched_vnd | int / null | pool only |
| travel_min / max_detour_min | int / null | |
| match_likelihood / fill_likelihood | enum / null | `HIGH` \| `MEDIUM` \| `LOW` |
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
