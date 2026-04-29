from tfse.finance.advance_rate import inventory_advance_rate

ELIGIBILITY_CRITERIA = [
    "Physical commodity in LME-approved warehouse",
    "HSBC-controlled warehouse receipt or trust receipt in place",
    "Commodity hedgeable on recognised exchange (LME, CME)",
    "LME-quality specification confirmed by independent inspector",
    "Collateral monitoring agent appointed",
    "Insurance in place (all-risk, warehouse-to-warehouse)",
]


def size_inventory_facility(
    inventory_mm: float,
    commodities: list[str],
    wc_gap_mm: float,
) -> dict:
    rates = [inventory_advance_rate(c) for c in commodities]
    blended_rate = sum(rates) / len(rates) if rates else 0.65
    haircut = 0.01
    net_advance = blended_rate * (1 - haircut)
    eligible_mm = inventory_mm * net_advance
    facility_limit_mm = round(min(eligible_mm, wc_gap_mm * 1.2), 0)
    return {
        "advance_rate": blended_rate,
        "dilution_reserve": 0.0,
        "eligible_mm": eligible_mm,
        "facility_limit_mm": facility_limit_mm,
        "price_haircut": haircut,
        "eligibility_criteria": ELIGIBILITY_CRITERIA,
    }
