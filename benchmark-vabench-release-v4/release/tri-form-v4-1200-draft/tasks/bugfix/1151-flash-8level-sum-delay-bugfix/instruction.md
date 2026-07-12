# Flash 8level Sum Delay Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `flash_8level_sum_delay.va`:
  - Module `flash_8level_sum_delay` (entry)
    - position 0: `vip` (input, electrical)
    - position 1: `vim` (input, electrical)
    - position 2: `clks` (input, electrical)
    - position 3: `reset` (input, electrical)
    - position 4: `refp` (input, electrical)
    - position 5: `refn` (input, electrical)
    - position 6: `doutsum` (output, electrical)
    - position 7: `doutsumdelay` (output, electrical)

## Public Parameter Contract

- `flash_8level_sum_delay.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `flash_8level_sum_delay.ref_scaling` defaults to `0.5`; valid range: finite; overrides ref_scaling.
- `flash_8level_sum_delay.tt` defaults to `10p`; valid range: finite; overrides tt.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_FLASH_THRESHOLD_SUM`: restore: Each rising `clks` crossing compares `V(vip,vim)` against the symmetric flash thresholds and updates `doutsum`. Required traces: `time`, `clks`, `doutsum`, `doutsumdelay`, `refn`, `refp`, `reset`, `vim`, `vip`.
- `P_REFERENCE_SCALING`: restore: The flash thresholds use `V(refp)-V(refn)` multiplied by `ref_scaling`. Required traces: `time`, `clks`, `doutsum`, `doutsumdelay`, `refn`, `refp`, `reset`, `vim`, `vip`.
- `P_ONE_CYCLE_DELAYED_SUM`: restore: `doutsumdelay` reports the previous sampled flash summary, not the current summary. Required traces: `time`, `clks`, `doutsum`, `doutsumdelay`, `refn`, `refp`, `reset`, `vim`, `vip`.
- `P_NORMALIZED_OUTPUT`: restore: The flash summary is normalized by the eight-level count before being driven. Required traces: `time`, `clks`, `doutsum`, `doutsumdelay`, `refn`, `refp`, `reset`, `vim`, `vip`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `flash_8level_sum_delay.va`.
Every supplied `.va` file is editable; do not add or omit files.
