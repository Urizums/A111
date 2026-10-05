#!/usr/bin/env python3
"""Create explicitly incomplete Forge response and evaluation-result drafts."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile

import flowctl as flow
import nestedcheck
import packagectl


SHA256 = re.compile(r"^[0-9a-f]{64}$")
INVOCATION = re.compile(r"^[0-9a-f]{32}$")
FLOW_DISPATCH_KEYS = {
    "status", "node", "kind", "invocation_id", "prompt", "inputs",
    "capabilities", "acceptance", "outcomes", "artifact_types",
}
PACKAGE_V1_DISPATCH_KEYS = FLOW_DISPATCH_KEYS | {
    "execution_settings", "host_requirements",
}
PACKAGE_V2_DISPATCH_KEYS = PACKAGE_V1_DISPATCH_KEYS | {
    "plan_hash", "input_hash", "execution_settings", "host_requirements",
}
FACTORY_DISPATCH_KEYS = FLOW_DISPATCH_KEYS | {"materials_assessment"}
FACTORY_PLAN_DISPATCH_KEYS = FACTORY_DISPATCH_KEYS | {"plan_hash"}
DISPATCH_SHAPES = (
    FLOW_DISPATCH_KEYS,
    PACKAGE_V1_DISPATCH_KEYS,
    PACKAGE_V2_DISPATCH_KEYS,
    FACTORY_DISPATCH_KEYS,
    FACTORY_PLAN_DISPATCH_KEYS,
)
MATERIAL_OPERATIONS = {"inspect", "design", "modify"}


class TemplateError(ValueError):
    """An input is not a valid source for a draft."""


def _reject_constant(value):
    raise TemplateError(f"Non-finite JSON number: {value}")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TemplateError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path):
    """Read strict, finite JSON data without interpreting it as code."""
    try:
        value = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        flow.canonical(value)  # Reject exponent overflow and non-JSON values.
        return value
    except TemplateError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError,
            OverflowError, RecursionError) as error:
        raise TemplateError(f"Cannot read strict JSON from {path}: {error}") from error


def _nonempty_text(value):
    return type(value) is str and bool(value.strip())


def _validate_dispatch(dispatch):
    if type(dispatch) is not dict:
        raise TemplateError("Dispatch must be a JSON object")
    keys = set(dispatch)
    if not any(keys == expected for expected in DISPATCH_SHAPES):
        missing = sorted((FLOW_DISPATCH_KEYS - keys))
        known = set().union(*DISPATCH_SHAPES)
        extra = sorted((keys - known))
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        if not details:
            details.append("dispatch extension fields do not match a supported protocol")
        raise TemplateError("Dispatch has the wrong structure: " + "; ".join(details))
    if dispatch.get("status") != "ready":
        raise TemplateError("Dispatch must have status 'ready'")
    if not _nonempty_text(dispatch.get("node")) or flow.IDENT.fullmatch(dispatch["node"]) is None:
        raise TemplateError("Dispatch node must be a valid flow node ID")
    if not _nonempty_text(dispatch.get("kind")):
        raise TemplateError("Dispatch kind must be nonempty text")
    if type(dispatch.get("invocation_id")) is not str or INVOCATION.fullmatch(dispatch["invocation_id"]) is None:
        raise TemplateError("Dispatch invocation_id must be a 32-character lowercase hex ID")
    if not _nonempty_text(dispatch.get("prompt")):
        raise TemplateError("Dispatch prompt must be nonempty text")
    if type(dispatch.get("inputs")) is not dict:
        raise TemplateError("Dispatch inputs must be an object")
    if type(dispatch.get("capabilities")) is not dict:
        raise TemplateError("Dispatch capabilities must be an object")
    for name, capability in dispatch["capabilities"].items():
        capability_keys = {"binding", "effect", "available", "authorization", "evidence"}
        if (not _nonempty_text(name) or type(capability) is not dict or
                set(capability) != capability_keys):
            raise TemplateError("Dispatch capabilities have the wrong structure")
        if (not _nonempty_text(capability["binding"]) or
                capability["effect"] not in ("read", "local_write", "external_write") or
                type(capability["available"]) is not bool or
                capability["authorization"] not in ("granted", "required", "not_applicable") or
                not _nonempty_text(capability["evidence"])):
            raise TemplateError(f"Dispatch capability {name!r} has invalid values")
        if capability["effect"] == "external_write" and capability["authorization"] == "not_applicable":
            raise TemplateError(f"Dispatch capability {name!r} has an invalid external-write authorization")
    if not flow.strings(dispatch.get("acceptance")):
        raise TemplateError("Dispatch acceptance must be a string list")

    outcomes = dispatch.get("outcomes")
    artifact_types = dispatch.get("artifact_types")
    if type(outcomes) is not dict or not outcomes:
        raise TemplateError("Dispatch outcomes must be a nonempty object")
    if type(artifact_types) is not dict:
        raise TemplateError("Dispatch artifact_types must be an object")
    for outcome, artifact_names in outcomes.items():
        if not _nonempty_text(outcome) or not flow.strings(artifact_names):
            raise TemplateError("Each dispatch outcome must map to a string list of artifact names")
        if len(artifact_names) != len(set(artifact_names)):
            raise TemplateError(f"Outcome {outcome!r} contains duplicate artifact names")
        for name in artifact_names:
            if name not in artifact_types:
                raise TemplateError(f"Outcome {outcome!r} has no artifact_types descriptor for {name!r}")

    for name, descriptor in artifact_types.items():
        if not _nonempty_text(name) or type(descriptor) is not dict:
            raise TemplateError("artifact_types must map artifact names to descriptor objects")
        if set(descriptor) not in ({"type", "description"}, {"type", "description", "schema"}):
            raise TemplateError(
                f"Artifact type descriptor {name!r} needs type and description, with optional schema only"
            )
        if not _nonempty_text(descriptor.get("type")) or not _nonempty_text(descriptor.get("description")):
            raise TemplateError(f"Artifact type descriptor {name!r} needs type and description")
        if descriptor["type"] not in flow.TYPES:
            raise TemplateError(f"Artifact type descriptor {name!r} has an unsupported type")
        if "schema" in descriptor:
            schema_errors = nestedcheck.schema_errors(
                descriptor["schema"], descriptor["type"], f"artifact_types.{name}.schema"
            )
            if schema_errors:
                raise TemplateError("Invalid artifact schema: " + "; ".join(schema_errors))
        try:
            flow.canonical(descriptor)
        except (TypeError, ValueError, OverflowError, RecursionError) as error:
            raise TemplateError(f"Artifact type descriptor {name!r} is not finite JSON data") from error

    if keys in (PACKAGE_V1_DISPATCH_KEYS, PACKAGE_V2_DISPATCH_KEYS):
        settings = dispatch["execution_settings"]
        if (type(settings) is not dict or set(settings) != {"model", "write_scope"} or
                not _nonempty_text(settings.get("model")) or not flow.strings(settings.get("write_scope"))):
            raise TemplateError("Package dispatch execution_settings has the wrong structure")
        requirements = dispatch["host_requirements"]
        if type(requirements) is not list:
            raise TemplateError("Package dispatch host_requirements must be a list")
        for requirement in requirements:
            required_keys = {"id", "scope", "kind", "value", "status", "binding", "evidence"}
            if type(requirement) is not dict or set(requirement) != required_keys:
                raise TemplateError("Package dispatch host requirement has the wrong structure")
            if (not _nonempty_text(requirement["id"]) or
                    requirement["scope"] not in ("flow", dispatch["node"]) or
                    requirement["kind"] not in packagectl.KINDS or
                    requirement["status"] not in ("verified", "unverified", "unsupported") or
                    requirement["value"] in (None, "", [], {}) or
                    type(requirement["binding"]) is not str or not flow.strings(requirement["evidence"])):
                raise TemplateError("Package dispatch host requirement has invalid values")
            if requirement["status"] == "verified" and (
                    not _nonempty_text(requirement["binding"]) or not requirement["evidence"]):
                raise TemplateError("Verified package dispatch requirements need binding and evidence")
        if keys == PACKAGE_V2_DISPATCH_KEYS:
            for field in ("plan_hash", "input_hash"):
                if type(dispatch[field]) is not str or SHA256.fullmatch(dispatch[field]) is None:
                    raise TemplateError(f"Package dispatch {field} must be a SHA-256 hex digest")

    if keys in (FACTORY_DISPATCH_KEYS, FACTORY_PLAN_DISPATCH_KEYS):
        _validate_factory_materials(dispatch["materials_assessment"])

    if keys == FACTORY_PLAN_DISPATCH_KEYS:
        if type(dispatch["plan_hash"]) is not str or SHA256.fullmatch(dispatch["plan_hash"]) is None:
            raise TemplateError("Factory dispatch plan_hash must be a SHA-256 hex digest")

    try:
        flow.canonical(dispatch)
    except (TypeError, ValueError, OverflowError, RecursionError) as error:
        raise TemplateError(f"Dispatch must be finite JSON data: {error}") from error


def _validate_factory_materials(assessment):
    expected = {
        "configured", "operation", "decision", "valid", "status", "manifest_sha256",
        "claim_scope", "allowed_operations", "blockers", "claim_limit", "material_sha256",
        "gate_blockers",
    }
    if type(assessment) is not dict or set(assessment) != expected:
        raise TemplateError("Factory materials_assessment has the wrong structure")
    if (type(assessment["configured"]) is not bool or
            assessment["decision"] not in ("not_configured", "allow", "blocked") or
            type(assessment["valid"]) is not bool or
            assessment["status"] not in ("not_configured", "pass", "blocked", "invalid") or
            not _nonempty_text(assessment["claim_scope"]) or
            not _nonempty_text(assessment["claim_limit"]) or
            type(assessment["material_sha256"]) is not dict):
        raise TemplateError("Factory materials_assessment has invalid values")
    for field in ("allowed_operations", "blockers", "gate_blockers"):
        value = assessment[field]
        if type(value) is not list or any(not _nonempty_text(item) for item in value):
            raise TemplateError(f"Factory materials_assessment {field} must be a text list")
    if any(operation not in MATERIAL_OPERATIONS for operation in assessment["allowed_operations"]):
        raise TemplateError("Factory materials_assessment has an unknown allowed operation")
    if assessment["configured"] is False:
        if (assessment["decision"] != "not_configured" or assessment["operation"] is not None or
                assessment["status"] != "not_configured" or assessment["manifest_sha256"] is not None or
                assessment["allowed_operations"] or assessment["material_sha256"] != {}):
            raise TemplateError("Unconfigured factory materials gate has contradictory fields")
        return
    operation = assessment["operation"]
    if operation not in MATERIAL_OPERATIONS:
        raise TemplateError("Configured factory materials gate needs a known operation")
    if (assessment["decision"] != "allow" or assessment["valid"] is not True or
            assessment["status"] not in ("pass", "blocked") or
            operation not in assessment["allowed_operations"] or assessment["gate_blockers"]):
        raise TemplateError(f"Configured materials gate does not allow operation: {operation}")
    if type(assessment["manifest_sha256"]) is not str or SHA256.fullmatch(assessment["manifest_sha256"]) is None:
        raise TemplateError("Configured factory materials gate needs a manifest SHA-256")
    material_hashes = assessment["material_sha256"]
    if set(material_hashes) != {"source", "binary", "provenance"} or any(
            value is not None and (type(value) is not str or SHA256.fullmatch(value) is None)
            for value in material_hashes.values()):
        raise TemplateError("Configured factory materials gate has invalid material hashes")


def _empty_placeholder(descriptor):
    """Return a visibly empty value of the descriptor's top-level type.

    Nested schemas are intentionally not interpreted: a template has no evidence
    and is not an execution result. Replace these values with actual host output.
    """
    typename = descriptor["type"]
    if typename == "object":
        return {}
    if typename == "array":
        return []
    if typename == "string":
        return ""
    if typename in ("integer", "number", "boolean"):
        return None
    raise TemplateError(f"Unsupported artifact type for empty placeholder: {typename}")


def make_response_draft(dispatch, outcome):
    _validate_dispatch(dispatch)
    if type(outcome) is not str or outcome not in dispatch["outcomes"]:
        choices = ", ".join(dispatch["outcomes"])
        raise TemplateError(f"Unknown outcome {outcome!r}; choose one of: {choices}")
    artifacts = {
        name: _empty_placeholder(dispatch["artifact_types"][name])
        for name in dispatch["outcomes"][outcome]
    }
    return {
        "invocation_id": dispatch["invocation_id"],
        "outcome": outcome,
        "artifacts": artifacts,
        "evidence": [],
    }


def make_results_draft(package):
    if type(package) is not dict or package.get("schema") != packagectl.SCHEMA_V2:
        raise TemplateError("Results drafts require schema 'forge-package/2'")
    validation = packagectl.validate(package)
    if not validation.get("valid"):
        details = "; ".join(validation.get("errors", [])) or "package validation failed"
        raise TemplateError(f"Package is not valid: {details}")

    acceptance = package.get("acceptance")
    if type(acceptance) is not dict or type(acceptance.get("plan")) is not dict:
        raise TemplateError("Validated forge-package/2 must contain its frozen acceptance plan")
    plan = acceptance["plan"]
    criteria = {criterion["id"]: criterion for criterion in plan["criteria"]}
    rows = []
    for case in plan["cases"]:
        rows.append({
            "case_id": case["id"],
            "run": None,
            "checks": [
                {
                    "id": criterion_id,
                    "kind": criteria[criterion_id]["kind"],
                    "status": "not_run",
                    "evidence": [],
                }
                for criterion_id in case["criteria"]
            ],
        })

    draft = {
        "package_hash": flow.digest(package),
        "plan_hash": acceptance["plan_hash"],
        "cases": rows,
    }
    assessment = packagectl.assess(package, draft)
    if assessment.get("verdict") != "pending":
        raise TemplateError(
            "Generated results draft did not assess as pending; refusing to write it"
        )
    return draft


def _write_exclusive_json(path, value, input_paths=()):
    destination = Path(path)
    resolved_destination = destination.resolve()
    for source in input_paths:
        if resolved_destination == Path(source).resolve():
            raise TemplateError("Output path must not be the same as an input path")
    if destination.exists() or destination.is_symlink():
        raise TemplateError(f"Output already exists: {destination}")

    body = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".forge-template-", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        # A hard link publishes the completed file atomically and never replaces
        # another file, including one created after the preflight existence check.
        os.link(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    response = commands.add_parser("response", help="write a response-envelope draft")
    response.add_argument("--dispatch", required=True)
    response.add_argument("--outcome", required=True)
    response.add_argument("--out", required=True)

    results = commands.add_parser("results", help="write a forge-package/2 results draft")
    results.add_argument("--package", required=True)
    results.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "response":
            dispatch = load_json(args.dispatch)
            draft = make_response_draft(dispatch, args.outcome)
            _write_exclusive_json(args.out, draft, input_paths=(args.dispatch,))
        else:
            package = load_json(args.package)
            draft = make_results_draft(package)
            _write_exclusive_json(args.out, draft, input_paths=(args.package,))
        print(json.dumps({"status": "draft_created", "out": str(Path(args.out).resolve())}, ensure_ascii=False))
        return 0
    except (TemplateError, flow.FlowError, OSError, ValueError, TypeError, KeyError,
            IndexError, AttributeError, OverflowError, RecursionError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
