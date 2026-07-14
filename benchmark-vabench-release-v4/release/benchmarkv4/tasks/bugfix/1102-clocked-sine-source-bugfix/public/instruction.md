# Clocked Sine Source Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `vin_src.va`:
  - Module `vin_src` (entry)
    - position 0: `CLK` (input, electrical)
    - position 1: `RST_N` (input, electrical)
    - position 2: `VOUT_P` (output, electrical)
    - position 3: `VOUT_N` (output, electrical)

## Public Parameter Contract

- `vin_src.vdd` defaults to `0.9` V; valid range: vdd > 0; sets twice the output common-mode level.
- `vin_src.vth` defaults to `0.45` V; valid range: finite real; sets CLK and active-low reset decision thresholds.
- `vin_src.ampl` defaults to `0.15` V; valid range: ampl >= 0; sets sampled sine amplitude on VOUT_P.
- `vin_src.freq` defaults to `300000.0` Hz; valid range: freq >= 0; sets sampled sine frequency.
- `vin_src.sigma` defaults to `0.01` V; valid range: sigma >= 0; sets the scale of the optional deterministic seeded perturbation on VOUT_P.
- `vin_src.SEED` defaults to `0`; valid range: any integer accepted by the simulator random function; initializes the repeatable perturbation sequence.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_COMMON_MODE`: restore: While RST_N is below vth, both outputs hold near vdd divided by two. Required traces: `time`, `rst_n`, `vinp`, `vinn`.
- `P_RISING_EDGE_SAMPLE`: restore: After reset release, VOUT_P updates only on rising CLK crossings through vth. Required traces: `time`, `clk`, `rst_n`, `vinp`.
- `P_SAMPLED_SINE`: restore: At each qualifying clock edge, VOUT_P samples vdd/2 plus ampl times sin(2*pi*freq*time), plus the optional seeded perturbation. Required traces: `time`, `clk`, `rst_n`, `vinp`.
- `P_REFERENCE_SIDE_COMMON_MODE`: restore: VOUT_N remains at vdd divided by two during reset and active sampling. Required traces: `time`, `rst_n`, `vinn`.
- `P_INTEREDGE_HOLD`: restore: Both outputs hold their sampled values between CLK events rather than continuously recomputing the sine or perturbation. Required traces: `time`, `clk`, `vinp`, `vinn`.
- `P_SEEDED_REPEATABILITY`: restore: For fixed SEED, sigma, controls, and timing, the sampled perturbation sequence and outputs are repeatable; sigma zero removes the perturbation. Required traces: `time`, `clk`, `rst_n`, `vinp`, `vinn`.

## Modeling Constraints

- Sample the sine and optional seeded perturbation only on rising CLK crossings after reset release.
- Use deterministic seeded behavior and smoothed voltage contributions only.
- Do not use transistor-level devices, AC/noise analysis, waveform files, validation artifacts, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `vin_src.va`.
Every supplied `.va` file is editable; do not add or omit files.
