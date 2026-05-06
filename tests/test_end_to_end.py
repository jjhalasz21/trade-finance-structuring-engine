import pytest
import json
from pathlib import Path
from unittest.mock import patch
from tfse.models import (
    ClientProfile, DiagnosticReport, Structure, Economics,
    ProductType, Obligor, SensitivityRow, PitchBundle
)


def _mock_profile():
    return ClientProfile(
        client_name="Test Client",
        sector="Energy",
        revenue_mm=1000,
        ar_balance_mm=150,
        top_obligors=[Obligor(name="Test Co", rating="A", exposure_pct=1.0)],
        wc_gap_mm=100,
        payment_terms_days=30,
        off_bs_appetite=True,
        dilution_rate_pct=2.0,
    )


def _mock_diagnostic():
    return DiagnosticReport(
        pain_point=ProductType.RF,
        scores={"ccc_stress": 0.7, "obligor_concentration": 0.8,
                "supplier_criticality": 0.2, "inventory_days": 0.1, "off_bs_appetite": 1.0},
        recommendation_rationale="Test rationale.",
        eligible_pool_mm=120.0,
    )


def _mock_structure():
    return Structure(
        product=ProductType.RF,
        facility_limit_mm=130.0,
        advance_rate=0.87,
        dilution_reserve=0.04,
        recourse=False,
        committed=True,
        eligible_criteria=["Invoice tenor <= 120 days"],
        pricing_sofr_spread_bps=145,
        fees_bps=25,
        tenor_days=90,
        structure_rationale="Test structure.",
    )


def _mock_economics():
    return Economics(
        drawn_mm=97.5,
        gross_revenue_mm=1.6,
        cost_of_funds_mm=0.2,
        opex_mm=0.15,
        expected_loss_mm=0.02,
        pretax_nii_mm=1.23,
        tax_mm=0.31,
        posttax_nii_mm=0.92,
        rwa_mm=65.0,
        capital_mm=7.8,
        roe=0.135,
        clearing_margin_bps=130,
        hurdle_headroom_bps=10,
        sensitivity=[
            SensitivityRow(utilization_pct=0.75, margin_bps=130, roe=0.135)
        ],
        distribution_pct=0.12,
        distribution_fee_bps=30,
        distributed_mm=15.6,
        fee_income_mm=0.0468,
        retained_mm=114.4,
        retained_rwa_mm=57.2,
        retained_capital_mm=6.864,
        retained_roe=0.138,
    )


def test_output_generators_produce_artifacts(tmp_path):
    from tfse.outputs.term_sheet_pdf import generate_term_sheet
    from tfse.outputs.profitability_xlsx import generate_profitability_model
    from tfse.outputs.pitch_deck_md import generate_pitch_md
    from tfse.outputs.cme_payload import generate_cme_payload

    profile = _mock_profile()
    structure = _mock_structure()
    economics = _mock_economics()
    bundle = PitchBundle(
        profile=profile,
        diagnostic=_mock_diagnostic(),
        structure=structure,
        economics=economics,
    )

    pdf_path = generate_term_sheet(profile, structure, economics, tmp_path / "term_sheet.pdf")
    xlsx_path = generate_profitability_model(structure, economics, tmp_path / "profitability_model.xlsx")
    md_path = generate_pitch_md(bundle, "# Test\n## Executive Summary\nContent.", tmp_path / "pitch_deck.md")
    cme_path = generate_cme_payload(profile, structure, economics, tmp_path / "cme_entry.json")

    assert pdf_path.exists() and pdf_path.stat().st_size > 0
    assert xlsx_path.exists() and xlsx_path.stat().st_size > 0
    assert md_path.exists() and md_path.read_text() == "# Test\n## Executive Summary\nContent."
    assert cme_path.exists()

    cme = json.loads(cme_path.read_text())
    assert cme["roe_pct"] == pytest.approx(13.5, abs=0.01)
    assert cme["status"] == "Indicative"
    assert cme["product_code"] == "GTS-RF-001"

    assert economics.distribution_pct == 0.12
    assert economics.retained_roe > 0
    assert pdf_path.stat().st_size > 1000


def test_three_client_jsons_parse():
    for fname in ["gulf_coast_refining", "permian_pure_energy", "atlantic_metals_trading"]:
        data = json.loads(Path(f"clients/{fname}.json").read_text())
        profile = ClientProfile(**data)
        assert profile.client_name
        assert profile.wc_gap_mm > 0
