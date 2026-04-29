from tfse.finance.advance_rate import rf_advance_rate, inventory_advance_rate


def test_rf_all_a_rated():
    obligors = [{"rating": "A", "exposure_pct": 1.0}]
    assert abs(rf_advance_rate(obligors) - 0.87) < 0.001


def test_rf_mixed_rating():
    obligors = [
        {"rating": "A", "exposure_pct": 0.5},
        {"rating": "BBB", "exposure_pct": 0.5},
    ]
    expected = (0.87 * 0.5 + 0.85 * 0.5) / 1.0
    assert abs(rf_advance_rate(obligors) - expected) < 0.001


def test_inventory_copper():
    assert inventory_advance_rate("LME_COPPER") == 0.70


def test_inventory_aluminum():
    assert inventory_advance_rate("LME_ALUMINUM") == 0.65
