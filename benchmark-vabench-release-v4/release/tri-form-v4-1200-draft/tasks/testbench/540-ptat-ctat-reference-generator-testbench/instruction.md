# PTAT CTAT Reference Generator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PTAT CTAT Reference Generator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `ptat_ctat_reference_generator.va`:
  - Module `ptat_ctat_reference_generator` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ptat_ctat_reference_generator` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `ptat_ctat_reference_generator.tr` defaults to `1e-10` s; valid range: tr > 0; sets output and metric transition smoothing.
- `ptat_ctat_reference_generator.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets clk and rst logic threshold.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_REFERENCE`: exercise and make observable: Reset initializes out to 0.45 V and metric to 0 V until a valid rising-clock update. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_INPUT_CLAMP`: exercise and make observable: Each rising clk update with reset inactive samples vin and clamps the temperature/control value to 0 V through 0.9 V. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_PTAT_TREND`: exercise and make observable: Metric reports the PTAT branch 0.18 V plus 0.34 times the clamped sampled input and therefore increases monotonically with vin. Required traces: `time`, `clk`, `vin`, `metric`.
- `P_CTAT_PTAT_AVERAGE`: exercise and make observable: Out is the equal-weight average of PTAT = 0.18 V + 0.34*vin_clamped and CTAT = 0.78 V - 0.34*vin_clamped. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_REFERENCE_BOUNDS`: exercise and make observable: Out remains within the public 0 V through 0.9 V voltage range with finite transition smoothing. Required traces: `time`, `out`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
