Write a Verilog-A module named `cmp_hysteresis` and one minimal EVAS-compatible Spectre testbench.

# Task: comparator_hysteresis_smoke

## Objective

Create a pure voltage-domain differential comparator with hysteresis. The testbench must drive the
differential input through both hysteresis thresholds so both output states are observable.

## DUT Contract

- Module name: `cmp_hysteresis`
- Ports, all `electrical`, exactly in this order: `vinn`, `vinp`, `out_n`, `out_p`, `vss`, `vdd`
- Parameters:
  - `vhys` real, default `10e-3`
  - `tedge` real, default `50p`
- Behavior:
  - Rising decision threshold: `V(vinp) - V(vinn) > +vhys/2` drives `out_p` HIGH and `out_n` LOW.
  - Falling decision threshold: `V(vinp) - V(vinn) < -vhys/2` drives `out_p` LOW and `out_n` HIGH.
  - Between thresholds, hold the previous decision.
  - Use two separate `@(cross(...))` events for rising and falling thresholds.
  - Output HIGH should track `V(vdd)` and output LOW should track `V(vss)`.
  - Drive outputs with `transition(...)`.

## Testbench Contract

- Use a 0.9 V supply and 0 V reference.
- Drive `vinp` and `vinn` so the differential input crosses both `+vhys/2` and `-vhys/2` within the final validation window.
- Instantiate the DUT by positional ports.
- Save these exact scalar names: `vinp`, `vinn`, `out_p`, `out_n`.
- Include the generated DUT file `cmp_hysteresis.va`.
- Use the final transient setting provided by the injected Strict EVAS Validation Contract.

## Deliverables

Return exactly two fenced code blocks:

1. `cmp_hysteresis.va`
2. `tb_cmp_hysteresis.scs`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=80n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `time`, `out_p`, `out_n`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `vdd`, `gnd`, `vinp`, `vinn`.
