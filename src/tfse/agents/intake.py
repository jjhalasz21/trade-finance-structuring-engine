import json
import re
import anthropic
from tfse.constants import MODEL_HAIKU, ANTHROPIC_API_KEY
from tfse.models import ClientProfile

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

INTAKE_SYSTEM = (
    "You are a data validation agent. You receive a JSON object representing a "
    "trade finance client intake. Validate the data, normalize units (revenue and "
    "balances in $M), and return a cleaned JSON object. If a required field is missing "
    "or invalid, raise a ValueError describing the issue. Return ONLY valid JSON."
)


def _extract_json(text: str) -> str:
    """Extract JSON object from response text, stripping markdown fences or extra prose."""
    text = text.strip()
    # Try to extract from code fence first
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    # Otherwise find the first { ... } block
    start = text.find("{")
    if start != -1:
        # Find matching closing brace
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return text


def run_intake(raw: dict) -> ClientProfile:
    response = _client.messages.create(
        model=MODEL_HAIKU,
        max_tokens=1024,
        temperature=0,
        system=INTAKE_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(raw, indent=2)}],
    )
    cleaned = json.loads(_extract_json(response.content[0].text))
    return ClientProfile(**cleaned)
