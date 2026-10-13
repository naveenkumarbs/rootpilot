from app.rca.evidence_store import EvidenceStore

def test_evidence_store():
    store = EvidenceStore()

    sample_log = {
        "timestamp": "2026-10-12T18:27:28Z",
        "service_name": "checkout",
        "severity": "WARN",
        "message": (
            "failed POST to email service: "
            "context deadline exceeded"
        ),
        "trace_id": None,
        "span_id": None,
    }

    arguments = {
        "service_name": "checkout",
        "minutes": 60,
        "severity": "WARN",
    }

    evidence_1 = store.add_log(
        log=sample_log,
        tool_name="search_service_logs",
        tool_arguments=arguments,
    )

    assert evidence_1.evidence_id == "EV-0001"
    assert store.count() == 1

    # Adding the same log again should not create new evidence.
    evidence_2 = store.add_log(
        log=sample_log,
        tool_name="search_service_log",
        tool_arguments=arguments,
    )

    assert evidence_2.evidence_id == "EV-0001"
    assert store.count() == 1

    # Different log should receive a new evidence ID.
    second_log = {
        **sample_log,
        "timestamp": "2026-10-12T18:28:00Z",
    }

    evidence_3 = store.add_log(
        log=second_log,
        tool_name="search_service_logs",
        tool_arguments=arguments,
    )

    assert evidence_3.evidence_id == "EV-0002"
    assert store.count() == 2

    assert store.get("EV-0001") is not None
    assert store.get("EV-9999") is None

    print("EvidenceStore tests passed successfully")

if __name__ == "__main__":
    test_evidence_store()
