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
        "dist_pct": 0.12,
        "retained_roe": 0.1244,
    },
    {
        "name": "Permian Pure Energy",
        "slug": "permian_pure_energy",
        "sector": "Energy — E&P",
        "product": "SCF",
        "facility_mm": 152,
        "margin": "SOFR+200bps",
        "roe": 0.1217,
        "dist_pct": 0.12,
        "retained_roe": 0.1270,
    },
    {
        "name": "Atlantic Metals Trading",
        "slug": "atlantic_metals_trading",
        "sector": "Materials — Metals",
        "product": "INVENTORY",
        "facility_mm": 97,
        "margin": "SOFR+250bps",
        "roe": 0.1222,
        "dist_pct": 0.12,
        "retained_roe": 0.1256,
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
