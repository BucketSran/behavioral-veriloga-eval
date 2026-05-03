# sourced_port_drive_boundary

## Trigger

Use this skill when EVAS/Spectre-strict reports `spectre_strict:sourced_port_voltage_drive`.

## Rule

A Verilog-A port driven by a contribution must not be tied directly to a source-fixed node such as `0`, `vss`, or a voltage source branch in the Spectre harness.

## Current Action

Judge only. This skill intentionally has no deterministic fixer yet because safe repair may require understanding whether the node is an input supply, output observable, or bidirectional port.

## Future Repair Direction

A safe fixer should split source-fixed and observable nodes only when direction and saved observables make the intent unambiguous, then verify with EVAS/Spectre before accepting.

Prompt-side repair guidance:

```spectre
// Bad: output-like port is tied to a fixed supply/source node.
XDUT (in vss) dut
```

Prefer connecting driven outputs to free observable nodes and tying only true
input supply ports to fixed sources:

```spectre
XDUT (in out_probe) dut
save out_probe
```

This remains judge-only locally because a deterministic fixer cannot always
infer whether a node is a supply input, a monitored output, or a bidirectional
boundary.
