# Iter Loop 状态协议

## 存储位置

每个目标仓库使用自己的本地状态目录：

```text
<repo-root>/auto-iter/runs/
├── active.json
└── <run-id>/
    ├── state.json
    └── events.jsonl
```

首次初始化时，状态助手通过 `git rev-parse --git-common-dir` 定位共享 Git 元数据，并向
`info/exclude` 幂等追加：

```gitignore
# iter-loop local runtime state
/auto-iter/runs/
```

状态目录属于当前 clone，不提交、不 push，也不视为备份。`git clean -xfd` 仍可能删除它。

## 写入所有权

- 只有 coordinator 可以调用状态助手的写命令。
- `iter-scout`、`iter-builder` 和 `iter-reviewer` 禁止修改 `auto-iter/runs`。
- `/iter-status` 只可调用 `show`、`list` 和不带 `--write` 的 `reconcile`。
- `/iter-stop`、`/iter-resume` 和主协调流程可按本协议写入状态。
- 不得直接手工拼接 `.git/info/exclude` 路径，也不得覆盖其中的用户内容。

状态助手位于本 Skill 的 `scripts/state_store.py`。调用前根据当前 `SKILL.md` 的实际位置
解析绝对脚本路径，不把脚本复制到目标仓库。

## 状态模型

`active.json` 是活动运行指针；真实状态保存在对应运行目录的 `state.json`。核心字段：

```json
{
  "schemaVersion": 1,
  "runId": "20260911T051800Z-a1b2c3d4",
  "repoRoot": "C:\\path\\to\\repo",
  "commonGitDir": "C:\\path\\to\\repo\\.git",
  "state": "RUNNING",
  "stateReason": "run initialized",
  "strategy": "conservative",
  "goal": "修复失败门禁",
  "budget": {},
  "policy": {
    "stacks": ["typescript", "frontend-web"]
  },
  "integration": {
    "branch": "main",
    "baseSha": "...",
    "lastKnownHead": "..."
  },
  "gates": {},
  "tasks": {},
  "ownedResources": {
    "worktrees": [],
    "branches": []
  },
  "lastReconciliation": null,
  "createdAt": "...",
  "updatedAt": "..."
}
```

`state.json` 和 `active.json` 使用同目录临时文件加 `os.replace` 原子写入。`events.jsonl`
只追加审计事件；最后一行损坏时不得据此覆盖主状态。

状态文件不得保存密钥、Token、完整源码、用户数据或不必要的完整命令输出。门禁只记录
命令、退出码和足以诊断的摘要。

## 初始化

开工审计确认仓库、策略和预算后创建运行：

```text
python <state-helper> init
  --repo <repo-root>
  --strategy <conservative|balanced|feature>
  --goal <goal>
  --budget-kind <tasks|deadline|until-stop>
  --budget-value <value-if-required>
  --integration-branch <branch>
  --base-sha <sha>
  --risk-auto-approve <low|medium|high>
  --stack <stack-id> ...
  --default-concurrency <n>
  --max-concurrency <n>
  --policy-json <additional-policy-object>
  --gate <command> ...
```

助手在创建状态前：

1. 确认目标是 Git 工作树；
2. 确认 `auto-iter/runs` 没有已跟踪文件且没有解析到仓库外；
3. 幂等配置并验证 `info/exclude`；
4. 拒绝覆盖未停止的活动运行，除非 coordinator 已获得明确授权并使用
   `--replace-active`。

初始化成功后，将返回 `runId`、状态路径和 exclude 路径。把 `runId` 加入本轮运行卡。

## 同步时点

下列事件发生后立即写状态，不要等阶段结束：

- 状态在 `RUNNING`、`DRAINING`、`PAUSED`、`STOPPED` 间转换；
- 候选被接受、builder 被派发或完成；
- 任务分支、worktree 或 commit SHA 确定；池模式下 worktree 为池位绝对路径，且该
  路径在派发落账时必须写入任务记录；
- 基线、任务、完整或合并后门禁完成；
- reviewer 请求修改、任务阻塞、拒绝、合并或取消；
- coordinator 创建或清理自有 worktree/分支，含 run 启动时对池位的接管登记。

常用写命令：

```text
python <state-helper> transition --repo <repo> --to PAUSED --reason <reason>

python <state-helper> task --repo <repo> --task-id Task-01
  --status RUNNING --branch iter/<run>/<task> --worktree <absolute-path>

python <state-helper> gate --repo <repo> --phase full
  --task-id Task-01 --command <command> --exit-code 0 --summary <summary>

python <state-helper> sync-head --repo <repo> --reason <reason>

python <state-helper> resource --repo <repo>
  --action <add|remove> --kind <branch|worktree> --value <value>
```

命令行换行仅用于说明；实际调用按当前 shell 的续行规则执行。

## 只读状态与 Git 对账

读取活动状态：

```text
python <state-helper> show --repo <repo>
```

列出历史运行：

```text
python <state-helper> list --repo <repo>
```

读取并激活用户明确选择的历史运行：

```text
python <state-helper> show --repo <repo> --run-id <run-id>

python <state-helper> activate --repo <repo>
  --run-id <run-id> --reason <reason>
```

`activate` 不允许恢复 `STOPPED` 运行，也不会静默覆盖另一项未停止的活动运行。活动指针
损坏或冲突时，只有人工核对后才可使用 `--replace-active`。

只读对账：

```text
python <state-helper> reconcile --repo <repo>
```

对账必须重新检查：

- 状态记录的仓库与当前仓库是否一致；
- 集成分支是否存在、是否在仓库根检出、HEAD 是否变化；
- 集成工作树是否干净；
- 每个任务分支、commit 和 worktree 是否仍存在；
- commit 是否已包含在集成分支；
- worktree 是否注册及是否存在未提交改动。

ff-only 合并成功并确认集成工作树干净后调用 `sync-head`。创建或清理本轮分支/worktree
时调用 `resource`，确保 `ownedResources` 只包含仍由本轮负责的资源。

对账永远假设旧会话中的后台 Agent **不再运行**。`safeToResume` 只是说明 Git 现场允许
恢复协调，不代表任何任务已经完成或仍在执行。

## 恢复规则

`/iter-resume` 按以下顺序处理：

1. `show` 读取活动状态；失败时用 `list` 区分缺失、旧版本和损坏运行。只有用户明确选择
   历史 Run ID 后才调用 `activate`。
2. 调用只读 `reconcile` 并向用户报告所有 blocker。
3. 集成工作树或任务 worktree 脏、分支缺失、仓库不匹配时保持 `PAUSED`，不得自动清理。
4. 已包含在集成分支的 commit 可在人工核对后把任务标为 `MERGED`。
5. 存在但未合并且干净的任务分支进入重新审查流程；不得信任旧 Agent 报告。
6. 只有 `safeToResume` 为真且用户没有新增约束时，才把状态转换为 `RUNNING` 或原先的
   `DRAINING`。
7. 确认恢复后可运行带 `--write` 的 `reconcile` 留下对账记录。

损坏或不支持的状态文件不得自动覆盖。保留现场，报告路径，并让用户决定新建运行还是
人工修复。
