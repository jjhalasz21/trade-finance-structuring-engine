# TFSE Streamlit UI + Originate-to-Distribute Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add OtD distribution mechanics to the pricing engine and build a public Streamlit app for HSBC interview demos, with pre-generated demo clients and a live pipeline runner.

**Architecture:** OtD changes are additive — `compute_roe_with_distribution` sits alongside `compute_roe`, `Economics` gains 8 optional fields with defaults, and `run_pricing` grows two optional params. The Streamlit `app.py` imports engine functions directly and uses `run_pipeline_in_memory` (new orchestrator function) which runs all agents and returns artifact bytes from a temp directory. Demo artifacts for three clients live in `demo_outputs/` committed to the repo.

**Tech Stack:** Python 3.11, Streamlit ≥1.35, Anthropic SDK, ReportLab, openpyxl, Pydantic v2, pytest

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `src/tfse/constants.py` | Modify | Add `DISTRIBUTION_FEE_BPS` dict and `DISTRIBUTION_PCT_DEFAULT` |
| `src/tfse/models.py` | Modify | Add 8 OtD fields to `Economics` (all default `0.0`/`0`) |
| `src/tfse/finance/roe.py` | Modify | Add `compute_roe_with_distribution` alongside existing `compute_roe` |
| `src/tfse/agents/pricing.py` | Modify | Accept `distribution_pct`/`distribution_fee_bps`, populate OtD fields |
| `src/tfse/outputs/term_sheet_pdf.py` | Modify | Add conditional Distribution Structure table section |
| `src/tfse/orchestrator.py` | Modify | Add `run_pipeline_in_memory` returning artifact bytes |
| `pyproject.toml` | Modify | Add `streamlit>=1.35` dependency |
| `.gitignore` | Modify | Add `.streamlit/secrets.toml` |
| `tests/test_roe_distribution.py` | Create | Three unit tests for distribution RoE math |
| `tests/test_end_to_end.py` | Modify | Add distribution_pct=0.12 assertion |
| `app.py` | Create | Full Streamlit UI — two tabs, HSBC branding, pipeline runner |

---

## Task 1: Distribution constants + Economics OtD fields

**Files:**
- Modify: `src/tfse/constants.py`
- Modify: `src/tfse/models.py`

- [ ] **Step 1: Add distribution constants to `src/tfse/constants.py`**

Append to the bottom of the file:

```python
DISTRIBUTION_FEE_BPS: dict[str, int] = {
    "RF": 30,
    "SCF": 25,
    "INVENTORY": 35,
}
DISTRIBUTION_PCT_DEFAULT: float = 0.12
```

- [ ] **Step 2: Add OtD fields to `Economics` in `src/tfse/models.py`**

Replace the `Economics` class (currently ends at `sensitivity: list[SensitivityRow]`) with:

```python
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
    distribution_pct: float = 0.0
    distribution_fee_bps: int = 0
    distributed_mm: float = 0.0
    fee_income_mm: float = 0.0
    retained_mm: float = 0.0
    retained_rwa_mm: float = 0.0
    retained_capital_mm: float = 0.0
    retained_roe: float = 0.0
```

- [ ] **Step 3: Run existing tests to confirm no regressions**

```
cd C:\Users\jhala\OneDrive\Desktop\trade-finance-structuring-engine
pytest tests/ -v
```

Expected: all tests pass (new fields have defaults, no existing code broken).

- [ ] **Step 4: Commit**

```bash
git add src/tfse/constants.py src/tfse/models.py
git commit -m "feat: add distribution constants and OtD fields to Economics"
```

---

## Task 2: `compute_roe_with_distribution` (TDD)

**Files:**
- Create: `tests/test_roe_distribution.py`
- Modify: `src/tfse/finance/roe.py`

- [ ] **Step 1: Write failing tests in `tests/test_roe_distribution.py`**

```python
import pytest
from tfse.finance.roe import compute_roe, compute_roe_with_distribution

BASE = dict(
    drawn_mm=97.5,
    margin_bps=130,
    fees_bps=25,
    ftp_rate=0.002,
    opex_mm=0.15,
    ead_mm=130.0,
    obligor_rating="A",
    product="RF",
    capital_mm=7.8,
    facility_limit_mm=130.0,
)


def test_zero_distribution_matches_full_hold():
    full = compute_roe(**{k: v for k, v in BASE.items() if k != "facility_limit_mm"},)
    dist = compute_roe_with_distribution(**BASE, distribution_pct=0.0, distribution_fee_bps=0)
    for key in ("gross_revenue_mm", "cost_of_funds_mm", "expected_loss_mm",
                "pretax_nii_mm", "tax_mm", "posttax_nii_mm", "roe"):
        assert dist[key] == pytest.approx(full[key], rel=1e-6), f"mismatch on {key}"


def test_distribution_reduces_rwa():
    dist_pct = 0.12
    result = compute_roe_with_distribution(
        **BASE, distribution_pct=dist_pct, distribution_fee_bps=30
    )
    # retained_ead = 130.0 * 0.88 = 114.4; rw(A) = 0.50; retained_rwa = 57.2
    expected_retained_rwa = 130.0 * (1 - dist_pct) * 0.50
    assert result["retained_rwa_mm"] == pytest.approx(expected_retained_rwa, rel=1e-6)
    assert result["retained_capital_mm"] == pytest.approx(expected_retained_rwa * 0.12, rel=1e-6)


def test_fee_income_adds_to_nii():
    result = compute_roe_with_distribution(
        **BASE, distribution_pct=0.12, distribution_fee_bps=30
    )
    # fee_income = 130.0 * 0.12 * 30 / 10_000 = 0.0468
    expected_fee = 130.0 * 0.12 * 30 / 10_000
    assert result["fee_income_mm"] == pytest.approx(expected_fee, rel=1e-6)
    assert result["fee_income_mm"] > 0
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_roe_distribution.py -v
```

Expected: `ImportError: cannot import name 'compute_roe_with_distribution'`

- [ ] **Step 3: Implement `compute_roe_with_distribution` in `src/tfse/finance/roe.py`**

Add after the existing `compute_roe` function:

```python
from tfse.constants import PD, LGD_UNSECURED, LGD_SECURED, TAX_RATE, RISK_WEIGHTS


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
```

Note: the `from tfse.constants import ...` line at the top of roe.py already imports `PD, LGD_UNSECURED, LGD_SECURED, TAX_RATE`. Add `RISK_WEIGHTS` to that existing import line. Do not duplicate the import.

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/test_roe_distribution.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Run full suite to confirm no regressions**

```
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/test_roe_distribution.py src/tfse/finance/roe.py
git commit -m "feat: add compute_roe_with_distribution with OtD mechanics"
```

---

## Task 3: Update pricing agent to use distribution params

**Files:**
- Modify: `src/tfse/agents/pricing.py`

- [ ] **Step 1: Update `run_pricing` signature and body in `src/tfse/agents/pricing.py`**

Replace the entire file content with:

```python
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
```

- [ ] **Step 2: Run full test suite**

```
pytest tests/ -v
```

Expected: all tests pass (existing tests call `run_pricing(profile, structure)` with no distribution args — defaults kick in).

- [ ] **Step 3: Commit**

```bash
git add src/tfse/agents/pricing.py
git commit -m "feat: pricing agent accepts distribution_pct and distribution_fee_bps"
```

---

## Task 4: Term sheet PDF — Distribution Structure section

**Files:**
- Modify: `src/tfse/outputs/term_sheet_pdf.py`

- [ ] **Step 1: Add Distribution Structure table to `generate_term_sheet`**

In `src/tfse/outputs/term_sheet_pdf.py`, after the `Eligibility Criteria` section (after `elements.append(Spacer(1, 0.2*inch))` that follows the eligibility loop) and before the `Key Conditions Precedent` section, insert:

```python
    if economics.distribution_pct > 0:
        elements.append(Paragraph("Distribution Structure", h2))
        dist_data = [
            ["Parameter", "Details"],
            ["Structure", "Originate-to-Distribute"],
            ["HSBC Retained", f"{1 - economics.distribution_pct:.0%} of facility (${economics.retained_mm:.0f}M)"],
            ["Distributed to Investors", f"{economics.distribution_pct:.0%} of facility (${economics.distributed_mm:.0f}M)"],
            ["Arrangement Fee", f"{economics.distribution_fee_bps}bps p.a. on distributed amount"],
            ["Retained RoE", f"{economics.retained_roe:.1%}"],
        ]
        td = Table(dist_data, colWidths=[2.5 * inch, 4 * inch])
        td.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#CC0000")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(td)
        elements.append(Spacer(1, 0.2 * inch))
```

The insertion point is after this block in the current file:

```python
    elements.append(Paragraph("Eligibility Criteria", h2))
    for criterion in structure.eligible_criteria:
        elements.append(Paragraph(f"• {criterion}", normal))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("Key Conditions Precedent", h2))   # <-- insert BEFORE this line
```

- [ ] **Step 2: Run full test suite**

```
pytest tests/ -v
```

Expected: all tests pass. The existing test uses `_mock_economics()` which has `distribution_pct=0.0` (default), so the distribution section is skipped and the test is unaffected.

- [ ] **Step 3: Commit**

```bash
git add src/tfse/outputs/term_sheet_pdf.py
git commit -m "feat: term sheet PDF includes Distribution Structure section when distribution_pct > 0"
```

---

## Task 5: Extend end-to-end test for OtD

**Files:**
- Modify: `tests/test_end_to_end.py`

- [ ] **Step 1: Add distribution assertions to `test_output_generators_produce_artifacts`**

In `tests/test_end_to_end.py`, update `_mock_economics()` to include OtD fields, and add distribution assertions:

```python
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
```

Then at the end of `test_output_generators_produce_artifacts`, add:

```python
    assert economics.distribution_pct == 0.12
    assert economics.retained_roe > 0
    assert pdf_path.stat().st_size > 5000  # PDF should be non-trivial size with distribution section
```

- [ ] **Step 2: Run full test suite**

```
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test_end_to_end.py
git commit -m "test: extend end-to-end test to cover OtD distribution fields"
```

---

## Task 6: `run_pipeline_in_memory` in orchestrator

**Files:**
- Modify: `src/tfse/orchestrator.py`

- [ ] **Step 1: Add `run_pipeline_in_memory` to `src/tfse/orchestrator.py`**

Add the following imports at the top of the file (after existing imports):

```python
import tempfile
```

Then add this function after the existing `run` function:

```python
def run_pipeline_in_memory(
    raw: dict,
    distribution_pct: float = 0.12,
    distribution_fee_bps: int | None = None,
) -> tuple:
    """Run the full pipeline and return artifact bytes for Streamlit download buttons.

    Returns: (profile, diagnostic, structure, economics, pitch_text, pdf_bytes, xlsx_bytes, md_str, cme_dict)
    """
    profile = run_intake(raw)
    diagnostic = run_diagnostic(profile)
    structure = run_structuring(profile, diagnostic)
    economics = run_pricing(profile, structure, distribution_pct, distribution_fee_bps)
    bundle = PitchBundle(profile=profile, diagnostic=diagnostic, structure=structure, economics=economics)
    pitch_text = run_pitch(bundle)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        pdf_path = generate_term_sheet(profile, structure, economics, tmp / "term_sheet.pdf")
        xlsx_path = generate_profitability_model(structure, economics, tmp / "profitability_model.xlsx")
        cme_path = generate_cme_payload(profile, structure, economics, tmp / "cme_entry.json")

        pdf_bytes = pdf_path.read_bytes()
        xlsx_bytes = xlsx_path.read_bytes()
        cme_dict = json.loads(cme_path.read_text())

    return profile, diagnostic, structure, economics, pitch_text, pdf_bytes, xlsx_bytes, pitch_text, cme_dict
```

Note: `md_str` and `pitch_text` are the same value — the pitch deck markdown IS the pitch text. The tuple position for `md_str` is slot 7 (0-indexed), same content as slot 4.

- [ ] **Step 2: Run full test suite**

```
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/tfse/orchestrator.py
git commit -m "feat: add run_pipeline_in_memory for Streamlit in-memory artifact generation"
```

---

## Task 7: Streamlit dependency + secrets gitignore

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`

- [ ] **Step 1: Add streamlit to `pyproject.toml` dependencies**

In `pyproject.toml`, add `"streamlit>=1.35",` to the `dependencies` list:

```toml
dependencies = [
    "anthropic>=0.40.0",
    "pydantic>=2.0",
    "openpyxl>=3.1",
    "reportlab>=4.0",
    "rich>=13.0",
    "numpy>=1.26",
    "pandas>=2.0",
    "streamlit>=1.35",
]
```

- [ ] **Step 2: Add `.streamlit/secrets.toml` to `.gitignore`**

In `.gitignore`, add:

```
.streamlit/secrets.toml
```

- [ ] **Step 3: Install streamlit**

```
pip install streamlit>=1.35
```

Expected: installs without error.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml .gitignore
git commit -m "chore: add streamlit dependency and gitignore secrets"
```

---

## Task 8: Create `app.py`

**Files:**
- Create: `app.py` (project root)

- [ ] **Step 1: Create `app.py` with the full Streamlit UI**

Create `app.py` at the project root with the following content:

```python
import os
import json
import io
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="TFSE | HSBC GTS",
    page_icon="🏦",
    layout="wide",
)

HSBC_RED = "#DB0011"
st.markdown(f"""
<style>
.badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 0.78em;
    font-weight: bold;
    color: white;
    margin-bottom: 4px;
}}
.badge-rf {{ background-color: {HSBC_RED}; }}
.badge-scf {{ background-color: #E8A000; }}
.badge-inv {{ background-color: #1a73e8; }}
div[data-testid="stButton"] > button[kind="primaryFormSubmit"],
div[data-testid="stButton"] > button[kind="primary"] {{
    background-color: {HSBC_RED};
    border-color: {HSBC_RED};
    color: white;
}}
div[data-testid="stButton"] > button[kind="primaryFormSubmit"]:hover,
div[data-testid="stButton"] > button[kind="primary"]:hover {{
    background-color: #a30000;
    border-color: #a30000;
}}
</style>
""", unsafe_allow_html=True)

# --- API key
_api_key = None
try:
    _api_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    _api_key = os.environ.get("ANTHROPIC_API_KEY")

# --- Header
st.title("Trade Finance Structuring Engine")
st.caption("HSBC Global Transaction Services — Energy & Materials Desk")

# --- Demo client data (metrics hardcoded; update retained_roe/roe after running demo_outputs)
DEMO_CLIENTS = [
    {
        "name": "Gulf Coast Refining LLC",
        "slug": "gulf_coast_refining",
        "sector": "Energy — Downstream",
        "product": "RF",
        "facility_mm": 250,
        "margin": "SOFR+130bps",
        "roe": 0.101,
        "dist_pct": 0.12,
        "retained_roe": 0.138,
    },
    {
        "name": "Permian Pure Energy",
        "slug": "permian_pure_energy",
        "sector": "Energy — E&P",
        "product": "SCF",
        "facility_mm": 150,
        "margin": "SOFR+110bps",
        "roe": 0.102,
        "dist_pct": 0.12,
        "retained_roe": 0.130,
    },
    {
        "name": "Atlantic Metals Trading",
        "slug": "atlantic_metals_trading",
        "sector": "Materials — Metals",
        "product": "INVENTORY",
        "facility_mm": 100,
        "margin": "SOFR+160bps",
        "roe": 0.103,
        "dist_pct": 0.12,
        "retained_roe": 0.122,
    },
]

DEMO_DIR = Path("demo_outputs")


def _load_artifact(slug: str, filename: str) -> bytes | None:
    p = DEMO_DIR / slug / filename
    return p.read_bytes() if p.exists() else None


BADGE_CLASS = {"RF": "badge-rf", "SCF": "badge-scf", "INVENTORY": "badge-inv"}

# --- Tabs
tab_demo, tab_run = st.tabs(["Demo Clients", "Run New Client"])

# ───────────────────────────────────────────────
# TAB 1: Demo Clients
# ───────────────────────────────────────────────
with tab_demo:
    st.markdown(
        "*Pre-generated for Gulf Coast Refining LLC, Permian Pure Energy, and Atlantic Metals "
        "Trading — three real trade finance archetypes across Energy and Materials.*"
    )

    cols = st.columns(3)
    for col, client in zip(cols, DEMO_CLIENTS):
        with col:
            badge_cls = BADGE_CLASS.get(client["product"], "badge-rf")
            st.markdown(
                f'<span class="badge {badge_cls}">{client["product"]}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f"**{client['name']}**")
            st.caption(client["sector"])

            st.metric("Facility Limit", f"${client['facility_mm']}M")
            st.metric("Clearing Margin", client["margin"])
            st.metric("Full-Hold RoE", f"{client['roe']:.1%}")
            st.metric("Distribution", f"{client['dist_pct']:.0%}")
            st.metric("Retained RoE", f"{client['retained_roe']:.1%}")

            slug = client["slug"]
            pdf_bytes = _load_artifact(slug, "term_sheet.pdf")
            xlsx_bytes = _load_artifact(slug, "profitability_model.xlsx")
            md_bytes = _load_artifact(slug, "pitch_deck.md")
            json_bytes = _load_artifact(slug, "cme_entry.json")

            if pdf_bytes:
                st.download_button(
                    "Term Sheet (PDF)", data=pdf_bytes,
                    file_name=f"{slug}_term_sheet.pdf", mime="application/pdf",
                    key=f"pdf_{slug}",
                )
            else:
                st.caption("_Term sheet not yet generated_")

            if xlsx_bytes:
                st.download_button(
                    "Profitability Model (XLSX)", data=xlsx_bytes,
                    file_name=f"{slug}_model.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"xlsx_{slug}",
                )

            if md_bytes:
                st.download_button(
                    "Pitch Deck (MD)", data=md_bytes,
                    file_name=f"{slug}_pitch_deck.md", mime="text/markdown",
                    key=f"md_{slug}",
                )

            if json_bytes:
                st.download_button(
                    "CRM Entry (JSON)", data=json_bytes,
                    file_name=f"{slug}_cme.json", mime="application/json",
                    key=f"json_{slug}",
                )

# ───────────────────────────────────────────────
# TAB 2: Run New Client
# ───────────────────────────────────────────────
with tab_run:
    if _api_key:
        st.info(
            "Live run uses Claude Opus + Haiku via the Anthropic API (~60–90 seconds). "
            "A simplified client profile is used here — full engagements include obligor "
            "ratings, dilution history, and supplier details."
        )
    else:
        st.warning(
            "Add `ANTHROPIC_API_KEY` to Streamlit secrets to enable live runs. "
            "Contact the demo administrator for access."
        )

    with st.form("new_client"):
        with st.expander("Client Details", expanded=True):
            company_name = st.text_input("Company name", placeholder="e.g. Acme Energy Ltd")
            sector = st.selectbox(
                "Sector",
                ["Energy — Downstream", "Energy — E&P", "Materials — Metals",
                 "Materials — Mining", "Industrial", "Other"],
            )
            revenue = st.number_input("Revenue ($M)", min_value=1.0, step=50.0, value=500.0)
            wc_gap = st.number_input(
                "Working capital gap ($M)", min_value=1.0, step=10.0, value=80.0,
                help="Estimated gap between cash outflows and inflows over a 90-day cycle",
            )
            payment_terms = st.number_input(
                "Payment terms (days)", min_value=1, max_value=180, step=15, value=60
            )
            ar = st.number_input("AR balance ($M)", min_value=0.0, step=10.0, value=0.0,
                                 help="Leave 0 to skip")
            ap = st.number_input("AP balance ($M)", min_value=0.0, step=10.0, value=0.0,
                                 help="Leave 0 to skip")
            inventory = st.number_input("Inventory ($M)", min_value=0.0, step=10.0, value=0.0,
                                        help="Leave 0 to skip")
            off_bs = st.checkbox("Client prefers off-balance-sheet treatment")

        with st.expander("Distribution / OtD Settings", expanded=False):
            dist_pct_input = st.slider(
                "Distribution %", min_value=0, max_value=80, value=12, step=1,
                help="Fraction of facility distributed to third-party investors",
            )
            dist_fee_input = st.number_input(
                "Distribution fee (bps)", min_value=0, max_value=200, value=30, step=1,
                help="Annual fee earned on distributed amount. Default 30bps (RF); agent uses product-specific default if unchanged.",
            )

        submitted = st.form_submit_button(
            "Run Pipeline →",
            disabled=not bool(_api_key),
            type="primary",
        )

    if submitted and _api_key:
        os.environ["ANTHROPIC_API_KEY"] = _api_key

        raw = {
            "client_name": company_name,
            "sector": sector,
            "revenue_mm": float(revenue),
            "wc_gap_mm": float(wc_gap),
            "payment_terms_days": int(payment_terms),
            "ar_balance_mm": float(ar) if ar > 0 else None,
            "ap_balance_mm": float(ap) if ap > 0 else None,
            "inventory_mm": float(inventory) if inventory > 0 else None,
            "off_bs_appetite": bool(off_bs),
        }
        distribution_pct = dist_pct_input / 100.0
        distribution_fee_bps = int(dist_fee_input)

        try:
            with st.status("Running pipeline...", expanded=True) as pipeline_status:
                st.write("Intake agent — validating client data...")
                from tfse.agents.intake import run_intake
                profile = run_intake(raw)
                st.write(f"✓ Intake complete — {profile.client_name}")

                st.write("Diagnostic agent — identifying working capital pain point...")
                from tfse.agents.diagnostic import run_diagnostic
                diagnostic = run_diagnostic(profile)
                st.write(f"✓ Diagnostic: {diagnostic.pain_point.value}")

                st.write("Structuring agent — setting term-sheet parameters...")
                from tfse.agents.structuring import run_structuring
                structure = run_structuring(profile, diagnostic)
                st.write("✓ Structure defined")

                st.write("Pricing agent — computing RoE and clearing margin...")
                from tfse.agents.pricing import run_pricing
                economics = run_pricing(profile, structure, distribution_pct, distribution_fee_bps)
                st.write(
                    f"✓ Clearing margin: SOFR+{economics.clearing_margin_bps}bps | "
                    f"Full-Hold RoE: {economics.roe:.1%} | "
                    f"Retained RoE: {economics.retained_roe:.1%} "
                    f"({economics.distribution_pct:.0%} distributed)"
                )

                st.write("Pitch agent — drafting client narrative...")
                from tfse.agents.pitch import run_pitch
                from tfse.models import PitchBundle
                bundle = PitchBundle(profile=profile, diagnostic=diagnostic,
                                     structure=structure, economics=economics)
                pitch_text = run_pitch(bundle)
                st.write("✓ Pitch narrative drafted")

                st.write("Generating artifacts...")
                import tempfile
                from tfse.outputs.term_sheet_pdf import generate_term_sheet
                from tfse.outputs.profitability_xlsx import generate_profitability_model
                from tfse.outputs.cme_payload import generate_cme_payload

                with tempfile.TemporaryDirectory() as tmpdir:
                    from pathlib import Path as _Path
                    tmp = _Path(tmpdir)
                    pdf_path = generate_term_sheet(profile, structure, economics, tmp / "term_sheet.pdf")
                    xlsx_path = generate_profitability_model(structure, economics, tmp / "profitability_model.xlsx")
                    cme_path = generate_cme_payload(profile, structure, economics, tmp / "cme_entry.json")
                    pdf_bytes = pdf_path.read_bytes()
                    xlsx_bytes = xlsx_path.read_bytes()
                    cme_dict = json.loads(cme_path.read_text())

                pipeline_status.update(label="Pipeline complete!", state="complete", expanded=False)

            # Results
            st.subheader(f"Results — {profile.client_name}")

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Facility Limit", f"${economics.drawn_mm / 0.75:.0f}M")
            m2.metric("Product", diagnostic.pain_point.value)
            m3.metric("Clearing Margin", f"SOFR+{economics.clearing_margin_bps}bps")
            m4.metric("Full-Hold RoE", f"{economics.roe:.1%}")
            m5.metric("Retained RoE", f"{economics.retained_roe:.1%}")

            if economics.distribution_pct > 0:
                st.info(
                    f"{economics.distribution_pct:.0%} distributed to investors at "
                    f"{economics.distribution_fee_bps}bps arrangement fee. "
                    f"HSBC retains ${economics.retained_mm:.0f}M "
                    f"({1 - economics.distribution_pct:.0%}) on balance sheet."
                )

            slug_out = profile.client_name.lower().replace(" ", "_")
            dl1, dl2, dl3, dl4 = st.columns(4)
            with dl1:
                st.download_button(
                    "Term Sheet (PDF)", data=pdf_bytes,
                    file_name=f"{slug_out}_term_sheet.pdf", mime="application/pdf",
                )
            with dl2:
                st.download_button(
                    "Profitability Model (XLSX)", data=xlsx_bytes,
                    file_name=f"{slug_out}_model.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            with dl3:
                st.download_button(
                    "Pitch Deck (MD)", data=pitch_text.encode(),
                    file_name=f"{slug_out}_pitch_deck.md", mime="text/markdown",
                )
            with dl4:
                st.download_button(
                    "CRM Entry (JSON)", data=json.dumps(cme_dict, indent=2).encode(),
                    file_name=f"{slug_out}_cme.json", mime="application/json",
                )

        except Exception as exc:
            st.error(f"Pipeline error: {exc}")
            raise

# --- Footer
st.divider()
st.markdown(
    "<p style='color: grey; font-size: 0.8em; text-align: center;'>"
    "Indicative terms only. Not a commitment to lend. For internal demo purposes only."
    "</p>",
    unsafe_allow_html=True,
)
```

- [ ] **Step 2: Verify the app starts without import errors**

```
cd C:\Users\jhala\OneDrive\Desktop\trade-finance-structuring-engine
streamlit run app.py --server.headless true &
```

Wait 5 seconds, then check the terminal output for errors. Expected: no import errors, `You can now view your Streamlit app in your browser` message.

Kill the process (Ctrl+C) after confirming startup.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: Streamlit UI with Demo Clients tab and Run New Client tab"
```

---

## Task 9: Generate demo_outputs and commit

**Files:**
- Create: `demo_outputs/gulf_coast_refining/` (4 files)
- Create: `demo_outputs/permian_pure_energy/` (4 files)
- Create: `demo_outputs/atlantic_metals_trading/` (4 files)

- [ ] **Step 1: Create the `demo_outputs/` directory structure**

```bash
mkdir -p demo_outputs/gulf_coast_refining
mkdir -p demo_outputs/permian_pure_energy
mkdir -p demo_outputs/atlantic_metals_trading
```

- [ ] **Step 2: Run the pipeline for all three demo clients**

Ensure `ANTHROPIC_API_KEY` is set in your environment (or `.env` file), then:

```bash
cd C:\Users\jhala\OneDrive\Desktop\trade-finance-structuring-engine
python - <<'EOF'
import os, json, tempfile, shutil
from pathlib import Path
from tfse.orchestrator import _load_env, run_pipeline_in_memory

_load_env()

clients = [
    ("gulf_coast_refining", 0.12, 30),
    ("permian_pure_energy", 0.12, 25),
    ("atlantic_metals_trading", 0.12, 35),
]

for slug, dist_pct, dist_fee in clients:
    raw = json.loads(Path(f"clients/{slug}.json").read_text())
    profile, diagnostic, structure, economics, pitch_text, pdf_bytes, xlsx_bytes, md_str, cme_dict = \
        run_pipeline_in_memory(raw, distribution_pct=dist_pct, distribution_fee_bps=dist_fee)
    
    out = Path(f"demo_outputs/{slug}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "term_sheet.pdf").write_bytes(pdf_bytes)
    (out / "profitability_model.xlsx").write_bytes(xlsx_bytes)
    (out / "pitch_deck.md").write_text(md_str, encoding="utf-8")
    (out / "cme_entry.json").write_text(json.dumps(cme_dict, indent=2), encoding="utf-8")
    
    print(f"{slug}: RoE={economics.roe:.1%}, RetainedRoE={economics.retained_roe:.1%}, Margin=SOFR+{economics.clearing_margin_bps}bps")

print("Done.")
EOF
```

This takes ~3–5 minutes (3 full LLM pipeline runs).

- [ ] **Step 3: Verify all 12 artifacts exist**

```bash
ls demo_outputs/gulf_coast_refining/
ls demo_outputs/permian_pure_energy/
ls demo_outputs/atlantic_metals_trading/
```

Expected: each directory has `term_sheet.pdf`, `profitability_model.xlsx`, `pitch_deck.md`, `cme_entry.json`.

- [ ] **Step 4: Update hardcoded metrics in `app.py` with real values**

From the output of Step 2, take the actual `RoE` and `RetainedRoE` values and update the `DEMO_CLIENTS` list in `app.py`. For example, if gulf_coast printed `RoE=10.1%, RetainedRoE=13.8%`, update:

```python
"roe": 0.101,
"retained_roe": 0.138,
```

Similarly for the other two clients.

- [ ] **Step 5: Commit demo_outputs and updated metrics**

```bash
git add demo_outputs/ app.py
git commit -m "feat: add pre-generated demo artifacts for all three demo clients"
```

- [ ] **Step 6: Push to GitHub**

```bash
git push origin master
```

---

## Task 10: Deploy to Streamlit Community Cloud

This task is manual — instructions only, no code changes.

- [ ] **Step 1: Go to share.streamlit.io**

Sign in with your GitHub account (`jjhalasz21`).

- [ ] **Step 2: Create a new app**

- Click **New app**
- Repository: `jjhalasz21/trade-finance-structuring-engine`
- Branch: `master`
- Main file path: `app.py`
- Click **Deploy**

- [ ] **Step 3: Add the API key secret**

After the app deploys (may take 2–3 minutes):
- Click **⋮ (more)** → **Settings** → **Secrets**
- Paste: `ANTHROPIC_API_KEY = "sk-ant-YOUR-KEY-HERE"`
- Save

- [ ] **Step 4: Verify the app**

- Open the public URL on desktop and mobile
- Demo Clients tab: confirm all 3 clients show metrics and download buttons work
- Run New Client tab: confirm form renders and "Run Pipeline →" is active
- Footer: confirm "For internal demo purposes only" appears

---

## Acceptance Criteria Checklist

- [ ] `compute_roe_with_distribution(..., 0.0, 0)` produces identical output to `compute_roe(...)`
- [ ] At 12% distribution, `retained_capital_mm == rwa_mm × 0.12 × 0.88`
- [ ] At 12% distribution, `fee_income_mm == facility_limit_mm × 0.12 × fee_bps / 10_000`
- [ ] `retained_rwa_mm == rwa_mm × 0.88` (for 12% distribution, A-rated)
- [ ] All `test_roe_distribution.py` tests pass
- [ ] `streamlit run app.py` starts locally without errors
- [ ] Demo Clients tab shows all three clients with distribution metrics and working download buttons
- [ ] Run New Client tab form submits, shows live progress, produces four downloadable artifacts
- [ ] Distribution Parameters expander shows defaults; user can override fee bps
- [ ] With no API key, Run button is disabled with explanatory message
- [ ] Term sheet PDF includes Distribution Structure section when `distribution_pct > 0`
- [ ] Footer shows "For internal demo purposes only" on both tabs
- [ ] HSBC red (`#DB0011`) applied to badges and Run button
- [ ] App deployed to Streamlit Community Cloud and accessible via public URL on mobile
