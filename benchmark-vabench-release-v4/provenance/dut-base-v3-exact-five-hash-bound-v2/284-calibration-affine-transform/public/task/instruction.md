# Calibration Affine Transform

## Task Contract

Build a Spectre-compatible voltage-domain behavioral model for Calibration helper that applies a rail-coded gain and offset transform with observable residual error.

This is a DUT source task. Implement only the `calibration_affine_transform` module; no external validation code, transistor devices, or extra helper module is part of the requested artifact.

## Public Verilog-A Interface

```verilog
module calibration_affine_transform(clk, rst, raw, gain_ctrl, offset_ctrl, en, out, resid_metric);
```

## Public Parameter Contract

- `parameter real vth = 0.45`.
- `parameter real vhi = 0.9`.
- `parameter real center = 0.45`.
- `parameter real gain_base = 0.50`.
- `parameter real gain_span = 1.00`.
- `parameter real resid_fullscale = 0.45`.
- `parameter real tr = 60p`.

## Required Behavior

- Update the stored output and metric only on each rising `clk` crossing. At that edge, if `V(rst) > vth` or `V(en) <= vth`, store `out = 0 V` and `resid_metric = 0 V`.
- Otherwise let `gain = gain_base + gain_span * clip01(V(gain_ctrl) / vhi)` and `offset = V(offset_ctrl) - center`.
- Compute `transformed = center + gain * (V(raw) - center) + offset` and store `out = clamp(transformed, 0, vhi)`.
- Store `resid_metric = vhi * clip01(abs(transformed - V(raw)) / resid_fullscale)`. Here `clip01(x)` limits `x` to `[0, 1]`.
- Use local analog helper functions rather than user task/endtask syntax.

## Modeling Constraints

Use voltage-domain behavioral Verilog-A only. Do not use user `task`/`endtask`, Verilog-AMS digital kernels, branch current contributions, transistor devices, `ddt()`, or `idt()`. Do not hard-code testbench-specific stimulus timing.

## Output Contract

Return only `calibration_affine_transform.va` implementing the public module. The file must compile under Spectre-compatible Verilog-A and must not require additional modules, include files beyond standard disciplines, or testbench changes.
