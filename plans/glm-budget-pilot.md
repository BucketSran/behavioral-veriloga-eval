# GLM-first bounded API pilot

Updated: 2026-08-30. Base: `2aea03a828fa62d4b979929827c86692576f548d`.
Status: preparation only; platform confirmation and verified live execution
remain open. No authenticated provider request has been made.

## Brief and acceptance

The user has saved both provider keys and now prioritizes GLM. This supersedes
the DeepSeek-first launch choice in [the earlier pilot plan](deepseek-budget-pilot.md),
not its historical tests or selection evidence. Do not fall back to DeepSeek
automatically. The existing CNY 5 ceiling remains unchanged; no automatic
recharge, subscription use, GPU rental or benchmark expansion is authorized.

Acceptance remains six scheduled cells with complete started/censored/not-started
accounting, private trajectories and immutable EVAS evidence for eligible
submissions. Model quality is not a pass/fail acceptance gate.

Keep seeded family `029`: `v4-029` DUT, `v4-1029` bugfix and `v4-529` Testbench.
Use separate matched Agentic campaigns for native mini-swe and native Reasoning,
one repetition, one fresh attempt, one active cell globally and at most eight
logical calls per cell. Retain the planned 4096-output cap and r53 wall-time
policy. Freeze exact alternating order before generation. This family becomes
development/calibration exposure; no score-driven retry or selection changes.
Keep r53, EVAS 0.8.7, legacy defaults and final-feedback isolation unchanged.

## Provider choice is still conditional

Official sources checked on 2026-08-30:

- [BigModel GLM-4.7-Flash model card](https://docs.bigmodel.cn/cn/guide/models/free/glm-4.7-flash)
  documents native Function Calling, streaming, 200K context and 128K output.
- [BigModel model overview](https://docs.bigmodel.cn/cn/guide/start/model-overview)
  lists GLM-4.7-Flash among free text models.
- [Z.ai ordinary API pricing](https://docs.z.ai/guides/overview/pricing)
  lists input, cached input, storage and output for GLM-4.7-Flash as free.
- [Chat API](https://docs.z.ai/api-reference/llm/chat-completion) and
  [streaming contract](https://docs.z.ai/guides/capabilities/streaming)
  describe native tools, thinking options and terminal usage.

Proposed initial model: `glm-4.7-flash`, with explicitly disabled provider
thinking, native tools and no paid built-in search. A requested model alias is
not an immutable serving snapshot. Bind the observed response identity too.
The higher-level Reasoning backend does not require hidden provider thinking.

The key's platform is not known from its variable name. Confirm whether it is
BigModel ordinary API, GLM Coding Plan or Z.ai before sending credentials.
BigModel and Z.ai ordinary endpoints are respectively:

- `https://open.bigmodel.cn/api/paas/v4/chat/completions`
- `https://api.z.ai/api/paas/v4/chat/completions`

Coding Plan routing/subscription quotas are not the ordinary token-billing
contract. Do not substitute its endpoint or assume a CNY spending cap applies.
Do not try the same key against several guessed platforms. Recheck the selected
platform's rate/model contract before launch; do not silently use paid FlashX
or another model if free Flash is unavailable. Free pricing is a documented
rate, not proof of this account's access or a measured zero-cost invoice.

## Safe local credential preparation (AA-VAE-051)

`operations/calibration_pilot/pilot_credentials.py::load_pilot_key` reads the
user-named external two-key template as literal data. It returns only the
selected field; it never sources the file or exports either key to environment
variables. It checks a bounded regular file, owner-only POSIX permissions and
owner identity, and rejects final-component symlinks and malformed values.

The normal `--api-key-file` argument still expects one raw key. Do not pass the
shared two-key template to it. The helper is not yet wired to a live pilot CLI;
credentials remain outside Git, prompt/model data and sandbox environments.
Its local-only tests do not establish API authentication or compatibility.

## Remaining launch gates

1. Confirm the key's platform without asking the user to disclose the key.
2. Adapt the existing pilot budget/capture seam to that exact GLM endpoint,
   model, mode, rates and terminal usage. Preserve the tested DeepSeek path;
   avoid a new controller or duplicated accounting loop. Verify actual payload
   and stop behavior with free fixtures before a real provider call.
3. Implement a minimal serial six-cell driver using the existing builder and
   native dispatch. Preserve all scheduled rows, including not-started budget
   stops, in a separate pilot index. Do not synthesize scored results or shrink
   the denominator to satisfy the normal native scorer.
4. Bind code/image/release/model/rates/mode/order/limits in fresh manifests.
   Old DeepSeek dry-run roots and spending journals are not resumable live runs.
5. Verify the provider boundary and actual Docker/EVAS evidence chain, obtain
   independent review, then execute within the frozen limits. Every diagnostic
   model call must be accounted separately and must not receive hidden assets.

When terminal usage/accounting or provider identity is ambiguous, stop before
another HTTP attempt. Unknown usage stays unknown even for an advertised free
model. Keep candidate failure distinct from operational censoring. No Evolution,
full-r53 run, Spectre, domain/RAG tool or model-quality claim is enabled here.
