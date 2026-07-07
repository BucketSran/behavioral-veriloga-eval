# vaBench v3 Layered Certification

Date: 2026-07-07

## Headline

- Total tasks: **505**
- Original behavior-certified full-300 surface: **300**
- Extension candidates: **205**
- Behavior-certified extension rows: **205**
- Compile-supported candidate rows: **0**
- Unsupported candidate rows: **0**
- Spectre-divergent retained rows: **6**

## Semantic Layers

| Layer | Tasks | Certification levels |
| --- | ---: | --- |
| `behavioral_continuous_time_extension` | 14 | behavior_certified_extension: 14 |
| `behavioral_event_core` | 275 | behavior_certified: 275 |
| `behavioral_event_support` | 25 | behavior_certified_support: 25 |
| `behavioral_language_extension` | 170 | behavior_certified_extension: 164, behavior_certified_extension_spectre_divergent: 6 |
| `cadence_simulator_function_extension` | 3 | behavior_certified_extension: 3 |
| `conservative_kcl_syntax_extension` | 6 | behavior_certified_extension: 6 |
| `noise_analysis_extension` | 12 | behavior_certified_extension: 12 |

## Blocking Issues

| EVAS issue | Blocked tasks | Semantic layers | Promotion acceptance |
| --- | ---: | --- | --- |

## Spectre-Divergent Rows

| Task | Reason |
| --- | --- |
| `391-rdist-exponential-jitter` | seeded random exponential sequence differs from Spectre |
| `392-rdist-poisson-count-noise` | seeded random poisson sequence differs from Spectre |
| `393-rdist-normal-offset-dither` | seeded random normal sequence differs from Spectre |
| `396-rdist-erlang-latency` | seeded random erlang sequence differs from Spectre |
| `404-vector-part-select-window` | integer vector part-select behavior differs from Spectre |
| `405-vector-concat-code-build` | integer vector concatenation behavior differs from Spectre |

## Completion Audit

- Status: `partial_external_blocked`
- Complete: `false`
- Reason: The full 301-505 objective is not complete because 0 extension tasks still lack behavior checker evidence and are excluded until EVAS support issues are resolved.

| Requirement | Status | Evidence | Gap |
| --- | --- | --- | --- |
| Scope covers all v3 extension tasks 301-505. | `satisfied` | layered_certification summary reports extension_candidate_count=205. |  |
| Each extension task has a clear prompt and required behavior section. | `satisfied` | extension_sop_audit has no missing_required_behavior_section issue. |  |
| Each extension task has executable visible and hidden test evidence. | `satisfied` | extension_sop_audit complete_tests_count=205. |  |
| Each extension task has five useful negative variants. | `satisfied` | extension_sop_audit reports no negative_count_lt5 issues. |  |
| Each extension task has repository behavior checker evidence and can be scored fairly. | `satisfied` | 205 extension tasks are behavior-certified; 0 remain excluded_until_behavior_promotion. |  |
| Behavior-certified extension tasks pass gold verification and reject all negative variants. | `satisfied` | verify_301_505_layered: gold_pass=205, gold_fail=0, negative_rejected=1025, negative_accepted=0, expectation_fail=0. |  |
| Every staged task has a concrete EVAS issue and promotion checklist. | `satisfied` | No staged tasks remain; no EVAS promotion blockers are required. |  |
| No retained default row is marked spectre-divergent for a full Spectre-certified claim. | `not_satisfied` | 6 retained row(s) require Spectre recalibration. | Recalibrate the affected gold/checker contracts against Spectre before enabling a full Spectre-certified or formal score-denominator claim. |

## Claim Boundary

- Only tasks 001-300 are part of the original behavior-certified full-300 claim.
- Tasks 301-505 are behavior-certified extension rows outside the original full-300 denominator.
- Rows marked spectre-divergent are excluded from full Spectre-certified and score-denominator claims until recalibrated.
- Continuous-time rows certify the repository's finite-difference/stateful behavioral response, not a general analog solver accuracy claim.
- KCL/current rows certify observable branch-current contribution behavior, not unknown-node MNA/KCL solving.
- AMS, noise/analysis, Cadence-helper, Cadence-derived data-converter, and table-model extension rows are certified only for their layer-specific transient/checker contracts.

## Evidence Sources

| Evidence | Path / note |
| --- | --- |
| `task_manifest` | `benchmark-vabench-release-v3/TASKS.json` |
| `checker_manifest` | `benchmark-vabench-release-v3/CHECKS.yaml` |
| `extension_sop_audit` | `benchmark-vabench-release-v3/reports/extension_sop_audit.json` |
| `behavior_certified_extension_task_evidence` | `benchmark-vabench-release-v3/reports/behavior_certified_extension_task_evidence.json` |
| `language_extension_notes` | `benchmark-vabench-release-v3/LANGUAGE_EXTENSION.md` |
| `core_behavior_evidence` | `benchmark-vabench-release-v1/reports/benchmark_overview.json` |
| `staged_gold_probe` | `benchmark-vabench-release-v3/reports/staged_promotion_gold_probe.json` |
| `staged_gold_probe_summary` | `benchmark-vabench-release-v3/reports/staged_promotion_gold_probe.md` |
| `staged_blocker_matrix` | `benchmark-vabench-release-v3/reports/staged_blocker_matrix.json` |
| `staged_blocker_matrix_summary` | `benchmark-vabench-release-v3/reports/staged_blocker_matrix.md` |
| `latest_compile_probe` | `local EVAS compile/verification probes cover the current staging rows and their five negative variants per task.` |
