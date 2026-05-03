# vector_scalar_interface

## Trigger

Use this skill when EVAS/Spectre-strict reports `spectre_strict:dynamic_analog_vector_index` or `spectre_strict:instance_port_count_mismatch` caused by scalar Spectre nodes connected to Verilog-A vector ports.

## Rule

Runtime integer indexing inside analog accessors such as `V(bus[i])` is not Spectre-safe. If the public harness uses scalar node names, materialize scalar ports and fixed-index contributions.

## Repair Pattern

Convert vector ports such as `output [15:0] out; electrical [15:0] out;` into scalar ports that match the Spectre instance nodes, and replace simple `for` loops over `V(out[i])` with fixed-index contributions.

## Safety Boundary

This skill is safe only when the Spectre instance node count matches the expanded vector width. Complex computed scatter indices should be judged but not blindly rewritten unless a dedicated scatter skill exists.

Computed scatter patterns include forms such as:

```verilog-a
cell_idx = ptr + i;
V(cell_en_o[cell_idx]) <+ transition(vdd, 0, tr);
```

These are stronger than simple vector-to-scalar materialization because the
target node is selected at runtime. A future scatter skill should convert the
runtime selection into explicit state variables and fixed top-level
contributions, then accept only after EVAS/Spectre compile validation.
