# -*- coding: utf-8 -*-
"""
CENTRALIZED RETIREMENT STRATEGY PARAMETERS COMMAND CENTER
Modifying values here updates both compare.py and gen_excel.py instantly.
"""

# 1. Timeline & Demographics
WIFE_START_AGE = 47
HUSBAND_START_AGE = 46


# NEW PARAMETER: Specify the exact calendar month you choose to begin retirement
# Options: "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
RETIREMENT_START_MONTH = "Feb"

AVAILABLE_BRACKET_CHOICES = [0, 22, 24]

PHASE_1_DURATION_YEARS = 7  # Specify exactly how long Phase 1 (Low Income/Holiday) runs

# --- Open config.py and restore your real starting balances ---
STARTING_BALANCES = {
    "brokerage_1": 91313.29,
    "brokerage_2": 15673.00,
    "house_sale_proceeds": 300000.00,  # Re-injects your $350k sales proceed shield
    "house_equity_invested": 0.00,
    "trad_401k": 1476432.85,
    "roth_pool": 130967.93             # CRITICAL: Restore your grandfathered baseline pool
}


TOTAL_INITIAL_BROKERAGE = (
    STARTING_BALANCES["brokerage_1"] + 
    STARTING_BALANCES["brokerage_2"] + 
    STARTING_BALANCES["house_sale_proceeds"] + 
    STARTING_BALANCES["house_equity_invested"]
)

# 3. Market and Yield Economic Parameters
GROWTH_RATE = 0.06             # 6.0% Portfolio Core Growth Rate
CASH_YIELD_RATE = 0.04         # 4.0% HYSA / Cash Yield Rate
INFLATION_RATE = 0.03          # 3.0% Baseline Consumer Inflation

# 4. Cash Inflow Stream Vectors
ANNUAL_PENSION_VALUE = 35250.00      # Wife Pension Income Stream (Age 61)
ANNUAL_SOCIAL_SECURITY = 100000.00   # Social Security Income Stream (Age 62)

# --- 5. Lifestyle Spending and Outflow Targets ---
SPENDING = {
    "phase1_living_expense": 65000.00,
    "phase1_healthcare_cost": 0.00,
    "phase1_rental_income": 24000.00,
    "phase2_living_expense": 100000.00,
    "phase2_healthcare_cost": 9600.00
}

# --- ADDED: RETIREMENT LIFESTYLE AGING "SMILE CURVE" MODIFIERS ---
LIFESTYLE_AGING_MODIFIERS = {
    "age_70_slow_go": 0.85,  # 15% Real drop in standard lifestyle outlays at Age 70
    "age_80_no_go": 0.70     # 30% Real drop in standard lifestyle outlays at Age 80
}

# 6. Multi-Authority Tax Exemption Shields
TAX_SHIEILDS = {
    "federal_standard_deduction": 33200.00,  
    "senior_filer_bonus": 1650.00,           
    "fed_tax_rate": 0.15,                    
    "nm_joint_exemption": 8000.00,           
    "nm_tax_rate": 0.049,                    
    "aca_magi_ceiling": 85000.00             
}

# 7. Comparative Alternative Scenario Configurations
SCENARIOS = {
    "base_case": {
        "title": "BASELINE STRATEGY REPORT (6% GROWTH)",
        "growth_rate": 0.06,
        "inflation_rate": 0.03,
        "filename": "Retirement_Timeline_BASE_CASE_6pct.pdf"
    },
    "stress_test": {
        "title": "STRESS TEST MATRIX REPORT (4% GROWTH)",
        "growth_rate": 0.04,
        "inflation_rate": 0.045,
        "filename": "Retirement_Timeline_STRESS_TEST_4pct.pdf"
    }
}
# --- 8. CHRONOLOGICAL TAX BRACKET TARGET MAP ---
DYNAMIC_BRACKET_SCHEDULE = [22, 24, 22, 24, 22] # Satisfies your Years 1,4 at 24%, others at 22%
DEFAULT_FALLBACK_BRACKET = 22

# --- 9. PROGRESSIVE MARRIED FILING JOINTLY (MFJ) IRS TAX BRACKET STRUCTURE ---
IRS_MFJ_STANDARD_DEDUCTION = 30000.00
IRS_MFJ_TAX_BRACKETS = [
    (23200.00, 0.10, 0.00),
    (94300.00, 0.12, 2320.00),
    (201050.00, 0.22, 10852.00),
    (383900.00, 0.24, 34337.00),
    (487450.00, 0.32, 78221.00),
    (731200.00, 0.35, 111357.00),
    (float('inf'), 0.37, 196669.50)
]

# --- 10. NEW MEXICO PROGRESSIVE STATE TAX STRUCTURE (MFJ 2026+) ---
NM_MFJ_STANDARD_DEDUCTION = 32200.00
NM_MFJ_TAX_BRACKETS = [
    (8000.00, 0.015, 0.00),
    (25000.00, 0.032, 120.00),
    (50000.00, 0.043, 664.00),
    (100000.00, 0.047, 1739.00),
    (31500.00, 0.049, 4089.00),
    (float('inf'), 0.059, 14624.00)
]

