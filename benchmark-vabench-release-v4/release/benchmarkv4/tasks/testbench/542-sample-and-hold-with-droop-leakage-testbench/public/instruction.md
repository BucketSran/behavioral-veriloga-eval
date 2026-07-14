# Sample And Hold With Droop Leakage Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Sample And Hold With Droop Leakage` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `leaky_hold.va`:
  - Module `leaky_hold` (entry)
    - position 0: `sample` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `leaky_hold` as `XDUT` with ordered public binding: sample=sample, rst=rst, vin=vin, vout=vout.

## Public Parameter Contract

- `leaky_hold.vth` defaults to `0.45` V; valid range: vth > 0; sets sample and rst voltage-coded logic threshold.
- `leaky_hold.decay` defaults to `0.985`; valid range: 0 < decay <= 1; sets the multiplicative held-value retention factor per leakage update.
- `leaky_hold.leak_period` defaults to `1e-09` s; valid range: leak_period > 0; sets the periodic leakage update interval.
- `leaky_hold.tr` defaults to `5e-10` s; valid range: tr > 0; sets vout transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SAMPLE_CAPTURE`: exercise and make observable: Each rising sample crossing while reset is inactive captures the instantaneous vin voltage into the held state. Required traces: `time`, `sample`, `rst`, `vin`, `vout`.
- `P_HOLD_BETWEEN_EVENTS`: exercise and make observable: Between sample and leakage events, vout reflects the retained held state rather than continuously tracking vin. Required traces: `time`, `sample`, `vin`, `vout`.
- `P_PERIODIC_DROOP`: exercise and make observable: At every leak_period update while reset is inactive, the held value is multiplied by decay. Required traces: `time`, `rst`, `vout`.
- `P_RESET_CLEAR`: exercise and make observable: Active reset clears the held state to 0 V at sampling or leakage update events. Required traces: `time`, `sample`, `rst`, `vout`.
- `P_SMOOTH_OUTPUT`: exercise and make observable: Vout approaches each held-state target with the finite transition smoothing set by tr. Required traces: `time`, `vout`.

The required trace names are: `time`, `sample`, `rst`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
