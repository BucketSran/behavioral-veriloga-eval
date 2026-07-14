# Latched Bus DAC8 Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `latched_bus_dac8.va`:
  - Module `latched_bus_dac8` (entry)
    - position 0: `vclk` (input, electrical)
    - position 1: `b7` (input, electrical)
    - position 2: `b6` (input, electrical)
    - position 3: `b5` (input, electrical)
    - position 4: `b4` (input, electrical)
    - position 5: `b3` (input, electrical)
    - position 6: `b2` (input, electrical)
    - position 7: `b1` (input, electrical)
    - position 8: `b0` (input, electrical)
    - position 9: `vout` (output, electrical)

## Public Parameter Contract

- `latched_bus_dac8.vth` defaults to `0.45` V; valid range: vth > 0; sets the rising-edge and input-bit decision threshold.
- `latched_bus_dac8.vref` defaults to `1` V; valid range: vref > 0; sets the full-scale analog endpoint.
- `latched_bus_dac8.tr` defaults to `2e-11` s; valid range: tr > 0; sets analog output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RISING_EDGE_CAPTURE`: restore: Each rising crossing of vclk through vth captures the unsigned value of b[7:0]. Required traces: `time`, `vclk`, `b7`, `b6`, `b5`, `b4`, `b3`, `b2`, `b1`, `b0`, `vout`.
- `P_HOLD_BETWEEN_EDGES`: restore: vout retains the value from the most recent rising clock crossing despite input-bus changes between update edges. Required traces: `time`, `vclk`, `b7`, `b6`, `b5`, `b4`, `b3`, `b2`, `b1`, `b0`, `vout`.
- `P_ENDPOINTS`: restore: Latched code 0 maps to 0 V and latched code 255 maps to vref. Required traces: `time`, `vclk`, `b7`, `b6`, `b5`, `b4`, `b3`, `b2`, `b1`, `b0`, `vout`.
- `P_BINARY_MONOTONICITY`: restore: Increasing the latched unsigned code never decreases vout, with b7 as MSB and b0 as LSB. Required traces: `time`, `vclk`, `b7`, `b6`, `b5`, `b4`, `b3`, `b2`, `b1`, `b0`, `vout`.
- `P_OUTPUT_SMOOTHING`: restore: vout approaches each newly latched target with finite transition smoothing set by tr. Required traces: `time`, `vclk`, `vout`.

## Modeling Constraints

- Use deterministic rising-edge state updates and unconditional voltage output contribution.
- Preserve the public binary bit order and latch behavior.
- Do not make the DAC transparent between clock edges or add undeclared artifacts, validation hooks, current contributions, ddt(), or idt().
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `latched_bus_dac8.va`.
Every supplied `.va` file is editable; do not add or omit files.
