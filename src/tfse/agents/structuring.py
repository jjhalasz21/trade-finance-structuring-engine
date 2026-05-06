import json
import re
from pathlib import Path
import anthropic
from tfse.constants import MODEL_OPUS, ANTHROPIC_API_KEY
from tfse.models import ClientProfile, DiagnosticReport, Structure
from tfse.products.receivables_finance import size_rf_facility
from tfse.products.supply_chain_finance import size_scf_facility
from tfse.products.inventory_finance import size_inventory_facility

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
_PROMPT = (Path(__file__).parent.parent / "prompts" / "structuring.md").read_text()


def _sizing_context(profile: ClientProfile, diagnostic: DiagnosticReport) -> dict:
    product = diagnostic.pain_point.value
    obligors = [o.model_dump() for o in profile.top_obligors]
    if product == "RF":
        return size_rf_facility(
            profile.ar_balance_mm or diagnostic.eligible_pool_mm,
            obligors,
            profile.dilution_rate_pct,
            profile.wc_gap_mm,
        )
    if product == "SCF":
        return size_scf_facility(
            profile.ap_balance_mm or diagnostic.eligible_pool_mm,
            profile.supplier_count or 50,
            profile.wc_gap_mm,
            profile.dpo_current_days or 45,
            profile.dpo_target_days or 75,
        )
    return size_inventory_facility(
        profile.inventory_mm or diagnostic.eligible_pool_mm,
        profile.inventory_commodities or ["LME_COPPER"],
        profile.wc_gap_mm,
    )


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


def run_structuring(profile: ClientProfile, diagnostic: DiagnosticReport) -> Structure:
    sizing = _sizing_context(profile, diagnostic)
    payload = {
        "diagnostic": diagnostic.model_dump(),
        "profile_summary": {
            "client_name": profile.client_name,
            "sector": profile.sector,
            "top_obligors": [o.model_dump() for o in profile.top_obligors],
            "off_bs_appetite": profile.off_bs_appetite,
        },
        "sizing_module_output": sizing,
    }
    response = _client.messages.create(
        model=MODEL_OPUS,
        max_tokens=1024,
        system=_PROMPT,
        messages=[{"role": "user", "content": json.dumps(payload, indent=2)}],
    )
    data = json.loads(_extract_json(response.content[0].text))
    return Structure(**data)
