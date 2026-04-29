from tfse.constants import CCF, RISK_WEIGHTS


def _ccf(product: str, committed: bool) -> float:
    if product == "RF" and committed:
        return CCF["RF_COMMITTED"]
    if product == "SCF":
        return CCF["SCF_UNCOMMITTED"]
    return CCF["INVENTORY_UNCOMMITTED"]


def compute_rwa(
    drawn_mm: float,
    limit_mm: float,
    product: str,
    committed: bool,
    obligor_rating: str,
) -> dict:
    ccf = _ccf(product, committed)
    ead_mm = drawn_mm + ccf * (limit_mm - drawn_mm)
    rw = RISK_WEIGHTS.get(obligor_rating, 1.00)
    rwa_mm = ead_mm * rw
    capital_mm = rwa_mm * 0.12
    return {"ead_mm": ead_mm, "rwa_mm": rwa_mm, "capital_mm": capital_mm}
