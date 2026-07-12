# Subradix DAC10 Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `subradix_dac10.va`:
  - Module `subradix_dac10` (entry)
    - position 0: `vd9` (input, electrical)
    - position 1: `vd8` (input, electrical)
    - position 2: `vd7` (input, electrical)
    - position 3: `vd6` (input, electrical)
    - position 4: `vd5` (input, electrical)
    - position 5: `vd4` (input, electrical)
    - position 6: `vd3` (input, electrical)
    - position 7: `vd2` (input, electrical)
    - position 8: `vd1` (input, electrical)
    - position 9: `vd0` (input, electrical)
    - position 10: `vout` (output, electrical)

## Public Parameter Contract

- `subradix_dac10.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `subradix_dac10.vref` defaults to `1.0`; valid range: finite; overrides vref.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_TREAT_EACH_INPUT_AS_LOGIC_ONE`: restore: Treat each input as logic one when its voltage is greater than `vth`. Decode `vd9..vd0` as a sub-radix word whose adjacent bit weights follow radix `1.8`, with `vd0` weight one and `vd9` weight `1.8^9`. Scale the active-weight sum by the all-ones sub-radix weight sum so that all ones maps to `vref`. Required traces: `time`, `vd0`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vd7`, `vd8`, `vd9`, `vout`.
- `P_VTH_0_45_V_DECISION_THRESHOLD`: restore: `vth = 0.45 V`: decision threshold for each input bit. Required traces: `time`, `vd0`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vd7`, `vd8`, `vd9`, `vout`.
- `P_VREF_1_0_V_OUTPUT_FULL`: restore: `vref = 1.0 V`: output full-scale/reference voltage. Required traces: `time`, `vd0`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vd7`, `vd8`, `vd9`, `vout`.
- `P_VTH_0_45_V_DECISION_THRESHOLD_2`: restore: - `vth = 0.45 V`: decision threshold for each input bit. - `vref = 1.0 V`: output full-scale/reference voltage. Required traces: `time`, `vd0`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vd7`, `vd8`, `vd9`, `vout`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: restore: Use deterministic voltage-domain Verilog-A and voltage contributions only. It is acceptable to express sub-radix weights with portable real arithmetic such as `pow(1.8, k)`. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `vd0`, `vd1`, `vd2`, `vd3`, `vd4`, `vd5`, `vd6`, `vd7`, `vd8`, `vd9`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `subradix_dac10.va`.
Every supplied `.va` file is editable; do not add or omit files.
