# Iterative ISAR DAC Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `iterative_isar_dac.va`:
  - Module `iterative_isar_dac` (entry)
    - position 0: `dcmp` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `vdac` (output, electrical)

## Public Parameter Contract

- `iterative_isar_dac.vth` defaults to `0.5`; valid range: finite; overrides vth.
- `iterative_isar_dac.tr` defaults to `100p`; valid range: finite; overrides tr.
- `iterative_isar_dac.range` defaults to `0.1`; valid range: finite; overrides range.
- `iterative_isar_dac.lsb` defaults to `10u`; valid range: finite; overrides lsb.
- `iterative_isar_dac.radix` defaults to `2`; valid range: finite; overrides radix.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_INITIAL_SEARCH_STATE`: restore: At initialization and reset, `vdac` returns to zero and the search step returns to `range`. Required traces: `time`, `rst`, `vdac`.
- `P_COMPARATOR_POLARITY_UPDATE`: restore: On each rising `clk` crossing while active, `dcmp > vth` steps `vdac` in the specified comparator-driven direction and low decisions step the opposite way. Required traces: `time`, `clk`, `dcmp`, `vdac`.
- `P_RADIX_STEP_REDUCTION`: restore: The search step is divided by the public radix after each active comparison until it reaches the LSB limit. Required traces: `time`, `clk`, `dcmp`, `rst`, `vdac`.
- `P_HELD_DAC_OUTPUT`: restore: `vdac` holds the current iterative search value between reset and qualifying clock events. Required traces: `time`, `clk`, `rst`, `vdac`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `iterative_isar_dac.va`.
Every supplied `.va` file is editable; do not add or omit files.
