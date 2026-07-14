# Cyclic Decoder 10b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cyclic_decoder_10b.va`:
  - Module `cyclic_decoder_10b` (entry)
    - position 0: `dp` (input, electrical)
    - position 1: `dn` (input, electrical)
    - position 2: `ready` (input, electrical)
    - position 3: `clks` (input, electrical)
    - position 4: `dout` (output, electrical)

## Public Parameter Contract

- `cyclic_decoder_10b.vth` defaults to `0.55`; valid range: finite; overrides vth.
- `cyclic_decoder_10b.nbit` defaults to `10`; valid range: finite; overrides nbit.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_READY_SERIAL_CAPTURE`: restore: After each publication clock, rising `ready` crossings collect up to `nbit` serial decisions MSB first. Required traces: `time`, `clks`, `ready`, `dp`, `dn`, `dout`.
- `P_TERNARY_WEIGHTING`: restore: For each collected decision, high `dp` adds the full current binary weight and low `dp` with high `dn` adds half of that weight. Required traces: `time`, `ready`, `dp`, `dn`, `dout`.
- `P_NORMALIZED_MIDSCALE_OUTPUT`: restore: The decoded value is normalized by the public bit depth and shifted by the required midscale offset before driving `dout`. Required traces: `time`, `clks`, `ready`, `dout`.
- `P_CLOCKED_PUBLICATION_HOLD`: restore: `dout` updates from event-driven ready/publication handling and holds between publication events. Required traces: `time`, `clks`, `ready`, `dout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cyclic_decoder_10b.va`.
Every supplied `.va` file is editable; do not add or omit files.
