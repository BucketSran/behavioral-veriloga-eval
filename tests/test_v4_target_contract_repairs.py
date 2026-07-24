from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "provenance"
    / "dut-base-v3-exact-five-hash-bound-v2"
)
RELEASE = ROOT / "benchmark-vabench-release-v4" / "release" / "benchmarkv4"


def _family(prefix: str) -> Path:
    matches = list(SOURCE.glob(f"{prefix}-*"))
    assert len(matches) == 1
    return matches[0]


def _spec(prefix: str) -> dict[str, object]:
    return json.loads((_family(prefix) / "evaluator" / "family_spec.json").read_text())


def _task(name: str) -> Path:
    task = RELEASE / "tasks" / name
    assert task.is_dir()
    return task


def _public_contract(task_name: str) -> dict[str, object]:
    return json.loads((_task(task_name) / "public_contract.json").read_text())


def _source_prefix_for_task_name(task_name: str) -> str:
    family_id = int(task_name.split("-", 1)[0])
    if family_id >= 1000:
        family_id -= 1000
    elif family_id >= 500:
        family_id -= 500
    return f"{family_id:03d}"


def _source_instruction_for_task(task_name: str) -> str:
    return (
        _family(_source_prefix_for_task_name(task_name))
        / "public"
        / "task"
        / "instruction.md"
    ).read_text(encoding="utf-8")


def _source_properties_for_task(task_name: str) -> dict[str, str]:
    return {
        item["id"]: item["observable_contract"]
        for item in _spec(_source_prefix_for_task_name(task_name))["properties"]
    }


def _binding_nets(task_name: str) -> dict[str, str]:
    contract = _public_contract(task_name)
    nets: dict[str, str] = {}
    for instance in contract["testbench_binding"]["instances"]:
        for connection in instance["connections"]:
            nets[connection["port_ref"]] = connection["net"]
    return nets


def _spectre_seconds(token: str) -> float:
    multipliers = {
        "f": 1e-15,
        "p": 1e-12,
        "n": 1e-9,
        "u": 1e-6,
        "m": 1e-3,
    }
    match = re.fullmatch(r"([0-9.]+)([fpnum]?)", token)
    assert match is not None, token
    value = float(match.group(1))
    suffix = match.group(2)
    return value * multipliers.get(suffix, 1.0)


def _pwl_wave(deck: str, source_name: str) -> list[tuple[float, float]]:
    match = re.search(
        rf"^{re.escape(source_name)}\s+\([^)]*\)\s+vsource\s+type=pwl\s+wave=\[([^\]]+)\]",
        deck,
        re.MULTILINE,
    )
    assert match is not None
    tokens = match.group(1).split()
    assert len(tokens) % 2 == 0
    return [
        (_spectre_seconds(tokens[index]), float(tokens[index + 1]))
        for index in range(0, len(tokens), 2)
    ]


def test_masked_config_public_binding_uses_its_declared_trace_net_names() -> None:
    spec = _spec("058")
    instance = spec["testbench_binding"]["instances"][0]
    nets = {item["port_ref"]: item["net"] for item in instance["connections"]}
    for bit in range(32):
        assert nets[f"old_cfg[{bit}]"] == f"old{bit}"
        assert nets[f"new_cfg[{bit}]"] == f"new{bit}"
        assert nets[f"mask[{bit}]"] == f"mask{bit}"
        assert nets[f"out_cfg[{bit}]"] == f"out{bit}"


def test_control_word_public_binding_declares_both_parameterized_instances() -> None:
    spec = _spec("147")
    instances = spec["testbench_binding"]["instances"]
    assert {item["name"] for item in instances} == {"XCTRL42", "XCTRL85"}
    for instance in instances:
        ctrl = int(instance["parameter_overrides"]["ctrl"])
        assert ctrl in {42, 85}
        assert {
            item["port_ref"]: item["net"] for item in instance["connections"]
        } == {f"d{bit}": f"d{bit}_{ctrl}" for bit in range(7)}


def test_repaired_families_have_explicit_reference_testbenches() -> None:
    for prefix in (
        "013",
        "017",
        "020",
        "021",
        "022",
        "024",
        "028",
        "030",
        "033",
        "034",
        "037",
        "040",
        "041",
        "042",
        "043",
        "044",
        "046",
        "050",
        "051",
        "052",
        "053",
        "054",
        "055",
        "056",
        "057",
        "058",
        "059",
        "060",
        "062",
        "064",
        "065",
        "066",
        "067",
        "071",
        "073",
        "074",
        "076",
        "077",
        "078",
        "102",
        "109",
        "111",
        "147",
        "170",
        "301",
        "302",
        "321",
        "364",
        "398",
    ):
        reference = _family(prefix) / "evaluator" / "reference_tb.scs"
        text = reference.read_text(encoding="utf-8")
        assert re.search(r'ahdl_include\s+"\./dut/[^\"]+\.va"', text)


def test_strengthened_reference_testbenches_cover_previous_survivors() -> None:
    strongarm = (
        _family("017") / "evaluator" / "reference_tb.scs"
    ).read_text(encoding="utf-8")
    vinp = _pwl_wave(strongarm, "V_VINP")
    vinn = _pwl_wave(strongarm, "V_VINN")
    zero_diff_times = [
        time
        for (time, vinp_value), (_, vinn_value) in zip(vinp, vinn, strict=True)
        if abs(vinp_value - vinn_value) < 1e-12
    ]
    assert any(4.05e-9 <= time <= 4.15e-9 for time in zero_diff_times)
    assert any(
        4.05e-9 <= time <= 4.15e-9
        and abs(vinp_value - 0.45) < 1e-12
        and abs(vinn_value - 0.45) < 1e-12
        for (time, vinp_value), (_, vinn_value) in zip(vinp, vinn, strict=True)
    )
    assert "tran tran stop=5n" in strongarm

    sample_hold = (
        _family("024") / "evaluator" / "reference_tb.scs"
    ).read_text(encoding="utf-8")
    input_ramp = _pwl_wave(sample_hold, "V_IN")
    assert input_ramp[0] == (0.0, 0.0)
    assert abs(input_ramp[-1][0] - 240e-9) < 1e-18
    assert input_ramp[-1][1] == 0.9
    assert "period=20n" in sample_hold
    assert "tran tran stop=240n maxstep=1n" in sample_hold


def test_charge_pump_reference_never_drives_a_declared_dut_output() -> None:
    family = _family("321")
    spec = json.loads((family / "evaluator" / "family_spec.json").read_text())
    output_nets = {
        connection["net"]
        for instance in spec["testbench_binding"]["instances"]
        for connection in instance["connections"]
        if connection["port_ref"] in {"vctrl", "imbalance_metric", "balanced"}
    }
    text = (family / "evaluator" / "reference_tb.scs").read_text(encoding="utf-8")
    driven_nets = {
        match.group(1)
        for match in re.finditer(
            r"^\s*[A-Za-z_][A-Za-z0-9_]*\s+\(\s*([A-Za-z_][A-Za-z0-9_]*)\s+0\s*\)\s+vsource\b",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
    }
    assert output_nets.isdisjoint(driven_nets)


def test_release_testbench_includes_use_declared_dut_path_contract() -> None:
    bad_includes: list[tuple[str, str]] = []
    missing_support: list[tuple[str, str]] = []
    for task in sorted((RELEASE / "tasks").glob("*-testbench")):
        reference = task / "evaluator" / "reference_tb.scs"
        if not reference.exists():
            reference = task / "evaluator" / "score_tb.scs"
        text = reference.read_text()
        for match in re.finditer(r'ahdl_include\s+"([^"]+)"', text):
            include_path = match.group(1)
            if not include_path.startswith("./dut/"):
                bad_includes.append((task.name, include_path))
            if include_path.startswith("./dut/support/"):
                public_support = (
                    task / "public" / "supplied_dut" / include_path.removeprefix("./dut/")
                )
                if not public_support.exists():
                    missing_support.append((task.name, include_path))

    assert bad_includes == []
    assert missing_support == []


def test_release_reference_decks_do_not_drive_declared_outputs() -> None:
    direct_drives: list[tuple[str, str]] = []
    for task in sorted((RELEASE / "tasks").glob("*-testbench")):
        reference = task / "evaluator" / "reference_tb.scs"
        if not reference.exists():
            reference = task / "evaluator" / "score_tb.scs"
        text = reference.read_text()
        contract = json.loads((task / "public_contract.json").read_text())
        port_directions: dict[str, dict[str, str]] = {}
        for file_contract in contract["artifact_contract"]["files"]:
            for module in file_contract["modules"]:
                module_ports: dict[str, str] = {}
                for port in module["ports"]:
                    module_ports[port["name"]] = port["direction"]
                    module_ports[port["name"].split("[", 1)[0]] = port["direction"]
                port_directions[module["name"]] = module_ports

        output_nets: set[str] = set()
        for instance in contract["testbench_binding"]["instances"]:
            module_ports = port_directions[instance["module_ref"]]
            for connection in instance["connections"]:
                port_ref = connection["port_ref"]
                direction = module_ports.get(
                    port_ref,
                    module_ports.get(port_ref.split("[", 1)[0]),
                )
                net = connection["net"]
                if direction == "output" and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", net):
                    output_nets.add(net)

        for net in output_nets:
            if re.search(
                rf"^V\w+\s*\([^)]*\b{re.escape(net)}\b[^)]*\)\s+vsource\b",
                text,
                re.MULTILINE,
            ):
                direct_drives.append((task.name, net))

    assert direct_drives == []


def test_sarfend_public_contract_exposes_trial_and_bit_mapping_semantics() -> None:
    task_names = (
        "186-sarfend-logic-4b",
        "686-sarfend-logic-4b-testbench",
        "1186-sarfend-logic-4b-bugfix",
    )
    for task_name in task_names:
        instruction = _source_instruction_for_task(task_name)
        assert "dp4=dm4=0" in instruction
        assert "dp3=dm3=dp2=dm2=dp1=dm1=1" in instruction
        assert "dout3=dp4" in instruction
        assert "`dtest3`, `dtest2`, `dtest1`, then `dtest0`" in instruction

        properties = _source_properties_for_task(task_name)
        assert "dp4=dm4=0" in properties["P_CONVERSION_RESET_AND_PREVIOUS_WORD"]
        assert "MSB-to-LSB" in properties["P_SAMPLE_AND_COMPARATOR_DECISIONS"]


def test_sarfend_checker_clamps_pre_roll_baseline_after_affine_normalization() -> None:
    sys.path.insert(0, str(ROOT))
    from runners.checkers.v4.task_186 import sample_signal_at

    rows = [
        {"time": 0.8325e-9, "clkc": 0.0},
        {"time": 1.025e-9, "clkc": 1.0},
    ]
    assert sample_signal_at(rows, "clkc", 0.3e-9) == 0.0
    assert sample_signal_at(rows, "clkc", 0.9e-9) > 0.0
    assert sample_signal_at(rows, "clkc", 2.0e-9) is None


def test_quadrature_monitor_gold_uses_the_public_voltage_tolerance() -> None:
    solution = (
        _family("335")
        / "evaluator"
        / "solution"
        / "quadrature_oscillator_phase_error_monitor.va"
    ).read_text(encoding="utf-8")
    assert "metric_v <= phase_tol" in solution
    assert "phase_err <= 0.10" not in solution


def test_quadrature_monitor_checker_waits_for_inactive_outputs_to_settle() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_335.py").read_text()
    assert "inactive_ready = t >= inactive_time + 0.7e-9" in checker
    assert "if inactive_ready and (rst or disabled) and not clear" in checker


def test_repaired_checkers_name_every_public_property() -> None:
    sys.path.insert(0, str(ROOT))
    from runners.checkers.v4.task_254 import CHECKER as checker_254
    from runners.checkers.v4.task_393 import CHECKER as checker_393

    for prefix, checker in (("254", checker_254), ("393", checker_393)):
        property_ids = json.loads(
            (_family(prefix) / "evaluator" / "harness_spec.json").read_text()
        )["property_ids"]
        _, note = checker([])
        assert all(property_id in note for property_id in property_ids)


def test_dynamic_comparator_checker_does_not_require_redundant_decisions() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_313.py").read_text()
    assert "checked >= 5" in checker
    assert "checked >= 6" not in checker


def test_serializer_checker_uses_observed_disable_timing() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_392.py").read_text()
    assert "disable_time" in checker
    assert "t > 82e-9" not in checker


def test_supply_supervisor_checker_orders_overlapping_input_crossings() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_399.py").read_text()
    assert "events.sort()" in checker
    assert "vdd_at_event = _value_at_time" in checker
    assert "controls_changed" in checker


def test_pll_monitor_checker_resets_across_clockless_inactive_windows() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_351.py").read_text()
    assert "inactive_between(previous_event_time, time)" in checker
    assert "inactive_between(previous_fb_time, edge)" in checker


def test_cdr_checker_uses_the_bound_lock_window_and_transition_sample() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_357.py").read_text()

    assert "LOCK_WINDOW_STEPS = 2.0" in checker
    assert "UNIT_PHASE_DELAY = 40e-12" in checker
    assert "DECISION_SAMPLE_FRACTION = 0.5" in checker
    assert 'rows[0].get("_time_scale", 1.0)' in checker
    assert "PHASE_ERROR_FRACTION_MAX" not in checker
    assert "_inactive_between(rows, source_time, observation_stop)" in checker
    assert 'expected_destination > float(rows[-1]["time"])' in checker
    assert "last_inactive < edge < source_time" in checker


def test_tia_checker_samples_only_stable_input_windows() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_368.py").read_text()

    assert "last_input_change" in checker
    assert "stable_samples" in checker
    assert 'rows[0].get("_time_scale", 1.0)' in checker
    assert "t > 82e-9" not in checker


def test_cdr_and_tia_checkers_name_every_public_property() -> None:
    sys.path.insert(0, str(ROOT))
    from runners.checkers.v4.task_357 import CHECKER as checker_357
    from runners.checkers.v4.task_368 import CHECKER as checker_368

    for prefix, checker in (("357", checker_357), ("368", checker_368)):
        property_ids = json.loads(
            (_family(prefix) / "evaluator" / "harness_spec.json").read_text()
        )["property_ids"]
        _, note = checker([])
        assert all(property_id in note for property_id in property_ids)


def test_sample_hold_checker_uses_clamped_capture_and_duration_scaled_droop() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_100.py").read_text()

    assert "expected = min(vdd, max(vss, vin_capture))" in checker
    assert "math.exp(-(stop_time - start_time) / droop_tau)" in checker
    assert 'expected="rising_edges>=6_aperture_sensitive>=1"' in checker
    assert "0.004 <= droop <= 0.16" not in checker


def test_sarfend_checker_accepts_event_relative_noncanonical_timing() -> None:
    sys.path.insert(0, str(ROOT))
    from runners.checkers.v4.task_186 import CHECKER

    rows: list[dict[str, float]] = []
    for time_ns in range(151):
        if time_ns < 20 or 80 <= time_ns < 95 or time_ns >= 140:
            p = [0, 1, 1, 1]
        elif time_ns < 40 or 95 <= time_ns < 105:
            p = [1, 1, 1, 1]
        elif time_ns < 70 or 105 <= time_ns < 125:
            p = [1, 0, 1, 1]
        else:
            p = [1, 0, 1, 0]
        if 60 <= time_ns < 80 or 115 <= time_ns < 140:
            m = [0, 1, 0, 1]
        else:
            m = [0, 1, 1, 1]
        if time_ns < 10:
            dout = [0, 0, 0, 0]
        elif time_ns < 80:
            dout = [1, 1, 1, 0]
        else:
            dout = [0, 1, 0, 1]
        clkc = int(
            15 <= time_ns < 20
            or 25 <= time_ns < 40
            or 45 <= time_ns < 60
            or 65 <= time_ns < 70
            or 85 <= time_ns < 95
            or 100 <= time_ns < 105
            or 110 <= time_ns < 115
            or 120 <= time_ns < 125
            or time_ns >= 145
        )
        rows.append(
            {
                "time": (time_ns + 3000) * 1e-9,
                "clks": float(
                    10 <= time_ns < 15
                    or 80 <= time_ns < 85
                    or 140 <= time_ns < 145
                ),
                "dcomp": float(
                    20 <= time_ns < 25
                    or 60 <= time_ns < 65
                    or 105 <= time_ns < 110
                    or 125 <= time_ns < 130
                    or 132 <= time_ns < 136
                ),
                "dcompb": float(
                    40 <= time_ns < 45
                    or 70 <= time_ns < 75
                    or 95 <= time_ns < 100
                    or 115 <= time_ns < 120
                ),
                "test": float(time_ns >= 90),
                "dtest0": 0.0,
                "dtest1": 1.0,
                "dtest2": 0.0,
                "dtest3": 1.0,
                "clkc": float(clkc),
                "dp4": float(p[0]),
                "dp3": float(p[1]),
                "dp2": float(p[2]),
                "dp1": float(p[3]),
                "dm4": float(m[0]),
                "dm3": float(m[1]),
                "dm2": float(m[2]),
                "dm1": float(m[3]),
                "dout0": float(dout[0]),
                "dout1": float(dout[1]),
                "dout2": float(dout[2]),
                "dout3": float(dout[3]),
            }
        )

    passed, note = CHECKER(rows)
    assert passed, note


def test_rail_normalized_mapper_exposes_formula_and_distinct_valid_gate() -> None:
    task_names = (
        "274-rail-normalized-metric-mapper",
        "774-rail-normalized-metric-mapper-testbench",
        "1274-rail-normalized-metric-mapper-bugfix",
    )
    for task_name in task_names:
        instruction = _source_instruction_for_task(task_name)
        assert "local_meas = V(meas) - V(vss)" in instruction
        assert "norm = vhi * clip01(local_meas / span)" in instruction
        assert "span_min <= span <= span_max" in instruction
        assert "above `span_max`" in instruction

        properties = _source_properties_for_task(task_name)
        assert "local_meas / span" in properties[
            "P_NORMALIZE_MEAS_RELATIVE_TO_THE_LOCAL"
        ]
        assert "does not by itself clear clipped norm" in properties[
            "P_CLEAR_NORM_AND_VALID_WHILE_DISABLED"
        ]


def test_affine_calibration_exposes_sampled_update_and_exact_formula() -> None:
    task_names = (
        "284-calibration-affine-transform",
        "784-calibration-affine-transform-testbench",
        "1284-calibration-affine-transform-bugfix",
    )
    for task_name in task_names:
        instruction = _source_instruction_for_task(task_name)
        assert "only on" in instruction
        assert "gain_base + gain_span * clip01(V(gain_ctrl) / vhi)" in instruction
        assert "center + gain * (V(raw) - center) + offset" in instruction
        assert "abs(transformed - V(raw)) / resid_fullscale" in instruction

        properties = _source_properties_for_task(task_name)
        assert "only on each rising clk crossing" in properties[
            "P_ON_EACH_RISING_CLOCK_CROSSING_COMPUTE"
        ]
        assert "clip01(abs(transformed - V(raw))" in properties[
            "P_EXPOSE_A_BOUNDED_RESIDUAL_METRIC_FOR"
        ]


def test_reacquire_lock_exposes_count_and_metric_encoding() -> None:
    task_names = (
        "291-event-reacquire-lock-detector",
        "791-event-reacquire-lock-detector-testbench",
        "1291-event-reacquire-lock-detector-bugfix",
    )
    for task_name in task_names:
        instruction = _source_instruction_for_task(task_name)
        assert "phase_error" in instruction
        assert "metric_fullscale" in instruction
        assert "phase_error / metric_fullscale" in instruction
        assert "good_count / lock_count" in instruction

        properties = _source_properties_for_task(task_name)
        assert "phase_error <= lock_window" in properties[
            "P_REQUIRE_CONSECUTIVE_IN_WINDOW_FEEDBACK_EDGE"
        ]
        assert "good_count / lock_count" in properties[
            "P_EXPOSE_PHASE_METRIC_AND_STATE_MON"
        ]


def test_generated_monitor_families_replace_task_specific_placeholders() -> None:
    expected = {
        "285-configurable-startup-policy": "abs(x0 - 0.48) / 0.48",
        "286-explicit-replicated-stage-chain": "0.36*x0 + 0.28*x1",
        "287-edge-delay-qualified-driver": "x0 > x1",
    }
    for family, formula in expected.items():
        family_id, slug = family.split("-", 1)
        for task_name in (
            family,
            f"{int(family_id) + 500}-{slug}-testbench",
            f"{int(family_id) + 1000}-{slug}-bugfix",
        ):
            instruction = _source_instruction_for_task(task_name)
            contracts = " ".join(_source_properties_for_task(task_name).values())
            assert "task-specific" not in instruction
            assert "task-specific" not in contracts
            assert formula.replace(" ", "") in instruction.replace(" ", "")


def test_sampled_error_monitor_exposes_update_equations() -> None:
    for task_name in (
        "270-sampled-error-update-monitor",
        "770-sampled-error-update-monitor-testbench",
        "1270-sampled-error-update-monitor-bugfix",
    ):
        instruction = _source_instruction_for_task(task_name)
        compact = instruction.replace(" ", "")
        assert "V(target)-V(sample)" in compact
        assert "V(sample)+coeff*error" in compact
        assert "abs(error)/err_fullscale" in compact
        assert "stable_count/ready_count" in compact
        assert "enabled rising clock edge" not in instruction


def test_tia_and_track_hold_expose_numeric_metric_contracts() -> None:
    for task_name in (
        "304-common-gate-tia-front-end",
        "804-common-gate-tia-front-end-testbench",
        "1304-common-gate-tia-front-end-bugfix",
    ):
        compact = _source_instruction_for_task(task_name).replace(" ", "")
        assert "(V(bias)-bias_min)/(vcm-bias_min)" in compact
        assert "vdd*effective_gain/rz_gain" in compact
        assert "raw_target" in compact

    for task_name in (
        "311-muxed-track-hold-array-readout",
        "811-muxed-track-hold-array-readout-testbench",
        "1311-muxed-track-hold-array-readout-bugfix",
    ):
        compact = _source_instruction_for_task(task_name).replace(" ", "")
        assert "vcm+0.15*code" in compact
        assert "held-valid" in compact
        assert "vout" in compact and "vcm" in compact


def test_long_running_families_expose_exact_numeric_contracts() -> None:
    expected = {
        "305": ("1.0+gain_step*code", "donotapplyanadditionalslewstep"),
        "313": ("0.30/(1.0+overdrive/0.030)", "abs(v(vinp)-v(vinn))"),
        "317": ("code*corr_lsb", "cal_0+2*cal_1+4*cal_2+8*cal_3"),
        "323": ("code*200ps", "code*unit_delay_metric"),
        "326": ("(code+1)*200ps", "(vdd-vss)*code/15"),
    }
    for family_id, snippets in expected.items():
        compact = (
            (_family(family_id) / "public" / "task" / "instruction.md")
            .read_text()
            .lower()
            .replace(" ", "")
        )
        for snippet in snippets:
            assert snippet in compact


def test_dfe_family_exposes_exact_state_transition_contract() -> None:
    snippets = (
        "tap_1andtap_0aredut-driven",
        "r0=x-w1*h1-w0*h0",
        "w1=clamp(w1+0.04*r0*h1,-0.18,0.18)",
        "w0=clamp(w0+0.025*r0*h0,-0.12,0.12)",
        "h0=h1;h1=d",
        "tap_1=vcm+w1",
        "corrected_out=clamp(vcm+r,vss,vdd)",
    )
    family = (
        ROOT
        / "benchmark-vabench-release-v4"
        / "provenance"
        / "dut-base-v3-exact-five-hash-bound-v2"
        / "331-dfe-error-proxy-loop"
    )
    compact = (
        (family / "public" / "task" / "instruction.md")
        .read_text()
        .lower()
        .replace(" ", "")
        .replace("\n", "")
        .replace("`", "")
    )
    for snippet in snippets:
        assert snippet in compact

    spec = json.loads((family / "evaluator" / "family_spec.json").read_text())
    modules = {
        module["name"]: module
        for file_record in spec["artifact_contract"]["files"]
        for module in file_record["modules"]
    }
    top_parameter_names = [
        parameter["name"]
        for parameter in modules["dfe_error_proxy_loop_top"]["parameters"]
    ]
    assert top_parameter_names[-1] == "residual_tol"
    assert [port["name"] for port in modules["decision_history"]["ports"]] == [
        "sample_in", "decision_clk", "rst", "enable", "hist_1", "hist_0"
    ]
    assert [port["name"] for port in modules["feedback_correction_core"]["ports"]][-5:] == [
        "tap_1", "tap_0", "corrected_out", "error_metric", "converged"
    ]


def test_residue_gain_calibration_exposes_exact_state_transition_contract() -> None:
    snippets = (
        "gain_2,gain_1,andgain_0aredut-driven",
        "drivevouttotheneutralresiduelevelvcm",
        "gain=base_gain+gain_lsb*code",
        "vout=clamp(vcm+gain*(vin-vcm),vss,vdd)",
        "signed_error=residue_ref-vout",
        "error_metric=abs(residue_ref-vout)",
        "saturatingat7",
        "saturatingat0",
        "afterthethirdsuchsample",
    )
    family = (
        ROOT
        / "benchmark-vabench-release-v4"
        / "provenance"
        / "dut-base-v3-exact-five-hash-bound-v2"
        / "316-residue-amplifier-gain-calibration"
    )
    compact = (
        (family / "public" / "task" / "instruction.md")
        .read_text()
        .lower()
        .replace(" ", "")
        .replace("\n", "")
        .replace("`", "")
    )
    for snippet in snippets:
        assert snippet in compact

    spec = json.loads((family / "evaluator" / "family_spec.json").read_text())
    contracts = " ".join(item["observable_contract"] for item in spec["properties"])
    assert "vout = clamp(vcm + gain*(vin-vcm), vss, vdd)" in contracts
    assert "error_metric = abs(residue_ref-vout)" in contracts
    assert "while `cal_en` is low" in contracts


def test_residue_gain_calibration_emits_property_diagnostics() -> None:
    from runners.checkers.v4.task_316 import CHECKER

    passed, note = CHECKER([])
    assert not passed
    for property_id in (
        "P_ON_RESET_CLEAR_GAIN_CODE_OUTPUT",
        "P_WHILE_CAL_EN_IS_HIGH_COMPARE",
        "P_INCREMENT_OR_DECREMENT_THE_GAIN_CODE",
        "P_DRIVE_VOUT_AS_A_CLAMPED_RESIDUE",
        "P_ASSERT_LOCKED_AFTER_THREE_CONSECUTIVE_UPDATES",
        "P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE",
    ):
        assert f"{property_id} mismatch_count=" in note
    assert "diagnostic_schema=v4-checker-diagnostic-v1" in note


def test_residue_gain_calibration_gold_uses_public_lock_contract() -> None:
    controller = (
        ROOT
        / "benchmark-vabench-release-v4"
        / "provenance"
        / "dut-base-v3-exact-five-hash-bound-v2"
        / "316-residue-amplifier-gain-calibration"
        / "evaluator"
        / "solution"
        / "gain_cal_controller.va"
    ).read_text(encoding="utf-8")

    assert "err > lock_tol" in controller
    assert "err < -lock_tol" in controller
    assert "absval(err) <= lock_tol" in controller
    assert "lock_count >= 3" in controller
    assert "code >= 4" not in controller
    assert "updates >= 8" not in controller


def test_image_reject_mixer_exposes_exact_calibration_contract() -> None:
    snippets = (
        "drivei_outandq_outtotheneutralmixerlevelvcm",
        "g=0.8*(gain_trim-vcm)",
        "p=0.6*(phase_trim-vcm)",
        "i=x*si*(1-g)",
        "q=-x*sq*(1+g)-p*x*si",
        "raw_image_metric=clamp(0.5*abs(i+q),vss,vdd)",
        "gain_trim=clamp(gain_trim+d*18e-3",
        "phase_trim=clamp(phase_trim-d*9e-3",
        "d=-d",
    )
    family = (
        ROOT
        / "benchmark-vabench-release-v4"
        / "provenance"
        / "dut-base-v3-exact-five-hash-bound-v2"
        / "333-image-reject-mixer-calibration-loop"
    )
    compact = (
        (family / "public" / "task" / "instruction.md")
        .read_text()
        .lower()
        .replace(" ", "")
        .replace("\n", "")
        .replace("`", "")
    )
    for snippet in snippets:
        assert snippet in compact

    spec = json.loads((family / "evaluator" / "family_spec.json").read_text())
    contracts = " ".join(item["observable_contract"] for item in spec["properties"])
    assert "q=-x*sq*(1+g)-p*x*si" in contracts
    assert "phase trim by `-d*9e-3`" in contracts
    assert "drive `i_out` and `q_out` to `vcm`" in contracts


def test_vga_step_response_exposes_exact_classifier_contract() -> None:
    snippets = (
        "tick=250ps",
        "code=4*gain_2+2*gain_1+gain_0",
        "target=clamp(vcm+(1+gain_lsb*code)*(vin-vcm),vss,vdd)",
        "overshoot_metric=vdd*abs(code-prev_code)/7",
        "ifcode==prev_code",
        "newlychangedcodesettlesaftertwosubsequentunchanged-codecomparisons",
    )
    family = (
        ROOT
        / "benchmark-vabench-release-v4"
        / "provenance"
        / "dut-base-v3-exact-five-hash-bound-v2"
        / "337-vga-step-response-classifier"
    )
    compact = (
        (family / "public" / "task" / "instruction.md")
        .read_text()
        .lower()
        .replace(" ", "")
        .replace("\n", "")
        .replace("`", "")
    )
    for snippet in snippets:
        assert snippet in compact

    spec = json.loads((family / "evaluator" / "family_spec.json").read_text())
    contracts = " ".join(item["observable_contract"] for item in spec["properties"])
    assert "overshoot_metric=vdd*abs(code-prev_code)/7" in contracts
    assert "a newly changed code therefore needs two subsequent unchanged-code comparisons" in contracts
    assert "without adding an overshoot excursion to `vout`" in contracts


def test_common_mode_feedback_exposes_exact_unsigned_control_contract() -> None:
    snippets = (
        "raw_error=(vop_in+von_in)/2-vcm",
        "residual_before=raw_error-trim_code*trim_lsb",
        "residual_before>lock_tol",
        "residual_before<-lock_tol",
        "residual_after=raw_error-trim_code*trim_lsb",
        "abs(residual_after)<=lock_tol",
        "vop_out=clamp(vop_in-trim_corr,vss,vdd)",
        "von_out=clamp(von_in-trim_corr,vss,vdd)",
    )
    family = (
        ROOT
        / "benchmark-vabench-release-v4"
        / "provenance"
        / "dut-base-v3-exact-five-hash-bound-v2"
        / "390-common-mode-feedback-loop"
    )
    compact = (
        (family / "public" / "task" / "instruction.md")
        .read_text()
        .lower()
        .replace(" ", "")
        .replace("\n", "")
        .replace("`", "")
    )
    for snippet in snippets:
        assert snippet in compact

    spec = json.loads((family / "evaluator" / "family_spec.json").read_text())
    contracts = " ".join(item["observable_contract"] for item in spec["properties"])
    assert "residual_before=raw_error-trim_code*trim_lsb" in contracts
    assert "abs(residual_after)<=lock_tol" in contracts
    assert "applying the same correction to preserve the differential" in contracts


def test_late_dut_families_expose_checker_defining_equations() -> None:
    required = {
        "365": (
            "gain_error=abs(i_in-vcm)-abs(q_in-vcm)-signed_gain*trim_lsb",
            "phase_error=(i_in-vcm)*(q_in-vcm)-signed_phase*trim_lsb",
        ),
        "366": (
            "i_state=i_state+alpha*(vin-i_state)",
            "q_state=q_state+alpha*(old_i-q_state)",
        ),
        "370": (
            "error_metric=vcm+error",
            "target=clamp(vcm+(1+gain_lsb*code)*(vin-vcm),vss,vdd)",
        ),
        "372": (
            "carrier_count=(carrier_count+1)%20",
            "carrier_count+0.5<20*duty_metric",
        ),
        "387": (
            "active_gain=small_gain/(1+excess/0.20)",
            "active_gain<0.85*small_gain",
        ),
        "389": (
            "rail_limit=min(vdd_sense,vbias)-headroom_drop",
            "rail_limit>vcm+0.05v",
        ),
    }
    for family_id, snippets in required.items():
        compact = (
            (_family(family_id) / "public" / "task" / "instruction.md")
            .read_text()
            .lower()
            .replace(" ", "")
            .replace("\n", "")
            .replace("`", "")
        )
        for snippet in snippets:
            assert snippet in compact


def test_quadrature_correction_rejects_short_calibration_prefix() -> None:
    source = (ROOT / "runners" / "checkers" / "v4" / "task_365.py").read_text()
    assert "minimum_checks = 5" in source
    assert "trim_checks < minimum_checks" in source
    assert "correction_checks < minimum_checks" in source
    assert "hold_checks < minimum_checks" in source


def test_repaired_testbench_bindings_match_reference_trace_names() -> None:
    expected = {
        "517-strongarm-style-latch-comparator-testbench": {
            "DCMPN": "out_n",
            "DCMPP": "out_p",
        },
        "524-clocked-sample-and-hold-testbench": {
            "IN": "in",
            "OUT": "out",
        },
        "527-dwa-dem-encoder-testbench": {
            "clk": "clk_i",
            "vin": "vin_node",
            "code_msb_i[3]": "code_3",
            "code_msb_i[0]": "code_0",
            "cell_en_o[15]": "cell_en_15",
            "cell_en_o[0]": "cell_en_0",
            "ptr_o[15]": "ptr_15",
            "ptr_o[0]": "ptr_0",
        },
        "539-propagation-delay-comparator-testbench": {
            "CLK": "clk",
            "VINN": "vinn",
            "VINP": "vinp",
            "DCMPN": "out_n",
            "DCMPP": "out_p",
            "LP": "lp_int",
            "LM": "lm_int",
            "VSS": "gnd",
            "VDD": "vdd",
            "CLK_1": "clk",
            "CLK_2": "out_p",
        },
        "602-clocked-sine-source-testbench": {
            "VOUT_P": "vinp",
            "VOUT_N": "vinn",
        },
    }

    for task_name, expected_nets in expected.items():
        actual = _binding_nets(task_name)
        for port_ref, net in expected_nets.items():
            assert actual[port_ref] == net


def test_testbench_checkers_do_not_require_canonical_stimulus_end_states() -> None:
    lock_checker = (ROOT / "runners" / "checkers" / "v4" / "task_009.py").read_text()
    offset_checker = (ROOT / "runners" / "checkers" / "v4" / "task_010.py").read_text()

    assert "and final_lock_low" not in lock_checker
    assert 'sequence == "LLLHHLL"' not in offset_checker
    assert "for edge_t in edge_times:" in offset_checker
    assert "for index, edge_time in enumerate(edge_times):" in offset_checker


def test_dynamic_testbench_checkers_do_not_bind_unrelated_stimulus_windows() -> None:
    divider_checker = (ROOT / "runners" / "checkers" / "v4" / "task_012.py").read_text()
    slew_checker = (ROOT / "runners" / "checkers" / "v4" / "task_016.py").read_text()
    tdc_checker = (ROOT / "runners" / "checkers" / "v4" / "task_179.py").read_text()
    gain_checker = (ROOT / "runners" / "checkers" / "v4" / "task_093.py").read_text()
    peak_checker = (ROOT / "runners" / "checkers" / "v4" / "task_075.py").read_text()

    assert "stable_logic_plateaus" in divider_checker
    assert "active[-1][bit] > 0.45" not in divider_checker
    assert 'max(row[bit] for row in rows)' not in divider_checker
    assert "0.10 <= row[\"vout\"] <= 0.68" not in slew_checker
    assert "_transition_fit(rows, rise_time, fall_time)" in slew_checker
    assert "measured_deltas" in tdc_checker
    assert "_trace_time_scale" in tdc_checker
    assert "(3.0, -0.3" not in tdc_checker
    assert "0.045 <= in_span <= 0.075" not in gain_checker
    assert "0.27 <= out_span <= 0.45" not in gain_checker
    assert "gain_err <= gain_tolerance" in gain_checker
    assert "stop - start < 8.0e-9" not in peak_checker
    assert "stop - start < 2.0e-9" in peak_checker


def test_slew_checker_skips_short_diagnostic_pulses() -> None:
    sys.path.insert(0, str(ROOT))
    from runners.checkers.v4.task_016 import _sustained_excursion

    excursion = _sustained_excursion(
        [0.5e-9, 5.5e-9, 45.5e-9],
        [1.5e-9, 20.5e-9],
        trace_stop=95.0e-9,
    )

    assert excursion == (5.5e-9, 20.5e-9, 45.5e-9)


def test_slew_transition_fit_ignores_later_near_target_reentry() -> None:
    sys.path.insert(0, str(ROOT))
    from runners.checkers.v4.task_016 import _transition_fit

    outputs = (0.06, 0.045, 0.03, 0.015, 0.0, 0.0, 0.0, 0.008, 0.008, 0.008)
    rows = [
        {"time": index * 1e-9, "vin": 0.0, "vout": output}
        for index, output in enumerate(outputs)
    ]

    fit = _transition_fit(rows, 0.0, 10e-9)

    assert len(fit) == 3
    assert fit[-1]["time"] < 4e-9


def test_settling_window_gold_and_mutations_saturate_entry_code() -> None:
    evaluator = _family("063") / "evaluator"
    implementations = [
        evaluator / "solution" / "settling_window_detector.va",
        *sorted(
            (evaluator / "mutation_bundles").glob(
                "neg_00*/settling_window_detector.va"
            )
        ),
    ]
    implementations = [path for path in implementations if "neg_001_zero" not in path.parts]

    for implementation in implementations:
        source = implementation.read_text()
        assert "if (code > 255) code=255;" in source
        assert "if (code < 0) code=0;" in source

    wrong_code = (
        evaluator
        / "mutation_bundles"
        / "neg_005_wrong_code"
        / "settling_window_detector.va"
    ).read_text()
    assert "$abstime+20n" in wrong_code


def test_settling_window_checker_normalizes_affine_trace_time() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_063.py").read_text()

    assert 'rows[0].get("_time_scale", 1.0)' in checker
    assert 'rows[0].get("_time_shift_s", 0.0)' in checker
    assert "physical_entry = (entry - time_shift_s) / time_scale" in checker
    assert 'row_at_or_after(rows, settled_t)' in checker


def test_v4_batch_certifier_uses_the_active_suite_not_the_full_catalog() -> None:
    certifier = (
        ROOT
        / "benchmark-vabench-release-v4"
        / "scripts"
        / "validate_v4_checker_batch.py"
    ).read_text()

    assert "load_family_rows" in certifier
    assert "selected_mutation_ids(task, active_suites)" in certifier
    assert 'if str(row["id"]) in mutation_ids' in certifier
    assert "non-empty diagnostic, not one particular rendering vocabulary" in certifier
    assert 'return bool(note.strip()) and "=" in note' in certifier


def test_legacy_event_checkers_replay_submitted_stimulus_instead_of_gold_times() -> None:
    event_families = ("173", "182", "183", "184", "185")
    for family_id in event_families:
        checker = (
            ROOT / "runners" / "checkers" / "v4" / f"task_{family_id}.py"
        ).read_text()
        assert "normalize_affine_time" not in checker
        assert "edge_times(" in checker
        assert "PropertyResult" in checker

    trim_checker = (
        ROOT / "runners" / "checkers" / "v4" / "task_189.py"
    ).read_text()
    assert "normalize_affine_time" not in trim_checker
    assert "_code_plateaus" in trim_checker
    assert 'math.floor(row["ain"] + 0.5)' in trim_checker


def test_leaky_hold_capture_ignores_sample_edges_while_reset_is_active() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_042.py").read_text()

    assert 'sample(rows, "rst", edge_t)' in checker
    assert 'expected="active_sample_edges>=3"' in checker
    assert "hold_windows" in checker


def test_edge_interval_tdc_pairs_only_armed_start_stop_events() -> None:
    checker = (ROOT / "runners" / "checkers" / "v4" / "task_059.py").read_text()

    assert "_measurement_pairs(starts, stops)" in checker
    assert "for start_t, stop_t in zip(starts, stops)" not in checker
    assert "math.floor((stop_t - start_t)" in checker
