# L2 CDAC 4b Switch Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `L2 CDAC 4b Switch` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `l2_cdac_4b_switch.va`:
  - Module `l2_cdac_4b_switch` (entry)
    - position 0: `din1` (input, electrical)
    - position 1: `din2` (input, electrical)
    - position 2: `din3` (input, electrical)
    - position 3: `din4` (input, electrical)
    - position 4: `rdy` (input, electrical)
    - position 5: `aout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `l2_cdac_4b_switch` as `XDUT` with ordered public binding: din1=din1, din2=din2, din3=din3, din4=din4, rdy=rdy, aout=aout.

## Public Parameter Contract

- `l2_cdac_4b_switch.vdd` defaults to `1.1`; valid range: finite; overrides vdd.
- `l2_cdac_4b_switch.vth` defaults to `0.55`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_FIRST_READY_EDGE_ARMS_ONLY`: exercise and make observable: The first rising `rdy` edge arms the DAC and leaves the initialized output at zero. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `rdy`.
- `P_READY_SAMPLES_FOUR_BITS`: exercise and make observable: Each later rising `rdy` edge samples `din1..din4` against `vth` with the declared switched weights. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `rdy`.
- `P_SWITCHED_WEIGHT_DENOMINATOR`: exercise and make observable: Compute `switched_weight` and normalize by `8.5` before output scaling. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `rdy`.
- `P_BIPOLAR_CDAC_OUTPUT`: exercise and make observable: Map the sampled ratio to `(switched_weight / 8.5) * 2.0 * vdd - vdd` and hold it between ready edges. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `rdy`.

The required trace names are: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `rdy`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
