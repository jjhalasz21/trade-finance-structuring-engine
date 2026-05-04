# TFSE Streamlit UI Design Spec — 2026-05-04

## Overview

Add a Streamlit web app (`app.py`) to the existing Trade Finance Structuring Engine so the HSBC interview panel can use it independently via a public Streamlit Community Cloud URL. The app surfaces the three pre-generated demo clients and allows a live pipeline run via a minimal intake form.

The existing CLI (`python -m tfse run`) is unchanged. The Streamlit app imports the same orchestrator functions directly.

---

## 1. Goals

- Interviewers can browse pre-generated artifacts for all three demo clients without an API key
- Interviewers can run the live pipeline against a new client via a short form (~60–90 seconds)
- Deployed to Streamlit Community Cloud; accessible from mobile browser
- HSBC-branded, professional, no Lorem Ipsum, no placeholder content

---

## 2. File Structure Changes

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

## 3. Page Chrome

```python
st.set_page_config(
    page_title="TFSE | HSBC GTS",
    page_icon="🏦",
    layout="wide",
)
```

**Header** (top of every page):
- Title: `Trade Finance Structuring Engine`
- Subtitle: `HSBC Global Transaction Services — Energy & Materials Desk`

**Footer** (bottom of every page):
- `Indicative terms only. Not a commitment to lend. For internal demo purposes only.`
- Grey, small font, separator line above

**HSBC red** (`#DB0011`) applied via `st.markdown` CSS injection to:
- Product type badges (RF / SCF / INVENTORY pills)
- Primary action buttons (Run Pipeline)

---

## 4. Tab Layout

Two tabs rendered with `st.tabs(["Demo Clients", "Run New Client"])`.

---

## 5. Demo Clients Tab

Three `st.columns(3)` — one per demo client. On mobile these stack vertically (Streamlit default).

Section intro text:
> *Pre-generated for Gulf Coast Refining LLC, Permian Pure Energy, and Atlantic Metals Trading — three real trade finance archetypes across Energy and Materials.*

Each column contains:

| Element | Detail |
|---|---|
| Product badge | Coloured pill: RF (red) / SCF (amber) / INVENTORY (blue) |
| Client name | Bold, e.g. "Gulf Coast Refining LLC" |
| Sector | Grey subtext, e.g. "Energy — Downstream / Refining" |
| Metrics strip | Three `st.metric` widgets: Facility Limit ($M), Clearing Margin (SOFR+Xbps), RoE (%) |
| Download buttons | `st.download_button` × 4: Term Sheet (PDF), Profitability Model (XLSX), Pitch Deck (MD), CRM Entry (JSON) |

Metrics are hardcoded from the pre-generated runs — no live computation needed. Artifact bytes are read from `demo_outputs/{slug}/` at app startup.

### Demo client metadata (hardcoded)

| Client | Slug | Product | Facility | Margin | RoE |
|---|---|---|---|---|---|
| Gulf Coast Refining LLC | gulf_coast_refining | RF | $250M | SOFR+130bps | ~14% |
| Permian Pure Energy | permian_pure_energy | SCF | $150M | SOFR+110bps | ~13% |
| Atlantic Metals Trading | atlantic_metals_trading | INVENTORY | $100M | SOFR+160bps | ~12% |

*(Exact values populated from actual pipeline run before deployment)*

---

## 6. Run New Client Tab

### 6.1 Info Banner

Grey `st.info` box at tab top:
> *Live run uses Claude Opus + Haiku via the Anthropic API (~60–90 seconds). A simplified client profile is used here — full engagements include obligor ratings, dilution history, and supplier details.*

If `ANTHROPIC_API_KEY` is absent from both `st.secrets` and `os.environ`, show instead:
> *Add `ANTHROPIC_API_KEY` to Streamlit secrets to enable live runs.*
And disable the Run button.

### 6.2 Intake Form

`st.form("new_client")` with these fields:

| Field | Widget | Notes |
|---|---|---|
| Company name | `st.text_input` | Required |
| Sector | `st.selectbox` | Energy — Downstream, Energy — E&P, Materials — Metals, Materials — Mining, Industrial, Other |
| Revenue ($M) | `st.number_input` | min=1, step=50 |
| Working capital gap ($M) | `st.number_input` | min=1, step=10; tooltip: "Estimated gap between cash outflows and inflows over a 90-day cycle" |
| Payment terms (days) | `st.number_input` | min=1, max=180, step=15 |
| AR balance ($M) | `st.number_input` | Optional; leave 0 to skip |
| AP balance ($M) | `st.number_input` | Optional; leave 0 to skip |
| Inventory ($M) | `st.number_input` | Optional; leave 0 to skip |
| Off-balance sheet appetite | `st.checkbox` | "Client prefers off-balance-sheet treatment" |

Submit button label: **Run Pipeline →** (HSBC red)

### 6.3 Pipeline Progress

On submit, an `st.status` container shows each agent step sequentially:

```
⟳  Intake agent — validating client data...
✓  Intake complete
⟳  Diagnostic agent — identifying working capital pain point...
✓  Diagnostic: RF  (or SCF / INVENTORY)
⟳  Structuring agent — setting term-sheet parameters...
✓  Structure defined
⟳  Pricing agent — computing RoE and clearing margin...
✓  Clearing margin: SOFR+130bps | RoE: 14.2%
⟳  Pitch agent — drafting client narrative...
✓  Pitch narrative drafted
```

Updates happen in real time as each agent returns. The `st.status` container collapses to a green "Complete" bar when all five steps finish.

### 6.4 Results

After completion, a results section appears below the status container:

- **Headline metrics** — `st.metric` row: Facility Limit, Product, Clearing Margin, RoE
- **Four download buttons** — same layout as Demo Clients tab
- Artifacts are generated in memory (bytes) and never written to Streamlit's disk

The pipeline is called via a thin wrapper function `run_pipeline(raw: dict) -> tuple` in `app.py` that calls each agent in sequence and returns `(profile, diagnostic, structure, economics, pitch_text, pdf_bytes, xlsx_bytes, md_str, cme_dict)` — artifact bytes generated in memory using the existing output generators with `io.BytesIO` instead of file paths.

---

## 7. API Key Handling

Priority order:
1. `st.secrets["ANTHROPIC_API_KEY"]` (Streamlit Cloud secrets)
2. `os.environ["ANTHROPIC_API_KEY"]` (local `.env` loaded by orchestrator)

The app checks for a key at startup. If absent, Run tab shows the disabled-state info banner (Section 6.1).

For Streamlit Community Cloud deployment: user adds `ANTHROPIC_API_KEY` in the app's **Secrets** settings in the Streamlit dashboard (Settings → Secrets). Never committed to the repo.

---

## 8. Dependencies

Add to `pyproject.toml`:
```toml
"streamlit>=1.35",
```

Add to `.gitignore`:
```
.streamlit/secrets.toml
```

---

## 9. Deployment Steps (post-implementation)

1. Push repo to GitHub
2. Go to share.streamlit.io → New app → select repo → `app.py`
3. In app Settings → Secrets, add: `ANTHROPIC_API_KEY = "sk-ant-..."`
4. Generate demo artifacts locally (`python -m tfse run` for all 3 clients into `demo_outputs/`)
5. Commit `demo_outputs/` to repo
6. Share the public URL

---

## 10. Acceptance Criteria

- [ ] `streamlit run app.py` starts locally without errors
- [ ] Demo Clients tab shows all three clients with download buttons that serve real files
- [ ] Run New Client tab form submits, shows live progress, and produces four downloadable artifacts
- [ ] With no API key set, Run button is disabled with explanatory message
- [ ] Footer shows "For internal demo purposes only" on both tabs
- [ ] HSBC red (`#DB0011`) applied to badges and Run button
- [ ] App deployed to Streamlit Community Cloud and accessible via public URL on mobile
