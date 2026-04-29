from tfse.finance.roe import compute_roe


def test_rf_baseline():
    result = compute_roe(
        drawn_mm=200.0,
        margin_bps=145,
        fees_bps=25,
        ftp_rate=0.002,
        opex_mm=0.15,
        ead_mm=250.0,
        obligor_rating="A",
        product="RF",
        capital_mm=15.0,
    )
    # gross_revenue = 200*(145/10000) + 200*(25/10000) = 2.90 + 0.50 = 3.40
    assert abs(result["gross_revenue_mm"] - 3.40) < 0.01
    # cof = 200 * 0.002 = 0.40
    assert abs(result["cost_of_funds_mm"] - 0.40) < 0.01
    # roe should clear 12% hurdle at 145bps margin
    assert result["roe"] > 0.12
    assert result["roe"] == result["posttax_nii_mm"] / 15.0


def test_zero_drawn_returns_negative_roe():
    result = compute_roe(
        drawn_mm=0.0,
        margin_bps=145,
        fees_bps=25,
        ftp_rate=0.002,
        opex_mm=0.15,
        ead_mm=125.0,
        obligor_rating="A",
        product="RF",
        capital_mm=15.0,
    )
    assert result["roe"] < 0
