# Real-model workflow differential and tool diagnostic

Date: 2026-09-01. This is a sanitized single-family engineering diagnostic,
not a formal r53 benchmark result or a reproduction of the paper baseline.

## Frozen scope and spending

- Run source: `cce382d93bbc20baa554aaa090b2fe2554c0ed39` on fork `main`.
- Fixed assets: sealed r53, EVAS 0.8.7, Docker image
  `sha256:fe44bb54370160ee99bef939ae67a0ab1f51fb3b9a41d3d0c4cf29e7ea38115b`
  and no-EVAS branch image
  `sha256:8da5b17c97a6d5f3a9b7685d57e6643ca083ad488cda05ecb75b8115392ab124`.
- Provider contract: `deepseek-v4-flash`, documented
  `DeepSeek-V4-Flash-0731`, temperature 0, thinking disabled, 4,096 output
  tokens. The alias is not an immutable model snapshot.
- User ceiling: CNY 30.00. Frozen guard ceilings: CNY 5.00 for Study 1 and
  CNY 5.00 for each of four Study 2 roots, totaling CNY 25.00. The remaining
  CNY 5.00 was not allocated to retries or additional conditions.
- Sum of known conservative peak/cache-miss guard upper bounds: **CNY
  2.979222**. This is not a provider invoice or account-billing statement.
- Private raw output remains in the ignored local directory
  `benchmark-vabench-release-v4/reports/real-model-studies-20260901T0648Z/`.
  No credential, prompt, raw response, candidate, waveform or trajectory is
  committed.

## Study 1: legacy versus native mini-swe

The fixed schedule contains family001 DUT, bugfix and Testbench under both
backends. One shared guard and one-use execution were used; no outcome-driven
retry or task replacement occurred.

| Form | Backend | Disposition | Logical model calls | Guard upper bound (CNY) | EVAS score |
| --- | --- | --- | ---: | ---: | ---: |
| DUT | legacy | completed | 10 | 0.316230 | 1.0 |
| DUT | native-mini-swe | completed | 14 | 0.469701 | 1.0 |
| bugfix | native-mini-swe | completed | 10 | 0.348294 | 1.0 |
| bugfix | legacy | completed | 13 | 0.584442 | 1.0 |
| Testbench | legacy | budget-censored before the next reservation | 9 | 0.100581 | null |
| Testbench | native-mini-swe | not started after shared stop | 0 | 0.000000 | null |

The reader records 55 potentially billable transport attempts. The next
worst-case reservation was CNY 3.182592; adding it to the already committed
upper bound would exceed the CNY 5.00 root cap, so the guard stopped before
transport. The six scheduled rows remain in the denominator.

The two complete pairs have matched audited public/runtime surfaces and equal
scores. DUT native-minus-legacy score delta is 0.0, with guard-bound delta
`+0.153471`; bugfix score delta is 0.0, with guard-bound delta `-0.236148`.
Testbench has no complete pair. This supports bounded compatibility evidence
for two forms only; it does not prove backend equivalence or quality parity.

## Study 2: Reasoning/Evolution × baseline/RAG-waveform

All four roots use family001 DUT. Baselines require zero public-tool use;
tool-enabled conditions require complete successful use, and Evolution also
requires candidate-bound waveform feedback to reach a later model request.

| Cell | Backend / intervention | Score | Calls | Guard upper bound (CNY) | Condition acceptance |
| --- | --- | ---: | ---: | ---: | --- |
| A | Reasoning / baseline | 1.0 | 6 | 0.168342 | passed |
| B | Reasoning / RAG-waveform | 1.0 | 7 | 0.242328 | failed: neither tool was called |
| C | Evolution / baseline | 1.0 | 21 | 0.502428 | passed; 4/4 branch-round records |
| D | Evolution / RAG-waveform | 1.0 | 13 | 0.246876 | failed: incomplete round-0 waveform evidence |

Raw score differences are B−A = 0, D−C = 0, C−A = 0, D−B = 0 and the
descriptive interaction is 0. These zeros do **not** establish zero tool
effect: B never used either enabled tool, while D made no documentation query
and has no public-waveform receipt for either round-0 branch. The two round-1
receipts occur too late to establish next-round feedback exposure. C versus A
and D versus B are also not compute-matched backend effects.

The practical finding is that family001 was easy enough for all completed
final submissions to pass with Bash alone. This run validates real provider,
candidate, freeze and EVAS joins, but it does not validate tool utility or
natural tool adoption. A later utility study needs a separately preregistered
task-selection rule and must distinguish optional natural use from a forced-use
connectivity test.

## Reporter defect exposed without rerun

Cell D completed Evolution, final freeze and EVAS trusted replay, but the live
command initially exited while producing its read-only report: incomplete
waveform evidence yielded `feedback_exposed_requests=null`, and the acceptance
expression compared it directly with zero. Commit `7f1c2ed3ee` makes this path
fail closed to `condition_acceptance_passed=false` while preserving score 1.0
and all incomplete-evidence details. It was verified against the existing
immutable D evidence; no model, public validator or final judge was rerun.

## Evidence bindings

| Root | Manifest SHA-256 | Raw execution-log SHA-256 | Budget SHA-256 |
| --- | --- | --- | --- |
| Study 1 | `bd9bd1eedb9127919299ebd698cf8c4f301f889d37d25f9cb2e0cf0c1b24a8b6` | `3a0daa7d802d549d0003ab9db28baa34771a24f7183919dd6574f0e89448f16a` | `6785b69c938950fd17b20d5186cc51d121944a43e7a51d94dde7c2ac72b64405` |
| A | `110d9ef2871a9a59d00c778a7e4049620e11f17bbce669fc6ba66cfdbcf16d8f` | `56f130cde4485978e6e5de31385f2d2d97348b61463102a7b480d1177359df89` | `9ac9321bb3fad757dd6337ddc67031a9ee474e6cdd4f58cac9f30f4c38cfde6d` |
| B | `63f26ead7e1ad541b1b2c458dd50dbafe7d43af36b0481a5ec0f3ef999d971f1` | `0dff61861d0412c99eb653ada2f907eefcbcc4c04f6b638249d7d25e461ad607` | `fd85ba2e743de6bddf9ca3714d343eef83bc23255790cd1b82f87e90b0efb7f6` |
| C | `3c888e9381349514e170a67503a0776d3e68dd10fbbdbf7fd4b4d19d508dd747` | `4379d358ebe63952dd982b96421d8eda2bd4216edcb7259d96c350f220c46b61` | `186d656fbc0141cbab72589ebcbb5e4b75431a3972555efd2260ad817bb73dbc` |
| D | `420935f0f4625bb7056d0f8d9c7e330c5109996bc6793e3a5e0f74ef9d8e421b` | `5a02127dac975372c810de3b957b12e1a032f9c1b11b6190683281a5277212b6` | `964871355f8b0545eeafa7f027b15a260ee6b8c25ef56e4973ef38383fbe4d82` |

Study 1 derived comparison-execution SHA-256 is
`b445fdbbb36bebc1cca5751caa2ecc4cd0519c3e491fed96ad97dbc4d8e3b407`.
Evolution final-result SHA-256 values are
`05f8a592b949b511d7e948c63efa63a5b1132c6ac7dbd8bf22477d6a1ca6dea4`
for C and
`c703434f9499159fe8bfdf82b50a973578410dc5997780405da323bde6554501`
for D.

D's fail-closed acceptance was re-read with
`run_combined_tools.py report --output-root .../study2-D-evolution-rag-waveform`;
the command validates existing receipts only and does not rerun the model,
public validator or final judge.

## Next evidence decision

Do not spend the unused authorization on a replacement row. The next decision
is methodological: either run a new larger-cap six-cell completion campaign,
or preregister a harder multi-family tool-utility study with explicit natural-
use versus forced-use estimands. The present data justifies neither a harness
superiority claim nor further feature expansion by itself.
