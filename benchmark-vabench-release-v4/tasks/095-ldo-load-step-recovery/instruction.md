# LDO Load-Step Recovery Flow

## Task Contract

Implement the requested Verilog-A artifact for `LDO Load Step Recovery`.
- Form: `dut`
- Level: `L2`
- Category: `bias_reference_power_management`
- Target artifact(s): `ldo_load_step_recovery_flow.va`

- Target artifact: `ldo_load_step_recovery_flow.va`
- Implement only the requested Verilog-A flow DUT. Do not generate a Spectre testbench, validation logic, or auxiliary test hooks.
- Preserve the public module name, port order, starter parameters, and saved waveform observable names.

## Public Verilog-A Interface

```verilog
module ldo_load_step_recovery_flow(clk, rst, vin, out, metric, load_mon, ctrl_mon);
input clk, rst, vin;
output out, metric, load_mon, ctrl_mon;
electrical clk, rst, vin, out, metric, load_mon, ctrl_mon;
```

Starter parameter declarations are part of the public contract:

- `tr = 100p`: output transition rise/fall time.
- `vth = 0.45`: voltage-coded logic threshold.

## Public Parameter Contract

The public parameters declared by the target artifact are part of the contract and may be overridden by validation harnesses. Preserve their names, defaults, ranges, and meanings:

- `parameter real tr = 100p;` in `ldo_load_step_recovery_flow.va`.
- `parameter real vth = 0.45;` in `ldo_load_step_recovery_flow.va`.

## Required Behavior

- `clk` and `rst` are voltage-coded logic signals.
- Treat `vin` as a bounded load-step request for a behavioral LDO recovery flow.
- On reset, initialize the regulator output state and target to 0.60 V,
  `load_mon` to 0.10 V, `ctrl_mon` to 0.50 V, `metric` to 0.9 V, and the
  recovery counter to zero.
- On each rising `clk` crossing with reset low, clamp the sampled load request
  to `[0 V, 0.9 V]` and drive `load_mon` from that bounded load.
- Compute the load-dependent regulation target as `0.61 V - 0.025 * load`.
- Compute the abstract pass/recovery control monitor as
  `0.45 V + 0.40 * load + 0.50 * (target - regulator_state)`, clamped to
  `[0.05 V, 0.85 V]`, and drive `ctrl_mon` from that value.
- If the bounded load has increased by more than 0.20 V since the previous
  sampled load, apply a transient droop by subtracting 0.13 V from the
  regulator state and reset the recovery counter.
- If the bounded load has decreased by more than 0.20 V since the previous
  sampled load, apply a light-load recovery kick by adding 0.05 V to the
  regulator state and reset the recovery counter.
- On every non-reset update, after applying any load-step kick, update the
  current regulator state with first-order recovery:
  `state_next = state_prev + 0.30 * (target - state_prev)`, then clamp the
  driven `out` voltage to `[0.20 V, 0.75 V]`.
- Increment the recovery counter on each non-reset update. Drive `metric` to
  0.9 V when the recovery counter is at least 5 and
  `abs(regulator_state - target) < 0.045 V`; otherwise drive `metric` to
  0.25 V.
- Keep the model pure voltage-domain behavioral Verilog-A. Do not use branch-current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL regulation loops.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `ldo_load_step_recovery_flow.va`.
Do not include explanatory prose outside the source artifact contents.
