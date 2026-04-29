from tfse.constants import ADVANCE_RATE_RF, ADVANCE_RATE_INVENTORY


def rf_advance_rate(obligors: list[dict]) -> float:
    """Weighted-average advance rate based on obligor rating mix."""
    total_weight = sum(o["exposure_pct"] for o in obligors)
    if total_weight == 0:
        return 0.85
    weighted = sum(
        ADVANCE_RATE_RF.get(o["rating"], 0.80) * o["exposure_pct"]
        for o in obligors
    )
    return weighted / total_weight


def inventory_advance_rate(commodity: str) -> float:
    return ADVANCE_RATE_INVENTORY.get(commodity.upper().replace(" ", "_"), 0.65)
