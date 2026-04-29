from tfse.finance.pricing_buildup import find_clearing_margin


def test_returns_positive_clearing_margin():
    result = find_clearing_margin(
        drawn_mm=200.0,
        limit_mm=250.0,
        product="RF",
        committed=True,
        obligor_rating="A",
        fees_bps=25,
    )
    assert result["clearing_margin_bps"] > 0
    assert result["clearing_margin_bps"] <= 500
    assert result["roe_result"]["roe"] >= 0.12
    assert result["hurdle_headroom_bps"] >= 0
