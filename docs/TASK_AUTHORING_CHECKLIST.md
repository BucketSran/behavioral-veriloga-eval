# Task Authoring Checklist

## 任务 ID: ___________

### 1. 目录结构
- [ ] `tasks/<family>/voltage/<id>/prompt.md` 存在
- [ ] `tasks/<family>/voltage/<id>/meta.json` 存在，并通过 schema 验证
- [ ] `tasks/<family>/voltage/<id>/checks.yaml` 存在

### 2. `meta.json` 字段
- [ ] `id` 与目录名一致
- [ ] `family` 属于 `end-to-end` / `spec-to-va` / `bugfix` / `tb-generation`
- [ ] `domain` = `voltage`
- [ ] `expected_backend` = `evas`
- [ ] `scoring` 字段正确，`tb-generation` 不包含 `sim_correct`
- [ ] `parity_policy` 字段正确，PLL 类使用 `pll_task_aware`，`tb-generation` 使用 `not_required`

### 3. Gold 资产
- [ ] `gold/dut.va` 存在
- [ ] `gold/tb_*.scs` 存在
- [ ] DUT 端口为纯电压域 `electrical`
- [ ] `transition()` 目标采用离散变量风格
- [ ] `save` 语句不包含旧式限定符
- [ ] `ahdl_include` 使用裸文件名，不写绝对路径

### 4. EVAS 验证
- [ ] 本地运行 `python runners/run_gold_suite.py` 通过
- [ ] `simulate_evas.py` 对该任务 checks 全部 pass

### 5. Dual validation（如适用）
- [ ] 已通过 `scripts/run_with_bridge.sh` 运行 dual-suite
- [ ] parity 结论符合该任务的 `parity_policy`
- [ ] 结果保存到 `results/<run_name>/`
- [ ] `MANIFEST.md` 已生成

### 6. 结果登记
- [ ] 在 `coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md` 新增一行
- [ ] 运行 `python coordination/scripts/sync_task_assignment.py --check` 无报错
- [ ] `WORK_TODO.md` 的相关状态节已更新
