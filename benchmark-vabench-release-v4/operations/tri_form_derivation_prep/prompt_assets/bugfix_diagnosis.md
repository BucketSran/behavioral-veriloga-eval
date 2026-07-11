# Verilog-A Bugfix Diagnosis Skill

Treat the supplied source bundle as an existing system. Inspect all editable
files and declared module dependencies, compare their behavior with the public
contract, and make the smallest justified semantic repair.

Preserve the exact file set, module graph, public interfaces, parameters, and
all behavior that already satisfies the contract. Avoid replacing a structured
system with an unrelated implementation or tuning only one observed stimulus.

Runtime baseline strategy and feedback-loop choices are intentionally outside
this writing skill. Do not assume a particular faulty file, line, constant, or
root cause unless the public evidence establishes it.
