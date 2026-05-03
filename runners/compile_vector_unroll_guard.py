#!/usr/bin/env python3
"""Deterministic compile guard for vector-port/scalar-node mismatches.

The guard handles a common Spectre-strict failure pattern:

* the Verilog-A module declares an electrical vector port, for example
  `input [15:0] din;`
* the Spectre testbench instantiates the DUT with one scalar node per bit
* the Verilog-A source uses runtime electrical indexing such as `V(din[i])`

Spectre-style validation is much more reliable when the public interface is
materialized as scalar nodes.  This module rewrites only the interface shape and
fixed electrical accesses; it does not tune behavior constants.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


_MODULE_RE = re.compile(
    r"\bmodule\s+(?P<name>[A-Za-z_]\w*)\s*\((?P<ports>.*?)\)\s*;",
    re.DOTALL,
)
_DIRECTION_VECTOR_RE = re.compile(
    r"\b(?P<dir>input|output|inout)\s+(?P<electrical>electrical\s+)?"
    r"\[\s*(?P<msb>\d+)\s*:\s*(?P<lsb>\d+)\s*\]\s*"
    r"(?P<name>[A-Za-z_]\w*)\s*;",
    re.IGNORECASE,
)
_ELECTRICAL_VECTOR_RE = re.compile(
    r"\belectrical\s+\[\s*(?P<msb>\d+)\s*:\s*(?P<lsb>\d+)\s*\]\s*"
    r"(?P<name>[A-Za-z_]\w*)\s*;",
    re.IGNORECASE,
)
_BUS_NODE_RE = re.compile(r"\b([A-Za-z_]\w*)\[(\d+)\]")


@dataclass(frozen=True)
class VectorDecl:
    name: str
    msb: int
    lsb: int

    @property
    def indices(self) -> list[int]:
        step = -1 if self.msb >= self.lsb else 1
        return list(range(self.msb, self.lsb + step, step))


@dataclass(frozen=True)
class ModuleSpec:
    name: str
    ports: list[str]
    vector_decls: dict[str, VectorDecl]
    header_match: re.Match[str]


def _split_ports(raw_ports: str) -> list[str]:
    return [item.strip() for item in re.split(r",", raw_ports.replace("\n", " ")) if item.strip()]


def _normalize_spectre_bus_nodes(text: str) -> tuple[str, bool]:
    updated = _BUS_NODE_RE.sub(r"\1_\2", text)
    return updated, updated != text


def _module_specs(text: str) -> list[ModuleSpec]:
    vector_decls: dict[str, VectorDecl] = {}
    for match in _DIRECTION_VECTOR_RE.finditer(text):
        name = match.group("name")
        vector_decls[name] = VectorDecl(name, int(match.group("msb")), int(match.group("lsb")))
    for match in _ELECTRICAL_VECTOR_RE.finditer(text):
        name = match.group("name")
        vector_decls.setdefault(name, VectorDecl(name, int(match.group("msb")), int(match.group("lsb"))))

    specs: list[ModuleSpec] = []
    for match in _MODULE_RE.finditer(text):
        specs.append(
            ModuleSpec(
                name=match.group("name"),
                ports=_split_ports(match.group("ports")),
                vector_decls=vector_decls,
                header_match=match,
            )
        )
    return specs


def _expanded_port_count(spec: ModuleSpec) -> int:
    count = 0
    for port in spec.ports:
        vector = spec.vector_decls.get(port)
        count += len(vector.indices) if vector else 1
    return count


def _instance_nodes_for_module(tb_text: str, module_name: str, expected_count: int) -> list[str] | None:
    pattern = re.compile(
        rf"\b[A-Za-z_]\w*\s*\((?P<nodes>[^)]*)\)\s*(?:\\\s*)?{re.escape(module_name)}\b",
        re.DOTALL,
    )
    for match in pattern.finditer(tb_text):
        raw = match.group("nodes").replace("\\", " ")
        nodes = [node for node in re.split(r"\s+", raw.strip()) if node]
        if len(nodes) == expected_count:
            return nodes
    return None


def _scalar_mapping(spec: ModuleSpec, nodes: list[str]) -> tuple[list[str], dict[str, dict[int, str]]] | None:
    next_node = 0
    new_ports: list[str] = []
    vector_map: dict[str, dict[int, str]] = {}
    for port in spec.ports:
        vector = spec.vector_decls.get(port)
        if not vector:
            new_ports.append(port)
            next_node += 1
            continue
        width = len(vector.indices)
        consumed = nodes[next_node : next_node + width]
        if len(consumed) != width:
            return None
        new_ports.extend(consumed)
        vector_map[port] = {idx: node for idx, node in zip(vector.indices, consumed)}
        next_node += width
    return new_ports, vector_map


def _format_wrapped(items: list[str], *, indent: str = "    ", per_line: int = 8) -> str:
    lines: list[str] = []
    for idx in range(0, len(items), per_line):
        lines.append(indent + ", ".join(items[idx : idx + per_line]))
    return ",\n".join(lines)


def _replace_module_header(text: str, spec: ModuleSpec, new_ports: list[str]) -> str:
    replacement = f"module {spec.name} (\n{_format_wrapped(new_ports)}\n);"
    return text[: spec.header_match.start()] + replacement + text[spec.header_match.end() :]


def _replace_vector_declarations(text: str, vector_map: dict[str, dict[int, str]]) -> str:
    def replace_direction(match: re.Match[str]) -> str:
        name = match.group("name")
        scalars = list(vector_map.get(name, {}).values())
        if not scalars:
            return match.group(0)
        electrical = match.group("electrical") or ""
        return f"{match.group('dir')} {electrical}{', '.join(scalars)};"

    def replace_electrical(match: re.Match[str]) -> str:
        name = match.group("name")
        scalars = list(vector_map.get(name, {}).values())
        if not scalars:
            return match.group(0)
        return f"electrical {', '.join(scalars)};"

    text = _DIRECTION_VECTOR_RE.sub(replace_direction, text)
    text = _ELECTRICAL_VECTOR_RE.sub(replace_electrical, text)
    return text


def _replace_constant_v_accesses(text: str, vector_map: dict[str, dict[int, str]]) -> str:
    for vector_name, index_map in vector_map.items():
        for index, scalar in index_map.items():
            pattern = re.compile(rf"\bV\(\s*{re.escape(vector_name)}\s*\[\s*{index}\s*\]\s*\)")
            text = pattern.sub(f"V({scalar})", text)
    return text


def _find_matching_end(text: str, begin_start: int) -> int | None:
    token_re = re.compile(r"\b(begin|end)\b")
    depth = 0
    for match in token_re.finditer(text, begin_start):
        token = match.group(1)
        if token == "begin":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return match.end()
    return None


def _expand_dynamic_vector_contributions(body: str, vector_map: dict[str, dict[int, str]]) -> str:
    """Materialize LHS writes such as V(out[idx]) into static guarded writes.

    Spectre's Verilog-A front end does not accept runtime electrical-vector
    target indexing.  The generated code pattern is usually a scatter write:
    compute a runtime integer index, then drive exactly one vector bit.  This
    rewrite keeps that semantics at the syntax level by spelling out one
    guarded contribution per scalarized bit.
    """
    for vector_name, index_map in vector_map.items():
        pattern = re.compile(
            rf"(?P<indent>[ \t]*)V\(\s*{re.escape(vector_name)}\s*"
            rf"\[\s*(?P<idx>[A-Za-z_]\w*)\s*\]\s*\)\s*<\+\s*(?P<rhs>[^;]+);"
        )

        def replace(match: re.Match[str]) -> str:
            idx_expr = match.group("idx")
            if idx_expr.isdigit():
                return match.group(0)
            indent = match.group("indent")
            rhs = match.group("rhs").strip()
            lines = [
                f"{indent}if ({idx_expr} == {index}) V({scalar}) <+ {rhs};"
                for index, scalar in index_map.items()
            ]
            return "\n".join(lines)

        body = pattern.sub(replace, body)
    return body


def _unroll_dynamic_v_loops(text: str, vector_map: dict[str, dict[int, str]]) -> tuple[str, int]:
    edits = 0
    search_from = 0
    for_re = re.compile(
        r"for\s*\(\s*(?P<var>[A-Za-z_]\w*)\s*=\s*(?P<start>\d+)\s*;"
        r"\s*(?P=var)\s*<\s*(?P<stop>\d+)\s*;[^)]*\)\s*begin",
        re.DOTALL,
    )
    while True:
        match = for_re.search(text, search_from)
        if not match:
            break
        loop_var = match.group("var")
        start = int(match.group("start"))
        stop = int(match.group("stop"))
        begin_match = re.search(r"\bbegin\b", text[match.start() : match.end()])
        if begin_match is None:
            search_from = match.end()
            continue
        begin_start = match.start() + begin_match.start()
        begin_end = match.start() + begin_match.end()
        block_end = _find_matching_end(text, begin_start)
        if block_end is None:
            search_from = match.end()
            continue
        body = text[begin_end : block_end - len("end")]

        vector_names = [
            name
            for name in vector_map
            if re.search(rf"\bV\(\s*{re.escape(name)}\s*\[\s*{re.escape(loop_var)}\s*\]\s*\)", body)
        ]
        if not vector_names:
            search_from = block_end
            continue

        chunks: list[str] = []
        for index in range(start, stop):
            chunk = body
            for name in vector_names:
                scalar = vector_map[name].get(index)
                if not scalar:
                    continue
                chunk = re.sub(
                    rf"\bV\(\s*{re.escape(name)}\s*\[\s*{re.escape(loop_var)}\s*\]\s*\)",
                    f"V({scalar})",
                    chunk,
                )
            chunk = _expand_dynamic_vector_contributions(chunk, vector_map)
            chunk = re.sub(rf"\[\s*{re.escape(loop_var)}\s*\]", f"[{index}]", chunk)
            chunk = re.sub(rf"\b{re.escape(loop_var)}\b", str(index), chunk)
            chunks.append(chunk.rstrip())
        replacement = "\n".join(chunks) + "\n"
        text = text[: match.start()] + replacement + text[block_end:]
        edits += 1
        search_from = match.start() + len(replacement)
    return text, edits


def _rewrite_va_text(text: str, tb_texts: list[str]) -> tuple[str, list[str]]:
    edits: list[str] = []
    specs = _module_specs(text)
    # Rewrite from the end of the file toward the front so cached module-header
    # offsets stay valid even if a source happens to contain helper modules.
    for spec in reversed(specs):
        if not spec.vector_decls:
            continue
        expected = _expanded_port_count(spec)
        nodes: list[str] | None = None
        for tb_text in tb_texts:
            nodes = _instance_nodes_for_module(tb_text, spec.name, expected)
            if nodes:
                break
        if not nodes:
            continue
        mapping = _scalar_mapping(spec, nodes)
        if not mapping:
            continue
        new_ports, vector_map = mapping
        relevant_vector_map = {name: value for name, value in vector_map.items() if name in spec.vector_decls}
        if not relevant_vector_map:
            continue
        before = text
        text = _replace_module_header(text, spec, new_ports)
        text = _replace_vector_declarations(text, relevant_vector_map)
        text = _replace_constant_v_accesses(text, relevant_vector_map)
        text, loop_edits = _unroll_dynamic_v_loops(text, relevant_vector_map)
        if text != before:
            vector_names = ",".join(sorted(relevant_vector_map))
            edits.append(f"vector_unroll:{spec.name}:{vector_names}:loops={loop_edits}")
    return text, edits


def apply_vector_unroll_guard(sample_dir: Path, *, notes: list[str] | None = None) -> list[str]:
    """Apply scalar interface materialization when strict diagnostics call for it."""
    joined_notes = " ".join(str(note).lower() for note in notes or [])
    if notes is not None and not any(
        marker in joined_notes
        for marker in (
            "dynamic_analog_vector_index",
            "instance_port_count_mismatch",
            "sourced_port_voltage_drive",
        )
    ):
        return []

    edits: list[str] = []
    tb_texts: list[str] = []
    for tb_path in sorted(sample_dir.glob("*.scs")):
        text = tb_path.read_text(encoding="utf-8", errors="ignore")
        updated, changed = _normalize_spectre_bus_nodes(text)
        if changed:
            tb_path.write_text(updated, encoding="utf-8")
            edits.append(f"spectre_bus_nodes_to_scalars:{tb_path.name}")
        tb_texts.append(updated)

    for va_path in sorted(sample_dir.glob("*.va")):
        text = va_path.read_text(encoding="utf-8", errors="ignore")
        updated, va_edits = _rewrite_va_text(text, tb_texts)
        if va_edits:
            va_path.write_text(updated, encoding="utf-8")
            edits.extend(f"{item}:{va_path.name}" for item in va_edits)
    return edits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample_dir", type=Path)
    parser.add_argument("--notes-json", type=Path, default=None)
    args = parser.parse_args()
    notes = None
    if args.notes_json:
        data = json.loads(args.notes_json.read_text(encoding="utf-8"))
        notes = data.get("evas_notes") or data.get("notes") or []
    edits = apply_vector_unroll_guard(args.sample_dir, notes=notes)
    print(json.dumps({"sample_dir": str(args.sample_dir), "edits": edits}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
