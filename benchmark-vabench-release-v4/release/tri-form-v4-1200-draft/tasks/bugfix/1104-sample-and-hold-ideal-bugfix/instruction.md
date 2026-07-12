# Ideal Sample And Hold Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `source_sample_hold.va`:
  - Module `source_sample_hold` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)
    - position 2: `vclk` (input, electrical)

## Public Parameter Contract

- `source_sample_hold.vtrans_clk` defaults to `0.45` V; valid range: finite real; sets the rising vclk sampling threshold.
- `source_sample_hold.tr` defaults to `2e-11` s; valid range: tr >= 0; sets vout transition smoothing without changing the sampled value.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RISING_EDGE_CAPTURE`: restore: On each rising vclk crossing through vtrans_clk, vout captures the instantaneous vin value. Required traces: `time`, `vclk`, `vin`, `vout`.
- `P_INTEREDGE_HOLD`: restore: The captured value holds until the next rising sampling event even when vin changes. Required traces: `time`, `vclk`, `vin`, `vout`.
- `P_NO_FALLING_EDGE_CAPTURE`: restore: Falling vclk crossings do not update the held value. Required traces: `time`, `vclk`, `vin`, `vout`.
- `P_UNITY_SAMPLE_GAIN`: restore: The held target equals the sampled vin without gain, offset, quantization, or rail remapping. Required traces: `time`, `vclk`, `vin`, `vout`.
- `P_PARAMETERIZED_THRESHOLD`: restore: Legal vtrans_clk overrides move the sampling crossing threshold while preserving rising-edge capture and hold behavior. Required traces: `time`, `vclk`, `vin`, `vout`.

## Modeling Constraints

- Use rising-edge event-driven capture and persistent held state.
- Use a smoothed voltage contribution for vout.
- Do not use current contributions, transistor-level devices, ddt(), idt(), validation hooks, auxiliary test ports, or testbench-specific timing constants.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `source_sample_hold.va`.
Every supplied `.va` file is editable; do not add or omit files.
