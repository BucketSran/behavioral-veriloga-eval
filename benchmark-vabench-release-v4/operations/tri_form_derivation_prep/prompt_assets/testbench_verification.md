# Spectre Testbench Verification Skill

Map each public property to a trigger, controlled stimulus, required public
signals, and an observable relation. Build one bounded transient experiment
that accepts the supplied correct DUT while exposing meaningful threshold,
polarity, state, reset, timing, rail, gain, clipping, and sequencing errors
implied by the contract.

Use only the declared `./dut/...` source binding and public module interfaces.
Save every signal named by the trace contract. Prefer stimulus-relative
observations so the fixed oracle can interpret events chosen by the testbench.
Compilation failure, missing traces, and invalid runs do not count as detecting
a behavioral fault.

Submit exactly the declared top-level `.scs` file. Do not redefine the DUT,
drive DUT outputs, probe private internals, load undeclared files, or emit a
self-reported PASS/FAIL result.
