#!/usr/bin/env python3
"""Deterministic compile guards for C-PLUS style experiments.

These guards operate only on generated candidate artifacts and public validator
diagnostics.  They are intentionally narrower than an LLM repair loop: the goal
is to materialize common Spectre-strict legality fixes without using hidden
checkers, gold behavior, or task-id-specific templates.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from compile_skill_library import select_compile_skills, skill_summary
from compile_vector_unroll_guard import apply_vector_unroll_guard


_MODULE_RE = re.compile(
    r"\bmodule\s+(?P<name>[A-Za-z_][A-Za-z0-9_$]*)\s*\(",
    re.MULTILINE,
)
_PARAM_RANGE_RE = re.compile(
    r"(?P<prefix>\bparameter\s+(?:real|integer)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_$]*)\s*=\s*[^;]+?)"
    r"\s+from\s*(?P<range>[\[\(][^;]*[\]\)])\s*;",
    re.IGNORECASE,
)
_INSTANCE_RE = re.compile(
    r"^(?P<prefix>\s*[A-Za-z_][A-Za-z0-9_.$]*\s*\([^)]*\)\s+[A-Za-z_][A-Za-z0-9_.$]*)"
    r"\s+parameters\b(?P<suffix>.*)$",
    re.IGNORECASE,
)
_WAVE_RE = re.compile(r"wave\s*=\s*\[(?P<body>[^\]]+)\]", re.IGNORECASE)
_TRANSITION_RE = re.compile(
    r"(?P<indent>[ \t]*)V\s*\(\s*(?P<dest>[^)]+?)\s*\)\s*<\+\s*"
    r"transition\s*\((?P<args>.*?)\)\s*;",
    re.DOTALL,
)
_MODULE_HEADER_RE = re.compile(
    r"\bmodule\s+(?P<name>[A-Za-z_][A-Za-z0-9_$]*)\s*\((?P<ports>.*?)\)\s*;",
    re.DOTALL,
)
_DIRECTION_DECL_RE = re.compile(
    r"\b(?P<dir>input|output|inout)\b(?P<rest>[^;]*);",
    re.IGNORECASE,
)
_SOURCED_PORT_RE = re.compile(
    r"sourced_port_voltage_drive=\d+:(?P<inst>[A-Za-z_][A-Za-z0-9_.$]*):"
    r"(?P<model>[A-Za-z_][A-Za-z0-9_.$]*):(?P<port>[A-Za-z_][A-Za-z0-9_$]*)"
    r"->(?P<node>[^|\s]+)",
    re.IGNORECASE,
)

_TIME_SCALE = {
    "fs": 1e-15,
    "ps": 1e-12,
    "ns": 1e-9,
    "us": 1e-6,
    "ms": 1e-3,
    "s": 1.0,
    "f": 1e-15,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "m": 1e-3,
}


def _notes_text(notes: list[str] | None) -> str:
    return " ".join(str(note) for note in notes or [])


def _split_top_level_commas(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for idx, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            parts.append(text[start:idx].strip())
            start = idx + 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _sanitize_identifier(text: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_$]+", "_", text.strip())
    sanitized = sanitized.strip("_") or "node"
    if not re.match(r"[A-Za-z_]", sanitized):
        sanitized = "n_" + sanitized
    return sanitized


def _module_names(text: str) -> list[str]:
    return [match.group("name") for match in _MODULE_RE.finditer(text)]


def _clean_port_token(token: str) -> str:
    cleaned = re.sub(r"//.*", " ", token)
    cleaned = re.sub(r"/\*.*?\*/", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\[[^\]]+\]", " ", cleaned)
    cleaned = re.sub(r"\b(input|output|inout|electrical|real|integer|wire|reg|signed)\b", " ", cleaned)
    parts = [part for part in re.split(r"\s+", cleaned.strip()) if part]
    return parts[-1].strip() if parts else token.strip()


def _module_port_orders(sample_dir: Path) -> dict[str, list[str]]:
    orders: dict[str, list[str]] = {}
    for va_path in sorted(sample_dir.glob("*.va")):
        source = va_path.read_text(encoding="utf-8", errors="ignore")
        for match in _MODULE_HEADER_RE.finditer(source):
            ports = [_clean_port_token(item) for item in _split_top_level_commas(match.group("ports"))]
            orders[match.group("name")] = [port for port in ports if port]
    return orders


def _apply_module_name_guard(sample_dir: Path, notes: list[str] | None) -> list[str]:
    text = _notes_text(notes)
    match = re.search(r"undefined_module=([^;|\s]+);available_modules=([^|\s]+)", text)
    if not match:
        return []
    missing = [item for item in match.group(1).split(",") if item and item != "<none>"]
    available = [item for item in match.group(2).split(",") if item and item != "<none>"]
    if len(missing) != 1 or len(available) != 1:
        return []

    needed = missing[0]
    actual = available[0]
    edits: list[str] = []
    for va_path in sorted(sample_dir.glob("*.va")):
        source = va_path.read_text(encoding="utf-8", errors="ignore")
        names = _module_names(source)
        if actual not in names or needed in names:
            continue
        updated = re.sub(
            rf"\bmodule\s+{re.escape(actual)}\s*\(",
            f"module {needed} (",
            source,
            count=1,
        )
        if updated != source:
            va_path.write_text(updated, encoding="utf-8")
            edits.append(f"module_name:{va_path.name}:{actual}->{needed}")
    return edits


def _apply_parameter_range_guard(sample_dir: Path, notes: list[str] | None) -> list[str]:
    text = _notes_text(notes).lower()
    remove_default_violations = "parameter_default_range=" in text
    remove_open_upper = "parameter_open_upper_range=" in text
    if not remove_default_violations and not remove_open_upper:
        return []
    edits: list[str] = []
    for va_path in sorted(sample_dir.glob("*.va")):
        source = va_path.read_text(encoding="utf-8", errors="ignore")
        count = 0

        def replace(match: re.Match[str]) -> str:
            nonlocal count
            range_text = match.group("range")
            has_empty_upper = bool(re.search(r":\s*[\]\)]\s*$", range_text))
            if remove_default_violations or (remove_open_upper and has_empty_upper):
                count += 1
                return f"{match.group('prefix')};"
            return match.group(0)

        updated = _PARAM_RANGE_RE.sub(replace, source)
        if count:
            va_path.write_text(updated, encoding="utf-8")
            edits.append(f"parameter_default_range_removed:{va_path.name}:count={count}")
    return edits


def _parse_time_seconds(token: str) -> float | None:
    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([A-Za-z]*)", token.strip())
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    return value * _TIME_SCALE.get(unit, 1.0)


def _format_seconds(value: float) -> str:
    return f"{value:.12g}"


def _fix_pwl_body(body: str) -> tuple[str, bool]:
    tokens = body.split()
    if len(tokens) < 4 or len(tokens) % 2:
        return body, False
    pairs: list[tuple[str, str, float | None]] = []
    for idx in range(0, len(tokens), 2):
        pairs.append((tokens[idx], tokens[idx + 1], _parse_time_seconds(tokens[idx])))
    if any(seconds is None for _, _, seconds in pairs):
        return body, False

    changed = False
    fixed: list[str] = []
    previous = -float("inf")
    for time_token, value_token, seconds in pairs:
        assert seconds is not None
        fixed_seconds = seconds
        if fixed_seconds <= previous:
            # 1 fs is enough to break duplicate ideal steps without changing
            # the public intent at benchmark time scales.
            fixed_seconds = previous + 1e-15
            changed = True
        fixed.extend([_format_seconds(fixed_seconds), value_token])
        previous = fixed_seconds
    return " ".join(fixed), changed


def _apply_pwl_monotonic_guard(sample_dir: Path, notes: list[str] | None) -> list[str]:
    text = _notes_text(notes).lower()
    if "nonincreasing_pwl_time=" not in text:
        return []
    edits: list[str] = []
    for tb_path in sorted(sample_dir.glob("*.scs")):
        source = tb_path.read_text(encoding="utf-8", errors="ignore")
        changed_count = 0

        def replace(match: re.Match[str]) -> str:
            nonlocal changed_count
            fixed, changed = _fix_pwl_body(match.group("body"))
            if not changed:
                return match.group(0)
            changed_count += 1
            return f"wave=[{fixed}]"

        updated = _WAVE_RE.sub(replace, source)
        if changed_count:
            tb_path.write_text(updated, encoding="utf-8")
            edits.append(f"pwl_strictly_increasing:{tb_path.name}:waves={changed_count}")
    return edits


def _apply_instance_parameter_keyword_guard(sample_dir: Path, notes: list[str] | None) -> list[str]:
    text = _notes_text(notes).lower()
    if "instance_parameters_keyword=" not in text:
        return []
    edits: list[str] = []
    for tb_path in sorted(sample_dir.glob("*.scs")):
        lines = tb_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        changed = 0
        new_lines: list[str] = []
        for line in lines:
            updated = _INSTANCE_RE.sub(r"\g<prefix>\g<suffix>", line)
            if updated == line and re.match(r"^\s+parameters\b", line, flags=re.IGNORECASE):
                updated = re.sub(r"^(\s+)parameters\b\s*", r"\1", line, flags=re.IGNORECASE)
            if updated != line:
                changed += 1
            new_lines.append(updated)
        if changed:
            tb_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            edits.append(f"instance_parameters_keyword_removed:{tb_path.name}:count={changed}")
    return edits


def _apply_sourced_port_role_repair_guard(sample_dir: Path, notes: list[str] | None) -> list[str]:
    """Detach DUT-driven ports from source-fixed nodes when strict preflight proves the conflict.

    This is intentionally a compile-boundary repair.  It does not guess hidden
    behavior; it only prevents a generated module's driven port from being tied
    directly to a voltage-source or ground node.
    """
    matches = list(_SOURCED_PORT_RE.finditer(_notes_text(notes)))
    if not matches:
        return []

    port_orders = _module_port_orders(sample_dir)
    edits: list[str] = []
    for tb_path in sorted(sample_dir.glob("*.scs")):
        source = tb_path.read_text(encoding="utf-8", errors="ignore")
        updated = source
        changed_for_file = 0
        for note_match in matches:
            inst = note_match.group("inst")
            model = note_match.group("model")
            port = note_match.group("port")
            old_node = note_match.group("node")
            instance_re = re.compile(
                rf"\b(?P<inst>{re.escape(inst)})\s*\((?P<nodes>[^)]*)\)\s*(?:\\\s*)?"
                rf"{re.escape(model)}\b",
                re.DOTALL,
            )
            instance_match = instance_re.search(updated)
            if not instance_match:
                continue
            raw_nodes = instance_match.group("nodes")
            nodes = [node for node in re.split(r"\s+", raw_nodes.replace("\\", " ").strip()) if node]
            if not nodes:
                continue
            target_idx: int | None = None
            ports = port_orders.get(model, [])
            if port in ports and len(ports) == len(nodes):
                candidate_idx = ports.index(port)
                if candidate_idx < len(nodes) and nodes[candidate_idx] == old_node:
                    target_idx = candidate_idx
            if target_idx is None:
                for idx, node in enumerate(nodes):
                    if node == old_node:
                        target_idx = idx
                        break
            if target_idx is None:
                continue
            new_node_base = f"__cg_{_sanitize_identifier(inst)}_{_sanitize_identifier(port)}_free"
            new_node = new_node_base
            suffix = 1
            while new_node in nodes:
                suffix += 1
                new_node = f"{new_node_base}_{suffix}"
            nodes[target_idx] = new_node
            new_nodes = " ".join(nodes)
            updated = updated[: instance_match.start("nodes")] + new_nodes + updated[instance_match.end("nodes") :]
            changed_for_file += 1
            edits.append(f"sourced_port_detached:{tb_path.name}:{inst}:{port}:{old_node}->{new_node}")
        if changed_for_file:
            tb_path.write_text(updated, encoding="utf-8")
    return edits


def _parse_direction_declarations(module_text: str) -> tuple[dict[str, str], dict[str, list[int]]]:
    directions: dict[str, str] = {}
    vectors: dict[str, list[int]] = {}
    for match in _DIRECTION_DECL_RE.finditer(module_text):
        direction = match.group("dir").lower()
        rest = match.group("rest")
        vector_match = re.search(r"\[\s*(?P<msb>\d+)\s*:\s*(?P<lsb>\d+)\s*\]", rest)
        rest = re.sub(r"\[[^\]]+\]", " ", rest)
        rest = re.sub(r"\b(electrical|real|integer|wire|reg|signed)\b", " ", rest, flags=re.IGNORECASE)
        for raw_name in rest.split(","):
            name = _clean_port_token(raw_name)
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_$]*$", name):
                continue
            directions[name] = direction
            if vector_match:
                msb = int(vector_match.group("msb"))
                lsb = int(vector_match.group("lsb"))
                step = -1 if msb >= lsb else 1
                vectors[name] = list(range(msb, lsb + step, step))
    return directions, vectors


def _module_skeleton_specs(sample_dir: Path) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for va_path in sorted(sample_dir.glob("*.va")):
        source = va_path.read_text(encoding="utf-8", errors="ignore")
        for match in _MODULE_HEADER_RE.finditer(source):
            end_match = re.search(r"\bendmodule\b", source[match.end() :], flags=re.IGNORECASE)
            body_end = match.end() + end_match.end() if end_match else len(source)
            module_text = source[match.start() : body_end]
            directions, vectors = _parse_direction_declarations(module_text)
            ports = [_clean_port_token(item) for item in _split_top_level_commas(match.group("ports"))]
            specs.append(
                {
                    "name": match.group("name"),
                    "path": va_path,
                    "ports": [port for port in ports if port],
                    "directions": directions,
                    "vectors": vectors,
                }
            )
    return specs


def _expanded_instance_nodes(spec: dict[str, object]) -> list[tuple[str, str, str]]:
    nodes: list[tuple[str, str, str]] = []
    directions = spec["directions"]
    vectors = spec["vectors"]
    assert isinstance(directions, dict)
    assert isinstance(vectors, dict)
    for port in spec["ports"]:
        assert isinstance(port, str)
        direction = str(directions.get(port, "input"))
        indices = vectors.get(port)
        if indices:
            for index in indices:
                nodes.append((f"{port}_{index}", port, direction))
        else:
            nodes.append((port, port, direction))
    return nodes


def _is_supply_hi(name: str) -> bool:
    return bool(re.fullmatch(r"(?i)(vdd|vdda|avdd|dvdd|vcc|vp|vplus|supply|supply_hi)", name))


def _is_supply_lo(name: str) -> bool:
    return bool(re.fullmatch(r"(?i)(vss|vssa|avss|dvss|gnd|vneg|vminus|vee|supply_lo)", name))


def _is_clock_like(name: str) -> bool:
    return bool(re.search(r"(?i)(clk|clock|strobe|sample|ref)", name))


def _is_reset_like(name: str) -> bool:
    return bool(re.search(r"(?i)(^rst|reset|clear)", name))


def _source_line_for_node(node: str, port: str, direction: str) -> str | None:
    if direction == "output":
        return None
    source_name = "V_" + _sanitize_identifier(node)
    if _is_supply_hi(port):
        return f"{source_name} ({node} 0) vsource dc=0.9"
    if _is_supply_lo(port):
        return f"{source_name} ({node} 0) vsource dc=0"
    if direction == "inout":
        return None
    if _is_clock_like(port):
        return f"{source_name} ({node} 0) vsource type=pulse val0=0 val1=0.9 period=10n delay=1n rise=50p fall=50p width=5n"
    if _is_reset_like(port):
        value = "0.9" if re.search(r"(?i)(rst_n|reset_n|rstb|resetb)", port) else "0"
        return f"{source_name} ({node} 0) vsource dc={value}"
    return f"{source_name} ({node} 0) vsource dc=0"


def _apply_missing_testbench_skeleton_guard(sample_dir: Path, notes: list[str] | None) -> list[str]:
    text = _notes_text(notes).lower()
    if "missing_generated_files=testbench.scs" not in text and "missing_generated_files: testbench.scs" not in text and "missing_staged_tb" not in text:
        return []
    if any(sample_dir.glob("*.scs")):
        return []

    specs = _module_skeleton_specs(sample_dir)
    if not specs:
        return []
    specs = sorted(
        specs,
        key=lambda item: (
            str(item["name"]).lower().startswith(("v2b", "probe", "checker")),
            -len(item["ports"]),
            str(item["name"]),
        ),
    )
    spec = specs[0]
    nodes = _expanded_instance_nodes(spec)
    if not nodes:
        return []
    include_lines = [f'ahdl_include "{path.name}"' for path in sorted(sample_dir.glob("*.va"))]
    source_lines = [
        line
        for node, port, direction in nodes
        for line in [_source_line_for_node(node, port, direction)]
        if line
    ]
    instance_nodes = " ".join(node for node, _, _ in nodes)
    output_nodes = [node for node, _, direction in nodes if direction == "output"] or [node for node, _, _ in nodes]
    tb_lines = [
        "simulator lang=spectre",
        "global 0",
        *include_lines,
        *source_lines,
        f"XSKEL ({instance_nodes}) {spec['name']}",
        "save " + " ".join(output_nodes),
        "tran tran stop=200n maxstep=0.1n",
        "",
    ]
    tb_path = sample_dir / "tb_generated.scs"
    tb_path.write_text("\n".join(tb_lines), encoding="utf-8")
    edits = [f"missing_testbench_skeleton:{tb_path.name}:model={spec['name']}:nodes={len(nodes)}"]
    if any("transition" in path.read_text(encoding="utf-8", errors="ignore") for path in sample_dir.glob("*.va")):
        transition_edits = _apply_transition_target_guard(
            sample_dir,
            ["transition() contribution is inside a conditional/event/loop/case statement"],
        )
        edits.extend(f"missing_testbench_bootstrap:{edit}" for edit in transition_edits)
    return edits


def _apply_dynamic_scatter_materialization_guard(sample_dir: Path, notes: list[str] | None) -> list[str]:
    text = _notes_text(notes).lower()
    if "dynamic_analog_vector_index=" not in text:
        return []
    edits = apply_vector_unroll_guard(sample_dir, notes=notes)
    return [f"dynamic_scatter_materialization:{edit}" for edit in edits]


def _find_analog_end_insert_at(text: str) -> int | None:
    matches = list(re.finditer(r"(?m)^[ \t]*end\s*\n[ \t]*endmodule\b", text))
    if not matches:
        return None
    return matches[-1].start()


def _insert_declarations_before_analog(text: str, declarations: list[str]) -> str:
    if not declarations:
        return text
    analog = re.search(r"(?m)^[ \t]*analog\s+begin\b", text)
    if not analog:
        return text
    declaration_text = "\n".join(declarations) + "\n\n"
    return text[: analog.start()] + declaration_text + text[analog.start() :]


def _apply_transition_target_guard(sample_dir: Path, notes: list[str] | None) -> list[str]:
    text = _notes_text(notes).lower()
    if "conditional_transition=" not in text and "transition() contribution is inside" not in text:
        return []

    edits: list[str] = []
    for va_path in sorted(sample_dir.glob("*.va")):
        source = va_path.read_text(encoding="utf-8", errors="ignore")
        if "transition" not in source:
            continue

        targets: dict[str, dict[str, str]] = {}

        def replace(match: re.Match[str]) -> str:
            dest = match.group("dest").strip()
            args = _split_top_level_commas(match.group("args"))
            if len(args) < 3:
                return match.group(0)
            expr = args[0]
            rest = ", ".join(args[1:])
            key = dest
            var = "__cg_" + _sanitize_identifier(dest) + "_target"
            targets.setdefault(key, {"dest": dest, "var": var, "rest": rest})
            return f"{match.group('indent')}{var} = {expr};"

        rewritten = _TRANSITION_RE.sub(replace, source)
        if not targets or rewritten == source:
            continue

        declarations: list[str] = []
        for target in targets.values():
            if re.search(rf"\breal\s+{re.escape(target['var'])}\b", rewritten):
                continue
            declarations.append(f"    real {target['var']};")
        rewritten = _insert_declarations_before_analog(rewritten, declarations)

        insert_at = _find_analog_end_insert_at(rewritten)
        if insert_at is None:
            continue
        contributions = "\n".join(
            f"        V({target['dest']}) <+ transition({target['var']}, {target['rest']});"
            for target in targets.values()
        )
        rewritten = rewritten[:insert_at] + contributions + "\n\n" + rewritten[insert_at:]
        va_path.write_text(rewritten, encoding="utf-8")
        edits.append(f"transition_target_buffer:{va_path.name}:outputs={len(targets)}")
    return edits


def _apply_fixer_action(sample_dir: Path, *, fixer: str, notes: list[str] | None) -> list[str]:
    if fixer == "module_name":
        return _apply_module_name_guard(sample_dir, notes)
    if fixer == "parameter_default_range":
        return _apply_parameter_range_guard(sample_dir, notes)
    if fixer == "pwl_monotonic_time":
        return _apply_pwl_monotonic_guard(sample_dir, notes)
    if fixer == "instance_parameter_keyword":
        return _apply_instance_parameter_keyword_guard(sample_dir, notes)
    if fixer == "sourced_port_role_repair":
        return _apply_sourced_port_role_repair_guard(sample_dir, notes)
    if fixer == "missing_testbench_skeleton":
        return _apply_missing_testbench_skeleton_guard(sample_dir, notes)
    if fixer == "dynamic_scatter_materialization":
        return _apply_dynamic_scatter_materialization_guard(sample_dir, notes)
    if fixer == "vector_unroll":
        return apply_vector_unroll_guard(sample_dir, notes=notes)
    if fixer == "transition_target_buffer":
        return _apply_transition_target_guard(sample_dir, notes)
    return []


def apply_compile_skill_actions(sample_dir: Path, *, notes: list[str] | None = None) -> dict[str, object]:
    """Apply selected compile skills and return an auditable action manifest."""
    selected = select_compile_skills(notes)
    # Keep action order stable and close to the original C-PLUS hard-guard pass:
    # linkage/syntax normalizations first, structural vector materialization
    # next, transition target-buffering last.
    fixer_order = {
        "module_name": 0,
        "parameter_default_range": 1,
        "pwl_monotonic_time": 2,
        "instance_parameter_keyword": 3,
        "missing_testbench_skeleton": 4,
        "sourced_port_role_repair": 5,
        "dynamic_scatter_materialization": 6,
        "vector_unroll": 7,
        "transition_target_buffer": 8,
        None: 99,
    }
    selected = sorted(selected, key=lambda skill: (fixer_order.get(skill.fixer, 50), skill.id))

    all_edits: list[str] = []
    skill_records: list[dict[str, object]] = []
    for skill in selected:
        edits: list[str] = []
        if skill.fixer:
            edits = _apply_fixer_action(sample_dir, fixer=skill.fixer, notes=notes)
            all_edits.extend(edits)
        record = skill_summary(skill)
        record["edits"] = edits
        record["action"] = "fixer" if skill.fixer else "judge_only"
        skill_records.append(record)
    return {
        "selected_skills": skill_records,
        "edits": all_edits,
    }


def apply_compile_hard_guard(sample_dir: Path, *, notes: list[str] | None = None) -> list[str]:
    """Apply public, deterministic compile guards to a candidate sample."""
    return list(apply_compile_skill_actions(sample_dir, notes=notes)["edits"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample_dir", type=Path)
    parser.add_argument("--notes-json", type=Path, default=None)
    args = parser.parse_args()
    notes = None
    if args.notes_json:
        data = json.loads(args.notes_json.read_text(encoding="utf-8"))
        notes = data.get("notes") or data.get("evas_notes") or []
    edits = apply_compile_hard_guard(args.sample_dir, notes=notes)
    print(json.dumps({"sample_dir": str(args.sample_dir), "edits": edits}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
