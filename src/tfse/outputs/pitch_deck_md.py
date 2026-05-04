from pathlib import Path
from tfse.models import PitchBundle


def generate_pitch_md(bundle: PitchBundle, pitch_text: str, output_path: Path) -> Path:
    output_path.write_text(pitch_text, encoding="utf-8")
    return output_path
