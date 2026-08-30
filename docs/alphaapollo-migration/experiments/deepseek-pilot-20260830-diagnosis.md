# DeepSeek pilot: offline trajectory diagnosis

Date: 2026-08-30. Analysis base: `34823a7dfca6ff3385b6ad274741ecaa218766a7`.
This is a sanitized engineering case study, not a model comparison or score.
The [original stopped-run audit](deepseek-pilot-20260830.md) owns the frozen
source, schedule, budget and root evidence hashes.

## Brief, method and boundary

Question: where did the two DUT cells spend their eight admitted model calls,
and which obstacles belong to the harness rather than the candidate or provider?
Acceptance: reconstruct every attempted round, test falsifiable interface
hypotheses, preserve the original evidence and distinguish observation from
causal inference. No paid request, credential load, simulator invocation,
final judging, source-code repair or r53/EVAS mutation occurs in this diagnosis.

The feedback loop is deterministic replay of hash-bound events plus small
offline probes, not another generation run. Two native rows were revalidated
with `read_native_cell` and matched the frozen pilot index exactly. All four
root hashes still match; the four unstarted runtimes remain absent.

Private event files, relative to the ignored live-run root:

| Backend | File | SHA-256 |
| --- | --- | --- |
| native-mini-swe | `native-mini-swe/run/v4-029-G2-r00-agentic/evidence/native-launcher/private-events.jsonl` | `89152cb5f1beca87de7728f8a033f17a2487badb1e17a56ea0fbaf38917ffb60` |
| native-reasoning | `native-reasoning/run/v4-029-G2-r00-agentic/evidence/native-launcher/private-events.jsonl` | `d2d49a9529514691d4c8c43dd88bbfd6e3ffd2671cb7bbefe4b0520f192b7972` |

Commands below are described, not executable replay instructions. Raw responses,
candidate source, output logs and wrapper nonces remain private. Frozen event
sequence numbers let an authorized reviewer reproduce the attribution.

## Round-by-round case study

| Admitted call | native-mini-swe | native-reasoning |
| ---: | --- | --- |
| 1 | List task/submission; read public runtime command | Search installed Verilog-A examples |
| 2 | Read task instruction and visible deck | Locate public workspace; one shell command returns 1 |
| 3 | Read EVAS help | Read task instruction, deck and runtime command |
| 4 | Write candidate v1 | Read installed ideal/delayed comparator examples |
| 5 | Attempt EVAS from wrong cwd; deck not found | Inspect task/submission directories |
| 6 | Fix cwd; strict lint rejects conditional analog operators | Write candidate v1 |
| 7 | Edit candidate; public EVAS compile/simulation completes | Attempt EVAS from wrong cwd; deck not found |
| 8 | Rerun unchanged candidate to inspect warnings; no submit | SSL handshake fails; no response or tool action |
| After cap/stop | Ninth policy request refused before HTTP | Shared budget stops; no retry |

Mini-swe tool-output sequences are 4, 10, 16, 22, 28, 34, 40, 46;
Reasoning sequences are 4, 10, 16, 22, 28, 34, 40. Neither executes
`vabench-submit`. All 15 returned responses use native tool calls; the replay
shows no malformed/multiple-action rejection or output-limit finish.

Mini-swe's first candidate triggered `EVAS-COMP-E2143`; it then moved the
output operations outside the conditional and obtained a public simulation
completion. This is evidence of a useful validation/edit loop, not an EVAS
defect or a hidden behavioral pass. Two warnings remained. Reasoning's candidate
was not successfully simulated before the transport stop. We did not score
either candidate after the fact.

## Findings and confidence

### 1. Confirmed bug: Reasoning omits the operational Bash/submit contract

The two backends share the executor, image, public task, controller, freeze and
judge path, but do not receive equivalent operational instructions.

- `NativeMiniSwePolicy` appends `mini.BASH_CONTRACT` to its first user message
  in [run_native_mini_swe.py](../../../benchmark-vabench-release-v4/operations/calibration_pilot/run_native_mini_swe.py)
  (class at lines 865-878 on the analysis base).
- The Reasoning branch passes only the original task prompt through the
  observation payload (lines 782-798). Its generic system prompt and shared
  Bash tool description do not explain the submit executable.
- Every captured mini-swe request contains `vabench_bash_contract` and
  `vabench-submit`; none of Reasoning's eight captured requests contains either,
  including tools and message history. This is not just a difference in wording.

The omission affects the shared native Reasoning interactive path, not OneShot
or legacy mini-swe. It removes an essential discoverability contract. It does
not prove that adding the text alone would have completed this task: the run
also encountered path friction and an unrelated SSL failure.

Existing free integration fixtures preprogram `vabench-submit` independently of
the incoming prompt; see `test_pilot_real_docker_free_http_preserves_all_six_rows`
in [test_agent_harness_deepseek_pilot.py](../../../tests/test_agent_harness_deepseek_pilot.py).
They prove execution/freeze/scoring connectivity, not that a model is told how
to submit. This explains why those gates did not detect the omission.

### 2. Confirmed interface gap: the pilot call horizon is not model-visible

Neither backend's public instruction provides the eight-call limit or remaining
calls. `BudgetedDeepSeekClient.complete()` passes messages through unchanged;
`DeepSeekPilotBudget.begin_call()` enforces the limit externally in
[deepseek_budget.py](../../../benchmark-vabench-release-v4/operations/calibration_pilot/deepseek_budget.py).

Mini-swe spent call 8 inspecting warnings after public simulation success on
call 7, then hit the guard. Budget enforcement worked. Whether horizon
information would improve submission rate is untested; eight calls cannot be
interpreted as an ordinary r53 stopping rule or a model-capability conclusion.

### 3. Confirmed path friction and layered exit-status semantics

The Docker workspace is `/workspace`; the public runtime command is relative
to that root. Both agents added an incompatible `cd`, producing respectively
`/workspace/public/task/public/task/visible_test.scs` and
`/workspace/public/public/task/visible_test.scs`. The shared Bash contract lists
relative directories but does not explicitly name the absolute root or explain
the fresh per-command shell. Reasoning additionally misses the entire contract.

A read-only probe in the frozen image confirms that the relative deck exists
from `/workspace` and not from those other two directories. No candidate was
mounted or executed by the probe.

The failed EVAS commands pipe into `head`/`tail`: Bash reports the last pipeline
stage's zero status, while EVAS wrapper telemetry records exit 1. A synthetic
failed child in the same image reproduces status 0 normally and 1 with
`pipefail`. This is normal shell semantics, not lost private telemetry.
The model sees cleaned diagnostic text and the whole Bash status; wrapper
markers are removed. No structured per-EVAS status is included in that public
observation. Error text was present, so the pipeline did not hide every signal.

### 4. Confirmed information surface: installed EVAS examples are readable

Reasoning read the package's `cmp_ideal.va` and `cmp_delay.va` (tool-output
sequence 22), not just their filenames. These are installed public examples,
not evidence of hidden-checker or private-answer access.

Read-only filename inventories found 15 `.va` examples in the pinned Agentic
image `fe44bb543701…`, including both files, and zero at that package location
in the local paired no-EVAS image
`sha256:8da5b17c97a6d5f3a9b7685d57e6643ca083ad488cda05ecb75b8115392ab124`.
This is a scoped package-directory check, not an exhaustive information-leak
audit of either image.

Both cells in this pilot use the same Agentic image, so actual example use is
a behavioral difference, not a configured information mismatch between these
two cells. A future Agentic/no-EVAS causal comparison must either equalize the
relevant documentation surface or explicitly study the bundled environment
effect. No image or package is modified here.

### 5. Confirmed transport stop; no output-protocol failure observed

The eighth Reasoning HTTP attempt returned curl 35, zero response-body bytes
and no terminal usage. The budget guard retained the uncertain reservation and
stopped before retry. This is distinct from an invalid candidate or refusal to
submit. We cannot infer how its next action would have behaved.

## Do not conflate counters

| Recorded field | Actual meaning in this run |
| --- | --- |
| Mini-swe provider requests = 9; HTTP attempts = 8 | Includes a ninth policy request rejected before transport |
| Mini-swe `evas_usage.calls_executed = 5` | One help invocation plus four simulation attempts; two simulation attempts completed |
| Mini-swe `evas_usage.calls_failed = 2` | Wrong path and strict-lint rejection, despite whole Bash status 0 |
| Native `telemetry.evas_calls = 0` | Legacy `run_evas` function-tool counter, not direct Bash EVAS usage |
| Native metering `tools.failures = 0` | No harness `tool_failure` event; does not mean every shell command succeeded |

Per-invocation return codes remain in raw `evas_invocations`; help versus
simulation is not a structured operation field. Generic invocation/candidate-
hash counts must not be relabeled as successful simulations or refinement
rounds. See `summarize_evas_invocations()` in
[run_campaign.py](../../../benchmark-vabench-release-v4/operations/calibration_pilot/run_campaign.py),
`event_telemetry()` in
[score_campaign.py](../../../benchmark-vabench-release-v4/operations/calibration_pilot/score_campaign.py),
and tool-event aggregation in
[evidence_export.py](../../../runners/agent_harness/evidence_export.py).

## Minimal next repair, not implemented in this diagnosis

1. **Operational-contract parity first.** Reuse the existing public Bash
   contract when constructing native Reasoning observations. Test the actual
   outbound first request for Agentic and No-EVAS across all three forms,
   including submission, paths and the condition-appropriate executable
   authority. Keep OneShot unchanged. Do not copy EVAS-available guidance into
   the no-EVAS condition without checking its existing transformation.
2. **Explicit workspace and pilot horizon.** Explain `/workspace` and
   per-command cwd behavior in the public environment contract. Keep any
   trusted remaining-call information pilot-specific; do not hard-code eight
   calls into generic Reasoning or alter sealed r53 policy. Verify no refund,
   reset, hidden-test feedback or extra HTTP can arise from the new message.
3. **Clarify diagnostic reporting.** Separate Bash execution, direct EVAS
   invocation, simulation completion and final score. If public per-process
   status is added later, retain shell semantics and strip private markers;
   do not globally change pipelines without compatibility tests.
4. **Record the examples policy before causal comparisons.** Inventory and
   bind accessible material to image/campaign identity; decide equalization
   versus bundled-environment scope before a new run, not from its scores.

Use test-first, independently reviewable implementation commits. A new paid
pilot requires a separately frozen decision/budget and cannot replace these
six original denominator rows. Family029 remains development exposure.

## Verification and limits

- Strict offline evidence reread: both native rows equal their frozen index
  records; root hashes match; all four unstarted runtimes absent.
- Main free focused suite: **81 passed, 3 opt-in Docker tests skipped** in
  0.25s (`test_agent_harness_deepseek_budget.py`, `deepseek_pilot.py`,
  `mini_swe_backend.py`, `reasoning_backend.py`, with the full `test_agent_harness_`
  prefix). Skips are not integration passes.
- Independent read-only code lane: **56 passed, 42 deselected** in 0.63s for
  selected controller/backend contracts; these overlap the main suite.
- Fresh offline Docker probes: relative-path and pipeline hypotheses reproduced;
  example-directory inventories completed. Only disposable containers changed.
- Existing green tests do not prove the missing prompt contract is correct.
  No new regression or runtime repair is claimed in this documentation slice.
- No final score, baseline reproduction, backend ranking or EVAS defect is
  established. Original raw artifacts and stopped budget remain unchanged.
