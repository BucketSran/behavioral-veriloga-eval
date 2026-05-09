# B1 Prompt Controller Finding - 2026-05-09

## Finding

The adaptive behavior-repair prompt currently over-injects generic guidance for
some simple B1 tasks.  This is an important confounder: failures can come from
prompt/control overload rather than model inability or token ceiling alone.

The practical implication is that B1 repair should use a controller that selects
the minimal relevant information for the current failure mode, rather than
concatenating every repair policy, diagnostic, syntax rule, original prompt, and
candidate file into one large prompt.

## Why The Prompt Became Large

`build_evas_guided_repair_prompt()` composes the repair prompt from multiple
sections:

- artifact contract and output rules
- targeted EVAS repair skill
- observation-driven repair policy
- metric-to-mechanism map
- behavioral diagnosis analysis
- EVAS result and notes
- loop state/history
- original task prompt
- current candidate files
- strict validation/module/syntax contracts

Even with `--no-repair-skill` and `--disable-contract-diagnosis`, the prompt can
still include broad generic repair policies and syntax contracts.

## Prompt Size Evidence

| Task | Original prompt chars | Adaptive prompt chars | Ratio | 8192 result |
| --- | ---: | ---: | ---: | --- |
| `vbm1_first_order_lowpass_dut` | 608 | 12185 | 20.0x | first call hit `length`; retry generated |
| `vbm1_resettable_counter_divider_dut` | 1437 | 16128 | 11.2x | `no_code_extracted` at 8192 |
| `vbm1_edge_detector_dut` | 604 | 11747 | 19.4x | generated |

This means the controller was spending most of the prompt budget on meta-repair
instructions rather than the small task contract.

## Compact Controller Experiment

Target task: `vbm1_first_order_lowpass_dut`

Compared prompts:

| Condition | Prompt chars | API elapsed | Finish | Generated file | EVAS |
| --- | ---: | ---: | --- | --- | --- |
| full adaptive strict+retry, 8192 | 12185 | 209.53s | first `length`, retry `stop` | yes | 0/1 |
| full adaptive strict+retry, 32768 | 12185 | long call stopped | no final meta | no complete result | not decisive |
| compact controller, 32768 | 3001 | 67.744s | `stop` | yes | 0/1 |
| compact-controller runner mode, 32768 | 5448 | 56.686s | `stop` | yes | 0/1 |

Compact-controller artifact:

- generated root:
  `generated-b1-ablation-compact-controller-firstorder-mimo-mt32768-20260509`
- result root:
  `results/b1-ablation-compact-controller-firstorder-mimo-mt32768-evas-20260509`

The compact prompt reliably produced a complete Verilog-A file with
`finish_reason=stop`, but the candidate still failed EVAS with:

```text
returncode=1
evas_runtime_error=ZeroDivisionError: float division by zero
tran.csv missing
```

## Runner Mode Smoke

Implementation added to `runners/run_adaptive_repair.py`:

- `--compact-controller {off,fallback,always}`
- `--compact-controller-public-spec-mode`
- `--compact-controller-max-candidate-chars`
- per-round `generation_meta.json` fields:
  `compact_controller_used`, `prompt_chars`, and the controller configuration

Smoke command root:

- generated root:
  `generated-b1-compact-controller-runner-smoke-mimo-mt32768-20260509`
- official EVAS result root:
  `results/b1-compact-controller-runner-smoke-mimo-mt32768-evas-20260509`

Official EVAS result: 2/3 pass.

| Task | Prompt chars | API elapsed | Finish | Official EVAS | Notes |
| --- | ---: | ---: | --- | --- | --- |
| `vbm1_edge_detector_dut` | n/a | n/a | reused PASS anchor | PASS | no repair call needed |
| `vbm1_first_order_lowpass_dut` | 5448 | 56.686s | `stop` | FAIL | still `ZeroDivisionError` / `tran.csv missing` |
| `vbm1_resettable_counter_divider_dut` | 5252 | 358.925s | `stop` | PASS | repaired divider ratio: `ratio=5`, `out_edges=16` from `in_edges=80` |

This strengthens the earlier finding:

1. The controller is effective for prompt-size and artifact-completeness control.
2. It can improve some tasks when the problem is a compact compile/interface
   repair plus a simple behavior surface (`resettable_counter_divider`).
3. It is not sufficient for first-order analog dynamics; that task needs a
   mechanism-specific repair template or a checker-guided runtime diagnosis.
4. Provider wall time is not explained by prompt size alone.  Resettable used a
   5252-character prompt but took 358.925 seconds, so provider latency/output
   generation remains a separate bottleneck.

## Reproducibility Checks

- `python3 -m py_compile runners/run_adaptive_repair.py runners/validate_benchmark_v2_gold.py`
- `python3 -m pytest tests/test_compact_controller_repair.py -q`
- official EVAS validation with `runners/validate_benchmark_v2_gold.py`

Audit caveat: adaptive quick-check under-reported
`vbm1_resettable_counter_divider_dut` as not having a behavior check, while
official validation marked it PASS.  Therefore B1 behavior claims should use
`validate_benchmark_v2_gold.py` result roots, not adaptive quick summaries.

## Interpretation

1. Compact prompting improves generation controllability and latency.  It turned
   a long-tail prompt into a normal `stop` response in 67.744 seconds.
2. Compact prompting alone is not a behavior-repair mechanism.  It produced a
   clean artifact, but the first-order lowpass still failed EVAS.
3. The next controller should route by failure layer:
   - artifact recovery: shortest prompt, only interface/module/syntax/runtime
     constraints
   - behavior repair: include only the specific measured behavior failure
   - task mechanism template: include a small circuit-specific template only
     when the task class is simple and known
4. The right comparison is no longer fixed token budget.  Use a high token
   ceiling as a resource budget, then compare fixed controller policies.

## Recommended Next Experiment

Implement a `compact-controller` repair mode in `run_adaptive_repair.py`:

- trigger on `finish_reason=length`, API wall-time timeout, `no_code_extracted`,
  or runtime artifact notes such as `tran.csv missing`
- use a short prompt limited to:
  - module name and ports
  - required output artifact
  - exact EVAS failure notes
  - current candidate file
  - one selected mechanism hint
- avoid generic skill bundles, broad metric maps, and long syntax tutorials unless
  the failure explicitly requires them

Then run EVAS-only B1 smoke with:

```text
strict + retry + compact-controller + high-token-ceiling
```

Primary metrics:

- EVAS pass@1
- generated file rate
- long-call rate
- mean/median API elapsed time
- failure transition: no-code -> compile -> runtime -> behavior
