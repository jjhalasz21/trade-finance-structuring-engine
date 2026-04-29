import pytest
from tfse.finance.rwa import compute_rwa


def test_rf_committed_a_rated():
    result = compute_rwa(
        drawn_mm=200.0,
        limit_mm=250.0,
        product="RF",
        committed=True,
        obligor_rating="A",
    )
    # EAD = 200 + 1.00 * (250-200) = 250; RW=0.50; RWA=125; Capital=15.0
    assert abs(result["ead_mm"] - 250.0) < 0.01
    assert abs(result["rwa_mm"] - 125.0) < 0.01
    assert abs(result["capital_mm"] - 15.0) < 0.01


def test_scf_uncommitted_bbb_rated():
    result = compute_rwa(
        drawn_mm=100.0,
        limit_mm=150.0,
        product="SCF",
        committed=False,
        obligor_rating="BBB",
    )
    # EAD = 100 + 0.20 * (150-100) = 110; RW=1.00; RWA=110; Capital=13.2
    assert abs(result["ead_mm"] - 110.0) < 0.01
    assert abs(result["rwa_mm"] - 110.0) < 0.01
    assert abs(result["capital_mm"] - 13.2) < 0.01


def test_inventory_uncommitted_bbb():
    result = compute_rwa(
        drawn_mm=70.0,
        limit_mm=100.0,
        product="INVENTORY",
        committed=False,
        obligor_rating="BBB",
    )
    # EAD = 70 + 0.50 * (100-70) = 85; RW=1.00; RWA=85; Capital=10.2
    assert abs(result["ead_mm"] - 85.0) < 0.01
    assert abs(result["rwa_mm"] - 85.0) < 0.01
    assert abs(result["capital_mm"] - 10.2) < 0.01
