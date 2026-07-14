# Frequency-word DCO with Divider Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `frequency_word_dco.va`:
  - Module `frequency_word_dco` (entry)
    - position 0: `enable` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `fcw_5` (input, electrical)
    - position 3: `fcw_4` (input, electrical)
    - position 4: `fcw_3` (input, electrical)
    - position 5: `fcw_2` (input, electrical)
    - position 6: `fcw_1` (input, electrical)
    - position 7: `fcw_0` (input, electrical)
    - position 8: `dco_clk` (output, electrical)
    - position 9: `div_clk` (output, electrical)
    - position 10: `freq_metric` (output, electrical)

## Public Parameter Contract

- `frequency_word_dco.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module frequency_word_dco.
- `frequency_word_dco.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module frequency_word_dco.
- `frequency_word_dco.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module frequency_word_dco.
- `frequency_word_dco.f_min` defaults to `80.0e6` Hz; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public f_min behavior for module frequency_word_dco.
- `frequency_word_dco.f_step` defaults to `2.0e6` Hz; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public f_step behavior for module frequency_word_dco.
- `frequency_word_dco.f_max` defaults to `250.0e6` Hz; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public f_max behavior for module frequency_word_dco.
- `frequency_word_dco.divide_ratio` defaults to `4 from [1:inf)`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public divide_ratio behavior for module frequency_word_dco.
- `frequency_word_dco.tr` defaults to `100p from (0:inf)` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module frequency_word_dco.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_STOP`: restore: Reset or disabled operation stops and clears both clocks, the divider counter, and the frequency metric. Required traces: `time`, `enable`, `rst`, `dco_clk`, `div_clk`, `freq_metric`.
- `P_FREQUENCY_WORD_MAPPING`: restore: The six-bit frequency word maps to min(f_max, f_min plus f_step times code), with the public normalized metric matching that target. Required traces: `time`, `fcw_5`, `fcw_4`, `fcw_3`, `fcw_2`, `fcw_1`, `fcw_0`, `dco_clk`, `freq_metric`.
- `P_DIVIDER_MONITOR`: restore: div_clk toggles once per divide_ratio rising DCO edges and its counter restarts after reset or disable. Required traces: `time`, `enable`, `rst`, `dco_clk`, `div_clk`.
- `P_RESTART_MONOTONICITY`: restore: Enable restarts both clocks low with the first DCO rise one half-period later, and larger frequency words produce nondecreasing edge counts. Required traces: `time`, `enable`, `rst`, `fcw_5`, `fcw_4`, `fcw_3`, `fcw_2`, `fcw_1`, `fcw_0`, `dco_clk`, `div_clk`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation.
- Use public voltage contributions only and preserve the declared artifact and module interfaces.
- Do not hard-code evaluator stimulus, sample windows, checker tolerances, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `frequency_word_dco.va`.
Every supplied `.va` file is editable; do not add or omit files.
