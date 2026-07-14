# Single Shot Pulse Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Single Shot Pulse` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `source_single_shot.va`:
  - Module `source_single_shot` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `source_single_shot` as `XDUT` with ordered public binding: vin=vin, vout=vout.

## Public Parameter Contract

- `source_single_shot.pulse_width` defaults to `1e-08` s; valid range: pulse_width > 0; sets output high duration after a qualifying rising crossing.
- `source_single_shot.vlogic_high` defaults to `0.9` V; valid range: finite real; sets the asserted output level.
- `source_single_shot.vlogic_low` defaults to `0.0` V; valid range: finite real; sets the deasserted output level.
- `source_single_shot.vtrans` defaults to `0.45` V; valid range: finite real; sets the rising vin trigger threshold.
- `source_single_shot.tdel` defaults to `1e-09` s; valid range: tdel >= 0; sets output transition delay.
- `source_single_shot.trise` defaults to `2e-11` s; valid range: trise > 0; sets vout rise smoothing.
- `source_single_shot.tfall` defaults to `2e-11` s; valid range: tfall > 0; sets vout fall smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RISING_CROSS_TRIGGER`: exercise and make observable: Each qualifying rising vin crossing through vtrans initiates an output pulse. Required traces: `time`, `vin`, `vout`.
- `P_NO_FALLING_TRIGGER`: exercise and make observable: Falling vin crossings do not initiate pulses. Required traces: `time`, `vin`, `vout`.
- `P_PULSE_WIDTH`: exercise and make observable: After a qualifying trigger, the output target remains high for pulse_width before returning low. Required traces: `time`, `vin`, `vout`.
- `P_OUTPUT_LEVELS`: exercise and make observable: The deasserted and asserted targets are vlogic_low and vlogic_high respectively. Required traces: `time`, `vin`, `vout`.
- `P_REPEATABLE_ONE_SHOTS`: exercise and make observable: Distinct qualifying rising edges produce corresponding pulses and vout returns low between sufficiently separated events. Required traces: `time`, `vin`, `vout`.
- `P_TRANSITION_TIMING`: exercise and make observable: Output changes use tdel delay with trise and tfall smoothing without altering the logical pulse duration contract. Required traces: `time`, `vin`, `vout`.

The required trace names are: `time`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
