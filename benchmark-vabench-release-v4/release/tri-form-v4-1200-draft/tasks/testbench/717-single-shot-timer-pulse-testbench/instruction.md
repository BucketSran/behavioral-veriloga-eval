# Single Shot Timer Pulse Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Single Shot Timer Pulse` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `single_shot_timer_pulse.va`:
  - Module `single_shot_timer_pulse` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `single_shot_timer_pulse` as `XDUT` with ordered public binding: vin=vin, vout=vout.

## Public Parameter Contract

- `single_shot_timer_pulse.pulse_width` defaults to `2n`; valid range: finite; overrides pulse_width.
- `single_shot_timer_pulse.vlogic_high` defaults to `0.9`; valid range: finite; overrides vlogic_high.
- `single_shot_timer_pulse.vlogic_low` defaults to `0.0`; valid range: finite; overrides vlogic_low.
- `single_shot_timer_pulse.vtrans` defaults to `0.45`; valid range: finite; overrides vtrans.
- `single_shot_timer_pulse.tdel` defaults to `100p`; valid range: finite; overrides tdel.
- `single_shot_timer_pulse.trise` defaults to `10p`; valid range: finite; overrides trise.
- `single_shot_timer_pulse.tfall` defaults to `10p`; valid range: finite; overrides tfall.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DETECT_RISING_VIN_CROSSINGS_AT_VTRANS`: exercise and make observable: Detect rising `vin` crossings at `vtrans`. Required traces: `time`, `vin`, `vout`.
- `P_ON_EACH_QUALIFYING_RISING_EDGE_DRIVE`: exercise and make observable: On each qualifying rising edge, drive `vout` high after the configured transition delay. Required traces: `time`, `vin`, `vout`.
- `P_USE_A_TIMER_TO_SCHEDULE_THE`: exercise and make observable: Use a timer to schedule the low-going state update at `edge_time + pulse_width + trise`, where `edge_time` is the qualifying rising input edge time. The voltage contribution still uses the public `tdel`, `trise`, and `tfall` transition parameters. Required traces: `time`, `vin`, `vout`.
- `P_GENERATE_ONE_OUTPUT_PULSE_PER_INPUT`: exercise and make observable: Generate one output pulse per input rising edge. Required traces: `time`, `vin`, `vout`.
- `P_HOLD_THE_LOW_OUTPUT_LEVEL_BETWEEN`: exercise and make observable: Hold the low output level between pulses. Required traces: `time`, `vin`, `vout`.

The required trace names are: `time`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
