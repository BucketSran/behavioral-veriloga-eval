Given a voltage-domain timer-based DCO DUT, generate a minimal EVAS-compatible
Spectre-format `.scs` testbench that applies a control-voltage step and saves
the control and clock waveforms so frequency change can be measured before and
after the step.

Requirements:

- provide `VDD`, `VSS`, and a `vctrl` stimulus
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `vctrl`: input electrical
- `vout`: output electrical

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`

DUT module to instantiate: `dco_gain_step_ref`
