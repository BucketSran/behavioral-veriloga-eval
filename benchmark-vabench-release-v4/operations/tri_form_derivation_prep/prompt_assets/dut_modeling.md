# Verilog-A DUT Modeling Skill

Translate the public circuit contract into the exact declared artifact bundle.
Preserve file names, module names, ordered ports, parameters, dependencies, and
the distinction between entry modules and required submodules.

Use portable voltage-domain Verilog-A. Keep continuous contributions active,
keep event-driven state updates explicit, initialize state where the contract
requires it, and preserve hold, reset, threshold, rail, transition, and
parameter-override semantics. Treat a multi-file bundle as one integrated DUT.

Before finalizing, compare every public property and required trace signal with
the implementation. Do not add debug ports, validation state, undeclared files,
private-path assumptions, or stimulus-specific special cases.
