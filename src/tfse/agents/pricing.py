from tfse.models import ClientProfile, Structure, Economics, SensitivityRow
from tfse.finance.pricing_buildup import find_clearing_margin
from tfse.finance.roe import compute_roe, compute_roe_with_distribution
from tfse.finance.rwa import compute_rwa
from tfse.constants import FTP_RATE, OPEX, DISTRIBUTION_FEE_BPS, DISTRIBUTION_PCT_DEFAULT


def _dominant_rating(profile: ClientProfile) -> str:
    if not profile.top_obligors:
        return "BBB"
    top = max(profile.top_obligors, key=lambda o: o.exposure_pct)
    return top.rating


def run_pricing(
    profile: ClientProfile,
    structure: Structure,
    distribution_pct: float = DISTRIBUTION_PCT_DEFAULT,
    distribution_fee_bps: int | None = None,
) -> Economics:
    product = structure.product.value
    obligor_rating = _dominant_rating(profile)
    drawn_mm = structure.facility_limit_mm * 0.75

    if distribution_fee_bps is None:
        distribution_fee_bps = DISTRIBUTION_FEE_BPS.get(product, 30)

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

    dist = compute_roe_with_distribution(
        drawn_mm=drawn_mm,
        margin_bps=result["clearing_margin_bps"],
        fees_bps=structure.fees_bps,
        ftp_rate=FTP_RATE,
        opex_mm=opex_mm,
        ead_mm=rwa_r["ead_mm"],
        obligor_rating=obligor_rating,
        product=product,
        capital_mm=rwa_r["capital_mm"],
        facility_limit_mm=structure.facility_limit_mm,
        distribution_pct=distribution_pct,
        distribution_fee_bps=distribution_fee_bps,
    )

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
        distribution_pct=distribution_pct,
        distribution_fee_bps=distribution_fee_bps,
        distributed_mm=dist["distributed_mm"],
        fee_income_mm=dist["fee_income_mm"],
        retained_mm=dist["retained_mm"],
        retained_rwa_mm=dist["retained_rwa_mm"],
        retained_capital_mm=dist["retained_capital_mm"],
        retained_roe=dist["retained_roe"],
    )
