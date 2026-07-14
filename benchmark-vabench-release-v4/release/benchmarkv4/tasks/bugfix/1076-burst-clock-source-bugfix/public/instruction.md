# Burst Clock Source Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `clk_burst_gen.va`:
  - Module `clk_burst_gen` (entry)
    - position 0: `CLK` (input, electrical)
    - position 1: `RST_N` (input, electrical)
    - position 2: `CLK_OUT` (output, electrical)

## Public Parameter Contract

- `clk_burst_gen.div` defaults to `8` input-clock cycles; valid range: div >= 3; sets the number of input-clock cycles in each repeating burst frame.
- `clk_burst_gen.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded CLK_OUT high level.
- `clk_burst_gen.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the CLK and active-low reset decision threshold.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ACTIVE_LOW_RESET`: restore: While RST_N is below vth, CLK_OUT is low and the burst frame counter is restarted. Required traces: `time`, `CLK`, `RST_N`, `CLK_OUT`.
- `P_FRAME_START`: restore: After reset release, rising CLK crossings advance a repeating frame of div input-clock cycles beginning at position 0. Required traces: `time`, `CLK`, `RST_N`, `CLK_OUT`.
- `P_TWO_CYCLE_BURST`: restore: At frame positions 0 and 1, CLK_OUT passes the voltage-coded CLK waveform, including its high and low phases. Required traces: `time`, `CLK`, `RST_N`, `CLK_OUT`.
- `P_QUIET_REMAINDER`: restore: At frame positions 2 through div minus 1, CLK_OUT remains low regardless of CLK level. Required traces: `time`, `CLK`, `RST_N`, `CLK_OUT`.
- `P_FRAME_REPEAT`: restore: The two-cycle burst followed by the quiet remainder repeats every div rising CLK crossings. Required traces: `time`, `CLK`, `RST_N`, `CLK_OUT`.
- `P_OUTPUT_LEVELS`: restore: CLK_OUT uses 0 V and vdd as its voltage-coded low and high levels. Required traces: `time`, `CLK_OUT`.

## Modeling Constraints

- Use deterministic threshold-crossing event logic and voltage output contribution.
- Treat reset as active low and restart the frame deterministically.
- Do not add undeclared clocks, ports, or validation-only frame controls.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `clk_burst_gen.va`.
Every supplied `.va` file is editable; do not add or omit files.
