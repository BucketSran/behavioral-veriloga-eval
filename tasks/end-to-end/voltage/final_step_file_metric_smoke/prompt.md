Write a Verilog-A module named `final_step_file_metric_ref`.

# Task: final_step_file_metric_smoke

## Objective

Write a Verilog-A measurement helper that counts input edges, exposes the normalized count on a voltage output, and writes the final metric to a file during `@(final_step)`.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `ref`: input electrical
- `metric_out`: output electrical
