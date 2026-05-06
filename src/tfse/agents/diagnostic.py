import json
import re
from pathlib import Path
import anthropic
from tfse.constants import MODEL_OPUS, ANTHROPIC_API_KEY
from tfse.models import ClientProfile, DiagnosticReport

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
_PROMPT = (Path(__file__).parent.parent / "prompts" / "diagnostic.md").read_text()


def _extract_json(text: str) -> str:
    """Extract JSON object from response text, stripping markdown fences or extra prose."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    start = text.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return text


def run_diagnostic(profile: ClientProfile) -> DiagnosticReport:
    response = _client.messages.create(
        model=MODEL_OPUS,
        max_tokens=1024,
        system=_PROMPT,
        messages=[{"role": "user", "content": profile.model_dump_json(indent=2)}],
    )
    data = json.loads(_extract_json(response.content[0].text))
    return DiagnosticReport(**data)
