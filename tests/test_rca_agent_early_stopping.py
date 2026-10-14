import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from app.agents.rca_agent import RCAAgent
from app.agents.investigation_progress import (
    StoppingDecision,
    StopReason,
)


class FakeProvider:
    def __init__(self):
        self.generate_calls = 0
        self.structured_calls = 0

    def generate(self, messages, tools, max_tokens):
        self.generate_calls += 1

        return SimpleNamespace(
            text="Searching incident evidence",
            tool_calls=[
                SimpleNamespace(
                    id=f"call-{self.generate_calls}",
                    name="search_service_logs",
                    arguments={
                        "service_name": "checkout",
                        "start_time": "2026-10-13T14:01:00Z",
                        "end_time": "2026-10-13T14:02:00Z",
                    },
                )
            ],
            provider_metadata={},
            input_tokens=10,
            output_tokens=5,
            reasoning_tokens=0,
        )

    def generate_structured(self, messages, schema, max_tokens):
        self.structured_calls += 1

        raise RuntimeError(
            "Structured generation intentionally stopped for this test"
        )


class FakeProgressEvaluator:
    def __init__(self):
        self.calls = 0

    def evaluate(self, progress):
        self.calls += 1

        if self.calls == 4:
            return StoppingDecision(
                should_stop=True,
                reason=StopReason.INVESTIGATION_SATURATED,
                explanation="Simulated saturation after four iterations.",
            )

        return StoppingDecision(
            should_stop=False,
            reason=StopReason.CONTINUE,
            explanation="Continue investigation.",
        )


async def fake_execute_tool(tool_name, arguments):
    return []


async def main():
    provider = FakeProvider()
    evaluator = FakeProgressEvaluator()

    with (
        patch(
            "app.agents.rca_agent.LLMProviderfactory.create",
            return_value=provider,
        ),
        patch(
            "app.agents.rca_agent.InvestigationProgressEvaluator",
            return_value=evaluator,
        ),
        patch(
            "app.agents.rca_agent.execute_tool",
            side_effect=fake_execute_tool,
        ),
    ):
        agent = RCAAgent()
        agent.max_iterations = 8

        result = await agent.investigate(
            "Investigate checkout timeout."
        )

        assert result["status"] == "finalization_failed"
        assert result["completion_reason"] == "structured_finalization_error"
        assert result["iterations"] == 4
        assert result["tool_calls_executed"] == 4

    assert provider.generate_calls == 4
    assert provider.structured_calls == 1
    assert evaluator.calls == 4

    print("PASS: Agent stopped after four iterations")
    print("PASS: Agent did not exhaust eight-iteration budget")
    print("PASS: Structured RCA finalization was triggered")
    print("PASS: Structured finalization failure was handled safely")

if __name__ == "__main__":
    asyncio.run(main())