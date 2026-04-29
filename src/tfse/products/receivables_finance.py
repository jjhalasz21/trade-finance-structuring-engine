from tfse.finance.advance_rate import rf_advance_rate
from tfse.finance.dilution import dilution_reserve


ELIGIBILITY_CRITERIA = [
    "Invoice tenor ≤ 120 days",
    "Obligor on approved counterparty list",
    "Single obligor concentration ≤ 25% of eligible pool",
    "Sector concentration ≤ 40% of eligible pool",
    "No disputed or credit-noted invoices",
    "Invoice denominated in USD, EUR, or GBP",
]


def size_rf_facility(
    ar_balance_mm: float,
    obligors: list[dict],
    dilution_rate_pct: float,
    wc_gap_mm: float,
) -> dict:
    advance_rate = rf_advance_rate(obligors)
    dil_reserve = dilution_reserve(dilution_rate_pct)
    net_advance = advance_rate - dil_reserve
    eligible_mm = ar_balance_mm * net_advance
    facility_limit_mm = round(min(eligible_mm * 1.1, wc_gap_mm * 1.25), 0)
    return {
        "advance_rate": advance_rate,
        "dilution_reserve": dil_reserve,
        "eligible_mm": eligible_mm,
        "facility_limit_mm": facility_limit_mm,
        "eligibility_criteria": ELIGIBILITY_CRITERIA,
    }
