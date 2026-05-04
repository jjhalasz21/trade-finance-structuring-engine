import json
from pathlib import Path
from datetime import date
from tfse.models import ClientProfile, Structure, Economics


def generate_cme_payload(
    profile: ClientProfile,
    structure: Structure,
    economics: Economics,
    output_path: Path,
) -> Path:
    product_codes = {"RF": "GTS-RF-001", "SCF": "GTS-SCF-001", "INVENTORY": "GTS-INV-001"}
    payload = {
        "deal_name": f"{profile.client_name} — {structure.product.value} Facility",
        "client_id": profile.client_name.upper().replace(" ", "_"),
        "product_code": product_codes.get(structure.product.value, "GTS-OTHER"),
        "facility_size_mm": structure.facility_limit_mm,
        "sector": profile.sector,
        "indicative_margin_bps": structure.pricing_sofr_spread_bps,
        "expected_annual_revenue_mm": round(economics.gross_revenue_mm, 3),
        "rwa_mm": round(economics.rwa_mm, 3),
        "roe_pct": round(economics.roe * 100, 2),
        "status": "Indicative",
        "date_created": date.today().isoformat(),
        "relationship_manager": "HSBC GTS Sales",
        "next_step": "Credit application and KYC submission",
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
