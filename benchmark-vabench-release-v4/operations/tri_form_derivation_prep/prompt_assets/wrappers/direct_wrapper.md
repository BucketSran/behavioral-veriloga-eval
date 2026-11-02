# vaBench Direct Submission Contract

Return only the candidate artifacts declared by the task through the output
transport provided by the evaluation runtime. Preserve exact file names,
module names, ports, parameters, and required artifact paths.

Follow the runtime's transport-specific instruction exactly. Do not emit an
alternate marker format, Markdown fence, JSON envelope, explanatory prose,
diagnostic logs, pass/fail claims, or undeclared files. Do not duplicate
artifacts or invent placeholder paths.

The transport is delivery-only: it does not execute the candidate or provide
checker feedback.
