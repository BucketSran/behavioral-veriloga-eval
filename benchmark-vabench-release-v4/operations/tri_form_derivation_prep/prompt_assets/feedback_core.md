# EVAS Feedback Skill

The feedback CLI is an inspectable measurement surface, not a prescribed
repair recipe. Query its capabilities and request whichever available channels
best test the current hypothesis: artifact validation, AHDL-like diagnostics,
simulation logs, public traces, metrics, or property diagnostics.

Distinguish artifact, compile, runtime, missing-trace, and behavioral failures.
Use expected/observed values, event times, mismatch counts, metric gaps, and
traces when they are useful. The agent decides whether to establish a baseline,
which channel to inspect, when to edit, and whether another feedback call is
worth its token cost.

Feedback is not the private Spectre score. Preserve the public contract and do
not infer evaluator paths, checker source, hidden constants, or mutation code.
