# LT Readout SAR4 Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `LT Readout SAR4` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `lt_readout_sar4.va`:
  - Module `lt_readout_sar4` (entry)
    - position 0: `d0` (input, electrical)
    - position 1: `d1` (input, electrical)
    - position 2: `d2` (input, electrical)
    - position 3: `d3` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `gnd` (input, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `lt_readout_sar4` as `XDUT` with ordered public binding: d0=d0, d1=d1, d2=d2, d3=d3, vout=vout, gnd=gnd.

## Public Parameter Contract

- `lt_readout_sar4.vth` defaults to `0.9`; valid range: finite; overrides vth.
- `lt_readout_sar4.vref` defaults to `1.8`; valid range: finite; overrides vref.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CONTINUOUSLY_DECODE_D0_D3_AS_AN`: exercise and make observable: Continuously decode `d0..d3` as an unsigned binary code with `d0` as LSB and `d3` as MSB. Drive `vout` to the readout level `code * vref / 16`. The output should update when the voltage-coded input bits cross the threshold. Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `gnd`, `vout`.

The required trace names are: `time`, `d0`, `d1`, `d2`, `d3`, `gnd`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
