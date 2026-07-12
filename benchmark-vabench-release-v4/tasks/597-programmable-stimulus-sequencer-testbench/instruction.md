# Programmable Stimulus Sequencer Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Programmable Stimulus Sequencer` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `programmable_stimulus_sequencer.va`:
  - Module `programmable_stimulus_sequencer` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `mode` (input, electrical)
    - position 3: `gate` (input, electrical)
    - position 4: `out` (output, electrical)
    - position 5: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `programmable_stimulus_sequencer` as `XDUT` with ordered public binding: clk=clk, rst=rst, mode=mode, gate=gate, out=out, metric=metric.

## Public Parameter Contract

- `programmable_stimulus_sequencer.tr` defaults to `8e-11` s; valid range: finite real; use tr >= 0 for physical transition smoothing; sets rise and fall smoothing for out and metric without changing segment selection.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_IDLE`: exercise and make observable: When rst is above the 0.45 V control threshold, out is held near 0.45 V and metric is low. Required traces: `time`, `rst`, `out`, `metric`.
- `P_RAMP_MODE`: exercise and make observable: For mode below 0.30 V outside reset, out produces a monotonic ramp segment from about 0.18 V toward 0.45 V and metric is near 0.20 V. Required traces: `time`, `rst`, `mode`, `out`, `metric`.
- `P_CHIRP_MODE`: exercise and make observable: For mode from 0.30 V through below 0.60 V, out is a sine segment centered near 0.45 V whose instantaneous frequency increases over the segment, with metric near 0.50 V. Required traces: `time`, `rst`, `mode`, `out`, `metric`.
- `P_BURST_GATE`: exercise and make observable: For mode at or above 0.60 V and gate high, out produces a deterministic PRBS-like burst between the low and high stimulus levels. Required traces: `time`, `clk`, `rst`, `mode`, `gate`, `out`.
- `P_BURST_IDLE`: exercise and make observable: In burst mode with gate low, out returns near 0.45 V and metric reports the idle rather than active-burst status. Required traces: `time`, `rst`, `mode`, `gate`, `out`, `metric`.
- `P_CONTROL_DRIVEN_SELECTION`: exercise and make observable: Mode and gate behavior follows the voltage-coded inputs over arbitrary legal control schedules rather than a fixed stimulus timeline. Required traces: `time`, `clk`, `rst`, `mode`, `gate`, `out`, `metric`.

The required trace names are: `time`, `clk`, `rst`, `mode`, `gate`, `out`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
