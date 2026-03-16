# VibeMouse 第 1 步 PR 拆分执行文档

## 目的

本文档不改变原迁移目标，只改变第 1 步的落地方式：把原本"大一步完成"的 Step 1 拆成多个可 review、可回滚、可逐步合并的 PR。

- 原方案来源：`docs/TWO_STEP_MIGRATION_PLAN.zh-CN.md`
- 本文聚焦：原方案中的"第 1 步"
- 本文不改动：原方案中的"第 2 步"

## 使用方式

阅读本文件时，有两个判断原则：

1. 以原方案的目标和边界为准
2. 以本文的 PR 顺序作为实际落地顺序

如果两者冲突，以"原方案目标不变、拆分方式更细"为准。

## 执行前检查（Preflight）

在开第一个分支之前，先本地确认以下条件全部满足：

```bash
# 1. 确认默认分支
git remote show origin | grep 'HEAD branch'
# 预期输出：HEAD branch: master

# 2. 确认本地与远端同步
git fetch origin
git status
# 预期：nothing to commit, working tree clean

# 3. 确认 GitHub 仓库 merge 策略
# 登录 GitHub → Settings → General → Pull Requests
# 如果只允许 squash/rebase，后续 PR 需要 rebase（见"前序 PR 合并后的处理"）

# 4. 确认 CI 依赖可用（不安装 torch/funasr 等重量依赖）
pip install --no-deps -e ".[ci]"
pytest --collect-only 2>&1 | head -20
# 预期：能发现测试文件，无导入错误

# 5. 记录当前基线测试结果
pytest 2>&1 | tail -5
# 记录哪些测试在改动前已经失败，后续 PR 不应新增失败
```

如果 `pytest` 模块不存在，先修复开发依赖再开 stack。

## 拆分原则

这些原则直接来自原方案里的执行顺序、兼容性要求和风险控制，只是把它们转成更可合并的 PR 形态。

- 一次只引入一种新的运行时契约
- 兼容层在引入它的 PR 内收口，不跨 PR 累积
- 先稳定边界，再并平台
- 测试应随契约一起前移，而不是全部压到最后
- `panel` 在 Step 1 内只保持窄边界，不扩张为完整 UI 产品

原文位置：

- 执行顺序：[第 1 步执行顺序](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步执行顺序)
- 第 1 步兼容性要求：[第 1 步兼容性要求](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步兼容性要求)
- 第 1 步风险：[第 1 步风险](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步风险)
- 第 1 步风险控制：[第 1 步风险控制](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步风险控制)

## 总览

为便于 review，本文把原 Step 1 拆成 7 个 PR。

说明：

- 文件搬迁（PR2a）与语义命令改造（PR2b）分开：PR2a 是纯 `git mv` + import 路径更新，reviewer 只需确认 import 不断、逻辑不变；PR2b 才是真正的命名契约和 bindings 工作。
- 平台并回拆成 Windows（PR4）和 macOS（PR5）两个 PR，**两者串行**：PR5 从 PR4 切出，避免两者同时修改 `pyproject.toml` 和 `system_integration.py` 造成 rebase 冲突。
- PR6 是整条链唯一的 join 点：等 PR4 和 PR5 依次合并后，再从 `master` 切出。

| PR | 主题 | 对应原文章节 | 主要收益 |
| --- | --- | --- | --- |
| PR1 | JSON 配置/状态边界 + `shared/` 骨架 + 最小 CI | A、执行顺序 1-2 | 先稳定配置模型，同步建立 CI 基线 |
| PR2a | 文件搬迁（纯 `git mv` + import 路径更新） | 第 1 步文件映射 | review 成本极低：只验证 import 不断，无逻辑变化 |
| PR2b | 语义命令、bindings、进程内逻辑改造 | B、C、操作改名与事件模型、执行顺序 3-4 | 命名契约与职责拆分一次完成，不引入跨进程 |
| PR3 | IPC、`listener=child/off`、新运行模式 | D、E、执行顺序 5-6 | 单独评审协议和运行模式 |
| PR4 | Windows 主线并回 | F 中的 Windows、执行顺序 7 | 在稳定边界上合并 Windows，PR5（macOS）从本 PR 切出 |
| PR5 | macOS 适配并回 | F 中的 macOS、执行顺序 8 | 在 Windows 已并回的基础上补齐 macOS（与 PR4 串行） |
| PR6 | `panel` 窄边界收口、测试重组、CI 扩展三平台 | G、H、执行顺序 9-11 | 把发布/测试/面板边界作为收尾 PR |

## 版本管理与分支策略

这一节定义的是"怎么提交这 6 个 PR"，不是"代码应该怎么实现"。

如果没有这组规则，文档虽然说明了 PR 拆分顺序，但实际执行时仍然会遇到以下问题：

- 每个 PR 应该从哪一个分支切出
- PR 的 base 应该指向 `master` 还是前一个 PR
- 前一个 PR 合并后，后一个 PR 要不要 rebase
- Step 1 期间什么时候改版本号、什么时候打 tag
- `windows-port/` 这种临时对照目录应该怎么避免被误提交

### 基本约定

- 仓库只需要 fork 一次，不要为了 7 个 PR 再 fork 7 份仓库。
- PR1→PR2a→PR2b→PR3 是严格的串行 stacked PR 链。
- PR5（macOS）从 PR4（Windows）切出，两者串行；原因是两者都会修改 `pyproject.toml` 和 `vibemouse/system_integration.py`，并行提出会产生 rebase 冲突和 review drift。
- PR6 是整条链唯一的 join 点：等 PR4 和 PR5 依次合并进 `master` 后，再从 `master` 切出。
- 在 Step 1 完成前，产品仍然保持单一版本线，不为 Windows/macOS 单独维护 release 版本。
- `windows-port/` 只是临时对照工作树或移植快照，不是长期保留目录，也不是最终仓库结构的一部分。
- Step 1 期间不引入额外的长期集成分支；真正长期存在的只有 `master` 和当前活跃 PR 分支。

### 推荐分支命名与初始 base

| PR | 推荐分支名 | 从哪里切出 | PR 初始 base |
| --- | --- | --- | --- |
| PR1 | `step1/pr1-config-boundary` | `master` | `master` |
| PR2a | `step1/pr2a-file-moves` | `step1/pr1-config-boundary` | `step1/pr1-config-boundary` |
| PR2b | `step1/pr2b-commands-bindings` | `step1/pr2a-file-moves` | `step1/pr2a-file-moves` |
| PR3 | `step1/pr3-ipc-runtime` | `step1/pr2b-commands-bindings` | `step1/pr2b-commands-bindings` |
| PR4 | `step1/pr4-windows-port` | `step1/pr3-ipc-runtime` | `step1/pr3-ipc-runtime` |
| PR5 | `step1/pr5-macos-port` | `step1/pr4-windows-port` | `step1/pr4-windows-port` |
| PR6 | `step1/pr6-panel-tests-ci` | `master`（PR4+PR5 合并后） | `master` |

建议的标题前缀：

- `[1/7] config boundary`
- `[2/7] file moves`
- `[3/7] commands bindings`
- `[4/7] ipc runtime`
- `[5/7] windows merge-in`
- `[6/7] macos port`
- `[7/7] panel tests ci`

### 提交与合并规则

- PR1 先对 `master` 开启；PR2-PR5 先作为 stacked PR 依次挂在前一个 PR 之上（PR5 挂在 PR4 之上）；PR6 在 PR4/PR5 都合并后单独对 `master` 开启。
- 一个 PR 只承载本节定义的主题，不允许顺手混入下一个 PR 的准备性重构。
- 每个 PR 应该保持可单独通过测试，至少要保证自己的合同和新增契约测试完整。
- 每个 PR 引入的兼容层（compat shim、旧路径别名）必须在本 PR 内收口，不留给后续 PR 清理。
- 如果仓库允许，Step 1 这组 stacked PR 优先使用 `Create a merge commit` 合并；这样前序 PR 合并后，后续 PR 通常只需要 retarget base，而不需要大范围重写历史。
- 如果仓库策略只允许 `Squash and merge` 或 `Rebase and merge`，那就接受后续分支需要 rebase，这是 stacked PR 的正常维护成本，不应把这种成本转嫁成"大 PR 一次合完"。

### 前序 PR 合并后的处理

默认规则：

- 前一个 PR 没合并前，后一个 PR 的 base 继续指向前一个 PR 分支。
- 前一个 PR 合并后，先处理它的直接子 PR，再逐层往后处理，不要一次性重排整条栈。

如果平台支持 merge commit：

- PR1 合并后，把 PR2a 的 base 改到 `master`。
- PR2a 合并后，把 PR2b 的 base 改到 `master`。
- PR2b 合并后，把 PR3 的 base 改到 `master`。
- PR3 合并后，把 PR4 的 base 改到 `master`。
- PR4 合并后，把 PR5 的 base 改到 `master`。
- PR5 合并后，PR6 直接对 `master` 开启。

如果平台只允许 squash/rebase merge，推荐按"只处理直接子分支"的方式维护：

```bash
git fetch origin
git switch step1/pr2a-file-moves
git rebase --onto origin/master step1/pr1-config-boundary
git push --force-with-lease
# PR2a 合并后再处理 PR2b：
git switch step1/pr2b-commands-bindings
git rebase --onto origin/master step1/pr2a-file-moves
git push --force-with-lease
```

PR4 合并后，PR5 rebase 到 `master`：

```bash
git switch step1/pr5-macos-port
git rebase --onto origin/master step1/pr4-windows-port
git push --force-with-lease
```

始终只对"直接父子关系"做一次调整，不跨层乱改 base。

如果某个前序 PR 还在频繁改动，不要急着把 PR5、PR6 也提出来；宁可把后续项留在本地分支，也不要把 review 链拉得过长。

### 版本号、tag 和 changelog 规则

Step 1 的这 6 个 PR 属于同一条未发布版本线。

- PR1-PR5 原则上不做正式 release bump；除非某个依赖元数据必须同步调整，否则版本号保持在未发布状态。
- `CHANGELOG` 或发布说明应该以一个统一的 `Unreleased / Step 1` 段落累计，不为每个 PR 单独切产品版本。
- 当 PR6 合并、Linux/Windows/macOS CI 全绿、Step 1 验收标准满足后，再一次性从 `master` 打正式 tag。
- 正式 tag 仍然遵循原迁移文档里的单一版本线，例如 `v0.4.0`，然后按平台产出 agent / panel 资产。
- 如果中途确实需要 QA 检查点，用预发布 tag 即可，例如 `v0.4.0-step1-pr3` 或 `v0.4.0-rc.1`；这类 tag 只用于内部验证，不替代最终正式版本。

如果 Step 1 执行过程中 `master` 上插入了 hotfix：

- hotfix 直接从 `master` 单开分支、单独合并
- 剩余未合并的 Step 1 PR 统一 rebase 到最新 `master`
- 不要为了吸收 hotfix 再额外切一条长期 `step1-integration` 分支

### `windows-port` 临时目录与 `.gitignore` 规则

**`windows-port/` 是纯本地参考目录，全程不进任何 PR 的 commit。**

这是最重要的一句话。展开说：

- `windows-port/` 是一份移植快照或本地对照工作树，供开发者在本地 diff、查阅、复制代码时使用。
- **Windows 适配的最终实现，全部落在主线目录结构里**：`vibemouse/platform/`、`vibemouse/listener/`、`vibemouse/ops/` 等。PR4 提交的是这些主线目录里的代码，不是 `windows-port/` 里的文件路径。
- `windows-port/` 永远不应该出现在任何 PR 的 diff 里。它已经被根目录 `.gitignore` 忽略（`/windows-port/` 和 `/windows-port-*/`），这是有意的设计，不是疏漏。

PR4 的开发流程是：

1. 参考 `windows-port/` 里的实现，理解 Windows 适配的差异点
2. 把对应逻辑**按照主线目录结构**写进 `vibemouse/platform/`、`vibemouse/listener/` 等目录
3. 提交主线目录里的代码；`windows-port/` 原地保留供本地参考，但不进 commit

对于 PR4 的 reviewer 预期：

- reviewer 看到的是主线目录里的 Windows 实现，和 Linux 路径并列
- reviewer 不会也不应该看到 `windows-port/` 里的任何文件
- 任何把 `windows-port/` 整目录或其中文件路径带进 PR 的变更，都是版本管理失控

`windows-port/` 的最终命运是在 Step 1 完成后从本地删除，或者保留在仓库根目录之外的位置作为历史参考。它不是仓库结构的一部分，也没有长期保留价值。

## 原文到 PR 的映射

### Step 1 范围映射

| 原文项 | 原文位置 | 新 PR |
| --- | --- | --- |
| A. 引入 JSON 配置与状态文件边界 | [A. 引入 JSON 配置与状态文件边界](TWO_STEP_MIGRATION_PLAN.zh-CN.md#a-引入-json-配置与状态文件边界) | PR1 |
| 第 1 步文件映射（搬迁部分） | [第 1 步文件映射](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步文件映射) | PR2a |
| B. 引入语义命令 | [B. 引入语义命令](TWO_STEP_MIGRATION_PLAN.zh-CN.md#b-引入语义命令) | PR2b |
| C. 把 listener 从 core agent 里拆出来 | [C. 把 listener 从 core agent 里拆出来](TWO_STEP_MIGRATION_PLAN.zh-CN.md#c-把-listener-从-core-agent-里拆出来) | PR2b |
| D. 引入 IPC 运行时边界 | [D. 引入 IPC 运行时边界](TWO_STEP_MIGRATION_PLAN.zh-CN.md#d-引入-ipc-运行时边界) | PR3 |
| E. 增加运行模式 | [E. 增加运行模式](TWO_STEP_MIGRATION_PLAN.zh-CN.md#e-增加运行模式) | PR3 |
| F. 并回三端平台实现 | [F. 在这些边界之上并回三端平台实现](TWO_STEP_MIGRATION_PLAN.zh-CN.md#f-在这些边界之上并回三端平台实现) | PR4、PR5 |
| G. 建立 panel 边界 | [G. 建立 panel 边界](TWO_STEP_MIGRATION_PLAN.zh-CN.md#g-建立-panel-边界) | PR6 |
| H. 重组测试和 CI | [H. 重组测试和 CI](TWO_STEP_MIGRATION_PLAN.zh-CN.md#h-重组测试和-ci) | PR1 建立 Linux 最小 CI，PR2a-PR5 增量补测，PR6 完成最终重组 |

### Step 1 执行顺序映射

| 原执行项 | 原文位置 | 新 PR |
| --- | --- | --- |
| 1. 创建 `panel/` 和 `shared/` | [第 1 步执行顺序](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步执行顺序) 第 1 项 | PR1 |
| 2. 引入 `config.json` / `status.json` / schema / store / migration | 同上 第 2 项 | PR1 |
| 2.5. 搬迁文件（git mv + import 路径更新） | [第 1 步文件映射](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步文件映射) | PR2a |
| 3. 定义语义命令并完成改名 | 同上 第 3 项 | PR2b |
| 4. 拆出 `listener` / `bindings` / `core` | 同上 第 4 项 | PR2b |
| 5. 加入 agent IPC 和 `listener=child/off` | 同上 第 5 项 | PR3 |
| 6. 兼容路径在引入它的 PR 内收口 | 同上 第 6 项 | 各 PR 在自身范围内引入并收口，不跨 PR 保留 |
| 7. Windows 并回主线 | 同上 第 7 项 | PR4 |
| 8. 补齐 macOS | 同上 第 8 项 | PR5 |
| 9. 重组测试并补 binding / IPC 覆盖 | 同上 第 9 项 | PR2b、PR3 先补契约测试，PR6 做最终重组 |
| 10. CI 改成 Linux / Windows / macOS | 同上 第 10 项 | PR1 建立 Linux 最小 CI；PR6 扩展到三平台 |
| 11. 继续从仓库根目录发布 | 同上 第 11 项 | PR6 |

## PR 详细计划

### PR1：JSON 配置/状态边界 + `shared/` 骨架 + 最小 CI

目标：

- 先建立 `config.json` / `status.json` 的所有权和读写边界
- 创建 `shared/` 骨架（schema、示例、协议占位）
- 保留环境变量覆盖和旧 CLI
- 建立 Linux 单平台 CI，作为后续所有 PR 的 gating 基础

`panel/` 不在本 PR 创建。`panel/` 目录和边界说明留到 PR6 一并处理，和 panel 的窄边界实现放在同一个 review 上下文里。把 `panel/` 骨架放进 PR1 只会让 reviewer 看到一个空目录加一个 README，与 PR1 的主题无关，应避免。

对应原文位置：

- 第 1 步范围 A：[A. 引入 JSON 配置与状态文件边界](TWO_STEP_MIGRATION_PLAN.zh-CN.md#a-引入-json-配置与状态文件边界)
- 执行顺序 1-2：[第 1 步执行顺序](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步执行顺序)
- 配置模型：[配置模型](TWO_STEP_MIGRATION_PLAN.zh-CN.md#配置模型)
- 第 1 步兼容性要求中的"环境变量继续保留为覆盖项"：[第 1 步兼容性要求](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步兼容性要求)

应包含：

- `shared/schema/config.schema.json`
- `shared/schema/status.schema.json`
- `shared/examples/config.example.json`
- `vibemouse/config/` 下的 `schema.py`、`store.py`、`env_overrides.py`、`migration.py`
- `load_config()` 兼容入口，旧调用方先不强制改完
- 集中的 `status.json` 写入入口
- `pyproject.toml` 新增 `[ci]` extras：
  - 仅含 `numpy`、`pyperclip`、`pytest`、`pytest-cov` 四个轻量依赖
  - 背景：`torch`/`funasr-onnx`/`modelscope`/`sounddevice`/`pynput`/`evdev` 均通过 `importlib.import_module()` 懒加载，测试用 `unittest.mock.patch` 隔离，不需要安装即可运行全部现有测试；`pip install -e ".[dev]"` 会拉取 torch（~2 GB）等，在 GitHub Actions 免费层可能超时
  - CI 和本地 preflight 均改为：`pip install --no-deps -e ".[ci]" && pytest`
- `.github/workflows/ci.yml`：Linux 单平台，`pip install --no-deps -e ".[ci]" && pytest`

不应包含：

- IPC
- 子进程 listener
- Windows/macOS 并回
- `panel/` 目录（留到 PR6）
- 完整 panel UI

合并标准：

- 现有 `vibemouse` 入口继续可用
- 不传 `config.json` 时，默认行为与当前版本兼容
- env 覆盖仍然生效
- 配置读写和状态写入有独立测试
- Linux CI 绿色

### PR2a：文件搬迁（纯 `git mv` + import 路径更新）

目标：

- 把现有文件按目标结构搬迁，不改任何逻辑
- reviewer 只需验证：import 没断、测试仍通过、没有夹带逻辑改动

对应原文位置：

- 第 1 步文件映射：[第 1 步文件映射](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步文件映射)
- 风险控制"能先搬文件就先搬文件，再改更深的行为"：[第 1 步风险控制](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步风险控制)

应包含：

- `git mv` 以下文件并更新包内 import 路径（不改逻辑）：
  - `vibemouse/main.py` → `vibemouse/cli/main.py`
  - `vibemouse/app.py` → `vibemouse/core/app.py`
  - `vibemouse/audio.py` → `vibemouse/core/audio.py`
  - `vibemouse/output.py` → `vibemouse/core/output.py`
  - `vibemouse/transcriber.py` → `vibemouse/core/transcriber.py`
  - `vibemouse/logging_setup.py` → `vibemouse/core/logging_setup.py`
  - `vibemouse/mouse_listener.py` → `vibemouse/listener/mouse_listener.py`
  - `vibemouse/keyboard_listener.py` → `vibemouse/listener/keyboard_listener.py`
  - `vibemouse/system_integration.py` → `vibemouse/platform/system_integration.py`（整体搬迁，暂不拆分）
  - `vibemouse/doctor.py` → `vibemouse/ops/doctor.py`
  - `vibemouse/deploy.py` → `vibemouse/ops/deploy.py`
- 各新目录的 `__init__.py`（空文件或最小转发）
- 旧路径的向后兼容 shim（如 `vibemouse/app.py` 改为 `from vibemouse.core.app import *`），保持 `from vibemouse.app import VoiceMouseApp` 等旧 import 仍可用
- `pyproject.toml` 的 scripts 入口更新：`vibemouse = "vibemouse.cli.main:main"`；同时在 `vibemouse/main.py` 保留 shim 使旧 import 不断
- 对应测试文件一并 `git mv`：
  - `tests/test_main.py` → `tests/cli/test_main.py`
  - `tests/test_app.py`、`test_audio.py`、`test_output.py` → `tests/core/`
  - `tests/test_system_integration.py` → `tests/platform/`
  - `tests/test_mouse_listener.py`、`test_keyboard_listener.py` → `tests/listener/`
  - `tests/test_doctor.py`、`tests/test_deploy.py` → `tests/ops/`

不应包含：

- 任何语义/逻辑变化（命令重命名、bindings、状态机改造）
- IPC 相关内容
- Windows/macOS 适配

合并标准：

- `pytest` 全绿（与 PR1 合并前的结果完全一致）
- `diff` 里除 import 路径外看不到逻辑变化行
- 旧 `from vibemouse.app import VoiceMouseApp` 等路径仍可正常 import

---

### PR2b：语义命令、bindings、进程内逻辑改造

目标：

- 把"具象输入 -> 语义命令"的契约固定下来
- 引入 bindings，在进程内完成映射
- 完成 `listener` / `bindings` / `core` 的职责拆分，理顺逻辑边界
- 旧 import 路径在 PR2a 已处理；本 PR 专注语义改造

对应原文位置：

- 第 1 步范围 B：[B. 引入语义命令](TWO_STEP_MIGRATION_PLAN.zh-CN.md#b-引入语义命令)
- 第 1 步范围 C：[C. 把 listener 从 core agent 里拆出来](TWO_STEP_MIGRATION_PLAN.zh-CN.md#c-把-listener-从-core-agent-里拆出来)
- 操作改名与事件模型：[操作改名与事件模型](TWO_STEP_MIGRATION_PLAN.zh-CN.md#操作改名与事件模型)
- 执行顺序 3-4：[第 1 步执行顺序](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步执行顺序)
- 风险控制"先定义 command，再改 listener"：[第 1 步风险控制](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步风险控制)

应包含：

- `vibemouse/core/commands.py`：语义命令常量/枚举
- `vibemouse/bindings/resolver.py`：`event -> command` 映射
- `vibemouse/bindings/actions.py`：默认 bindings 定义
- 规范化事件名和语义命令名的常量或 schema
- 旧前侧键/后侧键/热键/手势到语义命令的适配层（listener 侧改造）
- 对 `bindings` 配置段的支持
- 新增 bindings 和 commands 测试
- 现有 CLI 入口（`vibemouse run`、`vibemouse doctor`、`vibemouse deploy`）尽量保留，不强制删除

不应包含：

- IPC 协议
- `listener=child` / `listener=off`
- Windows/macOS 主线并回

合并标准：

- 进程内运行路径功能等价
- 当前产品语义不变：录音切换、空闲态 Enter、录音态提交、工作区切换保持一致
- 新增 bindings 和 commands 测试
- 无悬空的旧 import 路径（import 路径在 PR2a 已收口）

### PR3：IPC、`listener=child/off`、新运行模式

目标：

- 单独引入协议、消息模型和运行模式
- 让 reviewer 可以只看"协议是否合理、运行模式是否清晰"
- 从 PR2b 切出

对应原文位置：

- 第 1 步范围 D：[D. 引入 IPC 运行时边界](TWO_STEP_MIGRATION_PLAN.zh-CN.md#d-引入-ipc-运行时边界)
- 第 1 步范围 E：[E. 增加运行模式](TWO_STEP_MIGRATION_PLAN.zh-CN.md#e-增加运行模式)
- 内建 IPC 传输方案：[6. 内建 IPC 传输方案固定为 `stdio + LPJSON`](TWO_STEP_MIGRATION_PLAN.zh-CN.md#6-内建-ipc-传输方案固定为-stdio--lpjson)
- 执行顺序 5-6：[第 1 步执行顺序](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步执行顺序)
- 风险控制"先定义 IPC schema，再接多个 IPC 客户端"：[第 1 步风险控制](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步风险控制)

应包含：

- `vibemouse/ipc/server.py`
- `vibemouse/ipc/client.py`
- `vibemouse/ipc/messages.py`
- `shared/schema/ipc.schema.json`
- `shared/protocol/COMMANDS.md`
- `shared/protocol/EVENTS.md`
- `vibemouse agent run --listener=child`
- `vibemouse agent run --listener=off`
- `vibemouse listener run --connect ...`
- 新增 IPC 测试

不应包含：

- Windows fork 回并
- macOS 适配
- 完整 panel UI

合并标准：

- `listener=child` 可用
- `listener=off` 可用
- 内建链路采用 `stdio + LPJSON`
- 新增 IPC 测试

### PR4：Windows 主线并回

目标：

- 在新边界下，把 Windows 适配实现写入主线目录结构（`vibemouse/platform/`、`vibemouse/listener/` 等）
- `windows-port/` 仅作本地参考，不进任何 commit（见"windows-port 临时目录"一节）
- 把"平台适配"与"运行时契约变更"分开评审
- 从 PR3 切出；PR5（macOS）将从本 PR 切出，两者串行

对应原文位置：

- 第 1 步范围 F 中的 Windows：[F. 在这些边界之上并回三端平台实现](TWO_STEP_MIGRATION_PLAN.zh-CN.md#f-在这些边界之上并回三端平台实现)
- 执行顺序 7：[第 1 步执行顺序](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步执行顺序)
- "先有边界，再并平台"：[5. 先有边界，再并平台](TWO_STEP_MIGRATION_PLAN.zh-CN.md#5-先有边界再并平台)
- 验收标准中的三端目标：[验收标准](TWO_STEP_MIGRATION_PLAN.zh-CN.md#验收标准)

应包含：

- `vibemouse/platform/` 里的 Windows 适配实现（参考 `windows-port/` 中对应文件，按主线结构落地）
- `vibemouse/listener/`、`vibemouse/ops/` 里的 Windows 路径适配（`keyboard_listener`、`deploy`、`doctor`）
- `pyproject.toml` 的平台条件依赖（Windows 专属依赖加 `sys_platform == 'win32'` marker）
- Windows 相关测试并入主测试树

不包含：

- `windows-port/` 下的任何文件路径（该目录全程不进 commit）

不应包含：

- macOS 适配
- panel 职责扩张

合并标准：

- Windows 不再依赖独立 fork 才能工作
- Linux 基线不被回归
- Windows 特有行为在主线测试中可验证

### PR5：macOS 适配并回

目标：

- 在和 Windows 相同的边界模型上补齐 macOS
- 把"第三平台支持"作为独立评审主题
- 从 PR4 切出，建立在 Windows 已并回的基础上（与 PR4 串行，避免两者同时修改 `pyproject.toml` 和 `system_integration.py`）

对应原文位置：

- 第 1 步范围 F 中的 macOS：[F. 在这些边界之上并回三端平台实现](TWO_STEP_MIGRATION_PLAN.zh-CN.md#f-在这些边界之上并回三端平台实现)
- 执行顺序 8：[第 1 步执行顺序](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步执行顺序)
- 第 1 步交付物中的"三端支持"：[第 1 步交付物](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步交付物)
- 验收标准中的三端目标：[验收标准](TWO_STEP_MIGRATION_PLAN.zh-CN.md#验收标准)

应包含：

- `platform/` 下的 macOS 实现
- doctor / deploy 在 macOS 上的适配
- macOS 上的最小可用 listener/platform/output 合同实现

不应包含：

- monorepo 目录搬迁
- panel 功能扩张

合并标准：

- macOS 具备与主合同兼容的运行能力
- 不为 macOS 引入长期分叉路径
- Linux/Windows 不被回归

### PR6：`panel` 窄边界收口、测试重组、CI 扩展三平台

目标：

- 在运行时和平台边界稳定后，再做测试树、CI、发布和 `panel` 收尾
- 把"最终 review 面"聚焦在质量收口，而不是运行时重构
- 本 PR 从 `master` 切出（PR4/PR5 依次合并后）

对应原文位置：

- 第 1 步范围 G：[G. 建立 panel 边界](TWO_STEP_MIGRATION_PLAN.zh-CN.md#g-建立-panel-边界)
- 第 1 步范围 H：[H. 重组测试和 CI](TWO_STEP_MIGRATION_PLAN.zh-CN.md#h-重组测试和-ci)
- 执行顺序 9-11：[第 1 步执行顺序](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步执行顺序)
- 风险控制"listener / binding / IPC 测试先补，再大规模并平台"和"panel 先保持窄边界"：[第 1 步风险控制](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步风险控制)

应包含：

- `tests/cli/`
- `tests/core/`
- `tests/config/`
- `tests/platform/`
- `tests/listener/`
- `tests/bindings/`
- `tests/ipc/`
- `tests/ops/`
- CI 扩展到 Linux / Windows / macOS 三平台矩阵（在 PR1 的单平台基础上扩展）
- 从仓库根目录继续发布的脚本和文档更新
- `panel` 的窄边界实现（见下方"panel 实现方案"）

不应包含：

- 完整 panel 产品化
- Step 2 的 monorepo 迁移

合并标准：

- 测试目录按职责完成重组
- bindings / IPC / platform 三类测试在主线存在
- CI 覆盖 Linux / Windows / macOS
- `panel` 仍然只停留在 Step 1 定义的窄边界内

### panel 实现方案（Avalonia UI）

#### 技术选型

使用 [Avalonia UI](https://avaloniaui.net/)（.NET，跨平台桌面 UI 框架），原因：

- 一套代码产出 Windows / macOS / Linux 三平台原生桌面程序
- 不依赖 Python 运行时，panel 与 agent 完全独立部署
- Step 2 迁移到 monorepo 时，`panel/` 目录原地保留，无需重构

#### 目录结构

```
panel/
  VibeMouse.Panel/
    VibeMouse.Panel.csproj   # Avalonia 项目文件
    App.axaml                # 应用入口
    App.axaml.cs
    Views/
      MainWindow.axaml       # 主窗口
      MainWindow.axaml.cs
    ViewModels/
      MainViewModel.cs       # 绑定逻辑
    Services/
      ConfigService.cs       # 读写 config.json
      StatusService.cs       # 轮询 status.json
      AgentControlService.cs # 发送控制命令
  VibeMouse.Panel.sln
```

#### 界面设计（Step 1 窄边界）

主窗口包含三个区域，单窗口布局，无需多标签：

**状态区（顶部，只读）**

轮询 `status.json`（每 2 秒），展示：

- agent 运行状态（idle / recording / processing）
- 当前监听模式（`inline` / `child` / `off`）
- 最近一次转录文本摘要（截断显示）

**配置区（中部，可编辑）**

直接映射 `config.json` 中用户最常用的字段，以简单表单呈现：

| 字段 | 控件类型 |
|------|----------|
| `model` | 下拉选择 |
| `language` | 文本输入 |
| `hotkey` | 文本输入（只展示，暂不做按键捕获） |
| `log_level` | 下拉选择 |

点击"保存"后写入 `config.json`；不自动保存，防止误操作。

**操作区（底部，控制命令）**

三个按钮，对应 Step 1 允许的有限控制动作：

| 按钮 | 行为 |
|------|------|
| Reload Config | 通过 IPC 发送 `reload` 命令（IPC 不可用时禁用并提示） |
| Run Doctor | 通过 IPC 发送 `doctor` 命令 |
| Open Log Dir | 用系统文件管理器打开日志目录 |

IPC 可用性判断：检查 `status.json` 里是否有 `ipc_socket` 或 `ipc_port` 字段；没有则视为不可用。

#### 与 agent 的通信方式

Step 1 采用两层通信，无需强制要求 IPC 在线：

1. **文件层（始终可用）**：直接读写 `config.json` / `status.json`，适用于配置编辑和状态展示
2. **IPC 层（可选）**：若 PR3 的 IPC server 在线，通过 `stdio + LPJSON` 发送控制命令；不在线时操作区按钮禁用

panel 不持有对 agent 进程的直接引用，不直接修改 agent 运行时内部对象。

#### 构建与发布

```bash
# 开发运行
dotnet run --project panel/VibeMouse.Panel

# 各平台打包
dotnet publish panel/VibeMouse.Panel -c Release -r win-x64 --self-contained -o dist/panel-windows
dotnet publish panel/VibeMouse.Panel -c Release -r osx-arm64 --self-contained -o dist/panel-macos
dotnet publish panel/VibeMouse.Panel -c Release -r linux-x64 --self-contained -o dist/panel-linux
```

产物与 agent 产物并列放在 `dist/` 下，从仓库根目录统一发布。CI 在 PR6 阶段新增 `dotnet build` 步骤验证三平台编译通过，不要求 UI 集成测试。

#### Step 1 边界约束（不可逾越）

- panel **不**负责输入监听、设备控制、音频采集、核心状态机
- panel **不**直接读写 agent 进程内部状态
- panel **不**在 Step 1 阶段引入系统托盘、热键注册、开机自启等平台特有能力（留 Step 2）
- `panel/` 目录在 Step 2 原地成为独立子项目，Step 1 不预先拆解它

## 每个 PR 为什么更容易合并

拆分后的收益不是"总工作量减少"，而是"单个 PR 需要证明的事情减少"。

- PR1 只证明配置和状态边界，顺带建立 CI 基线，不动主运行链路
- PR2a 只做文件搬迁，reviewer 只需确认 import 不断，无需理解业务逻辑
- PR2b 只证明命名契约、bindings 和模块职责拆分，不动进程模型
- PR3 只证明协议和运行模式，不处理平台 fork
- PR4 只处理 Windows 回并，不同时重构 IPC
- PR5 只处理 macOS，在 Windows 已并回的基础上补齐，不引入新的运行时语义
- PR6 只做质量收口，不再引入新的运行时语义

这对应原文里最核心的风险控制：

- 先搬文件（PR2a），再改语义（PR2b）
- 先定义 command，再改 listener
- 先定义 IPC schema，再接多个 IPC 客户端
- listener / binding / IPC 测试先补，再大规模并平台
- panel 先保持窄边界

原文位置：[第 1 步风险控制](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-1-步风险控制)

## 明确不放进 Step 1 PR 的内容

以下内容仍然留在原方案的 Step 2，不提前进入上述 PR：

- 把 Python 项目整体挪到 `agent/`
- 把 `pyproject.toml` 搬到 `agent/`
- 把测试整体搬到 `agent/tests/`
- 让 `panel/` 成为真正独立的 UI 子项目
- monorepo 根目录下的最终 packaging 组织

原文位置：

- 第 2 步目标与范围：[第 2 步：升级为最终 monorepo 结构](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-2-步升级为最终-monorepo-结构)
- 第 2 步执行顺序：[第 2 步执行顺序](TWO_STEP_MIGRATION_PLAN.zh-CN.md#第-2-步执行顺序)

## 最终判断标准

只要出现下面任一情况，就说明拆分计划被破坏了，应当把改动退回到更小的 PR：

- 一个 PR 同时改 JSON 配置、IPC 协议和平台回并
- 一个 PR 同时改 listener 拆分和 Windows fork 合并
- `panel` 在 Step 1 阶段直接开始操作 runtime 内部对象
- 在 command 和 IPC 都没稳定前，就开始做 monorepo 搬迁

这些正是原方案明确要求避免的反模式。

原文位置：[需要避免的反模式](TWO_STEP_MIGRATION_PLAN.zh-CN.md#需要避免的反模式)
