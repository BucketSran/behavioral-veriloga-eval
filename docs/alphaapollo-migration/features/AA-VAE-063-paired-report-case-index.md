# AA-VAE-063：配对结果摘要与安全 case 索引

日期：2026-08-31。普通 native campaign 的只读结果投影，不新增评分器。

## 思想、代码与变化

沿用完整实验分母、失败可见、来源可追踪的评测原则。复用
`operations/calibration_pilot/result_ledger.py::build_native_campaign_ledger`，
不另建报告框架；输入仍必须通过既有 schedule/score-eligibility 校验。

- `paired_summary`：每个 arm 的计划/观察/可评分/通过数与显式分母；每对条件
  的计划槽位、有效配对、跳过原因、左右胜/平局与均值差。零分母为 null。
- `case_study_index`：身份、状态、费用、selected attempt，以及 trajectory、
  private events、reviewer export、冻结候选、final profile/sidecar 的可用 hash。
  缺项列入 `incomplete_evidence`，不自行补造、不扫描磁盘。
- 生产 reader 的 `native_evidence.files` 是 canonical path→hash，兼容
  `native-launcher` 和 `native-episode` 两种私有证据布局。全 trajectory 文件
  hash 用于追踪；不输出 raw prompt、模型输出、候选源码或私有 checker 文本。

## 验证与边界

`tests/test_agent_harness_result_ledger.py` 覆盖三条件失败分母、零配对、胜平负、
缺失证据、两种真实字段布局及原始文本泄漏 sentinel。联合既有 integration
测试 33 passed；独立复审提出的路径映射缺口都有 RED→GREEN 回归。
普通 ledger 仍拒绝扩展/Evolution 混入。不存在统计显著性、模型质量提升或
真实实验效果结论；本切片也不是原始 trajectory 的可视化渲染器。
