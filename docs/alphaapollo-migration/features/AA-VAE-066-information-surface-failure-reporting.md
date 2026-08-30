# AA-VAE-066：信息面声明与 Evolution 失败责任投影

日期：2026-08-31。不增加权限、不改评分、不启动重试，只补证据字段。

## 代码与动机

比较 coding agent 时，模型能看到什么与能执行什么必须写清；编译失败、
checker 执行异常和未知无候选，也不能混成一个“模型失败”。

- `run_campaign.py::declared_information_surface` 生成纯声明：逻辑条件、生成
  export arm、Bash/EVAS、公开 validation 入口、扩展干预、final 不回流。
  明确 `declared_expected_policy`、`observed_image_audit=false`、
  `information_parity_established=false`；安装 examples、提示词与模型/预算
  的差异需要另外核查，不把配置声明当成镜像审计或公平性证明。
- native launcher 和 Evolution 都在 config hash 前绑定声明；native scorer
  对新字段校验并保留，旧 manifest 缺字段仍可读取；Evolution final 摘要保留。
- `run_native_evolution.py::_terminal_failure_fields` 复用既有 result protocol：
  setup/public cleanup/final replay 抛错为 infrastructure/system，phase 另记；
  无候选但无法确定原因时为 undetermined。流程 completed 但候选 compile/runtime/
  behavior failure 仍保持 candidate verdict，不重标为基础设施失败。

## 验证与限制

native conditions / native Evolution / extension 联合 46 passed；独立复审
12 项定向验证通过且无问题。覆盖 hash 前绑定/score row、四种信息面、setup/
cleanup/final 异常与 candidate compile verdict。Ruff、compile、diff checks 通过；
最终全量、真实集成和 hosted CI 由验证日志另记。

没有增加新的通用 read/edit 框架：现有受控 Bash 和统一 controller 仍可用。
测试锁住已发现的具体缺陷，比为“像 coding agent”而新增工具更可审计。
独立 LSP/typecheck 未提供，不能把替代静态检查称为完整 typecheck。
