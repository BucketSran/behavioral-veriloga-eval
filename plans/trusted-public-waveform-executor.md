# Trusted public waveform execution

Updated: 2026-08-31. Base: `2f2c159fc4`. Feature: AA-VAE-060.

## Brief / frozen scope

Implement the execution prerequisite of AA-VAE-058, not a model tool yet.
An explicit coordinator API accepts an Agentic context, public runtime, declared
candidate artifacts, r53 manifest, campaign identity and immutable Docker image
ID. Each call snapshots bounded public inputs and runs the fixed public EVAS
command in a new container. Reuse existing Docker lifecycle/resource controls;
add a default-false read-only submission mount option. Never mount the original
generation workspace, skills, hidden evaluator, old output or credentials.

Only `/usr/local/bin/evas` and a fixed bounded output reader run there. Neither
model Bash commands nor wrapper markers establish execution authority. Bind the
actual process outcome, attempt/task, candidate, profile, image, invocation ID,
parser policy and accepted output hash into a coordinator-owned receipt.
No verdict, hidden threshold, final-score reuse or Spectre claim is introduced.

## Acceptance / limits

- Preserve r53 + EVAS 0.8.7, legacy defaults and current public validator.
- Bound each input tree to 256 entries / 16 MiB total / 1,000,000 bytes per file; reject
  links, nonregular files, unexpected candidates and unsafe paths. Task profile
  is frozen before calls; verify live candidate/task and terminal state before
  and after execution. Coordinator owns exclusive source-workspace access.
- Pin image by sha256, verify actual image/version; use fresh private scratch,
  no network, read-only task/candidate mounts and absolute executable paths.
  Scratch is an exclusive temporary sibling of the source runtime, in its
  trusted Docker-shared parent; never inside the generation public mounts.
- Only fixed `tran.csv` from this invocation's tmpfs may supply the summary.
  Cap extraction at parser MAX_BYTES, reject symlink/FIFO and use isolated Python
  import mode. Missing/invalid/too-large/failed outputs never imply correctness.
- No reusable output on timeout or infrastructure failure; cleanup attempted on
  every branch. Infrastructure/identity failures invalidate this executor.
- Unit adversarial cases plus real free Docker checks cover fresh output,
  immutable inputs, candidate/profile/image binding and DUT/Testbench contracts.
  Receipt hashes are tamper-evident joins under a trusted coordinator/host, not
  signatures, hostile-host defense or proof against simulator vulnerabilities.

## Sequence / ownership / stop condition

Concrete mapping: `operations/calibration_pilot/public_waveform.py` (under
`benchmark-vabench-release-v4/`) and `tests/test_agent_harness_public_waveform.py`.
`public_execution_contract()` must accept the metadata before replacing the
fixed bare EVAS token with `/usr/local/bin/evas`. DUT/bugfix output root is
`/tmp/vabench-visible/evas-output`; Testbench root adds `/reference`. The copied
bytes must match canonical sorted `{path, sha256}` candidate rows, never the
wrapper-specific framed digest. Tests explicitly cover wrapper/PATH bypass,
stale outputs, both roots, candidate/image drift and separate cleanup incidents.

Main owns plan/docs/Git; `public_waveform.py`, its tests, the minimal environment
mount option, parser byte-input reuse and their tests, and the relevant CI gate.
Read-only mapping and boundary reviewers have no write/Git rights. Follow
vertical TDD, focused GREEN commits, independent review, full harness regression
and Docker smoke; publish only to BucketSran origin.

This slice stops with the verified standalone executor and source-binding
receipt. Registry/controller budget admission, native tool exposure, trajectory
and scorer joins, and Evolution/memory activation are a subsequent opt-in slice.
No automatic CLI switch, corpus ingestion, real training/export, paid model call,
new dependency, sealed release mutation or EVAS source change is authorized.

## Verified outcome

Implementation commit `8b747e977c`. Independent code review found zero issues;
LSP/typecheck unavailable is an explicit validation gap, not a claimed pass.
Main verified Ruff 0.12.12, AST, bytecode compilation and workflow YAML. Final
full harness: 939 passed / 21 opt-in skipped; focused module: 30 passed / 2 skipped;
real Docker DUT/Testbench: 2 passed, each with two fresh executions and actual
read-only/network/cleanup inspection. Active navigation + CI: 38 passed.
Exact commands, initial Docker sharing failure and final proof are in the log.
Next native integration is separately scoped; this executor is not a model tool.
