# FM/VCO Modulation Source Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `FM/VCO Modulation Source Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `fm_vco_modulation_source.va`:
  - Module `fm_vco_modulation_source` (entry)
    - position 0: `mod_in` (inout, electrical)
    - position 1: `enable` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `osc_out` (inout, electrical)
    - position 4: `freq_metric` (inout, electrical)
    - position 5: `phase_marker` (inout, electrical)
    - position 6: `valid` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `fm_vco_modulation_source` as `XDUT` with ordered public binding: mod_in=mod_in, enable=enable, rst=rst, osc_out=osc_out, freq_metric=freq_metric, phase_marker=phase_marker, valid=valid.

## Public Parameter Contract

- `fm_vco_modulation_source.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `fm_vco_modulation_source.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `fm_vco_modulation_source.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `fm_vco_modulation_source.f0` defaults to `10e6`; valid range: finite; overrides f0.
- `fm_vco_modulation_source.kvco` defaults to `5e6`; valid range: finite; overrides kvco.
- `fm_vco_modulation_source.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `fm_vco_modulation_source.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `fm_vco_modulation_source.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive `osc_out`, `freq_metric`, `phase_marker`, and `valid` low. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.
- `P_WHEN_ENABLED_GENERATE_A_DETERMINISTIC_BEHAVIOR`: exercise and make observable: When enabled, generate a deterministic behavioral oscillator whose frequency increases monotonically with `mod_in`. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.
- `P_CLAMP_THE_COMMANDED_FREQUENCY_TO_A`: exercise and make observable: Clamp the commanded frequency to a nonnegative range and expose the normalized command on `freq_metric`. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.
- `P_OSC_OUT_MUST_TOGGLE_BETWEEN_VSS`: exercise and make observable: `osc_out` must toggle between `vss` and `vdd` according to the commanded oscillator state. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.
- `P_PHASE_MARKER_MUST_PULSE_OR_TOGGLE`: exercise and make observable: `phase_marker` must pulse or toggle once per oscillator cycle so cycle period order is observable from public behavior. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.
- `P_ASSERT_VALID_AFTER_THE_FIRST_COMPLETED`: exercise and make observable: Assert `valid` after the first completed oscillator cycle following enable. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.

The required trace names are: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
