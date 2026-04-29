from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field


class ProductType(str, Enum):
    RF = "RF"
    SCF = "SCF"
    INVENTORY = "INVENTORY"


class Obligor(BaseModel):
    name: str
    rating: str  # AAA / AA / A / BBB / BB / B / CCC
    exposure_pct: float  # share of total AR or AP


class ClientProfile(BaseModel):
    client_name: str
    sector: str
    revenue_mm: float
    ar_balance_mm: float | None = None
    ap_balance_mm: float | None = None
    top_obligors: list[Obligor] = Field(default_factory=list)
    wc_gap_mm: float
    payment_terms_days: int
    off_bs_appetite: bool = False
    banking_relationships: list[str] = Field(default_factory=list)
    dilution_rate_pct: float = 2.0
    inventory_mm: float | None = None
    inventory_commodities: list[str] = Field(default_factory=list)
    supplier_count: int | None = None
    dpo_current_days: int | None = None
    dpo_target_days: int | None = None


class DiagnosticReport(BaseModel):
    pain_point: ProductType
    scores: dict[str, float]
    recommendation_rationale: str
    eligible_pool_mm: float


class Structure(BaseModel):
    product: ProductType
    facility_limit_mm: float
    advance_rate: float
    dilution_reserve: float
    recourse: bool
    committed: bool
    eligible_criteria: list[str]
    pricing_sofr_spread_bps: int
    fees_bps: int
    tenor_days: int
    structure_rationale: str


class SensitivityRow(BaseModel):
    utilization_pct: float
    margin_bps: int
    roe: float


class Economics(BaseModel):
    drawn_mm: float
    gross_revenue_mm: float
    cost_of_funds_mm: float
    opex_mm: float
    expected_loss_mm: float
    pretax_nii_mm: float
    tax_mm: float
    posttax_nii_mm: float
    rwa_mm: float
    capital_mm: float
    roe: float
    clearing_margin_bps: int
    hurdle_headroom_bps: int
    sensitivity: list[SensitivityRow]


class PitchBundle(BaseModel):
    profile: ClientProfile
    diagnostic: DiagnosticReport
    structure: Structure
    economics: Economics
