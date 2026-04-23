Given a voltage-domain NRZ PRBS source DUT, generate a minimal EVAS-compatible
Spectre-format `.scs` testbench that can expose jittered bit transitions and burst gaps.

Requirements:

1. Provide `VDD`, `VSS`, and a clock source
2. Include an `enable` stimulus with at least one on/off burst window
3. Instantiate the DUT by position
4. Include `tran`
5. Include explicit `save` for `clk`, `enable`, `sout_p`, `sout_n`
6. Place `ahdl_include` last

Ports:
- `vdd`: inout electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `enable`: input electrical
- `sout_p`: output electrical
- `sout_n`: output electrical

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`

DUT module to instantiate: `nrz_prbs_jitter_ref`
