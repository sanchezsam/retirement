# -*- coding: utf-8 -*-
"""
CENTRALIZED RETIREMENT STRATEGY PARAMETERS COMMAND CENTER
Modifying values here updates both compare.py and gen_excel.py instantly.
Aligns with inflation-adjusted tax structures across all operational runways.
"""

# 1. Timeline & Demographics
WIFE_START_AGE = 47
HUSBAND_START_AGE = 46

# NEW PARAMETER: Specify the exact calendar month you choose to begin retirement
# Options: "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
RETIREMENT_START_MONTH = "Feb"

AVAILABLE_BRACKET_CHOICES = [0, 22, 24]
PHASE_1_DURATION_YEARS = 7  # Specify exactly how long Phase 1 (Low Income/Holiday) runs

# 2. Starting Asset Balances
STARTING_BALANCES = {
    "brokerage_1": 71313.29,
    "brokerage_2": 15673.00,
    "house_sale_proceeds": 350000.00,  # Re-injects your $300k sales proceed shield
    "house_equity_invested": 0.00,
    "trad_401k": 1476432.85,
    "roth_pool": 130967.93             # CRITICAL: Grandfathered baseline pool
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

# 5. Lifestyle Spending and Outflow Targets
SPENDING = {
    "phase1_living_expense": 65000.00,
    "phase1_healthcare_cost": 0.00,
    "phase1_rental_income": 24000.00,
    #"phase1_rental_income": 0.00,
    "phase2_living_expense": 100000.00,
    "phase2_healthcare_cost": 9600.00
}

# RETIREMENT LIFESTYLE AGING "SMILE CURVE" MODIFIERS
LIFESTYLE_AGING_MODIFIERS = {
    "age_70_slow_go": 0.85,  # 15% Real drop in standard lifestyle outlays at Age 70
    "age_80_no_go": 0.70     # 30% Real drop in standard lifestyle outlays at Age 80
}

# 6. Multi-Authority Tax Exemption Shields
TAX_SHIELDS = {
    "federal_standard_deduction": 33200.00,  # Updated for 2027 parameters
    "senior_filer_bonus": 1650.00,           
    "fed_tax_rate": 0.15,                    
    "nm_joint_exemption": 33200.00,          # Updated: NM conforms to federal deduction standard
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

# 8. CHRONOLOGICAL TAX BRACKET TARGET MAP
DYNAMIC_BRACKET_SCHEDULE = [22, 24, 22, 24, 22] 
DEFAULT_FALLBACK_BRACKET = 22

# 9. PROGRESSIVE MARRIED FILING JOINTLY (MFJ) IRS TAX BRACKET STRUCTURE
# Adjusted upward to map true projected 2027 parameters (preventing artificial bracket creep)
IRS_MFJ_STANDARD_DEDUCTION = 33200.00
IRS_MFJ_TAX_BRACKETS = [
    (24800.00, 0.10, 0.00),
    (100800.00, 0.12, 2480.00),
    (218250.00, 0.22, 11600.00),  # Adjusted 22% Ceiling
    (416650.00, 0.24, 35439.00),  # Adjusted 24% Ceiling
    (529150.00, 0.32, 82455.00),
    (793750.00, 0.35, 117455.00),
    (float('inf'), 0.37, 207565.00)
]

# 10. NEW MEXICO PROGRESSIVE STATE TAX STRUCTURE (MFJ 2026+)
NM_MFJ_STANDARD_DEDUCTION = 33200.00
NM_MFJ_TAX_BRACKETS = [
    (8000.00, 0.015, 0.00),
    (16000.00, 0.035, 120.00),
    (24000.00, 0.047, 400.00),
    (315000.00, 0.049, 776.00),  # Corrected Graduation Bracket Ceiling
    (float('inf'), 0.059, 15035.00)
]

