# Clocked Sample And Hold Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sample_hold.va`:
  - Module `sample_hold` (entry)
    - position 0: `VDD` (input, electrical)
    - position 1: `VSS` (input, electrical)
    - position 2: `IN` (input, electrical)
    - position 3: `CLK` (input, electrical)
    - position 4: `OUT` (output, electrical)

## Public Parameter Contract

- `sample_hold.vth` defaults to `0.45` V; valid range: finite real; sets the rising CLK sampling threshold.
- `sample_hold.tedge` defaults to `1e-10` s; valid range: tedge > 0; sets OUT transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RISING_EDGE_SAMPLE`: restore: OUT acquires the IN voltage present at each rising CLK crossing through vth, subject only to transition smoothing. Required traces: `time`, `in`, `clk`, `out`.
- `P_INTERSAMPLE_HOLD`: restore: OUT retains the most recently sampled value between rising CLK crossings. Required traces: `time`, `in`, `clk`, `out`.
- `P_NO_HIGH_PHASE_TRACKING`: restore: Changes on IN while CLK remains high do not make OUT transparent before the next rising crossing. Required traces: `time`, `in`, `clk`, `out`.
- `P_LOCAL_RAIL_REFERENCE`: restore: The held analog voltage is driven as a smooth voltage-domain output referenced to the local VDD and VSS rails. Required traces: `time`, `vdd`, `vss`, `in`, `out`.

## Modeling Constraints

- Use deterministic rising-edge sampled state and intersample hold.
- Use smoothed voltage contributions only.
- Do not use current contributions, ddt(), idt(), extra observability ports, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sample_hold.va`.
Every supplied `.va` file is editable; do not add or omit files.
