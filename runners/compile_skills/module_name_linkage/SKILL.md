# module_name_linkage

## Trigger

Use this skill when EVAS/Spectre-strict reports `spectre_strict:undefined_module=<needed>;available_modules=<actual>`.

## Rule

The Spectre instance model name must match a Verilog-A `module` declaration included in the staged sample.

## Repair Pattern

If there is exactly one missing model and exactly one generated module, rename the module declaration to the required public harness model name. Do not change ports or behavior in this skill.

## Safety Boundary

If multiple modules or multiple missing models are present, abstain. This skill only handles unique name-linkage mismatches.

The rename must be treated as a candidate edit, not a guaranteed fix. Accept it
only if the compile judge improves. If the renamed module then exposes an
incompatible port signature, the failure is not a linkage typo; it means the
generated body implements the wrong public function. In that case, reject the
local edit and route the task to prompt-side LLM repair or regeneration.
