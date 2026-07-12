# VA Lx DAC Ideal 4b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `VA Lx DAC Ideal 4b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `va_lx_dac_ideal_4b.va`:
  - Module `va_lx_dac_ideal_4b` (entry)
    - position 0: `din1` (input, electrical)
    - position 1: `din2` (input, electrical)
    - position 2: `din3` (input, electrical)
    - position 3: `din4` (input, electrical)
    - position 4: `rdy` (input, electrical)
    - position 5: `aout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `va_lx_dac_ideal_4b` as `XDUT` with ordered public binding: din1=din1, din2=din2, din3=din3, din4=din4, rdy=rdy, aout=aout.

## Public Parameter Contract

- `va_lx_dac_ideal_4b.vdd` defaults to `1.8`; valid range: finite; overrides vdd.
- `va_lx_dac_ideal_4b.vth` defaults to `0.9`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_READY_CLOCKED_SAMPLING`: exercise and make observable: Only rising crossings of `rdy` through `vth` sample the four input bits; `aout` holds between ready events. Required traces: `time`, `rdy`, `din1`, `din2`, `din3`, `din4`, `aout`.
- `P_BINARY_BIT_ORDER`: exercise and make observable: `din4` is the MSB and `din1` is the LSB of the sampled 4-bit unipolar code. Required traces: `time`, `rdy`, `din1`, `din2`, `din3`, `din4`, `aout`.
- `P_VDD_SCALED_DAC_OUTPUT`: exercise and make observable: The sampled binary fraction is scaled by `vdd` and driven smoothly on `aout`. Required traces: `time`, `rdy`, `din1`, `din2`, `din3`, `din4`, `aout`.

The required trace names are: `time`, `din1`, `din2`, `din3`, `din4`, `rdy`, `aout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
