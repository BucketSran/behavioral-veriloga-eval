# Prompt Hygiene Audit

Date: 2026-04-27

Scope: active `tasks/**/prompt.md` files.

Goal: adopt the generic prompt wording policy and remove failure-sample-specific
negative examples from official prompts.

## Adopted Policy

Official prompts may state public interface, artifact, and simulator dialect
requirements, but should avoid concrete negative examples copied from a failed
model output.

Accepted wording style:

- `Use Spectre-compatible Verilog-A syntax.`
- `Use Spectre-compatible netlist syntax for module instantiation.`
- `Use plain scalar save names.`
- `Expose every required public waveform column under the scalar names listed.`

Avoided wording style:

- Naming a specific bad model output pattern.
- Listing exact syntax mistakes as examples unless they are part of the task
  specification itself.
- Adding helper modules or stimulus generators that prescribe a concrete
  validation strategy beyond the public task interface.

## Prompt Changes

| Task | Before | After |
|---|---|---|
| `gain_extraction_smoke` | Specific named-port negative example in Spectre testbench guidance | Generic `Spectre-compatible netlist syntax` wording |
| `segmented_dac` | Specific integer bit-slice negative examples | Generic `Spectre-compatible Verilog-A syntax for scalar integer arithmetic and data-bit decoding` |
| `sar_12bit` | Specific block-scoped loop-declaration negative example | Generic declaration/loop/event syntax wording |
| `digital_basics_smoke` | Specific digital-Verilog construct examples and instance/save negative examples | Generic Spectre-compatible Verilog-A and instance/save syntax wording |
| `d2b_4bit_smoke` | Specific digital-Verilog construct examples | Generic pure Spectre-compatible Verilog-A syntax wording |
| `dwa_wraparound_smoke` | Specific vector CSV header examples | Generic vector-indexed CSV header wording |
| `dwa_ptr_gen_no_overlap_smoke` | Specific vector CSV header examples | Generic vector-indexed CSV header wording |
| `timer_absolute_grid_smoke` | `gold testbench` wording | `public evaluation testbench` wording |
| `sc_integrator` | Specific Verilog `initial begin` negative example and one corrupted edge-detection line | Generic Spectre-compatible initialization/event/cross-event syntax wording |
| `adpll_timer` | Specific Verilog `initial begin` negative example | Generic Spectre-compatible initialization/event syntax wording |
| end-to-end prompts with active-low reset contract | Specific reset-name examples (`rstb`, `rst_n`, `rst_ni`) | Generic `active-low reset inputs` wording |

## Static Check

After cleanup, this scan has no active hits:

```bash
rg -n 'named port syntax|digital Verilog constructs|gold testbench|code\\[[0-9]|\\.clk\\s+clk|for \\(integer|ref_step_clk|bsource|Strict EVAS|injected|Do not use Verilog `initial begin`|packed-vector|bit-slice' tasks --glob prompt.md -S
```

The remaining `such as` hit is intentionally task-specific stimulus coverage:

- `tasks/tb-generation/voltage/segmented_dac_glitch_tb/prompt.md`: boundary
  transitions such as `3->4`, `7->8`, and `11->12`.

## Validation Note

The generic wording probe is recorded at
`results/A-linkage-promptfix-generic-kimi-2026-04-27`. It showed that cleaner
wording can reduce pass rate versus concrete negative examples, so the official
prompt policy favors hygiene and fairness over maximizing this local probe.
