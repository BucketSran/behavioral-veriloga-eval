# Hysteretic Comparator Receiver Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `hysteretic_comparator_receiver.va`:
  - Module `hysteretic_comparator_receiver` (entry)
    - position 0: `inp` (input, electrical)
    - position 1: `inm` (input, electrical)
    - position 2: `out` (output, electrical)

## Public Parameter Contract

- `hysteretic_comparator_receiver.vout_high` defaults to `0.9`; valid range: finite; overrides vout_high.
- `hysteretic_comparator_receiver.vout_low` defaults to `0.0`; valid range: finite; overrides vout_low.
- `hysteretic_comparator_receiver.offset` defaults to `0.0`; valid range: finite; overrides offset.
- `hysteretic_comparator_receiver.vhys` defaults to `40e-3 from [0:inf)`; valid range: finite; overrides vhys.
- `hysteretic_comparator_receiver.td` defaults to `400p from [0:inf)`; valid range: finite; overrides td.
- `hysteretic_comparator_receiver.tr` defaults to `80p from [0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DEFINE_UPPER_TH_OFFSET_VHYS_2`: restore: Define `upper_th = offset + vhys/2` and `lower_th = offset - vhys/2`. On initialization, set the output state high if `V(inp,inm)` is at or above the upper threshold; otherwise set it low. After initialization, switch high only on a rising crossing of `upper_th`, switch low only on a falling crossing of `lower_th`, and hold the previous state inside the hysteresis band. Drive `out` to the selected rail with delay `td` and transition time `tr`. Required traces: `time`, `inm`, `inp`, `out`.
- `P_VOUT_HIGH_0_9_V_HIGH`: restore: `vout_high = 0.9 V`: high output rail. Required traces: `time`, `inm`, `inp`, `out`.
- `P_VOUT_LOW_0_0_V_LOW`: restore: `vout_low = 0.0 V`: low output rail. Required traces: `time`, `inm`, `inp`, `out`.
- `P_OFFSET_0_0_V_INPUT_REFERRED`: restore: `offset = 0.0 V`: input-referred switching offset. Required traces: `time`, `inm`, `inp`, `out`.
- `P_VHYS_40_MV_FROM_0_INF`: restore: `vhys = 40 mV from [0:inf)`: total hysteresis width. Required traces: `time`, `inm`, `inp`, `out`.
- `P_TD_400_PS_FROM_0_INF`: restore: `td = 400 ps from [0:inf)`: propagation delay from a qualifying threshold crossing to the output state change. Required traces: `time`, `inm`, `inp`, `out`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `hysteretic_comparator_receiver.va`.
Every supplied `.va` file is editable; do not add or omit files.
