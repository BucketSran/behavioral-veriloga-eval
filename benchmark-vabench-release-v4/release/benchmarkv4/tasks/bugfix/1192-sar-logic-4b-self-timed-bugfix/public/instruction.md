# SAR Logic 4b Self Timed Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

## Public Parameter Contract

- `sar_logic_4b_self_timed.t_logic_delay` defaults to `100p`; valid range: finite; overrides t_logic_delay.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_INITIALIZES_SELF_TIMED_STATE`: restore: Initialization and rising `rst` reset the conversion step, clear `cmpck/dout`, and initialize DAC bottom-plate controls. Required traces: `time`, `clkc`, `cmpck`, `dbotn1`, `dbotn2`, `dbotn3`, `dbotp1`, `dbotp2`, `dbotp3`, `dcmpn`, `dcmpp`, `dout1`, `dout2`, `dout3`, `dout4`, `rst`, `vdd`, `gnd`.
- `P_COMPARATOR_PULSE_DECISION_POLARITY`: restore: Rising `dcmpp` or `dcmpn` pulses store comparator decisions with the declared polarity. Required traces: `time`, `clkc`, `cmpck`, `dbotn1`, `dbotn2`, `dbotn3`, `dbotp1`, `dbotp2`, `dbotp3`, `dcmpn`, `dcmpp`, `dout1`, `dout2`, `dout3`, `dout4`, `rst`, `vdd`, `gnd`.
- `P_STEP_ADVANCE_ON_COMPARATOR_FALL`: restore: Comparator-output falling events advance the SAR step and update the next control state. Required traces: `time`, `clkc`, `cmpck`, `dbotn1`, `dbotn2`, `dbotn3`, `dbotp1`, `dbotp2`, `dbotp3`, `dcmpn`, `dcmpp`, `dout1`, `dout2`, `dout3`, `dout4`, `rst`, `vdd`, `gnd`.
- `P_CMPCK_TIMING_AND_LEVEL`: restore: `cmpck` is scheduled low after `t_logic_delay` and driven with valid voltage-coded levels. Required traces: `time`, `clkc`, `cmpck`, `dbotn1`, `dbotn2`, `dbotn3`, `dbotp1`, `dbotp2`, `dbotp3`, `dcmpn`, `dcmpp`, `dout1`, `dout2`, `dout3`, `dout4`, `rst`, `vdd`, `gnd`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sar_logic_4b_self_timed.va`.
Every supplied `.va` file is editable; do not add or omit files.
