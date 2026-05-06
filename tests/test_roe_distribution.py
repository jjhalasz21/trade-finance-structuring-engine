import pytest
from tfse.finance.roe import compute_roe, compute_roe_with_distribution

BASE = dict(
    drawn_mm=97.5,
    margin_bps=130,
    fees_bps=25,
    ftp_rate=0.002,
    opex_mm=0.15,
    ead_mm=130.0,
    obligor_rating="A",
    product="RF",
    capital_mm=7.8,
    facility_limit_mm=130.0,
)


def test_zero_distribution_matches_full_hold():
    full = compute_roe(**{k: v for k, v in BASE.items() if k != "facility_limit_mm"})
    dist = compute_roe_with_distribution(**BASE, distribution_pct=0.0, distribution_fee_bps=0)
    for key in ("gross_revenue_mm", "cost_of_funds_mm", "expected_loss_mm",
                "pretax_nii_mm", "tax_mm", "posttax_nii_mm", "roe"):
        assert dist[key] == pytest.approx(full[key], rel=1e-6), f"mismatch on {key}"


def test_distribution_reduces_rwa():
    dist_pct = 0.12
    result = compute_roe_with_distribution(
        **BASE, distribution_pct=dist_pct, distribution_fee_bps=30
    )
    # retained_ead = 130.0 * 0.88 = 114.4; rw(A) = 0.50; retained_rwa = 57.2
    expected_retained_rwa = 130.0 * (1 - dist_pct) * 0.50
    assert result["retained_rwa_mm"] == pytest.approx(expected_retained_rwa, rel=1e-6)
    assert result["retained_capital_mm"] == pytest.approx(expected_retained_rwa * 0.12, rel=1e-6)


def test_fee_income_adds_to_nii():
    result = compute_roe_with_distribution(
        **BASE, distribution_pct=0.12, distribution_fee_bps=30
    )
    # fee_income = 130.0 * 0.12 * 30 / 10_000 = 0.0468
    expected_fee = 130.0 * 0.12 * 30 / 10_000
    assert result["fee_income_mm"] == pytest.approx(expected_fee, rel=1e-6)
    assert result["fee_income_mm"] > 0
