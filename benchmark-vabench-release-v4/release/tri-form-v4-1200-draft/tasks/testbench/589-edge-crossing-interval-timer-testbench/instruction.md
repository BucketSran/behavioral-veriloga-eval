# Edge Crossing Interval Timer Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Edge Crossing Interval Timer` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `cross_interval_163p333_ref.va`:
  - Module `cross_interval_163p333_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `a` (input, electrical)
    - position 3: `b` (input, electrical)
    - position 4: `delay_out` (output, electrical)
    - position 5: `seen_out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cross_interval_163p333_ref` as `XDUT` with ordered public binding: VDD=vdd, VSS=vss, a=a, b=b, delay_out=delay_out, seen_out=seen_out.

## Public Parameter Contract

- `cross_interval_163p333_ref.vth` defaults to `0.45` V; valid range: finite real within the VSS-to-VDD logic range; sets rising-edge thresholds for a and b relative to VSS.
- `cross_interval_163p333_ref.scale_ps` defaults to `200.0` ps; valid range: scale_ps > 0; sets measured-delay normalization for delay_out.
- `cross_interval_163p333_ref.tedge` defaults to `2e-11` s; valid range: tedge > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_A_EDGE_ARMS`: exercise and make observable: A rising a crossing arms a fresh measurement and clears seen_out until completion. Required traces: `time`, `a`, `seen_out`.
- `P_FIRST_B_EDGE_CAPTURES`: exercise and make observable: The first rising b crossing after an armed a edge captures their elapsed time; b edges before arming do not complete a measurement. Required traces: `time`, `a`, `b`, `delay_out`, `seen_out`.
- `P_DELAY_NORMALIZATION`: exercise and make observable: Delay_out equals the VDD-to-VSS rail span multiplied by measured delay in picoseconds divided by scale_ps. Required traces: `time`, `vdd`, `vss`, `a`, `b`, `delay_out`.
- `P_COMPLETION_MARKER`: exercise and make observable: Seen_out is rail-high after a valid a-then-b capture and rail-low while a newly armed measurement is incomplete. Required traces: `time`, `vdd`, `vss`, `a`, `b`, `seen_out`.
- `P_SINGLE_CAPTURE_PER_ARM`: exercise and make observable: Additional b crossings after completion do not change delay_out until the next rising a edge rearms the timer. Required traces: `time`, `a`, `b`, `delay_out`, `seen_out`.

The required trace names are: `time`, `vdd`, `vss`, `a`, `b`, `delay_out`, `seen_out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
