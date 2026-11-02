# vaBench 公开 Agent 评测 Docker

仓库顶层的 [`environment/`](../../environment/) 是唯一共享的 Harbor 环境构建源。这套辅助脚本供评测执行方从公开 GitHub 仓库自行构建固定的 Agent 运行环境。执行方负责启动 Agent 和收集提交物，不需要接触内部镜像仓库、私有 evaluator 或专用 sandbox 机器。

## 1. 获取固定版本

安装 Docker 后执行：

```bash
git clone https://github.com/Arcadia-1/behavioral-veriloga-eval.git
cd behavioral-veriloga-eval
git checkout <我们提供的固定 commit>
cd benchmark-vabench-release-v4/public-agent-runtime
```

不要直接用会移动的 `main` 作为正式实验版本。实验记录中应保存 commit、镜像 ID、模型和运行参数。

## 2. 从零构建并自检

```bash
./build.sh
./verify.sh
```

如果当前账号无 Docker 权限，使用：

```bash
sudo ./build.sh
sudo ./verify.sh
```

默认情况下，验证脚本会在当前 runtime 目录下创建并自动清理 Docker bind mount
所需的临时目录，以兼容 Docker Desktop 和 Colima。若需使用其他已共享的宿主机目录，
可设置 `VABENCH_DOCKER_SHARED_TMPDIR`。

`build.sh` 会生成配对的 `vabench-agent-runtime:0.8.4` 与
`vabench-agent-runtime:0.8.4-noexec` 镜像。后者保留相同基础镜像、依赖锁、
Shell 和 mini-SWE 运行环境，但移除 EVAS 包与命令，用于 Agent-NoExec 对照。

`verify.sh` 会实际运行一条 EVAS 仿真，并确认 Agent 能读取 `tran.csv`，而不只是得到 0/1。它还会检查题目只读、提交目录可写、EVAS 0.8.4 Rust core 可加载、Agent-NoExec 镜像确实无法找到 EVAS 命令或 Python 模块，以及镜像中没有预设的 evaluator 目录。

## 3. 准备单题公开包

评测组织方为每次运行提供三个目录：

```text
task/        仅包含这一题可公开的题面、源码、visible tests 和运行说明
submission/  空目录，用于导出最终提交
work/        空目录，用于 Agent 的临时文件和公开仿真结果
```

`task/` 中不得包含 hidden tests、checker、gold、mutations、私有 evaluator、其他题目或凭证。Docker 镜像本身也不包含任何题目，因此同一个固定镜像可以复用于全部任务，无需为每题构建镜像。

## 4. 启动 Agent

启动交互式 Bash：

```bash
./run.sh ./task ./submission ./work
```

或者把 Agent 命令直接交给启动器：

```bash
cp /path/to/agent ./work/agent
./run.sh ./task ./submission ./work /workspace/work/agent --workspace /workspace
```

容器内的固定路径为：

```text
/workspace/public/task        只读
/workspace/public/submission  可写
/workspace/work               可写
/tmp                           可写、每次运行独立
```

Agent 可以运行完整 Bash，并直接调用：

```bash
evas simulate public/task/visible_test.scs \
  -o /tmp/vabench-visible/evas-output \
  --spectre-strict

head /tmp/vabench-visible/evas-output/tran.csv
cat /tmp/vabench-visible/evas-output/run.json
```

也就是说，EVAS 的日志和波形在同一容器里对 Agent 可读。完成后只从 `submission/` 收集题目约定的最终文件。

## 5. 隐藏评分

Agent 运行环境只负责公开验证和生成 submission。hidden 评分由我方在另一个私有环境中对最终 submission 执行一次，不能把 hidden checker 包进镜像，也不能在 Agent 循环中返回 hidden 分数。

默认启动器关闭网络、使用只读根文件系统、丢弃 Linux capabilities，并且只挂载上述三个目录。若 Agent 必须联网，应由执行方创建受控 Docker network，并确保任何模型凭证仅在运行时提供，绝不能写入镜像或公开任务包。

## 安全边界

Docker 隔离只能保证本次镜像和挂载不泄漏私有资料，不能让已经发布到公开 GitHub 的内容重新变成秘密。现有 r49 是公开开发 benchmark；真正的盲测必须使用从未公开过 hidden evaluator 的 held-out 题目，并只向执行方发放清理后的单题公开包。

导出 Harbor task 时，应从顶层共享源生成 `<task>/environment/`，不要人工维护 1200 份 Dockerfile。
