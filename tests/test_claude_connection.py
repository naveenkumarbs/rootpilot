from anthropic import AnthropicVertex

PROJECT_ID = "project-deee471f-da7a-4fa1-b00"
MODEL_ID = "claude-haiku-4-5@20251001"

client = AnthropicVertex (
    project_id=PROJECT_ID,
    region="global",
)

response = client.messages.create(
    model=MODEL_ID,
    max_tokens=256,
    messages=[
        {
            "role": "user",
            "context": "Explain Root Cause Analysis in two sentences."
        }
    ],
)

print("\nClaude Response:\n")

for block in response.content:
    if block.type == "text":
        print(block.text)

print ("\nToken Usage:")
print ("Input: ", response.usage.input_tokens)
print ("Output: ", response.usage.output_tokens)