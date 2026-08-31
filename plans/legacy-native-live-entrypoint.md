# Legacy/native comparison: explicit live entrypoint

Date: 2026-08-31. Intake: `f1c78b3dd7b9b0913a626661158c816c55091667`.

## Brief and scope

The user accepted the next comparison step. Implement the missing live transport
and an inspectable frozen provider/fee profile, using AA-VAE-071's existing
coordinator, guard, credential loader, receipts and result reader. This turn
performs free engineering only: no real keys, provider metadata requests, paid
generation, historical budget reuse, benchmark/evaluator edit, or new dependency.
The agreed scope answers the workflow intake; no further permission handoff is
needed for local tests, review and fork-only focused commits.

Keep legacy defaults, the free v1 fixture API and AA-VAE-069 blueprint unchanged.
An explicit new live preparation is not spending authorization. Execution must
require an operator assertion of the exact manifest hash and its exact fee cap;
this is an accidental-launch guard, not host-authenticated human identity.
No automatic default paid launch or resume is added.

## Acceptance / KPI

1. Freeze a named service/model, endpoint, decoding, date-reviewed rates,
   currency/cap and model-alias limitation before generation. Reject stale or
   changed profiles rather than silently changing rates or service.
2. Both workflows share the same existing budgeted HTTP client; every actual
   transport attempt is reserved. Unknown usage retains its reservation and
   stops subsequent calls. Preserve all six dispositions and no reentry.
3. Validate manifest/source/runtime/approval before reading credentials; reuse
   the owner-only literal loader and remove known provider environment keys.
   Never publish raw credentials, balance, requests, traces or judge assets.
4. Free fixture and live preparation are distinct. Read-only output binds the
   execution authorization receipt and counts transport attempts; live evidence
   must never be labeled zero-paid fixture evidence by default.
5. Free tests exercise the real curl boundary with synthetic responses, plus
   real Docker/EVAS six-cell integration, corruption/reentry/admission failure,
   static checks and independent review. Do not claim live model quality or
   an account-wide/invoice guarantee.

## Controlled plan and ownership

Main owns calibration-pilot `comparison_live.py`,
`run_legacy_native_comparison.py`, `tests/test_agent_harness_comparison_live.py`,
minimal related regression/CI updates, plans/logs/README/ledger/feature note and
all Git publication. No delegated writer. A read-only researcher verifies the
already chosen DeepSeek service contract; a separate reviewer audits final code.

Use vertical RED/GREEN slices: frozen profile and gate; budgeted transport and
coordinator reuse; CLI/receipt/report binding; real free integration; independent
review; focused GREEN commits and exact-source hosted CI. Stop the affected
branch if the current service needs a guard redesign, scoring changes or new
spending authority. Preserve all stopped evidence; never retry by resetting a
budget or deleting receipts.

## Evidence and residual gates

Record RED/GREEN commands, changed files, code map, public primary sources and
exact hosted source in verification-log and AA-VAE-072. Raw fixtures belong in
ignored reports. Before any future paid run, explicitly agree a new currency/
cap, inspect the frozen profile and approve its manifest hash. Tests establish
transport/evidence connectivity, not backend performance, controller causality,
Spectre equivalence or independent hidden-stimulus coverage.
