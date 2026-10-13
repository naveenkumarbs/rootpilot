from app.llm.factory import LLMProviderfactory
from app.llm.models import LLMMessage
from app.rca.models import RCAAnalysis

provider = LLMProviderfactory.create()

analysis, response = provider.generate_structured(
    messages=[
        LLMMessage(
            role="user",
            content=(
                "Generate an RCA analysis for a checkout service "
                "that experienced HTTP timeouts when calling an "
                "email service. No evidence IDs are available. "
                "Do not create confirmed findings or observations."
            ),
        )
    ],
    response_model=RCAAnalysis,
)

print(analysis.model_dump_json(indent=2))