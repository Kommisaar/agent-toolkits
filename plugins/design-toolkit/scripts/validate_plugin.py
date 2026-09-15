#!/usr/bin/env python3
"""Validate the design-toolkit plugin (Cursor + Claude 双清单) without third-party dependencies."""

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
# 契约快照：插件应包含的 Skill 集合（skills/ 下的一级目录名）。
# Skill 选型落地时把目录名加入此处，并同步三处清单 description
# 与 README 的 design-toolkit 小节。
CONTRACT_VERSION = "0.3.0"
EXPECTED_SKILLS: set[str] = {"motion", "ui-design"}
REQUIRED_COMPONENT_KEYS = ("skills",)
OPTIONAL_COMPONENT_KEYS = ("agents", "commands")
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
# 禁令语境豁免：条文以“不得/禁止”等否定措辞引用破坏性命令名时属于
# 规则本身，不是在教执行。
FORBIDDEN_NEGATION_RE = re.compile(r"不得|禁止|不要|不应|不自动|不执行")


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
    for key in REQUIRED_COMPONENT_KEYS:
        component_paths(manifest, key, validation)
    for key in OPTIONAL_COMPONENT_KEYS:
        if manifest.get(key) is not None:
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


def validate_skill_references(
    skill_dir: Path, body: str, validation: Validation
) -> None:
    for path in sorted(skill_dir.rglob("*.md")):
        if path == skill_dir / "SKILL.md":
            continue
        relative = path.relative_to(skill_dir).as_posix()
        validation.require(
            relative in body,
            f"参考文件未被 SKILL.md 直接链接：{skill_dir.name}/{relative}",
        )


def validate_skills(validation: Validation) -> int:
    skills_dir = ROOT / "skills"
    skill_paths = sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.is_dir() else []
    found = {path.parent.name for path in skill_paths}
    validation.require(
        found == EXPECTED_SKILLS,
        f"Skill 目录集合与 v{CONTRACT_VERSION} 契约不一致："
        f"期望 {sorted(EXPECTED_SKILLS) or '（空）'}，实际 {sorted(found)}；"
        "选型变化时更新 EXPECTED_SKILLS",
    )

    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            if child.is_dir():
                validation.require(
                    (child / "SKILL.md").is_file(),
                    f"Skill 目录缺少 SKILL.md：{child.relative_to(ROOT)}",
                )

    names: list[str] = []
    for path in skill_paths:
        metadata, body = parse_frontmatter(path, validation)
        validate_name_and_description(path, metadata, validation)
        name = metadata.get("name")
        if isinstance(name, str):
            names.append(name)
            validation.require(
                name == path.parent.name,
                f"Skill name 必须与目录名一致：{path.relative_to(ROOT)}",
            )
        validation.require(
            len(read_text(path, validation).splitlines()) < 500,
            f"SKILL.md 必须少于 500 行：{path.relative_to(ROOT)}",
        )
        validate_skill_references(path.parent, body, validation)

    validation.require(len(names) == len(set(names)), "Skill 名称必须唯一")
    return len(skill_paths)


def validate_markdown(validation: Validation) -> None:
    for path in sorted(ROOT.rglob("*.md")):
        text = read_text(path, validation)
        relative = path.relative_to(ROOT)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.endswith((" ", "\t")):
                validation.error(f"行尾空白：{relative}:{line_number}")

        for match in FORBIDDEN_OPERATION_RE.finditer(text):
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.end())
            if line_end == -1:
                line_end = len(text)
            context = text[line_start:line_end]
            if not FORBIDDEN_NEGATION_RE.search(context):
                validation.error(f"包含禁止的破坏性命令：{relative}")
                break

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


def main() -> int:
    validation = Validation()
    manifest = validate_manifest(validation)
    validate_marketplace_manifests(manifest, validation)
    skill_count = validate_skills(validation)
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

    print("design-toolkit plugin validation: OK")
    print(f"version: {manifest.get('version', 'UNKNOWN')}")
    print(
        f"skills: {skill_count} (EXPECTED_SKILLS: {len(EXPECTED_SKILLS)} 个登记)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
