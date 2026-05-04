# TFSE Design Spec — 2026-04-28

## Overview

Trade Finance Structuring Engine (TFSE): a local Python CLI that ingests a client JSON intake file and runs a sequential multi-agent pipeline (Claude SDK) to produce four per-client artifacts — a PDF term sheet, an XLSX profitability model, a Markdown pitch deck, and a JSON CRM entry. Built as an interview demo for the HSBC AVP GTS Sales Manager role (Energy & Materials desk).

---

## 1. Project Location

`C:\Users\jhala\OneDrive\Desktop\trade-finance-structuring-engine\`

Standalone project — not integrated into the existing WAT framework repo.

---

## 2. Repository Layout

```
trade-finance-structuring-engine/
├── .env.example                        # ANTHROPIC_API_KEY=your_key_here
├── pyproject.toml                      # deps + [project.scripts] tfse entry point
├── clients/
│   ├── gulf_coast_refining.json
│   ├── permian_pure_energy.json
│   └── atlantic_metals_trading.json
├── src/tfse/
│   ├── __init__.py
│   ├── orchestrator.py                 # sequential pipeline runner + rich logging
│   ├── models.py                       # Pydantic v2: ClientProfile, DiagnosticReport,
│   │                                   #   Structure, Economics, PitchBundle
│   ├── agents/
│   │   ├── intake.py                   # validates raw JSON → ClientProfile (Haiku)
│   │   ├── diagnostic.py               # scores 5 WC axes → DiagnosticReport (Opus)
│   │   ├── structuring.py              # picks product + terms → Structure (Opus)
│   │   ├── pricing.py                  # calls finance modules → Economics (no LLM)
│   │   └── pitch.py                    # writes MD narrative (Haiku)
│   ├── finance/
│   │   ├── rwa.py                      # Basel III standardized RWA + capital
│   │   ├── roe.py                      # post-tax RoE waterfall
│   │   ├── advance_rate.py             # RF and inventory advance rate logic
│   │   ├── dilution.py                 # dilution reserve calculation
│   │   └── pricing_buildup.py          # margin iteration to clear RoE hurdle
│   ├── products/
│   │   ├── receivables_finance.py      # RF eligibility + sizing logic
│   │   ├── supply_chain_finance.py     # SCF discount + DPO extension logic
│   │   └── inventory_finance.py        # borrowing base + price haircut logic
│   ├── outputs/
│   │   ├── term_sheet_pdf.py           # 2-page reportlab PDF
│   │   ├── profitability_xlsx.py       # openpyxl with live Excel formulas
│   │   ├── pitch_deck_md.py            # structured markdown for Claude Design
│   │   └── cme_payload.py             # JSON CRM deal record
│   └── prompts/
│       ├── diagnostic.md
│       ├── structuring.md
│       └── pitch.md
├── tests/
│   ├── test_rwa.py
│   ├── test_roe.py
│   ├── test_advance_rate.py
│   └── test_end_to_end.py
├── outputs/                            # generated artifacts land here per client slug
└── docs/
    ├── architecture.md
    ├── trade_finance_primer.md
    └── interview_walkthrough.md
```

---

## 3. Entry Point

```
python -m tfse run clients/gulf_coast_refining.json
```

- `rich` progress panel shows each agent step as it runs
- On completion, prints artifact paths for all four outputs
- Runs in under 90 seconds per client

---

## 4. Data Models (Pydantic v2)

Five typed objects form the agent wire format:

| Model | Produced by | Consumed by |
|---|---|---|
| `ClientProfile` | Intake | Diagnostic |
| `DiagnosticReport` | Diagnostic | Structuring |
| `Structure` | Structuring | Pricing, Pitch |
| `Economics` | Pricing | Pitch |
| `PitchBundle` | orchestrator (assembles all) | Pitch |

Key fields:
- `ClientProfile`: revenue, AR/AP aging, obligor concentration, top-5 obligors + ratings, WC gap, banking relationships, sector, off-BS appetite flag
- `DiagnosticReport`: pain_point (enum: RF / SCF / INVENTORY), scores dict (5 axes), recommendation_rationale (str)
- `Structure`: product, facility_limit, advance_rate, dilution_reserve, recourse (bool), committed (bool), eligible_criteria (list), pricing_components (dict)
- `Economics`: gross_revenue, cost_of_funds, opex, expected_loss, pretax_nii, tax, posttax_nii, rwa, capital, roe, clearing_margin_bps, hurdle_headroom_bps, sensitivity_table
- `PitchBundle`: all four above

---

## 5. Agent Pipeline

Sequential execution in `orchestrator.py`. Each agent is a plain Python function.

### 5.1 Intake Agent — `claude-haiku-4-5-20251001`
- Input: raw client JSON dict
- Validates required fields, normalises units (e.g. revenue in $M), flags missing data
- Output: `ClientProfile`

### 5.2 Diagnostic Agent — `claude-opus-4-7`
- Input: `ClientProfile`
- Scores client on 5 axes: cash conversion cycle stress, obligor concentration, supplier criticality, inventory days, off-BS appetite
- Picks primary pain point and product recommendation with written rationale
- Output: `DiagnosticReport`
- `temperature=0` for reproducibility

### 5.3 Structuring Agent — `claude-opus-4-7`
- Input: `DiagnosticReport` + `ClientProfile`
- Selects product (RF / SCF / INVENTORY), sets all term-sheet parameters
- Calls product module for eligibility logic; agent fills narrative fields
- Output: `Structure`
- `temperature=0`

### 5.4 Pricing Agent — no LLM
- Input: `Structure` + `ClientProfile`
- Calls `rwa.py`, `roe.py`, `advance_rate.py`, `dilution.py`, `pricing_buildup.py` directly
- `pricing_buildup.py` iterates margin in 5bps steps until post-tax RoE ≥ 12%
- Output: `Economics`

### 5.5 Pitch Agent — `claude-haiku-4-5-20251001`
- Input: `PitchBundle`
- Drafts client-facing narrative sections for the markdown pitch deck
- Output: structured markdown string (8 sections matching slide order)

---

## 6. Deterministic Finance Modules

### `rwa.py` — Basel III Standardized
```
EAD    = drawn + (limit × CCF)
RWA    = EAD × RiskWeight[obligor_rating][product_type]
Capital = RWA × 0.12

CCF table:   committed RF = 100%
             uncommitted SCF = 20%
             inventory = 50%

Risk weights: AAA=20%, AA=20%, A=50%, BBB=100%, BB=100%, <BB=150%
```

### `roe.py` — Post-Tax Waterfall
```
Gross Revenue    = drawn × margin + fees
− Cost of Funds  = drawn × FTP_rate
− OpEx           = product_fixed_allocation
− Expected Loss  = EAD × PD × LGD
= Pre-tax NII
− Tax            = pre-tax × 0.25
= Post-tax NII
÷ Capital        = RoE
```

### `advance_rate.py`
- RF: 80–90% based on weighted-average obligor rating (IG mix → higher rate)
- Inventory: LME copper 70%, LME aluminum 65%; both subject to 1-day LME price haircut

### `dilution.py`
- Reserve = rolling_12m_dilution_rate × 2.0 multiplier
- Subtracted from gross eligible AR to get net eligible base

### `pricing_buildup.py`
- Starts at SOFR + 100bps; steps up in 5bps increments
- Returns first margin where post-tax RoE ≥ 12% hurdle
- Also returns headroom bps (distance to 12% at clearing margin)

---

## 7. Product Modules

Each module encodes the eligibility rules for its product type and is called by the Structuring agent to compute the eligible pool size before Claude fills in the narrative.

- `receivables_finance.py`: invoice tenor ≤ 120 days, obligor on approved list, no concentration breach (single obligor cap 25%, sector cap 40%), no disputed invoices, approved CCY
- `supply_chain_finance.py`: invoice approved by anchor, supplier onboarded, tenor ≤ anchor-extended terms; discount formula = face × (days/360) × discount_rate
- `inventory_finance.py`: commodity in LME-approved warehouse, HSBC-controlled warehouse receipt, hedgeable on recognised exchange; advance = MTM_price × (1 − haircut) × advance_rate

---

## 8. Outputs (per client, written to `outputs/<client_slug>/`)

| File | Format | Generator | Notes |
|---|---|---|---|
| `term_sheet.pdf` | PDF | reportlab | 2-page: facility summary + eligibility/CP |
| `profitability_model.xlsx` | XLSX | openpyxl | Live Excel formulas; sensitivity table |
| `pitch_deck.md` | Markdown | plain Python | 8 sections; fed to Claude Design for styling |
| `cme_entry.json` | JSON | `cme_payload.py` | Mock CRM record |

### Pitch deck markdown sections (8)
1. Cover (client name, date, proposed solution headline)
2. Executive Summary (3 bullets)
3. Client Diagnostic (WC pain point, scoring rationale)
4. Proposed Solution (product, structure, why this product)
5. Illustrative Economics (RoE waterfall summary, key metrics)
6. Structure Diagram (text-based flowchart: client → HSBC → obligors/suppliers)
7. Indicative Terms (table: limit, advance rate, pricing, tenor, recourse)
8. Next Steps (3 bullets: KYC, term sheet, credit approval)

### Profitability XLSX layout
- **Inputs block** (rows 1–10): drawn balance, facility limit, margin bps, FTP rate, tax rate — all editable cells
- **RoE waterfall** (rows 12–22): formulas referencing inputs; RoE in a highlighted cell
- **RWA/Capital block** (rows 24–30): EAD, RWA, allocated capital
- **Sensitivity table** (rows 32–40): RoE at 60/75/90% utilization × margin ±25bps

---

## 9. Three Demo Clients

| Client | Product | Facility | Key Driver |
|---|---|---|---|
| Gulf Coast Refining LLC | Non-recourse RF | $250M committed | IG obligor concentration; off-BS appetite |
| Permian Pure Energy | Payables SCF | $150M uncommitted | DPO extension; anchor credit pull-through |
| Atlantic Metals Trading | Inventory/BBF | $100M uncommitted | LME-quality copper/aluminum; contango trade |

Each client JSON includes: revenue, AR/AP aging buckets, top-5 obligors with ratings, WC gap, banking relationships, sector, off-BS appetite flag, dilution history, inventory details (for Client 3), supplier list (for Client 2).

---

## 10. Dependencies

```toml
[project]
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40.0",
    "pydantic>=2.0",
    "openpyxl>=3.1",
    "reportlab>=4.0",
    "rich>=13.0",
    "numpy>=1.26",
    "pandas>=2.0",
]
```

No `python-pptx`. No `weasyprint`. No `firecrawl`.

---

## 11. Models Used

| Agent | Model | Reason |
|---|---|---|
| Intake | `claude-haiku-4-5-20251001` | Schema validation — speed/cost |
| Diagnostic | `claude-opus-4-7` | Judgment: pain point ranking |
| Structuring | `claude-opus-4-7` | Judgment: product selection + terms |
| Pricing | none | Deterministic finance math |
| Pitch | `claude-haiku-4-5-20251001` | Text drafting — speed/cost |

All Claude calls use `temperature=0`. Model IDs pinned in a `constants.py`.

`constants.py` also holds hardcoded internal cost assumptions used by the Pricing agent — these represent illustrative HSBC desk defaults and are not user-supplied:
- `FTP_RATE`: 5.35% (SOFR proxy)
- `PD` per rating bucket: AAA=0.01%, A=0.05%, BBB=0.20%, BB=1.00%
- `LGD`: 45% (Basel foundation LGD for unsecured; 40% for secured inventory)
- `OPEX_ALLOCATION`: RF=$150k/yr, SCF=$100k/yr, Inventory=$200k/yr
- `TAX_RATE`: 25%
- `ROE_HURDLE`: 12%

---

## 12. Testing

- `test_rwa.py`: CCF table, risk-weight lookups, capital calculation
- `test_roe.py`: waterfall arithmetic, edge cases (zero utilization, max utilization)
- `test_advance_rate.py`: RF rating-mix scenarios, inventory haircut scenarios
- `test_end_to_end.py`: runs full pipeline on all three client JSONs, asserts output files exist and Economics.roe > 0

---

## 13. Acceptance Criteria

- [ ] `python -m tfse run clients/gulf_coast_refining.json` produces 4 artifacts in `outputs/` in under 90 seconds
- [ ] Same command works for `permian_pure_energy.json` and `atlantic_metals_trading.json`
- [ ] Each client gets a different product recommendation
- [ ] XLSX has live Excel formulas — changing drawn balance updates RoE
- [ ] Pitch deck markdown has 8 sections, no Lorem Ipsum
- [ ] All unit tests pass
- [ ] README has elevator pitch, architecture summary, and "run it" section with API key setup instructions
