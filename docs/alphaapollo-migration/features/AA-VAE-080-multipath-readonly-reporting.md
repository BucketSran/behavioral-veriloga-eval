# AA-VAE-080 — Multi-path read-only reporting

Status: implemented; report interoperability, not execution delegation.

## Idea and reuse

Use one viewer without redefining experimental conditions. Evolution remains
a multi-branch selected-candidate estimand, not a single-trajectory result.
Reuse vaEVAS verified readers and the existing pinned Inspect 0.3.261 log API;
no new inference, scheduler, scorer or third-party dependency is introduced.

## Code and interface

- `operations/calibration_pilot/reporting_sources.py` under the v4 package:
  structural allowlists over `read_comparison`, `validate_terminal_result` and
  `read_combined`; separate groups, zero/null eligibility, costs and source hashes.
- Adjacent `result_adapter.py`: additive `--source-kind`, existing native-campaign
  API remains the default. All outputs are fresh and outside input evidence.
- `tests/test_agent_harness_reporting_sources.py`: read-only export, corruption,
  unstarted/zero cases, real combined native/Evolution and official SDK readback.

Supported source roots:

| source kind | root | denominator |
| --- | --- | --- |
| `native-campaign` | native batch run, plus `--campaign` | existing native ledger |
| `legacy-native-comparison` | sealed comparison directory | all six planned rows, separate backends |
| `evolution-single` | one terminal attempt with `campaign.json` and `run/` | one cell, source branch costs/denominator |
| `combined-tools` | terminal combined directory | one named backend/feature condition |

Non-native imports omit `--campaign` and use one reader. Partial combined
execution fails closed. Unstarted comparison rows stay unscored, not zero.
Source runtime hashes remain authoritative; only the known relative
`public/public -> .` alias is permitted by the additional symlink precheck.

## Information and claim boundaries

No prompts, tool diagnostics, hidden feedback, transcripts or raw evidence
objects are copied. Records retain structural counts, candidate IDs and branch
evidence hashes. Missing legacy costs remain unknown. Combined counters use
the reader's actual `attempted`, `succeeded`, and feedback-exposure fields;
incomplete diagnostics are represented by a count, not copied text.

`evolution-single` is NOT a whole batch/retry aggregate: selecting one attempt
cannot establish all-attempt spend or a batch success rate. Candidate lineage
is selected identity plus branch hash references, not an expanded graph.
Legacy paired-delta visualization is not yet exported. All-branch costs are
preserved when present in the source; absent historical summaries stay null.
Inspect reports the imported final score without rerunning the judge. No
pooled headline or model-quality/performance improvement claim is produced.
