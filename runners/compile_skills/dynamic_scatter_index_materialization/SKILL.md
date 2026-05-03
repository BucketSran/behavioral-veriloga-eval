# dynamic_scatter_index_materialization

Use this skill when strict preflight reports `dynamic_analog_vector_index` for generated Verilog-A code.

The common failure shape is a runtime scatter write such as `V(out[idx]) <+ ...` after the model has computed an integer index. Spectre requires electrical contribution targets to be statically materialized.

Repair policy:
- First map public vector ports to scalar instance nodes when the Spectre harness already uses scalar nodes.
- Replace fixed-index reads/writes with the corresponding scalar node.
- For runtime scatter writes, emit one guarded static contribution per scalar target, for example `if (idx == 3) V(out_3) <+ expr;`.
- If the expression uses `transition()`, combine this with the transition target-buffer skill so the final contribution is unconditional at the analog block level.
- Do not infer hidden behavior; preserve the generated index arithmetic and only materialize the illegal electrical target syntax.
