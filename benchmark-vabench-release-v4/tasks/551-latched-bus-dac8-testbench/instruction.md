# Latched Bus DAC8 Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Latched Bus DAC8` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `latched_bus_dac8.va`:
  - Module `latched_bus_dac8` (entry)
    - position 0: `vclk` (input, electrical)
    - position 1: `b7` (input, electrical)
    - position 2: `b6` (input, electrical)
    - position 3: `b5` (input, electrical)
    - position 4: `b4` (input, electrical)
    - position 5: `b3` (input, electrical)
    - position 6: `b2` (input, electrical)
    - position 7: `b1` (input, electrical)
    - position 8: `b0` (input, electrical)
    - position 9: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `latched_bus_dac8` as `XDUT` with ordered public binding: vclk=vclk, b7=b7, b6=b6, b5=b5, b4=b4, b3=b3, b2=b2, b1=b1, b0=b0, vout=vout.

## Public Parameter Contract

- `latched_bus_dac8.vth` defaults to `0.45` V; valid range: vth > 0; sets the rising-edge and input-bit decision threshold.
- `latched_bus_dac8.vref` defaults to `1` V; valid range: vref > 0; sets the full-scale analog endpoint.
- `latched_bus_dac8.tr` defaults to `2e-11` s; valid range: tr > 0; sets analog output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RISING_EDGE_CAPTURE`: exercise and make observable: Each rising crossing of vclk through vth captures the unsigned value of b[7:0]. Required traces: `time`, `vclk`, `b7`, `b6`, `b5`, `b4`, `b3`, `b2`, `b1`, `b0`, `vout`.
- `P_HOLD_BETWEEN_EDGES`: exercise and make observable: vout retains the value from the most recent rising clock crossing despite input-bus changes between update edges. Required traces: `time`, `vclk`, `b7`, `b6`, `b5`, `b4`, `b3`, `b2`, `b1`, `b0`, `vout`.
- `P_ENDPOINTS`: exercise and make observable: Latched code 0 maps to 0 V and latched code 255 maps to vref. Required traces: `time`, `vclk`, `b7`, `b6`, `b5`, `b4`, `b3`, `b2`, `b1`, `b0`, `vout`.
- `P_BINARY_MONOTONICITY`: exercise and make observable: Increasing the latched unsigned code never decreases vout, with b7 as MSB and b0 as LSB. Required traces: `time`, `vclk`, `b7`, `b6`, `b5`, `b4`, `b3`, `b2`, `b1`, `b0`, `vout`.
- `P_OUTPUT_SMOOTHING`: exercise and make observable: vout approaches each newly latched target with finite transition smoothing set by tr. Required traces: `time`, `vclk`, `vout`.

The required trace names are: `time`, `vclk`, `b7`, `b6`, `b5`, `b4`, `b3`, `b2`, `b1`, `b0`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
