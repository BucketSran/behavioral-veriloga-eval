# Start Gated Offset Search Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Start Gated Offset Search` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `start_gated_offset_search.va`:
  - Module `start_gated_offset_search` (entry)
    - position 0: `CLK` (input, electrical)
    - position 1: `VOUT` (input, electrical)
    - position 2: `START` (input, electrical)
    - position 3: `VINP` (output, electrical)
    - position 4: `VINN` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `start_gated_offset_search` as `XDUT` with ordered public binding: CLK=clk, VOUT=vout, START=start, VINP=vinp, VINN=vinn.

## Public Parameter Contract

- `start_gated_offset_search.vdd` defaults to `0.9` V; valid range: vdd > 0; sets twice the CLK and VOUT decision threshold.
- `start_gated_offset_search.vcm` defaults to `0.7` V; valid range: finite real; sets the common mode of VINP and VINN.
- `start_gated_offset_search.vstart_th` defaults to `0.45` V; valid range: finite real; sets the START enable and reinitialization threshold.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DISABLED_COMMON_MODE`: exercise and make observable: While START is below vstart_th, VINP and VINN both equal vcm and the internal search state is reset. Required traces: `time`, `start`, `vinp`, `vinn`.
- `P_START_REINITIALIZATION`: exercise and make observable: Each rising START crossing through vstart_th reinitializes differential value to zero, step to 20 mV, and remembered direction high. Required traces: `time`, `start`, `vinp`, `vinn`.
- `P_FALLING_CLOCK_UPDATES`: exercise and make observable: While START is high, search updates occur only on falling CLK crossings through vdd/2. Required traces: `time`, `clk`, `start`, `vout`, `vinp`, `vinn`.
- `P_DECISION_DIRECTED_STEP`: exercise and make observable: At each enabled update, VOUT above vdd/2 moves the differential value positive and VOUT at or below vdd/2 moves it negative. Required traces: `time`, `clk`, `vout`, `vinp`, `vinn`.
- `P_REVERSAL_STEP_HALVING`: exercise and make observable: When the newly sampled decision direction differs from the remembered direction, the current step is halved before applying the move. Required traces: `time`, `clk`, `vout`, `vinp`, `vinn`.
- `P_COMMON_MODE_AND_DIFFERENTIAL`: exercise and make observable: During search, the average of VINP and VINN remains vcm and their difference equals the accumulated differential search value. Required traces: `time`, `start`, `vinp`, `vinn`.

The required trace names are: `time`, `clk`, `vout`, `start`, `vinp`, `vinn`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
