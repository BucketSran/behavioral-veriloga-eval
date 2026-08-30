# AA-VAE-051：共享本地凭据的安全读取

日期：2026-08-30。状态：本地 helper 与测试已验证，未接入 live pilot CLI。

## 思想与来源

用户保存了 DeepSeek/GLM 两个 key，并将本轮模型优先级改为 GLM。
多 provider 配置不能直接作为 raw-key 参数，也不能通过 `source` 执行。
这不是复制 AlphaApollo 的模块，而是落实 provider adapter 与可信 host
配置的边界：key 不属于模型状态、trajectory、公开数据或 sandbox 环境。

## 代码映射

- `benchmark-vabench-release-v4/operations/calibration_pilot/pilot_credentials.py`：
  `load_pilot_key` 只解析受限的两个字段，返回选定非空 literal；拒绝重复字段、
  未知字段、shell expansion 与多行值。读取上限 16 KiB，检查当前 owner、
  owner-only POSIX mode、regular file，拒绝末级 symlink，FIFO 不会阻塞。
- `tests/test_agent_harness_pilot_credentials.py`：选择、不执行、不修改环境、
  权限/路径类型、大小/编码、错误不回显凭据的本地 fixture 测试。
- `tests/test_agent_harness_ci_gate.py` 与 evaluator-closure workflow：
  新 helper 的 PR/push 变更触发既有 harness tests。
- `plans/glm-budget-pilot.md`：GLM 优先、保留六-cell 分母和 CNY 5 上限；
  明确平台确认、请求保护与 live driver 的剩余门槛。

## 验证与边界

TDD 从缺少模块开始；权限/错误处理检查和 CI 路径检查均先失败后修复。
独立只读审查未发现本切片阻断。精确命令/计数见 verification log。
测试只用虚构凭据，不访问 provider。旧 raw-key CLI、r53、EVAS 0.8.7、
scorer 和 legacy 默认值均未改变。

helper 不推断 key 所属平台、不认证 API、不决定计费、不重写调用者环境。
POSIX mode 检查不是完整 ACL/父目录威胁模型，也不是防同用户恶意进程的
安全边界。真实请求适配/预算保护/轨迹→EVAS 集成仍需后续独立验收。
