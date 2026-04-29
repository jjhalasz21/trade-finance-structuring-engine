ELIGIBILITY_CRITERIA = [
    "Invoice confirmed irrevocably by anchor buyer",
    "Supplier onboarded and signed framework agreement",
    "Invoice tenor ≤ extended buyer payment terms (max 120 days)",
    "Invoice denominated in USD",
    "No set-off or counterclaim rights outstanding",
]


def size_scf_facility(
    ap_balance_mm: float,
    supplier_count: int,
    wc_gap_mm: float,
    dpo_current_days: int,
    dpo_target_days: int,
) -> dict:
    dpo_extension = dpo_target_days - dpo_current_days
    facility_limit_mm = round(min(ap_balance_mm * 0.80, wc_gap_mm * 1.5), 0)
    return {
        "advance_rate": 1.00,
        "dilution_reserve": 0.0,
        "eligible_mm": ap_balance_mm * 0.80,
        "facility_limit_mm": facility_limit_mm,
        "dpo_extension_days": dpo_extension,
        "supplier_count": supplier_count,
        "eligibility_criteria": ELIGIBILITY_CRITERIA,
    }


def discount_amount(face_mm: float, days_outstanding: int, discount_rate: float) -> float:
    return face_mm * (days_outstanding / 360) * discount_rate
