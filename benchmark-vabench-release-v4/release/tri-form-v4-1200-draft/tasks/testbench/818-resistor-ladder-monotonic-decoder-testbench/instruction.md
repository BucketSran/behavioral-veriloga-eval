# Resistor Ladder Monotonic Decoder Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Resistor Ladder Monotonic Decoder` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `resistor_ladder_monotonic_decoder.va`:
  - Module `resistor_ladder_monotonic_decoder` (entry)
    - position 0: `code_2` (inout, electrical)
    - position 1: `code_1` (inout, electrical)
    - position 2: `code_0` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `rst` (inout, electrical)
    - position 5: `vout` (inout, electrical)
    - position 6: `step_metric` (inout, electrical)
    - position 7: `monotonic_ok` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `resistor_ladder_monotonic_decoder` as `XDUT` with ordered public binding: code_2=code_2, code_1=code_1, code_0=code_0, enable=enable, rst=rst, vout=vout, step_metric=step_metric, monotonic_ok=monotonic_ok.

## Public Parameter Contract

- `resistor_ladder_monotonic_decoder.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `resistor_ladder_monotonic_decoder.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `resistor_ladder_monotonic_decoder.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `resistor_ladder_monotonic_decoder.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `resistor_ladder_monotonic_decoder.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `resistor_ladder_monotonic_decoder.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive `vout` low, clear `step_metric`, and clear `monotonic_ok`. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.
- `P_DECODE_CODE_2_CODE_0_AS`: exercise and make observable: Decode `code_2..code_0` as an unsigned ladder tap index from 0 to 7. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.
- `P_DRIVE_VOUT_TO_THE_CORRESPONDING_EVENLY`: exercise and make observable: Drive `vout` to the corresponding evenly spaced ladder voltage between `vss` and `vdd`. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.
- `P_EXPOSE_ONE_LSB_STEP_ON_STEP`: exercise and make observable: Expose one LSB step on `step_metric` while enabled. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.
- `P_ASSERT_MONOTONIC_OK_WHEN_THE_ACTIVE`: exercise and make observable: Assert `monotonic_ok` when the active code-to-output mapping is nondecreasing. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.

The required trace names are: `time`, `code_2`, `code_1`, `code_0`, `enable`, `rst`, `vout`, `step_metric`, `monotonic_ok`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
