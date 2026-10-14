from dataclasses import dataclass, field
from enum import Enum

"""
RootPilot will stop early only when all the following conditions hold:

A minimum number of investigation iterations have completed.
Sufficient evidence has been collected.
At least one potentially incident-relevant warning or error has been observed.
At least two services have been investigated successfully.
The last two completed iterations have produced no new evidence.

This is a conservative investigation-saturation heuristic, 
not proof that the root cause has been identified.

"""

class StopReason(str, Enum):
    CONTINUE = "continue"
    INVESTIGATION_SATURATED = "investigation_saturated"


@dataclass(frozen=True)
class InvestigationProgress:
    iteration: int
    total_evidence: int
    new_evidence: int
    services_with_evidence: frozenset[str]
    has_warning_or_error: bool


@dataclass(frozen=True)
class StoppingDecision:
    should_stop: bool
    reason: StopReason
    explanation: str


@dataclass
class InvestigationProgressEvaluator:
    min_iterations: int = 4
    min_evidence: int = 5
    min_services: int = 2
    max_stale_iterations: int = 2

    history: list[InvestigationProgress] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        if self.min_iterations < 1:
            raise ValueError("min_iterations must be >= 1")

        if self.min_evidence < 1:
            raise ValueError("min_evidence must be >= 1")

        if self.min_services < 1:
            raise ValueError("min_services must be >= 1")

        if self.max_stale_iterations < 1:
            raise ValueError(
                "max_stale_iterations must be >= 1"
            )

    def evaluate(
        self,
        progress: InvestigationProgress,
    ) -> StoppingDecision:

        if progress.iteration < 1:
            raise ValueError("iteration must be >= 1")

        if progress.total_evidence < 0:
            raise ValueError("total_evidence cannot be negative")

        if progress.new_evidence < 0:
            raise ValueError("new_evidence cannot be negative")

        if progress.new_evidence > progress.total_evidence:
            raise ValueError(
                "new_evidence cannot exceed total_evidence"
            )

        if self.history:
            previous = self.history[-1]

            if progress.iteration != previous.iteration + 1:
                raise ValueError(
                    "Iterations must be recorded sequentially"
                )

            if progress.total_evidence < previous.total_evidence:
                raise ValueError(
                    "Total evidence cannot decrease"
                )

            actual_growth = (
                progress.total_evidence
                - previous.total_evidence
            )

            if progress.new_evidence != actual_growth:
                raise ValueError(
                    "new_evidence does not match evidence growth"
                )

        self.history.append(progress)

        if progress.iteration < self.min_iterations:
            return self._continue(
                "Minimum investigation iterations not reached."
            )

        if progress.total_evidence < self.min_evidence:
            return self._continue(
                "Insufficient evidence collected."
            )

        if not progress.has_warning_or_error:
            return self._continue(
                "No warning or error evidence observed."
            )

        if len(progress.services_with_evidence) < self.min_services:
            return self._continue(
                "Insufficient service investigation coverage."
            )

        recent = self.history[-self.max_stale_iterations:]

        if len(recent) < self.max_stale_iterations:
            return self._continue(
                "Not enough iterations to assess saturation."
            )

        if any(item.new_evidence > 0 for item in recent):
            return self._continue(
                "Recent iterations produced new evidence."
            )

        return StoppingDecision(
            should_stop=True,
            reason=StopReason.INVESTIGATION_SATURATED,
            explanation=(
                "Investigation appears saturated: "
                "minimum coverage and evidence requirements "
                "were met, but recent iterations produced "
                "no new evidence."
            ),
        )

    @staticmethod
    def _continue(explanation: str) -> StoppingDecision:
        return StoppingDecision(
            should_stop=False,
            reason=StopReason.CONTINUE,
            explanation=explanation,
        )