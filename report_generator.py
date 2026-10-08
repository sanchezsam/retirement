# -*- coding: utf-8 -*-
"""
RETIREMENT RUNWAY SCORECARD DOCUMENT GENERATION HUB
Completely independent standalone engine managing high-fidelity Excel and PDF exports.
Routes outputs directly into a dedicated local data/ folder with zero external dependencies.
Value Tracking Layout: WIDESCREEN LANDSCAPE PRESENTATION PREVENTING TEXT WRAP FRAGMENTATION.
"""
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.legends import Legend

import config

def generate_custom_dossiers(target_rank, selected_record, full_timeline_data, rotation_list, grand_total_taxes, grand_total_health, grand_total_base_inflow, grand_total_util_inflow, grand_total_brokerage, grand_total_roth, grand_total_401k):
    """Orchestrates standalone, penny-accurate Excel and PDF compilation stamped by Strategy Rank."""
    print("[DEBUG] Independent report_generator engine triggered successfully.")
    
    # Create the data directory if it does not already exist
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"[DEBUG] Created storage directory: ./{data_dir}/")

    excel_name = os.path.join(data_dir, f"strategy_rank_{target_rank}_workbook.xlsx")
    pdf_name = os.path.join(data_dir, f"strategy_rank_{target_rank}_dossier.pdf")
    print(f"[INFO] Compiling self-contained dossiers for Strategy Rank {target_rank}...")

    # --- 1. OPENPYXL EXCEL MASTER COMPILER SYNCHRONIZATION ---
    wb = openpyxl.Workbook()
    
    # Instantiate corporate theme fonts and solid color cell fills
    navy_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    gray_fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
    thin_border = Border(left=Side(style="thin", color="D9D9D9"), right=Side(style="thin", color="D9D9D9"), top=Side(style="thin", color="D9D9D9"), bottom=Side(style="thin", color="D9D9D9"))
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    font_data = Font(name="Segoe UI", size=10)
    font_data_bold = Font(name="Segoe UI", size=10, bold=True)

    # Tab 1 Creation: Executive Suitability Matrix Dashboard
    ws_dash = wb.active
    ws_dash.title = "Executive Dashboard"
    ws_dash.sheet_view.showGridLines = True
    
    ws_dash.merge_cells("A1:D1")
    ws_dash["A1"] = f"RETIREMENT SUITABILITY STRATEGY COMPARE FRAMEWORK - STRATEGY RANK {target_rank}"
    ws_dash["A1"].font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    ws_dash["A1"].fill = navy_fill
    ws_dash["A1"].alignment = align_center

    dash_headers = ["Strategic Performance Metric Profile", "Target Strategy Metric Value", "Operational Index Weight", "Compliance Profile Boundary"]
    for c_idx, text in enumerate(dash_headers, start=1):
        cell = ws_dash.cell(row=3, column=c_idx, value=text)
        cell.font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        cell.fill = gray_fill
        cell.alignment = align_center
        cell.border = thin_border
        
    dash_rows = [
        ("Liquidity Valley Defense Score", selected_record["liq_buffer"], "Max 25 Pts", "Cash runway buffer survival metrics."),
        ("IRS 5-Year Clock Safety Score", selected_record["clock_safety"], "Max 25 Pts", "Protection boundary against active penalty metrics."),
        ("Generational Roth Ratio Score", selected_record["roth_split"], "Max 25 Pts", "Final accumulation assets locked inside Roth pool."),
        ("Legislative Risk Defense Score", selected_record["legis_risk"], "Max 25 Pts", "Clearing speed timeline defense score."),
        ("FINAL RETIREMENT SUITABILITY INDEX", f"{selected_record['suitability_score']} / 100", "Combined Total", "Strategic filter scorecard suitability total.")
    ]
    for idx, r_val in enumerate(dash_rows, start=4):
        for c_idx, val in enumerate(r_val, start=1):
            cell = ws_dash.cell(row=idx, column=c_idx, value=val)
            cell.font = Font(name="Segoe UI", size=10, bold=(idx==8))
            cell.border = thin_border
            if c_idx == 2 or c_idx == 3:
                cell.alignment = align_center

    # Syncs your original comparative metrics map rows down inside columns A through C
    comparison_map = [
        ("Total Multi-Year Allowable Conversion Volume", "=SUM('Ledger Summary Rank ' & " + str(target_rank) + "!T4:T47)", "=SUM('Ledger Summary Rank ' & " + str(target_rank) + "!T4:T47)", "=SUM('Ledger Summary Rank ' & " + str(target_rank) + "!T4:T47)"),
        ("Cumulative Tax Pool Paid to Convert", "=SUM('Ledger Summary Rank ' & " + str(target_rank) + "!J4:J47)", "=SUM('Ledger Summary Rank ' & " + str(target_rank) + "!J4:J47)", "=SUM('Ledger Summary Rank ' & " + str(target_rank) + "!J4:J47)"),
        ("Total Lifetime ACA / Medicare Insurance Costs", "=SUM('Ledger Summary Rank ' & " + str(target_rank) + "!I4:I47)", "=SUM('Ledger Summary Rank ' & " + str(target_rank) + "!I4:I47)", "=SUM('Ledger Summary Rank ' & " + str(target_rank) + "!I4:I47)"),
        ("Overall Total Value inside the Roth at Age 90", "='Ledger Summary Rank ' & " + str(target_rank) + "!W47", "='Ledger Summary Rank ' & " + str(target_rank) + "!W47", "='Ledger Summary Rank ' & " + str(target_rank) + "!W47"),
    ]
    for idx, row_payload in enumerate(comparison_map, start=10):
        label_text = row_payload[0]
        ws_dash.cell(row=idx, column=1, value=label_text).font = Font(name="Segoe UI", size=10, bold=True)
        ws_dash.cell(row=idx, column=1).border = thin_border
        for col_i, ref in enumerate(row_payload[1:3], start=2):
            cell = ws_dash.cell(row=idx, column=col_i, value=ref)
            cell.font = font_data; cell.border = thin_border; cell.alignment = align_right
            if str(cell.value).startswith('='): 
                cell.number_format = '$#,##0.00'
    print("[DEBUG] Tab 1 Executive Scorecard built perfectly.")
    
    # Tab 2 Setup: 23-Column Chronological Transaction Records Data Matrix
    ws_ledg = wb.create_sheet(title=f"Ledger Summary Rank {target_rank}")
    ws_ledg.sheet_view.showGridLines = True

    ws_ledg.merge_cells("A1:W1")
    ws_ledg["A1"] = "CHRONOLOGICAL CONVERSION TIMELINE TRANSACTIONS MATRIX - COMPLIANCE RECORDS"
    ws_ledg["A1"].font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    ws_ledg["A1"].fill = navy_fill
    ws_ledg["A1"].alignment = align_center

    excel_headers = [
        "#", "Yr", "Wife Age", "Husband Age", "Brokerage Start", "401k Start", "Roth Start",
        "Living Expenses", "Healthcare Cost", "Estimated Taxes", "Total Outflow",
        "From Pension/SS/Rent", "Brok Yield", "Required Income", "From Brokerage", "From Roth", "From 401(k)", "Mandatory RMD",
        "Total Taxable Income", "Max Roth Conversion", "Brokerage End", "401(k) End", "Roth End"
    ]
    for c_idx, text in enumerate(excel_headers, start=1):
        cell = ws_ledg.cell(row=3, column=c_idx, value=text)
        cell.font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        cell.fill = navy_fill
        cell.alignment = align_center
        cell.border = thin_border

    # Calculate values across the complete sequence timeline
    for offset_idx in range(44):
        r_idx = 4 + offset_idx
        if offset_idx < len(full_timeline_data):
            y_row = full_timeline_data[offset_idx]
            c_tax = y_row.get("fed_tax", 0.0) + y_row.get("nm_tax", 0.0)
            y_from_inflow = sum(m.get("from_inflow", 0.0) for m in y_row["monthly_ledger"])
            y_from_brokerage = sum(m.get("from_brokerage", 0.0) for m in y_row["monthly_ledger"])
            y_from_roth = sum(m.get("from_roth", 0.0) for m in y_row["monthly_ledger"])
            y_from_401k = sum(m.get("from_401k", 0.0) for m in y_row["monthly_ledger"])

            y_needed = y_row.get("living_expense", 0.0)
            y_health = y_row.get("healthcare_cost", 0.0)
            y_outflow = y_needed + y_health + c_tax

            row_data = [
                offset_idx + 1,
                str(y_row.get("year", 2027 + offset_idx))[-2:],
                y_row.get("wife_age", 47 + offset_idx),
                y_row.get("husband_age", 46 + offset_idx),
                y_row.get("start_brokerage", 0.0),
                y_row.get("start_trad", 0.0),
                y_row.get("start_roth", 0.0),
                y_needed,
                y_health,
                c_tax,
                y_outflow,
                y_row.get("pension_ss_rent", 0.0),
                y_row.get("brokerage_gains", 0.0),
                y_row.get("required_income", y_outflow),
                y_from_brokerage,
                y_from_roth,
                y_from_401k,
                y_row.get("rmd_amount", 0.0),
                y_row.get("true_taxable_income", 0.0),
                y_row.get("actual_conversion", 0.0),
                y_row.get("end_brokerage", 0.0),
                y_row.get("end_trad", 0.0),
                y_row.get("end_roth", 0.0)
            ]
        else:
            row_data = [
                offset_idx + 1,
                str(2027 + offset_idx)[-2:],
                config.WIFE_START_AGE + offset_idx,
                config.HUSBAND_START_AGE + offset_idx,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            ]

        for c_idx, val in enumerate(row_data, start=1):
            cell = ws_ledg.cell(row=r_idx, column=c_idx, value=val)
            cell.font = Font(name="Segoe UI", size=10)
            cell.border = thin_border
            
            if r_idx % 2 == 0:
                cell.fill = PatternFill(start_color="F2F4F4", end_color="F2F4F4", fill_type="solid")
                
            if c_idx > 4:
                cell.number_format = '$#,##0.00'
                cell.alignment = align_right
            else:
                cell.alignment = align_center

    ws_ledg["R50"] = "Total Combined Conversion Volume:"
    ws_ledg["T50"] = "=SUM(T4:T47)"
    ws_ledg["R51"] = "Total Conversion Taxes Paid:"
    ws_ledg["T51"] = "=SUM(J4:J47)"
    ws_ledg["R52"] = "Total Lifetime Healthcare Cost:"
    ws_ledg["T52"] = "=SUM(I4:I47)"
    ws_ledg["R53"] = "Total Un-matured Roth Principal Tapped:"
    ws_ledg["T53"] = "=SUM(P4:P47)"
    ws_ledg["R54"] = "Cumulative 10% IRS Penalty Fees Paid:"
    ws_ledg["T54"] = selected_record.get("annual_penalties_paid", 0.00)
    ws_ledg["R55"] = "Terminal Roth Value at Age 90:"
    ws_ledg["T55"] = "=W47"

    for r_idx in range(50, 56):
        ws_ledg.cell(row=r_idx, column=18).font = Font(name="Segoe UI", size=10, bold=True)
        cell = ws_ledg.cell(row=r_idx, column=20)
        cell.font = font_data_bold; cell.number_format = '$#,##0.00'; cell.alignment = align_right
        if r_idx == 53 or r_idx == 54:
            ws_ledg.cell(row=r_idx, column=18).font = Font(name="Segoe UI", size=10, bold=True, color="9C0006")
            cell.font = Font(name="Segoe UI", size=10, bold=True, color="9C0006")

    for ws_target in wb.worksheets:
        for col_cells in ws_target.columns:
            val_strings = [str(cell.value or '') for cell in col_cells if not str(cell.value or '').startswith('=')]
            max_len = max(len(s) for s in val_strings) if val_strings else 10
            first_cell_in_column = col_cells[0]
            col_letter = get_column_letter(first_cell_in_column.column)
            ws_target.column_dimensions[col_letter].width = max(max_len + 5, 18)
            
    wb.save(excel_name)
    print(f"[SUCCESS] High-fidelity reporting spreadsheet compiled into: '{excel_name}'")

    # --- 2. REPORTLAB PDF COMPILER MASTER FACTORY ---
    print("[DEBUG] Launching PDF ReportLab flowable factory...")
    
    doc = SimpleDocTemplate(pdf_name, pagesize=landscape(letter), leftMargin=20, rightMargin=20, topMargin=25, bottomMargin=25)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13, textColor=colors.HexColor('#1F497D'), spaceAfter=10, alignment=1)
    section_style = ParagraphStyle('DocSection', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#1F497D'), spaceBefore=12, spaceAfter=6)
    sub_section_style = ParagraphStyle('DocSubSection', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#2C3E50'), spaceBefore=6, spaceAfter=4)
    table_hdr = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8, textColor=colors.white, alignment=1)
    cell_bold = ParagraphStyle('CB', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#1F497D'), alignment=1)
    cell_reg = ParagraphStyle('CR', fontName='Helvetica', fontSize=7.5, textColor=colors.black, alignment=1)
    cell_right = ParagraphStyle('CRG', fontName='Helvetica', fontSize=7.5, textColor=colors.black, alignment=2)
    cell_left_text = ParagraphStyle('CLT', fontName='Helvetica', fontSize=7.5, textColor=colors.HexColor('#2C3E50'), alignment=0)
    
    story = [
        Paragraph(f"RETIREMENT SUITABILITY DOSSIER (STRATEGY RANK {target_rank})", title_style)
    ]

    # --- GLOBAL DECIDING FACTORS & INPUT ASSUMPTIONS MATRIX ---
    story.append(Paragraph("GLOBAL RETIREMENT STRATEGY DECIDING PARAMETERS & INPUT ASSUMPTIONS", section_style))
    
    param_table_data = [
        [Paragraph("Strategic Parameter / Deciding Factor", table_hdr), Paragraph("Assumed Value", table_hdr), Paragraph("Operational Rationale & Application Boundary", table_hdr)],
        [Paragraph("Wife / Husband Starting Ages", cell_bold), Paragraph("47 / 46 Yrs", cell_reg), Paragraph("Establishes baseline timeline and initial demographics milestones.", cell_left_text)],
        [Paragraph("Retirement Start Month", cell_bold), Paragraph("February", cell_reg), Paragraph("Controls partial-year distribution splits in Year 1 natively.", cell_left_text)],
        [Paragraph("Strategic Runway Horizon", cell_bold), Paragraph("14 Years", cell_reg), Paragraph("Active optimization window before retirement stream infusions materialize at Age 61.", cell_left_text)],
        [Paragraph("Initial Taxable Brokerage Pool", cell_bold), Paragraph("$406,986.29", cell_reg), Paragraph("Liquid capital backing cash valley runway; includes $300k home sale shield injection.", cell_left_text)],
        [Paragraph("Initial Pre-Tax Traditional 401(k)", cell_bold), Paragraph("$1,476,432.85", cell_reg), Paragraph("Primary target asset balance targeted for multi-year bracket rotations.", cell_left_text)],
        [Paragraph("Initial Tax-Free Roth Pool", cell_bold), Paragraph("$130,967.93", cell_reg), Paragraph("Grandfathered baseline pool used as tax payment waterfall backup cushion.", cell_left_text)],
        [Paragraph("Portfolio Growth / Cash Yield Rates", cell_bold), Paragraph("6.0% / 4.0%", cell_reg), Paragraph("Annualized compounding applied to long-term equities vs liquid cash assets.", cell_left_text)],
        [Paragraph("Consumer Price Inflation Rate", cell_bold), Paragraph("3.0%", cell_reg), Paragraph("Compounding multiplier applied to lifestyle outflows and structural inflows.", cell_left_text)],
        [Paragraph("Annual Fixed Income Inflows", cell_bold), Paragraph("Pension: $35,250 / SS: $100,000", cell_reg), Paragraph("Systematic infusions starting at Wife Age 61 (Pension) and Age 62 (Social Security).", cell_left_text)],
        [Paragraph("Phase 1 Living / Health Outflows", cell_bold), Paragraph("$65,000.00 / $0.00", cell_reg), Paragraph("Low-income spending holiday targets running through designated Phase 1 years.", cell_left_text)],
        [Paragraph("Phase 2 Living / Health Outflows", cell_bold), Paragraph("$100,000.00 / $9,600.00", cell_reg), Paragraph("Standardized lifetime retirement outlays commencing in Phase 2.", cell_left_text)],
        [Paragraph("Lifestyle Aging Modifiers", cell_bold), Paragraph("Age 70: -15% / Age 80: -30%", cell_reg), Paragraph("Real expenditure reduction metrics mapping the retirement spending Smile Curve.", cell_left_text)],
        [Paragraph("Federal Deduction / NM Exemption", cell_bold), Paragraph("$33,200.00 / $8,000.00", cell_reg), Paragraph("Multi-authority statutory tax shields for Married Filing Jointly configurations.", cell_left_text)],
        [Paragraph("Permissible Bracket Choices", cell_bold), Paragraph("[0%, 22%, 24%]", cell_reg), Paragraph("Statutory marginal tax ceilings evaluated by chronological path permutation scanner.", cell_left_text)]
    ]
    
    t_param = Table(param_table_data, colWidths=[180, 140, 432])
    t_param.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')), 
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), 
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#1F497D')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9F9')])
    ]))
    story.append(t_param)
    story.append(Spacer(1, 10))

    story.append(Paragraph("STRATEGIC PILLAR COMPLIANCE SCORES PERFORMANCE INDEX", section_style))
    score_table_data = [
        [Paragraph("Strategic Performance Metric Pillar Profile", table_hdr), Paragraph("Calculated Vector Value", table_hdr), Paragraph("Compliance Boundary Weights & Strategic Target Profiles", table_hdr)],
        [Paragraph("Liquidity Valley Defense Score", cell_bold), Paragraph(f"{selected_record['liq_buffer']:.1f} / 25.0", cell_reg), Paragraph("Cash runway cushion buffer survival metrics inside the Phase 1 tactical window.", cell_reg)],
        [Paragraph("IRS 5-Year Clock Safety Score", cell_bold), Paragraph(f"{selected_record['clock_safety']:.1f} / 25.0", cell_reg), Paragraph("Protection margin against early unseasoned conversion ladder distribution penalties.", cell_reg)],
        [Paragraph("Generational Roth Ratio Score", cell_bold), Paragraph(f"{selected_record['roth_split']:.1f} / 25.0", cell_reg), Paragraph("Final distribution percentage stacked inside tax-free Roth vault.", cell_reg)],
        [Paragraph("Legislative Risk Defense Score", cell_bold), Paragraph(f"{selected_record['legis_risk']:.1f} / 25.0", cell_reg), Paragraph("Clearing speed timeline to firewall portfolio from rules changes.", cell_reg)],
        [Paragraph("FINAL SUITABILITY PERFORMANCE INDEX", cell_bold), Paragraph(f"<b>{selected_record['suitability_score']:.1f} / 100.0</b>", cell_reg), Paragraph("Combined suitability performance score across all four strategic pillars.", cell_reg)]
    ]
    t_score = Table(score_table_data, colWidths=[200, 100, 452])
    t_score.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#34495E')), 
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), 
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#34495E'))
    ]))
    story.append(t_score)
    story.append(Spacer(1, 10))

    # --- CHART GENERATION FOR MACRO WEALTH TRAJECTORY ---
    d_macro_chart = Drawing(752, 160)
    macro_vbc = VerticalBarChart()
    macro_vbc.x, macro_vbc.y, macro_vbc.height, macro_vbc.width = 45, 15, 110, 660
    
    macro_years = [str(r.get("year", "")) for r in full_timeline_data]
    macro_trad = [r.get("end_trad", 0.0) for r in full_timeline_data]
    macro_roth = [r.get("end_roth", 0.0) for r in full_timeline_data]
    macro_brok = [r.get("end_brokerage", 0.0) for r in full_timeline_data]
    
    macro_vbc.data = [macro_trad, macro_roth, macro_brok]
    macro_vbc.categoryAxis.categoryNames = macro_years
    macro_vbc.categoryAxis.labels.fontSize = 5.5
    macro_vbc.categoryAxis.labels.fontName = 'Helvetica-Bold'
    macro_vbc.categoryAxis.style = 'stacked'
    
    max_total_estate = max([(r.get("end_brokerage", 0.0) + r.get("end_trad", 0.0) + r.get("end_roth", 0.0)) for r in full_timeline_data]) if full_timeline_data else 100000
    macro_vbc.valueAxis.valueMin = 0
    macro_vbc.valueAxis.valueMax = max_total_estate * 1.05
    macro_vbc.valueAxis.valueStep = macro_vbc.valueAxis.valueMax / 5
    macro_vbc.valueAxis.labels.fontSize = 6
    macro_vbc.valueAxis.labels.fontName = 'Helvetica'
    
    macro_vbc.bars[0].fillColor = colors.HexColor('#34495E') # Pre-Tax Traditional (Charcoal Slate)
    macro_vbc.bars[1].fillColor = colors.HexColor('#2E7D32') # Tax-Free Roth Pool (Medium Green)
    macro_vbc.bars[2].fillColor = colors.HexColor('#1F497D') # Taxable Brokerage (Corporate Navy)
    d_macro_chart.add(macro_vbc)
    
    macro_legend = Legend()
    macro_legend.fontName = 'Helvetica'
    macro_legend.fontSize = 6
    macro_legend.x = 480
    macro_legend.y = 132
    macro_legend.dxTextSpace = 4
    macro_legend.dy = 4
    macro_legend.dx = 10
    macro_legend.columnMaximum = 1
    macro_legend.alignment = 'right'
    macro_legend.colorNamePairs = [
        (colors.HexColor('#34495E'), 'Traditional 401(k)'),
        (colors.HexColor('#2E7D32'), 'Roth Pool'),
        (colors.HexColor('#1F497D'), 'Brokerage Pool')
    ]
    d_macro_chart.add(macro_legend)
    d_macro_chart.add(String(45, 125, "Long-Term Strategic Wealth Preservation Matrix (Compounded Balances by Year)", fontName="Helvetica-Bold", fontSize=8, fillColor=colors.HexColor('#1F497D')))
    
    # --- PAGE 2 TRANSITION: ENFORCES CLEAN ISOLATION FOR SUMMARY MATRIX ---
    story.append(PageBreak())

    story.append(Paragraph("SUMMARY ACTIVE RETIREMENT CONVERSION LEDGER WINDOW", section_style))
    
    ledger_pdf_rows = [[
        Paragraph("#", table_hdr), Paragraph("Yr", table_hdr), Paragraph("Bracket", table_hdr), Paragraph("Brok Start", table_hdr), Paragraph("401k Start", table_hdr),
        Paragraph("Roth Start", table_hdr), Paragraph("Living Exp", table_hdr), Paragraph("Est Taxes", table_hdr), Paragraph("Health Cost", table_hdr), 
        Paragraph("Inflow Base", table_hdr), Paragraph("Brok Yield", table_hdr), Paragraph("Req Income", table_hdr), Paragraph("From Inflow", table_hdr), 
        Paragraph("From Brok", table_hdr), Paragraph("From Roth", table_hdr), Paragraph("End Roth", table_hdr)
    ]]
    
    truncated_total_taxes = 0.00
    truncated_total_health = 0.00
    truncated_total_base_inflow = 0.00
    truncated_total_util_inflow = 0.00
    truncated_total_brokerage = 0.00
    truncated_total_roth = 0.00
    truncated_total_living = 0.00
    truncated_total_req_income = 0.00
    t_brok_gains = 0.00
    
    active_years_data = []
    for y_idx, y_row in enumerate(full_timeline_data):
        pct_val = f"{rotation_list[y_idx]}%" if y_idx < len(rotation_list) else f"{getattr(config, 'DEFAULT_FALLBACK_BRACKET', 22)}%"
        c_tax = y_row["fed_tax"] + y_row["nm_tax"]
        y_from_inflow = sum(m["from_inflow"] for m in y_row["monthly_ledger"])
        y_from_brokerage = sum(m["from_brokerage"] for m in y_row["monthly_ledger"])
        y_from_roth = sum(m["from_roth"] for m in y_row["monthly_ledger"])
        
        y_living = y_row.get("living_expense", 0.00)
        y_req_income = y_row.get("required_income", 0.00)
        y_brok_gains = y_row.get("brokerage_gains", 0.00)
        
        truncated_total_taxes += c_tax
        truncated_total_health += y_row["healthcare_cost"]
        truncated_total_base_inflow += y_row["pension_ss_rent"]
        truncated_total_util_inflow += y_from_inflow
        truncated_total_brokerage += y_from_brokerage
        truncated_total_roth += y_from_roth
        truncated_total_living += y_living
        truncated_total_req_income += y_req_income
        t_brok_gains += y_brok_gains

        yr_short = str(y_row['year'])[-2:]
        ledger_pdf_rows.append([
            Paragraph(f"{y_idx + 1}", cell_bold), Paragraph(yr_short, cell_reg), Paragraph(pct_val, cell_reg), 
            Paragraph(f"${y_row['start_brokerage']:,.0f}", cell_right), Paragraph(f"${y_row['start_trad']:,.0f}", cell_right), Paragraph(f"${y_row['start_roth']:,.0f}", cell_right), 
            Paragraph(f"${y_living:,.0f}", cell_right), Paragraph(f"${c_tax:,.0f}", cell_right), Paragraph(f"${y_row['healthcare_cost']:,.0f}", cell_right), 
            Paragraph(f"${y_row['pension_ss_rent']:,.0f}", cell_right), Paragraph(f"${y_brok_gains:,.0f}", cell_right), Paragraph(f"${y_req_income:,.0f}", cell_right), Paragraph(f"${y_from_inflow:,.0f}", cell_right), 
            Paragraph(f"${y_from_brokerage:,.0f}", cell_right), Paragraph(f"${y_from_roth:,.0f}", cell_right), Paragraph(f"${y_row['end_roth']:,.0f}", cell_right)
        ])
        active_years_data.append(y_row)
        if y_row["end_trad"] <= 0.01:
            break

    ledger_pdf_rows.append([
        Paragraph("TOTALS", cell_bold), Paragraph("-", cell_reg), Paragraph("-", cell_reg), Paragraph("-", cell_reg), Paragraph("-", cell_reg), Paragraph("-", cell_reg), 
        Paragraph(f"${truncated_total_living:,.0f}", ParagraphStyle('TBR', parent=cell_right, fontName='Helvetica-Bold', fontSize=6.5)),
        Paragraph(f"${truncated_total_taxes:,.0f}", ParagraphStyle('TBR', parent=cell_right, fontName='Helvetica-Bold', fontSize=6.5)), 
        Paragraph(f"${truncated_total_health:,.0f}", ParagraphStyle('TBR', parent=cell_right, fontName='Helvetica-Bold', fontSize=6.5)), 
        Paragraph(f"${truncated_total_base_inflow:,.0f}", ParagraphStyle('TBR', parent=cell_right, fontName='Helvetica-Bold', fontSize=6.5)), 
        Paragraph(f"${t_brok_gains:,.0f}", ParagraphStyle('TBR', parent=cell_right, fontName='Helvetica-Bold', fontSize=6.5)), 
        Paragraph(f"${truncated_total_req_income:,.0f}", ParagraphStyle('TBR', parent=cell_right, fontName='Helvetica-Bold', fontSize=6.5)),
        Paragraph(f"${truncated_total_util_inflow:,.0f}", ParagraphStyle('TBR', parent=cell_right, fontName='Helvetica-Bold', fontSize=6.5)), 
        Paragraph(f"${truncated_total_brokerage:,.0f}", ParagraphStyle('TBR', parent=cell_right, fontName='Helvetica-Bold', fontSize=6.5)), 
        Paragraph(f"${truncated_total_roth:,.0f}", ParagraphStyle('TBR', parent=cell_right, fontName='Helvetica-Bold', fontSize=6.5)), 
        Paragraph("-", cell_reg)
    ])

    t_ledg = Table(ledger_pdf_rows, colWidths=[20, 22, 38, 50, 50, 50, 48, 48, 48, 50, 48, 52, 48, 48, 48, 64])
    t_ledg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')), 
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
        ('INNERGRID', (0,0), (-1,-2), 0.5, colors.HexColor('#E5E7E9')), 
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#1F497D')), 
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F8F9F9')]), 
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EAEDED')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2)
    ]))
    story.append(t_ledg)
    story.append(Spacer(1, 10))

    # --- REPOSITIONED: 30-YEAR MACRO TRAJECTORY CHART MOVED DIRECTLY UNDER LEDGER WINDOW TABLE ---
    story.append(Paragraph("30-YEAR MACRO PORTFOLIO WEALTH TRAJECTORY OVERVIEW", section_style))
    story.append(d_macro_chart)
    story.append(Spacer(1, 10))

    # --- MERGED DATA VISUALIZATION BAR GRAPH TRACKERS ---
    chart_years = [str(r["year"]) for r in active_years_data]
    chart_brok_bal = [r.get("end_brokerage", 0.0) for r in active_years_data]
    chart_roth_bal = [r.get("end_roth", 0.0) for r in active_years_data]
    chart_brok_draw = [sum(m.get("from_brokerage", 0.0) for m in r["monthly_ledger"]) for r in active_years_data]
    chart_roth_draw = [sum(m.get("from_roth", 0.0) for m in r["monthly_ledger"]) for r in active_years_data]
    chart_trad_bal = [r.get("end_trad", 0.0) for r in active_years_data]
    chart_req_income = [r.get("required_income", 0.0) for r in active_years_data]

    story.append(Paragraph("INTEGRATED RETIREMENT RESERVES DYNAMICS (BALANCES VS WITHDRAWALS WITH REQ INCOME OVERLAY)", section_style))
    d_br_chart = Drawing(752, 145)
    br_vbc = VerticalBarChart()
    br_vbc.x, br_vbc.y, br_vbc.height, br_vbc.width = 45, 15, 95, 660

    # UNIFIED GLOBAL ACCOUNT COLOR PALETTE RE-SYNCHRONIZATION
    br_vbc.data = [chart_trad_bal, chart_brok_bal, chart_roth_bal, chart_brok_draw, chart_roth_draw]
    br_vbc.categoryAxis.categoryNames = chart_years
    br_vbc.categoryAxis.labels.fontSize = 5.5
    br_vbc.categoryAxis.labels.angle = 45
    
    max_val_dynamics = max(max(chart_trad_bal), max(chart_brok_bal), max(chart_roth_bal)) * 1.10 if chart_trad_bal else 100000
    br_vbc.valueAxis.valueMin = 0
    br_vbc.valueAxis.valueMax = max_val_dynamics
    br_vbc.valueAxis.valueStep = max_val_dynamics / 5
    br_vbc.valueAxis.labels.fontSize = 6

    br_vbc.bars[0].fillColor = colors.HexColor('#34495E') # Traditional 401(k) Balance (Slate Charcoal)
    br_vbc.bars[1].fillColor = colors.HexColor('#1F497D') # Brokerage Balance (Corporate Navy - MATCHED SYSTEMWIDE)
    br_vbc.bars[2].fillColor = colors.HexColor('#2E7D32') # Roth Balance (Medium Green - MATCHED SYSTEMWIDE)
    br_vbc.bars[3].fillColor = colors.HexColor('#C62828') # Brokerage Withdrawal (Dark Red)
    br_vbc.bars[4].fillColor = colors.HexColor('#E53935') # Roth Withdrawal (Light Red)
    d_br_chart.add(br_vbc)

    # --- SYNCHRONIZED LINE OVERLAY FOR TOTAL INCOME REQUIRED / OUTFLOW ---
    lc = HorizontalLineChart()
    lc.x, lc.y, lc.height, lc.width = 45, 15, 95, 660
    lc.data = [chart_req_income]
    lc.categoryAxis.visible = 0
    lc.valueAxis.visible = 0
    lc.valueAxis.valueMin = 0
    lc.valueAxis.valueMax = br_vbc.valueAxis.valueMax
    lc.lines[0].strokeColor = colors.HexColor('#D35400') # Contrast dark orange for Required Outflow line
    lc.lines[0].strokeWidth = 2
    d_br_chart.add(lc)

    # --- UPDATED COMPREHENSIVE GRAPH KEY MATCHING MODIFIED SPEC ---
    merged_legend = Legend()
    merged_legend.fontName = 'Helvetica'
    merged_legend.fontSize = 6
    merged_legend.x = 310
    merged_legend.y = 114  # ADJUSTED: Shifted down from 125 to 114 to separate cleanly from title text string
    merged_legend.dxTextSpace = 4
    merged_legend.dy = 4
    merged_legend.dx = 10
    merged_legend.columnMaximum = 1
    merged_legend.alignment = 'right'
    merged_legend.colorNamePairs = [
        (colors.HexColor('#34495E'), '401(k) Bal'), # Slate Charcoal
        (colors.HexColor('#1F497D'), 'Brok Bal'),   # Corporate Navy
        (colors.HexColor('#2E7D32'), 'Roth Bal'),   # Medium Green
        (colors.HexColor('#C62828'), 'Brok Draw'),
        (colors.HexColor('#E53935'), 'Roth Draw'),
        (colors.HexColor('#D35400'), 'Req Income Line')
    ]
    d_br_chart.add(merged_legend)

    d_br_chart.add(String(45, 125, "Reserves Value Accumulation (Navy/Green/Slate) vs Active Capital Withdrawals (Reds) | Orange Line = Total Income Required", fontName="Helvetica-Bold", fontSize=7.5, fillColor=colors.HexColor('#1F497D')))
    story.append(d_br_chart)
    story.append(Spacer(1, 15))

    story.append(Paragraph("APPENDIX METRIC SUB-LEDGERS: COMPLETE CHRONOLOGICAL 44-YEAR RECORD TO AGE 90", section_style))
    for y_idx, y_row in enumerate(full_timeline_data):
        year_block_flowables = []
        phase_txt = "PHASE 1: HEALTHCARE HOLIDAY" if y_row["wife_age"] < 61 else "PHASE 2: FIXED STREAM INFUSION"
        year_headline = f"YEAR {y_row['year']} (AGES {y_row['husband_age']}/{y_row['wife_age']}) - {phase_txt}"
        year_block_flowables.append(Paragraph(year_headline, sub_section_style))

        ann_c_tax = y_row["fed_tax"] + y_row["nm_tax"]
        y_from_inflow = sum(m["from_inflow"] for m in y_row["monthly_ledger"])
        y_from_brokerage = sum(m["from_brokerage"] for m in y_row["monthly_ledger"])
        y_from_roth = sum(m["from_roth"] for m in y_row["monthly_ledger"])
        y_from_401k = sum(m["from_401k"] for m in y_row["monthly_ledger"])

        card_headers = [Paragraph("Yearly Expenses", table_hdr), Paragraph("From Pension/SS/Rent", table_hdr), Paragraph("From Brokerage", table_hdr), Paragraph("From Roth Pool", table_hdr), Paragraph("From 401(k) Pool", table_hdr)]
        card_values = [Paragraph(f"${y_row['living_expense'] + ann_c_tax + y_row['healthcare_cost']:,.2f}", cell_bold), Paragraph(f"${y_from_inflow:,.2f}", cell_reg), Paragraph(f"${y_from_brokerage:,.2f}", cell_reg), Paragraph(f"${y_from_roth:,.2f}", cell_reg), Paragraph(f"${y_from_401k:,.2f}", cell_reg)]
        
        t_card = Table([card_headers, card_values], colWidths=[150, 150, 150, 151, 151])
        t_card.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#7F8C8D')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#7F8C8D'))]))
        year_block_flowables.append(t_card); year_block_flowables.append(Spacer(1, 4))
        
        month_headers = [Paragraph("Month", table_hdr), Paragraph("From Inflow", table_hdr), Paragraph("From Brok", table_hdr), Paragraph("From Roth", table_hdr), Paragraph("From 401k", table_hdr), Paragraph("Lifestyle", table_hdr), Paragraph("Healthcare", table_hdr), Paragraph("Checklist Action Items & Compliance Alerts", table_hdr)]
        month_table_rows = [month_headers]

        brok_chart_points = []
        trad_chart_points = []
        roth_chart_points = []

        for m_data in y_row["monthly_ledger"]:
            m_name = m_data["month"]
            m_from_inflow = m_data["from_inflow"]
            m_from_brokerage = m_data["from_brokerage"]
            m_from_roth = m_data["from_roth"]
            m_from_401k = m_data["from_401k"]

            brok_chart_points.append(m_from_brokerage)
            trad_chart_points.append(m_from_401k)
            roth_chart_points.append(m_from_roth)

            if m_name == "Jan" and (y_row["fed_tax"] + y_row["nm_tax"]) > 0.01: m_text = "VOUCHER DUE: Pay IRS Quarter: $1,250.00 & NM: $400.00."
            elif m_name == "Feb" and y_row["year"] == 1: m_text = "RETIREMENT START: Active employment ceased. Drawdown cascades initialized."
            elif m_name in ["Apr", "Jun", "Sep"] and (y_row["fed_tax"] + y_row["nm_tax"]) > 0.01: m_text = "VOUCHER DUE: Pay IRS Quarter: $1,250.00 & NM: $400.00."
            elif m_name == "Dec":
                pct_label = f"{rotation_list[y_idx]}%" if y_idx < len(rotation_list) else f"{getattr(config, 'DEFAULT_FALLBACK_BRACKET', 22)}%"
                if y_row["end_trad"] <= 0.01: m_text = "Traditional balance depleted. Core conversions completed cleanly."
                else: m_text = f"EXECUTE RUNWAY: Roll over conversions under the {pct_label} target bracket. True-Up year-end liability."
            else: m_text = "Standard monthly loop sequence satisfied."
            
            y_lifestyle_draw = m_from_inflow + m_from_brokerage + m_from_roth + m_from_401k
            if m_name in ["Jan", "Apr", "Jun", "Sep"]: y_lifestyle_draw = max(0.00, y_lifestyle_draw - 1650.00)
            elif m_name == "Dec": y_lifestyle_draw = max(0.00, y_lifestyle_draw - (y_row["fed_tax"] + y_row["nm_tax"]))

            y_health_draw = m_data.get("health_draw", m_data.get("healthcare", 0.00))
            if y_health_draw <= 0.01 and y_row["healthcare_cost"] > 0.01: y_health_draw = y_row["healthcare_cost"] / 12.0

            month_table_rows.append([Paragraph(m_name, cell_bold), Paragraph(f"${m_from_inflow:,.2f}", cell_right), Paragraph(f"${m_from_brokerage:,.2f}", cell_right), Paragraph(f"${m_from_roth:,.2f}", cell_right), Paragraph(f"${m_from_401k:,.2f}", cell_right), Paragraph(f"${y_lifestyle_draw:,.2f}", cell_right), Paragraph(f"${y_health_draw:,.2f}", cell_right), Paragraph(m_text, cell_left_text)])

        d_chart = Drawing(752, 125)
        vbc = VerticalBarChart()
        vbc.x, vbc.y, vbc.height, vbc.width = 45, 15, 75, 620
        brok_bal_series, trad_bal_series, roth_bal_series = [], [], []
        for m_b in y_row["monthly_ledger"]:
            brok_bal_series.append(m_b.get("end_brokerage", y_row["start_brokerage"]))
            trad_bal_series.append(m_b.get("end_trad", y_row["start_trad"]))
            roth_bal_series.append(m_b.get("end_roth", y_row["start_roth"]))

        vbc.data = [trad_bal_series, roth_bal_series, brok_bal_series]
        vbc.categoryAxis.categoryNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        vbc.categoryAxis.labels.fontSize, vbc.categoryAxis.labels.fontName = 6, 'Helvetica-Bold'
        vbc.categoryAxis.style = 'stacked'
        vbc.valueAxis.valueMin = 0
        vbc.valueAxis.valueMax = max((y_row["start_brokerage"] + y_row["start_trad"] + y_row["start_roth"]) * 1.10, 100000)
        vbc.valueAxis.valueStep = vbc.valueAxis.valueMax / 4
        vbc.valueAxis.labels.fontSize, vbc.valueAxis.labels.fontName = 6, 'Helvetica'
        
        vbc.bars[0].fillColor = colors.HexColor('#34495E')  # Traditional 401(k) (Slate Charcoal)
        vbc.bars[1].fillColor = colors.HexColor('#2E7D32')  # Roth Pool (Medium Green)
        vbc.bars[2].fillColor = colors.HexColor('#1F497D')  # Taxable Brokerage (Corporate Navy)
        d_chart.add(vbc)
        
        d_chart.add(String(45, 105, f"Year {y_row['year']} Month-by-Month Allocation Stacked Drawdown Trajectory Pool Breakdown Matrix", fontName="Helvetica-Bold", fontSize=7, fillColor=colors.HexColor('#1F497D')))
        
        sub_legend = Legend()
        sub_legend.x = 45
        sub_legend.y = 95
        sub_legend.alignment = 'right'
        sub_legend.fontName, sub_legend.fontSize = 'Helvetica', 6
        sub_legend.columnMaximum = 1
        sub_legend.colorNamePairs = [(colors.HexColor('#34495E'), 'Traditional 401(k)'), (colors.HexColor('#2E7D32'), 'Roth Pool'), (colors.HexColor('#1F497D'), 'Taxable Brokerage')]
        d_chart.add(sub_legend)
        year_block_flowables.append(d_chart); year_block_flowables.append(Spacer(1, 4))
        
        t_months = Table(month_table_rows, colWidths=[38, 48, 50, 50, 50, 50, 50, 416])
        t_months.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7E9')), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#1F497D')), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9F9')])]))
        year_block_flowables.append(t_months); year_block_flowables.append(Spacer(1, 6))

        conversion_target_val = y_row.get("actual_conversion", 0.00)
        if y_row["end_trad"] <= 0.01:
            conv_reminder_text = "Traditional pre-tax balance fully depleted. Active core conversions satisfied cleanly."
        else:
            conv_reminder_text = f"Execute Year {y_row['year']} Roth conversion pool of <b>${conversion_target_val:,.2f}</b> before Dec 31."

        t_bal = Table([
            [Paragraph("Account Asset Class Tracked", table_hdr), Paragraph("Jan 1 Initial Balance", table_hdr), Paragraph("Dec 31 Final Balance", table_hdr), Paragraph("December Summary Balances Ledger", table_hdr)],
            [Paragraph("Taxable Brokerage / Cash", cell_bold), Paragraph(f"${y_row['start_brokerage']:,.2f}", cell_right), Paragraph(f"${y_row['end_brokerage']:,.2f}", cell_right), Paragraph(conv_reminder_text, cell_left_text)],
            [Paragraph("Traditional Pre-Tax 401(k)", cell_bold), Paragraph(f"${y_row['start_trad']:,.2f}", cell_right), Paragraph(f"${y_row['end_trad']:,.2f}", cell_right), Paragraph("", cell_left_text)],
            [Paragraph("Tax-Free Combined Roth Pool", cell_bold), Paragraph(f"${y_row['start_roth']:,.2f}", cell_right), Paragraph(f"${y_row['end_roth']:,.2f}", cell_right), Paragraph("", cell_left_text)]
        ], colWidths=[150, 120, 120, 362])
        
        t_bal.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#34495E')), 
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), 
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#34495E')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('SPAN', (3,1), (3,3))
        ]))
        year_block_flowables.append(t_bal); year_block_flowables.append(Spacer(1, 12))

        story.append(KeepTogether(year_block_flowables))

    doc.build(story)
    print(f"[SUCCESS] Standalone custom dossiers compiled and stored inside directory: ./{data_dir}/")
    print(f" -> Document 1: ./{excel_name}")
    print(f" -> Document 2: ./{pdf_name}")

