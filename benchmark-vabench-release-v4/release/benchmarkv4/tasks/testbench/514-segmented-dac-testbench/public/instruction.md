# Segmented DAC Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Segmented DAC` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `segmented_dac.va`:
  - Module `segmented_dac` (entry)
    - position 0: `b0` (input, electrical)
    - position 1: `b1` (input, electrical)
    - position 2: `t0` (input, electrical)
    - position 3: `t1` (input, electrical)
    - position 4: `t2` (input, electrical)
    - position 5: `vref` (input, electrical)
    - position 6: `vss` (input, electrical)
    - position 7: `aout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `segmented_dac` as `XDUT` with ordered public binding: b0=b0, b1=b1, t0=t0, t1=t1, t2=t2, vref=vref, vss=vss, aout=aout.

## Public Parameter Contract

- `segmented_dac.vth` defaults to `0.45` V; valid range: vth > 0; sets binary and thermometer control threshold.
- `segmented_dac.tr` defaults to `5e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SEGMENT_WEIGHTS`: exercise and make observable: b0 and b1 contribute one and two LSB steps while each active thermometer control contributes four LSB steps. Required traces: `time`, `b0`, `b1`, `t0`, `t1`, `t2`, `aout`.
- `P_CODE_MONOTONICITY`: exercise and make observable: Increasing the summed segmented code does not decrease aout. Required traces: `time`, `b0`, `b1`, `t0`, `t1`, `t2`, `aout`.
- `P_ENDPOINTS`: exercise and make observable: The zero code maps to vss and the all-active 15-step code maps to vref. Required traces: `time`, `b0`, `b1`, `t0`, `t1`, `t2`, `vref`, `vss`, `aout`.
- `P_RAIL_RELATIVE_MAPPING`: exercise and make observable: Intermediate codes linearly span the vss-to-vref range. Required traces: `time`, `b0`, `b1`, `t0`, `t1`, `t2`, `vref`, `vss`, `aout`.

The required trace names are: `time`, `b0`, `b1`, `t0`, `t1`, `t2`, `vref`, `vss`, `aout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
