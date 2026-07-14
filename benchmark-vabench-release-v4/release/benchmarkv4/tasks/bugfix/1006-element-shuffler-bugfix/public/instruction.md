# Element Shuffler Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `element_shuffler.va`:
  - Module `element_shuffler` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst_n` (input, electrical)
    - position 2: `out0` (output, electrical)
    - position 3: `out1` (output, electrical)
    - position 4: `out2` (output, electrical)
    - position 5: `out3` (output, electrical)

## Public Parameter Contract

- `element_shuffler.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets clk and rst_n decision threshold.
- `element_shuffler.vdd` defaults to `0.9` V; valid range: vdd > 0; sets active output high level.
- `element_shuffler.tr` defaults to `3e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_START`: restore: Active-low reset establishes the state so the first rising clk edge after release selects out2. Required traces: `time`, `clk`, `rst_n`, `out0`, `out1`, `out2`, `out3`.
- `P_PERMUTATION`: restore: Rising clk edges advance the repeating out2, out0, out3, out1 permutation. Required traces: `time`, `clk`, `rst_n`, `out0`, `out1`, `out2`, `out3`.
- `P_ONE_HOT`: restore: Exactly one output is high in every stable released-reset state. Required traces: `time`, `rst_n`, `out0`, `out1`, `out2`, `out3`.
- `P_RAIL_LEVELS`: restore: The selected output approaches vdd and all other outputs approach 0 V with finite smoothing. Required traces: `time`, `out0`, `out1`, `out2`, `out3`.

## Modeling Constraints

- Use deterministic voltage-domain behavior driven by clk and rst_n rather than absolute time.
- Use voltage contributions and finite transition smoothing only.
- Do not use current contributions, transistor devices, ddt(), idt(), AC/noise behavior, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `element_shuffler.va`.
Every supplied `.va` file is editable; do not add or omit files.
