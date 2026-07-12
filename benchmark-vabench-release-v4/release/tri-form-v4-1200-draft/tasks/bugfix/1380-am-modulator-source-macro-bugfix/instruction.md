# AM Modulator Source Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `am_modulator_source_macro.va`:
  - Module `am_modulator_source_macro` (entry)
    - position 0: `carrier_in` (inout, electrical)
    - position 1: `mod_in` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `vout` (inout, electrical)
    - position 5: `envelope_dbg` (inout, electrical)
    - position 6: `valid` (inout, electrical)

## Public Parameter Contract

- `am_modulator_source_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `am_modulator_source_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `am_modulator_source_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `am_modulator_source_macro.mod_index` defaults to `0.5`; valid range: finite; overrides mod_index.
- `am_modulator_source_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `am_modulator_source_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `vout` to `vcm`, clear `envelope_dbg`, and clear `valid`. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.
- `P_WHEN_ENABLED_TREAT_CARRIER_IN_AND`: restore: When enabled, treat `carrier_in` and `mod_in` as deviations around `vcm`. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.
- `P_DRIVE_AN_AMPLITUDE_MODULATED_OUTPUT_WHOSE`: restore: Drive an amplitude-modulated output whose carrier deviation increases when `mod_in` rises above `vcm` and decreases when it falls below `vcm`. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.
- `P_CLAMP_THE_ENVELOPE_MULTIPLIER_SO_THE`: restore: Clamp the envelope multiplier so the output stays within `[vss, vdd]`. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.
- `P_ENVELOPE_DBG_MUST_EXPOSE_THE_ACTIVE`: restore: `envelope_dbg` must expose the active voltage-domain envelope multiplier mapped into the output voltage range. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.
- `P_ASSERT_VALID_WHILE_ENABLED_AFTER_RESET`: restore: Assert `valid` while enabled after reset has been released. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `am_modulator_source_macro.va`.
Every supplied `.va` file is editable; do not add or omit files.
