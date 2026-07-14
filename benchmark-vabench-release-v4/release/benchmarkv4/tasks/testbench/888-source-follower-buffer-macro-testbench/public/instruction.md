# Source-follower Buffer Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Source-follower Buffer Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `source_follower_buffer_macro.va`:
  - Module `source_follower_buffer_macro` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vbias` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `headroom_metric` (output, electrical)
    - position 6: `valid` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `source_follower_buffer_macro` as `XDUT` with ordered public binding: vin=vin, vbias=vbias, enable=enable, rst=rst, vout=vout, headroom_metric=headroom_metric, valid=valid.

## Public Parameter Contract

- `source_follower_buffer_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `source_follower_buffer_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `source_follower_buffer_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `source_follower_buffer_macro.vgs_drop` defaults to `0.12`; valid range: finite; overrides vgs_drop.
- `source_follower_buffer_macro.min_headroom` defaults to `0.10`; valid range: finite; overrides min_headroom.
- `source_follower_buffer_macro.tr` defaults to `150p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_OR_LOW_ENABLE_DRIVES_THE`: exercise and make observable: Reset or low `enable` drives the output and metrics low. Required traces: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.
- `P_WHEN_ENABLED_THE_OUTPUT_FOLLOWS_VIN`: exercise and make observable: When enabled, the output follows `vin - vgs_drop`. Required traces: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.
- `P_CLAMP_THE_OUTPUT_BETWEEN_VSS_AND`: exercise and make observable: Clamp the output between `vss` and `vbias - min_headroom`. Required traces: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.
- `P_HEADROOM_METRIC_REPORTS_THE_REMAINING_VBIAS`: exercise and make observable: `headroom_metric` reports the remaining `vbias - vout` margin clipped to the nominal flag range. Required traces: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.
- `P_VALID_IS_HIGH_ONLY_WHEN_ENABLED`: exercise and make observable: `valid` is high only when enabled, not reset, and the bias rail can support at least the minimum headroom. Required traces: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.

The required trace names are: `time`, `vin`, `vbias`, `enable`, `rst`, `vout`, `headroom_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
