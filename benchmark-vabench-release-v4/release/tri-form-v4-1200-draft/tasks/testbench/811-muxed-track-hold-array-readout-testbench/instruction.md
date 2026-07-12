# Muxed Track-hold Array Readout Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Muxed Track-hold Array Readout` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `muxed_track_hold_array_top.va`:
  - Module `muxed_track_hold_array_top` (entry)
    - position 0: `vin0` (input, electrical)
    - position 1: `vin1` (input, electrical)
    - position 2: `vin2` (input, electrical)
    - position 3: `clk` (input, electrical)
    - position 4: `rst` (input, electrical)
    - position 5: `sel_1` (input, electrical)
    - position 6: `sel_0` (input, electrical)
    - position 7: `sample_en` (input, electrical)
    - position 8: `vout` (output, electrical)
    - position 9: `channel_metric` (output, electrical)
    - position 10: `valid` (output, electrical)
- Artifact `track_hold_cell.va`:
  - Module `track_hold_cell` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `sample_en` (input, electrical)
    - position 4: `vhold` (output, electrical)
    - position 5: `held_valid` (output, electrical)
- Artifact `readout_mux.va`:
  - Module `readout_mux` (required_submodule)
    - position 0: `vh0` (input, electrical)
    - position 1: `vh1` (input, electrical)
    - position 2: `vh2` (input, electrical)
    - position 3: `valid0` (input, electrical)
    - position 4: `valid1` (input, electrical)
    - position 5: `valid2` (input, electrical)
    - position 6: `rst` (input, electrical)
    - position 7: `sel_1` (input, electrical)
    - position 8: `sel_0` (input, electrical)
    - position 9: `vout` (output, electrical)
    - position 10: `channel_metric` (output, electrical)
    - position 11: `valid` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `muxed_track_hold_array_top` as `XDUT` with ordered public binding: vin0=vin0, vin1=vin1, vin2=vin2, clk=clk, rst=rst, sel_1=sel_1, sel_0=sel_0, sample_en=sample_en, vout=vout, channel_metric=channel_metric, valid=valid.

## Public Parameter Contract

- `muxed_track_hold_array_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `muxed_track_hold_array_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `muxed_track_hold_array_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `muxed_track_hold_array_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `muxed_track_hold_array_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `track_hold_cell.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `track_hold_cell.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `track_hold_cell.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `track_hold_cell.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `track_hold_cell.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `readout_mux.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `readout_mux.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `readout_mux.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `readout_mux.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `readout_mux.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `readout_mux.tick` defaults to `400p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_CLEAR_ALL_HELD_CHANNEL`: exercise and make observable: On reset, clear all held channel states, output, channel metric, and `valid`. Required traces: `time`, `vin0`, `vin1`, `vin2`, `clk`, `rst`, `sel_1`, `sel_0`, `sample_en`, `vout`, `channel_metric`, `valid`.
- `P_ON_EACH_ENABLED_SAMPLING_CLOCK_EDGE`: exercise and make observable: On each enabled sampling clock edge, capture all three input channels into separate hold states. Required traces: `time`, `vin0`, `vin1`, `vin2`, `clk`, `rst`, `sel_1`, `sel_0`, `sample_en`, `vout`, `channel_metric`, `valid`.
- `P_DECODE_SEL_1_SEL_0_AND`: exercise and make observable: Decode `sel_1..sel_0` and route the selected held channel to `vout`; invalid code 3 must hold the previous output and clear `valid`. Required traces: `time`, `vin0`, `vin1`, `vin2`, `clk`, `rst`, `sel_1`, `sel_0`, `sample_en`, `vout`, `channel_metric`, `valid`.
- `P_EXPOSE_THE_SELECTED_CHANNEL_INDEX_ON`: exercise and make observable: Expose the selected channel index on `channel_metric` as a voltage-coded metric. Required traces: `time`, `vin0`, `vin1`, `vin2`, `clk`, `rst`, `sel_1`, `sel_0`, `sample_en`, `vout`, `channel_metric`, `valid`.
- `P_HOLD_ALL_CHANNEL_SAMPLES_BETWEEN_SAMPLING`: exercise and make observable: Hold all channel samples between sampling events. Required traces: `time`, `vin0`, `vin1`, `vin2`, `clk`, `rst`, `sel_1`, `sel_0`, `sample_en`, `vout`, `channel_metric`, `valid`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin0`, `vin1`, `vin2`, `clk`, `rst`, `sel_1`, `sel_0`, `sample_en`, `vout`, `channel_metric`, `valid`.

The required trace names are: `time`, `vin0`, `vin1`, `vin2`, `clk`, `rst`, `sel_1`, `sel_0`, `sample_en`, `vout`, `channel_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
