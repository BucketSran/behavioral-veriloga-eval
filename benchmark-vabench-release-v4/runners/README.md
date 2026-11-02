# benchmarkv4 runners

This directory contains public runtime tooling for
`benchmark-vabench-release-v4/release/benchmarkv4-r51`.

Implemented:

- `run_benchmarkv4_campaign.py` is the unified experiment entry point for
  `release/benchmarkv4-r51`: it builds a random or preselected campaign, then
  runs `G0`/`G1` through direct one-shot artifact extraction and `G2`-`G5`
  through the pinned mini-SWE-agent scaffold in the shared public Docker
  runtime, where the agent has full Bash and direct access to public EVAS.
  Both paths enter the same strict declared-artifact gate before they become
  score-eligible.

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
  --agent-timeout-s 5400 \
  --per-turn-max-tokens 65536 \
  --workers 12 \
  --output-root /tmp/benchmarkv4-deepseek-campaign
```

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
  --agent-timeout-s 5400 \
  --per-turn-max-tokens 65536 \
  --workers 12 \
  --output-root /tmp/benchmarkv4-deepseek-campaign
```

Set `VABENCH_PYTHON=/absolute/path/to/python` to select a specific host
interpreter. The launcher does not rely on a Python-version change to repair
invalid terminal descriptors; it disconnects the process from the calling
terminal before Python starts.

`--evas-command` is mandatory for executable campaigns. The wrapper resolves
the executable to an absolute path and stores its binary hash and complete
version identity in the campaign manifest; the runner refuses a changed
identity before any API request. Formal runs never fall back to a PATH-derived
`evas`.

The runner uses wall-clock time as the primary episode stopping rule. The
`--per-turn-max-tokens` value is passed to the provider as a per-call
`max_tokens` cap and is reported as telemetry; accumulated token usage does not
terminate an episode. Provider context-window failures and single-call output
limit stops are recorded as separate termination reasons. There is no fixed
revision-count or tool-call-count budget.

`--workers` controls concurrent cells and local work. Use
`--api-max-inflight` to cap provider requests independently after running
`operations/calibration_pilot/calibrate_provider_concurrency.py`. Provider
timing, timeout, transport-tool, and error-attribution requirements are defined
in
[`operations/calibration_pilot/PROVIDER_EVALUATION_PROTOCOL.md`](../operations/calibration_pilot/PROVIDER_EVALUATION_PROTOCOL.md).

## Executable-feedback control

`--comparison-profile executable-feedback-control` creates three matched arms:

- `OneShot`: G0 direct one-shot generation;
- `Agent-NoExec`: the G2 mini-SWE scaffold and public workspace, with EVAS,
  public simulator diagnostics, and waveforms absent;
- `Agentic`: the same G2 mini-SWE scaffold and public workspace, with pinned
  EVAS execution, diagnostics, and waveforms available.

Agent-NoExec uses the paired
`vabench-agent-runtime:0.8.4-noexec` image. The image has the same base,
dependency lock, shell, and mini-SWE controller, but the `evas-sim` package,
`evas` executable, runtime descriptor, and EVAS-specific prompt contract are
removed. All arms use the same configured private final judge outside the
model-visible container. The campaign records the judge-command hash and the
single controlled difference.

The last 50 complete families are selected deterministically with
`--family-range 351-400`; unlike `--sample-families 50`, this is not random:

```bash
python3 benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py \
  --release benchmark-vabench-release-v4/release/benchmarkv4-r51 \
  --family-range 351-400 \
  --comparison-profile executable-feedback-control \
  --model MODEL_ID \
  --base-url API_BASE_URL \
  --api-key-file /path/to/key.txt \
  --evas-command "$(pwd)/.venv/bin/evas" \
  --final-judge-command "python3 /path/to/private_spectre_adapter.py" \
  --agent-timeout-s 5400 \
  --per-turn-max-tokens 65536 \
  --workers 12 \
  --output-root /path/to/output
```

With all three task forms, one repetition contains 50 families, 150 tasks, and
450 cells.

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
