# Variable Gain Differential Amplifier Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Variable Gain Differential Amplifier` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `variable_gain_differential_amplifier.va`:
  - Module `variable_gain_differential_amplifier` (entry)
    - position 0: `sigin_p` (input, electrical)
    - position 1: `sigin_n` (input, electrical)
    - position 2: `sigctrl_p` (input, electrical)
    - position 3: `sigctrl_n` (input, electrical)
    - position 4: `sigout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `variable_gain_differential_amplifier` as `XDUT` with ordered public binding: sigin_p=sigin_p, sigin_n=sigin_n, sigctrl_p=sigctrl_p, sigctrl_n=sigctrl_n, sigout=sigout.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DIFFERENTIAL_SIGNAL_AND_CONTROL`: exercise and make observable: Use `V(sigin_p, sigin_n)` as signal input and `V(sigctrl_p, sigctrl_n)` as gain-control input. Required traces: `time`, `sigin_p`, `sigin_n`, `sigctrl_p`, `sigctrl_n`, `sigout`.
- `P_VARIABLE_GAIN_MIDPOINT`: exercise and make observable: Drive the unclamped target as `2.0 * V(sigctrl_p, sigctrl_n) * V(sigin_p, sigin_n) + 0.2`. Required traces: `time`, `sigin_p`, `sigin_n`, `sigctrl_p`, `sigctrl_n`, `sigout`.
- `P_OUTPUT_CLAMP`: exercise and make observable: Clamp the final output target to the inclusive interval `[-0.4 V, 0.8 V]`. Required traces: `time`, `sigout`.

The required trace names are: `time`, `sigctrl_n`, `sigctrl_p`, `sigin_n`, `sigin_p`, `sigout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
