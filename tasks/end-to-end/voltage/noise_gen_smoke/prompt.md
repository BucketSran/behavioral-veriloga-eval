Write a Verilog-A module named `noise_gen`.

Create a voltage-domain Gaussian noise generator in Verilog-A,
then produce a minimal EVAS-compatible Spectre testbench and run a smoke simulation.

Behavioral intent:

- one analog input `vin_i` and one analog output `vout_o`
- parameter `sigma` (real, in Volts) controls the noise standard deviation
- output = input + zero-mean Gaussian noise: `vout_o = vin_i + sigma * $rdist_normal(...)`
- the noise is independent and added on every time step
- use `transition(...)` to drive `vout_o`

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- `$rdist_normal` is the correct EVAS-compatible call for Gaussian samples
- `vin_i` and `vout_o` must appear in the waveform CSV

Minimum simulation goal:

- DC input at 1.0 V, sigma=0.1 V, run for 500 ns with maxstep=0.5 ns
- `vout_o` mean must be within ±0.5 V of `vin_i` (zero-mean noise)
- noise standard deviation (std of `vout_o - vin_i`) must be between 0.01 V and 0.5 V
- `vout_o` must not be identical to `vin_i` (noise must be non-trivial)

Ports:
- `vin_i`: input electrical
- `vout_o`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=500n maxstep=1n
```

Required public waveform columns in `tran.csv`:

- `vin_i`, `vout_o`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `vin_i`.
