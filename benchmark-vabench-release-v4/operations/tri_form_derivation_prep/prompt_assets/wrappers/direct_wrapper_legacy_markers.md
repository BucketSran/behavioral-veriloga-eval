# vaBench Direct Submission Contract

Return only the candidate artifacts declared by the task. Preserve exact file
names, module names, ports, parameters, and required artifact paths.

For each candidate file, emit the complete file contents exactly once inside
the vaBench artifact markers. The start marker must begin with the literal text
`<<<VABENCH_ARTIFACT path="`, must contain the exact declared relative artifact
path for this task, and must end with exactly three `>` characters. The end
marker must be exactly `<<<END_VABENCH_ARTIFACT>>>`.

Do not use filename-only markers such as `<<<model.va>>>`. Do not use input or
starter-file markers such as `<<<VABENCH_INPUT_ARTIFACT ...>>>` for your
submission. Only `VABENCH_ARTIFACT` is a valid submission marker.

Do not wrap the artifact body in Markdown code fences. In particular, do not
emit triple-backtick fences such as ```verilog, ```spectre, or ```.

Do not include explanatory prose, diagnostic logs, pass/fail claims, or
undeclared files outside the artifact blocks.

Do not copy placeholder paths such as `path="..."` or
`path="declared/path.ext"` into your answer. Use only the artifact path(s)
declared by the current task.
