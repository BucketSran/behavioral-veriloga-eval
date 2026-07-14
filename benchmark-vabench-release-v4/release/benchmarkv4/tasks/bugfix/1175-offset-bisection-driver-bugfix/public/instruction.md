# Offset Bisection Driver Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `offset_bisection_driver.va`:
  - Module `offset_bisection_driver` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `vout` (input, electrical)
    - position 2: `vcm` (input, electrical)
    - position 3: `vinp` (output, electrical)
    - position 4: `vinn` (output, electrical)

## Public Parameter Contract

- `offset_bisection_driver.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `offset_bisection_driver.step_initial` defaults to `10m`; valid range: finite; overrides step_initial.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_BISECTION_INITIAL_STATE`: restore: The differential residue initializes to zero, the step initializes to `step_initial`, and the previous decision polarity initializes to the low-decision direction. Required traces: `time`, `clk`, `vout`, `vcm`, `vinp`, `vinn`.
- `P_FALLING_CLOCK_DECISION_UPDATE`: restore: On each falling `clk` crossing, sample `vout` and update the residue using the specified comparator polarity. Required traces: `time`, `clk`, `vout`, `vinp`, `vinn`.
- `P_SIGN_CHANGE_STEP_HALVING`: restore: The bisection step halves when the sampled decision polarity changes. Required traces: `time`, `clk`, `vout`, `vinp`, `vinn`.
- `P_VCM_CENTERED_DIFFERENTIAL_DRIVE`: restore: `vinp` and `vinn` remain centered around `vcm` with half of the differential residue on each side. Required traces: `time`, `vcm`, `vinp`, `vinn`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `offset_bisection_driver.va`.
Every supplied `.va` file is editable; do not add or omit files.
