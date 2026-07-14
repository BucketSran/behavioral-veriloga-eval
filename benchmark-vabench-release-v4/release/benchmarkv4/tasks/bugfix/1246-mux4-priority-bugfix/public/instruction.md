# Mux4 Priority Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `mux4_priority.va`:
  - Module `mux4_priority` (entry)
    - position 0: `sel0` (input, electrical)
    - position 1: `sel1` (input, electrical)
    - position 2: `in0` (input, electrical)
    - position 3: `in1` (input, electrical)
    - position 4: `in2` (input, electrical)
    - position 5: `in3` (input, electrical)
    - position 6: `out` (output, electrical)

## Public Parameter Contract

- `mux4_priority.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DECODE_THE_SELECT_CODE_AS_SEL0`: restore: Decode the select code as `sel0 + 2*sel1`. For code `0`, forward `in0` to `out`; for code `1`, forward `in1`; for code `2`, forward `in2`; for code `3`, forward `in3`. The selected analog voltage should pass through without quantization or rail coding. Required traces: `time`, `in0`, `in1`, `in2`, `in3`, `out`, `sel0`, `sel1`.
- `P_PROVIDE_OVERRIDEABLE_PUBLIC_PARAMETER_VTH_0`: restore: Provide overrideable public parameter `vth = 0.45 V` as the decision threshold for `sel0` and `sel1`. Required traces: `time`, `in0`, `in1`, `in2`, `in3`, `out`, `sel0`, `sel1`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: restore: Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `in0`, `in1`, `in2`, `in3`, `out`, `sel0`, `sel1`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `mux4_priority.va`.
Every supplied `.va` file is editable; do not add or omit files.
