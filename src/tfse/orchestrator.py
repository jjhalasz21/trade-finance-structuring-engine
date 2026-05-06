import json
import os
import tempfile
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from tfse.models import PitchBundle
from tfse.agents.intake import run_intake
from tfse.agents.diagnostic import run_diagnostic
from tfse.agents.structuring import run_structuring
from tfse.agents.pricing import run_pricing
from tfse.agents.pitch import run_pitch
from tfse.outputs.term_sheet_pdf import generate_term_sheet
from tfse.outputs.profitability_xlsx import generate_profitability_model
from tfse.outputs.pitch_deck_md import generate_pitch_md
from tfse.outputs.cme_payload import generate_cme_payload

console = Console()


def _load_env():
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() not in os.environ:
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")


def run(client_json_path: str) -> None:
    _load_env()
    raw = json.loads(Path(client_json_path).read_text())
    client_slug = Path(client_json_path).stem

    output_dir = Path("outputs") / client_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        t1 = progress.add_task("Intake agent — validating client data...", total=None)
        profile = run_intake(raw)
        progress.update(t1, description="[green]✓ Intake complete")
        progress.stop_task(t1)

        t2 = progress.add_task("Diagnostic agent — identifying WC pain point...", total=None)
        diagnostic = run_diagnostic(profile)
        progress.update(t2, description=f"[green]✓ Diagnostic: {diagnostic.pain_point.value}")
        progress.stop_task(t2)

        t3 = progress.add_task("Structuring agent — setting term-sheet parameters...", total=None)
        structure = run_structuring(profile, diagnostic)
        progress.update(t3, description="[green]✓ Structure defined")
        progress.stop_task(t3)

        t4 = progress.add_task("Pricing agent — computing RoE and clearing margin...", total=None)
        economics = run_pricing(profile, structure)
        progress.update(t4, description=f"[green]✓ Clearing margin: SOFR+{economics.clearing_margin_bps}bps | RoE: {economics.roe:.1%}")
        progress.stop_task(t4)

        t5 = progress.add_task("Pitch agent — drafting client narrative...", total=None)
        bundle = PitchBundle(profile=profile, diagnostic=diagnostic, structure=structure, economics=economics)
        pitch_text = run_pitch(bundle)
        progress.update(t5, description="[green]✓ Pitch narrative drafted")
        progress.stop_task(t5)

    console.print("\n[bold]Generating artifacts...[/bold]")
    pdf_path = generate_term_sheet(profile, structure, economics, output_dir / "term_sheet.pdf")
    xlsx_path = generate_profitability_model(structure, economics, output_dir / "profitability_model.xlsx")
    md_path = generate_pitch_md(bundle, pitch_text, output_dir / "pitch_deck.md")
    cme_path = generate_cme_payload(profile, structure, economics, output_dir / "cme_entry.json")

    console.print(f"\n[bold green]Done! Artifacts for {profile.client_name}:[/bold green]")
    console.print(f"  [cyan]Term Sheet:[/cyan]          {pdf_path}")
    console.print(f"  [cyan]Profitability Model:[/cyan] {xlsx_path}")
    console.print(f"  [cyan]Pitch Deck (MD):[/cyan]     {md_path}")
    console.print(f"  [cyan]CRM Entry:[/cyan]           {cme_path}")


def run_pipeline_in_memory(
    raw: dict,
    distribution_pct: float = 0.12,
    distribution_fee_bps: int | None = None,
) -> tuple:
    """Run the full pipeline and return artifact bytes for Streamlit download buttons.

    Returns: (profile, diagnostic, structure, economics, pitch_text, pdf_bytes, xlsx_bytes, md_str, cme_dict)
    """
    profile = run_intake(raw)
    diagnostic = run_diagnostic(profile)
    structure = run_structuring(profile, diagnostic)
    economics = run_pricing(profile, structure, distribution_pct, distribution_fee_bps)
    bundle = PitchBundle(profile=profile, diagnostic=diagnostic, structure=structure, economics=economics)
    pitch_text = run_pitch(bundle)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        pdf_path = generate_term_sheet(profile, structure, economics, tmp / "term_sheet.pdf")
        xlsx_path = generate_profitability_model(structure, economics, tmp / "profitability_model.xlsx")
        cme_path = generate_cme_payload(profile, structure, economics, tmp / "cme_entry.json")

        pdf_bytes = pdf_path.read_bytes()
        xlsx_bytes = xlsx_path.read_bytes()
        cme_dict = json.loads(cme_path.read_text())

    return profile, diagnostic, structure, economics, pitch_text, pdf_bytes, xlsx_bytes, pitch_text, cme_dict
