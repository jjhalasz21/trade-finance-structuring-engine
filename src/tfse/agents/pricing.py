from tfse.models import ClientProfile, Structure, Economics, SensitivityRow
from tfse.finance.pricing_buildup import find_clearing_margin
from tfse.finance.roe import compute_roe
from tfse.finance.rwa import compute_rwa
from tfse.constants import FTP_RATE, OPEX


def _dominant_rating(profile: ClientProfile) -> str:
    if not profile.top_obligors:
        return "BBB"
    top = max(profile.top_obligors, key=lambda o: o.exposure_pct)
    return top.rating


def run_pricing(profile: ClientProfile, structure: Structure) -> Economics:
    product = structure.product.value
    obligor_rating = _dominant_rating(profile)
    drawn_mm = structure.facility_limit_mm * 0.75

    result = find_clearing_margin(
        drawn_mm=drawn_mm,
        limit_mm=structure.facility_limit_mm,
        product=product,
        committed=structure.committed,
        obligor_rating=obligor_rating,
        fees_bps=structure.fees_bps,
    )

    rr = result["roe_result"]
    rwa_r = result["rwa_result"]
    opex_mm = OPEX[product] / 1_000_000

    sensitivity = []
    for util in [0.60, 0.75, 0.90]:
        for margin_delta in [-25, 0, 25]:
            test_drawn = structure.facility_limit_mm * util
            test_margin = result["clearing_margin_bps"] + margin_delta
            test_rwa = compute_rwa(test_drawn, structure.facility_limit_mm, product, structure.committed, obligor_rating)
            test_roe = compute_roe(
                drawn_mm=test_drawn,
                margin_bps=test_margin,
                fees_bps=structure.fees_bps,
                ftp_rate=FTP_RATE,
                opex_mm=opex_mm,
                ead_mm=test_rwa["ead_mm"],
                obligor_rating=obligor_rating,
                product=product,
                capital_mm=test_rwa["capital_mm"],
            )
            sensitivity.append(SensitivityRow(
                utilization_pct=util,
                margin_bps=test_margin,
                roe=test_roe["roe"],
            ))

    return Economics(
        drawn_mm=drawn_mm,
        gross_revenue_mm=rr["gross_revenue_mm"],
        cost_of_funds_mm=rr["cost_of_funds_mm"],
        opex_mm=rr["opex_mm"],
        expected_loss_mm=rr["expected_loss_mm"],
        pretax_nii_mm=rr["pretax_nii_mm"],
        tax_mm=rr["tax_mm"],
        posttax_nii_mm=rr["posttax_nii_mm"],
        rwa_mm=rwa_r["rwa_mm"],
        capital_mm=rwa_r["capital_mm"],
        roe=rr["roe"],
        clearing_margin_bps=result["clearing_margin_bps"],
        hurdle_headroom_bps=result["hurdle_headroom_bps"],
        sensitivity=sensitivity,
    )
