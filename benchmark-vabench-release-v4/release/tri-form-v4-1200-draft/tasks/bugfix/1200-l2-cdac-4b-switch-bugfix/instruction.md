# L2 CDAC 4b Switch Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `l2_cdac_4b_switch.va`:
  - Module `l2_cdac_4b_switch` (entry)
    - position 0: `din1` (input, electrical)
    - position 1: `din2` (input, electrical)
    - position 2: `din3` (input, electrical)
    - position 3: `din4` (input, electrical)
    - position 4: `rdy` (input, electrical)
    - position 5: `aout` (output, electrical)

## Public Parameter Contract

- `l2_cdac_4b_switch.vdd` defaults to `1.1`; valid range: finite; overrides vdd.
- `l2_cdac_4b_switch.vth` defaults to `0.55`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FIRST_READY_EDGE_ARMS_ONLY`: restore: The first rising `rdy` edge arms the DAC and leaves the initialized output at zero. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `rdy`.
- `P_READY_SAMPLES_FOUR_BITS`: restore: Each later rising `rdy` edge samples `din1..din4` against `vth` with the declared switched weights. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `rdy`.
- `P_SWITCHED_WEIGHT_DENOMINATOR`: restore: Compute `switched_weight` and normalize by `8.5` before output scaling. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `rdy`.
- `P_BIPOLAR_CDAC_OUTPUT`: restore: Map the sampled ratio to `(switched_weight / 8.5) * 2.0 * vdd - vdd` and hold it between ready edges. Required traces: `time`, `aout`, `din1`, `din2`, `din3`, `din4`, `rdy`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `l2_cdac_4b_switch.va`.
Every supplied `.va` file is editable; do not add or omit files.
