# Task: random_fluctuation_source

Design a Verilog-A module named `random_fluctuation_source` that adds a zero-mean random perturbation to an input base signal and outputs the result.

## Module Interface

| Port | Direction | Description |
|------|-----------|-------------|
| base_signal | input | The clean input voltage signal |
| fluctuated_out | output | Input signal plus random perturbation |

## Behavioral Specification

At every simulation step, the module reads the instantaneous voltage on `base_signal`, draws a random perturbation from a bell-shaped distribution with standard deviation `sigma` centered at zero, adds it to the base signal, and drives the output through a `transition()` filter.

The perturbation must follow a normal (Gaussian) distribution with zero mean and standard deviation `sigma`.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| sigma | 0.01 | Standard deviation of the random perturbation |

## Constraints

- Must be pure voltage-domain
- Use `transition()` for output
- Use `$rdist_normal` for random number generation
- Do NOT use current-domain constructs

## Negative Constraints

- This is NOT a PRBS or pseudo-random bit sequence generator
- This is NOT a chirp, sine sweep, or deterministic waveform generator
- The perturbation must be drawn from a Gaussian distribution, NOT a uniform distribution

## Public Evaluation Contract

```spectre
simulator lang=spectre
global 0
Vbase (base_signal 0) vsource dc=1.0 type=dc
tran tran stop=500n maxstep=1n
save base_signal fluctuated_out
```

## Deliverables
Write your module to `dut.va`.
