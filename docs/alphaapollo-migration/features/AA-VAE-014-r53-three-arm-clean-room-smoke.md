# AA-VAE-014: r53 三条件 clean-room smoke

## AlphaApollo 思想

AlphaApollo 的一个关键工程启发是：评测样本应该保存完整 trajectory，而不是只保存
最终答案。controller/environment 需要记录模型动作、环境反馈和终止状态，这样后续
才能判断问题出在采样、工具、状态管理还是最终评判。

## vaEVAS 适配

vaEVAS 的正式评测还必须把 trajectory 和硬件评分链路 join 起来。因此本功能用一个
r53 单任务垂直切片验证：

1. 三个 matched arms 使用同一个 public task，但各自在新 runtime 中执行；
2. `Agent-No-EVAS` 的运行期 EVAS 能力为 0，`Agentic` 可以记录公开 EVAS feedback；
3. 每个 arm 都写出可哈希的 trajectory；
4. final submission 通过 `snapshot_submission` 冻结；
5. `score_campaign.py` 用 EVAS 0.8.7 trusted replay 生成 sidecar；
6. claim gate 只允许 pipeline connectivity claim。

## 代码落点

- `scripts/run_v4_r53_clean_room_smoke.py`
  - 新增 deterministic smoke CLI；
  - 只从 `public_contract.json` 生成一个故意不完整的中性候选，不读取
    evaluator solution；
  - 真实调用 `run_campaign.py::run_cell`：OneShot 走 `submit_artifacts`，
    `Agent-No-EVAS` 和 `Agentic` 走 mini-SWE；
  - 记录 append-only event hash chain；
  - 以 `write_back=false` 调用 scorer，并写 content-addressed EVAS sidecar。
- `result_protocol.py::snapshot_submission`
  - freeze 首次写入后只允许相同字节的幂等验证；candidate 或 snapshot 漂移
    都会 fail closed；多文件 manifest 会先按路径规范化，声明顺序不会造成
    虚假的 hash drift。
- `result_protocol.py::trusted_replay`
  - adapter 零退出但缺少 structured result 时不再隐式通过。
- `score_campaign.py::evaluate_cell`
  - 新增非回写模式，closure scorer 不再修改 frozen campaign result。
- `tests/test_v4_r53_clean_room_smoke.py`
  - 锁定公开接口和报告字段；
  - 断言三条件、trajectory hash、submission tree hash、EVAS 0.8.7 sidecar、
    `Agent-No-EVAS` 零 EVAS 调用和 pipeline-only claim boundary。
- `.github/workflows/evaluator-closure.yml`
  - 将 evaluator closure smoke gate 接到 r53 三条件 smoke。

## 验证

- RED：新测试最初暴露四项缺口：旧脚本绕过 runner、EVAS 版本不校验、
  freeze 可覆盖、零退出但无 structured result 会被记为通过。
- GREEN：`tests/test_v4_r53_clean_room_smoke.py` 为 `4 passed`；审查修复后
  result protocol 与 smoke 联合测试为 `57 passed`，受影响 v4 测试面为
  `203 passed, 3 skipped`。
- 真实 Docker smoke：`v4-001` 三条件均为独立 runtime；OneShot 通过
  provider transport 隔离，两个 G2 条件使用 Docker。EVAS identity 为
  `evas-sim 0.8.7 (rust-core 0.2.4, ABI 20260718, ... loadable)`。
- 三个故意不完整候选均得到 structured `behavior_failure`，因此
  `judge_statuses={"behavior_failure": 3}`；这正是预期的 evaluator 结果，
  smoke 的 PASS 只表示链路闭环。
- `Agent-No-EVAS` 记录 0 次 in-loop EVAS，`Agentic` 记录 1 次；三条
  trajectory chain 均验证通过，submission tree SHA256 均为
  `ed247e3e8f80ac258bb3e1c07330af63399241af519a679121b31c3e82ab8a67`。
- 汇总 score sidecar SHA256 为
  `00c58581601acb361c588407052824c8c36b83575c163dcc9b4629b5054985ee`。

## 边界和后续

该 smoke 使用 deterministic public-contract fixture，不代表任何模型 baseline，也不支持
aggregate benchmark claim。trajectory hash chain 已在 smoke 内实现；下一步是把同一
schema 提升为所有真实模型 campaign 的通用协议，并补齐 result-to-claim index。
