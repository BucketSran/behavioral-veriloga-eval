# missing_testbench_artifact

## Trigger

Use this skill when a candidate is missing the required generated Spectre testbench, e.g. `missing_generated_files=testbench.scs` or `spectre_strict:missing_staged_tb`.

## Rule

End-to-end and testbench-generation tasks must provide a staged Spectre testbench artifact. A Verilog-A-only response cannot pass the compile/interface gate.

## Current Action

Judge only. This skill has no deterministic fixer yet because generating a complete testbench is a synthesis task, not a safe local rewrite.

## Future Repair Direction

A skill-guided LLM repair can regenerate the missing testbench from public prompt and candidate DUT. A local selector may reuse an earlier compile-clean testbench only if provenance and task-family constraints are explicit.

Prompt-side repair guidance:

1. Emit the required `.scs` testbench artifact for end-to-end and
   testbench-generation tasks.
2. Include the generated Verilog-A module with `ahdl_include`.
3. Instantiate the DUT with the public port order from the prompt or generated
   module declaration.
4. Add `tran` and `save` statements for the public observable signals.

Do not mark this as safe local autofix until the provenance rule for reusing or
synthesizing a testbench is explicit.
