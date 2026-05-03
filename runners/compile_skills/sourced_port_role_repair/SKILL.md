# sourced_port_role_repair

Use this skill when Spectre-strict preflight reports `sourced_port_voltage_drive`.

The compile hazard is a boundary-role conflict: a generated Verilog-A model drives a port, but the Spectre harness connects that port to a source-fixed node such as `0`, `VDD`, or `VSS`. Spectre rejects this because two ideal drivers own the same node.

Repair policy:
- Trust only public information: the generated module declaration, the generated Spectre instance, and the strict diagnostic `instance:model:port->node`.
- Prefer preserving behavior by correcting the instance port position when a public module signature is available.
- If the candidate only exposes a source-fixed conflict and no trustworthy signature, detach the driven port to a fresh auditable node such as `__cg_XDUT_port_free` rather than tying it to an ideal source.
- Do not use task ids or hidden gold templates.
- Treat the edit as compile-boundary repair; accept it only if the strict validator improves or remains behaviorally safe under the experiment's accept/reject gate.
