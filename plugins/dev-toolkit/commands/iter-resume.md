---
name: iter-resume
description: 从仓库的 .auto-iter/runs 持久状态恢复 iter-loop，重新核对 Git 现场后安全重建协调流程。
---

# 恢复 Iter Loop

从当前 Git 仓库恢复一次未完成的 `iter-loop`。恢复不代表旧会话中的后台 Agent 仍然运行；
所有旧 Agent 一律视为已失联，必须根据持久状态和实际 Git 重新判断。

## 恢复流程

1. 定位插件内 `skills/iter-loop/scripts/state_store.py`，不得复制到目标仓库。
2. 运行 `show --repo <repo-root>`：
   - 没有活动指针时运行 `list`，让用户明确选择 Run ID；
   - 先用 `show --run-id <run-id>` 核对所选历史，再用 `activate --run-id <run-id>`
     恢复活动指针；
   - 状态损坏或 schema 不支持时报告准确路径，不覆盖、不迁移；
   - 状态为 `STOPPED` 时不恢复，提示用户使用 `/iter-loop` 创建新运行。
3. 阅读主 Skill、所选策略和 `references/state-protocol.md`，恢复运行卡、预算、排除项、
   风险阈值和门禁。
4. 运行不带 `--write` 的 `reconcile --repo <repo-root>`。逐项核对：
   - 仓库根、集成分支和 HEAD；
   - 集成工作树及任务 worktree 的干净状态；
   - 任务分支、commit 和 worktree 是否存在；
   - commit 是否已包含在集成分支；
   - 预算或截止时间是否仍有效。
5. `safeToResume` 为 false 时：
   - 能安全写状态则转换为 `PAUSED` 并记录 blocker；
   - 不 reset、stash、清理、切换分支或自动解决冲突；
   - 提出一个能解除当前 blocker 的明确问题。
6. Git 现场安全后运行 `ensure-ignore`，确认 `/.auto-iter/runs/` 仍被当前 clone 忽略，再运行
   带 `--write` 的 `reconcile` 保存对账证据。
7. 核对现存池位：优先接管并复用热依赖，不重装；缺失槽位才新建，依赖损坏
   先重装；池位带遗留分支时按集成分支包含性核对后处置，脏池位报告询问、不自动
   清理。
8. 重建任务状态：
   - commit 已在集成分支：核对后标记 `MERGED`；
   - 分支和 worktree 存在、干净但未合并：标记 `UNKNOWN`，重新检查 diff、完整门禁和
     reviewer，不信任旧报告；
   - worktree 有未提交改动：保持 `PAUSED`，让用户决定保留、人工提交或放弃；
   - 分支或 worktree 缺失：标记 `BLOCKED`，不自动重建为同名资源；
   - 状态为 `RUNNING` 的旧任务：不得宣称 Agent 仍在运行。
9. 恢复状态：
   - 原状态为 `DRAINING` 时保持 `DRAINING`，只收尾，不补位；
   - 原状态为 `PAUSED` 时，先确认原暂停原因已经解除；
   - 原状态为 `RUNNING` 且预算有效时恢复 `RUNNING`；
   - 截止时间已过时进入 `DRAINING`，没有待收尾任务则转为 `STOPPED`。
10. 展示恢复后的运行卡，再继续审查、合并或派发。任何新动作前先把对应任务写入状态。

## 恢复摘要

```text
Iter Loop: RUNNING | DRAINING | PAUSED
Run ID:
状态文件:
策略:
目标与剩余预算:
集成分支:
记录 HEAD / 实际 HEAD:

已确认合并:
- Task ID / commit

待重新审查:
- Task ID / branch / worktree / commit

需要人工处理:
- Task ID / Git 现场 / blocker

旧 Agent:
- 一律不假设仍在运行

下一动作:
- 恢复后唯一允许的下一步
```

恢复成功只表示协调状态已重建，不表示任务验收、门禁或合并可以跳过。
