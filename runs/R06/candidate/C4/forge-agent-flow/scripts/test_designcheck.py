"""Portable structural tests for the designcheck intake gates."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import designcheck
import flowctl


def complete_contract():
    request = "Summarize this ticket and identify its owner."
    dimensions = {
        "scope": "Summarize the ticket and identify the owner.",
        "inputs": "One ticket text value.",
        "outputs": "A summary and an owner field.",
        "quality": "Preserve source facts and signal a missing owner.",
        "tools_and_authority": "No tools or external actions.",
        "failures": "Return a missing-owner state when evidence is absent.",
        "state_and_handoffs": "No persistent state or handoff.",
        "budget_and_stop": "One bounded processing step.",
        "model_and_topology": "One model call in one node.",
    }
    return {
        "goal": "Produce a grounded ticket summary and owner field.",
        "requirements": [
            {
                "id": "ticket_summary",
                "text": "Return a concise summary of the ticket.",
                "origin": "explicit",
                "basis": "Summarize this ticket",
                "criteria": ["output_shape"],
            },
            {
                "id": "owner_field",
                "text": "Identify the owner from the ticket, or mark it missing.",
                "origin": "derived",
                "basis": "A usable owner field is needed to make the requested summary actionable.",
                "criteria": ["owner_evidence"],
            },
        ],
        "decisions": {
            dimension: {
                "choice": choice,
                "reason": f"This is the smallest design that satisfies {dimension}.",
                "origin": "derived",
            }
            for dimension, choice in dimensions.items()
        },
        "blocking_questions": [],
        "request_echo": request,
    }, request


def complete_plan():
    return {
        "schema": "forge-eval/1",
        "id": "ticket_summary_eval",
        "criteria": [
            {
                "id": "output_shape",
                "kind": "machine",
                "required": True,
                "assertion": "The output contains a concise summary and owner field.",
            },
            {
                "id": "owner_evidence",
                "kind": "human",
                "required": True,
                "assertion": "The owner comes from the ticket or is marked missing.",
            },
        ],
        "cases": [
            {
                "id": "owner_present",
                "inputs": {"ticket": "Owner: Mina. The deployment is delayed."},
                "expected": {"artifacts": {"result": {"summary": "Deployment delayed", "owner": "Mina"}}},
                "expected_status": "completed",
                "criteria": ["output_shape", "owner_evidence"],
                "required": True,
            },
            {
                "id": "owner_missing",
                "inputs": {"ticket": "The deployment is delayed."},
                "expected": {"artifacts": {"result": {"summary": "Deployment delayed", "owner": None}}},
                "expected_status": "completed",
                "criteria": ["output_shape", "owner_evidence"],
                "required": True,
            },
        ],
        "baseline": "A single model call with no tools.",
        "limitations": ["Fixture expectations do not establish runtime quality."],
    }


def complete_architecture():
    return {
        "mode": "lite",
        "necessity": {
            "choice": "single_agent",
            "rationale": "One node can complete the short text transformation.",
            "baseline": "One text-only model call.",
        },
        "decisions": [
            {
                "id": "D02",
                "status": "chosen",
                "choice": "One agent node.",
                "rationale": "The task has no independent work to coordinate.",
                "rejected": [],
                "rollback": "Revisit only if repeated cases show a verification need.",
            }
        ],
        "lifecycle": {
            "infra": "No external capabilities or persistent storage.",
            "post": "Run one bounded extraction step.",
            "after": "Review output against the frozen cases.",
        },
        "knowledge": [],
        "source_refs": [],
        "coverage": [
            {"requirement_id": "ticket_summary", "node_ids": ["summarize"], "criteria": ["output_shape"]},
            {"requirement_id": "owner_field", "node_ids": ["summarize"], "criteria": ["owner_evidence"]},
        ],
        "stress_cases": [
            {"case_id": "owner_present", "risk": "Owner could be inferred from unrelated text.", "handling": "Use only ticket evidence."},
            {"case_id": "owner_missing", "risk": "A missing owner could be guessed.", "handling": "Return null when absent."},
        ],
        "review": {
            "mode": "self_review",
            "summary": "Checked each frozen requirement and its case/node references.",
            "unresolved": [],
        },
        "design_note": "Extra architecture fields remain permitted.",
    }


def complete_flow():
    return {
        "schema_version": "1.0",
        "id": "ticket_summary_flow",
        "goal": "Summarize a ticket and identify its owner.",
        "assumptions": [],
        "inputs": {"ticket": {"type": "string", "description": "Untrusted ticket text."}},
        "artifacts": {"result": {"type": "object", "description": "Ticket summary and owner."}},
        "outputs": ["result"],
        "capabilities": {},
        "budgets": {"max_steps": 1},
        "entry": "summarize",
        "nodes": [
            {
                "id": "summarize",
                "kind": "agent",
                "reads": ["ticket"],
                "writes": ["result"],
                "tools": [],
                "prompt": "Summarize the ticket and identify an evidenced owner.",
                "acceptance": ["Owner is never guessed."],
                "max_visits": 1,
                "routes": {"ok": "$done", "error": "$failed", "blocked": "$blocked"},
                "emits": {"ok": ["result"], "error": [], "blocked": []},
            }
        ],
    }


class DesignCheckTests(unittest.TestCase):
    def setUp(self):
        self.contract, self.request = complete_contract()
        self.plan = complete_plan()
        self.architecture = complete_architecture()

    def test_complete_design_passes_and_inputs_are_unchanged(self):
        before = copy.deepcopy((self.contract, self.plan, self.architecture))
        self.assertIs(designcheck.require_contract(self.contract, self.request), self.contract)
        self.assertIs(designcheck.require_plan(self.contract, self.plan), self.plan)
        self.assertIs(
            designcheck.require_architecture(self.contract, self.plan, self.architecture, complete_flow()),
            self.architecture,
        )
        self.assertEqual((self.contract, self.plan, self.architecture), before)

    def test_each_of_the_nine_decision_dimensions_is_required(self):
        for dimension in designcheck.DECISION_DIMENSIONS:
            with self.subTest(dimension=dimension):
                contract = copy.deepcopy(self.contract)
                del contract["decisions"][dimension]
                with self.assertRaisesRegex(flowctl.FlowError, dimension):
                    designcheck.require_contract(contract, self.request)

    def test_explicit_decision_requires_basis_and_verbatim_request_evidence(self):
        contract = copy.deepcopy(self.contract)
        decision = contract["decisions"]["scope"]
        decision["origin"] = "explicit"
        with self.assertRaisesRegex(flowctl.FlowError, "explicit decisions require nonempty evidence"):
            designcheck.require_contract(contract, self.request)

        decision["basis"] = "Summarize this ticket"
        designcheck.require_contract(contract, self.request)
        decision["basis"] = "The request asked for a summary"
        with self.assertRaisesRegex(flowctl.FlowError, "exact substring"):
            designcheck.require_contract(contract, self.request)

    def test_architecture_requires_package_design_structure(self):
        architecture = copy.deepcopy(self.architecture)
        del architecture["mode"]
        with self.assertRaisesRegex(flowctl.FlowError, "design.mode"):
            designcheck.require_architecture(self.contract, self.plan, architecture)

        architecture = copy.deepcopy(self.architecture)
        del architecture["necessity"]
        with self.assertRaisesRegex(flowctl.FlowError, "design.necessity"):
            designcheck.require_architecture(self.contract, self.plan, architecture)

    def test_full_architecture_requires_every_design_dimension(self):
        architecture = copy.deepcopy(self.architecture)
        architecture["mode"] = "full"
        with self.assertRaisesRegex(flowctl.FlowError, "requires all decisions D01-D14"):
            designcheck.require_architecture(self.contract, self.plan, architecture)

    def test_explicit_basis_must_be_a_verbatim_request_substring(self):
        contract = copy.deepcopy(self.contract)
        contract["requirements"][0]["basis"] = "The user asked for a summary"
        with self.assertRaisesRegex(flowctl.FlowError, "exact substring"):
            designcheck.require_contract(contract, self.request)

    def test_successful_intake_cannot_have_blocking_questions(self):
        contract = copy.deepcopy(self.contract)
        contract["blocking_questions"] = ["Which system should receive the summary?"]
        with self.assertRaisesRegex(flowctl.FlowError, "blocked branch"):
            designcheck.require_contract(contract, self.request)

    def test_requirement_criterion_must_exist_and_be_required(self):
        contract = copy.deepcopy(self.contract)
        contract["requirements"][0]["criteria"] = ["unknown_criterion"]
        with self.assertRaisesRegex(flowctl.FlowError, "missing from plan.criteria"):
            designcheck.require_plan(contract, self.plan)

        plan = copy.deepcopy(self.plan)
        plan["criteria"][0]["required"] = False
        with self.assertRaisesRegex(flowctl.FlowError, "required=true"):
            designcheck.require_plan(self.contract, plan)

    def test_plan_needs_two_required_probe_cases(self):
        plan = copy.deepcopy(self.plan)
        plan["cases"][1]["required"] = False
        with self.assertRaisesRegex(flowctl.FlowError, "at least two required cases"):
            designcheck.require_plan(self.contract, plan)

    def test_architecture_rejects_missing_flow_node_and_unknown_plan_case(self):
        architecture = copy.deepcopy(self.architecture)
        architecture["coverage"][0]["node_ids"] = ["missing_node"]
        with self.assertRaisesRegex(flowctl.FlowError, "does not exist in flow"):
            designcheck.require_architecture(self.contract, self.plan, architecture, complete_flow())

        architecture = copy.deepcopy(self.architecture)
        architecture["stress_cases"][1]["case_id"] = "not_in_plan"
        with self.assertRaisesRegex(flowctl.FlowError, "required case in the frozen plan"):
            designcheck.require_architecture(self.contract, self.plan, architecture)

    def test_architecture_rejects_unresolved_review_findings(self):
        architecture = copy.deepcopy(self.architecture)
        architecture["review"]["unresolved"] = ["The owner evidence rule is unclear."]
        with self.assertRaisesRegex(flowctl.FlowError, "must be empty"):
            designcheck.require_architecture(self.contract, self.plan, architecture)

    def test_malicious_field_types_raise_flowerror_instead_of_typeerror(self):
        malformed_contracts = [
            [],
            {**self.contract, "requirements": {"id": "not-an-array"}},
            {**self.contract, "decisions": {"scope": ["not", "an", "object"]}},
            {**self.contract, "blocking_questions": {"question": "not-an-array"}},
        ]
        for contract in malformed_contracts:
            with self.subTest(contract_type=type(contract).__name__):
                with self.assertRaises(flowctl.FlowError):
                    designcheck.require_contract(contract, self.request)

        contract = copy.deepcopy(self.contract)
        contract["requirements"][0]["criteria"] = {"bad": "type"}
        with self.assertRaises(flowctl.FlowError):
            designcheck.require_plan(contract, self.plan)

        malformed_architectures = []
        architecture = copy.deepcopy(self.architecture)
        architecture["coverage"][0]["node_ids"] = None
        malformed_architectures.append(architecture)
        architecture = copy.deepcopy(self.architecture)
        architecture["stress_cases"][0] = "not-an-object"
        malformed_architectures.append(architecture)
        architecture = copy.deepcopy(self.architecture)
        architecture["review"] = None
        malformed_architectures.append(architecture)
        architecture = copy.deepcopy(self.architecture)
        architecture["coverage"][0]["requirement_id"] = ["not", "an", "id"]
        malformed_architectures.append(architecture)
        for architecture in malformed_architectures:
            with self.subTest(field_type=type(architecture.get("review")).__name__):
                with self.assertRaises(flowctl.FlowError):
                    designcheck.require_architecture(self.contract, self.plan, architecture)


if __name__ == "__main__":
    unittest.main()
