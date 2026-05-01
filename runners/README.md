# Runner design

This directory is reserved for the benchmark harness implementation.

Planned runner split:

- `migrate_veriloga_evals.py`
  Converts the legacy `veriloga/evals/evals.json` list into structured
  `behavioral-va-eval/tasks/...` case directories
- `generate.py`
  Calls the model/agent and materializes DUT/testbench outputs
- `simulate_evas.py`
  Runs voltage-domain `.scs` cases under EVAS and collects DUT/testbench/sim outcomes
- `run_examples_suite.py`
  Executes the 14 self-contained benchmark examples from `examples/manifest.json`
  with their default testbenches and emits a smoke-suite report
- `run_gold_suite.py`
  Auto-discovers formal end-to-end tasks that already have `gold/` DUT/testbench
  assets and runs them through EVAS to emit reusable verification evidence
- `run_gold_dual_suite.py`
  Reuses the gold-backed end-to-end tasks, runs EVAS plus remote Spectre,
  exports `tran_spectre.csv`, reuses the same behavior checks, and emits
  waveform-parity summaries for coordination backfill
- `simulate_openvaf.py`
  Out of scope for this benchmark
- `score.py`
  Computes per-layer scores and aggregate reports from executable evidence

Recommended workflow:

1. load task case directory
2. generate candidate output
3. invoke EVAS on the DUT/testbench pair
4. run behavior checks
5. score from compiled/simulated artifacts
7. emit `result.schema.json`-compatible output

Do not introduce precheck-only scorers as benchmark outputs. Syntax/rule checks
may exist internally inside executable runners, but benchmark results should be
driven by DUT compile, testbench compile, and behavioral evidence.

Current implemented executable runner:

- `simulate_evas.py`
  Inputs: `task_dir`, `dut.va`, `tb_*.scs`
  Outputs:
  - benchmark signature guardrail notes
  - `dut_compile`
  - `tb_compile`
  - `sim_correct`
- `run_examples_suite.py`
  Inputs: benchmark `examples/manifest.json`
  Outputs:
  - per-example EVAS smoke result for the 14 default examples
- `run_gold_suite.py`
  Inputs: `tasks/end-to-end/voltage/*/gold/`
  Outputs:
  - per-task EVAS result for every discoverable gold-backed end-to-end task
  - `summary.json` in the chosen output directory
- `run_gold_dual_suite.py`
  Inputs: `tasks/end-to-end/voltage/*/gold/`, bridge repo path, Cadence cshrc
  Outputs:
  - per-task EVAS + Spectre result
  - `tran_spectre.csv` under each task output directory
  - waveform parity summary in `summary.json`
  - bridge preflight diagnostics in `summary.json` so misconfigured tunnel /
    Virtuoso / Spectre sessions fail fast instead of hanging until subprocess
    timeout

## Signature guardrail

Task metadata may include a `signature_requirements` object:

```json
{
  "signature_requirements": {
    "required_ports": ["OUTP", "OUTN", "VCTR", "VDD", "VSS"],
    "required_parameters": ["Kvco"],
    "required_tokens": ["idtmod(", "$bound_step(", "flicker_noise("],
    "forbidden_tokens": ["ddt("],
    "required_tb_tokens": ["simulator lang=spectre", "tran", "save"],
    "forbidden_tb_tokens": []
  }
}
```

`simulate_evas.py` checks these requirements before invoking EVAS. Missing DUT
ports, public parameters, or benchmark-critical DUT tokens fail the candidate
with `FAIL_DUT_COMPILE`; missing testbench tokens fail with `FAIL_TB_COMPILE`.
Both paths emit a `signature_guardrail_failed` note. This keeps candidates from
receiving compile/simulation credit when they omit prompt-critical items such as
noise, timestep control, required integration idioms, or required testbench
statements.

Legacy `must_include` and `must_not_include` metadata remain broad authoring
hints. They are not automatically promoted to hard signature checks unless a
task also writes the corresponding explicit `signature_requirements` fields.

Recommended Spectre workflow:

1. `./scripts/check_bridge_ready.sh`
   Quick preflight-only sanity check for bridge, tunnel, and Spectre visibility.
2. `./scripts/run_with_bridge.sh python3 runners/run_gold_dual_suite.py ...`
   Recommended reproducible path. The wrapper creates a temporary SSH tunnel for
   the child command, runs bridge preflight, and cleans the listener up on exit.

Keep `start_bridge_tunnel.sh` and `stop_bridge_tunnel.sh` for manual debugging.
For routine validation runs, prefer the wrapper so background tunnel state does
not drift away from the command you actually care about.

Useful preflight variants:

1. `./scripts/check_bridge_ready.sh --json`
   Machine-readable summary for local debugging or wrapper health checks.
2. `./scripts/check_bridge_ready.sh --require-daemon`
   Treat a disconnected Virtuoso CIW daemon as a hard failure.
3. `./scripts/check_bridge_ready.sh --require-daemon --json`
   Strict JSON mode for automation that depends on an active Virtuoso session.

Current regression protection:

1. `python -m py_compile runners/bridge_preflight.py runners/run_gold_dual_suite.py runners/signature_guardrail.py`
2. `python -m pytest -q tests/test_bridge_preflight.py tests/test_bridge_scripts.py tests/test_run_gold_dual_suite.py tests/test_save_statements.py tests/test_pwl_statements.py tests/test_signature_guardrail.py`

These smoke tests cover the bridge preflight JSON surface and the
`tb-generation` `parity=not_required` control path, the gold testbench lint
guards, and helper-script behavior such as bridge-repo overrides plus wrapper
usage checks.
