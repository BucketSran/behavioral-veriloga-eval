# vaBench Direct Submission Contract

Return only the candidate artifacts declared by the task through the output
transport provided by the evaluation runtime. Preserve exact file names,
module names, ports, parameters, and required artifact paths.

Follow the runtime's transport-specific instruction exactly. Emit every
declared candidate artifact once, with complete contents. Do not add
explanatory prose, diagnostic logs, pass/fail claims, undeclared files, or
placeholder paths.

The transport is delivery-only: it does not execute the candidate or provide
checker feedback.
