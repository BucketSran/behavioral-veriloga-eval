# missing_testbench_generation

Use this skill when a candidate lacks the required Spectre testbench artifact, for example `missing_generated_files=testbench.scs` or `spectre_strict:missing_staged_tb`.

The goal is compile closure, not behavior invention. Build a minimal smoke harness from public generated files:
- Include every generated `.va` file with `ahdl_include`.
- Choose the likely DUT from public module declarations, preferring non-helper modules and wider public interfaces.
- Instantiate ports in the declared order; expand vector ports into scalar nodes when the declaration gives a width.
- Drive only public inputs and supply-like inouts with simple deterministic sources.
- Leave outputs undriven and save them.
- If the smoke harness exposes already-known Spectre-strict syntax hazards in
  the generated DUT, compose only with existing public compile skills such as
  `conditional_transition_target_buffer`; do not invent new behavior.
- Do not inject task-specific expected waveforms, hidden reference behavior, or task ids.

A generated skeleton should be accepted only through the same strict validator used by the benchmark.
