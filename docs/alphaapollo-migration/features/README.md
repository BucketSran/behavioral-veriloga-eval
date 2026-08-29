# 单项功能记录模板

每个真正新增或显著改变的功能，在本目录新建：

```text
AA-VAE-NNN-short-name.md
```

至少包含以下内容：

## 功能标识

- ID：`AA-VAE-NNN`
- 名称：
- 状态：设计中 / 已有基础 / 已实现 / 已验证 / 暂不迁移 / 条件启用
- 负责人或变更任务：
- 日期：

## 思想来源

- AlphaApollo 中的公开概念、论文位置或代码入口：
- 要解决的通用问题：
- 哪些内容属于观察，哪些属于我们的推断：

## vaEVAS 适配决策

- 采用什么：
- 修改什么：
- 明确不采用什么：
- evaluator、leakage、budget、memory 与 claim 边界：

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `path::symbol` |  | harness / trajectory / scorer / result / CI / docs |

## 数据与状态变化

- 输入：
- 中间状态：
- 输出：
- 新增 schema 字段：
- backward compatibility：

## 验证证据

- regression tests：
- clean-room smoke：
- evidence/manifest hash：
- 未验证部分：

## Claim boundary

- 该功能能够支持的主张：
- 不能支持的主张：
- 若使用 Spectre，触发条件和 sidecar：
