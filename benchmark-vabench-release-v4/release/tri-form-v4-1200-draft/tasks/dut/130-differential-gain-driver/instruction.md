# Differential Gain Driver

## Task Contract
Implement the Verilog-A DUT `differential_gain_driver.va` for a balanced differential output driver referenced to a supplied common node.

## Public Verilog-A Interface
Provide `module differential_gain_driver(sigin_p, sigin_n, sigout_p, sigout_n, sigref);` with electrical inputs `sigin_p`, `sigin_n`, `sigref` and electrical outputs `sigout_p`, `sigout_n`.

## Public Parameter Contract
Expose `parameter real gain = 1;`. Testbenches may override this gain.

## Required Behavior
Read `V(sigin_p, sigin_n)` and generate a differential output equal to that input differential voltage multiplied by `gain`. Split the output swing equally: `sigout_p` moves positive around `sigref`, and `sigout_n` moves negative around `sigref` for a positive input differential.

## Modeling Constraints
Use voltage-domain contributions only. Do not add an unrelated common-mode shift, collapse the output to a single-ended response, invert polarity, or depend on testbench-specific constants.

## Output Contract
Submit only the completed Verilog-A module in `differential_gain_driver.va`.
