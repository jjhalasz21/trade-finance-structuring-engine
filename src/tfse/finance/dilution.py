def dilution_reserve(dilution_rate_pct: float, multiplier: float = 2.0) -> float:
    """Returns reserve as a fraction of gross eligible AR."""
    return (dilution_rate_pct / 100) * multiplier
