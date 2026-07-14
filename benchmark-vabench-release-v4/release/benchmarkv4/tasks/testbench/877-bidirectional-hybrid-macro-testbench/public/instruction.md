# Bidirectional Hybrid Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Bidirectional Hybrid Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `bidirectional_hybrid_macro.va`:
  - Module `bidirectional_hybrid_macro` (entry)
    - position 0: `port_a` (input, electrical)
    - position 1: `port_b` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `trim_2` (input, electrical)
    - position 5: `trim_1` (input, electrical)
    - position 6: `trim_0` (input, electrical)
    - position 7: `sum_out` (output, electrical)
    - position 8: `diff_out` (output, electrical)
    - position 9: `forward_metric` (output, electrical)
    - position 10: `reverse_metric` (output, electrical)
    - position 11: `balance_ok` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `bidirectional_hybrid_macro` as `XDUT` with ordered public binding: port_a=port_a, port_b=port_b, clk=clk, rst=rst, trim_2=trim_2, trim_1=trim_1, trim_0=trim_0, sum_out=sum_out, diff_out=diff_out, forward_metric=forward_metric, reverse_metric=reverse_metric, balance_ok=balance_ok.

## Public Parameter Contract

- `bidirectional_hybrid_macro.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `bidirectional_hybrid_macro.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `bidirectional_hybrid_macro.vcm` defaults to `0.45` V; valid range: vcm is finite and preserves the public operating range; overrides the public vcm behavior parameter consistently for this module.
- `bidirectional_hybrid_macro.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `bidirectional_hybrid_macro.trim_lsb` defaults to `0.01` V; valid range: trim_lsb is finite and preserves the public operating range; overrides the public trim_lsb behavior parameter consistently for this module.
- `bidirectional_hybrid_macro.balance_tol` defaults to `0.02` V; valid range: balance_tol is finite and preserves the public operating range; overrides the public balance_tol behavior parameter consistently for this module.
- `bidirectional_hybrid_macro.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_CLEAR`: exercise and make observable: Reset centers the continuous sum and difference outputs and clears sampled metrics and balance qualification. Required traces: `time`, `clk`, `rst`, `sum_out`, `diff_out`, `forward_metric`, `reverse_metric`, `balance_ok`.
- `P_SUM_DIFF_MAPPING`: exercise and make observable: sum_out and diff_out implement the clipped common and differential mappings of port_a and port_b around vcm. Required traces: `time`, `rst`, `port_a`, `port_b`, `trim_2`, `trim_1`, `trim_0`, `sum_out`, `diff_out`.
- `P_TRIM_RESPONSE`: exercise and make observable: The signed three-bit trim correction shifts sum and difference in opposite directions by trim_lsb per code. Required traces: `time`, `rst`, `trim_2`, `trim_1`, `trim_0`, `sum_out`, `diff_out`.
- `P_DIRECTIONAL_METRICS`: exercise and make observable: At rising clock edges forward and reverse metrics reconstruct the directional components from the mapped sum and difference outputs. Required traces: `time`, `clk`, `rst`, `sum_out`, `diff_out`, `forward_metric`, `reverse_metric`.
- `P_BALANCE_QUALIFICATION`: exercise and make observable: balance_ok asserts only after two consecutive metric updates whose directional mismatch is within balance_tol. Required traces: `time`, `clk`, `rst`, `forward_metric`, `reverse_metric`, `balance_ok`.

The required trace names are: `time`, `port_a`, `port_b`, `clk`, `rst`, `trim_2`, `trim_1`, `trim_0`, `sum_out`, `diff_out`, `forward_metric`, `reverse_metric`, `balance_ok`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
