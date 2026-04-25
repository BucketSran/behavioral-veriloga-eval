Write a pure voltage-domain Verilog-A comparator with a built-in static offset.

Module name: `comparator_offset_search_ref`.

Requirements:

1. Ports: `vdd`, `vss`, `inp`, `inn`, `outp`
2. Built-in offset parameter `vos = 5m`
3. Output should switch high when `V(inp) - V(inn) > vos`
4. Use EVAS-compatible `cross()` events and `transition()`
5. The benchmark testbench will ramp `inp` and verify that the crossing occurs near `inn + vos`

Ports:
- `vdd`: electrical
- `vss`: electrical
- `inp`: electrical
- `inn`: electrical
- `outp`: electrical (power rail)
- `vss`: inout electrical (power rail)
- `inp`: input electrical
- `inn`: input electrical
- `outp`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=100n maxstep=100p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `time`, `inp`, `inn`, `outp`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `inn`, `inp`.
