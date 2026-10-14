import asyncio
import json
from types import SimpleNamespace

from app.rca.models import RCAAnalysis, Finding, Confidence
from app.rca.evidence_store import EvidenceStore
from app.rca.semantic_grounding import (
    GroundingClassification,
    FindingGroundingEvaluation,
    SemanticGroundingAnalysis,
    SemanticEvaluationValidationError,
    validate_semantic_evaluation,
    SemanticGroundingEvaluator
)


def make_analysis():

    return RCAAnalysis(
        title="Checkout timeout",
        services_investigated=["checkout", "email"],
        observations=[],
        confirmed_findings=[
            Finding(
                finding_id="F-0001",
                statement=(
                    "Checkout experienced a timeout "
                    "calling email."
                ),
                evidence_ids=["EV-0001"],
                confidence=Confidence.HIGH,
            )
        ],
        hypotheses=[],
        limitations=[],
        recommended_next_steps=[],
    )


def make_evaluation(
    finding_id="F-0001",
    evidence_ids=None,
):

    if evidence_ids is None:
        evidence_ids = ["EV-0001"]

    return SemanticGroundingAnalysis(
        evaluations=[
            FindingGroundingEvaluation(
                finding_id=finding_id,
                classification=GroundingClassification.SUPPORTED,
                explanation="The log directly records the timeout.",
                supporting_evidence_ids=evidence_ids,
                unsupported_claims=[],
            )
        ]
    )


def test_valid_evaluation():

    validate_semantic_evaluation(
        make_analysis(),
        make_evaluation(),
    )

    print("PASS: Valid evaluation")


def test_unknown_finding():

    try:
        validate_semantic_evaluation(
            make_analysis(),
            make_evaluation(finding_id="F-9999"),
        )
        assert False, "Expected validation error"

    except SemanticEvaluationValidationError:
        print("PASS: Unknown finding rejected")


def test_unknown_evidence():

    try:
        validate_semantic_evaluation(
            make_analysis(),
            make_evaluation(evidence_ids=["EV-9999"]),
        )
        assert False, "Expected validation error"

    except SemanticEvaluationValidationError:
        print("PASS: Unknown evidence rejected")


def test_missing_finding():

    evaluation = SemanticGroundingAnalysis(
        evaluations=[]
    )

    try:
        validate_semantic_evaluation(
            make_analysis(),
            evaluation,
        )
        assert False, "Expected validation error"

    except SemanticEvaluationValidationError:
        print("PASS: Missing finding rejected")


def test_duplicate_finding():

    item = make_evaluation().evaluations[0]

    evaluation = SemanticGroundingAnalysis(
        evaluations=[item, item]
    )

    try:
        validate_semantic_evaluation(
            make_analysis(),
            evaluation,
        )
        assert False, "Expected validation error"

    except SemanticEvaluationValidationError:
        print("PASS: Duplicate finding rejected")


class FakeProvider:

    def __init__(self):
        self.received_messages = None

    def generate_structured(
        self,
        messages,
        response_model,
        max_output_tokens=4096,
    ):
        self.received_messages = messages

        evaluation = make_evaluation()

        response = SimpleNamespace(
            input_tokens=100,
            output_tokens=40,
            reasoning_tokens=0,
        )

        return evaluation, response


async def test_evaluator_with_mock():

    store = EvidenceStore()

    evidence = store.add_log(
        log={
            "timestamp": "2026-10-13T14:01:18Z",
            "service": "checkout",
            "severity": "WARN",
            "message": (
                "Checkout failed to call email: "
                "context deadline exceeded"
            ),
        },
        tool_name="search_service_logs",
        tool_arguments={
            "service_name": "checkout",
        },
    )

    assert evidence.evidence_id == "EV-0001"

    provider = FakeProvider()

    evaluator = SemanticGroundingEvaluator(provider)

    evaluation, response = await evaluator.evaluate(
        analysis=make_analysis(),
        evidence_store=store,
    )

    assert len(evaluation.evaluations) == 1
    assert response.input_tokens == 100

    payload = json.loads(
        provider.received_messages[1].content
    )

    assert payload["findings"][0]["finding_id"] == "F-0001"

    assert (
        payload["findings"][0]["cited_evidence"][0]["evidence_id"]
        == "EV-0001"
    )

    print("PASS: Mock LLM evaluation")


def run_mock_test():
    asyncio.run(test_evaluator_with_mock())   

def main():

    test_valid_evaluation()
    test_unknown_finding()
    test_unknown_evidence()
    test_missing_finding()
    test_duplicate_finding()
    run_mock_test()

    print("\nAll semantic grounding validation tests passed.")


if __name__ == "__main__":
    main()