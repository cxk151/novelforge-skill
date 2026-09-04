#!/usr/bin/env python3
"""Deterministic project helpers for the NovelForge skill."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_ROOT / "assets" / "project-template"
REQUIRED = [
    "canon.yaml", "constraints.md", "change-log.yaml",
    "story-bible/characters.yaml", "story-bible/world.yaml",
    "continuity/timeline.yaml", "continuity/open-threads.yaml",
    "planning/master-outline.md", "manuscript", "summaries", "exports",
]


def chapter_number(path: Path) -> int:
    match = re.search(r"(\d+)", path.stem)
    return int(match.group(1)) if match else -1


def chapter_files(root: Path) -> list[Path]:
    folder = root / "manuscript"
    files = [p for p in folder.glob("*.md") if p.is_file()]
    return sorted(files, key=lambda p: (chapter_number(p), p.name))


def count_text(text: str) -> dict[str, int]:
    body = re.sub(r"(?m)^#.*$", "", text)
    no_space = re.sub(r"\s+", "", body)
    cjk = re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", body)
    words = re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", body)
    return {"characters_no_whitespace": len(no_space), "cjk_characters": len(cjk), "latin_words": len(words)}


def init_project(args: argparse.Namespace) -> int:
    target = Path(args.path).resolve()
    if target.exists() and any(target.iterdir()):
        print(f"Refusing to initialize non-empty directory: {target}", file=sys.stderr)
        return 2
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE, target, dirs_exist_ok=True)
    canon = target / "canon.yaml"
    canon.write_text(canon.read_text(encoding="utf-8").replace('title: ""', f'title: {json.dumps(args.title, ensure_ascii=False)}', 1), encoding="utf-8")
    for rel in ["planning/volumes", "planning/arcs", "planning/events", "planning/options"]:
        (target / rel).mkdir(parents=True, exist_ok=True)
    print(target)
    return 0


def validate_project(args: argparse.Namespace) -> int:
    root = Path(args.project).resolve()
    missing = [rel for rel in REQUIRED if not (root / rel).exists()]
    empty_title = False
    canon = root / "canon.yaml"
    if canon.exists():
        empty_title = bool(re.search(r'(?m)^\s*title:\s*(?:""|null)?\s*$', canon.read_text(encoding="utf-8")))
    result = {"project": str(root), "valid": not missing and not empty_title, "missing": missing, "empty_title": empty_title}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


def audit_project(args: argparse.Namespace) -> int:
    root = Path(args.project).resolve()
    chapters = chapter_files(root)
    issues: list[dict[str, object]] = []
    seen: dict[int, str] = {}
    for path in chapters:
        number = chapter_number(path)
        if number in seen:
            issues.append({"severity": "serious", "type": "duplicate_chapter_number", "chapter": number, "files": [seen[number], path.name]})
        seen[number] = path.name
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            issues.append({"severity": "critical", "type": "empty_chapter", "file": path.name})
    numbers = sorted(n for n in seen if n >= 0)
    for left, right in zip(numbers, numbers[1:]):
        if right > left + 1:
            issues.append({"severity": "moderate", "type": "chapter_gap", "after": left, "before": right})
    result = {"project": str(root), "chapters": len(chapters), "issues": issues, "counts": {p.name: count_text(p.read_text(encoding="utf-8")) for p in chapters}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if any(i["severity"] in {"critical", "serious"} for i in issues) else 0


def build_context(args: argparse.Namespace) -> int:
    root = Path(args.project).resolve()
    chapters = chapter_files(root)
    selected = [p for p in chapters if chapter_number(p) < args.chapter][-args.previous:]
    summary_files = sorted((root / "summaries").glob("*.y*ml"), key=chapter_number)[-args.summaries:]
    payload = {
        "project": str(root),
        "target_chapter": args.chapter,
        "authority_files": [str(root / p) for p in ["canon.yaml", "constraints.md", "change-log.yaml"] if (root / p).exists()],
        "previous_chapters": [str(p) for p in selected],
        "recent_summaries": [str(p) for p in summary_files],
        "continuity_files": [str(p) for p in (root / "continuity").glob("*.yaml")],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def count_command(args: argparse.Namespace) -> int:
    path = Path(args.path)
    print(json.dumps({"path": str(path.resolve()), **count_text(path.read_text(encoding="utf-8"))}, ensure_ascii=False, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="NovelForge project utilities")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="initialize a novel project")
    init.add_argument("path")
    init.add_argument("--title", required=True)
    init.set_defaults(func=init_project)
    validate = sub.add_parser("validate", help="validate project structure")
    validate.add_argument("project")
    validate.set_defaults(func=validate_project)
    audit = sub.add_parser("audit", help="audit chapter numbering and counts")
    audit.add_argument("project")
    audit.set_defaults(func=audit_project)
    context = sub.add_parser("context", help="build a compact context manifest")
    context.add_argument("project")
    context.add_argument("--chapter", type=int, required=True)
    context.add_argument("--previous", type=int, default=1)
    context.add_argument("--summaries", type=int, default=5)
    context.set_defaults(func=build_context)
    count = sub.add_parser("count", help="count a manuscript file")
    count.add_argument("path")
    count.set_defaults(func=count_command)
    return p


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
