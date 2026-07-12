# Cascode Gain-cell Headroom Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Cascode Gain-cell Headroom Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `cascode_gain_cell_headroom.va`:
  - Module `cascode_gain_cell_headroom` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vbias` (input, electrical)
    - position 2: `vdd_sense` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `rst` (input, electrical)
    - position 5: `vout` (output, electrical)
    - position 6: `gain_metric` (output, electrical)
    - position 7: `headroom_ok` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cascode_gain_cell_headroom` as `XDUT` with ordered public binding: vin=vin, vbias=vbias, vdd_sense=vdd_sense, enable=enable, rst=rst, vout=vout, gain_metric=gain_metric, headroom_ok=headroom_ok.

## Public Parameter Contract

- `cascode_gain_cell_headroom.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `cascode_gain_cell_headroom.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `cascode_gain_cell_headroom.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `cascode_gain_cell_headroom.gain` defaults to `1.8`; valid range: finite; overrides gain.
- `cascode_gain_cell_headroom.headroom_drop` defaults to `0.16`; valid range: finite; overrides headroom_drop.
- `cascode_gain_cell_headroom.tr` defaults to `150p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_OR_LOW_ENABLE_DRIVES_VOUT`: exercise and make observable: Reset or low `enable` drives `vout` to common mode and clears metrics. Required traces: `time`, `vin`, `vbias`, `vdd_sense`, `enable`, `rst`, `vout`, `gain_metric`, `headroom_ok`.
- `P_WHEN_ENABLED_COMPUTE_AN_INVERTING_GAIN`: exercise and make observable: When enabled, compute an inverting gain-cell output around common mode. Required traces: `time`, `vin`, `vbias`, `vdd_sense`, `enable`, `rst`, `vout`, `gain_metric`, `headroom_ok`.
- `P_CLAMP_THE_OUTPUT_BETWEEN_VSS_AND`: exercise and make observable: Clamp the output between `vss` and the available headroom limit. Required traces: `time`, `vin`, `vbias`, `vdd_sense`, `enable`, `rst`, `vout`, `gain_metric`, `headroom_ok`.
- `P_GAIN_METRIC_REPORTS_THE_ABSOLUTE_OUTPUT`: exercise and make observable: `gain_metric` reports the absolute output excursion from common mode. Required traces: `time`, `vin`, `vbias`, `vdd_sense`, `enable`, `rst`, `vout`, `gain_metric`, `headroom_ok`.
- `P_HEADROOM_OK_IS_HIGH_ONLY_WHEN`: exercise and make observable: `headroom_ok` is high only when the available headroom limit remains above common mode. Required traces: `time`, `vin`, `vbias`, `vdd_sense`, `enable`, `rst`, `vout`, `gain_metric`, `headroom_ok`.

The required trace names are: `time`, `vin`, `vbias`, `vdd_sense`, `enable`, `rst`, `vout`, `gain_metric`, `headroom_ok`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
