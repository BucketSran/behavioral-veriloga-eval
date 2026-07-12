# Latched Comparator Delay Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `latched_comparator_delay.va`:
  - Module `latched_comparator_delay` (entry)
    - position 0: `DOUT` (output, electrical)
    - position 1: `GND` (inout, electrical)
    - position 2: `VDD` (inout, electrical)
    - position 3: `CLK` (input, electrical)
    - position 4: `VINN` (input, electrical)
    - position 5: `VINP` (input, electrical)

## Public Parameter Contract

- `latched_comparator_delay.td` defaults to `1e-09` s; valid range: td >= 0; sets DOUT delay after a latch event.
- `latched_comparator_delay.tr` defaults to `1e-10` s; valid range: tr >= 0; sets DOUT transition smoothing.
- `latched_comparator_delay.vos` defaults to `0.0` V; valid range: finite real; sets deterministic input-referred decision offset.
- `latched_comparator_delay.vn` defaults to `0.001` V; valid range: vn >= 0; sets standard deviation of the input-referred random decision term; zero disables it.
- `latched_comparator_delay.seed_init` defaults to `0.0`; valid range: finite integer-valued real accepted as a random seed; initializes the repeatable random decision sequence.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SUPPLY_REFERENCED_THRESHOLD`: restore: The latch clock threshold is the midpoint of VDD and GND, and DOUT low and high levels use those same rails. Required traces: `time`, `vdd`, `clk`, `dout`.
- `P_RISING_EDGE_LATCH`: restore: Each rising CLK midpoint crossing latches one comparison result; falling crossings do not resample the input. Required traces: `time`, `vdd`, `clk`, `vinn`, `vinp`, `dout`.
- `P_OFFSET_DECISION`: restore: With vn zero, DOUT latches high exactly when VINP minus VINN exceeds vos and low otherwise. Required traces: `time`, `clk`, `vinn`, `vinp`, `dout`.
- `P_SEEDED_RANDOM_TERM`: restore: With vn nonzero, each latch decision includes a normal input-referred term scaled by vn from the sequence initialized by seed_init. Required traces: `time`, `clk`, `vinn`, `vinp`, `dout`.
- `P_INTEREDGE_HOLD`: restore: The latched decision holds between rising CLK events even if VINP or VINN changes. Required traces: `time`, `clk`, `vinn`, `vinp`, `dout`.
- `P_DELAY_AND_SMOOTHING`: restore: DOUT applies td delay and tr transition smoothing after each latch event. Required traces: `time`, `clk`, `dout`.

## Modeling Constraints

- Initialize rail references and the random seed at initial_step, then sample only on rising CLK midpoint crossings.
- Use seeded repeatable decision noise and a smoothed supply-referenced voltage contribution for DOUT.
- Do not use current contributions, ddt(), idt(), validation hooks, hard-coded waveform sample points, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `latched_comparator_delay.va`.
Every supplied `.va` file is editable; do not add or omit files.
