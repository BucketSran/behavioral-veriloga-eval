# V4 Upstream Integration And Tri-Form Handoff

Status: preparation only; no branch, commit, push, or PR is created by this file.

## 1. Ownership Boundary

- The DUT closeout task owns the 400 canonical DUT families and the exact-five
  scored mutation projection.
- `operations/tri_form_derivation_prep/` owns Testbench and Bugfix derivation
  preparation only.
- The EVAS repository owns simulator semantics, ABI, runtime identity, and
  parity regressions. Benchmark task IDs must never appear in EVAS fixes.
- Raw simulator output, agent scratch, and `/tmp` evidence are not release
  source. Only compact hash-bound evidence indexes may enter an upstream PR.

## 2. Exact-Five Release Contract

The immutable source catalog contains 2,051 certified mutations. The scored
tri-form projection activates exactly five mutations per family:

- 400 families;
- 2,000 active mutations;
- 51 provenance-only catalog extras;
- one Bugfix seed selected from the same five active mutations;
- all five active mutations assigned to the Testbench mutation suite.

The 51 extras are not deleted. They remain available for provenance and future
robustness studies but are outside the formal score denominator.

## 3. Behavioral Repository PR Chain

Do not add later work to the existing pilot PR branch. PRs after the pilot use
new branches rooted from the latest accepted upstream state.

| Order | Scope | Review shape |
|---:|---|---|
| B0 | Existing 10-family pilot PR | Keep its current narrow purpose. |
| B1 | Evidence schemas, component fingerprints, strict audits | No task bulk and no simulator output. |
| B2 | Spectre runner, trace replay, evidence carry-forward | Runner tests and fixtures only. |
| B3 | Checker registry/modules, form adapters, release builders | No 400-family asset dump. |
| B4-B11 | Canonical families 001-400 in eight 50-family PRs | Five commits per PR, ten canonical families per commit. |
| B12 | Exact-five denominator, compact certification indexes, final release audit | Depends on all family PRs; no duplicate historical release trees. |
| B13 | Tri-form generator and pilot-derived Testbench/Bugfix packages | Starts only after the exact-five projection is frozen. |

Each family PR must contain a machine-readable changed-family manifest and run
the same integrity/audit command. Canonical family IDs, not source directory
prefixes, determine the batch membership.

Later branches are prepared and verified locally while an earlier dependency
is under review. To keep the upstream review diff narrow, a dependent PR is
opened against `main` only after its prerequisite merges. A draft PR with a
cumulative prerequisite diff is avoided unless the maintainer explicitly asks
for a stacked review.

## 4. EVAS Repository PR Chain

Do not push Rust work into the existing Python-compatibility PR branch.

| Order | Scope | Required evidence |
|---:|---|---|
| E0 | Existing Python compatibility PR | Existing focused tests. |
| E1 | Reproducible runtime identity, netlist boundary, hierarchy semantics | Parser/netlist/backend regression tests; no benchmark-ID special cases. |
| E2 | Rust `cross`/`transition` event scheduling and trace semantics | Atomic Rust/Python boundary regressions and Spectre parity cases. |

The final benchmark release lock records the merged EVAS commit, Rust core ABI,
executable hash, selected engine, and runtime package identity. EVAS PRs do not
depend on benchmark asset PRs; the benchmark release PR depends on the final
merged EVAS identity.

## 5. Reuse And Rerun Policy

- Preserve existing gold and mutation evidence when all consumed component
  hashes remain identical.
- A path adapter or private support-resource declaration is not, by itself, an
  analog rerun trigger.
- Existing score-profile evidence directly covers 1,186 of the 2,000 active
  mutations.
- The remaining 814 cross-profile cells first receive a semantic witness
  portability audit. Only unresolved cells receive targeted Spectre runs.
- A final frozen-toolchain replay is a release-sealing choice, not evidence
  that all historical results were invalid.

## 6. Tri-Form Preparation While DUT PRs Are Reviewed

Work that may proceed without changing canonical DUT assets:

1. freeze Testbench and Bugfix task-record schemas;
2. implement generators that consume only `family_spec.json`, the exact-five
   suite index, and stable artifact/checker references;
3. render into a staging directory, never directly into scored release paths;
4. implement public/evaluator bundle isolation audits;
5. implement G0-G5 records for all three forms;
6. implement Testbench scoring against the supplied gold DUT and all five
   active mutations;
7. implement Bugfix packaging for one representative active mutation;
8. record token, wall time, tool calls, candidate versions, simulator calls,
   and the final frozen candidate hash for every experiment cell.

Materialized scored Testbench/Bugfix tasks remain blocked until the DUT
exact-five release manifest is frozen and hash-bound.

The existing `formal_derivatives/` front-20 packages are early prototypes with
an obsolete family-to-form numbering map. They may inform templates, but they
must not be submitted or promoted. The formal 800 derivatives are regenerated
from the frozen 400-family numbering plan and exact-five manifest.

## 7. PR Acceptance Checklist

Every PR must state:

- its upstream base and prerequisite PR;
- canonical family IDs or EVAS semantic classes in scope;
- generated versus author-owned files;
- exact tests and audits run;
- reused evidence count and newly executed evidence count;
- known deferred work;
- confirmation that raw simulator artifacts and unrelated workspace files are
  absent from the diff.
