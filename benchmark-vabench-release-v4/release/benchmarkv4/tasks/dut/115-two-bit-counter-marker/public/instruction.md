# Two Bit Counter Marker

## Task Contract

Implement the requested Verilog-A artifact for `Two Bit Counter Marker`, a
timing/readout marker for AMS sequencing flows that need one marker pulse per
four qualifying analog clock edges.
- Form: `dut`
- Level: `L1`
- Category: `measurement_instrumentation_flows`
- Target artifact(s): `two_bit_counter_marker.va`

The module must be named `two_bit_counter_marker` and use this port order:

`CLKIN, MC`

Initialize the counter and marker low. On each rising crossing of `CLKIN`
through 0.5 V, increment a modulo-four counter. Drive `MC` to 1.0 V only on the
edge that wraps the counter from 3 back to 0, and drive `MC` to 0.0 V on all
other counted edges.

## Public Verilog-A Interface

The file `two_bit_counter_marker.va` must define `module two_bit_counter_marker(CLKIN, MC);`. Both ports are electrical. `CLKIN` is the counted input clock and `MC` is the voltage-coded marker output.

## Public Parameter Contract

This task has no public parameters.

## Required Behavior

Implement a modulo-four edge counter marker for timing/readout sequencing.
Initialize the internal counter and `MC` low. On each rising crossing of
`CLKIN` through 0.5 V, increment the counter modulo four. Drive `MC` high as a
1.0 V voltage-coded marker only on the edge that wraps the count from 3 back to
0; keep it at 0.0 V on the other counted edges.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `two_bit_counter_marker.va`. Do not include explanatory prose outside the source artifact contents.
