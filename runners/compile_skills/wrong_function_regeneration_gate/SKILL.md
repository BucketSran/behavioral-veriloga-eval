# wrong_function_regeneration_gate

Use this skill when an apparent module-linkage failure is actually wrong-function generation.

Trigger pattern:
- Strict preflight reports `undefined_module=<needed>;available_modules=<actual>`.
- A unique `module_name_linkage` rename is attempted and rejected.
- The renamed candidate then exposes a public interface mismatch such as `instance_port_count_mismatch` for the needed module.

Interpretation:
- The generated body is not merely named incorrectly.
- The candidate has implemented or emitted the wrong public function for the requested artifact slot.
- Deterministic local rewrite must stop here because changing the body would require functional regeneration, not syntax legalization.

Repair routing:
- Route to prompt-side LLM repair or regeneration.
- Include public evidence: missing model name, available model name, expected instance node count, generated module port count, and public prompt/interface contract.
- Do not use task ids, hidden gold code, checker internals, or benchmark-specific templates.
- Do not synthesize a replacement module in a hard guard.

For LLM regeneration, ask the model to regenerate the missing public module with the exact public interface required by the harness, while preserving the rest of the candidate artifacts.
