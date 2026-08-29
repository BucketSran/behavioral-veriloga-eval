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
- `run_vabench_v3_model_eval.py`
  Runs the v3 public-prompt generation and private hidden-scoring entrypoint,
  indexes environment/input/result provenance, and derives the formal claim
  gate from executed evidence.
- `../scripts/run_v3_clean_room_smoke.py`
  Executes one deterministic generation-to-hidden-scoring path in a temporary
  public clean room and verifies private-path isolation plus cleanup.
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
- `materialize_main120_inventory.py`
  Inputs: local `vabench-main-v1-main120` EVAS/Spectre result directories and
  current `tasks/` metadata.
  Outputs:
  - `docs/VABENCH_MAIN120_MATERIALIZATION.md`
  - `docs/VABENCH_MAIN120_MATERIALIZATION.csv`
  - source-materialization counts for main120 provenance/recovery work

Recommended Spectre workflow:

1. `labctl -v check`
   Quick preflight for SSH, remote bash/tar/timeout, and Spectre visibility
   after sourcing the Cadence cshrc.
2. `python3 scripts/run_v3_spectre_audit.py --spectre-backend labctl ...`
   Recommended v3 path. The runner stages the Spectre case locally, uses
   `labctl up` to transfer it, runs the final Spectre command behind a tiny
   remote csh boundary, downloads the completed run directory, and reuses the
   existing PSFASCII/checker path.

See `docs/LABCTL_SPECTRE_WORKFLOW.md` for the distilled THU configuration and
the 451-row chunked audit commands.

Legacy bridge workflow:

1. `./scripts/check_bridge_ready.sh`
   Quick preflight-only sanity check for bridge, tunnel, and Spectre visibility.
2. `./scripts/run_with_bridge.sh python3 runners/run_gold_dual_suite.py ...`
   Recommended reproducible path. The wrapper creates a temporary SSH tunnel for
   the child command, runs bridge preflight, and cleans the listener up on exit.

Keep `start_bridge_tunnel.sh` and `stop_bridge_tunnel.sh` for manual debugging.
For old bridge validation runs, prefer the wrapper so background tunnel state
does not drift away from the command you actually care about.

Labctl Spectre backend:

- `--spectre-backend labctl` is the standard remote execution path for new v3
  Spectre evidence. It uses the same staged-input and PSF parsing logic as the
  old direct path, but delegates remote transfer, remote bash execution, and
  cleanup to the `labctl` CLI.
- The backend accepts `--sui-host` / `--sui-work-root` for compatibility and
  `--labctl-host` / `--labctl-work-root` as the preferred labctl spelling.
- Environment variables:

```bash
export VAEVAS_SPECTRE_BACKEND=labctl
export VAEVAS_SPECTRE_MODE=ax
export VAEVAS_LABCTL_HOST=zhangz@101.6.68.147
export VAEVAS_LABCTL_WORK_ROOT=/home/zhangz/WORK/vaevas-direct-spectre
export VAEVAS_LABCTL_CADENCE_CSHRC=/home/cshrc/.cshrc.cadence.IC618SP201
```

Direct SUI Spectre backend:

- `--spectre-backend sui-direct` is retained as a legacy fallback. It bypasses
  `virtuoso-bridge-lite` and runs
  Spectre over SSH on `thu-wei` by default, using `thu-sui` as the SSH jump
  host.
- The runner uploads an isolated gold testbench plus `ahdl_include` files to a
  temporary directory under `/tmp/vaevas-direct-spectre`, runs
  `spectre -format psfascii`, downloads the raw directory and side-output files,
  converts PSFASCII to `tran_spectre.csv`, then reuses the same checker path.
- Direct-SUI keeps isolated per-case run directories, but symlinks each case's
  Spectre `*.ahdlSimDB` directory into a content-addressed
  `_ahdlcmi_cache/` under the selected remote work root. This preserves
  Spectre AHDL-CMI warm-cache behavior across repeated visible/hidden reruns of
  the same Verilog-A source while still deleting the temporary run directory.
  Set `VAEVAS_SUI_DIRECT_AHDLCMI_CACHE=0` to restore fully cold runs; remove
  `<sui-work-root>/_ahdlcmi_cache` manually when a remote cache reset is needed.
- Direct-SUI Spectre uses a bounded license queue timeout derived from the
  runner timeout. Override it with `--spectre-license-wait-s`, and make sure
  `--timeout-s` is larger than the requested license wait.
- High-concurrency callers may provide a comma-separated pool of existing SSH
  master sockets through `VAEVAS_SSH_CONTROL_PATHS`. Entries must be absolute
  paths to existing Unix sockets. The runner validates the pool and assigns
  connections round-robin; it never creates or removes the masters. This
  explicit pool takes precedence over `VAEVAS_SSH_USE_CONFIG_MULTIPLEX`.
- Use it when the bridge listener is the blocker but SSH plus Cadence setup are
  available:

```bash
python3 runners/run_gold_dual_suite.py \
  --spectre-backend sui-direct \
  --sui-host thu-wei \
  --task <task_id>

python3 runners/run_vabench_release_dual_rerun.py \
  --spectre-backend sui-direct \
  --sui-host thu-wei \
  --workers 8
```

The direct backend uses
`/home/cshrc/.cshrc.cadence.IC618SP201` unless overridden by
`--cadence-cshrc`, `VAEVAS_SUI_CADENCE_CSHRC`, or `VB_CADENCE_CSHRC`.

Useful preflight variants:

1. `./scripts/check_bridge_ready.sh --json`
   Machine-readable summary for local debugging or wrapper health checks.
2. `./scripts/check_bridge_ready.sh --require-daemon`
   Treat a disconnected Virtuoso CIW daemon as a hard failure.
3. `./scripts/check_bridge_ready.sh --require-daemon --json`
   Strict JSON mode for automation that depends on an active Virtuoso session.

Current regression protection:

1. `python -m py_compile runners/bridge_preflight.py runners/run_gold_dual_suite.py`
2. `python -m pytest -q tests/test_bridge_preflight.py tests/test_bridge_scripts.py tests/test_run_gold_dual_suite.py tests/test_save_statements.py tests/test_pwl_statements.py`

These smoke tests cover the bridge preflight JSON surface and the
`tb-generation` `parity=not_required` control path, the gold testbench lint
guards, and helper-script behavior such as bridge-repo overrides plus wrapper
usage checks.
