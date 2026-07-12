# Two Bit Counter Marker Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Two Bit Counter Marker` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `two_bit_counter_marker.va`:
  - Module `two_bit_counter_marker` (entry)
    - position 0: `CLKIN` (input, electrical)
    - position 1: `MC` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `two_bit_counter_marker` as `XDUT` with ordered public binding: CLKIN=clkin, MC=mc.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_LOW`: exercise and make observable: The timing/readout marker output initializes at 0.0 V before any counted edge. Required traces: `time`, `clkin`, `mc`.
- `P_RISING_EDGE_COUNT`: exercise and make observable: Only rising crossings of CLKIN through 0.5 V advance the internal modulo-four sequence. Required traces: `time`, `clkin`, `mc`.
- `P_WRAP_MARKER`: exercise and make observable: MC is driven to the 1.0 V marker level on the counted edge that wraps the sequence from count 3 to count 0. Required traces: `time`, `clkin`, `mc`.
- `P_NONWRAP_LOW`: exercise and make observable: MC is driven to 0.0 V on each of the other three counted edges in every four-edge cycle. Required traces: `time`, `clkin`, `mc`.
- `P_PERIOD_FOUR`: exercise and make observable: For a continuing valid clock, marker assertions repeat once per four rising threshold crossings. Required traces: `time`, `clkin`, `mc`.

The required trace names are: `time`, `clkin`, `mc`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
