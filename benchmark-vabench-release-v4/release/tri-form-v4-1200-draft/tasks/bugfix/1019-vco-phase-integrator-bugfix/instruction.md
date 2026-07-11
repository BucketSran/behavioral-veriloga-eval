# VCO Phase Integrator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `vco_phase_integrator.va`:
  - Module `vco_phase_integrator` (entry)
    - position 0: `vctrl` (input, electrical)
    - position 1: `phase` (output, electrical)
    - position 2: `clk` (output, electrical)

## Public Parameter Contract

- `vco_phase_integrator.tr` defaults to `2e-10` s; valid range: tr > 0; sets phase and clock transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_PERIODIC_PHASE_UPDATE`: restore: Phase state updates on the public 1 ns periodic schedule by 0.03 plus 0.09 times vctrl. Required traces: `time`, `vctrl`, `phase`.
- `P_WRAPPED_PHASE_RANGE`: restore: The observable phase remains in the normalized range from 0 inclusive to 1 exclusive. Required traces: `time`, `phase`.
- `P_WRAP_TOGGLES_CLOCK`: restore: Each phase wrap by one cycle toggles the voltage-coded clock between 0 V and 0.9 V. Required traces: `time`, `phase`, `clk`.
- `P_CONTROLLED_EDGE_RATE`: restore: A sustained higher vctrl produces more clock toggles over the same observation interval than a sustained lower vctrl. Required traces: `time`, `vctrl`, `clk`.

## Modeling Constraints

- Use deterministic 1 ns timer-updated state and wrapped normalized phase.
- Use smoothed voltage contributions only.
- Do not use current contributions, ddt(), idt(), topology assumptions, validation hooks, or extra observability ports.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `vco_phase_integrator.va`.
Every supplied `.va` file is editable; do not add or omit files.
