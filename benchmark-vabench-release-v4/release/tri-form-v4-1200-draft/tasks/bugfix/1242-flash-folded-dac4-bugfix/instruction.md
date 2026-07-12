# Flash Folded DAC4 Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `flash_folded_dac4.va`:
  - Module `flash_folded_dac4` (entry)
    - position 0: `vd4` (input, electrical)
    - position 1: `vd3` (input, electrical)
    - position 2: `vd2` (input, electrical)
    - position 3: `vd1` (input, electrical)
    - position 4: `vout` (output, electrical)

## Public Parameter Contract

- `flash_folded_dac4.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `flash_folded_dac4.vref` defaults to `1.0`; valid range: finite; overrides vref.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_TREAT_EACH_INPUT_BIT_AS_LOGIC`: restore: Treat each input bit as logic one when its voltage is above `vth`. The MSB selects the folded half of the transfer. When `vd4` is high, add the lower-bit weighted value above midscale. When `vd4` is low, subtract the lower-bit weighted value from midscale. The lower bits use binary weights `4`, `2`, and `1`, and the output is scaled by `vref/16`. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.
- `P_VTH_0_45_V_DECISION_THRESHOLD`: restore: `vth = 0.45 V`: decision threshold for each voltage-coded input bit. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.
- `P_VREF_1_0_V_OUTPUT_REFERENCE`: restore: `vref = 1.0 V`: output reference/full-scale voltage. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.
- `P_VTH_0_45_V_DECISION_THRESHOLD_2`: restore: - `vth = 0.45 V`: decision threshold for each voltage-coded input bit. - `vref = 1.0 V`: output reference/full-scale voltage. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: restore: Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `vd1`, `vd2`, `vd3`, `vd4`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `flash_folded_dac4.va`.
Every supplied `.va` file is editable; do not add or omit files.
