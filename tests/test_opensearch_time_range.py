from app.telemetry.opensearch_client import build_time_range


def expect_value_error(fn, description):
    try:
        fn()
    except ValueError:
        print(f"PASS: {description}")
        return

    raise AssertionError(
        f"Expected ValueError: {description}"
    )


def test_default_relative_range():
    result = build_time_range()

    assert result == {
        "gte": "now-15m",
        "lte": "now",
    }

    print("PASS: Default relative range")


def test_explicit_relative_range():
    result = build_time_range(minutes=30)

    assert result == {
        "gte": "now-30m",
        "lte": "now",
    }

    print("PASS: Explicit relative range")


def test_absolute_range():
    result = build_time_range(
        start_time="2026-10-13T14:00:00Z",
        end_time="2026-10-13T14:05:00Z",
    )

    assert result["gte"] == "2026-10-13T14:00:00+00:00"
    assert result["lte"] == "2026-10-13T14:05:00+00:00"

    print("PASS: Absolute range")


def test_invalid_order():
    expect_value_error(
        lambda: build_time_range(
            start_time="2026-10-13T14:05:00Z",
            end_time="2026-10-13T14:00:00Z",
        ),
        "Start time after end time rejected",
    )


def test_missing_end_time():
    expect_value_error(
        lambda: build_time_range(
            start_time="2026-10-13T14:00:00Z",
        ),
        "Missing end_time rejected",
    )


def test_conflicting_modes():
    expect_value_error(
        lambda: build_time_range(
            minutes=15,
            start_time="2026-10-13T14:00:00Z",
            end_time="2026-10-13T14:05:00Z",
        ),
        "Conflicting time modes rejected",
    )


def test_excessive_range():
    expect_value_error(
        lambda: build_time_range(
            start_time="2026-10-13T12:00:00Z",
            end_time="2026-10-13T14:00:00Z",
        ),
        "Absolute range over 60 minutes rejected",
    )


def test_missing_timezone():
    expect_value_error(
        lambda: build_time_range(
            start_time="2026-10-13T14:00:00",
            end_time="2026-10-13T14:05:00",
        ),
        "Timezone-free timestamps rejected",
    )


def main():
    test_default_relative_range()
    test_explicit_relative_range()
    test_absolute_range()
    test_invalid_order()
    test_missing_end_time()
    test_conflicting_modes()
    test_excessive_range()
    test_missing_timezone()

    print("\nAll OpenSearch time-range tests passed.")


if __name__ == "__main__":
    main()