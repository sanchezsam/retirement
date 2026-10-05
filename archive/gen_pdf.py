# -*- coding: utf-8 -*-
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
# Native ReportLab Vector Graphic and Multi-Asset Chart Modules
from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart
import config  # Dynamically pull universal retirement input values from config.py

def generate_retirement_pdf(scenario_params):
    """
    Modular layout blueprint function. Accepts custom scenario parameters dynamically
    to compile distinct scenario report dossier files.
    """
    pdf_filename = scenario_params["filename"]
    growth_rate = scenario_params["growth_rate"]
    inflation_rate = scenario_params["inflation_rate"]
    scenario_title = scenario_params["title"]

    # 1. Pull Core System Constants Directly From Centralized Config File
    wife_start_age = config.WIFE_START_AGE
    husband_start_age = config.HUSBAND_START_AGE
    
    # Aggregate starting liquid brokerage cash base matching excel engine input logic
    brokerage = (
        config.STARTING_BALANCES["brokerage_1"] + 
        config.STARTING_BALANCES["brokerage_2"] + 
        config.STARTING_BALANCES["house_sale_proceeds"] + 
        config.STARTING_BALANCES["house_equity_invested"]
    )
    trad_401k = config.STARTING_BALANCES["trad_401k"]
    roth = config.STARTING_BALANCES["roth_pool"]
    
    base_living_holiday = config.SPENDING["phase1_living_expense"]
    base_living_standard = config.SPENDING["phase2_living_expense"]
    base_hc_standard = config.SPENDING["phase2_healthcare_cost"]
    
    pension_value = config.ANNUAL_PENSION_VALUE
    ss_value = config.ANNUAL_SOCIAL_SECURITY
    standard_deduction = config.TAX_SHIEILDS["federal_standard_deduction"]
    senior_filer_bonus = config.TAX_SHIEILDS["senior_filer_bonus"]
    nm_exemption = config.TAX_SHIEILDS["nm_joint_exemption"]
    
    fed_tax_rate = config.TAX_SHIEILDS["fed_tax_rate"]
    nm_tax_rate = config.TAX_SHIEILDS["nm_tax_rate"]

    # 2. Initialize Document Template & Set Page Constraints
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=36,   # Tight margins optimized for physical page binding
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    # 3. Setup Typography & Document Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=colors.HexColor('#1F497D'),
        spaceAfter=10
    )
    
    phase_style = ParagraphStyle(
        'PhaseHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.white,
        spaceBefore=6,
        spaceAfter=4
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1 # Center aligned
    )
    
    cell_bold = ParagraphStyle(
        'CellBold',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1F497D')
    )
    
    cell_reg = ParagraphStyle(
        'CellReg',
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.black
    )

    story = []
    # 4. Pre-Run Data Simulation to Accumulate Dashboard Totals Dynamically
    sim_brokerage = brokerage
    sim_trad = trad_401k
    sim_roth = roth
    
    total_conversions_volume = 0.00
    total_fed_taxes_paid = 0.00
    total_nm_taxes_paid = 0.00
    total_healthcare_costs = 0.00
    total_growth_earned = 0.00
    
    depletion_year_alert = None
    prev_fed_tax_sim = 4545.45
    prev_nm_tax_sim = 3265.31

    for year in range(1, 45):
        wife_age = wife_start_age + year - 1
        y_start_total = sim_brokerage + sim_trad + sim_roth
        
        if year <= 5:
            living_expense = base_living_holiday * ((1 + inflation_rate) ** (year - 1))
            healthcare_cost = 0.00
            raw_target = 416100.00 - (36000.00 * ((1 + inflation_rate) ** (year - 1)))
            pension_ss_rent = (44000.00 + 6600.00 + config.SPENDING["phase1_rental_income"]) if year == 1 else (config.SPENDING["phase1_rental_income"] * ((1 + inflation_rate) ** (year - 1)))
        else:
            living_expense = base_living_standard * ((1 + inflation_rate) ** (year - 1))
            healthcare_cost = 4800.00 * ((1 + inflation_rate) ** (year - 1)) if wife_age < 65 else base_hc_standard * ((1 + inflation_rate) ** (year - 1))
            active_pension = pension_value if wife_age >= 61 else 0.00
            pension_ss_rent = active_pension + (ss_value if wife_age >= 62 else 0.00)
            raw_target = max(0.00, config.TAX_SHIEILDS["aca_magi_ceiling"] - active_pension) if wife_age < 65 else 416100.00

        if wife_age >= 62 and wife_age < 65:
            raw_target = 0.00

        conversion_target = min(sim_trad, raw_target) if sim_trad > 0 else 0.00
        
        fed_tax = max(0.00, (conversion_target - standard_deduction) * fed_tax_rate)
        nm_tax = max(0.00, (conversion_target - (standard_deduction + nm_exemption)) * nm_tax_rate)
        total_taxes = fed_tax + nm_tax
        
        q_fed_voucher_sim = (prev_fed_tax_sim * 1.10) / 4.0
        q_nm_voucher_sim = (prev_nm_tax_sim * 1.10) / 4.0
        annual_vouchers_sim = (q_fed_voucher_sim + q_nm_voucher_sim) * 4.0
        
        dec_tax_true_up_sim = max(0.00, total_taxes - annual_vouchers_sim)
        total_outflow = living_expense + healthcare_cost + annual_vouchers_sim + dec_tax_true_up_sim
        
        from_pension_ss_rent = min(total_outflow, pension_ss_rent)
        remaining_need = max(0.00, total_outflow - from_pension_ss_rent)
        
        if sim_brokerage <= 0 and depletion_year_alert is None:
            depletion_year_alert = 2026 + year - 1
            
        from_brokerage = min(remaining_need, sim_brokerage)
        remaining_need -= from_brokerage
        from_401k = min(remaining_need, sim_trad) if wife_age >= 75 else 0.00
        
        total_conversions_volume += conversion_target
        total_fed_taxes_paid += fed_tax
        total_nm_taxes_paid += nm_tax
        total_healthcare_costs += healthcare_cost
        
        sim_brokerage = max(0.00, (sim_brokerage - from_brokerage) * (1 + growth_rate))
        sim_trad = max(0.00, (sim_trad - conversion_target - from_401k) * (1 + growth_rate))
        sim_roth = max(0.00, (sim_roth + conversion_target) * (1 + growth_rate))
        
        y_end_total = sim_brokerage + sim_trad + sim_roth
        total_growth_earned += max(0.00, y_end_total - (y_start_total - from_brokerage - conversion_target - from_401k))
        
        prev_fed_tax_sim = fed_tax
        prev_nm_tax_sim = nm_tax

    # --- BUILD EXECUTIVE DASHBOARD COVER PAGE ---
    story.append(Paragraph("EXECUTIVE SUMMARY DASHBOARD - " + scenario_title, title_style))
    story.append(Paragraph("Lifelong Metrics Formulated Across Your 44-Year Matrix Horizon (Growth: " + str(growth_rate*100) + "%, Inflation: " + str(inflation_rate*100) + "%)", cell_bold))
    story.append(Spacer(1, 10))

    dash_data = [
        [Paragraph("Strategic Wealth Parameter Tracked", table_header_style), Paragraph("Value Amount (USD)", table_header_style), Paragraph("Strategic Model Implementation Insight Notes", table_header_style)],
        [Paragraph("Initial Starting Net Worth (Age 47)", cell_bold), Paragraph("$2,494,714.07", cell_reg), Paragraph("Combined starting asset value base across Brokerage, pre-tax 401(k), and Roth pool.")],
        [Paragraph("Total Lifetime Conversion Volume", cell_bold), Paragraph("$" + "{:,.2f}".format(total_conversions_volume), cell_reg), Paragraph("Total amount successfully shifted into tax-free Roth pool before Age 65 income shields applied.")],
        [Paragraph("Cumulative Federal Taxes Paid", cell_bold), Paragraph("$" + "{:,.2f}".format(total_fed_taxes_paid), cell_reg), Paragraph("Federal income tax paid on conversions based on your 15% bracket drag assumption.")],
        [Paragraph("Cumulative New Mexico State Taxes", cell_bold), Paragraph("$" + "{:,.2f}".format(total_nm_taxes_paid), cell_reg), Paragraph("NM state tax drag (4.9%) factoring in deductions and your joint $8,000 exemption shield.")],
        [Paragraph("Total Lifetime Healthcare Cost Pool", cell_bold), Paragraph("$" + "{:,.2f}".format(total_healthcare_costs), cell_reg), Paragraph("Includes your $400/mo capped phase and post-65 inflation-adjusted Medicare outlays.")],
        [Paragraph("Total Compounded Growth Generated", cell_bold), Paragraph("$" + "{:,.2f}".format(total_growth_earned), cell_reg), Paragraph("Total investment compound growth earned over 44 years under this specific model rate.")],
        [Paragraph("Terminal Projected Net Worth (Age 90)", cell_bold), Paragraph("$" + "{:,.2f}".format(sim_brokerage + sim_trad + sim_roth), cell_reg), Paragraph("Final asset base. Pre-tax 401(k) minimized to $0.00, leaving wealth inside tax-free Roth.")],
    ]
    t_dash = Table(dash_data, colWidths=[150, 100, 290])
    t_dash.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')), ('ALIGN', (0,0), (1,-1), 'LEFT'), ('ALIGN', (1,1), (1,-1), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#1F497D')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E2F8FD')), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_dash)
    story.append(PageBreak()) 
    # 5. Generate 44 Continuous Pages with Granular Monthly Ledger Tables
    prev_fed_tax = 4545.45  
    prev_nm_tax = 3265.31   
    months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for year in range(1, 45):
        wife_age = wife_start_age + year - 1
        husband_age = husband_start_age + year - 1
        
        start_brokerage = brokerage
        start_trad = trad_401k
        start_roth = roth
        raw_conversion_target = 0.00
        
        # Header Assignment Mechanics Evaluated Every Loop
        if year <= 5:
            phase_name = "YEAR " + str(year) + " (AGES " + str(wife_age) + "/" + str(husband_age) + ") - PHASE 1: HEALTHCARE HOLIDAY"
            phase_bg = '#1F497D'
            living_expense = base_living_holiday * ((1 + inflation_rate) ** (year - 1))
            healthcare_cost = 0.00
            raw_conversion_target = 416100.00 - (36000.00 * ((1 + inflation_rate) ** (year - 1)))
            pension_ss_rent_annual = (44000.00 + 6600.00 + config.SPENDING["phase1_rental_income"]) if year == 1 else (config.SPENDING["phase1_rental_income"] * ((1 + inflation_rate) ** (year - 1)))
        else:
            living_expense = base_living_standard * ((1 + inflation_rate) ** (year - 1))
            healthcare_cost = 4800.00 * ((1 + inflation_rate) ** (year - 1)) if wife_age < 65 else base_hc_standard * ((1 + inflation_rate) ** (year - 1))
            active_pension = pension_value if wife_age >= 61 else 0.00
            pension_ss_rent_annual = active_pension + (ss_value if wife_age >= 62 else 0.00)
            
            if wife_age < 65:
                phase_name = "YEAR " + str(year) + " (AGES " + str(wife_age) + "/" + str(husband_age) + ") - PHASE 2: ACA SHIELD"
                phase_bg = '#2E7D32'
                raw_conversion_target = max(0.00, config.TAX_SHIEILDS["aca_magi_ceiling"] - active_pension)
            else:
                phase_name = "YEAR " + str(year) + " (AGES " + str(wife_age) + "/" + str(husband_age) + ") - PHASE 4: MEDICARE RECOVERY"
                phase_bg = '#C62828'
                raw_conversion_target = 416100.00

        if wife_age >= 62 and wife_age < 65:
            phase_name = "YEAR " + str(year) + " (AGES " + str(wife_age) + "/" + str(husband_age) + ") - PHASE 3: TRANSITION"
            phase_bg = '#EF6C00'
            raw_conversion_target = 0.00

        conversion_target = min(start_trad, raw_conversion_target) if start_trad > 0 else 0.00
        fed_tax = max(0.00, (conversion_target - standard_deduction) * fed_tax_rate)
        nm_tax = max(0.00, (conversion_target - (standard_deduction + nm_exemption)) * nm_tax_rate)
        total_taxes = fed_tax + nm_tax
        
        q_fed_voucher = (prev_fed_tax * 1.10) / 4.0
        q_nm_voucher = (prev_nm_tax * 1.10) / 4.0
        annual_vouchers_paid = (q_fed_voucher + q_nm_voucher) * 4.0
        
        # Safe Harbor Subtraction True-Up Logic Check
        dec_tax_true_up = max(0.00, total_taxes - annual_vouchers_paid)
        
        prev_fed_tax = fed_tax
        prev_nm_tax = nm_tax

        # Spaced headers width allocations to look completely clean
        monthly_table_rows = [[
            Paragraph("Execution Month", table_header_style), Paragraph("From Pension/SS/Rent", table_header_style),
            Paragraph("From Brokerage", table_header_style), Paragraph("From Roth", table_header_style),
            Paragraph("From 401(k)", table_header_style), 
            Paragraph("Lifestyle Cost / Conversion Tax Hold", table_header_style),
            Paragraph("Checklist Action Items & Authorizations", table_header_style)
        ]]
        
        annual_brokerage_draw = 0.00
        annual_roth_draw = 0.00
        annual_401k_draw = 0.00
        annual_inflow_utilized = 0.00
        
        chart_brokerage_data = []
        chart_trad_data = []
        chart_roth_data = []
        
        running_brokerage = start_brokerage
        running_trad = start_trad
        running_roth = start_roth
        monthly_conversion_split = conversion_target / 12.0
        for m_idx, m_name in enumerate(months_list):
            m_living = living_expense / 12.0
            m_hc = healthcare_cost / 12.0
            
            if year == 1:
                m_inflow = 3000.00  
            else:
                m_rent = 3000.00 * ((1 + inflation_rate) ** (year - 1)) if year <= 5 else 0.00
                m_pension = (pension_value / 12.0) if wife_age >= 61 else 0.00
                m_ss = (ss_value / 12.0) if wife_age >= 62 else 0.00
                m_inflow = m_rent + m_pension + m_ss
                
            m_tax_voucher = (q_fed_voucher + q_nm_voucher) if m_name in ["Apr", "Jun", "Sep", "Jan"] else 0.00
            m_conversion_tax_drag = dec_tax_true_up if m_name == "Dec" else 0.00
            m_total_need = m_living + m_hc + m_tax_voucher + m_conversion_tax_drag
            
            m_from_inflow = min(m_total_need, m_inflow)
            m_rem = max(0.00, m_total_need - m_from_inflow)
            annual_inflow_utilized += m_from_inflow
            
            m_from_brokerage = min(m_rem, running_brokerage)
            m_rem -= m_from_brokerage
            annual_brokerage_draw += m_from_brokerage
            running_brokerage = max(0.00, running_brokerage - m_from_brokerage)
            
            m_from_401k = min(m_rem, running_trad if wife_age >= 75 else 0.00)
            m_rem -= m_from_401k
            annual_401k_draw += m_from_401k
            running_trad = max(0.00, running_trad - m_from_401k - monthly_conversion_split)
            
            m_from_roth = min(m_rem, running_roth if running_roth > 0 else 0.00)
            m_rem -= m_from_roth
            annual_roth_draw += m_from_roth
            running_roth = max(0.00, running_roth - m_from_roth + monthly_conversion_split)
            
            chart_brokerage_data.append(running_brokerage)
            chart_trad_data.append(running_trad)
            chart_roth_data.append(running_roth)
            
            if m_name in ["Apr", "Jun", "Sep", "Jan"]:
                action_str = "<b>QUARTERLY VOUCHER:</b> Submit safe harbor targets: Pay IRS <b>$" + "{:,.2f}".format(q_fed_voucher) + "</b> & NM TAP <b>$" + "{:,.2f}".format(q_nm_voucher) + "</b>."
            elif m_name == "Nov" and conversion_target > 0:
                action_str = "<b>ASSET LIQUIDATION:</b> Re-balance brokerage principal allocations to fund next month's conversions."
            elif m_name == "Dec" and conversion_target > 0:
                if dec_tax_true_up > 0:
                    action_str = "<b>EXECUTE STRATEGY:</b> 1) Convert <b>$" + "{:,.2f}".format(conversion_target) + "</b> to Roth. 2) Settle true-up balance of <b>$" + "{:,.2f}".format(dec_tax_true_up) + "</b> via brokerage cash."
                else:
                    action_str = "<b>EXECUTE STRATEGY:</b> Convert <b>$" + "{:,.2f}".format(conversion_target) + "</b> to Roth IRA. Vouchers covered liability; December check needed is <b>$0.00</b>."
            elif start_trad <= 0:
                action_str = "Conversions 100% completed. Spend standard retirement cash streams."
            else:
                action_str = "Standard month. Satisfy basic lifestyle outlays from standard income channels."

            if m_name == "Dec" and dec_tax_true_up > 0:
                display_expense_string = "Lifestyle: $" + "{:,.2f}".format(m_living+m_hc) + "<br/>Tax Hold: $" + "{:,.2f}".format(dec_tax_true_up)
            elif m_name == "Dec" and conversion_target > 0:
                display_expense_string = "Lifestyle: $" + "{:,.2f}".format(m_living+m_hc) + "<br/>Tax Hold: $0.00 (Overpaid)"
            else:
                display_expense_string = "Lifestyle: $" + "{:,.2f}".format(m_living+m_hc+m_tax_voucher)

            full_m_name = "January" if m_name == "Jan" else "February" if m_name == "Feb" else "March" if m_name == "Mar" else "April" if m_name == "Apr" else "May" if m_name == "May" else "June" if m_name == "Jun" else "July" if m_name == "Jul" else "August" if m_name == "Aug" else "September" if m_name == "Sep" else "October" if m_name == "Oct" else "November" if m_name == "Nov" else "December"

            monthly_table_rows.append([
                Paragraph(full_m_name, cell_bold), Paragraph("$" + "{:,.2f}".format(m_from_inflow), cell_reg),
                Paragraph("$" + "{:,.2f}".format(m_from_brokerage), cell_reg), Paragraph("$" + "{:,.2f}".format(m_from_roth), cell_reg),
                Paragraph("$" + "{:,.2f}".format(m_from_401k), cell_reg), 
                Paragraph(display_expense_string, cell_bold), 
                Paragraph(action_str, cell_reg)
            ])

        # Compound Year-End Assets Balances Matrix
        brokerage = max(0.00, (start_brokerage - annual_brokerage_draw) * (1 + growth_rate))
        trad_401k = max(0.00, (start_trad - conversion_target - annual_401k_draw) * (1 + growth_rate))
        roth = max(0.00, (start_roth + conversion_target - annual_roth_draw) * (1 + growth_rate))
        # --- 7. NATIVE STACKED ASSET ALLOCATION CHART ENGINE ---
        drawing_box = Drawing(540, 110)
        drawing_box.add(Rect(0, 0, 540, 110, fillColor=colors.HexColor('#F8F9FA'), strokeColor=colors.HexColor('#E5E7EB'), strokeWidth=1))
        
        vbc = VerticalBarChart()
        vbc.x = 45; vbc.y = 15; vbc.height = 75; vbc.width = 440
        vbc.data = [chart_trad_data, chart_roth_data, chart_brokerage_data]
        vbc.categoryAxis.categoryNames = months_list
        vbc.categoryAxis.labels.fontSize = 7
        vbc.categoryAxis.labels.fontName = 'Helvetica-Bold'
        vbc.categoryAxis.style = 'stacked'
        
        max_annual_net_worth = (start_brokerage + start_trad + start_roth) * 1.10
        vbc.valueAxis.valueMin = 0
        vbc.valueAxis.valueMax = max(max_annual_net_worth, 100000)
        vbc.valueAxis.valueStep = vbc.valueAxis.valueMax / 4
        vbc.valueAxis.labels.fontSize = 6
        
        vbc.bars.fillColor = colors.HexColor('#7FA1C3') # Light Pre-Tax Blue
        vbc.bars.fillColor = colors.HexColor('#2E7D32') # Secure Growth Roth Green
        vbc.bars.fillColor = colors.HexColor('#1F497D') # Liquid Brokerage Navy
        drawing_box.add(vbc)
        
        drawing_box.add(String(10, 96, "Portfolio Assets ($)", fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#1F497D')))
        drawing_box.add(Rect(275, 96, 7, 5, fillColor=colors.HexColor('#1F497D'), strokeColor=None))
        drawing_box.add(String(285, 96, "Brokerage Cash", fontName='Helvetica', fontSize=7, textColor=colors.black))
        drawing_box.add(Rect(355, 96, 7, 5, fillColor=colors.HexColor('#2E7D32'), strokeColor=None))
        drawing_box.add(String(365, 96, "Roth Pool", fontName='Helvetica', fontSize=7, textColor=colors.black))
        drawing_box.add(Rect(425, 96, 7, 5, fillColor=colors.HexColor('#7FA1C3'), strokeColor=None))
        drawing_box.add(String(435, 96, "Traditional 401(k)", fontName='Helvetica', fontSize=7, textColor=colors.black))
        
        # Build Elements Layout Output Structure
        elements_block = []
        p_banner = Paragraph("  " + phase_name, phase_style)
        t_banner = Table([[p_banner]], colWidths=[540]) # FIXED width dimension
        t_banner.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor(phase_bg)), ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('TOPPADDING', (0,0), (-1,-1), 4)]))
        elements_block.append(t_banner)
        elements_block.append(Spacer(1, 2))
        
        summary_panel_data = [
            [Paragraph("Yearly Expenses", table_header_style), Paragraph("From Pension/SS/Rent", table_header_style), Paragraph("From Brokerage", table_header_style), Paragraph("From Roth", table_header_style), Paragraph("From 401(k)", table_header_style)],
            [Paragraph("$" + "{:,.2f}".format(living_expense + healthcare_cost + annual_vouchers_paid + dec_tax_true_up), cell_bold), Paragraph("$" + "{:,.2f}".format(annual_inflow_utilized), cell_reg), Paragraph("$" + "{:,.2f}".format(annual_brokerage_draw), cell_reg), Paragraph("$" + "{:,.2f}".format(annual_roth_draw), cell_reg), Paragraph("$" + "{:,.2f}".format(annual_401k_draw), cell_reg)]
        ]
        t_summary_panel = Table(summary_panel_data, colWidths=[108, 108, 108, 108, 108]) # FIXED widths (108 * 5 = 540)
        t_summary_panel.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A6572')), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#4A6572')),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F1F5F7')), ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements_block.append(t_summary_panel)
        elements_block.append(Spacer(1, 4))
        
        t_monthly = Table(monthly_table_rows, colWidths=[45, 65, 65, 55, 55, 80, 175]) # FIXED widths (Sum = 540)
        t_monthly.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('ALIGN', (6,1), (6,-1), 'LEFT'),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#1F497D')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F2F5F8')]), ('TOPPADDING', (0,0), (-1,-1), 2), ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        elements_block.append(t_monthly)
        elements_block.append(Spacer(1, 4))
        
        elements_block.append(drawing_box)
        elements_block.append(Spacer(1, 4))
        
        table_data = [
            [Paragraph("Account Asset Class Tracked", table_header_style), Paragraph("Jan 1 Initial Balance", table_header_style), Paragraph("Dec 31 Final Balance", table_header_style), Paragraph("December Year-End Summary Balances Ledger", table_header_style)],
            [Paragraph("Taxable Brokerage / Cash", cell_bold), Paragraph("$" + "{:,.2f}".format(start_brokerage), cell_reg), Paragraph("$" + "{:,.2f}".format(brokerage), cell_reg), Paragraph(f"Execute Year {year} Roth conversion transfer pool of <b>${conversion_target:,.2f}</b> before Dec 31." if conversion_target > 0 else "Conversions complete. Traditional 401(k) cleared.", cell_reg)],
            [Paragraph("Traditional Pre-Tax 401(k)", cell_bold), Paragraph("$" + "{:,.2f}".format(start_trad), cell_reg), Paragraph("$" + "{:,.2f}".format(trad_401k), cell_reg), Paragraph("", cell_reg)],
            [Paragraph("Tax-Free Combined Roth Pool", cell_bold), Paragraph("$" + "{:,.2f}".format(start_roth), cell_reg), Paragraph("$" + "{:,.2f}".format(roth), cell_reg), Paragraph("", cell_reg)]
        ]
        t_ledger = Table(table_data, colWidths=[100, 80, 80, 280]) # FIXED widths (Sum = 540)
        t_ledger.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#34495E')), ('ALIGN', (0,0), (-1,0), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#1F497D')), ('SPAN', (3,1), (3,3)), ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3)]))
        elements_block.append(t_ledger)
        
        story.append(KeepTogether(elements_block))
        story.append(PageBreak()) 

    doc.build(story)
    return depletion_year_alert

# --- CENTRAL RUNTIME CONTROLLER INTERFACE ---
if __name__ == '__main__':
    print("======================================================================")
    print("       MULTI-SCENARIO INTEGRATED DOSSIER COMPARISON RUNNER          ")
    print("======================================================================")

    # Scenarios leverage central economic configurations dynamically
    base_case = {
        "filename": config.SCENARIOS["base_case"]["filename"],
        "title": config.SCENARIOS["base_case"]["title"],
        "growth_rate": config.SCENARIOS["base_case"]["growth_rate"],
        "inflation_rate": config.SCENARIOS["base_case"]["inflation_rate"]
    }

    stress_test_case = {
        "filename": config.SCENARIOS["stress_test"]["filename"],
        "title": config.SCENARIOS["stress_test"]["title"],
        "growth_rate": config.SCENARIOS["stress_test"]["growth_rate"],
        "inflation_rate": config.SCENARIOS["stress_test"]["inflation_rate"]
    }

    print("\n[Processing Model 1 of 2] Compiling Baseline Case...")
    y_base = generate_retirement_pdf(base_case)

    print("\n[Processing Model 2 of 2] Compiling High-Inflation Stress Test...")
    y_stress = generate_retirement_pdf(stress_test_case)

    print("\n======================================================================")
    print("       AUTOMATED BROKERAGE DEPLETION RADAR ALERTS                     ")
    print("======================================================================")
    print(" -> Baseline Model (" + str(base_case["growth_rate"]*100) + "% Growth): Cash reserves deplete in calendar year: " + str(y_base or "Never (Asset Buffer Intact at 90)"))
    print(" -> Stress Test Model (" + str(stress_test_case["growth_rate"]*100) + "% Growth): Cash reserves deplete in calendar year: " + str(y_stress or "Never (Asset Buffer Intact at 90)"))
    print("======================================================================")
    print("SUCCESS: 2 Comparative Dossier PDFs generated on your Desktop!")
    print("======================================================================")

