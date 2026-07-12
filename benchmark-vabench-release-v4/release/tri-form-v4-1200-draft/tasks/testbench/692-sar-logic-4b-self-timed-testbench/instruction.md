# SAR Logic 4b Self Timed Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `SAR Logic 4b Self Timed` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `sar_logic_4b_self_timed.va`:
  - Module `sar_logic_4b_self_timed` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `gnd` (input, electrical)
    - position 2: `clkc` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `dcmpp` (input, electrical)
    - position 5: `dcmpn` (input, electrical)
    - position 6: `cmpck` (output, electrical)
    - position 7: `dout1` (output, electrical)
    - position 8: `dout2` (output, electrical)
    - position 9: `dout3` (output, electrical)
    - position 10: `dout4` (output, electrical)
    - position 11: `dbotp1` (output, electrical)
    - position 12: `dbotp2` (output, electrical)
    - position 13: `dbotp3` (output, electrical)
    - position 14: `dbotn1` (output, electrical)
    - position 15: `dbotn2` (output, electrical)
    - position 16: `dbotn3` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `sar_logic_4b_self_timed` as `XDUT` with ordered public binding: vdd=vdd, gnd=gnd, clkc=clkc, rst=rst, dcmpp=dcmpp, dcmpn=dcmpn, cmpck=cmpck, dout1=dout1, dout2=dout2, dout3=dout3, dout4=dout4, dbotp1=dbotp1, dbotp2=dbotp2, dbotp3=dbotp3, dbotn1=dbotn1, dbotn2=dbotn2, dbotn3=dbotn3.

## Public Parameter Contract

- `sar_logic_4b_self_timed.t_logic_delay` defaults to `100p`; valid range: finite; overrides t_logic_delay.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_INITIALIZES_SELF_TIMED_STATE`: exercise and make observable: Initialization and rising `rst` reset the conversion step, clear `cmpck/dout`, and initialize DAC bottom-plate controls. Required traces: `time`, `clkc`, `cmpck`, `dbotn1`, `dbotn2`, `dbotn3`, `dbotp1`, `dbotp2`, `dbotp3`, `dcmpn`, `dcmpp`, `dout1`, `dout2`, `dout3`, `dout4`, `rst`, `vdd`, `gnd`.
- `P_COMPARATOR_PULSE_DECISION_POLARITY`: exercise and make observable: Rising `dcmpp` or `dcmpn` pulses store comparator decisions with the declared polarity. Required traces: `time`, `clkc`, `cmpck`, `dbotn1`, `dbotn2`, `dbotn3`, `dbotp1`, `dbotp2`, `dbotp3`, `dcmpn`, `dcmpp`, `dout1`, `dout2`, `dout3`, `dout4`, `rst`, `vdd`, `gnd`.
- `P_STEP_ADVANCE_ON_COMPARATOR_FALL`: exercise and make observable: Comparator-output falling events advance the SAR step and update the next control state. Required traces: `time`, `clkc`, `cmpck`, `dbotn1`, `dbotn2`, `dbotn3`, `dbotp1`, `dbotp2`, `dbotp3`, `dcmpn`, `dcmpp`, `dout1`, `dout2`, `dout3`, `dout4`, `rst`, `vdd`, `gnd`.
- `P_CMPCK_TIMING_AND_LEVEL`: exercise and make observable: `cmpck` is scheduled low after `t_logic_delay` and driven with valid voltage-coded levels. Required traces: `time`, `clkc`, `cmpck`, `dbotn1`, `dbotn2`, `dbotn3`, `dbotp1`, `dbotp2`, `dbotp3`, `dcmpn`, `dcmpp`, `dout1`, `dout2`, `dout3`, `dout4`, `rst`, `vdd`, `gnd`.

The required trace names are: `time`, `clkc`, `cmpck`, `dbotn1`, `dbotn2`, `dbotn3`, `dbotp1`, `dbotp2`, `dbotp3`, `dcmpn`, `dcmpp`, `dout1`, `dout2`, `dout3`, `dout4`, `rst`, `vdd`, `gnd`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
