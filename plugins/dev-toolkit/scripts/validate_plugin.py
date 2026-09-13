#!/usr/bin/env python3
"""Validate the dev-toolkit plugin (Cursor + Claude 双清单) without third-party dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / ".cursor-plugin" / "plugin.json"
MARKETPLACE_MANIFEST_PATHS = (
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / "package.json",
)
EXPECTED_STRATEGIES = {"conservative", "balanced", "feature"}
EXPECTED_STACKS = {
    "typescript",
    "frontend-web",
    "python",
    "rust",
    "java",
    "react",
    "tauri",
}
COMPONENT_KEYS = ("skills", "agents", "commands")
NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FORBIDDEN_OPERATION_RE = re.compile(
    r"\b(?:git\s+reset\s+--hard|git\s+clean\s+-[a-z]*f|git\s+checkout\s+--|rm\s+-rf)\b",
    re.IGNORECASE,
)


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.error(message)


def read_text(path: Path, validation: Validation) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        validation.error(f"缺少文件：{path.relative_to(ROOT)}")
    except UnicodeDecodeError as exc:
        validation.error(f"文件不是有效 UTF-8：{path.relative_to(ROOT)} ({exc})")
    return ""


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value in {"true", "false"}:
        return value == "true"
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_frontmatter(
    path: Path, validation: Validation
) -> tuple[dict[str, Any], str]:
    text = read_text(path, validation)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        validation.error(f"缺少 YAML frontmatter：{path.relative_to(ROOT)}")
        return {}, text

    try:
        closing = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration:
        validation.error(f"frontmatter 未闭合：{path.relative_to(ROOT)}")
        return {}, text

    metadata: dict[str, Any] = {}
    for line_number, line in enumerate(lines[1:closing], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            validation.error(
                f"frontmatter 行缺少冒号：{path.relative_to(ROOT)}:{line_number}"
            )
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not key:
            validation.error(
                f"frontmatter 键为空：{path.relative_to(ROOT)}:{line_number}"
            )
            continue
        if key in metadata:
            validation.error(
                f"frontmatter 键重复：{path.relative_to(ROOT)}:{line_number} ({key})"
            )
            continue
        metadata[key] = parse_scalar(raw_value)

    return metadata, "\n".join(lines[closing + 1 :])


def validate_name_and_description(
    path: Path, metadata: dict[str, Any], validation: Validation
) -> None:
    relative = path.relative_to(ROOT)
    name = metadata.get("name")
    description = metadata.get("description")
    validation.require(
        isinstance(name, str) and bool(NAME_RE.fullmatch(name)) and len(name) <= 64,
        f"组件 name 非法：{relative}",
    )
    validation.require(
        isinstance(description, str) and 0 < len(description) <= 1024,
        f"组件 description 缺失或过长：{relative}",
    )


def component_paths(
    manifest: dict[str, Any], key: str, validation: Validation
) -> list[Path]:
    raw = manifest.get(key)
    if raw is None:
        validation.error(f"manifest 未声明组件路径：{key}")
        return []

    values = [raw] if isinstance(raw, str) else raw
    if not isinstance(values, list) or not values:
        validation.error(f"manifest 组件路径必须是字符串或非空数组：{key}")
        return []

    paths: list[Path] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            validation.error(f"manifest 组件路径无效：{key}={value!r}")
            continue
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            validation.error(f"manifest 组件路径必须位于插件内：{key}={value}")
            continue
        resolved = (ROOT / relative).resolve()
        try:
            resolved.relative_to(ROOT)
        except ValueError:
            validation.error(f"manifest 组件路径越界：{key}={value}")
            continue
        if not resolved.is_dir():
            validation.error(f"manifest 组件目录不存在：{key}={value}")
            continue
        paths.append(resolved)
    return paths


def validate_manifest(validation: Validation) -> dict[str, Any]:
    text = read_text(MANIFEST_PATH, validation)
    if not text:
        return {}
    try:
        manifest = json.loads(text)
    except json.JSONDecodeError as exc:
        validation.error(f"plugin.json 不是有效 JSON：{exc}")
        return {}

    if not isinstance(manifest, dict):
        validation.error("plugin.json 根节点必须是对象")
        return {}

    name = manifest.get("name")
    version = manifest.get("version")
    description = manifest.get("description")
    validation.require(
        isinstance(name, str) and bool(NAME_RE.fullmatch(name)),
        "manifest name 缺失或格式非法",
    )
    validation.require(
        isinstance(version, str) and bool(SEMVER_RE.fullmatch(version)),
        "manifest version 必须是语义化版本",
    )
    validation.require(
        isinstance(description, str) and bool(description.strip()),
        "manifest description 缺失",
    )
    for key in COMPONENT_KEYS:
        component_paths(manifest, key, validation)
    return manifest


def validate_marketplace_manifests(
    manifest: dict[str, Any], validation: Validation
) -> None:
    name = manifest.get("name")
    version = manifest.get("version")
    for path in MARKETPLACE_MANIFEST_PATHS:
        relative = path.relative_to(ROOT).as_posix()
        text = read_text(path, validation)
        if not text:
            continue
        try:
            extra = json.loads(text)
        except json.JSONDecodeError as exc:
            validation.error(f"{relative} 不是有效 JSON：{exc}")
            continue
        if not isinstance(extra, dict):
            validation.error(f"{relative} 根节点必须是对象")
            continue
        validation.require(
            extra.get("name") == name,
            f"{relative} name 与 Cursor manifest 不一致",
        )
        validation.require(
            extra.get("version") == version,
            f"{relative} version 与 Cursor manifest 不一致",
        )


def validate_components(validation: Validation) -> dict[str, int]:
    skill_paths = sorted((ROOT / "skills").rglob("SKILL.md"))
    agent_paths = sorted((ROOT / "agents").glob("*.md"))
    command_paths = sorted((ROOT / "commands").glob("*.md"))

    validation.require(
        {"init", "iter-loop"} <= {path.parent.name for path in skill_paths},
        "缺少必需 Skill：init 或 iter-loop",
    )
    validation.require(
        {path.stem for path in agent_paths}
        == {"iter-scout", "iter-builder", "iter-verifier", "iter-reviewer"},
        "Agent 文件集合与 v0.3.1 契约不一致",
    )
    validation.require(
        {path.stem for path in command_paths}
        == {"iter-status", "iter-stop", "iter-resume"},
        "Command 文件集合与 v0.3 契约不一致",
    )

    names: list[str] = []
    for path in [*skill_paths, *agent_paths, *command_paths]:
        metadata, _ = parse_frontmatter(path, validation)
        validate_name_and_description(path, metadata, validation)
        name = metadata.get("name")
        if isinstance(name, str):
            names.append(name)

    validation.require(
        len(names) == len(set(names)), "Skill、Agent 与 Command 名称必须唯一"
    )

    for path in skill_paths:
        validation.require(
            len(read_text(path, validation).splitlines()) < 500,
            f"SKILL.md 必须少于 500 行：{path.relative_to(ROOT)}",
        )

    main_skill = ROOT / "skills" / "iter-loop" / "SKILL.md"
    if main_skill.exists():
        metadata, body = parse_frontmatter(main_skill, validation)
        validation.require(
            metadata.get("name") == "iter-loop", "主 Skill 名称必须是 iter-loop"
        )
        validation.require(
            metadata.get("disable-model-invocation") is True,
            "iter-loop 必须保持显式调用",
        )
        for name in (
            "iter-scout",
            "iter-builder",
            "iter-verifier",
            "iter-reviewer",
        ):
            validation.require(name in body, f"SKILL.md 未引用 Agent：{name}")
        for name in ("conservative", "balanced", "feature"):
            validation.require(
                f"(strategies/{name}.md)" in body,
                f"SKILL.md 未直接引用策略：{name}",
            )
        for name in EXPECTED_STACKS:
            validation.require(
                f"(stacks/{name}.md)" in body,
                f"SKILL.md 未直接引用技术栈包：{name}",
            )
        validation.require(
            "(references/state-protocol.md)" in body,
            "SKILL.md 未直接引用状态协议",
        )
        validation.require(
            "/iter-resume" in body and ".auto-iter/runs" in body,
            "SKILL.md 未声明 v0.3 恢复与状态目录",
        )

    for path in agent_paths:
        metadata, _ = parse_frontmatter(path, validation)
        validation.require(
            metadata.get("model") == "inherit",
            f"Agent 应使用 model: inherit：{path.relative_to(ROOT)}",
        )
        validation.require(
            isinstance(metadata.get("readonly"), bool),
            f"Agent readonly 必须是布尔值：{path.relative_to(ROOT)}",
        )
        validation.require(
            metadata.get("is_background") is True,
            f"Agent 必须后台运行：{path.relative_to(ROOT)}",
        )

    return {
        "skills": len(skill_paths),
        "agents": len(agent_paths),
        "commands": len(command_paths),
    }


def validate_strategies(validation: Validation) -> int:
    strategy_dir = ROOT / "skills" / "iter-loop" / "strategies"
    paths = sorted(strategy_dir.glob("*.md"))
    ids: set[str] = set()
    required = {
        "id",
        "label",
        "default-concurrency",
        "max-concurrency",
        "default-task-budget",
        "risk-auto-approve",
    }

    for path in paths:
        metadata, body = parse_frontmatter(path, validation)
        missing = required - metadata.keys()
        validation.require(
            not missing,
            f"策略字段缺失：{path.relative_to(ROOT)} ({', '.join(sorted(missing))})",
        )

        strategy_id = metadata.get("id")
        validation.require(
            strategy_id == path.stem,
            f"策略 id 必须与文件名一致：{path.relative_to(ROOT)}",
        )
        if isinstance(strategy_id, str):
            ids.add(strategy_id)

        default_concurrency = metadata.get("default-concurrency")
        max_concurrency = metadata.get("max-concurrency")
        task_budget = metadata.get("default-task-budget")
        validation.require(
            isinstance(default_concurrency, int)
            and isinstance(max_concurrency, int)
            and 1 <= default_concurrency <= max_concurrency <= 4,
            f"策略并发范围非法：{path.relative_to(ROOT)}",
        )
        validation.require(
            isinstance(task_budget, int) and task_budget > 0,
            f"策略默认任务预算非法：{path.relative_to(ROOT)}",
        )
        validation.require(
            metadata.get("risk-auto-approve") in {"low", "medium", "high"},
            f"策略自动风险阈值非法：{path.relative_to(ROOT)}",
        )
        validation.require(
            bool(body.strip()), f"策略正文为空：{path.relative_to(ROOT)}"
        )

    validation.require(ids == EXPECTED_STRATEGIES, "策略文件集合与 v0.2 契约不一致")
    return len(paths)


def validate_stacks(validation: Validation) -> int:
    stack_dir = ROOT / "skills" / "iter-loop" / "stacks"
    paths = sorted(stack_dir.glob("*.md"))
    ids: set[str] = set()
    required = {"id", "label", "applies-to"}

    for path in paths:
        metadata, body = parse_frontmatter(path, validation)
        missing = required - metadata.keys()
        validation.require(
            not missing,
            f"技术栈包字段缺失：{path.relative_to(ROOT)} "
            f"({', '.join(sorted(missing))})",
        )
        stack_id = metadata.get("id")
        validation.require(
            stack_id == path.stem,
            f"技术栈包 id 必须与文件名一致：{path.relative_to(ROOT)}",
        )
        if isinstance(stack_id, str):
            ids.add(stack_id)
        validation.require(
            isinstance(metadata.get("label"), str)
            and bool(metadata["label"].strip()),
            f"技术栈包 label 不能为空：{path.relative_to(ROOT)}",
        )
        validation.require(
            isinstance(metadata.get("applies-to"), str)
            and bool(metadata["applies-to"].strip()),
            f"技术栈包 applies-to 不能为空：{path.relative_to(ROOT)}",
        )
        validation.require(
            bool(body.strip()), f"技术栈包正文为空：{path.relative_to(ROOT)}"
        )

    validation.require(ids == EXPECTED_STACKS, "技术栈包集合与 v0.3.1 契约不一致")
    return len(paths)


def validate_runtime_state(validation: Validation) -> None:
    helper_path = ROOT / "skills" / "iter-loop" / "scripts" / "state_store.py"
    protocol_path = (
        ROOT / "skills" / "iter-loop" / "references" / "state-protocol.md"
    )
    helper = read_text(helper_path, validation)
    protocol = read_text(protocol_path, validation)
    if helper:
        try:
            compile(helper, str(helper_path), "exec")
        except SyntaxError as exc:
            validation.error(f"状态助手存在 Python 语法错误：{exc}")
        for marker in (
            'STATE_DIR = Path(".auto-iter") / "runs"',
            'EXCLUDE_RULE = "/.auto-iter/runs/"',
            '"activate"',
            '"reconcile"',
            '"sync-head"',
            '"ensure-ignore"',
            "os.replace",
        ):
            validation.require(marker in helper, f"状态助手缺少契约标记：{marker}")
    if protocol:
        for marker in (
            "/.auto-iter/runs/",
            "git rev-parse --git-common-dir",
            "active.json",
            "state.json",
            "events.jsonl",
        ):
            validation.require(marker in protocol, f"状态协议缺少契约标记：{marker}")


def validate_markdown(validation: Validation) -> None:
    for path in sorted(ROOT.rglob("*.md")):
        text = read_text(path, validation)
        relative = path.relative_to(ROOT)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.endswith((" ", "\t")):
                validation.error(f"行尾空白：{relative}:{line_number}")

        if FORBIDDEN_OPERATION_RE.search(text):
            validation.error(f"包含禁止的破坏性命令：{relative}")

        for target in MARKDOWN_LINK_RE.findall(text):
            target = target.strip().strip("<>")
            if (
                not target
                or target.startswith("#")
                or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", target)
            ):
                continue
            local_target = target.split("#", 1)[0]
            if local_target and not (path.parent / local_target).resolve().exists():
                validation.error(f"本地链接不存在：{relative} -> {target}")


def validate_init_guidelines(validation: Validation) -> None:
    path = ROOT / "skills" / "init" / "coding-guidelines.md"
    lines = read_text(path, validation).splitlines()
    relative = path.relative_to(ROOT)
    starts = [
        index
        for index, line in enumerate(lines)
        if line.strip() == "<!-- user-guidelines:start -->"
    ]
    ends = [
        index
        for index, line in enumerate(lines)
        if line.strip() == "<!-- user-guidelines:end -->"
    ]
    validation.require(
        len(starts) == 1, f"init 通用模板 start marker 必须恰好一个：{relative}"
    )
    validation.require(
        len(ends) == 1, f"init 通用模板 end marker 必须恰好一个：{relative}"
    )
    for index in starts + ends:
        validation.require(
            lines[index] == lines[index].strip(),
            f"init 通用模板 marker 必须独占一行：{relative}:{index + 1}",
        )
    if len(starts) == 1 and len(ends) == 1:
        validation.require(
            starts[0] < ends[0], f"init 通用模板 marker 顺序颠倒：{relative}"
        )
        block = lines[starts[0] + 1 : ends[0]]
        validation.require(
            bool("\n".join(block).strip()),
            f"init 通用模板受管块为空：{relative}",
        )


def validate_init_stacks(validation: Validation) -> int:
    stack_dir = ROOT / "skills" / "init" / "stacks"
    paths = sorted(stack_dir.glob("*.md"))
    required = {"id", "label", "applies-to"}

    validation.require(bool(paths), "init 缺少技术栈文件：skills/init/stacks/")
    for path in paths:
        metadata, body = parse_frontmatter(path, validation)
        missing = required - metadata.keys()
        validation.require(
            not missing,
            f"init 技术栈字段缺失：{path.relative_to(ROOT)} "
            f"({', '.join(sorted(missing))})",
        )
        validation.require(
            metadata.get("id") == path.stem,
            f"init 技术栈 id 必须与文件名一致：{path.relative_to(ROOT)}",
        )
        validation.require(
            isinstance(metadata.get("label"), str) and bool(metadata["label"].strip()),
            f"init 技术栈 label 不能为空：{path.relative_to(ROOT)}",
        )
        validation.require(
            isinstance(metadata.get("applies-to"), str)
            and bool(metadata["applies-to"].strip()),
            f"init 技术栈 applies-to 不能为空：{path.relative_to(ROOT)}",
        )
        validation.require(
            "专项规范" in body and "###" in body,
            f"init 技术栈正文缺少专项规范小节：{path.relative_to(ROOT)}",
        )
        validation.require(
            bool(body.strip()), f"init 技术栈正文为空：{path.relative_to(ROOT)}"
        )
    return len(paths)


def main() -> int:
    validation = Validation()
    manifest = validate_manifest(validation)
    validate_marketplace_manifests(manifest, validation)
    counts = validate_components(validation)
    strategy_count = validate_strategies(validation)
    stack_count = validate_stacks(validation)
    validate_init_guidelines(validation)
    init_stack_count = validate_init_stacks(validation)
    validate_runtime_state(validation)
    validate_markdown(validation)

    for warning in validation.warnings:
        print(f"WARNING: {warning}")
    if validation.errors:
        for error in validation.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(
            f"校验失败：{len(validation.errors)} 个错误，"
            f"{len(validation.warnings)} 个警告。",
            file=sys.stderr,
        )
        return 1

    print("dev-toolkit plugin validation: OK")
    print(f"version: {manifest.get('version', 'UNKNOWN')}")
    print(
        "components: "
        f"{counts.get('skills', 0)} skill, "
        f"{counts.get('agents', 0)} agents, "
        f"{counts.get('commands', 0)} commands"
    )
    print(f"strategies: {strategy_count}")
    print(f"stacks: {stack_count}")
    print(f"init stacks: {init_stack_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
