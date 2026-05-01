#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")


@dataclass(frozen=True)
class SignatureSpec:
    required_ports: tuple[str, ...] = ()
    required_parameters: tuple[str, ...] = ()
    required_tokens: tuple[str, ...] = ()
    forbidden_tokens: tuple[str, ...] = ()
    required_tb_tokens: tuple[str, ...] = ()
    forbidden_tb_tokens: tuple[str, ...] = ()


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


def spec_from_meta(meta: dict[str, Any]) -> SignatureSpec:
    """Build a guardrail spec from task metadata.

    `signature_requirements` is the explicit contract for benchmark-critical
    ports/params/tokens. Do not promote legacy `must_include` text checks into
    hard guardrails here: the existing benchmark uses those fields as broad
    authoring hints, and some validated gold tasks use equivalent but nonliteral
    implementations.
    """
    signature = meta.get("signature_requirements") or {}
    return SignatureSpec(
        required_ports=_as_str_tuple(signature.get("required_ports")),
        required_parameters=_as_str_tuple(signature.get("required_parameters")),
        required_tokens=_as_str_tuple(signature.get("required_tokens")),
        forbidden_tokens=_as_str_tuple(signature.get("forbidden_tokens")),
        required_tb_tokens=_as_str_tuple(signature.get("required_tb_tokens")),
        forbidden_tb_tokens=_as_str_tuple(signature.get("forbidden_tb_tokens")),
    )


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*$", "", text, flags=re.MULTILINE)


def _has_identifier(text: str, name: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_$]){re.escape(name)}(?![A-Za-z0-9_$])", text) is not None


def _declares_parameter(text: str, name: str) -> bool:
    return (
        re.search(
            rf"\bparameter\b[^;]*?(?<![A-Za-z0-9_$]){re.escape(name)}(?![A-Za-z0-9_$])",
            text,
            flags=re.DOTALL,
        )
        is not None
    )


def check_candidate_signature(text: str, spec: SignatureSpec) -> list[str]:
    cleaned = _strip_comments(text)
    findings: list[str] = []

    for port in spec.required_ports:
        if not _has_identifier(cleaned, port):
            findings.append(f"missing required port `{port}`")

    for param in spec.required_parameters:
        if not _declares_parameter(cleaned, param):
            findings.append(f"missing required parameter `{param}`")

    for token in spec.required_tokens:
        if token and token not in cleaned:
            findings.append(f"missing required token `{token}`")

    for token in spec.forbidden_tokens:
        if token and token in cleaned:
            findings.append(f"forbidden token present `{token}`")

    return findings


def check_testbench_signature(text: str, spec: SignatureSpec) -> list[str]:
    cleaned = _strip_comments(text)
    findings: list[str] = []

    for token in spec.required_tb_tokens:
        if token and token not in cleaned:
            findings.append(f"missing required testbench token `{token}`")

    for token in spec.forbidden_tb_tokens:
        if token and token in cleaned:
            findings.append(f"forbidden testbench token present `{token}`")

    return findings


def check_signature_bundle(dut_text: str, tb_text: str, spec: SignatureSpec) -> tuple[list[str], list[str]]:
    return check_candidate_signature(dut_text, spec), check_testbench_signature(tb_text, spec)


def main() -> int:
    ap = argparse.ArgumentParser(description="Check benchmark signature guardrails for a candidate DUT.")
    ap.add_argument("meta", type=Path, help="Task meta.json")
    ap.add_argument("dut", type=Path, help="Candidate Verilog-A DUT")
    args = ap.parse_args()

    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    spec = spec_from_meta(meta)
    findings = check_candidate_signature(args.dut.read_text(encoding="utf-8"), spec)
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
