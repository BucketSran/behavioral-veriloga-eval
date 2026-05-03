# conditional_transition_target_buffer

## Trigger

Use this skill when EVAS/Spectre-strict reports `spectre_strict:conditional_transition` or an AHDL diagnostic that a `transition()` contribution is inside a conditional, event, loop, or case statement.

## Rule

Spectre requires analog contributions using `transition()` to be structurally present unconditionally at analog top level. Branches may update held target variables, but they must not conditionally instantiate the contribution itself.

## Repair Pattern

Replace branch-local contributions:

```verilog-a
if (state) begin
    V(out) <+ transition(vhi, 0, tr);
end else begin
    V(out) <+ transition(vlo, 0, tr);
end
```

with target-buffer form:

```verilog-a
real out_target;

if (state) begin
    out_target = vhi;
end else begin
    out_target = vlo;
end
V(out) <+ transition(out_target, 0, tr);
```

## Safety Boundary

Do not tune thresholds, gains, timing constants, or state-machine semantics. Only move the contribution shape into a Spectre-legal form.

If the contribution target itself is dynamically indexed, for example
`V(out[idx]) <+ transition(...)`, this skill alone is not sufficient. First
materialize a static target surface, such as `out_0 ... out_N`, or route the
case to a dedicated scatter-index skill. A plain target buffer only makes the
`transition()` structurally unconditional; it does not make a dynamic analog
accessor Spectre-legal.
