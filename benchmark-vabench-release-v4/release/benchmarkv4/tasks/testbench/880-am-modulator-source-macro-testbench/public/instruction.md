# AM Modulator Source Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `AM Modulator Source Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `am_modulator_source_macro.va`:
  - Module `am_modulator_source_macro` (entry)
    - position 0: `carrier_in` (inout, electrical)
    - position 1: `mod_in` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `vout` (inout, electrical)
    - position 5: `envelope_dbg` (inout, electrical)
    - position 6: `valid` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `am_modulator_source_macro` as `XDUT` with ordered public binding: carrier_in=carrier_in, mod_in=mod_in, enable=enable, rst=rst, vout=vout, envelope_dbg=envelope_dbg, valid=valid.

## Public Parameter Contract

- `am_modulator_source_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `am_modulator_source_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `am_modulator_source_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `am_modulator_source_macro.mod_index` defaults to `0.5`; valid range: finite; overrides mod_index.
- `am_modulator_source_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `am_modulator_source_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive `vout` to `vcm`, clear `envelope_dbg`, and clear `valid`. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.
- `P_WHEN_ENABLED_TREAT_CARRIER_IN_AND`: exercise and make observable: When enabled, treat `carrier_in` and `mod_in` as deviations around `vcm`. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.
- `P_DRIVE_AN_AMPLITUDE_MODULATED_OUTPUT_WHOSE`: exercise and make observable: Drive an amplitude-modulated output whose carrier deviation increases when `mod_in` rises above `vcm` and decreases when it falls below `vcm`. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.
- `P_CLAMP_THE_ENVELOPE_MULTIPLIER_SO_THE`: exercise and make observable: Clamp the envelope multiplier so the output stays within `[vss, vdd]`. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.
- `P_ENVELOPE_DBG_MUST_EXPOSE_THE_ACTIVE`: exercise and make observable: `envelope_dbg` must expose the active voltage-domain envelope multiplier mapped into the output voltage range. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.
- `P_ASSERT_VALID_WHILE_ENABLED_AFTER_RESET`: exercise and make observable: Assert `valid` while enabled after reset has been released. Required traces: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.

The required trace names are: `time`, `carrier_in`, `mod_in`, `enable`, `rst`, `vout`, `envelope_dbg`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
