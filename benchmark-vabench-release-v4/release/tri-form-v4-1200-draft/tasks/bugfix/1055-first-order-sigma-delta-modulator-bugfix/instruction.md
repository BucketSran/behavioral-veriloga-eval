# First Order Sigma Delta Modulator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `first_order_sigma_delta_modulator.va`:
  - Module `first_order_sigma_delta_modulator` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vclk` (input, electrical)
    - position 2: `bitout` (output, electrical)

## Public Parameter Contract

- `first_order_sigma_delta_modulator.vth_clk` defaults to `0.45` V; valid range: vth_clk > 0; sets the rising-clock decision threshold.
- `first_order_sigma_delta_modulator.vh` defaults to `0.9` V; valid range: vh > 0; sets the one-bit output high level.
- `first_order_sigma_delta_modulator.vref` defaults to `1` V; valid range: vref > 0; sets the normalized one-bit feedback magnitude.
- `first_order_sigma_delta_modulator.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RISING_EDGE_UPDATE`: restore: The one-bit output state updates only from accumulator decisions made on rising crossings of vclk through vth_clk. Required traces: `time`, `vin`, `vclk`, `bitout`.
- `P_FIRST_ORDER_FEEDBACK`: restore: Each clocked decision reflects accumulation of the current normalized input minus the previous one-bit feedback state. Required traces: `time`, `vin`, `vclk`, `bitout`.
- `P_BINARY_OUTPUT`: restore: bitout is voltage-coded low near 0 V or high near vh with finite transition smoothing. Required traces: `time`, `vclk`, `bitout`.
- `P_INPUT_DENSITY_ORDER`: restore: Over a sufficiently long common observation interval, a larger constant vin produces a nondecreasing fraction of high output bits. Required traces: `time`, `vin`, `vclk`, `bitout`.
- `P_FEEDBACK_STABILITY`: restore: For an in-range constant input, the output stream continues to alternate as needed rather than running away as an open-loop accumulator. Required traces: `time`, `vin`, `vclk`, `bitout`.

## Modeling Constraints

- Use deterministic rising-edge accumulator updates and previous-bit feedback.
- Drive bitout with a smooth unconditional voltage contribution.
- Do not hard-code a public or private bit sequence, sample window, stimulus timing, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `first_order_sigma_delta_modulator.va`.
Every supplied `.va` file is editable; do not add or omit files.
