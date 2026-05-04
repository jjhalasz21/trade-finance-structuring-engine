# TFSE Streamlit UI + OtD Design Spec — 2026-05-04

## Overview

Two parallel additions to the Trade Finance Structuring Engine:

1. **Originate-to-Distribute (OtD) mechanics** — extend the core pricing engine to model distribution of the originated asset to third-party investors, with distribution % and fee configurable per deal
2. **Streamlit web app** (`app.py`) — a public Streamlit Community Cloud UI for the HSBC interview panel, showing pre-generated demo results and a live pipeline runner with OtD inputs

The existing CLI (`python -m tfse run`) is unchanged. The Streamlit app imports the same engine functions directly.

---

## 1. Goals

- Pricing engine accurately models retained vs. distributed economics (RoE on retained capital only)
- Interviewers can browse pre-generated artifacts for all three demo clients without an API key
- Interviewers can run the live pipeline against a new client via a short form (~60–90 seconds)
- OtD parameters (distribution %, fee bps) are visible and adjustable in the UI
- Deployed to Streamlit Community Cloud; accessible from mobile browser
- HSBC-branded, professional, no Lorem Ipsum, no placeholder content

---

## 2. OtD Core Engine Changes

### 2.1 Economics Model — new fields

Add to `src/tfse/models.py` `Economics`:

```python
distribution_pct: float = 0.0        # fraction of facility distributed (0.0–0.80)
distribution_fee_bps: int = 0         # annual fee bps earned on distributed amount
distributed_mm: float = 0.0           # facility_limit_mm × distribution_pct
fee_income_mm: float = 0.0            # distributed_mm × distribution_fee_bps / 10_000
retained_mm: float = 0.0              # facility_limit_mm × (1 − distribution_pct)
retained_rwa_mm: float = 0.0          # RWA on retained slice only
retained_capital_mm: float = 0.0      # retained_rwa_mm × 0.12
retained_roe: float = 0.0             # post-tax NII (retained + fee) ÷ retained_capital_mm
```

`roe` (existing field) remains the full-hold RoE for reference. `retained_roe` is the distributed-structure RoE shown in the UI.

### 2.2 Distribution fee defaults — `src/tfse/constants.py`

```python
DISTRIBUTION_FEE_BPS: dict[str, int] = {
    "RF": 30,
    "SCF": 25,
    "INVENTORY": 35,
}
DISTRIBUTION_PCT_DEFAULT: float = 0.12   # 12%
```

### 2.3 RoE with distribution — `src/tfse/finance/roe.py`

New function `compute_roe_with_distribution(...)` (existing `compute_roe` unchanged):

```
retained_drawn    = drawn_mm × (1 − distribution_pct)
distributed_limit = facility_limit_mm × distribution_pct
retained_ead      = full_ead × (1 − distribution_pct)
retained_rwa      = retained_ead × risk_weight
retained_capital  = retained_rwa × 0.12

fee_income        = distributed_limit × distribution_fee_bps / 10_000

retained_gross_rev = retained_drawn × margin_bps/10_000 + retained_drawn × fees_bps/10_000
retained_cof       = retained_drawn × ftp_rate
retained_el        = retained_ead × PD × LGD
retained_opex      = opex_mm × (1 − distribution_pct)   # opex scales with retained share

total_income       = retained_gross_rev + fee_income − retained_cof − retained_opex − retained_el
tax                = max(total_income × TAX_RATE, 0.0)
posttax_nii        = total_income − tax
retained_roe       = posttax_nii / retained_capital  (if retained_capital > 0 else −999.0)
```

Returns the same dict shape as `compute_roe` plus the new fields above.

### 2.4 Pricing agent — `src/tfse/agents/pricing.py`

Accept two new parameters: `distribution_pct: float` and `distribution_fee_bps: int`. Pass them through to `compute_roe_with_distribution`. Populate all new `Economics` fields. Default values come from `constants.py` if not supplied.

### 2.5 Term sheet PDF — `src/tfse/outputs/term_sheet_pdf.py`

If `economics.distribution_pct > 0`, add a **Distribution Structure** section to page 2:

| Label | Value |
|---|---|
| Structure | Originate-to-Distribute |
| HSBC Retained | `{(1−dist_pct):.0%}` of facility |
| Distributed to Investors | `{dist_pct:.0%}` of facility (`${distributed_mm:.0f}M`) |
| Arrangement Fee | `{distribution_fee_bps}bps` p.a. on distributed amount |
| Retained RoE | `{retained_roe:.1%}` |

If `distribution_pct == 0`, section is omitted.

---

## 3. File Structure Changes

```
trade-finance-structuring-engine/
├── app.py                              ← NEW: Streamlit entry point
├── demo_outputs/                       ← NEW: committed pre-generated artifacts
│   ├── gulf_coast_refining/
│   │   ├── term_sheet.pdf
│   │   ├── profitability_model.xlsx
│   │   ├── pitch_deck.md
│   │   └── cme_entry.json
│   ├── permian_pure_energy/
│   │   ├── term_sheet.pdf
│   │   ├── profitability_model.xlsx
│   │   ├── pitch_deck.md
│   │   └── cme_entry.json
│   └── atlantic_metals_trading/
│       ├── term_sheet.pdf
│       ├── profitability_model.xlsx
│       ├── pitch_deck.md
│       └── cme_entry.json
├── .streamlit/
│   └── secrets.toml                    ← gitignored; local dev only
│                                          ANTHROPIC_API_KEY = "sk-ant-..."
└── ... (all existing files unchanged)
```

`streamlit>=1.35` added to `pyproject.toml` dependencies. `demo_outputs/` committed to git. `.streamlit/secrets.toml` added to `.gitignore`.

---

## 4. Page Chrome

```python
st.set_page_config(
    page_title="TFSE | HSBC GTS",
    page_icon="🏦",
    layout="wide",
)
```

**Header** (top of page):
- Title: `Trade Finance Structuring Engine`
- Subtitle: `HSBC Global Transaction Services — Energy & Materials Desk`

**Footer** (bottom of page):
- `Indicative terms only. Not a commitment to lend. For internal demo purposes only.`
- Grey, small font, separator line above

**HSBC red** (`#DB0011`) applied via `st.markdown` CSS injection to:
- Product type badges (RF / SCF / INVENTORY pills)
- Primary action button (Run Pipeline →)

---

## 5. Tab Layout

Two tabs: `st.tabs(["Demo Clients", "Run New Client"])`.

---

## 6. Demo Clients Tab

Three `st.columns(3)` — one per demo client. On mobile these stack vertically (Streamlit default).

Section intro text:
> *Pre-generated for Gulf Coast Refining LLC, Permian Pure Energy, and Atlantic Metals Trading — three real trade finance archetypes across Energy and Materials.*

Each column contains:

| Element | Detail |
|---|---|
| Product badge | Coloured pill: RF (red) / SCF (amber) / INVENTORY (blue) |
| Client name | Bold |
| Sector | Grey subtext |
| Metrics strip | `st.metric` × 5: Facility Limit ($M), Clearing Margin (SOFR+Xbps), Full-Hold RoE (%), Distribution (%), Retained RoE (%) |
| Download buttons | `st.download_button` × 4: Term Sheet (PDF), Profitability Model (XLSX), Pitch Deck (MD), CRM Entry (JSON) |

Metrics are hardcoded from the pre-generated runs. Artifact bytes are read from `demo_outputs/{slug}/` at app startup.

### Demo client metadata (hardcoded)

| Client | Slug | Product | Facility | Margin | Full-Hold RoE | Dist % | Retained RoE |
|---|---|---|---|---|---|---|---|
| Gulf Coast Refining LLC | gulf_coast_refining | RF | $250M | SOFR+130bps | ~10% | 12% | ~14% |
| Permian Pure Energy | permian_pure_energy | SCF | $150M | SOFR+110bps | ~10% | 12% | ~13% |
| Atlantic Metals Trading | atlantic_metals_trading | INVENTORY | $100M | SOFR+160bps | ~10% | 12% | ~12% |

*(Exact values populated from actual pipeline run before deployment)*

---

## 7. Run New Client Tab

### 7.1 Info Banner

Grey `st.info` box at tab top:
> *Live run uses Claude Opus + Haiku via the Anthropic API (~60–90 seconds). A simplified client profile is used here — full engagements include obligor ratings, dilution history, and supplier details.*

If `ANTHROPIC_API_KEY` is absent from both `st.secrets` and `os.environ`:
> *Add `ANTHROPIC_API_KEY` to Streamlit secrets to enable live runs.*
Run button disabled.

### 7.2 Intake Form

`st.form("new_client")` split into two `st.expander` sections:

**Client Details** (always expanded):

| Field | Widget | Notes |
|---|---|---|
| Company name | `st.text_input` | Required |
| Sector | `st.selectbox` | Energy — Downstream, Energy — E&P, Materials — Metals, Materials — Mining, Industrial, Other |
| Revenue ($M) | `st.number_input` | min=1, step=50 |
| Working capital gap ($M) | `st.number_input` | min=1, step=10; help="Estimated gap between cash outflows and inflows over a 90-day cycle" |
| Payment terms (days) | `st.number_input` | min=1, max=180, step=15 |
| AR balance ($M) | `st.number_input` | Optional; leave 0 to skip |
| AP balance ($M) | `st.number_input` | Optional; leave 0 to skip |
| Inventory ($M) | `st.number_input` | Optional; leave 0 to skip |
| Off-balance sheet appetite | `st.checkbox` | "Client prefers off-balance-sheet treatment" |

**Distribution Parameters** (collapsed by default, label: "Distribution / OtD Settings"):

| Field | Widget | Default | Notes |
|---|---|---|---|
| Distribution % | `st.slider` | 12% | min=0, max=80, step=1 |
| Distribution fee (bps) | `st.number_input` | Product-dependent (RF=30, SCF=25, INV=35) | Populated after product is known; user can override |

*Note: distribution fee default cannot be product-aware until the pipeline runs. Use RF=30bps as the form default; the agent recalculates with the correct product default if the user leaves it unchanged. If user edits the fee field, that value is used as-is.*

Submit button: **Run Pipeline →** (HSBC red)

### 7.3 Pipeline Progress

On submit, `st.status` container shows each agent step in real time:

```
⟳  Intake agent — validating client data...
✓  Intake complete
⟳  Diagnostic agent — identifying working capital pain point...
✓  Diagnostic: RF
⟳  Structuring agent — setting term-sheet parameters...
✓  Structure defined
⟳  Pricing agent — computing RoE and clearing margin...
✓  Clearing margin: SOFR+130bps | Full-Hold RoE: 10.1% | Retained RoE: 13.8% (12% distributed)
⟳  Pitch agent — drafting client narrative...
✓  Pitch narrative drafted
```

Collapses to green "Complete" bar when done.

### 7.4 Results

After completion:

- **Headline metrics row** — `st.metric` × 5: Facility Limit, Product, Clearing Margin, Full-Hold RoE, Retained RoE
- **OtD callout** (if `distribution_pct > 0`) — `st.info` box:
  > *{distribution_pct:.0%} distributed to investors at {distribution_fee_bps}bps arrangement fee. HSBC retains ${retained_mm:.0f}M ({(1−distribution_pct):.0%}) on balance sheet.*
- **Four download buttons** — Term Sheet (PDF), Profitability Model (XLSX), Pitch Deck (MD), CRM Entry (JSON)

Artifacts generated in memory via `run_pipeline(raw, distribution_pct, distribution_fee_bps) -> tuple` returning `(profile, diagnostic, structure, economics, pitch_text, pdf_bytes, xlsx_bytes, md_str, cme_dict)`. Output generators use `io.BytesIO` instead of file paths.

---

## 8. API Key Handling

Priority order:
1. `st.secrets["ANTHROPIC_API_KEY"]`
2. `os.environ["ANTHROPIC_API_KEY"]`

Checked at app startup. Absent → Run tab shows disabled banner.

For Streamlit Community Cloud: add key in app Settings → Secrets. Never committed to repo.

---

## 9. Dependencies

Add to `pyproject.toml`:
```toml
"streamlit>=1.35",
```

Add to `.gitignore`:
```
.streamlit/secrets.toml
```

---

## 10. Testing

New tests in `tests/`:

- `test_roe_distribution.py`:
  - `test_distribution_reduces_rwa`: retained_rwa = full_rwa × (1 − dist_pct)
  - `test_fee_income_adds_to_nii`: fee_income_mm > 0 when distribution_pct > 0
  - `test_zero_distribution_matches_full_hold`: `compute_roe_with_distribution(..., 0.0, 0)` == `compute_roe(...)`

- `test_end_to_end.py`: extend existing test to pass `distribution_pct=0.12` and assert `economics.retained_roe > economics.roe`

---

## 11. Deployment Steps (post-implementation)

1. Push repo to GitHub
2. Go to share.streamlit.io → New app → select repo → `app.py`
3. In app Settings → Secrets, add: `ANTHROPIC_API_KEY = "sk-ant-..."`
4. Generate demo artifacts locally (`python -m tfse run` for all 3 clients into `demo_outputs/`)
5. Commit `demo_outputs/` to repo
6. Share the public URL

---

## 12. Acceptance Criteria

- [ ] `compute_roe_with_distribution(..., 0.0, 0)` produces identical output to `compute_roe(...)`
- [ ] At 12% distribution, `retained_capital_mm == rwa_mm × 0.12 × 0.88` (capital relief confirmed)
- [ ] At 12% distribution, `fee_income_mm == facility_limit_mm × 0.12 × fee_bps / 10_000`
- [ ] `retained_rwa_mm == rwa_mm × 0.88` (for 12% distribution)
- [ ] All new `test_roe_distribution.py` tests pass
- [ ] `streamlit run app.py` starts locally without errors
- [ ] Demo Clients tab shows all three clients with distribution metrics and working download buttons
- [ ] Run New Client tab form submits, shows live progress with OtD step, and produces four downloadable artifacts
- [ ] Distribution Parameters expander shows correct defaults; user can override fee bps
- [ ] With no API key set, Run button is disabled with explanatory message
- [ ] Term sheet PDF includes Distribution Structure section when distribution_pct > 0
- [ ] Footer shows "For internal demo purposes only" on both tabs
- [ ] HSBC red (`#DB0011`) applied to badges and Run button
- [ ] App deployed to Streamlit Community Cloud and accessible via public URL on mobile
