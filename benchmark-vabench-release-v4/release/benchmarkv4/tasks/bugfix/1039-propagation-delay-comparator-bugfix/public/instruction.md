# Propagation Delay Comparator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cmp_delay.va`:
  - Module `cmp_delay` (entry)
    - position 0: `CLK` (input, electrical)
    - position 1: `VINN` (input, electrical)
    - position 2: `VINP` (input, electrical)
    - position 3: `DCMPN` (output, electrical)
    - position 4: `DCMPP` (output, electrical)
    - position 5: `LP` (output, electrical)
    - position 6: `LM` (output, electrical)
    - position 7: `VSS` (inout, electrical)
    - position 8: `VDD` (inout, electrical)
- Artifact `edge_interval_timer.va`:
  - Module `edge_interval_timer` (entry)
    - position 0: `CLK_1` (input, electrical)
    - position 1: `CLK_2` (input, electrical)
    - position 2: `OUT_PS` (output, electrical)

## Public Parameter Contract

- `cmp_delay.voffset` defaults to `0.0` V; valid range: finite real; subtracts an input-referred offset from VINP minus VINN.
- `cmp_delay.tau` defaults to `4.34e-12` s; valid range: tau > 0; sets the logarithmic regeneration-delay sensitivity.
- `cmp_delay.td_0` defaults to `2.05e-11` s; valid range: td_0 >= 0; sets the base clock-to-decision delay.
- `cmp_delay.td_min` defaults to `2e-11` s; valid range: 0 <= td_min <= td_max; sets the minimum scheduled decision delay.
- `cmp_delay.td_max` defaults to `2e-10` s; valid range: td_max >= td_min; sets the maximum scheduled decision delay.
- `edge_interval_timer.VTH` defaults to `0.4` V; valid range: VTH > 0; sets the rising-edge threshold for both timer inputs.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_DECISION`: restore: At each rising CLK crossing through half the VDD-to-VSS rail span, the comparator latches the sign of VINP minus VINN minus voffset into complementary DCMPP/DCMPN decisions, with LP mirroring DCMPP and LM mirroring DCMPN. Required traces: `time`, `clk`, `vinn`, `vinp`, `gnd`, `vdd`, `out_n`, `out_p`, `lp_int`, `lm_int`.
- `P_FALLING_RESET`: restore: Each falling CLK crossing resets both comparator decision outputs low. Required traces: `time`, `clk`, `out_n`, `out_p`.
- `P_DELAY_MAGNITUDE_TREND`: restore: For otherwise equal conditions, a smaller absolute effective differential input produces a longer clock-to-decision delay. Required traces: `time`, `clk`, `vinn`, `vinp`, `out_p`, `out_n`.
- `P_DELAY_CLAMP`: restore: The scheduled comparator decision delay follows the public log-linear regeneration relation and remains within td_min through td_max. Required traces: `time`, `clk`, `vinn`, `vinp`, `vdd`, `out_p`, `out_n`.
- `P_EDGE_INTERVAL_MEASUREMENT`: restore: After a rising CLK_1 crossing arms the timer, the next rising CLK_2 crossing updates OUT_PS to the elapsed interval expressed in picoseconds and holds that completed measurement. Required traces: `time`, `clk`, `out_p`, `delay_ps`.
- `P_BUNDLE_BINDING`: restore: The timing helper observes the comparator clock as CLK_1 and the positive comparator decision as CLK_2, exposing their measured interval on delay_ps. Required traces: `time`, `clk`, `out_p`, `delay_ps`.

## Modeling Constraints

- Keep both requested source files and both public module interfaces in one DUT bundle.
- Use voltage contributions and event-driven state; place driven contributions outside event blocks.
- Do not use current contributions, ddt(), idt(), hard-coded sample points, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cmp_delay.va`, `edge_interval_timer.va`.
Every supplied `.va` file is editable; do not add or omit files.
