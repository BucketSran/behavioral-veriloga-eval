# Divide By 8 9 Switch Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Divide By 8 9 Switch` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `divide_by_8_9_switch.va`:
  - Module `divide_by_8_9_switch` (entry)
    - position 0: `clkin` (input, electrical)
    - position 1: `mc` (input, electrical)
    - position 2: `out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `divide_by_8_9_switch` as `XDUT` with ordered public binding: clkin=clkin, mc=mc, out=out.

## Public Parameter Contract

- `divide_by_8_9_switch.tdel` defaults to `10p`; valid range: finite; overrides tdel.
- `divide_by_8_9_switch.tr` defaults to `10p`; valid range: finite; overrides tr.
- `divide_by_8_9_switch.tf` defaults to `10p`; valid range: finite; overrides tf.
- `divide_by_8_9_switch.vdd` defaults to `1.2`; valid range: finite; overrides vdd.
- `divide_by_8_9_switch.vth` defaults to `0.6`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_MODULUS_SWITCHING_ON_MC_EDGES`: exercise and make observable: `mc` crossings switch the divider between divide-by-8 and divide-by-9 operation and can restore divide-by-8 after divide-by-9. Required traces: `time`, `clkin`, `mc`, `out`.
- `P_DIVIDER_DUTY_WINDOW`: exercise and make observable: The divider output high window spans the specified count interval for the active modulus. Required traces: `time`, `clkin`, `mc`, `out`.
- `P_OUTPUT_RAIL_LEVEL`: exercise and make observable: `out` uses the declared high and low output levels without amplitude scaling. Required traces: `time`, `clkin`, `mc`, `out`.

The required trace names are: `time`, `clkin`, `mc`, `out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
