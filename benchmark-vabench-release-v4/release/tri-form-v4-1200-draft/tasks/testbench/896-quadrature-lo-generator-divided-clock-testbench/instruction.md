# Quadrature LO Generator from Divided Clock Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Quadrature LO Generator from Divided Clock` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `quadrature_lo_generator_divided_clock.va`:
  - Module `quadrature_lo_generator_divided_clock` (entry)
    - position 0: `clk_in` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `lo_i` (output, electrical)
    - position 4: `lo_q` (output, electrical)
    - position 5: `div_metric` (output, electrical)
    - position 6: `quad_ok` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `quadrature_lo_generator_divided_clock` as `XDUT` with ordered public binding: clk_in=clk_in, rst=rst, enable=enable, lo_i=lo_i, lo_q=lo_q, div_metric=div_metric, quad_ok=quad_ok.

## Public Parameter Contract

- `quadrature_lo_generator_divided_clock.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `quadrature_lo_generator_divided_clock.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `quadrature_lo_generator_divided_clock.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `quadrature_lo_generator_divided_clock.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_DISABLE_CLEAR`: exercise and make observable: Reset or disable clears both LO outputs, state metric, and quad_ok. Required traces: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.
- `P_QUADRATURE_SEQUENCE`: exercise and make observable: Enabled rising input edges drive the repeating 10, 11, 01, 00 sequence. Required traces: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.
- `P_DIVIDE_BY_FOUR`: exercise and make observable: Each LO has one cycle per four input rising edges with equal frequency and deterministic quadrature order. Required traces: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.
- `P_STATE_METRIC`: exercise and make observable: div_metric reports the currently driven sequence index as k/3 of the output span. Required traces: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.
- `P_QUAD_OK_DELAY`: exercise and make observable: quad_ok asserts only after two complete four-state output cycles. Required traces: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.

The required trace names are: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
