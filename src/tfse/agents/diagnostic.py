import json
from pathlib import Path
import anthropic
from tfse.constants import MODEL_OPUS, ANTHROPIC_API_KEY
from tfse.models import ClientProfile, DiagnosticReport

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
_PROMPT = (Path(__file__).parent.parent / "prompts" / "diagnostic.md").read_text()


def run_diagnostic(profile: ClientProfile) -> DiagnosticReport:
    response = _client.messages.create(
        model=MODEL_OPUS,
        max_tokens=1024,
        temperature=0,
        system=_PROMPT,
        messages=[{"role": "user", "content": profile.model_dump_json(indent=2)}],
    )
    data = json.loads(response.content[0].text)
    return DiagnosticReport(**data)
