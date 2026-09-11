---
name: iter-status
description: 只读读取仓库内持久状态并与 Git 对账，汇总当前 iter-loop 的任务、worktree、门禁和阻塞事项。
---

# Iter Loop 状态

只读报告当前仓库中的 `iter-loop` 状态。不得借此命令启动新任务、修改文件、写回状态、
切换分支、清理 worktree、提交或合并。

## 核对顺序

1. 定位插件内 `skills/iter-loop/scripts/state_store.py`，不得复制到目标仓库。
2. 在当前 Git 仓库运行 `show --repo <repo-root>`，读取 `auto-iter/runs/active.json` 指向的
   状态。
3. 运行不带 `--write` 的 `reconcile --repo <repo-root>`，核对：
   - 集成分支、HEAD 和工作树是否干净；
   - 状态中的任务分支和 worktree 是否仍存在；
   - 已记录 commit 是否确实包含在集成分支中；
   - 任务记录与推断状态是否冲突。
4. `show` 失败时可运行只读 `list`，区分无运行记录、活动指针损坏和历史状态损坏。
5. 不运行可能生成或修改文件的构建、测试和格式化命令，不向对账命令添加 `--write`。
6. 无法核对的内容标记为 `UNKNOWN`，不要用会话记录代替持久状态或 Git 证据。
7. 旧会话中的后台 Agent 一律视为不再运行，不能仅凭状态中的 `RUNNING` 断言仍在执行。
8. 没有活动或可恢复的 iter-loop 时报告 `INACTIVE`，不要自动启动或创建状态。

## 输出格式

```text
Iter Loop: RUNNING | DRAINING | PAUSED | STOPPED | INACTIVE
Run ID:
状态文件:
策略:
目标:
预算与剩余量:
集成分支与 HEAD:
工作树状态: CLEAN | DIRTY | UNKNOWN
安全恢复: YES | NO

已合并:
- Task ID / commit / 验证证据

在飞:
- Task ID / agent / branch / worktree / 影响面

已完成未合并:
- Task ID / commit / 待完成步骤

阻塞:
- Task ID / 原因 / 所需决策
- Git 对账 blocker

门禁:
- 基线结果
- 最近完整门禁结果

下一步:
- 当前状态允许的唯一下一动作
```

如果持久状态与 Git 现场冲突，列出冲突并建议进入 `PAUSED`；状态命令本身不写状态或
执行修复。状态文件损坏时报告准确路径，不覆盖或重新初始化。
