# Bang-Bang Phase Detector Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Bang-Bang Phase Detector` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `bbpd_ref.va`:
  - Module `bbpd_ref` (entry)
    - position 0: `data` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `retimed_data` (input, electrical)
    - position 3: `up` (output, electrical)
    - position 4: `down` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `bbpd_ref` as `XDUT` with ordered public binding: data=data, clk=clk, retimed_data=retimed_data, up=up, down=down.

## Public Parameter Contract

- `bbpd_ref.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded output high level.
- `bbpd_ref.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the data, clock, and retimed-data decision threshold.
- `bbpd_ref.trf` defaults to `1e-11` s; valid range: trf > 0; sets output rise and fall smoothing.
- `bbpd_ref.td` defaults to `0.0` s; valid range: td >= 0; sets output transition delay.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DIRECTION`: exercise and make observable: Each data transition selects UP for clock-high/retimed-low, DOWN for clock-low/retimed-high, and neither otherwise. Required traces: `time`, `data`, `clk`, `retimed_data`, `up`, `down`.
- `P_MUTUAL_EXCLUSION`: exercise and make observable: UP and DOWN are never asserted simultaneously. Required traces: `time`, `up`, `down`.
- `P_PULSE_CLEAR`: exercise and make observable: An asserted correction output returns low after the next clock transition. Required traces: `time`, `clk`, `up`, `down`.
- `P_RAIL_LEVELS`: exercise and make observable: Asserted outputs approach vdd and inactive outputs approach 0 V with finite smoothing. Required traces: `time`, `up`, `down`.

The required trace names are: `time`, `data`, `clk`, `retimed_data`, `up`, `down`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
