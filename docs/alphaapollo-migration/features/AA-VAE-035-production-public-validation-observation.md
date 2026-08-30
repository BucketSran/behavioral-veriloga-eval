# AA-VAE-035：Production public EVAS observation

## 功能标识与思想来源

- 日期：2026-08-30；负责人：main coordinator。
- 状态：opt-in 环境 API 已实现；单任务 Docker / 原生 trajectory 接入已验证。
- 来源：沿用 AA-VAE-020/029 中已讨论的 AlphaApollo 式公开反馈驱动推理、
  validation/final authority 分离，以及 mini-swe 的隔离执行环境。本切片没有复制新的
  外部代码、安装依赖或新增模型工具。
- 我们的适配推断：反馈不仅要有文字，还必须能回答“哪个 attempt 的哪个候选，在什么
  冻结配置下执行，实际发生了几次调用”。这不是 AlphaApollo 已替我们解决的保证。

## vaEVAS 适配决策

复用现有 `VaBenchBashEnvironment.execute`，仅执行 r53 DUT/bugfix 公共契约声明的
固定 EVAS 命令。生产调用要求 Docker；非隔离路径仅允许显式测试 override。
不使用会读取 evaluator 的历史 `feedback_adapter` / `feedback_oracle`。

当前能力是公开 **simulation diagnostics**，不是行为正确性 checker。返回进程状态、
退出码、耗时、截断日志及哈希；没有 `passed`、task score 或私有 fault 结果。
Testbench reference-only 合同尚不支持，遇到它明确拒绝，不能回退到私有 checker。

## 代码框架与改动

| 文件 / 符号 | 改动 | 层 |
| --- | --- | --- |
| `operations/calibration_pilot/public_validation.py::build_public_validation_profile` | 绑定 r53 manifest、campaign identity、公开输入/命令、候选声明、EVAS 0.8.7 身份、镜像、限制及适配器源码 | environment / authority |
| `public_validation.py::PublicEvasValidator` | 执行前后检查 candidate / authority，拒绝终评冻结后重入，形成 canonical Observation | environment |
| `mini_swe_vabench.py::inspect_public_evas` | 在实际 sandbox 中探测 EVAS 身份，不伪造模型工具调用计数 | runtime |
| `tests/test_agent_harness_production_public_validation.py` | 真实子进程、漂移/终止/资源/调用记录回归，test-only controller bridge，r53 Docker smoke | tests |
| `.github/workflows/evaluator-closure.yml` | 增加 adapter / mini-swe 触发路径，镜像构建后运行原生公开反馈 smoke | CI |

前三行路径前缀为 `benchmark-vabench-release-v4/`。没有修改 generic controller、
Observation schema、release 或 EVAS。

## 数据与状态变化

`冻结 profile → 校验公开输入/候选 → sandbox EVAS → 复核身份与调用证据
→ canonical Observation → controller budget / trajectory gate`

- 候选哈希使用现有 submission freeze 的 canonical 文件列表格式；拒绝未声明的
  submission 文件，避免 helper 文件参与执行却未参与绑定。
- 旧 EVAS telemetry 使用另一种 length-framed 哈希。Observation 显式记录其 schema 和
  digest，不把它和 canonical candidate hash 当作同一种值。缺失、错误哨兵或未知 schema
  均拒绝；主绑定依据仍为 canonical 执行前后检查。
- profile/input identity 同时绑定 attempt/task；profile 被复制冻结，不受 caller mutation
  影响。资源超限、候选/公开输入漂移或缺失调用证据不会成为成功反馈。
- contract failure 使本 adapter 实例失效；调用方必须放弃该 attempt。持久化崩溃恢复和
  跨实例重试 coordinator 尚未完成，不能用重建 adapter 绕开这一规则。
- 预算仍由 controller / campaign 所有，adapter 不引入第二套账本。测试在实际调用一次后
  请求第二次，证明 `public_validation_calls=1` 会在 dispatch 前拒绝。
- `evidence/final_submission`、`evidence/bound-final-test` 或 submit sentinel 存在时，
  不再公开执行；final score 从未进入本 adapter。

## 验证证据

- TDD：先观察缺失模块及边界回归失败，再实现；独立审查发现未声明 helper 漏绑，新增
  RED 测试并修复。资源超限、失败后恢复字节重用 adapter、错误 telemetry 亦有 RED/GREEN。
- 真实 subprocess 覆盖成功、非零退出、超时、截断、候选/公开配置漂移、终评门、缺失调用。
- r53 `v4-001` Docker smoke 使用仅从公开合同构造的不完整 DUT，无模型 API、无私有
  evaluator export。原生 trajectory 哈希链/语义检查通过；公开候选哈希与 freeze 一致；
  第二次 validation 因预算拒绝；freeze 后调用被拒绝。此 smoke 不执行 final judge。
- 测试命令、统计和外置 evidence/hash 见 `logs/verification-log.md`。

## Claim boundary 与保留缺口

可以主张 opt-in public simulation → candidate/profile-bound Observation → 原生
controller trajectory 的单任务接入成立。不能主张模型表现提升、论文 baseline 复现、
全 form 支持、完整 trajectory 内容存储、生产 campaign 默认切换或 full Phase 5 closure。

`run_evas` descriptor 只在测试桥中使用，未注册进生产模型 tool inventory；mini-swe
默认 Bash 路径保持不变，domain tools 仍暂缓。新的 API 与既有 final receipt 还没有通过
真实模型 campaign 的 typed result ledger 连成一条完整链。

可信 coordinator 负责证明输入来自封存 release、campaign 在生成前冻结，以及独占
environment。profile 记录观测到的公开文件和 manifest，不独立认证导出来源；runtime
fingerprint 也不是任意依赖/文件访问的完整闭包。wrapper nonce 使其成为 attempt-runtime
身份，不能当成跨 attempt 的 matched-config hash。前后哈希不是敌对并发修改/回滚的
安全证明。EVAS 仍固定 0.8.7，Spectre 不触发。
