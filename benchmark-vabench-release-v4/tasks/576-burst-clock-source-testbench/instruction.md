# Burst Clock Source Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Burst Clock Source` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `clk_burst_gen.va`:
  - Module `clk_burst_gen` (entry)
    - position 0: `CLK` (input, electrical)
    - position 1: `RST_N` (input, electrical)
    - position 2: `CLK_OUT` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `clk_burst_gen` as `XDUT` with ordered public binding: CLK=CLK, RST_N=RST_N, CLK_OUT=CLK_OUT.

## Public Parameter Contract

- `clk_burst_gen.div` defaults to `8` input-clock cycles; valid range: div >= 3; sets the number of input-clock cycles in each repeating burst frame.
- `clk_burst_gen.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded CLK_OUT high level.
- `clk_burst_gen.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the CLK and active-low reset decision threshold.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ACTIVE_LOW_RESET`: exercise and make observable: While RST_N is below vth, CLK_OUT is low and the burst frame counter is restarted. Required traces: `time`, `CLK`, `RST_N`, `CLK_OUT`.
- `P_FRAME_START`: exercise and make observable: After reset release, rising CLK crossings advance a repeating frame of div input-clock cycles beginning at position 0. Required traces: `time`, `CLK`, `RST_N`, `CLK_OUT`.
- `P_TWO_CYCLE_BURST`: exercise and make observable: At frame positions 0 and 1, CLK_OUT passes the voltage-coded CLK waveform, including its high and low phases. Required traces: `time`, `CLK`, `RST_N`, `CLK_OUT`.
- `P_QUIET_REMAINDER`: exercise and make observable: At frame positions 2 through div minus 1, CLK_OUT remains low regardless of CLK level. Required traces: `time`, `CLK`, `RST_N`, `CLK_OUT`.
- `P_FRAME_REPEAT`: exercise and make observable: The two-cycle burst followed by the quiet remainder repeats every div rising CLK crossings. Required traces: `time`, `CLK`, `RST_N`, `CLK_OUT`.
- `P_OUTPUT_LEVELS`: exercise and make observable: CLK_OUT uses 0 V and vdd as its voltage-coded low and high levels. Required traces: `time`, `CLK_OUT`.

The required trace names are: `time`, `CLK`, `RST_N`, `CLK_OUT`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
