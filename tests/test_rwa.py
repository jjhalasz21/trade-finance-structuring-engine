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
    # EAD = 200 + (250 * 1.00) = 450; RW=0.50; RWA=225; Capital=225*0.12=27
    assert abs(result["ead_mm"] - 450.0) < 0.01
    assert abs(result["rwa_mm"] - 225.0) < 0.01
    assert abs(result["capital_mm"] - 27.0) < 0.01


def test_scf_uncommitted_bbb_rated():
    result = compute_rwa(
        drawn_mm=100.0,
        limit_mm=150.0,
        product="SCF",
        committed=False,
        obligor_rating="BBB",
    )
    # EAD = 100 + (150 * 0.20) = 130; RW=1.00; RWA=130; Capital=15.6
    assert abs(result["ead_mm"] - 130.0) < 0.01
    assert abs(result["rwa_mm"] - 130.0) < 0.01
    assert abs(result["capital_mm"] - 15.6) < 0.01


def test_inventory_uncommitted_bbb():
    result = compute_rwa(
        drawn_mm=70.0,
        limit_mm=100.0,
        product="INVENTORY",
        committed=False,
        obligor_rating="BBB",
    )
    # EAD = 70 + (100 * 0.50) = 120; RW=1.00; RWA=120; Capital=14.4
    assert abs(result["ead_mm"] - 120.0) < 0.01
    assert abs(result["rwa_mm"] - 120.0) < 0.01
    assert abs(result["capital_mm"] - 14.4) < 0.01
