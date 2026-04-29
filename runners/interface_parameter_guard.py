#!/usr/bin/env python3
"""Check Spectre instance parameters against generated Verilog-A parameters."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


_IDENT_RE = r"[A-Za-z_][A-Za-z0-9_]*"
_PARAM_DECL_RE = re.compile(r"\bparameter\b\s+([^;]+);", re.DOTALL)
_MODULE_BLOCK_RE = re.compile(rf"\bmodule\s+({_IDENT_RE})\b.*?\bendmodule\b", re.DOTALL)
_PARAM_ASSIGN_RE = re.compile(rf"\b({_IDENT_RE})\s*=")


@dataclass(frozen=True)
class InterfaceParameterIssue:
    instance: str
    module: str
    missing_parameters: tuple[str, ...]
    passed_parameters: tuple[str, ...]
    declared_parameters: tuple[str, ...]
    tb_path: str

    def note(self) -> str:
        missing = ",".join(self.missing_parameters)
        passed = ",".join(self.passed_parameters)
        declared = ",".join(self.declared_parameters) or "<none>"
        return (
            f"interface_parameter_missing={self.module}:{missing} "
            f"instance={self.instance} passed={passed} declared={declared}"
        )


def _strip_verilog_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", text)


def _strip_spectre_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        lines.append(re.sub(r"//.*", "", line))
    return "\n".join(lines)


def _logical_spectre_lines(text: str) -> list[str]:
    text = _strip_spectre_comments(text)
    logical: list[str] = []
    current = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if current:
                logical.append(current.strip())
                current = ""
            continue
        if line.endswith("\\"):
            current += " " + line[:-1].strip()
            continue
        if current:
            current += " " + line
            logical.append(current.strip())
            current = ""
        else:
            logical.append(line)
    if current:
        logical.append(current.strip())
    return logical


def _parameter_names_from_declaration(declaration: str) -> set[str]:
    names: set[str] = set()
    for match in _PARAM_ASSIGN_RE.finditer(declaration):
        prefix = declaration[: match.start()]
        tail = prefix.rstrip().split()
        if tail and tail[-1] in {"from", "exclude"}:
            continue
        names.add(match.group(1))
    return names


def module_parameter_map(va_paths: list[Path]) -> dict[str, set[str]]:
    modules: dict[str, set[str]] = {}
    for va_path in va_paths:
        text = _strip_verilog_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
        for block in _MODULE_BLOCK_RE.finditer(text):
            module_name = block.group(1)
            body = block.group(0)
            params: set[str] = set()
            for declaration in _PARAM_DECL_RE.findall(body):
                params.update(_parameter_names_from_declaration(declaration))
            modules.setdefault(module_name, set()).update(params)
    return modules


def instance_parameter_uses(tb_paths: list[Path], module_names: set[str]) -> list[dict]:
    uses: list[dict] = []
    if not module_names:
        return uses
    module_pattern = "|".join(re.escape(name) for name in sorted(module_names, key=len, reverse=True))
    instance_re = re.compile(
        rf"^\s*(?P<instance>{_IDENT_RE})\s*\([^)]*\)\s+(?P<module>{module_pattern})\b(?P<rest>.*)$"
    )
    for tb_path in tb_paths:
        for line in _logical_spectre_lines(tb_path.read_text(encoding="utf-8", errors="ignore")):
            match = instance_re.match(line)
            if not match:
                continue
            rest = match.group("rest")
            params = sorted(set(_PARAM_ASSIGN_RE.findall(rest)))
            if not params:
                continue
            uses.append(
                {
                    "instance": match.group("instance"),
                    "module": match.group("module"),
                    "parameters": params,
                    "tb_path": str(tb_path),
                }
            )
    return uses


def check_interface_parameters(sample_dir: Path) -> list[InterfaceParameterIssue]:
    va_paths = sorted(sample_dir.glob("*.va"))
    tb_paths = sorted(sample_dir.glob("*.scs"))
    return check_interface_parameter_paths(va_paths=va_paths, tb_paths=tb_paths)


def check_interface_parameter_paths(
    *,
    va_paths: list[Path],
    tb_paths: list[Path],
) -> list[InterfaceParameterIssue]:
    modules = module_parameter_map(va_paths)
    uses = instance_parameter_uses(tb_paths, set(modules))
    issues: list[InterfaceParameterIssue] = []
    for use in uses:
        module = use["module"]
        declared = modules.get(module, set())
        passed = set(use["parameters"])
        missing = sorted(passed - declared)
        if not missing:
            continue
        issues.append(
            InterfaceParameterIssue(
                instance=use["instance"],
                module=module,
                missing_parameters=tuple(missing),
                passed_parameters=tuple(sorted(passed)),
                declared_parameters=tuple(sorted(declared)),
                tb_path=use["tb_path"],
            )
        )
    return issues


def format_issue_notes(issues: list[InterfaceParameterIssue]) -> list[str]:
    return [issue.note() for issue in issues]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-dir", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    issues = check_interface_parameters(args.sample_dir)
    payload = {
        "sample_dir": str(args.sample_dir),
        "status": "FAIL" if issues else "PASS",
        "issues": [
            {
                "instance": issue.instance,
                "module": issue.module,
                "missing_parameters": list(issue.missing_parameters),
                "passed_parameters": list(issue.passed_parameters),
                "declared_parameters": list(issue.declared_parameters),
                "tb_path": issue.tb_path,
                "note": issue.note(),
            }
            for issue in issues
        ],
        "notes": format_issue_notes(issues),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for note in payload["notes"]:
            print(note)
        if not issues:
            print("interface_parameter_guard=pass")
    return 2 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
