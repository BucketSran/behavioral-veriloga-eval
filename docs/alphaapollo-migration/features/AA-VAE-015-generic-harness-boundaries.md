# AA-VAE-015：通用 agent harness 边界原型

## 功能标识

- ID：`AA-VAE-015`
- 名称：通用 controller / environment / state / trajectory 边界
- 状态：契约原型已验证，尚未接入 production runner
- 日期：2026-08-29

## 思想来源

- AlphaApollo 的公开思想：一次求解是模型动作与环境反馈交替形成的完整
  trajectory，公开 verifier 反馈可用于同一题内的后续改进。
- coding-agent 的公开共同模式：模型只产生结构化 action；environment 拥有
  workspace、tool execution、budget 和终止状态；controller 记录有序
  Action/Observation 事件。
- vaEVAS 的额外约束：公开 validation 与最终 judge 权限不对称；final judge
  只能读取冻结 submission，返回值不能成为下一次 policy observation。
- 本功能只迁移上述公开架构思想，没有复制 AlphaApollo、OpenHands、SWE-agent、
  Aider 或 Codex CLI 的实现代码，也没有新增外部 runtime 依赖。

## vaEVAS 适配决策

- 采用版本化 JSON action/observation 对象，显式记录 action、tool、backend、
  candidate、payload 和 budget identity，并对参数与公开 payload 做规范化哈希。
- `PublicValidator` 是 environment 内部的 model-visible 服务；其结果可作为下一轮
  `Observation`。`FinalJudge` 是 submission freeze 之后的 terminal-only 服务；其
  `FinalJudgment` 必须绑定同一个 submission tree hash。
- controller 把 protocol、environment/backend/judge infrastructure、step budget 和
  cleanup failure 分别物化为结果或 incident；普通失败不再从 episode 边界裸抛。
- frozen submission 会校验 tree hash 并把 artifact 集合固化为不可变 tuple；trajectory
  事件显式标注 `model`、`harness` 或 `trusted` visibility，model-memory projection
  只接纳 `model` 事件。
- 保留 attempt lineage 和 append-only SHA-256 trajectory chain。
- 暂不接入现有 mini-swe、campaign 或 scorer；这一步只解决暂停 prototype 的去留与
  契约边界，生产兼容由后续独立提交完成。
- 暂不实现 waveform、RAG、candidate-edit 等 vaEVAS 领域工具；只为后续 capability
  registry 留出设计空间。

## 代码改动与模块去留

| 文件/符号 | 去留与改动 | 所属层 |
| --- | --- | --- |
| `runners/agent_harness/contracts.py` | 保留并重构；拆分 `PublicValidator` 与 `FinalJudge`，保留 policy/environment/trajectory protocol | harness |
| `runners/agent_harness/state.py` | 保留并重构；用 `vaevas-action-v1`、`vaevas-observation-v1`、`FinalJudgment`、`FailureDisposition` 替代弱字符串状态 | state |
| `runners/agent_harness/trajectory.py` | 保留；继续提供 attempt-scoped JSONL 与 tamper-evident event chain | trajectory |
| `runners/agent_harness/controller.py` | 保留并重构；final judge terminal-only，增加 submission binding 和分类失败结果 | harness |
| `runners/agent_harness/__init__.py` | 保留；只导出已验证的公共契约 | harness |
| `tests/test_agent_harness_controller.py` | 保留并扩展；锁定反馈可见性、freeze、失败分类、cleanup、lineage 和 event chain | tests |

`rg` 检查确认当前 production runner 没有导入该 package，因此本提交不会改变现有
r53、mini-swe 或 EVAS 0.8.7 执行路径。

## 数据与状态变化

- 输入：`EpisodeContext`、model-visible `Observation`、backend 生成的
  `AgentAction`。
- 中间状态：environment step、candidate binding、budget delta、attempt-scoped
  trajectory event。
- 输出：成功时为 frozen submission 加 hash-bound `FinalJudgment`；失败时为
  classified `FailureDisposition`，cleanup 仍作为独立 incident。
- 新增协议身份：`vaevas-action-v1`、`vaevas-observation-v1`。
- backward compatibility：尚未承诺 production compatibility；mini-swe adapter 在
  接入前必须用 deterministic fixture 证明旧、新路径等价。

## 验证证据

- RED：缺少 `FinalJudgment`/`PublicValidator`、弱字符串 action、裸抛 protocol 与
  environment failure、未分类的 max-step exhaustion、未校验 submission binding、
  可变 frozen artifacts、final-event visibility 泄漏和空 episode identity 均由独立
  回归先行暴露。
- GREEN：`tests/test_agent_harness_controller.py` 覆盖 18 个公共行为测试。
- clean-room smoke：未执行；本 prototype 尚未进入 formal runner，不能用既有 smoke
  证明新 runtime 行为。
- 未验证部分：production mini-swe adapter、capability registry、正式 JSON schema、
  public EVAS adapter、final-score coordinator、AlphaApollo reasoning/evolution。

## Claim boundary

- 能支持：prototype 层面的 Action/Observation 分离、公开反馈可继续、final judge
  terminal-only、freeze-before-judge、失败分类、cleanup 正交和 trajectory integrity。
- 不能支持：mini-swe 行为等价、真实模型性能、全量 r53 evaluation closure、
  AlphaApollo reasoning/evolution 收益、任何 Spectre 等价性。
- 本功能没有修改 EVAS，因此不触发 Spectre parity gate。
