# FM/VCO Modulation Source Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `fm_vco_modulation_source.va`:
  - Module `fm_vco_modulation_source` (entry)
    - position 0: `mod_in` (inout, electrical)
    - position 1: `enable` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `osc_out` (inout, electrical)
    - position 4: `freq_metric` (inout, electrical)
    - position 5: `phase_marker` (inout, electrical)
    - position 6: `valid` (inout, electrical)

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

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `osc_out`, `freq_metric`, `phase_marker`, and `valid` low. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.
- `P_WHEN_ENABLED_GENERATE_A_DETERMINISTIC_BEHAVIOR`: restore: When enabled, generate a deterministic behavioral oscillator whose frequency increases monotonically with `mod_in`. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.
- `P_CLAMP_THE_COMMANDED_FREQUENCY_TO_A`: restore: Clamp the commanded frequency to a nonnegative range and expose the normalized command on `freq_metric`. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.
- `P_OSC_OUT_MUST_TOGGLE_BETWEEN_VSS`: restore: `osc_out` must toggle between `vss` and `vdd` according to the commanded oscillator state. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.
- `P_PHASE_MARKER_MUST_PULSE_OR_TOGGLE`: restore: `phase_marker` must pulse or toggle once per oscillator cycle so cycle period order is observable from public behavior. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.
- `P_ASSERT_VALID_AFTER_THE_FIRST_COMPLETED`: restore: Assert `valid` after the first completed oscillator cycle following enable. Required traces: `time`, `mod_in`, `enable`, `rst`, `osc_out`, `freq_metric`, `phase_marker`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `fm_vco_modulation_source.va`.
Every supplied `.va` file is editable; do not add or omit files.
