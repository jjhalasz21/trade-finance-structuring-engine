from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from tfse.models import Structure, Economics


def generate_profitability_model(
    structure: Structure,
    economics: Economics,
    output_path: Path,
) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Profitability Model"
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 14

    red = "CC0000"
    light_grey = "F5F5F5"

    def header(row, text):
        ws.cell(row=row, column=1, value=text).font = Font(bold=True, color="FFFFFF", size=10)
        ws.cell(row=row, column=1).fill = PatternFill("solid", fgColor=red)
        ws.merge_cells(f"A{row}:C{row}")

    def row_data(row, label, value=None, formula=None, is_pct=False, bold=False, shade=False):
        c_label = ws.cell(row=row, column=1, value=label)
        c_label.font = Font(bold=bold, size=9)
        if shade:
            c_label.fill = PatternFill("solid", fgColor=light_grey)
        c_val = ws.cell(row=row, column=2)
        c_val.value = formula if formula else value
        c_val.font = Font(bold=bold, size=9)
        if shade:
            c_val.fill = PatternFill("solid", fgColor=light_grey)
        c_val.number_format = "0.0%" if is_pct else '#,##0.00"M"'

    # INPUTS BLOCK (rows 1-12)
    header(1, "INPUTS (edit yellow cells)")
    inp_fill = PatternFill("solid", fgColor="FFF2CC")
    inputs = [
        (2, "Facility Limit ($M)", structure.facility_limit_mm),
        (3, "Drawn Balance ($M)", economics.drawn_mm),
        (4, "Margin (bps)", economics.clearing_margin_bps),
        (5, "Fee (bps)", structure.fees_bps),
        (6, "FTP Rate", 0.0020),
        (7, "Tax Rate", 0.25),
        (8, "RWA ($M)", economics.rwa_mm),
        (9, "Capital ($M)", economics.capital_mm),
        (10, "OpEx ($M)", economics.opex_mm),
        (11, "PD", 0.0005),
        (12, "LGD", 0.45),
    ]
    for r, label, val in inputs:
        ws.cell(row=r, column=1, value=label).font = Font(size=9)
        c = ws.cell(row=r, column=2, value=val)
        c.fill = inp_fill
        c.font = Font(size=9)
        if label in ("FTP Rate", "Tax Rate", "PD", "LGD"):
            c.number_format = "0.00%"
        elif label in ("Margin (bps)", "Fee (bps)"):
            c.number_format = "0"
        else:
            c.number_format = '#,##0.00"M"'

    # ROE WATERFALL (rows 14-24)
    header(14, "ROE WATERFALL")
    row_data(15, "Gross Revenue ($M)", formula="=B3*(B4/10000)+B3*(B5/10000)")
    row_data(16, "(-) Cost of Funds ($M)", formula="=B3*B6", shade=True)
    row_data(17, "(-) Operating Cost ($M)", formula="=B10")
    row_data(18, "(-) Expected Loss ($M)", formula="=B8*B11*B12", shade=True)
    row_data(19, "= Pre-Tax NII ($M)", formula="=B15-B16-B17-B18", bold=True)
    row_data(20, "(-) Tax ($M)", formula="=MAX(B19*B7,0)", shade=True)
    row_data(21, "= Post-Tax NII ($M)", formula="=B19-B20", bold=True)
    row_data(22, "Allocated Capital ($M)", formula="=B9", shade=True)
    ws.cell(row=24, column=1, value="POST-TAX ROE").font = Font(bold=True, size=11)
    c_roe = ws.cell(row=24, column=2)
    c_roe.value = "=B21/B22"
    c_roe.number_format = "0.0%"
    c_roe.font = Font(bold=True, size=11, color=red)
    c_roe.fill = PatternFill("solid", fgColor="FFF2CC")

    # SENSITIVITY TABLE (rows 28-33)
    header(28, "SENSITIVITY: RoE vs Utilisation & Margin")
    ws.cell(row=29, column=1, value="Utilisation \\ Margin").font = Font(bold=True, size=9)
    margin_deltas = [-25, 0, 25]
    for i, d in enumerate(margin_deltas):
        ws.cell(row=29, column=2+i, value=f"Margin {d:+d}bps").font = Font(bold=True, size=9)
        ws.column_dimensions[get_column_letter(2+i)].width = 14

    for ri, util in enumerate([0.60, 0.75, 0.90]):
        ws.cell(row=30+ri, column=1, value=f"{util:.0%} utilisation").font = Font(size=9)
        for ci, delta in enumerate(margin_deltas):
            drawn_ref = f"B2*{util}"
            rev = f"({drawn_ref})*((B4+{delta})/10000+B5/10000)"
            cof = f"({drawn_ref})*B6"
            el = "B8*B11*B12"
            pretax = f"({rev}-{cof}-B10-{el})"
            tax = f"MAX({pretax}*B7,0)"
            posttax = f"({pretax}-{tax})"
            formula = f"=({posttax})/B9"
            c = ws.cell(row=30+ri, column=2+ci, value=formula)
            c.number_format = "0.0%"
            c.font = Font(bold=(util == 0.75 and delta == 0), size=9,
                         color=red if (util == 0.75 and delta == 0) else "000000")

    wb.save(str(output_path))
    return output_path
