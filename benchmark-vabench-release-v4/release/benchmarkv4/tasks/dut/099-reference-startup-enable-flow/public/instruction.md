# Reference Startup Enable Flow

## Task Contract

Implement the requested Verilog-A artifact for `Reference Startup Enable Flow`.
- Form: `dut`
- Level: `L2`
- Category: `bias_reference_power_management`
- Target artifact(s): `reference_startup_enable_flow.va`

- Target artifact: `reference_startup_enable_flow.va`
- Implement only the requested Verilog-A flow DUT. Do not generate a testbench, validation logic, or auxiliary test hooks.
- Preserve the public module name, port order, starter parameters, and saved waveform observable names.

## Public Verilog-A Interface

```verilog
module reference_startup_enable_flow(clk, rst, vdd_in, en, out, metric, supply_ok, enable_mon, state_mon, startup_mon);
input clk, rst, vdd_in, en;
output out, metric, supply_ok, enable_mon, state_mon, startup_mon;
electrical clk, rst, vdd_in, en, out, metric, supply_ok, enable_mon, state_mon, startup_mon;
```

Starter parameter declarations are part of the public contract:

- `tr = 100p`: output transition rise/fall time.
- `vth = 0.45`: voltage-coded logic threshold.

## Public Parameter Contract

The public parameters declared by the target artifact are part of the contract and may be overridden by validation harnesses. Preserve their names, defaults, ranges, and meanings:

- `parameter real tr = 100p;` in `reference_startup_enable_flow.va`.
- `parameter real vth = 0.45;` in `reference_startup_enable_flow.va`.

## Required Behavior

- `clk`, `rst`, and `en` are voltage-coded logic signals.
- `vdd_in` is the monitored supply waveform for the reference-startup flow.
- Update the startup flow on rising `clk` crossings through `vth`.
- Treat the supply as good when `vdd_in > 0.32 V`; drive `supply_ok` to 0.9 V when good and to 0 V otherwise.
- Drive `enable_mon` to 0.9 V when `en > vth` and to 0 V otherwise.
- When reset is active or the supply is not good, reset `out = 0 V`, `metric = 0 V`, startup count `0`, and state `0`.
- When supply is good but enable is low, hold the disabled reference at `out = 0.05 V`, drive `metric = 0.1 V`, reset startup count to `0`, and use state `1`.
- When supply is good and enable is high, update the reference as `out_next = out_prev + 0.32 * (0.55 - out_prev)` and increment the startup count by one until it saturates at `8`.
- The startup is valid after the enabled update when the count is at least `5` and `out > 0.48 V`. In startup but not yet valid, drive `metric = 0.25 V` and use state `2`; when valid, drive `metric = 0.9 V` and use state `3`.
- Drive `state_mon = 0.9 * state / 3.0`. Drive `startup_mon = 0.9 * count / 8.0` using the saturated startup count.
- A supply dip should reset valid status and startup progress; after the supply returns and enable remains asserted, the flow should recover through the same startup sequence.
- Keep the model pure voltage-domain behavioral Verilog-A. Do not use branch-current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL regulation loops.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `reference_startup_enable_flow.va`.
Do not include explanatory prose outside the source artifact contents.
