"""Fixed, candidate-bound public feedback; never final-checker authority."""

from copy import deepcopy
import hashlib
import json
import math
import re
import uuid

from ..authority_profiles import profile_input_identity_sha256, public_validation_profile_sha256
from ..state import EnvironmentStep, Observation, ToolExecutionRejection
from ..tool_registry import tool_descriptor_sha256
from . import waveform_summary as waveform

TOOL_NAME = "vaevas_public_simulate"
INTERVENTION = "isolated-public-waveform-v1"
PROMPT = (
    "\nOptional vaevas_public_simulate({}) runs the fixed public checker in a fresh isolated "
    "EVAS 0.8.7 workspace and returns bounded public waveform diagnostics. Missing candidate "
    "files can be completed and retried within the request budget. This is not a final score. "
    "The public-validation budget limits this fixed action, not arbitrary Bash EVAS processes.\n"
)
_SHA = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_TEXT = {"type": "string", "minLength": 1, "maxLength": 256}


def _closed(properties):
    return {"type": "object", "properties": properties, "required": sorted(properties),
            "additionalProperties": False}


def _nullable(schema):
    return {"anyOf": [{"type": "null"}, schema]}


def _summary_schema():
    count = {"type": "integer", "minimum": 0, "maximum": waveform.MAX_BYTES}
    signal = _closed({
        "name": {"type": "string", "minLength": 1, "maxLength": waveform.MAX_IDENTIFIER_CHARS},
        "unit": {"type": "null"},
        **{key: count for key in ("finite_count", "nonfinite_count", "empty_count")},
        **{key: _nullable({"type": "number"}) for key in ("min", "max", "mean", "first", "last")},
    })
    unavailable = _closed({"status": {"enum": ["missing", "invalid", "too_large"]},
                           "source_sha256": {"type": "null"}, "policy_sha256": _SHA})
    summary = _closed({
        "schema_version": {"const": waveform.SCHEMA_VERSION}, "policy_sha256": _SHA,
        "relative_path": {"const": "tran.csv"},
        "status": {"enum": ["available", "truncated", "invalid", "too_large", "missing"]},
        "file_size_bytes": _nullable(count), "source_sha256": _nullable(_SHA),
        **{key: count for key in ("accepted_bytes", "scanned_rows", "total_data_rows_seen",
                                 "returned_signals", "omitted_signals", "omitted_columns")},
        "incomplete_scan": {"type": "boolean"}, "invalid_reason": _nullable(_TEXT),
        "signals": {"type": "array", "maxItems": waveform.MAX_RETURNED_SIGNALS, "items": signal},
    })
    return {"anyOf": [{"type": "null"}, unavailable, summary]}


def _receipt_schema():
    return _closed({
        "schema_version": {"const": "vaevas-public-waveform-receipt-v1"},
        "authority": {"const": "public_diagnostic"}, "task_correctness": {"const": "not_evaluated"},
        **{key: _TEXT for key in ("attempt_id", "task_id", "invocation_id", "image_id")},
        **{key: _SHA for key in ("candidate_tree_sha256", "profile_sha256", "profile_input_identity_sha256",
                                "command_sha256", "public_task_tree_sha256", "waveform_summary_sha256", "receipt_sha256")},
        "feedback_scope": {"enum": ["public_simulation_only", "reference_dut_only"]},
        "status": {"enum": ["succeeded", "failed", "timed_out"]},
        "returncode": {"type": "integer"}, "elapsed_s": {"type": "number", "minimum": 0},
        "waveform_summary": _summary_schema(), "usable_feedback": {"type": "boolean"},
        "cleanup_incidents": {"type": "array", "maxItems": 2, "items": {"anyOf": [
            _closed({"stage": {"enum": ["container_cleanup", "scratch_cleanup"]}, "error_type": _TEXT}),
            _closed({"stage": {"const": "container_cleanup"}, "returncode": {"type": "integer"}}),
        ]}},
    })


def waveform_tool_descriptor():
    return {
        "schema_version": "vaevas-tool-descriptor-v1", "tool_id": "vaevas/public-waveform-v1",
        "tool_name": TOOL_NAME, "tool_version": "1", "lifecycle": "active",
        "model_visibility": "model_visible", "allowed_conditions": ["Agentic"],
        "budget_class": "public_validation", "state_effect": "read_only", "candidate_effect": "read",
        "argument_schema": _closed({}),
        "observation_schema": _closed({
            "schema_version": {"const": "vaevas-public-waveform-observation-v1"},
            "authority": {"const": "public_diagnostic"}, "task_correctness": {"const": "not_evaluated"},
            "rejection_kind": {"enum": [None, "candidate_incomplete"]},
            "usable_feedback": {"type": "boolean"}, "evas_invocation_executed": {"type": "boolean"},
            "receipt": _nullable(_receipt_schema()),
        }),
        "evidence_policy": {"records_private_evidence": False, "may_enter_model_observation": True,
                            "may_enter_shared_memory": False, "requires_candidate_binding": True},
        "handler_id": "public_waveform.validate-v1",
    }


def waveform_provider_tool():
    return {"type": "function", "function": {
        "name": TOOL_NAME, "description": PROMPT.strip(),
        "parameters": waveform_tool_descriptor()["argument_schema"],
    }}


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _matches(value, schema):
    """Validate only this module's fixed, closed wire schema (not general JSON Schema)."""
    if "anyOf" in schema:
        return any(_matches(value, alternative) for alternative in schema["anyOf"])
    if "const" in schema:
        return type(value) is type(schema["const"]) and value == schema["const"]
    if "enum" in schema:
        return any(type(value) is type(option) and value == option for option in schema["enum"])
    kind = schema["type"]
    if kind == "object":
        return isinstance(value, dict) and set(value) == set(schema["properties"]) and all(
            _matches(value[key], child) for key, child in schema["properties"].items())
    if kind == "array":
        return isinstance(value, list) and len(value) <= schema["maxItems"] and all(_matches(item, schema["items"]) for item in value)
    if kind == "null":
        return value is None
    if kind == "boolean":
        return type(value) is bool
    if kind == "string":
        return isinstance(value, str) and schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 4096) and (
            "pattern" not in schema or re.fullmatch(schema["pattern"], value) is not None)
    return (type(value) is int if kind == "integer" else type(value) in (int, float)) and math.isfinite(value) and (
        schema.get("minimum", -math.inf) <= value <= schema.get("maximum", math.inf))


def validate_waveform_observation(observation, *, profile, attempt_id, task_id):
    """Reconstruct receipt joins from trusted events; hashes are not signatures."""
    profile_sha = public_validation_profile_sha256(profile)
    payload = observation["payload"]
    candidate = observation["candidate_tree_sha256"]
    if (observation["tool_name"] != TOOL_NAME or observation["validation_profile_sha256"] != profile_sha
            or observation["payload_sha256"] != _sha(payload) or not _matches(candidate, _SHA)
            or not _matches(payload, waveform_tool_descriptor()["observation_schema"])):
        raise ValueError("public waveform observation contract mismatch")
    receipt = payload["receipt"]
    if payload["rejection_kind"] == "candidate_incomplete":
        if (receipt is not None or payload["evas_invocation_executed"] or payload["usable_feedback"]
                or observation["status"] != "candidate_incomplete"):
            raise ValueError("public waveform incomplete observation contradicts execution")
        return
    if (receipt is None or not payload["evas_invocation_executed"]
            or payload["usable_feedback"] != receipt["usable_feedback"]
            or observation["status"] != (receipt["status"] if receipt["usable_feedback"] else "unusable")):
        raise ValueError("public waveform receipt/observation mismatch")
    expected_input = profile_input_identity_sha256(profile_sha256=profile_sha, input_kind="candidate_tree",
        input_sha256=candidate, attempt_id=attempt_id, task_id=task_id)
    expected_status = "succeeded" if receipt["returncode"] == 0 else "timed_out" if receipt["returncode"] in (-1, 124) else "failed"
    if (receipt["profile_sha256"] != profile_sha or receipt["candidate_tree_sha256"] != candidate
            or receipt["attempt_id"] != attempt_id or receipt["task_id"] != task_id
            or receipt["profile_input_identity_sha256"] != expected_input
            or receipt["status"] != expected_status
            or receipt["usable_feedback"] != (not receipt["cleanup_incidents"] and expected_status != "timed_out")
            or receipt["receipt_sha256"] != _sha({key: value for key, value in receipt.items() if key != "receipt_sha256"})
            or receipt["waveform_summary_sha256"] != _sha(receipt["waveform_summary"])
            or ((not receipt["usable_feedback"] or expected_status != "succeeded") and receipt["waveform_summary"] is not None)):
        raise ValueError("public waveform receipt identity mismatch")
    if str(uuid.UUID(receipt["invocation_id"])) != receipt["invocation_id"]:
        raise ValueError("public waveform invocation identity invalid")
    if receipt["waveform_summary"] is not None and receipt["waveform_summary"]["policy_sha256"] != waveform.waveform_policy_sha256():
        raise ValueError("public waveform summary policy mismatch")


class WaveformFeedbackError(RuntimeError):
    def __init__(self, primary, incidents, *, executor_entered, receipt):
        super().__init__(str(primary))
        self.primary_type = type(primary).__name__
        self.cleanup_incidents = deepcopy(incidents)
        self.execution_count_status = ("confirmed_one_receipt" if receipt else
            "unknown_after_executor_entered" if executor_entered else "confirmed_zero_preflight")
        self.execution_receipt = deepcopy(receipt)


class PublicWaveformTool:
    def __init__(self, *, executor, quiesce, resume):
        self.executor, self.quiesce, self.resume = executor, quiesce, resume
        self.descriptor = waveform_tool_descriptor()

    def step(self, action, capability):
        if (action.tool_name != TOOL_NAME or capability.tool_name != TOOL_NAME
                or capability.descriptor_sha256 != tool_descriptor_sha256(self.descriptor) or action.arguments):
            return ToolExecutionRejection(code="invalid_tool_arguments", failure_category="tool_contract_rejected",
                primary_outcome="protocol_failure", message="fixed public waveform action rejected",
                candidate_tree_sha256=action.candidate_tree_sha256)
        primary, incidents, receipt = None, [], None
        executor_entered = False
        try:
            self.quiesce()
            candidate, missing = self.executor.inspect_candidate()
            if candidate != action.candidate_tree_sha256:
                raise ValueError("public waveform candidate drift before snapshot")
            if not missing:
                executor_entered = True
                receipt = self.executor.validate(candidate_tree_sha256=candidate)
        except Exception as error:
            primary = error
            incidents.extend(getattr(error, "cleanup_incidents", []))
        finally:
            try:
                self.resume()
            except Exception as error:
                incidents.append({"stage": "generation_resume", "error_type": type(error).__name__})
                primary = primary or error
        if primary is not None:
            raise WaveformFeedbackError(primary, incidents, executor_entered=executor_entered, receipt=receipt) from primary
        payload = {
            "schema_version": "vaevas-public-waveform-observation-v1", "authority": "public_diagnostic",
            "task_correctness": "not_evaluated", "rejection_kind": "candidate_incomplete" if missing else None,
            "usable_feedback": receipt["usable_feedback"] if receipt else False,
            "evas_invocation_executed": receipt is not None, "receipt": receipt,
        }
        observation = Observation(action.action_id + "/public-waveform", TOOL_NAME,
            "candidate_incomplete" if missing else receipt["status"] if receipt["usable_feedback"] else "unusable",
            payload, candidate_tree_sha256=candidate, validation_profile_sha256=self.executor.profile_sha256)
        validate_waveform_observation(observation.to_document(), profile=self.executor.profile,
            attempt_id=self.executor.context.attempt_id, task_id=self.executor.context.task_id)
        return EnvironmentStep(observation=observation, done=False)
