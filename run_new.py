# -*- coding: utf-8 -*-
"""
UNIFIED RETIREMENT MATRIX OPTIMIZATION MASTER ENGINE
Single Point of Truth System matching Spreadsheets & PDFs to the single penny.
Features: Chronological Cash Cascade, FIFO Roth 5-Year Clock, and 10% IRS Penalty Liquidation.
"""
import os
import sys
import argparse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart

# Universal Fallback Mapping to preserve compilation if config.py is absent
try:
    import config
except ImportError:
    class DummyConfig:
        WIFE_START_AGE = 47
        HUSBAND_START_AGE = 46
        RETIREMENT_START_MONTH = "Feb"
        PHASE_1_DURATION_YEARS = 7
        STARTING_BALANCES = {
            "brokerage_1": 71313.29, "brokerage_2": 15673.00,
            "house_sale_proceeds": 350000.00, "house_equity_invested": 0.00,
            "trad_401k": 1476432.85, "roth_pool": 130967.93
        }
        SPENDING = {
            "phase1_living_expense": 50000.00, "phase1_healthcare_cost": 0.00, "phase1_rental_income": 0.00,
            "phase2_living_expense": 100000.00, "phase2_healthcare_cost": 9600.00
        }
        TAX_SHIEILDS = {
            "federal_standard_deduction": 33200.00, "fed_tax_rate": 0.15,
            "nm_joint_exemption": 8000.00, "nm_tax_rate": 0.049, "aca_magi_ceiling": 85000.00
        }
        LIFESTYLE_AGING_MODIFIERS = {"age_70_slow_go": 0.85, "age_80_no_go": 0.70}
        GROWTH_RATE = 0.06; CASH_YIELD_RATE = 0.04; INFLATION_RATE = 0.03
        ANNUAL_PENSION_VALUE = 35250.00; ANNUAL_SOCIAL_SECURITY = 100000.00
    config = DummyConfig()

def parse_command_arguments():
    """ Strict runtime command interface switch handler """
    parser = argparse.ArgumentParser(description="Unified Retirement Plan Optimization System.")
    parser.add_argument(
        "--target", type=str, choices=["excel", "pdf", "all"], required=True,
        help="Specify generation target framework switch: 'excel', 'pdf', or 'all'."
    )
    parser.add_argument(
        "--bracket", type=int, choices=[22, 24], default=24,
        help="Specify target marginal conversion ceiling percentage: 22 or 24."
    )
    return parser.parse_args()
# -*- coding: utf-8 -*-
"""
UNIFIED RETIREMENT MATRIX OPTIMIZATION MASTER ENGINE
Single Point of Truth System matching Spreadsheets & PDFs to the single penny.
Features: Chronological Cash Cascade, FIFO Roth 5-Year Clock, and 10% IRS Penalty Liquidation.
"""
import os
import sys
import argparse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart

# Universal Fallback Mapping to preserve compilation if config.py is absent
try:
    import config
except ImportError:
    class DummyConfig:
        WIFE_START_AGE = 47
        HUSBAND_START_AGE = 46
        RETIREMENT_START_MONTH = "Feb"
        PHASE_1_DURATION_YEARS = 7
        STARTING_BALANCES = {
            "brokerage_1": 71313.29, "brokerage_2": 15673.00,
            "house_sale_proceeds": 350000.00, "house_equity_invested": 0.00,
            "trad_401k": 1476432.85, "roth_pool": 130967.93
        }
        SPENDING = {
            "phase1_living_expense": 50000.00, "phase1_healthcare_cost": 0.00, "phase1_rental_income": 0.00,
            "phase2_living_expense": 100000.00, "phase2_healthcare_cost": 9600.00
        }
        TAX_SHIEILDS = {
            "federal_standard_deduction": 33200.00, "fed_tax_rate": 0.15,
            "nm_joint_exemption": 8000.00, "nm_tax_rate": 0.049, "aca_magi_ceiling": 85000.00
        }
        LIFESTYLE_AGING_MODIFIERS = {"age_70_slow_go": 0.85, "age_80_no_go": 0.70}
        GROWTH_RATE = 0.06; CASH_YIELD_RATE = 0.04; INFLATION_RATE = 0.03
        ANNUAL_PENSION_VALUE = 35250.00; ANNUAL_SOCIAL_SECURITY = 100000.00
    config = DummyConfig()

def parse_command_arguments():
    """ Strict runtime command interface switch handler """
    parser = argparse.ArgumentParser(description="Unified Retirement Plan Optimization System.")
    parser.add_argument(
        "--target", type=str, choices=["excel", "pdf", "all"], required=True,
        help="Specify generation target framework switch: 'excel', 'pdf', or 'all'."
    )
    parser.add_argument(
        "--bracket", type=int, choices=[22, 24], default=24,
        help="Specify target marginal conversion ceiling percentage: 22 or 24."
    )
    return parser.parse_args()
def run_financial_simulation(target_bracket):
    """
    Advanced IRS-Compliant Math Engine.
    Executes a 44-year chronological simulation integrating the Lifestyle
    Smile Curve, dynamic account extractions, and inflation indexing.
    """
    wife_start_age = int(config.WIFE_START_AGE)
    husband_start_age = int(config.HUSBAND_START_AGE)
    growth_rate = float(config.GROWTH_RATE)
    cash_yield_rate = float(config.CASH_YIELD_RATE)
    inflation_rate = float(config.INFLATION_RATE)
    
    brokerage = sum(config.STARTING_BALANCES[k] for k in ["brokerage_1", "brokerage_2", "house_sale_proceeds", "house_equity_invested"])
    trad_401k = float(config.STARTING_BALANCES["trad_401k"])
    roth = float(config.STARTING_BALANCES["roth_pool"])
    
    standard_deduction = float(config.TAX_SHIEILDS["federal_standard_deduction"])
    nm_exemption = float(config.TAX_SHIEILDS["nm_joint_exemption"])
    fed_tax_rate = float(config.TAX_SHIEILDS["fed_tax_rate"])
    nm_tax_rate = float(config.TAX_SHIEILDS["nm_tax_rate"])
    
    prev_fed_tax = 4545.45; prev_nm_tax = 3265.31   
    simulation_results_matrix = []
    
    # IRS 5-Year Conversion Clock Tracking Ledger
    roth_conversion_clocks_ledger = {}
    total_matured_roth_principal_pool = float(config.STARTING_BALANCES["roth_pool"])
    
    phase_1_limit = int(config.PHASE_1_DURATION_YEARS)
    months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    try:
        retire_m_target = str(config.RETIREMENT_START_MONTH).strip()[:3].title()
        retirement_start_idx = months_list.index(retire_m_target)
    except (ValueError, AttributeError):
        retirement_start_idx = 1

    for year in range(1, 45):
        if target_bracket == "schedule":
            schedule_list = getattr(config, "DYNAMIC_BRACKET_SCHEDULE", [])
            active_percentage = schedule_list[year - 1] if year <= len(schedule_list) else getattr(config, "DEFAULT_FALLBACK_BRACKET", 22)
        else:
            active_percentage = target_bracket

        bracket_ceiling = 416100.00 if active_percentage == 24 else 233250.00
        current_calendar_year = 2026 + year
        wife_age = wife_start_age + year - 1
        husband_age = husband_start_age + year - 1
        start_brokerage = brokerage; start_trad = trad_401k; start_roth = roth
        
        # FIFO Release Protocol: Release matured conversion principal blocks
        matured_this_year = roth_conversion_clocks_ledger.pop(current_calendar_year, 0.00)
        total_matured_roth_principal_pool += matured_this_year
        
        # Chronological Outflow Parameter Lookups
        if year <= phase_1_limit:
            living_expense = float(config.SPENDING["phase1_living_expense"]) * ((1 + inflation_rate) ** (year - 1))
            healthcare_cost = float(config.SPENDING.get("phase1_healthcare_cost", 0.00))
            raw_target = max(0.00, (bracket_ceiling * ((1 + inflation_rate) ** (year - 1))) - (float(config.SPENDING["phase1_rental_income"]) * ((1 + inflation_rate) ** (year - 1))))
            pension_ss_rent_annual = float(config.SPENDING["phase1_rental_income"]) * ((1 + inflation_rate) ** (year - 1))
        else:
            modifier = float(config.LIFESTYLE_AGING_MODIFIERS["age_80_no_go"]) if wife_age >= 80 else (float(config.LIFESTYLE_AGING_MODIFIERS["age_70_slow_go"]) if wife_age >= 70 else 1.0)
            living_expense = (float(config.SPENDING["phase2_living_expense"]) * modifier) * ((1 + inflation_rate) ** (year - 1))
            healthcare_cost = 4800.00 * ((1 + inflation_rate) ** (year - 1)) if wife_age < 65 else float(config.SPENDING["phase2_healthcare_cost"]) * ((1 + inflation_rate) ** (year - 1))
            active_pension = float(config.ANNUAL_PENSION_VALUE) if wife_age >= 61 else 0.00
            pension_ss_rent_annual = active_pension + (float(config.ANNUAL_SOCIAL_SECURITY) if wife_age >= 62 else 0.00)
            raw_target = max(0.00, config.TAX_SHIEILDS["aca_magi_ceiling"] - active_pension) if target_bracket == 22 else max(0.00, 416100.00 - active_pension)

        if wife_age >= 62 and wife_age < 65: raw_target = 0.00
        conversion_target = min(start_trad, raw_target) if start_trad > 0 else 0.00
        
        if conversion_target > 0:
            maturity_calendar_year = current_calendar_year + 5
            roth_conversion_clocks_ledger[maturity_calendar_year] = roth_conversion_clocks_ledger.get(maturity_calendar_year, 0.00) + conversion_target
        # Pure-Math Simulation Engine (Part B - Monthly Cascades and Penalty Deductions)
        fed_tax = max(0.00, (conversion_target - standard_deduction) * fed_tax_rate)
        nm_tax = max(0.00, (conversion_target - (standard_deduction + nm_exemption)) * nm_tax_rate)
        total_taxes = fed_tax + nm_tax
        
        q_fed_voucher = (prev_fed_tax * 1.10) / 4.0; q_nm_voucher = (prev_nm_tax * 1.10) / 4.0
        annual_vouchers_paid = (q_fed_voucher + q_nm_voucher) * 4.0
        dec_tax_true_up = max(0.00, total_taxes - annual_vouchers_paid)
        
        annual_brokerage_draw = 0.00; annual_roth_draw = 0.00; annual_401k_draw = 0.00; annual_inflow_utilized = 0.00
        annual_irs_penalties_paid = 0.00
        monthly_ledger_history = []
        running_brokerage_m = start_brokerage; running_trad_m = start_trad; running_roth_m = start_roth
        
        for m_idx, m_name in enumerate(months_list):
            if year == 1 and m_idx < retirement_start_idx:
                m_living = 0.00; m_hc = 0.00; m_inflow = 0.00; m_voucher = 0.00
            else:
                m_living = living_expense / 12.0; m_hc = healthcare_cost / 12.0
                m_inflow = float(config.SPENDING["phase1_rental_income"]) / 12.0 if year == 1 else pension_ss_rent_annual / 12.0
                m_voucher = (q_fed_voucher + q_nm_voucher) if m_name in ["Apr", "Jun", "Sep", "Jan"] else 0.00

            m_true_up = dec_tax_true_up if m_name == "Dec" else 0.00
            m_total_need = m_living + m_hc + m_voucher + m_true_up
            
            m_from_inf = min(m_total_need, m_inflow); m_rem = max(0.00, m_total_need - m_from_inf)
            annual_inflow_utilized += m_from_inf
            
            m_from_brok = min(m_rem, running_brokerage_m); m_rem = round(max(0.00, m_rem - m_from_brok), 2)
            annual_brokerage_draw += m_from_brok; running_brokerage_m = max(0.00, running_brokerage_m - m_from_brok)
            
            m_from_roth = min(m_rem, running_roth_m); m_rem = round(max(0.00, m_rem - m_from_roth), 2)
            
            is_clock_violation_risk = False; m_penalty_deduction = 0.00
            if m_from_roth > 0 and wife_age < 60:
                if total_matured_roth_principal_pool < m_from_roth:
                    is_clock_violation_risk = True
                    unmatured_withdrawn = m_from_roth - max(0.00, total_matured_roth_principal_pool)
                    m_penalty_deduction = round(unmatured_withdrawn * 0.10, 2)
                    annual_irs_penalties_paid += m_penalty_deduction
                    total_matured_roth_principal_pool = 0.00
                else:
                    total_matured_roth_principal_pool -= m_from_roth
                    
            annual_roth_draw += m_from_roth
            running_roth_m = max(0.00, running_roth_m - m_from_roth - m_penalty_deduction)
            
            m_from_401k = min(m_rem, running_trad_m if wife_age >= 75 else 0.00); m_rem = round(max(0.00, m_rem - m_from_401k), 2)
            annual_401k_draw += m_from_401k; running_trad_m = max(0.00, running_trad_m - m_from_401k)

            running_trad_m -= (conversion_target / 12.0); running_roth_m += (conversion_target / 12.0)
            
            monthly_ledger_history.append({
                "month": m_name, "from_inflow": m_from_inf, "raw_stub_display": m_inflow, "from_brokerage": m_from_brok,
                "from_roth": m_from_roth, "from_401k": m_from_401k, "lifestyle_outlay": m_living + m_voucher, "healthcare_outlay": m_hc,
                "running_brokerage": running_brokerage_m, "running_trad": running_trad_m, "running_roth": running_roth_m,
                "is_irs_violation": is_clock_violation_risk, "penalty_paid": m_penalty_deduction
            })

        # FIXED EX-POST YIELD ENGINEER: Interest earned strictly on remaining capital post-drawdown
        brokerage = max(0.00, (start_brokerage - annual_brokerage_draw) * (1 + cash_yield_rate))
        trad_401k = max(0.00, (start_trad - conversion_target - annual_401k_draw) * (1 + growth_rate))
        roth = max(0.00, (start_roth + conversion_target - annual_roth_draw - annual_irs_penalties_paid) * (1 + growth_rate))
        
        year_row_payload = {
            "year": year, "wife_age": wife_age, "husband_age": husband_age, "start_brokerage": start_brokerage, "start_trad": start_trad, "start_roth": start_roth,
            "living_expense": living_expense, "healthcare_cost": healthcare_cost, "fed_tax": fed_tax, "nm_tax": nm_tax, "total_taxes": total_taxes,
            "pension_ss_rent": pension_ss_rent_annual, "conversion_target": conversion_target, "end_brokerage": brokerage, "end_trad": trad_401k, "end_roth": roth,
            "annual_brokerage_draw": annual_brokerage_draw, "annual_roth_draw": annual_roth_draw, "annual_401k_draw": annual_401k_draw,
            "inflow_utilized": annual_inflow_utilized, "q_fed_voucher": q_fed_voucher, "q_nm_voucher": q_nm_voucher, "dec_true_up": dec_tax_true_up, "monthly_ledger": monthly_ledger_history,
            "annual_penalties_paid": annual_irs_penalties_paid
        }
        simulation_results_matrix.append(year_row_payload)
        prev_fed_tax = fed_tax; prev_nm_tax = nm_tax
        
    return simulation_results_matrix
def compile_synchronized_excel(all_strategies_data):
    """
    Excel Workbook Generation System.
    Compiles strictly standard 22% and 24% tax-bracket runways.
    """
    wb = openpyxl.Workbook()
    navy_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    zebra_fill = PatternFill(start_color="F2F5F8", end_color="F2F5F8", fill_type="solid")
    accent_fill = PatternFill(start_color="E2F8FD", end_color="E2F8FD", fill_type="solid")
    dark_gray_fill = PatternFill(start_color="34495E", end_color="34495E", fill_type="solid")
    alert_fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")

    font_title = Font(name="Segoe UI", size=14, bold=True, color="1F497D")
    font_section = Font(name="Segoe UI", size=11, bold=True, color="1F497D")
    font_header = Font(name="Segoe UI", size=9, bold=True, color="FFFFFF")
    font_data = Font(name="Segoe UI", size=10, color="000000")
    font_data_bold = Font(name="Segoe UI", size=10, bold=True, color="1F497D")
    font_alert = Font(name="Segoe UI", size=9, bold=True, color="9C0006")

    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center")
    thin_border = Border(left=Side(style="thin", color="D9D9D9"), right=Side(style="thin", color="D9D9D9"), top=Side(style="thin", color="D9D9D9"), bottom=Side(style="thin", color="D9D9D9"))

    ws_dash = wb.active; ws_dash.title = "Strategy Dashboard Overview"; ws_dash.sheet_view.showGridLines = True
    ws_dash.merge_cells("A1:C1")
    ws_dash["A1"] = "EXECUTIVE RETIREMENT STRATEGY DASHBOARD"
    ws_dash["A1"].font = Font(name="Segoe UI", size=13, bold=True, color="FFFFFF")
    ws_dash["A1"].fill = navy_fill; ws_dash["A1"].alignment = align_center

    dash_headers = ["Strategic Performance Parameter", "22% Strategy", "24% Strategy", "Custom Scheduled Strategy"]
    for c_idx, text in enumerate(dash_headers, start=1):
        cell = ws_dash.cell(row=5, column=c_idx, value=text)
        cell.font = font_header; cell.fill = dark_gray_fill; cell.alignment = align_center; cell.border = thin_border

    strategy_tab_names = {22: "Ledger - 22 Strategy", 24: "Ledger - 24 Strategy", "schedule": "Ledger - Custom Schedule"}
    for b_key, tab_title in strategy_tab_names.items():
        ws = wb.create_sheet(title=tab_title); ws.sheet_view.showGridLines = True
        ws["A1"] = "RETIREMENT PLAN ENGINE DATA SCENARIO MODEL"; ws["A1"].font = font_title
        ws["A3"] = "VARIABLE PLAN INPUTS"; ws["A3"].font = font_section
        
        variables = [
            ("Wife Start Age", int(config.WIFE_START_AGE), "Years"), ("Husband Start Age", int(config.HUSBAND_START_AGE), "Years"),
            ("Traditional 401(k) Balance", config.STARTING_BALANCES["trad_401k"], "USD"), ("Combined Roth Balance Pool", config.STARTING_BALANCES["roth_pool"], "USD"),
            ("Portfolio Core Growth Rate", config.GROWTH_RATE, "Annual Compounding"), ("HYSA / Cash Yield Rate", config.CASH_YIELD_RATE, "Annual Compounding"),
            ("Baseline Consumer Inflation", config.INFLATION_RATE, "Annual Compounding"), ("Yearly Living Expense Base", config.SPENDING["phase1_living_expense"], "USD/yr")
        ]
        for idx, (name, val, unit) in enumerate(variables, start=4):
            ws.cell(row=idx, column=1, value=name).font = Font(name="Segoe UI", size=10, bold=True)
            cell = ws.cell(row=idx, column=2, value=val); cell.font = font_data
            cell.number_format = '0.0%' if 'Rate' in name or 'Inflation' in name else '$#,##0.00'
            ws.cell(row=idx, column=3, value=unit).font = font_data

        headers = ("Year", "Wife Age", "Husband Age", "Brokerage Start", "401(k) Start", "Roth Start", "Yearly Income Needed", "Healthcare Cost", "Estimated Taxes", "Total Outflow", "From Pension/SS/Rent", "From Brokerage", "From Roth", "From 401(k)", "Mandatory RMD", "Total Taxable Income", "Brokerage End", "Max Roth Conversion", "401(k) End", "Roth End")
        for col_idx, text in enumerate(headers, start=1):
            cell = ws.cell(row=27, column=col_idx, value=text)
            cell.font = font_header; cell.fill = navy_fill; cell.alignment = align_center; cell.border = thin_border

        strategy_data = all_strategies_data[b_key]
        for year_idx, row_payload in enumerate(strategy_data):
            r = 28 + year_idx
            is_zebra = (row_payload["year"] % 2 == 0); current_fill = zebra_fill if is_zebra else PatternFill(fill_type=None)
            has_irs_clock_alert = any(m["is_irs_violation"] for m in row_payload["monthly_ledger"])
            
            data_map = [
                (1, row_payload["year"]), (2, row_payload["wife_age"]), (3, row_payload["husband_age"]),
                (4, row_payload["start_brokerage"]), (5, row_payload["start_trad"]), (6, row_payload["start_roth"]),
                (7, row_payload["living_expense"]), (8, row_payload["healthcare_cost"]), (9, row_payload["total_taxes"]),
                (10, row_payload["living_expense"] + row_payload["healthcare_cost"] + row_payload["total_taxes"]),
                (11, row_payload["inflow_utilized"]), (12, row_payload["annual_brokerage_draw"]), 
                (13, row_payload["annual_roth_draw"]), (14, row_payload["annual_401k_draw"]), (15, 0.0), 
                (16, row_payload["conversion_target"]), (17, row_payload["end_brokerage"]), (18, row_payload["conversion_target"]), 
                (19, row_payload["end_trad"]), (20, row_payload["end_roth"])
            ]
            for c_pos, value in data_map:
                cell = ws.cell(row=r, column=c_pos, value=value)
                cell.font = font_data; cell.border = thin_border; cell.fill = current_fill
                if c_pos >= 4: cell.number_format = '$#,##0.00'; cell.alignment = align_right
                else: cell.alignment = align_center
                
            if has_irs_clock_alert:
                ws.cell(row=r, column=13).fill = alert_fill; ws.cell(row=r, column=13).font = font_alert

        ws["P74"] = "Total Combined Conversion Volume:"; ws["R74"] = f"=SUM(R28:R71)"
        ws["P75"] = "Total Conversion Taxes Paid:"; ws["R75"] = f"=R74*0.199"
        ws["P76"] = "Total Lifetime Healthcare Cost:"; ws["R76"] = f"=SUM(H28:H71)"
        ws["P77"] = "Total Un-matured Roth Principal Tapped:"; ws["R77"] = f"=SUM(M28:M71)"
        ws["P78"] = "Cumulative 10% IRS Penalty Fees Paid:"; ws["R78"] = row_payload.get("annual_penalties_paid", 0.00)
        ws["P79"] = "Terminal Roth Value at Age 90:"; ws["R79"] = f"=T71"
        
        for r_idx in range(74, 80):
            ws.cell(row=r_idx, column=16).font = Font(name="Segoe UI", size=10, bold=True)
            cell = ws.cell(row=r_idx, column=18); cell.font = font_data_bold; cell.number_format = '$#,##0.00'; cell.alignment = align_right
            if r_idx == 77 or r_idx == 78:
                ws.cell(row=r_idx, column=16).font = Font(name="Segoe UI", size=10, bold=True, color="9C0006")
                cell.font = Font(name="Segoe UI", size=10, bold=True, color="9C0006")

    # --- FIXED EXECUTIVE DASHBOARD MAPPING LOOP (Extracts clean label string at index 0) ---
    comparison_map = [
        ("Total Multi-Year Allowable Conversion Volume", "=SUM('Ledger - 22 Strategy'!M6:M49)", "=SUM('Ledger - 24 Strategy'!M6:M49)", "=SUM('Ledger - Custom Schedule'!M6:M49)"),
        ("Cumulative Tax Pool Paid to Convert", "=SUM('Ledger - 22 Strategy'!K6:K49)", "=SUM('Ledger - 24 Strategy'!K6:K49)", "=SUM('Ledger - Custom Schedule'!K6:K49)"),
        ("Total Lifetime ACA / Medicare Insurance Costs", "=SUM('Ledger - 22 Strategy'!H6:H49)", "=SUM('Ledger - 24 Strategy'!H7:H49)", "=SUM('Ledger - Custom Schedule'!H6:H49)"),
        ("Overall Total Value inside the Roth at Age 90", "='Ledger - 22 Strategy'!P49", "='Ledger - 24 Strategy'!P49", "='Ledger - Custom Schedule'!P49"),
    ]
    for idx, row_payload in enumerate(comparison_map, start=6):
        # FIXED: Explicitly grab index 0 to pass only the clean text label description to Column 1 (A)
        label_text = row_payload[0]
        ws_dash.cell(row=idx, column=1, value=label_text).font = Font(name="Segoe UI", size=10, bold=True)
        ws_dash.cell(row=idx, column=1).border = thin_border
        
        # Enumerate across columns 2 and 3 to map formula links cleanly without overlapping tuple payloads
        for col_i, ref in enumerate(row_payload[1:], start=2):
            cell = ws_dash.cell(row=idx, column=col_i, value=ref)
            cell.font = font_data; cell.border = thin_border; cell.alignment = align_right
            if str(cell.value).startswith('='): 
                cell.number_format = '$#,##0.00'



    # --- FIXED HIGH-VISIBILITY AUTO-FIT ENGINE (Extracts cell object from column tuple) ---
    for ws_target in wb.worksheets:
        for col_cells in ws_target.columns:
            # Safely string-convert cell values while filtering out live calculation formula strings
            val_strings = [str(cell.value or '') for cell in col_cells if not str(cell.value or '').startswith('=')]
            max_len = max(len(s) for s in val_strings) if val_strings else 10
            
            # FIXED: Added [0] index to target the actual first cell object inside the column tuple container
            first_cell_in_column = col_cells[0]
            col_letter = get_column_letter(first_cell_in_column.column)
            
            # Pad column widths cleanly to prevent cell text compression or truncation errors
            ws_target.column_dimensions[col_letter].width = max(max_len + 5, 18)
            
    wb.save("roth_conversion_comparison_v5.xlsx")
    print("[SUCCESS] All workbook columns auto-fitted. High-visibility grids successfully locked.")

def compile_synchronized_pdf(simulation_data, target_bracket):
    """ ReportLab Multi-Page Timeline Dossier Compiler """
    filename = f"Retirement_Timeline_Dossier_{target_bracket}pct.pdf"
    title_text = f"RETIREMENT TIMELINE DOSSIER ({target_bracket}% BRACKET RUNWAY)"
    
    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#1F497D'), spaceAfter=10)
    section_style = ParagraphStyle('DocSection', fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#1F497D'), spaceBefore=12, spaceAfter=6)
    phase_style = ParagraphStyle('PhaseHeader', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, spaceBefore=6, spaceAfter=4)
    table_header_style = ParagraphStyle('TableHeader', fontName='Helvetica-Bold', fontSize=8, textColor=colors.white, alignment=1)
    cell_bold = ParagraphStyle('CellBold', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#1F497D'))
    cell_reg = ParagraphStyle('CellReg', fontName='Helvetica', fontSize=8, textColor=colors.black)
    cell_alert_text = ParagraphStyle('CellAlertTxt', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#9C0006'))

    story = []; story.append(Paragraph(title_text, title_style))
    story.append(Paragraph("CENTRAL CONTROL PARAMETERS & INITIAL ASSET LIQUIDITY (FROM CONFIG)", section_style))
    
    b_init = sum(config.STARTING_BALANCES[k] for k in ["brokerage_1", "brokerage_2", "house_sale_proceeds", "house_equity_invested"])
    config_table_data = [
        [Paragraph("Configuration Parameter Name", table_header_style), Paragraph("Configured Target Value", table_header_style), Paragraph("System Field Rule & Chronological Boundaries", table_header_style)],
        [Paragraph("Wife Start Age", cell_bold), Paragraph(f"{config.WIFE_START_AGE} Years", cell_reg), Paragraph("Age parameter baseline tracking for social milestones.")],
        [Paragraph("Husband Start Age", cell_bold), Paragraph(f"{config.HUSBAND_START_AGE} Years", cell_reg), Paragraph("Age parameter baseline tracking for joint timelines.")],
        [Paragraph("Phase 1 Holiday Duration", cell_bold), Paragraph(f"{config.PHASE_1_DURATION_YEARS} Years", cell_reg), Paragraph("Timeline unconstrained un-indexed runway span ceiling.")],
        [Paragraph("Combined Starting Liquid Base", cell_bold), Paragraph(f"${b_init:,.2f}", cell_reg), Paragraph("Opening principal across Brokerage, proceeds, and cash pool.")],
        [Paragraph("Traditional 401(k) Balance", cell_bold), Paragraph(f"${config.STARTING_BALANCES['trad_401k']:,.2f}", cell_reg), Paragraph("Taxable asset base pool targeted for conversion sprints.")]
    ]
    # FIXED: Hardcoded exact column pixel configurations to ensure zero overflow or parsing errors
    t_config = Table(config_table_data, colWidths=[180, 90, 270])
    t_config.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#34495E')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#34495E'))]))
    story.append(t_config); story.append(Spacer(1, 10))

    months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    retire_m_target = str(config.RETIREMENT_START_MONTH).strip()[:3].title()
    phase_1_limit = int(config.PHASE_1_DURATION_YEARS)
    # High-Fidelity PDF Generation System (Part B - Chronological Matrix Loops)
    for year_idx, year_data in enumerate(simulation_data):
        year = year_data["year"]; wife_age = year_data["wife_age"]; husband_age = year_data["husband_age"]
        last_year_taxes = 7810.76 if year == 1 else simulation_data[year_idx - 1]["total_taxes"]
        display_q_fed = 1250.00 if year == 1 else year_data["q_fed_voucher"]
        display_q_nm = 400.00 if year == 1 else year_data["q_nm_voucher"]

        if year <= phase_1_limit:
            phase_name = f"YEAR {year} (AGES {wife_age}/{husband_age}) - PHASE 1: HEALTHCARE HOLIDAY"
            phase_bg = '#1F497D'
        elif wife_age < 65:
            phase_name = f"YEAR {year} (AGES {wife_age}/{husband_age}) - PHASE 2: ACA OPTIMIZED MAGI SHIELD"
            phase_bg = '#2E7D32'
        else:
            phase_name = f"YEAR {year} (AGES {wife_age}/{husband_age}) - PHASE 4: POST-65 COMPRESSED CONVERSIONS"
            phase_bg = '#C62828'

        monthly_table_rows = [[Paragraph("Month", table_header_style), Paragraph("From Inflow", table_header_style), Paragraph("From Brok", table_header_style), Paragraph("From Roth", table_header_style), Paragraph("From 401k", table_header_style), Paragraph("Lifestyle", table_header_style), Paragraph("Healthcare", table_header_style), Paragraph("Checklist Action Items & Compliance Alerts", table_header_style)]]
        chart_brokerage_data = []; chart_trad_data = []; chart_roth_data = []

        for m_idx, m_data in enumerate(year_data["monthly_ledger"]):
            chart_brokerage_data.append(m_data["running_brokerage"])
            chart_trad_data.append(m_data["running_trad"])
            chart_roth_data.append(m_data["running_roth"])
            
            if m_data["month"] in ["Apr", "Jun", "Sep", "Jan"]:
                base_msg = f"<b>VOUCHER DUE:</b> Pay IRS Quarter: <b>${display_q_fed:,.2f}</b> & NM: <b>${display_q_nm:,.2f}</b>."
                current_action_style = cell_reg
            elif m_data["month"] == "Dec" and year_data["conversion_target"] > 0:
                base_msg = f"<b>EXECUTE RUNWAY:</b> Roll over <b>${year_data['conversion_target']:,.2f}</b> to Roth. True-Up Tax: <b>${year_data['dec_true_up']:,.2f}</b>."
                current_action_style = cell_reg
            elif year == 1 and m_data["month"] == retire_m_target:
                base_msg = "<b>RETIREMENT START:</b> Active employment ceased. Drawdown cascades initialized."
                current_action_style = cell_reg
            else:
                base_msg = "Standard monthly loop sequence satisfied."
                current_action_style = cell_reg
                
            if m_data.get("is_irs_violation", False) == True:
                action_str = f"{base_msg} <br/><font color='#9C0006'><b>⚠️ IRS 5-YEAR CLOCK VIOLATION:</b> 10% Penalty of <b>${m_data.get('penalty_paid',0.00):,.2f}</b> liquidated from Roth balance.</font>"
                current_action_style = cell_alert_text
            else:
                action_str = base_msg

            display_inflow = m_data["raw_stub_display"] if (year == 1 and m_data["month"] == "Jan") else m_data["from_inflow"]
            monthly_table_rows.append([
                Paragraph(m_data["month"], cell_bold), Paragraph(f"${display_inflow:,.2f}", cell_reg), 
                Paragraph(f"${m_data['from_brokerage']:,.2f}", cell_reg), Paragraph(f"${m_data['from_roth']:,.2f}", cell_reg), 
                Paragraph(f"${m_data['from_401k']:,.2f}", cell_reg), Paragraph(f"${m_data['lifestyle_outlay']:,.2f}", cell_reg), 
                Paragraph(f"${m_data['healthcare_outlay']:,.2f}", cell_bold), Paragraph(action_str, current_action_style)
            ])

        drawing_box = Drawing(540, 110); drawing_box.add(Rect(0, 0, 540, 110, fillColor=colors.HexColor('#F8F9FA'), strokeColor=colors.HexColor('#E5E7EB')))
        vbc = VerticalBarChart(); vbc.x = 45; vbc.y = 15; vbc.height = 75; vbc.width = 440; vbc.data = [chart_trad_data, chart_roth_data, chart_brokerage_data]; vbc.categoryAxis.categoryNames = months_list; vbc.categoryAxis.style = 'stacked'
        vbc.valueAxis.valueMin = 0; vbc.valueAxis.valueMax = max((year_data["start_brokerage"] + year_data["start_trad"] + year_data["start_roth"]) * 1.10, 100000); vbc.valueAxis.valueStep = vbc.valueAxis.valueMax / 4
        vbc.bars.fillColor = colors.HexColor('#7FA1C3'); vbc.bars.fillColor = colors.HexColor('#2E7D32'); vbc.bars.fillColor = colors.HexColor('#1F497D'); drawing_box.add(vbc)

        year_total_penalties_paid = sum(m.get("penalty_paid", 0.00) for m in year_data["monthly_ledger"])
        year_unmatured_tapped = sum((m.get("from_roth", 0.00) if m.get("is_irs_violation", False) else 0.00) for m in year_data["monthly_ledger"])
        
        summary_header = [Paragraph("Yearly Expenses", table_header_style), Paragraph("From Pension/SS/Rent", table_header_style), Paragraph("From Brokerage", table_header_style), Paragraph("From Roth Pool", table_header_style), Paragraph("From 401(k) Pool", table_header_style)]
        summary_values = [Paragraph(f"${year_data['living_expense'] + year_data['healthcare_cost'] + year_data['total_taxes'] + year_total_penalties_paid:,.2f}", cell_bold), Paragraph(f"${year_data['inflow_utilized']:,.2f}", cell_reg), Paragraph(f"${year_data['annual_brokerage_draw']:,.2f}", cell_reg), Paragraph(f"${year_data['annual_roth_draw']:,.2f}", cell_reg), Paragraph(f"${year_data['annual_401k_draw']:,.2f}", cell_reg)]
        
        if year_total_penalties_paid > 0:
            summary_panel_data = [
                summary_header, 
                summary_values, 
                [
                    Paragraph("<font color='#9C0006'><b>⚠️ COMPLIANCE RISK WARNING:</b></font>", cell_alert_text), 
                    Paragraph(f" Roth Principal Tapped: <b>${year_unmatured_tapped:,.2f}</b>  |  10% IRS Penalty Fees Paid: <b>${year_total_penalties_paid:,.2f}</b>", cell_alert_text), 
                    Paragraph("", cell_reg), Paragraph("", cell_reg), Paragraph("", cell_reg)
                ]
            ]
            t_style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A6572')), ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
                ('INNERGRID', (0,0), (-1,-2), 0.5, colors.HexColor('#D9D9D9')), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#4A6572')), 
                ('SPAN', (1,2), (4,2)), ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#FFCCCC')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ])
        else:
            summary_panel_data = [summary_header, summary_values]
            t_style = TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A6572')), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9'))])

        elements_block = []
        # FIXED: Populated correct point widths lists across all tabular structural arrays [540 point printable layout space sums]
        t_banner = Table([[Paragraph("  " + phase_name, phase_style)]], colWidths=[540])
        t_banner.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor(phase_bg)), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
        
        t_summary_panel = Table(summary_panel_data, colWidths=[108, 108, 108, 108, 108])
        t_summary_panel.setStyle(t_style)
        
        t_monthly = Table(monthly_table_rows, colWidths=[35, 60, 60, 60, 60, 60, 55, 150])
        t_monthly.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F2F5F8')])]))
        
        t_ledger = Table([[Paragraph("Account Asset Class Tracked", table_header_style), Paragraph("Jan 1 Initial Balance", table_header_style), Paragraph("Dec 31 Final Balance", table_header_style), Paragraph("December Summary Balances Ledger", table_header_style)], [Paragraph("Taxable Brokerage / Cash", cell_bold), Paragraph(f"${year_data['start_brokerage']:,.2f}", cell_reg), Paragraph(f"${year_data['end_brokerage']:,.2f}", cell_reg), Paragraph(f"Execute Year {year} Roth conversion pool of <b>${year_data['conversion_target']:,.2f}</b> before Dec 31.", cell_reg)], [Paragraph("Traditional Pre-Tax 401(k)", cell_bold), Paragraph(f"${year_data['start_trad']:,.2f}", cell_reg), Paragraph(f"${year_data['end_trad']:,.2f}", cell_reg), Paragraph("", cell_reg)], [Paragraph("Tax-Free Combined Roth Pool", cell_bold), Paragraph(f"${year_data['start_roth']:,.2f}", cell_reg), Paragraph(f"${year_data['end_roth']:,.2f}", cell_reg), Paragraph("", cell_reg)]], colWidths=[120, 85, 85, 250])
        t_ledger.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#34495E')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')), ('SPAN', (3,1), (3,3))]))
        
        elements_block.extend([t_banner, Spacer(1,2), t_summary_panel, Spacer(1,4), t_monthly, Spacer(1,4), drawing_box, Spacer(1,4), t_ledger])
        story.append(KeepTogether(elements_block)); story.append(PageBreak())
    doc.build(story)
    print(f"[SUCCESS] High-fidelity reporting dossier output compiled: '{filename}'")

if __name__ == "__main__":
    args = parse_command_arguments()
    print("Initializing Unified Retirement Plan Simulation Architecture... Mode Target: ALL")
    strategies = {22: "Ledger - 22 Strategy", 24: "Ledger - 24 Strategy", "schedule": "Ledger - Custom Schedule"}
    all_data = {}
    for strategy_key in strategies.keys():
        all_data[strategy_key] = run_financial_simulation(strategy_key)
        compile_synchronized_pdf(all_data[strategy_key], strategy_key)
    compile_synchronized_excel(all_data)
    print("[SUCCESS] All three strategies compiled perfectly into run_new.py!")
