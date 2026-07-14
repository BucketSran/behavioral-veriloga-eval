# Lock Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `lock_detector.va`:
  - Module `lock_detector` (entry)
    - position 0: `ref_clk` (input, electrical)
    - position 1: `fb_clk` (input, electrical)
    - position 2: `rst_n` (input, electrical)
    - position 3: `lock` (output, electrical)

## Public Parameter Contract

- `lock_detector.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets input logic thresholds.
- `lock_detector.vdd` defaults to `0.9` V; valid range: vdd > 0; sets lock high level.
- `lock_detector.tol` defaults to `2e-09` s; valid range: tol >= 0; sets maximum ref-to-feedback edge separation.
- `lock_detector.need` defaults to `3`; valid range: need >= 1; sets consecutive aligned reference events required for lock.
- `lock_detector.tr` defaults to `5e-10` s; valid range: tr > 0; sets lock transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ALIGNMENT_STREAK`: restore: lock asserts only after need consecutive reference edges whose most recent feedback edge is within tol. Required traces: `time`, `ref_clk`, `fb_clk`, `rst_n`, `lock`.
- `P_PREMATURE_LOCK`: restore: lock remains low before the need-th consecutive aligned reference event. Required traces: `time`, `ref_clk`, `fb_clk`, `lock`.
- `P_MISS_BREAKS_STREAK`: restore: A reference event outside tol breaks the streak and clears lock. Required traces: `time`, `ref_clk`, `fb_clk`, `lock`.
- `P_RESET_REACQUIRE`: restore: Active-low reset clears stored edge history, streak, and lock and requires a fresh post-reset acquisition. Required traces: `time`, `ref_clk`, `fb_clk`, `rst_n`, `lock`.

## Modeling Constraints

- Use deterministic voltage-domain edge timing.
- Use voltage contributions with finite smoothing only.
- Do not hard-code evaluator stimulus, stop times, or sample windows.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `lock_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
