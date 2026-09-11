#!/usr/bin/env python3
"""Repository-local runtime state for the iter-loop Cursor Plugin."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
STATE_DIR = Path("auto-iter") / "runs"
EXCLUDE_RULE = "/auto-iter/runs/"
EXCLUDE_COMMENT = "# iter-loop local runtime state"
RUN_STATES = {"RUNNING", "DRAINING", "PAUSED", "STOPPED"}
TASK_STATES = {
    "CANDIDATE",
    "DISPATCHED",
    "RUNNING",
    "DONE",
    "BLOCKED",
    "MERGED",
    "REJECTED",
    "CANCELLED",
    "UNKNOWN",
}
STRATEGIES = {"conservative", "balanced", "feature"}
STACKS = {
    "typescript",
    "frontend-web",
    "python",
    "rust",
    "java",
    "react",
    "tauri",
}
RISK_LEVELS = {"low", "medium", "high"}
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class StateError(RuntimeError):
    """Raised when state cannot be read or changed safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def run_git(
    repo: Path, arguments: Iterable[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    command = ["git", "-C", str(repo), *arguments]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:
        raise StateError("未找到 git 可执行文件") from exc
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "未知 Git 错误"
        raise StateError(f"Git 命令失败：{' '.join(command)}\n{detail}")
    return result


def resolve_repo(candidate: str | Path) -> Path:
    requested = Path(candidate).expanduser().resolve()
    result = run_git(requested, ["rev-parse", "--show-toplevel"])
    root = Path(result.stdout.strip()).expanduser().resolve()
    if not root.is_dir():
        raise StateError(f"仓库根目录不存在：{root}")
    return root


def resolve_common_git_dir(repo: Path) -> Path:
    result = run_git(repo, ["rev-parse", "--git-common-dir"])
    common = Path(result.stdout.strip())
    if not common.is_absolute():
        common = repo / common
    return common.resolve()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def state_root(repo: Path) -> Path:
    return repo / STATE_DIR


def read_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise StateError(f"{label}不存在：{path}") from exc
    except UnicodeDecodeError as exc:
        raise StateError(f"{label}不是有效 UTF-8：{path}") from exc
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise StateError(f"{label}不是有效 JSON：{path} ({exc})") from exc
    if not isinstance(value, dict):
        raise StateError(f"{label}根节点必须是 JSON 对象：{path}")
    return value


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    )
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def append_event(run_dir: Path, event: dict[str, Any]) -> None:
    payload = {"at": utc_now(), **event}
    events_path = run_dir / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def ensure_untracked_state_path(repo: Path) -> None:
    auto_iter = repo / "auto-iter"
    runs = state_root(repo)
    if auto_iter.exists() and not is_within(auto_iter, repo):
        raise StateError(f"auto-iter 解析到仓库外部，拒绝使用：{auto_iter}")
    if runs.exists() and not is_within(runs, repo):
        raise StateError(f"运行状态目录解析到仓库外部，拒绝使用：{runs}")

    tracked = run_git(repo, ["ls-files", "--", "auto-iter/runs"]).stdout.strip()
    if tracked:
        raise StateError(
            "auto-iter/runs 下存在已跟踪文件，.git/info/exclude 无法保护它们：\n"
            f"{tracked}"
        )


def ensure_info_exclude(repo: Path) -> Path:
    ensure_untracked_state_path(repo)
    common_git_dir = resolve_common_git_dir(repo)
    exclude_path = common_git_dir / "info" / "exclude"
    try:
        current = exclude_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        current = ""
    except UnicodeDecodeError as exc:
        raise StateError(f".git/info/exclude 不是有效 UTF-8：{exclude_path}") from exc

    lines = current.splitlines()
    if EXCLUDE_RULE not in {line.strip() for line in lines}:
        additions: list[str] = []
        if current and not current.endswith(("\n", "\r")):
            additions.append("")
        if EXCLUDE_COMMENT not in lines:
            additions.append(EXCLUDE_COMMENT)
        additions.append(EXCLUDE_RULE)
        updated = current
        if additions:
            if updated and not updated.endswith(("\n", "\r")):
                updated += "\n"
            updated += "\n".join(additions) + "\n"
        atomic_write_text(exclude_path, updated)

    probe = run_git(
        repo,
        [
            "check-ignore",
            "--quiet",
            "--no-index",
            "--",
            "auto-iter/runs/.iter-loop-probe",
        ],
        check=False,
    )
    if probe.returncode != 0:
        raise StateError(
            f"忽略规则未生效，请检查 {exclude_path} 中的 {EXCLUDE_RULE}"
        )
    return exclude_path


def new_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{secrets.token_hex(4)}"


def state_file(repo: Path, run_id: str) -> Path:
    if not SAFE_ID_RE.fullmatch(run_id):
        raise StateError(f"非法 run id：{run_id}")
    path = state_root(repo) / run_id / "state.json"
    if not is_within(path, state_root(repo)):
        raise StateError(f"运行状态路径越界：{path}")
    return path


def active_file(repo: Path) -> Path:
    return state_root(repo) / "active.json"


def validate_state(state: dict[str, Any], path: Path) -> None:
    if state.get("schemaVersion") != SCHEMA_VERSION:
        raise StateError(
            f"不支持的状态 schemaVersion：{state.get('schemaVersion')!r} ({path})"
        )
    run_id = state.get("runId")
    if not isinstance(run_id, str) or not SAFE_ID_RE.fullmatch(run_id):
        raise StateError(f"状态文件 runId 非法：{path}")
    if state.get("state") not in RUN_STATES:
        raise StateError(f"状态文件 state 非法：{path}")
    if state.get("strategy") not in STRATEGIES:
        raise StateError(f"状态文件 strategy 非法：{path}")
    if not isinstance(state.get("tasks"), dict):
        raise StateError(f"状态文件 tasks 必须是对象：{path}")
    if not isinstance(state.get("integration"), dict):
        raise StateError(f"状态文件 integration 必须是对象：{path}")
    if not state["integration"].get("branch"):
        raise StateError(f"状态文件缺少集成分支：{path}")
    if not isinstance(state.get("gates"), dict):
        raise StateError(f"状态文件 gates 必须是对象：{path}")
    if not isinstance(state.get("ownedResources"), dict):
        raise StateError(f"状态文件 ownedResources 必须是对象：{path}")


def load_active(repo: Path) -> tuple[dict[str, Any], Path]:
    pointer_path = active_file(repo)
    pointer = read_json(pointer_path, label="活动运行指针")
    if pointer.get("schemaVersion") != SCHEMA_VERSION:
        raise StateError(
            f"活动运行指针 schemaVersion 不受支持：{pointer.get('schemaVersion')!r}"
        )
    run_id = pointer.get("runId")
    if not isinstance(run_id, str) or not SAFE_ID_RE.fullmatch(run_id):
        raise StateError(f"活动运行指针中的 runId 非法：{pointer_path}")

    path = state_file(repo, run_id)
    state = read_json(path, label="活动运行状态")
    validate_state(state, path)
    recorded_root = Path(str(state.get("repoRoot", ""))).resolve()
    if os.path.normcase(str(recorded_root)) != os.path.normcase(str(repo.resolve())):
        raise StateError(
            f"状态记录的仓库与当前仓库不一致：{recorded_root} != {repo}"
        )
    return state, path


def write_active(repo: Path, state: dict[str, Any]) -> None:
    run_id = str(state["runId"])
    pointer = {
        "schemaVersion": SCHEMA_VERSION,
        "runId": run_id,
        "state": state["state"],
        "statePath": f"{run_id}/state.json",
        "updatedAt": state["updatedAt"],
    }
    atomic_write_json(active_file(repo), pointer)


def save_state(
    repo: Path,
    state: dict[str, Any],
    path: Path,
    *,
    event: dict[str, Any] | None = None,
) -> None:
    state["updatedAt"] = utc_now()
    atomic_write_json(path, state)
    if event is not None:
        append_event(path.parent, event)
    write_active(repo, state)


def current_branch(repo: Path) -> str:
    branch = run_git(repo, ["branch", "--show-current"]).stdout.strip()
    if not branch:
        raise StateError("当前仓库处于 detached HEAD，无法确定集成分支")
    return branch


def resolve_commit(repo: Path, revision: str) -> str:
    result = run_git(repo, ["rev-parse", "--verify", f"{revision}^{{commit}}"])
    return result.stdout.strip()


def parse_json_option(raw: str | None, *, label: str) -> dict[str, Any]:
    if raw is None:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StateError(f"{label}不是有效 JSON：{exc}") from exc
    if not isinstance(value, dict):
        raise StateError(f"{label}必须是 JSON 对象")
    return value


def budget_from_args(args: argparse.Namespace) -> dict[str, Any]:
    kind = args.budget_kind
    value = args.budget_value
    if kind == "tasks":
        try:
            task_count = int(value)
        except (TypeError, ValueError) as exc:
            raise StateError("tasks 预算需要正整数 --budget-value") from exc
        if task_count <= 0:
            raise StateError("tasks 预算必须大于 0")
        return {"kind": kind, "value": task_count}
    if kind == "deadline":
        if not value:
            raise StateError("deadline 预算需要 --budget-value")
        return {"kind": kind, "value": value, "timezone": args.timezone}
    if value:
        raise StateError("until-stop 预算不接受 --budget-value")
    return {"kind": kind, "value": None}


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    exclude_path = ensure_info_exclude(repo)
    runs = state_root(repo)
    runs.mkdir(parents=True, exist_ok=True)

    if active_file(repo).exists() and not args.replace_active:
        existing, _ = load_active(repo)
        if existing["state"] != "STOPPED":
            raise StateError(
                "已有未停止的活动运行；请先 /iter-status、/iter-resume 或 /iter-stop"
            )

    branch = args.integration_branch or current_branch(repo)
    branch_head = resolve_commit(repo, f"refs/heads/{branch}")
    base_sha = (
        resolve_commit(repo, args.base_sha) if args.base_sha else branch_head
    )
    if not is_ancestor(repo, base_sha, branch_head):
        raise StateError("基准 SHA 不是集成分支 HEAD 的祖先")
    run_id = args.run_id or new_run_id()
    path = state_file(repo, run_id)
    if path.exists():
        raise StateError(f"run id 已存在：{run_id}")

    policy_extra = parse_json_option(args.policy_json, label="--policy-json")
    policy = {
        "stacks": args.stack or [],
        "allowed": args.allow or [],
        "excluded": args.exclude or [],
        "riskAutoApprove": args.risk_auto_approve,
        "defaultConcurrency": args.default_concurrency,
        "maxConcurrency": args.max_concurrency,
        **policy_extra,
    }
    default_concurrency = policy.get("defaultConcurrency")
    max_concurrency = policy.get("maxConcurrency")
    if (
        not isinstance(default_concurrency, int)
        or isinstance(default_concurrency, bool)
        or not isinstance(max_concurrency, int)
        or isinstance(max_concurrency, bool)
        or not 1 <= default_concurrency <= max_concurrency <= 4
    ):
        raise StateError("并发范围必须满足 1 <= 默认并发 <= 最大并发 <= 4")
    if policy.get("riskAutoApprove") not in RISK_LEVELS:
        raise StateError("自动执行风险上限必须是 low、medium 或 high")
    stacks = policy.get("stacks")
    if (
        not isinstance(stacks, list)
        or any(not isinstance(stack, str) or stack not in STACKS for stack in stacks)
        or len(stacks) != len(set(stacks))
    ):
        raise StateError("技术栈包必须是无重复的已知 stack 列表")

    now = utc_now()
    state: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "runId": run_id,
        "repoRoot": str(repo),
        "commonGitDir": str(resolve_common_git_dir(repo)),
        "state": "RUNNING",
        "stateReason": "run initialized",
        "strategy": args.strategy,
        "goal": args.goal,
        "budget": budget_from_args(args),
        "policy": policy,
        "integration": {
            "branch": branch,
            "baseSha": base_sha,
            "lastKnownHead": branch_head,
        },
        "gates": {
            "commands": args.gate or [],
            "baseline": [],
            "records": [],
        },
        "tasks": {},
        "ownedResources": {"worktrees": [], "branches": []},
        "lastReconciliation": None,
        "createdAt": now,
        "updatedAt": now,
    }
    atomic_write_json(path, state)
    append_event(
        path.parent,
        {
            "type": "run-created",
            "state": "RUNNING",
            "strategy": args.strategy,
            "baseSha": base_sha,
        },
    )
    write_active(repo, state)
    return {
        "runId": run_id,
        "statePath": str(path),
        "excludePath": str(exclude_path),
        "state": state,
    }


def command_show(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    if args.run_id:
        path = state_file(repo, args.run_id)
        state = read_json(path, label="运行状态")
        validate_state(state, path)
        if normalized_path(state.get("repoRoot", "")) != normalized_path(repo):
            raise StateError("所选运行记录属于其他仓库")
    else:
        state, path = load_active(repo)
    return {"statePath": str(path), "state": state}


def command_list(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    runs = state_root(repo)
    summaries: list[dict[str, Any]] = []
    if runs.is_dir():
        for path in sorted(runs.glob("*/state.json"), reverse=True):
            try:
                state = read_json(path, label="运行状态")
                validate_state(state, path)
                summaries.append(
                    {
                        "runId": state["runId"],
                        "state": state["state"],
                        "strategy": state["strategy"],
                        "goal": state.get("goal"),
                        "updatedAt": state.get("updatedAt"),
                        "statePath": str(path),
                    }
                )
            except StateError as exc:
                summaries.append(
                    {
                        "runId": path.parent.name,
                        "state": "CORRUPT",
                        "error": str(exc),
                        "statePath": str(path),
                    }
                )
    return {"repoRoot": str(repo), "runs": summaries}


def command_activate(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    path = state_file(repo, args.run_id)
    state = read_json(path, label="待激活运行状态")
    validate_state(state, path)
    if normalized_path(state.get("repoRoot", "")) != normalized_path(repo):
        raise StateError("待激活运行记录属于其他仓库")
    if state["state"] == "STOPPED":
        raise StateError("不能激活已经 STOPPED 的运行；请使用 /iter-loop 创建新运行")

    pointer = active_file(repo)
    if pointer.exists() and not args.replace_active:
        try:
            current, _ = load_active(repo)
        except StateError as exc:
            raise StateError(
                "活动指针存在但无法读取；人工确认后使用 --replace-active"
            ) from exc
        if current["runId"] != state["runId"] and current["state"] != "STOPPED":
            raise StateError(
                "已有其他未停止的活动运行；请先停止它或明确使用 --replace-active"
            )
        if current["runId"] == state["runId"]:
            return {
                "runId": state["runId"],
                "statePath": str(path),
                "alreadyActive": True,
            }

    write_active(repo, state)
    append_event(
        path.parent,
        {
            "type": "run-activated",
            "reason": args.reason,
        },
    )
    return {
        "runId": state["runId"],
        "statePath": str(path),
        "alreadyActive": False,
    }


def command_transition(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    state, path = load_active(repo)
    previous = state["state"]
    target = args.to
    allowed = {
        "RUNNING": {"RUNNING", "DRAINING", "PAUSED", "STOPPED"},
        "DRAINING": {"RUNNING", "DRAINING", "PAUSED", "STOPPED"},
        "PAUSED": {"RUNNING", "DRAINING", "PAUSED", "STOPPED"},
        "STOPPED": {"STOPPED"},
    }
    if target not in allowed[previous]:
        raise StateError(f"不允许的状态转换：{previous} -> {target}")
    state["state"] = target
    state["stateReason"] = args.reason
    save_state(
        repo,
        state,
        path,
        event={
            "type": "state-transition",
            "from": previous,
            "to": target,
            "reason": args.reason,
        },
    )
    return {"runId": state["runId"], "from": previous, "to": target}


def update_if_present(
    target: dict[str, Any], key: str, value: Any, changed: dict[str, Any]
) -> None:
    if value is not None:
        target[key] = value
        changed[key] = value


def command_task(args: argparse.Namespace) -> dict[str, Any]:
    if not SAFE_ID_RE.fullmatch(args.task_id):
        raise StateError(f"非法 task id：{args.task_id}")
    repo = resolve_repo(args.repo)
    state, path = load_active(repo)
    tasks = state["tasks"]
    now = utc_now()
    task = tasks.get(args.task_id)
    if task is None:
        task = {
            "id": args.task_id,
            "status": "CANDIDATE",
            "createdAt": now,
            "updatedAt": now,
            "notes": [],
        }
        tasks[args.task_id] = task

    changed: dict[str, Any] = {}
    update_if_present(task, "title", args.title, changed)
    update_if_present(task, "status", args.status, changed)
    update_if_present(task, "branch", args.branch, changed)
    update_if_present(task, "commit", args.commit, changed)
    update_if_present(task, "risk", args.risk, changed)
    update_if_present(task, "allowed", args.allow, changed)
    update_if_present(task, "forbidden", args.forbid, changed)
    update_if_present(task, "acceptance", args.acceptance, changed)
    if args.worktree is not None:
        worktree = str(Path(args.worktree).expanduser().resolve())
        task["worktree"] = worktree
        changed["worktree"] = worktree
    if args.note:
        task.setdefault("notes", []).append({"at": now, "text": args.note})
        changed["note"] = args.note

    task["updatedAt"] = now
    resources = state.setdefault(
        "ownedResources", {"worktrees": [], "branches": []}
    )
    if args.branch and args.branch not in resources["branches"]:
        resources["branches"].append(args.branch)
    if args.worktree:
        worktree_value = task["worktree"]
        if worktree_value not in resources["worktrees"]:
            resources["worktrees"].append(worktree_value)

    save_state(
        repo,
        state,
        path,
        event={
            "type": "task-updated",
            "taskId": args.task_id,
            "changed": changed,
        },
    )
    return {"runId": state["runId"], "task": task}


def command_gate(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    state, path = load_active(repo)
    if args.task_id and args.task_id not in state["tasks"]:
        raise StateError(f"未知 task id：{args.task_id}")
    record = {
        "at": utc_now(),
        "phase": args.phase,
        "taskId": args.task_id,
        "command": args.command,
        "exitCode": args.exit_code,
        "summary": args.summary,
    }
    state["gates"].setdefault("records", []).append(record)
    if args.phase == "baseline":
        state["gates"].setdefault("baseline", []).append(record)
    save_state(
        repo,
        state,
        path,
        event={
            "type": "gate-recorded",
            "taskId": args.task_id,
            "phase": args.phase,
            "exitCode": args.exit_code,
        },
    )
    return {"runId": state["runId"], "gate": record}


def command_event(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    state, path = load_active(repo)
    data = parse_json_option(args.data_json, label="--data-json")
    event = {
        "type": args.type,
        "taskId": args.task_id,
        "message": args.message,
        "data": data,
    }
    append_event(path.parent, event)
    return {"runId": state["runId"], "event": event}


def parse_worktrees(repo: Path) -> list[dict[str, Any]]:
    output = run_git(repo, ["worktree", "list", "--porcelain"]).stdout
    worktrees: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in [*output.splitlines(), ""]:
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["path"] = str(Path(value).resolve())
        elif key == "HEAD":
            current["head"] = value
        elif key == "branch":
            current["branchRef"] = value
            current["branch"] = value.removeprefix("refs/heads/")
        elif key in {"detached", "bare", "prunable", "locked"}:
            current[key] = value or True
    return worktrees


def git_status(repo: Path) -> dict[str, Any]:
    result = run_git(
        repo,
        ["status", "--porcelain=v1", "--untracked-files=normal"],
        check=False,
    )
    return {
        "available": result.returncode == 0,
        "dirty": bool(result.stdout.strip()) if result.returncode == 0 else None,
        "entries": result.stdout.splitlines() if result.returncode == 0 else [],
        "error": result.stderr.strip() if result.returncode != 0 else None,
    }


def try_resolve_commit(repo: Path, revision: str | None) -> str | None:
    if not revision:
        return None
    result = run_git(
        repo,
        ["rev-parse", "--verify", f"{revision}^{{commit}}"],
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    result = run_git(
        repo,
        ["merge-base", "--is-ancestor", ancestor, descendant],
        check=False,
    )
    return result.returncode == 0


def normalized_path(path: str | Path) -> str:
    return os.path.normcase(str(Path(path).expanduser().resolve()))


def build_reconciliation(repo: Path, state: dict[str, Any]) -> dict[str, Any]:
    integration = state["integration"]
    branch = str(integration["branch"])
    integration_ref = f"refs/heads/{branch}"
    actual_head = try_resolve_commit(repo, integration_ref)
    stored_head = integration.get("lastKnownHead")
    root_status = git_status(repo)
    actual_current_branch_result = run_git(
        repo, ["branch", "--show-current"], check=False
    )
    actual_current_branch = (
        actual_current_branch_result.stdout.strip()
        if actual_current_branch_result.returncode == 0
        else None
    )
    worktrees = parse_worktrees(repo)
    worktree_by_path = {
        normalized_path(item["path"]): item for item in worktrees if item.get("path")
    }

    task_reports: dict[str, Any] = {}
    unresolved_dirty_task = False
    for task_id, task in state["tasks"].items():
        branch_name = task.get("branch")
        branch_sha = try_resolve_commit(
            repo, f"refs/heads/{branch_name}" if branch_name else None
        )
        commit_sha = try_resolve_commit(repo, task.get("commit"))
        worktree_value = task.get("worktree")
        registered = (
            worktree_by_path.get(normalized_path(worktree_value))
            if worktree_value
            else None
        )
        worktree_exists = (
            Path(worktree_value).expanduser().exists() if worktree_value else False
        )
        worktree_status = (
            git_status(Path(worktree_value).expanduser().resolve())
            if registered and worktree_exists
            else None
        )
        dirty = worktree_status.get("dirty") if worktree_status else None
        if dirty:
            unresolved_dirty_task = True
        merged = (
            bool(commit_sha and actual_head)
            and is_ancestor(repo, str(commit_sha), str(actual_head))
        )
        if merged:
            inferred = "MERGED"
        elif dirty:
            inferred = "NEEDS_INSPECTION"
        elif branch_sha:
            inferred = "UNMERGED"
        elif worktree_exists or registered:
            inferred = "WORKTREE_WITHOUT_BRANCH"
        else:
            inferred = "MISSING"
        task_reports[task_id] = {
            "recordedStatus": task.get("status"),
            "branch": branch_name,
            "branchExists": branch_sha is not None,
            "branchHead": branch_sha,
            "recordedCommit": task.get("commit"),
            "commitExists": commit_sha is not None,
            "commitMerged": merged,
            "worktree": worktree_value,
            "worktreeExists": worktree_exists,
            "worktreeRegistered": registered is not None,
            "worktreeDirty": dirty,
            "inferredStatus": inferred,
        }

    repo_matches = normalized_path(state["repoRoot"]) == normalized_path(repo)
    branch_exists = actual_head is not None
    branch_checked_out = actual_current_branch == branch
    root_clean = root_status["dirty"] is False
    resumable_state = state["state"] in {"RUNNING", "DRAINING", "PAUSED"}
    safe_to_resume = all(
        [
            repo_matches,
            branch_exists,
            branch_checked_out,
            root_clean,
            not unresolved_dirty_task,
            resumable_state,
        ]
    )

    return {
        "at": utc_now(),
        "runId": state["runId"],
        "recordedState": state["state"],
        "recordedStateReason": state.get("stateReason"),
        "backgroundAgentsAssumedRunning": False,
        "repo": {
            "recordedRoot": state["repoRoot"],
            "actualRoot": str(repo),
            "matches": repo_matches,
        },
        "integration": {
            "branch": branch,
            "branchExists": branch_exists,
            "checkedOutInRepoRoot": branch_checked_out,
            "storedBaseSha": integration.get("baseSha"),
            "storedLastKnownHead": stored_head,
            "actualHead": actual_head,
            "headChanged": bool(
                stored_head and actual_head and str(stored_head) != str(actual_head)
            ),
            "worktree": root_status,
        },
        "tasks": task_reports,
        "safeToResume": safe_to_resume,
        "resumeBlockers": [
            message
            for condition, message in (
                (not repo_matches, "状态仓库与当前仓库不一致"),
                (not branch_exists, "集成分支不存在"),
                (not branch_checked_out, "仓库根未检出记录的集成分支"),
                (not root_clean, "集成工作树不干净或状态未知"),
                (unresolved_dirty_task, "至少一个任务 worktree 存在未提交改动"),
                (not resumable_state, "运行已处于 STOPPED"),
            )
            if condition
        ],
    }


def command_reconcile(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    state, path = load_active(repo)
    report = build_reconciliation(repo, state)
    if args.write:
        state["lastReconciliation"] = report
        save_state(
            repo,
            state,
            path,
            event={
                "type": "git-reconciled",
                "safeToResume": report["safeToResume"],
                "blockers": report["resumeBlockers"],
            },
        )
    return report


def command_sync_head(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    state, path = load_active(repo)
    branch = str(state["integration"]["branch"])
    checked_out = current_branch(repo)
    if checked_out != branch:
        raise StateError(
            f"仓库根当前分支不是记录的集成分支：{checked_out} != {branch}"
        )
    status = git_status(repo)
    if status["dirty"] is not False:
        raise StateError("集成工作树不干净或状态未知，拒绝同步 HEAD")
    actual_head = resolve_commit(repo, f"refs/heads/{branch}")
    previous = state["integration"].get("lastKnownHead")
    state["integration"]["lastKnownHead"] = actual_head
    save_state(
        repo,
        state,
        path,
        event={
            "type": "integration-head-synced",
            "from": previous,
            "to": actual_head,
            "reason": args.reason,
        },
    )
    return {
        "runId": state["runId"],
        "branch": branch,
        "from": previous,
        "to": actual_head,
    }


def command_resource(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    state, path = load_active(repo)
    resources = state.setdefault(
        "ownedResources", {"worktrees": [], "branches": []}
    )
    key = "worktrees" if args.kind == "worktree" else "branches"
    value = (
        str(Path(args.value).expanduser().resolve())
        if args.kind == "worktree"
        else args.value
    )
    values = resources.setdefault(key, [])
    if args.action == "add" and value not in values:
        values.append(value)
    elif args.action == "remove" and value in values:
        values.remove(value)
    save_state(
        repo,
        state,
        path,
        event={
            "type": "owned-resource-updated",
            "action": args.action,
            "kind": args.kind,
            "value": value,
            "note": args.note,
        },
    )
    return {
        "runId": state["runId"],
        "action": args.action,
        "kind": args.kind,
        "value": value,
        "ownedResources": resources,
    }


def command_ensure_ignore(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo)
    exclude_path = ensure_info_exclude(repo)
    return {
        "repoRoot": str(repo),
        "excludePath": str(exclude_path),
        "rule": EXCLUDE_RULE,
    }


def add_repo_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo",
        default=".",
        help="目标 Git 仓库内的路径，默认当前目录",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "在目标仓库的 auto-iter/runs 中维护 iter-loop 状态；"
            "所有输出均为 UTF-8 JSON。"
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="创建新的活动运行")
    add_repo_argument(init)
    init.add_argument("--strategy", choices=sorted(STRATEGIES), required=True)
    init.add_argument("--goal", required=True)
    init.add_argument(
        "--budget-kind",
        choices=("tasks", "deadline", "until-stop"),
        default="tasks",
    )
    init.add_argument("--budget-value")
    init.add_argument("--timezone")
    init.add_argument("--integration-branch")
    init.add_argument("--base-sha")
    init.add_argument("--risk-auto-approve", choices=sorted(RISK_LEVELS), default="low")
    init.add_argument("--stack", choices=sorted(STACKS), action="append")
    init.add_argument("--default-concurrency", type=int, default=1)
    init.add_argument("--max-concurrency", type=int, choices=range(1, 5), default=2)
    init.add_argument("--allow", action="append")
    init.add_argument("--exclude", action="append")
    init.add_argument("--gate", action="append")
    init.add_argument("--policy-json")
    init.add_argument("--run-id")
    init.add_argument("--replace-active", action="store_true")
    init.set_defaults(handler=command_init)

    show = subparsers.add_parser("show", help="输出活动运行状态")
    add_repo_argument(show)
    show.add_argument("--run-id", help="读取指定历史运行，不改变活动指针")
    show.set_defaults(handler=command_show)

    list_runs = subparsers.add_parser("list", help="列出仓库内的历史运行")
    add_repo_argument(list_runs)
    list_runs.set_defaults(handler=command_list)

    activate = subparsers.add_parser("activate", help="激活用户明确选择的历史运行")
    add_repo_argument(activate)
    activate.add_argument("--run-id", required=True)
    activate.add_argument("--reason", required=True)
    activate.add_argument("--replace-active", action="store_true")
    activate.set_defaults(handler=command_activate)

    transition = subparsers.add_parser("transition", help="转换活动运行状态")
    add_repo_argument(transition)
    transition.add_argument("--to", choices=sorted(RUN_STATES), required=True)
    transition.add_argument("--reason", required=True)
    transition.set_defaults(handler=command_transition)

    task = subparsers.add_parser("task", help="新增或更新任务记录")
    add_repo_argument(task)
    task.add_argument("--task-id", required=True)
    task.add_argument("--title")
    task.add_argument("--status", choices=sorted(TASK_STATES))
    task.add_argument("--branch")
    task.add_argument("--worktree")
    task.add_argument("--commit")
    task.add_argument("--risk", choices=sorted(RISK_LEVELS))
    task.add_argument("--allow", action="append")
    task.add_argument("--forbid", action="append")
    task.add_argument("--acceptance", action="append")
    task.add_argument("--note")
    task.set_defaults(handler=command_task)

    gate = subparsers.add_parser("gate", help="记录一次门禁结果")
    add_repo_argument(gate)
    gate.add_argument(
        "--phase",
        choices=("baseline", "task", "full", "postmerge"),
        required=True,
    )
    gate.add_argument("--task-id")
    gate.add_argument("--command", required=True)
    gate.add_argument("--exit-code", type=int, required=True)
    gate.add_argument("--summary", required=True)
    gate.set_defaults(handler=command_gate)

    event = subparsers.add_parser("event", help="追加审计事件")
    add_repo_argument(event)
    event.add_argument("--type", required=True)
    event.add_argument("--task-id")
    event.add_argument("--message", required=True)
    event.add_argument("--data-json")
    event.set_defaults(handler=command_event)

    reconcile = subparsers.add_parser("reconcile", help="将状态与实际 Git 对账")
    add_repo_argument(reconcile)
    reconcile.add_argument(
        "--write",
        action="store_true",
        help="将对账报告写入状态；默认只读输出",
    )
    reconcile.set_defaults(handler=command_reconcile)

    sync_head = subparsers.add_parser(
        "sync-head", help="确认集成工作树干净后记录当前 HEAD"
    )
    add_repo_argument(sync_head)
    sync_head.add_argument("--reason", required=True)
    sync_head.set_defaults(handler=command_sync_head)

    resource = subparsers.add_parser("resource", help="维护本轮自有分支和 worktree")
    add_repo_argument(resource)
    resource.add_argument("--action", choices=("add", "remove"), required=True)
    resource.add_argument("--kind", choices=("branch", "worktree"), required=True)
    resource.add_argument("--value", required=True)
    resource.add_argument("--note")
    resource.set_defaults(handler=command_resource)

    ensure_ignore = subparsers.add_parser(
        "ensure-ignore", help="幂等配置 .git/info/exclude"
    )
    add_repo_argument(ensure_ignore)
    ensure_ignore.set_defaults(handler=command_ensure_ignore)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.handler(args)
    except (StateError, OSError) as exc:
        print(
            json.dumps(
                {"ok": False, "error": str(exc)},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
