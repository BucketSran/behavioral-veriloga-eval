# Clock-and-data Valid Qualifier Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clock-and-data Valid Qualifier` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `clock_data_valid_qualifier.va`:
  - Module `clock_data_valid_qualifier` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `data` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `valid_out` (output, electrical)
    - position 5: `edge_age_metric` (output, electrical)
    - position 6: `qualified` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `clock_data_valid_qualifier` as `XDUT` with ordered public binding: clk=clk, data=data, rst=rst, enable=enable, valid_out=valid_out, edge_age_metric=edge_age_metric, qualified=qualified.

## Public Parameter Contract

- `clock_data_valid_qualifier.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `clock_data_valid_qualifier.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `clock_data_valid_qualifier.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `clock_data_valid_qualifier.max_age_cycles` defaults to `3` cycles; valid range: max_age_cycles >= 1; sets the inclusive qualification age limit.
- `clock_data_valid_qualifier.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_DISABLE_CLEAR`: exercise and make observable: Reset or disable clears valid, qualification, and the public age metric. Required traces: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.
- `P_DATA_EDGE_RESTART`: exercise and make observable: Either polarity data edge restarts the age count at zero while enabled. Required traces: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.
- `P_CLOCKED_AGE`: exercise and make observable: Each later rising clk edge increments age before qualification. Required traces: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.
- `P_INCLUSIVE_WINDOW`: exercise and make observable: Ages one through max_age_cycles are qualified and older ages are not. Required traces: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.
- `P_REGISTERED_METRIC`: exercise and make observable: valid_out is the registered qualified state and the metric reports saturated normalized age. Required traces: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.

The required trace names are: `time`, `clk`, `data`, `rst`, `enable`, `valid_out`, `edge_age_metric`, `qualified`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
