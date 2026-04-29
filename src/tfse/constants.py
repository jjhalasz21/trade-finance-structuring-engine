import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

MODEL_OPUS = "claude-opus-4-7"
MODEL_HAIKU = "claude-haiku-4-5-20251001"

ROE_HURDLE = 0.12
TAX_RATE = 0.25
FTP_RATE = 0.0535  # SOFR proxy

# Basel III CCF by product + commitment
CCF = {
    "RF_COMMITTED": 1.00,
    # "RF_UNCOMMITTED": 0.20,  # not supported in this version
    "SCF_UNCOMMITTED": 0.20,
    "INVENTORY_UNCOMMITTED": 0.50,
}

# Risk weights by rating bucket (standardized approach)
RISK_WEIGHTS = {
    "AAA": 0.20, "AA": 0.20, "A": 0.50,
    "BBB": 1.00, "BB": 1.00, "B": 1.50, "CCC": 1.50,
}

# PD by rating bucket
PD = {
    "AAA": 0.0001, "AA": 0.0002, "A": 0.0005,
    "BBB": 0.0020, "BB": 0.0100, "B": 0.0500, "CCC": 0.1500,
}

LGD_UNSECURED = 0.45
LGD_SECURED = 0.40

OPEX = {
    "RF": 150_000,
    "SCF": 100_000,
    "INVENTORY": 200_000,
}

ADVANCE_RATE_RF = {
    "AAA": 0.90, "AA": 0.90, "A": 0.87,
    "BBB": 0.85, "BB": 0.80,
    # B and CCC rated obligors are not eligible for RF facilities
}
ADVANCE_RATE_INVENTORY = {
    "LME_COPPER": 0.70,
    "LME_ALUMINUM": 0.65,
}
INVENTORY_HAIRCUT_DAYS = 1  # number of LME price days for liquidation haircut; product module uses 0.01 (1%) as proxy
