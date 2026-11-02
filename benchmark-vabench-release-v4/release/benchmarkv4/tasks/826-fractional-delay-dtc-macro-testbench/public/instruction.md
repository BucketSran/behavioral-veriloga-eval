# Fractional-delay DTC Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Fractional-delay DTC Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `fractional_delay_dtc_macro.va`:
  - Module `fractional_delay_dtc_macro` (entry)
    - position 0: `clk_in` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `frac_3` (inout, electrical)
    - position 4: `frac_2` (inout, electrical)
    - position 5: `frac_1` (inout, electrical)
    - position 6: `frac_0` (inout, electrical)
    - position 7: `clk_out` (inout, electrical)
    - position 8: `phase_metric` (inout, electrical)
    - position 9: `valid` (inout, electrical)

Stable public Spectre binding:

The submitted `testbench.scs` must use the supplied DUT through this public binding:

- Include path: `./dut/fractional_delay_dtc_macro.va`
- DUT instance: `XDUT (clk_in rst enable frac_3 frac_2 frac_1 frac_0 clk_out phase_metric valid) fractional_delay_dtc_macro`
- Required saved public traces: `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`
- Use one bounded transient analysis with a finite positive stop time.

You must design the stimulus yourself. Save traces as bare public signal names
(for example `clk`, not suffixed or hierarchical forms such as `clk:V` or
`XDUT.clk`). Do not redefine the DUT, drive DUT output nets, save
hierarchical/private nodes, or use checker/gold/internal files.

## Public Parameter Contract

- `fractional_delay_dtc_macro.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `fractional_delay_dtc_macro.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `fractional_delay_dtc_macro.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `fractional_delay_dtc_macro.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `fractional_delay_dtc_macro.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `fractional_delay_dtc_macro.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear output, phase metric, and `valid`. Required traces: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.
- `P_DECODE_FRAC_3_FRAC_0_AS`: exercise and make observable: Decode `frac_3..frac_0` as a fractional delay setting. Required traces: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.
- `P_FOR_EACH_INPUT_EDGE_EMIT_ONE`: exercise and make observable: For each input edge, emit one output edge with a delay proportional to the fractional code. Required traces: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.
- `P_EXPOSE_THE_FRACTIONAL_DELAY_AS_PHASE`: exercise and make observable: Expose the fractional delay as `phase_metric`. Required traces: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.
- `P_PRESERVE_INPUT_EDGE_ORDER_AND_ASSERT`: exercise and make observable: Preserve input-edge order and assert `valid` after the first emitted delayed edge. Required traces: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.


The following canonical public behavior is normative for this derived form:

- On reset or when disabled, clear output, phase metric, and `valid`.
- Decode `frac_3..frac_0` as a fractional delay setting.
- For each input edge, emit one output edge with a delay proportional to the fractional code.
- Expose the fractional delay as `phase_metric`.
- Preserve input-edge order and assert `valid` after the first emitted delayed edge.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.


The required trace names are: `time`, `clk_in`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `clk_out`, `phase_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.

- (vdd-vss)*code/15

- (code+1)*200ps
