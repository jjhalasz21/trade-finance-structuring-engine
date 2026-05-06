from tfse.constants import PD, LGD_UNSECURED, LGD_SECURED, TAX_RATE, RISK_WEIGHTS


def compute_roe(
    drawn_mm: float,
    margin_bps: int,
    fees_bps: int,
    ftp_rate: float,
    opex_mm: float,
    ead_mm: float,
    obligor_rating: str,
    product: str,
    capital_mm: float,
) -> dict:
    margin = margin_bps / 10_000
    fee_rate = fees_bps / 10_000
    gross_revenue_mm = drawn_mm * margin + drawn_mm * fee_rate
    cof_mm = drawn_mm * ftp_rate
    pd = PD.get(obligor_rating, 0.002)
    lgd = LGD_SECURED if product == "INVENTORY" else LGD_UNSECURED
    el_mm = ead_mm * pd * lgd
    pretax_nii_mm = gross_revenue_mm - cof_mm - opex_mm - el_mm
    tax_mm = max(pretax_nii_mm * TAX_RATE, 0.0)
    posttax_nii_mm = pretax_nii_mm - tax_mm
    roe = posttax_nii_mm / capital_mm if capital_mm > 0 else -999.0
    return {
        "gross_revenue_mm": gross_revenue_mm,
        "cost_of_funds_mm": cof_mm,
        "opex_mm": opex_mm,
        "expected_loss_mm": el_mm,
        "pretax_nii_mm": pretax_nii_mm,
        "tax_mm": tax_mm,
        "posttax_nii_mm": posttax_nii_mm,
        "roe": roe,
    }


def compute_roe_with_distribution(
    drawn_mm: float,
    margin_bps: int,
    fees_bps: int,
    ftp_rate: float,
    opex_mm: float,
    ead_mm: float,
    obligor_rating: str,
    product: str,
    capital_mm: float,
    facility_limit_mm: float,
    distribution_pct: float,
    distribution_fee_bps: int,
) -> dict:
    base = compute_roe(drawn_mm, margin_bps, fees_bps, ftp_rate, opex_mm,
                       ead_mm, obligor_rating, product, capital_mm)

    retained_pct = 1.0 - distribution_pct
    retained_drawn = drawn_mm * retained_pct
    distributed_limit = facility_limit_mm * distribution_pct
    retained_ead = ead_mm * retained_pct

    rw = RISK_WEIGHTS.get(obligor_rating, 1.00)
    retained_rwa = retained_ead * rw
    retained_capital = retained_rwa * 0.12

    fee_income = distributed_limit * distribution_fee_bps / 10_000

    margin = margin_bps / 10_000
    fee_rate = fees_bps / 10_000
    retained_gross_rev = retained_drawn * margin + retained_drawn * fee_rate
    retained_cof = retained_drawn * ftp_rate

    pd = PD.get(obligor_rating, 0.002)
    lgd = LGD_SECURED if product == "INVENTORY" else LGD_UNSECURED
    retained_el = retained_ead * pd * lgd
    retained_opex = opex_mm * retained_pct

    total_income = retained_gross_rev + fee_income - retained_cof - retained_opex - retained_el
    tax = max(total_income * TAX_RATE, 0.0)
    posttax_nii = total_income - tax
    retained_roe = posttax_nii / retained_capital if retained_capital > 0 else -999.0

    return {
        **base,
        "distributed_mm": distributed_limit,
        "fee_income_mm": fee_income,
        "retained_mm": facility_limit_mm * retained_pct,
        "retained_rwa_mm": retained_rwa,
        "retained_capital_mm": retained_capital,
        "retained_roe": retained_roe,
    }
