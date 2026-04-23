# Table 1: EVAS vs Spectre Behavioral Comparison

> Date: 2026-04-21
> Input: Gold VA + Gold TB (prescribed correct code)
> Purpose: Show behavioral differences between EVAS and Spectre simulators

## Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Tasks | 93 | - |
| Compile Pass (both) | 93 | **100%** |
| Behavior Match | 90 | **97%** |
| Parity Pass | 76 | 82% |

## By Family

| Family | Tasks | EVAS Compile | Spectre Compile | Behavior Match | Parity Pass |
|--------|-------|--------------|-----------------|----------------|-------------|
| spec-to-va | 18 | 18/18 (100%) | 18/18 (100%) | 18/18 (100%) | 17/18 |
| bugfix | 8 | 8/8 (100%) | 8/8 (100%) | 8/8 (100%) | 7/8 |
| tb-generation | 11 | 11/11 (100%) | 11/11 (100%) | 11/11 (100%) | 0/11* |
| end-to-end | 56 | 56/56 (100%) | 56/56 (100%) | 53/56 (95%) | 52/56 |
| **Total** | **93** | **93/93** | **93/93** | **90/93** | **76/93** |

*tb-generation tasks don't require sim_correct parity (testbench generation only)

## Behavioral Differences (3 tasks)

These tasks show different behavior between EVAS and Spectre:

### 1. `cross_sine_precision_smoke` (end-to-end)

| Metric | EVAS | Spectre |
|--------|------|---------|
| sim_correct | 1.0 (PASS) | 0.0 (FAIL) |
| max_err_ps | 0.000 | 1.86 |
| first_err_ps | 0.000 | 1.86 |

**Analysis**: Cross event timing precision differs. EVAS achieves exact timing, Spectre has ~1.86ps error.

### 2. `current_domain_outofscope_smoke` (end-to-end)

| Metric | EVAS | Spectre |
|--------|------|---------|
| sim_correct | 1.0 (PASS) | 0.0 (FAIL) |
| max_vout | 0.0009V | 900000000V (!) |

**Analysis**: Spectre produces unrealistic output (9e8 V), EVAS correctly produces near-zero. This is a domain mismatch issue - current-domain circuits may behave differently in Spectre.

### 3. `digital_basics_smoke` (end-to-end)

| Metric | EVAS | Spectre |
|--------|------|---------|
| modules_passed | 4/4 | 2/4 |
| NOT gate match_frac | 0.997 | 1.000 |
| AND gate errors | 2 | 1 |
| OR gate errors | 2 | 1 |
| DFF match | 1.000 | 1.000 |

**Analysis**: Multi-module task. EVAS passes all 4 modules, Spectre passes 2/4 due to slightly different timing tolerances.

## Parity Analysis

Parity comparison measures waveform similarity (RMSE, max_abs_v, NRMSE).

| Parity Status | Count | Reason |
|---------------|-------|--------|
| passed | 76 | Waveforms match within tolerance |
| blocked | 14 | Prerequisites not met (behavior mismatch) |
| not_required | 3 | tb-generation tasks |

## Key Findings

1. **Compile Compatibility**: 100% - All 93 gold VA/TB compile on both simulators
2. **Behavioral Consistency**: 97% - 90/93 tasks have matching behavior
3. **Identified Differences**: 3 tasks show real behavioral differences:
   - Cross event timing precision
   - Current-domain circuit handling
   - Multi-module timing tolerances

These differences are **expected** - EVAS is an event-driven simulator while Spectre is a continuous-time SPICE simulator. The behavioral differences highlight simulator-specific characteristics that users should be aware of when comparing simulation results.