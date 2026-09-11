---
name: iter-stop
description: 读取仓库内持久状态并安全停止当前 iter-loop，在有在飞任务时选择收尾或立即停止并保留可恢复现场。
---

# 停止 Iter Loop

停止当前仓库中的 `iter-loop`。此命令不得启动新任务或扩大任何已有任务范围，所有状态
转换通过插件内 `skills/iter-loop/scripts/state_store.py` 落账。

## 处理流程

1. 运行 `show --repo <repo-root>` 读取活动状态，再运行不带 `--write` 的 `reconcile` 与
   Git 现场对账。状态缺失或损坏时报告并停止，不得新建状态掩盖问题。
2. 立即停止新的候选生成和任务派发。
3. 没有在飞任务时：
   - 使用 `transition --to STOPPED --reason <reason>` 持久化停止状态；
   - 只读核对集成分支和遗留 worktree；
   - 输出停止摘要。
4. 存在在飞任务时，使用结构化选择题让用户选择：
   - **安全收尾（推荐）**：进入 `DRAINING`，允许已在飞任务完成；只有通过审查和完整
     门禁的提交才可合并，不再补位。
   - **立即停止**：停止进一步修改；在工具支持且用户已作此选择时中断后台代理，不 rebase、
     不合并、不清理未完成 worktree，保留现场。
5. 选择安全收尾后，先持久化 `DRAINING`；每个任务完成或阻塞后更新状态，最后持久化
   `STOPPED`。
6. 选择立即停止后，记录仍在运行、已中断和状态未知的任务，再持久化 `STOPPED`。旧 Agent
   是否真正终止必须依据工具结果，不得猜测。

不得把“停止”解释为 reset、丢弃改动、删除分支或强制清理。任何未验证提交都保持未合并。
状态写入失败时不再执行新的 Git 修改，并报告状态文件路径和实际现场。

## 安全收尾摘要

安全收尾完成后报告：

```text
Iter Loop: STOPPED
停止方式: 安全收尾
Run ID 与状态文件:
已合并:
- Task ID / commit / 门禁
未合并:
- Task ID / branch / worktree / 原因
残留资源:
- worktree / branch / 是否可安全清理
既有与新增失败:
- 证据
```

## 立即停止摘要

```text
Iter Loop: STOPPED
停止方式: 立即停止
Run ID 与状态文件:
已中断或仍在运行的代理:
- agent / Task ID / 状态
保留现场:
- branch / worktree / commit 或未提交状态
未执行:
- 审查、门禁、合并或清理
建议恢复方式:
- 下一次会话调用 /iter-resume 后需要核对的第一步
```

只报告能够从会话和实际 Git 状态核对的事实。
