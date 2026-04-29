import json
from pathlib import Path
import anthropic
from tfse.constants import MODEL_HAIKU, ANTHROPIC_API_KEY
from tfse.models import PitchBundle

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
_PROMPT = (Path(__file__).parent.parent / "prompts" / "pitch.md").read_text()


def run_pitch(bundle: PitchBundle) -> str:
    response = _client.messages.create(
        model=MODEL_HAIKU,
        max_tokens=4096,
        temperature=0,
        system=_PROMPT,
        messages=[{"role": "user", "content": bundle.model_dump_json(indent=2)}],
    )
    return response.content[0].text
