from tfse.constants import ROE_HURDLE, FTP_RATE, OPEX
from tfse.finance.rwa import compute_rwa
from tfse.finance.roe import compute_roe


def find_clearing_margin(
    drawn_mm: float,
    limit_mm: float,
    product: str,
    committed: bool,
    obligor_rating: str,
    fees_bps: int,
    start_bps: int = 100,
    step_bps: int = 5,
    max_bps: int = 500,
) -> dict:
    rwa_result = compute_rwa(drawn_mm, limit_mm, product, committed, obligor_rating)
    opex_mm = OPEX[product] / 1_000_000

    for margin_bps in range(start_bps, max_bps + 1, step_bps):
        roe_result = compute_roe(
            drawn_mm=drawn_mm,
            margin_bps=margin_bps,
            fees_bps=fees_bps,
            ftp_rate=FTP_RATE,
            opex_mm=opex_mm,
            ead_mm=rwa_result["ead_mm"],
            obligor_rating=obligor_rating,
            product=product,
            capital_mm=rwa_result["capital_mm"],
        )
        if roe_result["roe"] >= ROE_HURDLE:
            headroom_bps = 0
            next_roe = roe_result["roe"]
            while next_roe >= ROE_HURDLE and margin_bps - step_bps >= start_bps:
                headroom_bps += step_bps
                next_roe_result = compute_roe(
                    drawn_mm=drawn_mm,
                    margin_bps=margin_bps - headroom_bps,
                    fees_bps=fees_bps,
                    ftp_rate=FTP_RATE,
                    opex_mm=opex_mm,
                    ead_mm=rwa_result["ead_mm"],
                    obligor_rating=obligor_rating,
                    product=product,
                    capital_mm=rwa_result["capital_mm"],
                )
                next_roe = next_roe_result["roe"]
            return {
                "clearing_margin_bps": margin_bps,
                "hurdle_headroom_bps": max(0, headroom_bps - step_bps),
                "roe_result": roe_result,
                "rwa_result": rwa_result,
            }
    raise ValueError(f"No clearing margin found up to {max_bps}bps")
