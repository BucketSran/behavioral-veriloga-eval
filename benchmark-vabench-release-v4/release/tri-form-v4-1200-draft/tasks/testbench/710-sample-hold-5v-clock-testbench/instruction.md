# Sample Hold 5v Clock Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Sample Hold 5v Clock` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `sample_hold_5v_clock.va`:
  - Module `sample_hold_5v_clock` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)
    - position 2: `vclk` (input, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `sample_hold_5v_clock` as `XDUT` with ordered public binding: vin=vin, vout=vout, vclk=vclk.

## Public Parameter Contract

- `sample_hold_5v_clock.vtrans_clk` defaults to `2.5`; valid range: finite; overrides vtrans_clk.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DETECT_RISING_CROSSINGS_OF_VCLK_THROUGH`: exercise and make observable: Detect rising crossings of `vclk` through `vtrans_clk`. At each qualifying edge, sample the instantaneous value of `vin` and hold that sampled value on `vout` until the next rising clock edge. Falling clock edges must not update the held value. Required traces: `time`, `vclk`, `vin`, `vout`.

The required trace names are: `time`, `vclk`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
