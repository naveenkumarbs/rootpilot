from app.tools.query_coverage import CachedLogQuery, QueryCoverage


def make_cached(
    results=None,
    complete=True,
    **overrides,
):
    arguments = {
        "service_name": "checkout",
        "start_time": "2026-10-13T14:00:00Z",
        "end_time": "2026-10-13T14:05:00Z",
        "limit": 50,
    }

    arguments.update(overrides)

    return CachedLogQuery(
        arguments=arguments,
        results=results or [],
        complete=complete,
    )


def test_narrower_window():

    cached = make_cached()

    requested = {
        "service_name": "checkout",
        "start_time": "2026-10-13T14:01:00Z",
        "end_time": "2026-10-13T14:03:00Z",
        "limit": 20,
    }
    
    assert QueryCoverage.can_reuse(cached, requested)

    print("PASS: Narrower time window")


def test_different_service():

    cached = make_cached()

    requested = {
        "service_name": "email",
        "start_time": "2026-10-13T14:01:00Z",
        "end_time": "2026-10-13T14:03:00Z",
    }

    assert not QueryCoverage.can_reuse(cached, requested)

    print("PASS: Different service rejected")


def test_incomplete_result():

    cached = make_cached(complete=False)

    requested = {
        "service_name": "checkout",
        "start_time": "2026-10-13T14:01:00Z",
        "end_time": "2026-10-13T14:03:00Z",
    }

    assert not QueryCoverage.can_reuse(cached, requested)

    print("PASS: Incomplete result rejected")


def test_wider_window():

    cached = make_cached()

    requested = {
        "service_name": "checkout",
        "start_time": "2026-10-13T13:59:00Z",
        "end_time": "2026-10-13T14:06:00Z",
    }

    assert not QueryCoverage.can_reuse(cached, requested)

    print("PASS: Wider time window rejected")


def test_severity_filter():

    cached = make_cached(
        results=[
            {
                "timestamp": "2026-10-13T14:01:00Z",
                "severity": "ERROR",
                "message": "Timeout",
            },
            {
                "timestamp": "2026-10-13T14:02:00Z",
                "severity": "INFO",
                "message": "Request completed",
            },
        ]
    )

    requested = {
        "service_name": "checkout",
        "start_time": "2026-10-13T14:00:00Z",
        "end_time": "2026-10-13T14:03:00Z",
        "severity": "ERROR",
        "limit": 20,
    }

    assert QueryCoverage.can_reuse(cached, requested)

    result = QueryCoverage.filter_results(cached, requested)

    assert len(result) == 1
    assert result[0]["severity"] == "ERROR"

    print("PASS: Severity filtering")


def test_relative_window_not_reused():

    cached = make_cached()

    requested = {
        "service_name": "checkout",
        "minutes": 15,
    }

    assert not QueryCoverage.can_reuse(cached, requested)

    print("PASS: Relative-time query rejected")


def main():
    test_narrower_window()
    test_different_service()
    test_incomplete_result()
    test_wider_window()
    test_severity_filter()
    test_relative_window_not_reused()

    print("\nAll QueryCoverage tests passed.")


if __name__ == "__main__":
    main()