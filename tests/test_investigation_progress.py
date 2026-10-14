from app.agents.investigation_progress import (
    InvestigationProgress,
    InvestigationProgressEvaluator,
    StopReason,
)


def progress(
    iteration,
    total,
    new,
    services=None,
    warning=False,
):
    return InvestigationProgress(
        iteration=iteration,
        total_evidence=total,
        new_evidence=new,
        services_with_evidence=frozenset(
            services or []
        ),
        has_warning_or_error=warning,
    )


def test_does_not_stop_too_early():
    evaluator = InvestigationProgressEvaluator()

    decision = evaluator.evaluate(
        progress(
            iteration=1,
            total=20,
            new=20,
            services={"checkout"},
        )
    )

    assert decision.should_stop is False

    print("PASS: Does not stop too early")


def test_requires_warning_or_error():
    evaluator = InvestigationProgressEvaluator(
        min_iterations=2,
        max_stale_iterations=2,
    )

    evaluator.evaluate(
        progress(
            1, 10, 10,
            {"checkout", "email"},
            False,
        )
    )

    decision = evaluator.evaluate(
        progress(
            2, 10, 0,
            {"checkout", "email"},
            False,
        )
    )

    assert decision.should_stop is False

    print("PASS: Requires warning or error evidence")


def test_requires_service_coverage():
    evaluator = InvestigationProgressEvaluator(
        min_iterations=2,
        max_stale_iterations=2,
    )

    evaluator.evaluate(
        progress(
            1, 10, 10,
            {"checkout"},
            True,
        )
    )

    decision = evaluator.evaluate(
        progress(
            2, 10, 0,
            {"checkout"},
            True,
        )
    )

    assert decision.should_stop is False

    print("PASS: Requires service coverage")


def test_stops_after_saturation():
    evaluator = InvestigationProgressEvaluator(
        min_iterations=3,
        max_stale_iterations=2,
    )

    evaluator.evaluate(
        progress(
            1, 10, 10,
            {"checkout", "email"},
            True,
        )
    )

    evaluator.evaluate(
        progress(
            2, 10, 0,
            {"checkout", "email"},
            True,
        )
    )

    decision = evaluator.evaluate(
        progress(
            3, 10, 0,
            {"checkout", "email"},
            True,
        )
    )

    assert decision.should_stop is True

    assert (
        decision.reason
        == StopReason.INVESTIGATION_SATURATED
    )

    print("PASS: Stops after investigation saturation")


def test_new_evidence_resets_saturation():
    evaluator = InvestigationProgressEvaluator(
        min_iterations=4,
        max_stale_iterations=2,
    )

    evaluator.evaluate(
        progress(
            1, 10, 10,
            {"checkout", "email"},
            True,
        )
    )

    evaluator.evaluate(
        progress(
            2, 10, 0,
            {"checkout", "email"},
            True,
        )
    )

    evaluator.evaluate(
        progress(
            3, 15, 5,
            {"checkout", "email"},
            True,
        )
    )

    decision = evaluator.evaluate(
        progress(
            4, 15, 0,
            {"checkout", "email"},
            True,
        )
    )

    assert decision.should_stop is False

    print("PASS: New evidence resets saturation")


def test_rejects_inconsistent_evidence_growth():
    evaluator = InvestigationProgressEvaluator()

    evaluator.evaluate(
        progress(
            1, 10, 10,
            {"checkout"},
        )
    )

    try:
        evaluator.evaluate(
            progress(
                2, 15, 0,
                {"checkout"},
            )
        )
    except ValueError:
        print("PASS: Rejects inconsistent evidence growth")
        return

    raise AssertionError(
        "Expected ValueError for inconsistent evidence growth"
    )


def test_original_investigation_does_not_stop_early():
    """
    Reproduces the evidence-growth pattern observed
    in the previous RootPilot integration test.
    """

    evaluator = InvestigationProgressEvaluator()

    sequence = [
        (1, 20, 20, {"checkout"}, False),
        (2, 20, 0, {"checkout"}, False),
        (3, 40, 20, {"checkout", "email"}, False),
        (4, 40, 0, {"checkout", "email"}, False),
        (5, 69, 29, {"checkout", "email"}, True),
    ]

    for iteration, total, new, services, warning in sequence:

        decision = evaluator.evaluate(
            progress(
                iteration,
                total,
                new,
                services,
                warning,
            )
        )

        assert decision.should_stop is False, (
            f"Unexpected early stop at iteration {iteration}"
        )

    print(
        "PASS: Original investigation reaches critical evidence"
    )


def main():
    test_does_not_stop_too_early()
    test_requires_warning_or_error()
    test_requires_service_coverage()
    test_stops_after_saturation()
    test_new_evidence_resets_saturation()
    test_rejects_inconsistent_evidence_growth()
    test_original_investigation_does_not_stop_early()

    print(
        "\nPASS: All investigation progress tests"
    )


if __name__ == "__main__":
    main()