# Clocked Sine Source Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clocked Sine Source` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `vin_src.va`:
  - Module `vin_src` (entry)
    - position 0: `CLK` (input, electrical)
    - position 1: `RST_N` (input, electrical)
    - position 2: `VOUT_P` (output, electrical)
    - position 3: `VOUT_N` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `vin_src` as `XDUT` with ordered public binding: CLK=clk, RST_N=rst_n, VOUT_P=vout_p, VOUT_N=vout_n.

## Public Parameter Contract

- `vin_src.vdd` defaults to `0.9` V; valid range: vdd > 0; sets twice the output common-mode level.
- `vin_src.vth` defaults to `0.45` V; valid range: finite real; sets CLK and active-low reset decision thresholds.
- `vin_src.ampl` defaults to `0.15` V; valid range: ampl >= 0; sets sampled sine amplitude on VOUT_P.
- `vin_src.freq` defaults to `300000.0` Hz; valid range: freq >= 0; sets sampled sine frequency.
- `vin_src.sigma` defaults to `0.01` V; valid range: sigma >= 0; sets the scale of the optional deterministic seeded perturbation on VOUT_P.
- `vin_src.SEED` defaults to `0`; valid range: any integer accepted by the simulator random function; initializes the repeatable perturbation sequence.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_COMMON_MODE`: exercise and make observable: While RST_N is below vth, both outputs hold near vdd divided by two. Required traces: `time`, `rst_n`, `vinp`, `vinn`.
- `P_RISING_EDGE_SAMPLE`: exercise and make observable: After reset release, VOUT_P updates only on rising CLK crossings through vth. Required traces: `time`, `clk`, `rst_n`, `vinp`.
- `P_SAMPLED_SINE`: exercise and make observable: At each qualifying clock edge, VOUT_P samples vdd/2 plus ampl times sin(2*pi*freq*time), plus the optional seeded perturbation. Required traces: `time`, `clk`, `rst_n`, `vinp`.
- `P_REFERENCE_SIDE_COMMON_MODE`: exercise and make observable: VOUT_N remains at vdd divided by two during reset and active sampling. Required traces: `time`, `rst_n`, `vinn`.
- `P_INTEREDGE_HOLD`: exercise and make observable: Both outputs hold their sampled values between CLK events rather than continuously recomputing the sine or perturbation. Required traces: `time`, `clk`, `vinp`, `vinn`.
- `P_SEEDED_REPEATABILITY`: exercise and make observable: For fixed SEED, sigma, controls, and timing, the sampled perturbation sequence and outputs are repeatable; sigma zero removes the perturbation. Required traces: `time`, `clk`, `rst_n`, `vinp`, `vinn`.

The required trace names are: `time`, `clk`, `rst_n`, `vinp`, `vinn`, `vamp_p`, `vamp_n`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
