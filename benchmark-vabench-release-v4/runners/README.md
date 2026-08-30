# benchmarkv4 runners

This directory contains public runtime tooling for
`benchmark-vabench-release-v4/release/benchmarkv4-r53`, pinned to the
`vabench-agent-runtime:0.8.7` image.

Implemented:

- `run_benchmarkv4_campaign.py` is the unified experiment entry point for
  `release/benchmarkv4-r53`: it builds a random or preselected campaign, then
  runs `G0`/`G1` through direct one-shot artifact extraction and `G2`-`G5`
  through the pinned mini-SWE-agent scaffold in the shared public Docker
  runtime, where the agent has full Bash and direct access to public EVAS.
  Both paths enter the same strict declared-artifact gate before they become
  score-eligible.
- `--comparison-profile executable-feedback-control` projects every selected
  task onto three matched main-table arms: `OneShot` (G0),
  `Agent-No-EVAS` (the G2 mini-SWE/Bash scaffold without EVAS), and `Agentic`
  (G2 with EVAS). The two agent arms use paired `0.8.7` images built from the
  same Dockerfile; score reports group them by `experimental_arm`.
- Direct one-shot modes receive an output-only `submit_artifacts` function
  whose schema names every required file. The runner accepts only a complete
  declared bundle, narrowly normalizes redundant provider wrappers when their
  contents are identical, completes only unambiguous terminal JSON damage, and
  retains deterministic final-text recovery for providers that do not emit the
  function call. Malformed tool transport receives at most two attempts per
  run; an unrecovered transport is recorded as retryable
  `provider_transport_failure`, not as a candidate `invalid_submission`. None
  of these paths executes the candidate or returns checker feedback.

Boundary:

- The campaign runner is a generation/materialization runner, not the final
  Spectre scorer.
- Faithful single-turn API runs are `G0` and `G1`. `G2`-`G5` can read and write
  their isolated public workspace and invoke the pinned public `evas`
  executable; they cannot query a checker, gold solution, mutation catalog,
  hidden test, or score.
- Deprecated API-only and initial-judge entry points were removed from this
  package to keep one comparable G0-G5 path.

Unified G0-G5 campaign example:

```bash
python3 benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py \
  --sample-families 10 \
  --seed 20260715 \
  --model deepseek-v4-flash \
  --base-url https://api.deepseek.com/v1 \
  --api-key-file /path/to/key.txt \
  --evas-command "$(pwd)/.venv/bin/evas" \
  --per-turn-max-tokens 65536 \
  --workers 12 \
  --output-root /tmp/benchmarkv4-deepseek-campaign
```

Three-arm 400-family DeepSeek main-table example (3,600 cells per
repetition):

```bash
python3 benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py \
  --sample-families 400 \
  --comparison-profile executable-feedback-control \
  --model deepseek-v4-flash \
  --base-url https://api.deepseek.com/v1 \
  --api-key-file /path/to/key.txt \
  --evas-command "$(pwd)/.venv/bin/evas" \
  --per-turn-max-tokens 65536 \
  --workers 12 \
  --output-root /tmp/benchmarkv4-deepseek-main-table
```

Use repeated `--experimental-arm` flags to retain only a subset of the three
arms. A run containing only `OneShot` and/or `Agent-No-EVAS` does not require
`--evas-command`; any run containing `Agentic` does.

For an unattended run, use the detached launcher instead of inheriting a
terminal's standard streams. It binds stdin to `/dev/null`, sends stdout and
stderr to one log, and records the runner PID before returning:

```bash
benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign_detached.sh \
  --log /tmp/benchmarkv4-deepseek-campaign.log \
  --pid-file /tmp/benchmarkv4-deepseek-campaign.pid \
  -- \
  --sample-families 10 \
  --seed 20260715 \
  --model deepseek-v4-flash \
  --base-url https://api.deepseek.com/v1 \
  --api-key-file /path/to/key.txt \
  --evas-command "$(pwd)/.venv/bin/evas" \
  --per-turn-max-tokens 65536 \
  --workers 12 \
  --output-root /tmp/benchmarkv4-deepseek-campaign
```

Set `VABENCH_PYTHON=/absolute/path/to/python` to select a specific host
interpreter. The launcher does not rely on a Python-version change to repair
invalid terminal descriptors; it disconnects the process from the calling
terminal before Python starts.

`--evas-command` is mandatory when any selected arm exposes EVAS. The wrapper resolves
the executable to an absolute path and stores its binary hash and complete
version identity in the campaign manifest; the runner refuses a changed
identity before any API request. Formal runs never fall back to a PATH-derived
`evas`.

The runner uses wall-clock time as the primary episode stopping rule. Its limit
and deadline-finalization behavior are read only from
`benchmark-vabench-release-v4/EXPERIMENT_POLICY.json`; no CLI or campaign value
can override them. At the deadline, a complete declared submission is frozen
and scored normally while retaining `termination_reason=agent_timeout`. The
`--per-turn-max-tokens` value is passed to the provider as a per-call
`max_tokens` cap and is reported as telemetry; accumulated token usage does not
terminate an episode. Provider context-window failures and single-call output
limit stops are recorded as separate termination reasons.

Dry-run preflight without API credentials:

```bash
python3 benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py \
  --task-id v4-001 \
  --mode G0 \
  --model deepseek-v4-flash \
  --dry-run \
  --output-root /tmp/benchmarkv4-campaign-dry-run
```

Final trusted replay for a completed campaign:

```bash
python3 benchmark-vabench-release-v4/operations/calibration_pilot/score_campaign.py \
  --campaign-output /tmp/benchmarkv4-deepseek-campaign/run \
  --judge-kind final_trusted_replay \
  --evas-command "$(pwd)/.venv/bin/evas" \
  --judge-command \
    "python3 /path/to/trusted_replay_adapter.py"
```

For the opt-in native DUT/bugfix/Testbench three-condition path, add
`--episode-backend native-mini-swe --comparison-profile executable-feedback-control`
when creating the campaign and select supported forms explicitly. Keep the
default `--agent-scaffold mini-swe`; `--agent-scaffold native` is a different,
legacy sensitivity path. Native runs require fresh outputs and do not support
resume or post-freeze limit selection. Testbench public feedback is reference-DUT-only.
Native score aggregation uses
`--episode-backend native-mini-swe --campaign /absolute/path/campaign.json
--judge-kind final_trusted_replay` and reads existing terminal evidence instead
of invoking a judge. See `operations/calibration_pilot/README.md` for commands
and the deterministic smoke/claim boundary.

`--episode-backend native-reasoning` selects the distinct structured Reasoning
policy through the same native controller/runtime. Freeze the same backend
and `--reasoning-proposal-format` again at score time. Fresh-attempt recovery
uses `--native-max-attempts` (default one), never score-driven retries.
`score_campaign.py --ledger-output /absolute/new-ledger.json` optionally writes
a separate safe record/paired-coverage/claim ledger outside generation evidence.

Multi-model Evolution has a separate one-cell entrypoint,
`operations/calibration_pilot/run_evolution_campaign.py`; it is not another
single-trajectory backend flag. Its roster, round limits, public validation and
selection are frozen separately, and its final result must not be folded into
the single-trajectory ledger. See the calibration README for dry-run and roster
examples. Domain tools and real model quality experiments remain separate gates.
