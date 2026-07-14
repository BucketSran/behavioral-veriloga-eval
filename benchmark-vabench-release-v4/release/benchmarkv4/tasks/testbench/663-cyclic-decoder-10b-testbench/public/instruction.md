# Cyclic Decoder 10b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Cyclic Decoder 10b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `cyclic_decoder_10b.va`:
  - Module `cyclic_decoder_10b` (entry)
    - position 0: `dp` (input, electrical)
    - position 1: `dn` (input, electrical)
    - position 2: `ready` (input, electrical)
    - position 3: `clks` (input, electrical)
    - position 4: `dout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cyclic_decoder_10b` as `XDUT` with ordered public binding: dp=dp, dn=dn, ready=ready, clks=clks, dout=dout.

## Public Parameter Contract

- `cyclic_decoder_10b.vth` defaults to `0.55`; valid range: finite; overrides vth.
- `cyclic_decoder_10b.nbit` defaults to `10`; valid range: finite; overrides nbit.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_READY_SERIAL_CAPTURE`: exercise and make observable: After each publication clock, rising `ready` crossings collect up to `nbit` serial decisions MSB first. Required traces: `time`, `clks`, `ready`, `dp`, `dn`, `dout`.
- `P_TERNARY_WEIGHTING`: exercise and make observable: For each collected decision, high `dp` adds the full current binary weight and low `dp` with high `dn` adds half of that weight. Required traces: `time`, `ready`, `dp`, `dn`, `dout`.
- `P_NORMALIZED_MIDSCALE_OUTPUT`: exercise and make observable: The decoded value is normalized by the public bit depth and shifted by the required midscale offset before driving `dout`. Required traces: `time`, `clks`, `ready`, `dout`.
- `P_CLOCKED_PUBLICATION_HOLD`: exercise and make observable: `dout` updates from event-driven ready/publication handling and holds between publication events. Required traces: `time`, `clks`, `ready`, `dout`.

The required trace names are: `time`, `dp`, `dn`, `ready`, `clks`, `dout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
