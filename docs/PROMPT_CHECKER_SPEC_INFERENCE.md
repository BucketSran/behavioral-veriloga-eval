# Prompt Checker Spec Inference

This document describes the advisory prompt-to-checker-spec flow implemented in
`runners/infer_prompt_checker_specs.py`.

## Purpose

The flow answers this question:

```text
Given a public task prompt, what mechanism-level checker templates should a
repair loop consider before asking a model to change behavior?
```

It does not replace official `sim_correct` checkers. It produces structured
specs that can guide contract generation, repair prompts, and future streaming
checker work.

## Method

The recognizer uses deterministic rules:

1. Extract public signals from prompt backticks, port lists, and gold testbench
   save names.
2. Map signal names to roles such as clock, reset, reference clock, feedback
   clock, lock, up/down pulse, code bits, analog input, and analog output.
3. Lift prompt language into a compact functional IR before final template
   routing. Example claims include:
   - `code_to_analog_transfer`
   - `ordered_transfer`
   - `count_high_to_analog`
   - `quantized_encoding`
   - `sample_on_clock_edge`
   - `data_clock_lead_lag_pulses`
   - `one_bit_adjacent_transition`
   - `frame_aligned_serial_sequence`
   - `parameterized_repetition`
4. Detect mechanism families from prompt language plus functional-IR claims:
   - `quantized_reconstruction`
   - `monotonic_code_vs_input`
   - `dac_code_to_output_span`
   - `thermometer_dac_code_to_output_span`
   - `counter_cadence`
   - `gray_counter_sequence`
   - `paired_edge_response`
   - `bbpd_data_clock_lead_lag`
   - `pulse_non_overlap`
   - `absolute_event_window`
   - `timer_future_event_liveness`
   - `ratio_edge_window`
   - `lock_after_ratio_stable`
   - `calibration_settling_code`
   - `differential_code_response`
   - `sample_hold_tracking`
   - `droop_window`
5. Extract lightweight parameters such as bit width, divide ratios, pulse/toggle
   mode, public transient settings, and timer target times.
6. Adopt only specs that pass the validation-set expectation and meet the
   confidence threshold.

The recognizer also includes lightweight robustness guards: whitespace
normalization, fuzzy word matching for minor typos such as `monotocin` for
`monotonic`, prefix/alias matching for buses such as `dinp[9:0]`, and negation
checks so phrases such as "not a thermometer DAC" or "no parameter override" do
not trigger the positive mechanism.

The functional IR is the main difference from simple keyword matching. A prompt
does not need to contain the exact word `monotonic`; a sentence such as "if one
input word represents a greater integer than another, the produced voltage must
not be lower" is lifted to `ordered_transfer`, which can then trigger the DAC
code-to-output template.

## Adoption Rule

Adoption is intentionally conservative:

```text
adopted = confidence >= 0.70 and validation task matched
```

High-confidence specs for unvalidated tasks are reported, but not written into
`docs/PROMPT_CHECKER_SPECS_ADOPTED.json` unless explicitly allowed in a future
experiment.

## Reproduce

Validated task set:

```bash
python3 runners/infer_prompt_checker_specs.py \
  --output-dir results/prompt-checker-spec-inference-expanded-2026-04-27 \
  --adopted-out docs/PROMPT_CHECKER_SPECS_ADOPTED.json \
  --adopt-threshold 0.70
```

All-task scan without adopting unvalidated specs:

```bash
python3 runners/infer_prompt_checker_specs.py \
  --all \
  --output-dir results/prompt-checker-spec-inference-functional-ir-2026-04-27-v1 \
  --adopted-out docs/PROMPT_CHECKER_SPECS_ADOPTED.json \
  --adopt-threshold 0.70
```

Use adopted specs during behavior-contract generation:

```bash
python3 runners/generate_behavior_contracts.py \
  --triage-json results/behavior-contract-triage-H-on-F-stable-2026-04-26.json \
  --out-root results/generated-behavior-contracts-promptdriven-full-2026-04-27 \
  --prompt-specs docs/PROMPT_CHECKER_SPECS_ADOPTED.json
```

Important: contract generation does **not** look up `task_id -> adopted spec`.
For each task it reads the task prompt and runs prompt inference live. The
adopted specs file is used only as a validated mechanism-template catalog and
confidence threshold, so a mechanism must be triggered by the prompt text rather
than by a benchmark name.

The broader contract generator follows the same direction for mechanism-family
rules: PFD/PLL/ADC/Gray/differential-DAC branches use prompt text and public
signal roles rather than benchmark-name substrings wherever possible. `task_id`
remains a filesystem/result key and official-checker lookup key, not behavioral
evidence.

## Current Result

Validation-set result:

```text
tasks=92
validated_tasks=59
validation_matches=59
mechanism_match_rate=1.000
adopted_specs=59
```

Mechanism generalization benchmark:

```text
total_cases=19
pass_cases=19
pass_rate=1.0000
functional_paraphrase=5/5
functional_negative_control=1/1
```

Behavior contract generation:

```text
prompt_specs_loaded=59
prompt_spec_mode=live_prompt_inference_with_adopted_template_catalog
generated_tasks=31 on current H-on-F failed/diagnostic tasks
total_contracts=240
tasks_with_prompt_templates=24
```

The remaining low-confidence/no-template tasks are not adopted. They need future
mechanism labels before prompt-derived specs should guide repair.
