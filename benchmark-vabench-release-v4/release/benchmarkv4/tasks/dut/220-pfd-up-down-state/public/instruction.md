# PFD Up Down State

## Task Contract

Implement `pfd_up_down_state.va` as a bounded voltage-domain phase-frequency detector state machine.

## Public Verilog-A Interface

Use this module signature:

```verilog
module pfd_up_down_state(ref, fb, up, down);
```

All ports are scalar `electrical` nodes. `ref` and `fb` are voltage-coded clock inputs. `up` and `down` are voltage-coded detector outputs.

## Public Parameter Contract

- `vdd`: high level for outputs and threshold reference, default `1.2`.
- `tdel`: output transition delay, default `10p`.
- `tr`: output rise time, default `10p`.
- `tf`: output fall time, default `10p`.

## Required Behavior

- Detect rising `ref` and `fb` crossings at `vdd/2`.
- Maintain an integer detector state bounded to `-1`, `0`, or `+1`.
- A rising `ref` edge increments the state up to `+1`.
- A rising `fb` edge decrements the state down to `-1`.
- Drive `up` high when the state is `+1`.
- Drive `down` high when the state is `-1`.
- Drive both outputs low when the state is `0`.

## Modeling Constraints

Use voltage contributions only. Do not use current contributions, transistor-level devices, AC/noise analysis, checker logic, out-of-band test hooks, or simulator side channels.

## Output Contract

Return exactly one source artifact named `pfd_up_down_state.va`.
