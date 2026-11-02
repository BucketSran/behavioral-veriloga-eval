# Programmable Clock Skew Aligner Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Programmable Clock Skew Aligner` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `programmable_clock_skew_aligner.va`:
  - Module `programmable_clock_skew_aligner` (entry)
    - position 0: `clk_in` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `skew_2` (inout, electrical)
    - position 4: `skew_1` (inout, electrical)
    - position 5: `skew_0` (inout, electrical)
    - position 6: `clk_out` (inout, electrical)
    - position 7: `delay_metric` (inout, electrical)
    - position 8: `valid` (inout, electrical)

Stable public Spectre binding:

The submitted `testbench.scs` must use the supplied DUT through this public binding:

- Include path: `./dut/programmable_clock_skew_aligner.va`
- DUT instance: `XDUT (clk_in rst enable skew_2 skew_1 skew_0 clk_out delay_metric valid) programmable_clock_skew_aligner`
- Required saved public traces: `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`
- Use one bounded transient analysis with a finite positive stop time.

You must design the stimulus yourself. Save traces as bare public signal names
(for example `clk`, not suffixed or hierarchical forms such as `clk:V` or
`XDUT.clk`). Do not redefine the DUT, drive DUT output nets, save
hierarchical/private nodes, or use checker/gold/internal files.

## Public Parameter Contract

- `programmable_clock_skew_aligner.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `programmable_clock_skew_aligner.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `programmable_clock_skew_aligner.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `programmable_clock_skew_aligner.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `programmable_clock_skew_aligner.unit_delay_metric` defaults to `0.1`; valid range: finite; overrides unit_delay_metric.
- `programmable_clock_skew_aligner.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive output and metrics low. Required traces: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.
- `P_DECODE_SKEW_2_SKEW_0_AS`: exercise and make observable: Decode `skew_2..skew_0` as a programmable output-edge delay code. Required traces: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.
- `P_FOR_EACH_ACCEPTED_INPUT_CLOCK_EDGE`: exercise and make observable: For each accepted input clock edge, schedule one output edge after the code-dependent delay. Required traces: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.
- `P_EXPOSE_THE_ACTIVE_DELAY_CODE_AS`: exercise and make observable: Expose the active delay code as `delay_metric`. Required traces: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.
- `P_ASSERT_VALID_AFTER_THE_FIRST_DELAYED`: exercise and make observable: Assert `valid` after the first delayed output edge has been generated. Required traces: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.


The following canonical public behavior is normative for this derived form:

- On reset or when disabled, drive output and metrics low.
- Decode `skew_2..skew_0` as a programmable output-edge delay code.
- For each accepted input clock edge, schedule one output edge after the code-dependent delay.
- Expose the active delay code as `delay_metric`.
- Assert `valid` after the first delayed output edge has been generated.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.


The required trace names are: `time`, `clk_in`, `rst`, `enable`, `skew_2`, `skew_1`, `skew_0`, `clk_out`, `delay_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.

- (code+1)*200ps

- code*200ps

- code*unit_delay_metric
