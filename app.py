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
        "margin": "SOFR+145bps",
        "roe": 0.1219,
        "dist_pct": 0.25,
        "retained_roe": 0.1285,
    },
    {
        "name": "Permian Pure Energy",
        "slug": "permian_pure_energy",
        "sector": "Energy — E&P",
        "product": "SCF",
        "facility_mm": 152,
        "margin": "SOFR+215bps",
        "roe": 0.1235,
        "dist_pct": 0.30,
        "retained_roe": 0.1320,
    },
    {
        "name": "Atlantic Metals Trading",
        "slug": "atlantic_metals_trading",
        "sector": "Materials — Metals",
        "product": "INVENTORY",
        "facility_mm": 97,
        "margin": "SOFR+310bps",
        "roe": 0.1312,
        "dist_pct": 0.40,
        "retained_roe": 0.1445,
    },
]

CLIENT_BIOS = {
    "gulf_coast_refining": (
        "A mid-size independent petroleum refiner operating two Gulf Coast refineries "
        "with ~240,000 bbl/day combined throughput. The business buys crude on 30-day "
        "terms from producers and sells gasoline, diesel, and jet fuel to distributors "
        "on 45–60 day terms — a structural working capital gap of $180–220M that widens "
        "with every crude price spike. A Q3 2025 surge in WTI compressed margins and "
        "stressed their revolving credit facility covenants simultaneously, leaving the "
        "CFO reluctant to draw further. Gulf Coast is sitting on ~$260M in diversified, "
        "investment-grade receivables across 12+ fuel distributor counterparties with no "
        "efficient mechanism to monetize them.\n\n"
        "**HSBC solution:** Receivables finance — HSBC acquires the eligible AR pool at "
        "a discount reflecting SOFR+145bps, providing immediate liquidity without adding "
        "leverage. 25% of the facility is distributed to institutional investors, "
        "reducing HSBC's balance sheet commitment while earning an arrangement fee."
    ),
    "permian_pure_energy": (
        "A focused Permian Basin E&P running ~85,000 boe/day net production. A 2024 "
        "bolt-on acquisition of adjacent acreage accelerated their completions program "
        "to 4 active rigs and a $650M annual capex budget. That growth has ballooned "
        "their AP stack to $145M across 80+ vendors — drilling contractors, pipe "
        "suppliers, wireline firms — all demanding payment within 30–45 days while "
        "production revenues lag completions by 60–90 days. Smaller vendors are "
        "tightening credit terms, and Permian Pure's treasury team is managing vendor "
        "relationships that should be running on autopilot.\n\n"
        "**HSBC solution:** Supply Chain Finance — Permian Pure extends standard payment "
        "terms to 90 days while their suppliers receive payment in 2–3 business days at "
        "a modest discount funded at SOFR+215bps. DPO improves, vendor friction drops, "
        "and working capital is freed up for the next rig. 30% distributed to "
        "institutional SCF investors."
    ),
    "atlantic_metals_trading": (
        "A London-headquartered base metals merchant with US operations in New York, "
        "trading copper, aluminum, and zinc across the Atlantic basin. Atlantic sources "
        "physical metal from South American and European smelters, warehouses it in "
        "LME-approved facilities in New Orleans and Baltimore, and sells to US and "
        "European manufacturers — with average holding periods of 45–75 days and a "
        "typical inventory position of $85–100M. Their existing inventory finance line "
        "is fully drawn, forcing them to pass on profitable trades during the current "
        "aluminum supply disruption out of Mozambique.\n\n"
        "**HSBC solution:** Secured inventory finance — a borrowing base facility "
        "collateralized by LME-grade metal at 65–70% advance rates against warehouse "
        "receipts, supported by LME forward hedges. SOFR+310bps reflects commodity "
        "collateral risk. 40% distributed to specialist commodity finance investors, "
        "reducing HSBC's concentration exposure."
    ),
}

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

            slug = client["slug"]
            with st.expander("Client brief"):
                st.markdown(CLIENT_BIOS.get(slug, ""))

            st.metric("Facility Limit", f"${client['facility_mm']}M")
            st.metric("Clearing Margin", client["margin"])
            st.metric("Full-Hold RoE", f"{client['roe']:.1%}")
            st.metric("Distribution", f"{client['dist_pct']:.0%}")
            st.metric("Retained RoE", f"{client['retained_roe']:.1%}")

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
_RUN_PASSWORD = "Demo!K!tty4574!"

with tab_run:
    if "run_unlocked" not in st.session_state:
        st.session_state.run_unlocked = False

    if not st.session_state.run_unlocked:
        st.markdown("**This feature is password-protected.**")
        pw_col, btn_col = st.columns([3, 1])
        with pw_col:
            pw_input = st.text_input("Password", type="password", label_visibility="collapsed",
                                     placeholder="Enter password")
        with btn_col:
            if st.button("Unlock", type="primary"):
                if pw_input == _RUN_PASSWORD:
                    st.session_state.run_unlocked = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    else:
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
