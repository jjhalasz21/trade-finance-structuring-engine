from tfse.constants import PD, LGD_UNSECURED, LGD_SECURED, TAX_RATE


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
