from pathlib import Path
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from tfse.models import ClientProfile, Structure, Economics


def generate_term_sheet(
    profile: ClientProfile,
    structure: Structure,
    economics: Economics,
    output_path: Path,
) -> Path:
    doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=16, textColor=colors.HexColor("#CC0000"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11, textColor=colors.HexColor("#333333"))
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=normal, fontSize=8, textColor=colors.grey)

    product_labels = {"RF": "Receivables Finance", "SCF": "Supply Chain Finance", "INVENTORY": "Inventory Finance"}
    product_name = product_labels.get(structure.product.value, structure.product.value)

    elements = []
    elements.append(Paragraph("HSBC Global Trade Solutions", title_style))
    elements.append(Paragraph(f"Indicative Term Sheet — {product_name}", styles["Heading2"]))
    elements.append(Paragraph(f"Prepared for: {profile.client_name} | {date.today().strftime('%d %B %Y')}", normal))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CC0000")))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("Facility Summary", h2))
    summary_data = [
        ["Parameter", "Details"],
        ["Borrower", profile.client_name],
        ["Arranger / Facility Agent", "HSBC Bank plc, London"],
        ["Facility Type", product_name],
        ["Facility Limit", f"${structure.facility_limit_mm:,.0f}M"],
        ["Commitment", "Committed" if structure.committed else "Uncommitted"],
        ["Advance Rate", f"{structure.advance_rate:.0%}"],
        ["Dilution Reserve", f"{structure.dilution_reserve:.1%}"],
        ["Recourse", "Non-recourse" if not structure.recourse else "Full recourse to borrower"],
        ["Indicative Pricing", f"SOFR + {structure.pricing_sofr_spread_bps}bps + {structure.fees_bps}bps fee"],
        ["Tenor", f"{structure.tenor_days} days"],
        ["Governing Law", "English Law"],
    ]
    t = Table(summary_data, colWidths=[2.5*inch, 4*inch])
    t.setStyle(TableStyle([
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
    elements.append(t)
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("Eligibility Criteria", h2))
    for criterion in structure.eligible_criteria:
        elements.append(Paragraph(f"• {criterion}", normal))
    elements.append(Spacer(1, 0.2*inch))

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

    elements.append(Paragraph("Key Conditions Precedent", h2))
    cps = [
        "Execution of facility agreement and all ancillary documents",
        "Satisfactory KYC / AML review and credit approval",
        "Legal opinions (English law, jurisdiction of borrower)",
        "Appointment of collateral monitoring agent (if applicable)",
        "No material adverse change since date of application",
    ]
    for cp in cps:
        elements.append(Paragraph(f"• {cp}", normal))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(
        "This term sheet is indicative only and does not constitute a commitment to lend. "
        "All terms are subject to credit approval, legal documentation, and internal compliance review. "
        "HSBC Bank plc is authorised by the Prudential Regulation Authority.",
        small,
    ))

    doc.build(elements)
    return output_path
