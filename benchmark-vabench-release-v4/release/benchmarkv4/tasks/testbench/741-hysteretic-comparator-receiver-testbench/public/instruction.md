# Hysteretic Comparator Receiver Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Hysteretic Comparator Receiver` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `hysteretic_comparator_receiver.va`:
  - Module `hysteretic_comparator_receiver` (entry)
    - position 0: `inp` (input, electrical)
    - position 1: `inm` (input, electrical)
    - position 2: `out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `hysteretic_comparator_receiver` as `XDUT` with ordered public binding: inp=inp, inm=inm, out=out.

## Public Parameter Contract

- `hysteretic_comparator_receiver.vout_high` defaults to `0.9`; valid range: finite; overrides vout_high.
- `hysteretic_comparator_receiver.vout_low` defaults to `0.0`; valid range: finite; overrides vout_low.
- `hysteretic_comparator_receiver.offset` defaults to `0.0`; valid range: finite; overrides offset.
- `hysteretic_comparator_receiver.vhys` defaults to `40e-3 from [0:inf)`; valid range: finite; overrides vhys.
- `hysteretic_comparator_receiver.td` defaults to `400p from [0:inf)`; valid range: finite; overrides td.
- `hysteretic_comparator_receiver.tr` defaults to `80p from [0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DEFINE_UPPER_TH_OFFSET_VHYS_2`: exercise and make observable: Define `upper_th = offset + vhys/2` and `lower_th = offset - vhys/2`. On initialization, set the output state high if `V(inp,inm)` is at or above the upper threshold; otherwise set it low. After initialization, switch high only on a rising crossing of `upper_th`, switch low only on a falling crossing of `lower_th`, and hold the previous state inside the hysteresis band. Drive `out` to the selected rail with delay `td` and transition time `tr`. Required traces: `time`, `inm`, `inp`, `out`.
- `P_VOUT_HIGH_0_9_V_HIGH`: exercise and make observable: `vout_high = 0.9 V`: high output rail. Required traces: `time`, `inm`, `inp`, `out`.
- `P_VOUT_LOW_0_0_V_LOW`: exercise and make observable: `vout_low = 0.0 V`: low output rail. Required traces: `time`, `inm`, `inp`, `out`.
- `P_OFFSET_0_0_V_INPUT_REFERRED`: exercise and make observable: `offset = 0.0 V`: input-referred switching offset. Required traces: `time`, `inm`, `inp`, `out`.
- `P_VHYS_40_MV_FROM_0_INF`: exercise and make observable: `vhys = 40 mV from [0:inf)`: total hysteresis width. Required traces: `time`, `inm`, `inp`, `out`.
- `P_TD_400_PS_FROM_0_INF`: exercise and make observable: `td = 400 ps from [0:inf)`: propagation delay from a qualifying threshold crossing to the output state change. Required traces: `time`, `inm`, `inp`, `out`.

The required trace names are: `time`, `inm`, `inp`, `out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
