# Rail Normalized Metric Mapper Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Rail Normalized Metric Mapper` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `rail_normalized_metric_mapper.va`:
  - Module `rail_normalized_metric_mapper` (entry)
    - position 0: `meas` (input, electrical)
    - position 1: `vdd` (input, electrical)
    - position 2: `vss` (input, electrical)
    - position 3: `en` (input, electrical)
    - position 4: `norm` (output, electrical)
    - position 5: `valid` (output, electrical)

Stable public Spectre binding:

The submitted `testbench.scs` must use the supplied DUT through this public binding:

- Include path: `./dut/rail_normalized_metric_mapper.va`
- DUT instance: `XDUT (meas vdd vss en norm valid) rail_normalized_metric_mapper`
- Required saved public traces: `en`, `meas`, `norm`, `valid`, `vdd`, `vss`
- Use one bounded transient analysis with a finite positive stop time.

You must design the stimulus yourself. Save traces as bare public signal names
(for example `clk`, not suffixed or hierarchical forms such as `clk:V` or
`XDUT.clk`). Do not redefine the DUT, drive DUT output nets, save
hierarchical/private nodes, or use checker/gold/internal files.

## Public Parameter Contract

- `rail_normalized_metric_mapper.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `rail_normalized_metric_mapper.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `rail_normalized_metric_mapper.span_min` defaults to `0.60`; valid range: finite; overrides span_min.
- `rail_normalized_metric_mapper.span_max` defaults to `1.20`; valid range: finite; overrides span_max.
- `rail_normalized_metric_mapper.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_NORMALIZE_MEAS_RELATIVE_TO_THE_LOCAL`: exercise and make observable: Normalize meas relative to the local V(vdd,vss) span and vss rail. Required traces: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.
- `P_CLIP_THE_NORMALIZED_METRIC_TO_THE`: exercise and make observable: Clip the normalized metric to the public voltage-coded range. Required traces: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.
- `P_ASSERT_VALID_ONLY_WHEN_ENABLE_IS`: exercise and make observable: Assert valid only when enable is high, supply span is valid, and the measurement lies inside the local rail window. Required traces: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.
- `P_CLEAR_NORM_AND_VALID_WHILE_DISABLED`: exercise and make observable: Clear norm and valid while disabled or under the minimum supply span. Required traces: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.
- `P_USE_LOCAL_ANALOG_HELPER_FUNCTIONS_RATHER`: exercise and make observable: Use local analog helper functions rather than user task/endtask syntax. Required traces: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.


The following canonical public behavior is normative for this derived form:

- `P_NORMALIZE_MEAS_RELATIVE_TO_THE_LOCAL`: Normalize meas relative to the local V(vdd,vss) span and vss rail.
- `P_CLIP_THE_NORMALIZED_METRIC_TO_THE`: Clip the normalized metric to the public voltage-coded range.
- `P_ASSERT_VALID_ONLY_WHEN_ENABLE_IS`: Assert valid only when enable is high, supply span is valid, and the measurement lies inside the local rail window.
- `P_CLEAR_NORM_AND_VALID_WHILE_DISABLED`: Clear norm and valid while disabled or under the minimum supply span.
- `P_USE_LOCAL_ANALOG_HELPER_FUNCTIONS_RATHER`: Use local analog helper functions rather than user task/endtask syntax.

The evaluator saves and may inspect these public trace signals: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.


The required trace names are: `time`, `en`, `meas`, `norm`, `valid`, `vdd`, `vss`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.

- local_meas = V(meas) - V(vss)

- norm = vhi * clip01(local_meas / span)

- span_min <= span <= span_max

- above `span_max`

- does not by itself clear clipped norm
