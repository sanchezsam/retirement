# -*- coding: utf-8 -*-
"""
RETIREMENT RUNWAY BALANCES OPTIMIZER - DYNAMIC HYBRID SEPP ENGINE
Compiles pathways, progressive tax metrics, and dynamic drawdown waterfalls.
Safeguards: Dynamic Brokerage Cash Depletion Triggers and IRS Notice 2022-6 SEPP Compliance.
"""

import os
import sys
import itertools
import importlib.util

# Ensure local imports work by appending current script directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    import config
except ImportError:
    print("[ERROR] Optimization script must be placed in the same folder as config.py")
    sys.exit(1)

# IRS Single Life Expectancy Factors (Table I - Reg. § 1.401(a)(9)-9 post-2022 update)
SINGLE_LIFE_EXPECTANCY_TABLE = {
    40: 45.7, 41: 44.8, 42: 43.8, 43: 42.9, 44: 41.9,
    45: 41.0, 46: 40.0, 47: 39.0, 48: 38.1, 49: 37.1,
    50: 36.2, 51: 35.3, 52: 34.3, 53: 33.4, 54: 32.5,
    55: 31.6, 56: 30.6, 57: 29.8, 58: 28.9, 59: 28.0,
    60: 27.1, 61: 26.2, 62: 25.4, 63: 24.5, 64: 23.7,
    65: 22.9, 66: 22.0, 67: 21.2, 68: 20.4, 69: 19.6,
    70: 18.8, 71: 18.0, 72: 17.2, 73: 16.4, 74: 15.6,
    75: 14.8, 76: 14.1, 77: 13.3, 78: 12.6, 79: 11.9,
    80: 11.2, 81: 10.5, 82: 9.9, 83: 9.3, 84: 8.7,
    85: 8.1, 86: 7.6, 87: 7.1, 88: 6.6, 89: 6.1, 90: 5.7
}

# IRS Uniform Lifetime Table for RMD Calculations (Post-2022 standard)
UNIFORM_LIFETIME_TABLE = {
    72: 27.4, 73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7,
    77: 22.9, 78: 22.0, 79: 21.1, 80: 20.2, 81: 19.3,
    82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2,
    87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2
}



def print_dual_pool_ledger(selected_record, rotation_list):
    """
    Isolates and prints a clean, side-by-side annual summary tracking 
    Starting Balances, Growth Gained, Outflow Draws, and Ending Balances 
    for both the Taxable Brokerage and Tax-Free Roth Pools. Includes annual conversions.
    Financial data columns are locked to an identical, rigid 14-character width footprint.
    """
    sim_data = selected_record["simulation_data"]
    pattern_str = " -> ".join(f"{br}%" for br in rotation_list)

    # 5 asset columns for Brokerage + 5 asset columns for Roth (each 14 chars wide + formatting buffers)
    print("\n" + "="*165)
    print(f" ANNUAL BALANCE & FLOW TRACKER MATRIX | STRATEGY: {pattern_str}")
    print("="*165)
    print(f"      | {'--- TAXABLE BROKERAGE ASSET POOL ---':^73} | {'------- TAX-FREE ROTH POOL ASSET VAULT -------':^73} |")
    print(f"H_Age | {'Start Bal':<14} | {'Yield/Gain':<14} | {'Total Draw':<14} | {'End Bal':<14} | {'Start Bal':<14} | {'Amt Convert':<14} | {'Growth/Gain':<14} | {'Total Draw':<14} | {'End Bal':<14} |")
    print("-"*165)
   
    for y_idx, y_row in enumerate(sim_data):
        # Switched to Husband Age milestone tracking natively
        h_age = y_row.get("husband_age", 46 + y_idx)

        # 1. Parse Brokerage Flows Natively
        sb_brok = y_row.get("start_brokerage", 0.00)
        yield_brok = y_row.get("brokerage_gains", 0.00)
        eb_brok = y_row.get("end_brokerage", 0.00)
        draw_brok = sum(m.get("from_brokerage", 0.00) for m in y_row.get("monthly_ledger", []))

        # 2. Parse Roth Flows and Conversion Injections Natively
        sb_roth = y_row.get("start_roth", 0.00)
        eb_roth = y_row.get("end_roth", 0.00)
        actual_conversion = y_row.get("actual_conversion", 0.00)
        draw_roth = sum(m.get("from_roth", 0.00) for m in y_row.get("monthly_ledger", []))

        # Isolate Roth internal compounding growth separate from your rollover injections
        yield_roth = max(0.00, eb_roth + draw_roth - sb_roth - actual_conversion)

        # Convert numerical values into precise, formatted strings to prevent character overlap
        f_sb_brok = f"${sb_brok:,.2f}"
        f_yd_brok = f"${yield_brok:,.2f}"
        f_dr_brok = f"${draw_brok:,.2f}"
        f_eb_brok = f"${eb_brok:,.2f}"
        
        f_sb_roth = f"${sb_roth:,.2f}"
        f_cv_roth = f"${actual_conversion:,.2f}"
        f_yd_roth = f"${yield_roth:,.2f}"
        f_dr_roth = f"${draw_roth:,.2f}"
        f_eb_roth = f"${eb_roth:,.2f}"

        # FORCES EVERY PRIMARY COLUMN TO AN ABSOLUTE 14-CHARACTER whitespace CHANNEL
        print(f" {h_age:<4} | "
              f"{f_sb_brok:<14} | "
              f"{f_yd_brok:<14} | "
              f"{f_dr_brok:<14} | "
              f"{f_eb_brok:<14} | "
              f"{f_sb_roth:<14} | "
              f"{f_cv_roth:<14} | "
              f"{f_yd_roth:<14} | "
              f"{f_dr_roth:<14} | "
              f"{f_eb_roth:<14} |")

    print("="*165)


def calculate_sepp_amortization(principal, age, rate=0.05):
    """Computes the fixed annual payment using the IRS Amortization Method."""
    factor = SINGLE_LIFE_EXPECTANCY_TABLE.get(int(age), 30.0)
    if factor <= 0:
        return 0.00
    numerator = principal * rate
    denominator = 1.0 - ((1.0 + rate) ** (-factor))
    if denominator <= 0:
        return 0.00
    return round(numerator / denominator, 2)

def calculate_empirical_betr(strategy_net_estate, bracket_schedule, custom_brokerage=None, custom_rent=None, custom_living=None):
    """
    Calculates the true empirical Break-Even Tax Rate (BETR).
    Isolates the tax rate threshold below which pre-tax preservation beats conversions.
    Patched to conform corner-to-corner with the single-argument simulation engine signature.
    """
    # 1. Simulate the Zero-Conversion baseline control case
    zero_bracket_schedule = [0] * len(bracket_schedule)
    control_timeline = run_financial_simulation(zero_bracket_schedule)
        
    if not control_timeline:
        return 0.00
        
    control_final = control_timeline[-1]
    control_net_estate = (
        control_final.get("end_brokerage", 0.00) +
        control_final.get("end_trad", 0.00) +
        control_final.get("end_roth", 0.00)
    )   
        
    # 2. Get total conversion volume executed on the active path
    active_timeline = run_financial_simulation(bracket_schedule)
    total_converted = sum(y.get("actual_conversion", 0.00) for y in active_timeline)
    
    if total_converted <= 0 or strategy_net_estate <= control_net_estate:
        return 0.00
     
    # 3. Calculate Strategy Tax Savings Drag Delta
    strategy_lifetime_taxes = sum(y.get("total_taxes", 0.00) for y in active_timeline)
    control_lifetime_taxes = sum(y.get("total_taxes", 0.00) for y in control_timeline)
    tax_saved_delta = max(0.00, control_lifetime_taxes - strategy_lifetime_taxes)
        
    # 4. Hurdle rate calculation
    implied_hurdle = (tax_saved_delta / total_converted) * 100.0
    
    if implied_hurdle == 0.0 or implied_hurdle > 35.0:
        max_active_bracket = max(bracket_schedule) if bracket_schedule else 22
        return round(float(max_active_bracket), 2)

    return round(max(0.00, min(40.0, implied_hurdle)), 2)


def calc_marginal_tax(taxable_income, deduction, brackets):
    """Core mathematical engine for standard progressive tax brackets."""
    net_taxable = max(0.00, taxable_income - deduction)
    if net_taxable <= 0: 
        return 0.00
    
    prev_ceiling = 0.00
    for ceiling, rate, base_tax in brackets:
        if net_taxable <= ceiling:
            return base_tax + (net_taxable - prev_ceiling) * rate
        prev_ceiling = ceiling
    return 0.00


def calculate_progressive_taxes(income):
    """Pulls bracket structures from config and evaluates combined marginal liabilities."""
    fed_brackets = getattr(config, "IRS_MFJ_TAX_BRACKETS", [])
    shields = getattr(config, "TAX_SHIELDS", {})
    
    fed_deduction = shields.get("federal_standard_deduction", getattr(config, "IRS_MFJ_STANDARD_DEDUCTION", 33200.00))
    fed_tax = calc_marginal_tax(income, fed_deduction, fed_brackets)

    nm_brackets = getattr(config, "NM_MFJ_TAX_BRACKETS", [])
    nm_deduction = shields.get("nm_joint_exemption", getattr(config, "NM_MFJ_STANDARD_DEDUCTION", 33200.00))
    nm_tax = calc_marginal_tax(income, nm_deduction, nm_brackets)
    
    # Combined with a plus sign to guarantee a single float output for the loops
    return fed_tax + nm_tax


def run_financial_simulation(rotation_list):
    """
    Natively simulates a comprehensive lifecycle cash flow runway up to Husband Age 90.
    Prioritizes statutory IRS RMDs first at Age 75, stacks them alongside pensions,
    implements a permanent conversion lockout at the SEPP boundary, and routes
    living deficits straight to the Traditional 401(k) via 72(t) penalty-free rails
    during your 50s to completely protect your tax-free Roth core from early draws.
    """
    # 1. Initialize Baseline Assets from Central Command Configuration Center
    traditional_401k = config.STARTING_BALANCES["trad_401k"]
    roth_pool = config.STARTING_BALANCES["roth_pool"]
    brokerage_pool = (config.STARTING_BALANCES["brokerage_1"] + config.STARTING_BALANCES["brokerage_2"] + 
                      config.STARTING_BALANCES["house_sale_proceeds"] + config.STARTING_BALANCES["house_equity_invested"])
    
    # Establish local control variables from parameters
    growth_rate = config.GROWTH_RATE
    inflation_rate = config.INFLATION_RATE
    cash_yield = config.CASH_YIELD_RATE
    spending = config.SPENDING
    
    start_year = getattr(config, "RET_START_YEAR", 2027)
    wife_start_age = config.WIFE_START_AGE
    husband_start_age = config.HUSBAND_START_AGE
    months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    start_month = getattr(config, "RET_START_MONTH", "Jan")
    
    timeline_data = []
    active_conversion_ladder = {}
    
    # STATE MACHINE LATCH: Tracks if the SEPP conversion barrier has been breached
    sepp_has_initiated = False
    
    for year_idx in range(44):
        current_year = start_year + year_idx
        wife_age = wife_start_age + year_idx
        husband_age = husband_start_age + year_idx
        mult = (1.0 + inflation_rate) ** year_idx
        
        # Capture precise start-of-year parameters before transaction loops alter values
        start_brokerage = brokerage_pool
        start_trad = traditional_401k
        start_roth = roth_pool
        
        # TRIGGER: Automatically trip the permanent lockout when entering the SEPP window (Husband Age 52+)
        if husband_age >= 52:
            sepp_has_initiated = True
        
        # 2. Process Core Retirement Income Streams (Pensions, Social Security, Rental checks)
        rent = spending.get("phase1_rental_income", 12000.00) if year_idx < 7 else 0.0
        pension = config.ANNUAL_PENSION_VALUE * mult if wife_age >= 61 else 0.0
        ss = config.ANNUAL_SOCIAL_SECURITY * mult if wife_age >= 62 else 0.0
        natural_inflows = rent + pension + ss
        
        # Calculate inflated lifecycle expenditures
        living_exp = (spending.get("phase1_living_expense", 65000.00) if year_idx < 7 else spending.get("phase2_living_expense", 100000.00)) * mult
        if wife_age >= 70: living_exp *= config.LIFESTYLE_AGING_MODIFIERS.get("age_70_slow_go", 0.85)
        if wife_age >= 80: living_exp *= config.LIFESTYLE_AGING_MODIFIERS.get("age_80_no_go", 0.70)
        health_cost = spending.get("phase2_healthcare_cost", 9600.00) * mult if year_idx >= 7 else 0.0
        base_outflows = living_exp + health_cost
        
        # =========================================================================
        # 4. MANDATORY IRS REQUIRED MINIMUM DISTRIBUTIONS (AGE 75 THRESHOLD)
        # PRIORITIZED: Forced out first to comply with statutory rules before conversions
        # =========================================================================
        from_401k = 0.00
        if husband_age >= 75 and traditional_401k > 500.00:
            divisor = UNIFORM_LIFETIME_TABLE.get(husband_age, 24.6)
            from_401k = traditional_401k / divisor
            traditional_401k -= from_401k
        
              
        # =========================================================================
        # 3. DYNAMIC PARAMETERIZED HYBRID CONVERSION LAYER (CALIBRATED RESIDUAL CORE)
        # =========================================================================
        actual_conversion = 0.00

        # CORE CONSTRAINT: Voluntary conversions are permanently hard-locked at 0.00 if SEPP has started
        if traditional_401k > 500.00 and not sepp_has_initiated:
            target_bracket = rotation_list[year_idx] if year_idx < len(rotation_list) else rotation_list[-1]
            fed_brackets = getattr(config, "IRS_MFJ_TAX_BRACKETS", [])
            conversion_ceiling = 0.00

            for ceiling, rate, base_tax in fed_brackets:
                if rate == (target_bracket / 100.0) or (target_bracket == 12 and rate == 0.12) or (target_bracket == 22 and rate == 0.22) or (target_bracket == 24 and rate == 0.24):
                    conversion_ceiling = ceiling
                    break

            if conversion_ceiling == 0.00 or conversion_ceiling == float('inf'):
                conversion_ceiling = (201050.00 if target_bracket == 24 else (94300.00 if target_bracket == 22 else 23200.00)) * mult
            else:
                conversion_ceiling *= mult

            current_wage_base = 0.00
            if year_idx == 0:
                current_wage_base = getattr(config, "YEAR_1_WAGES", getattr(config, "PARTIAL_YEAR_SALARY", 0.00))

            total_current_ordinary_inflows = natural_inflows + from_401k + current_wage_base

            if conversion_ceiling > total_current_ordinary_inflows:
                # >>> FIXED: CAP RECONCILED VOLUNTARY CONVERSIONS TO LEAVE A HEALTHY RMD CORE PRINCIPAL <<<
                raw_headroom = conversion_ceiling - total_current_ordinary_inflows
                calibrated_conversion = raw_headroom * 0.45
                
                actual_conversion = min(traditional_401k, calibrated_conversion)
                traditional_401k -= actual_conversion
                roth_pool += actual_conversion
                active_conversion_ladder[current_year] = actual_conversion

        # =========================================================================
        # 5. CONFORMED LIFESTYLE LIQUIDATION WATERFALL (SEPP-PRIORITIZED)
        # =========================================================================
        available_cash_pool = natural_inflows + from_401k
        if available_cash_pool > base_outflows:
            surplus_cash = available_cash_pool - base_outflows
            brokerage_pool += surplus_cash
            net_deficit = 0.00
        else:
            net_deficit = max(0.00, base_outflows - available_cash_pool)

        from_brokerage = from_roth = 0.00
        
        # Step A: Exhaust the taxable brokerage cushion first
        if net_deficit > 0:
            from_brokerage = min(brokerage_pool, net_deficit)
            brokerage_pool -= from_brokerage
            net_deficit -= from_brokerage

        # Step B: CORE 72(t) SEPP ROUTING INTEGRATION
        # If inside the active SEPP window (ages 52-59), satisfy lifestyle shortfalls
        # directly from the Traditional 401(k) pre-tax vault penalty-free
        if net_deficit > 0 and (husband_age >= 52 and husband_age < 60):
            from_sepp_401k = min(traditional_401k, net_deficit)
            traditional_401k -= from_sepp_401k
            from_401k += from_sepp_401k
            net_deficit -= from_sepp_401k

        # Step C: Standard Drawdown Fallback (Only touches Roth if outside SEPP or pre-tax is dry)
        if net_deficit > 0:
            from_roth = min(roth_pool, net_deficit)
            roth_pool -= from_roth
            net_deficit -= from_roth
            if net_deficit > 0:
                from_401k += net_deficit
                traditional_401k -= net_deficit

        # =========================================================================
        # 6. FIXED TAX DRAWDOWNS: ITEMIZING JURISDICTIONS AND INITIALIZING VARIABLES
        # =========================================================================
        draw_t_brokerage = 0.00
        draw_t_roth = 0.00

        brokerage_gains = max(0.00, brokerage_pool * cash_yield)
        total_taxable_ordinary_income = actual_conversion + from_401k + brokerage_gains
        
        fed_brackets_calc = getattr(config, "IRS_MFJ_TAX_BRACKETS", [])
        shields_calc = getattr(config, "TAX_SHIELDS", {})
        fed_deduction_calc = shields_calc.get("federal_standard_deduction", getattr(config, "IRS_MFJ_STANDARD_DEDUCTION", 33200.00))
        fed_tax_value = calc_marginal_tax(total_taxable_ordinary_income, fed_deduction_calc, fed_brackets_calc)

        nm_brackets_calc = getattr(config, "NM_MFJ_TAX_BRACKETS", [])
        nm_deduction_calc = shields_calc.get("nm_joint_exemption", getattr(config, "NM_MFJ_STANDARD_DEDUCTION", 33200.00))
        nm_tax_value = calc_marginal_tax(total_taxable_ordinary_income, nm_deduction_calc, nm_brackets_calc)
        
        total_taxes = fed_tax_value + nm_tax_value
        
        # Tax Settlement Waterfall: Sweeps from Roth on brokerage cash exhaustion
        rem_tax_debt = total_taxes
        if rem_tax_debt > 0.00:
            if (brokerage_pool + roth_pool) <= 10.00:
                rem_tax_debt = 0.00
            else:
                draw_t_brokerage = min(brokerage_pool, rem_tax_debt)
                brokerage_pool -= draw_t_brokerage
                rem_tax_debt -= draw_t_brokerage
                
                if rem_tax_debt > 0.00:
                    draw_t_roth = min(roth_pool, rem_tax_debt)
                    roth_pool -= draw_t_roth
                    rem_tax_debt -= draw_t_roth
            
        if total_taxable_ordinary_income > 383900.00 * mult: display_bracket = "24%"
        elif total_taxable_ordinary_income > 201050.00 * mult: display_bracket = "22%"
        elif total_taxable_ordinary_income > 94300.00 * mult: display_bracket = "12%"
        elif total_taxable_ordinary_income > 23200.00 * mult: display_bracket = "10%"
        else: display_bracket = "0%"
            
        # Build out monthly tracking ledger objects for widescreen console rendering
        # Build out monthly tracking ledger objects for widescreen console rendering
        y_from_inflow = min(natural_inflows, living_exp + health_cost)
        monthly_ledger = []
        active_months = months_list if year_idx > 0 else months_list[months_list.index(start_month):]
        num_act = len(active_months)
        for m in months_list:
            if m in active_months:
                monthly_ledger.append({
                    "month": m,
                    "from_brokerage": round(from_brokerage / num_act, 2),
                    "from_roth": round(from_roth / num_act, 2),
                    "from_401k": round(from_401k / num_act, 2),
                    "from_inflow": round(y_from_inflow / num_act, 2)
                })
            else:
                monthly_ledger.append({"month": m, "from_brokerage": 0.00, "from_roth": 0.00, "from_401k": 0.00, "from_inflow": 0.00})
                
        # Cleanly compounds core assets exactly once per year
        traditional_401k *= (1.0 + growth_rate)
        roth_pool *= (1.0 + growth_rate)
        brokerage_pool *= (1.0 + growth_rate)
        
        year_row = {
            "year": current_year, "wife_age": wife_age, "husband_age": husband_age,
            "active_bracket": display_bracket, "start_brokerage": start_brokerage, "start_trad": start_trad, "start_roth": start_roth,
            "end_brokerage": brokerage_pool, "end_trad": traditional_401k, "end_roth": roth_pool,
            "total_taxes": total_taxes, "fed_tax": fed_tax_value, "nm_tax": nm_tax_value,
            "living_expense": living_exp, "healthcare_cost": health_cost,
            "pension_ss_rent": natural_inflows, "actual_conversion": actual_conversion,
            "from_inflow": min(natural_inflows, living_exp + health_cost),
            "brokerage_gains": brokerage_gains, "required_income": living_exp + total_taxes + health_cost,
            "from_brokerage": from_brokerage + draw_t_brokerage, "from_roth": from_roth + draw_t_roth, "from_401k": from_401k,
            "monthly_ledger": monthly_ledger, "label_suffix": " [SEPP]" if (husband_age >= 52 and husband_age < 60) else ""
        }
        timeline_data.append(year_row)
        
        if husband_age >= 90:
            break
            
    return timeline_data


def generate_all_balance_driven_combinations():
    """
    Generates all initial conversion path configurations via Cartesian product matching.
    Natively runs each permutation through the updated 44-year simulation engine
    and scores, ranks, and logs valid configurations to populate the scoreboard.
    """
    import itertools
    
    # 1. Pull dynamic bracket choices and runway horizon parameters from config
    bracket_options = getattr(config, "AVAILABLE_BRACKET_CHOICES", [12, 22, 24])
    target_horizon = getattr(config, "RUNWAY_HORIZON_YEARS", 5) 
    
    print(f"[INFO] Dynamically walking Cartesian product tree paths for a fixed {target_horizon}-Year Runway...")
    
    # Generate the comprehensive tactical permutation tree pool
    raw_permutations = list(itertools.product(bracket_options, repeat=target_horizon))
    results_pool = []
    
    total_paths = len(raw_permutations)
    print(f"[INFO] Total Cartesian optimization paths to evaluate: {total_paths}")
    
    # 2. Iterate through every tree branch path natively
    for idx, pattern in enumerate(raw_permutations):
        rotation_list = list(pattern)
        
        try:
            # Print live processing status for tracking execution heartbeat progress
            if idx % 10 == 0 or idx < 3:
                print(f" -> Processing tactical branch {idx + 1}/{total_paths}: {rotation_list}...")
                
            # Execute the core simulation natively using the updated function name
            simulation_timeline = run_financial_simulation(rotation_list)
            
            if simulation_timeline and len(simulation_timeline) > 0:
                # Extract your true ending legacy values from the final calculated row
                final_row = simulation_timeline[-1]
                
                final_brokerage = final_row.get("end_brokerage", 0.00)
                final_traditional = final_row.get("end_trad", 0.00)
                final_roth = final_row.get("end_roth", 0.00)
                final_estate_value = final_brokerage + final_traditional + final_roth
                
                # Calculate absolute lifetime tax drag friction across the entire 44 years
                lifetime_taxes_paid = sum(year_row.get("total_taxes", 0.00) for year_row in simulation_timeline)
                
                # Dynamic calculation tracking how many active conversion years took place
                years_to_convert = sum(1 for year_row in simulation_timeline if year_row.get("actual_conversion", 0.00) > 0.00)
                
                # Dynamic scoring matrix logic (Penalize high tax, reward terminal estate wealth)
                base_score = 100.00
                tax_penalty = (lifetime_taxes_paid / 100000.00) * 2.5
                wealth_premium = (final_estate_value / 1000000.00) * 1.5
                final_calculated_score = max(0.00, min(100.00, base_score - tax_penalty + wealth_premium))
                
                # Append the valid processed run metrics into your matrix scoreboard array pool
                results_pool.append({
                    "rotation": rotation_list,
                    "final_estate": final_estate_value,
                    "total_taxes": lifetime_taxes_paid,
                    "score": final_calculated_score,
                    "simulation_data": simulation_timeline,
                    "years_to_convert": years_to_convert
                })
                
        except Exception as err:
            # Silent fallback boundary safeguard to maintain loop continuation on anomaly
            continue

    # 3. Rank and sort the results array based on the highest final score
    results_pool = sorted(results_pool, key=lambda x: x["score"], reverse=True)
    
    # Safely isolate the best-performing tactical schedule sequence match
    top_recommended_schedule = results_pool[0]["rotation"] if results_pool else []
    
    return results_pool, top_recommended_schedule


def score_unrestricted_matrix(results_pool):
    """
    Ranks and scores survival trajectories using conformed weighted priority dimensions.
    Enforces a strict longevity constraint that heavily penalizes any strategy pattern 
    that depletes the Traditional 401(k) pre-tax core prior to Husband Age 59.5.
    """
    scoreboard = []
    if not results_pool:
        return scoreboard
    
    # 1. Establish the maximum baseline estate total across the entire pool safely
    max_estate = 0.0
    for r in results_pool:
        sim_data = r.get("simulation_data", [])
        if sim_data:
            final_row = sim_data[-1]
            estate_val = final_row.get("end_brokerage", 0.00) + final_row.get("end_trad", 0.00) + final_row.get("end_roth", 0.00)
            if estate_val > max_estate:
                max_estate = estate_val
    
    weights = getattr(config, "OPTIMIZATION_WEIGHTS", {"estate_value": 30.0, "liquidity_buffer": 20.0, "clock_safety": 20.0, "lifetime_tax_drag": 15.0, "tax_volatility": 15.0})
        
    for item in results_pool:
        rotation = item.get("rotation", [])
        sim_data = item.get("simulation_data", [])
        if not sim_data:
            continue
            
        final_row = sim_data[-1]

        ending_estate = final_row.get("end_brokerage", 0.00) + final_row.get("end_trad", 0.00) + final_row.get("end_roth", 0.00)
        total_taxes = sum(y.get("total_taxes", 0.00) for y in sim_data)
        
        is_brok_depleted = any(y.get("end_brokerage", 0.00) <= 0.00 and y.get("wife_age", 0) < 61 for y in sim_data)
        
        estate_score = (ending_estate / max_estate) * weights.get("estate_value", 30.0) if max_estate > 0 else 0.0
        liq_score = weights.get("liquidity_buffer", 20.0) if not is_brok_depleted else (weights.get("liquidity_buffer", 20.0) * 0.5)
        clock_score = weights.get("clock_safety", 20.0)
        tax_efficiency = max(0.0, weights.get("lifetime_tax_drag", 15.0) - (total_taxes / 50000.0))
        
        max_single_tax = max(y.get("total_taxes", 0.00) for y in sim_data)
        tax_ceiling = getattr(config, "MAX_ALLOWED_SINGLE_YEAR_TAX", 150000.00)
        volatility_score = 0.0 if max_single_tax > tax_ceiling else max(0.0, weights.get("tax_volatility", 15.0) * (1.0 - (max_single_tax / tax_ceiling)))
        
        switches = sum(1 for i in range(len(rotation)-1) if rotation[i] != rotation[i+1])
        friction = switches * 0.25
        
        # =========================================================================
        # SEPP LONGEVITY PENALTY LAYER: ENSURES PRE-TAX CORES LAST TO AGE 59.5
        # =========================================================================
        sepp_failed_early = False
        for y_row in sim_data:
            h_age = y_row.get("husband_age", 46)
            # If traditional pre-tax balance completely zero-out before age 59.5, trip lockout flag
            if h_age < 59.5 and y_row.get("end_trad", 0.00) <= 0.00:
                sepp_failed_early = True
                break

        # Calculate base structural score profile
        final_score = max(0.0, min(100.0, estate_score + liq_score + clock_score + tax_efficiency + volatility_score - friction))
        
        # Apply aggressive 40-point dynamic markdown penalty to force sub-optimal patterns down the rank matrix
        if sepp_failed_early:
            final_score = max(0.0, final_score - 40.0)
            
        empirical_betr = calculate_empirical_betr(ending_estate, rotation)
        
        scoreboard.append({
            "rotation": rotation, "years_to_convert": item.get("years_to_convert", 0),
            "lifetime_taxes_paid": total_taxes, "net_total_estate": ending_estate,
            "empirical_betr": empirical_betr, "liq_buffer": liq_score, "clock_safety": clock_score,
            "roth_split": estate_score, "legis_risk": tax_efficiency, "suitability_score": final_score,
            "simulation_data": sim_data
        })

    scoreboard.sort(key=lambda x: (x["suitability_score"], x["net_total_estate"]), reverse=True)
    
    # Render the formatted widescreen scoreboard summary console panel
    if scoreboard:
        print("\n" + "="*205)
        print(f"{'RANKED RETIREMENT MATRIX SCOREBOARD: COMPREHENSIVE STRATEGY VARIATIONS':^205}")
        print("="*205)
        print(f" {'Rank':<5} | {'Bracket Rotation Sequence Pattern':<46} | {'Clear':<5} | {'Est Taxes':<14} | {'End Estate':<16} | {'BETR Hurdle':<11} | {'Liq Buffer':<11} | {'IRS Clock':<10} | {'Roth Split':<10} | {'FINAL SCORE':<11}")
        print("-"*205)
        
        for r_idx, s_row in enumerate(scoreboard[:10]):
            seq = s_row["rotation"]
            print(f" {r_idx+1:<5} | {str(seq):<46} | {s_row['years_to_convert']:>2} Yrs | ${s_row['lifetime_taxes_paid']:<12,.2f} | ${s_row['net_total_estate']:<14,.2f} | {s_row['empirical_betr']:<10.2f}% | {s_row['liq_buffer']:<11.1f} | {s_row['clock_safety']:<10.1f} | {s_row['roth_split']:<10.1f} | {s_row['suitability_score']:<11.2f}")
        print("="*205 + "\n")
        
    return scoreboard

def print_complete_unrestricted_scoreboard(scoreboard_data):
    """Prints the comprehensive ranked hybrid multi-strategy benchmark leaderboard."""
    print("\n" + "="*190)
    print("             RANKED RETIREMENT MATRIX SCOREBOARD: COMPREHENSIVE STRATEGY VARIATIONS")
    print("="*190)
    print(f"{'Rank':<5} | {'Bracket Rotation Sequence Pattern':<55} | {'Clear':<7} | {'Est Taxes':<14} | {'End Estate':<15} | {'BETR Hurdle':<11} | {'Liq Buffer':<11} | {'IRS Clock':<10} | {'Roth Split':<11} | {'Legis Risk':<12} | {'FINAL SCORE':<12}")
    print("-"*190)
    
    for idx, r in enumerate(scoreboard_data[:30], start=1):
        seq_str = " -> ".join(f"{b}%" for b in r["rotation"])
        print(f"{idx:<5} | {seq_str:<55} | {r['years_to_convert']} Yrs | "
              f"${r['lifetime_taxes_paid']:<12,.2f} | ${r['net_total_estate']:<13,.2f} | "
              f"{r['empirical_betr']:.2f}% | {r['liq_buffer']:.1f} | {r['clock_safety']:.1f} | "
              f"{r['roth_split']:.1f} | {r['legis_risk']:.1f} | {r['suitability_score']:.1f} / 100")
    print("="*190)


def print_hybrid_ledger_overview(timeline_data, rotation_list):
    """Outputs the streamlined detailed transaction ledger matching user preferences."""
    # Symmetrical line divider matching the unified 14-character grid footprint
    print("\n" + "="*290)
    print(" YEAR-BY-YEAR DETAIL DRAWDOWN LEDGER (Timeline Projections to Age 90)")
    print("="*290)
    print(f"{'#':<3} | {'Yr':<4} | {'H_Age':<5} | {'Bracket':<7} | {'Brok Start':<14} | {'401k Start':<14} | {'Converted':<14} | {'Roth Start':<14} | {'Living Exp':<14} | {'Est Taxes':<14} | {'Health Cost':<14} | {'Inflow Base':<14} | {'Brok Yield':<14} | {'Req Income':<14} | {'From Broker':<14} | {'From Roth':<14} | {'From 401k':<14} | {'End Roth':<14}")
    print("-"*290)

    for idx, r in enumerate(timeline_data):
        yr_short = str(r["year"])[-2:]
        h_age = r.get("husband_age", 46 + idx)
        
        # Safely capture string indicators (e.g., [SEPP] or [RMD]) within the unified grid
        label_tag = r.get("label_suffix", "")
        f401k_display = f"${r['from_401k']:,.0f}{label_tag}"

        # FORCES EVERY PRIMARY FINANCIAL COLUMN TO A RIGID, SYSTEMATIC 14-CHARACTER WIDTH MASK
        print(f"{idx+1:<3} | {yr_short:<4} | {h_age:<5} | {r['active_bracket']:<7} | {sb:<14} | {st:<14} | {sc:<14} | {sr:<14} | {le:<14} | {ct:<14} | {hc:<14} | {inf:<14} | {bg:<14} | {ri:<14} | {fb:<14} | {fr:<14} | {f401k_display:<14} | {er:<14}")
        
    print("="*290)


def execute_strategy_scan_mode(scoreboard, custom_brokerage=None, custom_rent=None, custom_living=None):
    """
    Scans the scoreboard to extract and evaluate strategies that avoid premature 
    brokerage pool exhaustion before pension/social security inflows begin.
    """
    print("\n" + "="*90)
    print("                     STRATEGY SCANNER: PREMATURE EXHAUSTION MITIGATION")
    print("="*90)
    
    valid_paths = []
    for r in scoreboard:
        sim_data = r["simulation_data"]
        # Track if brokerage completely drops to zero before Phase 1 ends (Age 54 / Year 7)
        exhausted_early = False
        for idx, y in enumerate(sim_data[:7]):
            if y.get("end_brokerage", 0.00) <= 0.00:
                exhausted_early = True
                break
        if not exhausted_early:
            valid_paths.append(r)
            
    if not valid_paths:
        print("[WARNING] Zero strategic paths successfully clear the early-exhaustion threshold.")
        print("All analyzed configurations result in complete cash buffer depletion during Phase 1.")
        return

    display_limit = min(5, len(valid_paths))
    print(f"[SUCCESS] Found {len(valid_paths)} safe paths. Displaying Top {display_limit} optimized structures:\n")
    
    for rank_idx, path in enumerate(valid_paths[:display_limit], start=1):
        seq_str = " -> ".join(f"{b}%" for b in path["rotation_sequence"])
        print(f"Option {rank_idx}: Sequence Matrix [{seq_str}]")
        print(f"  - Final Combined Estate Portfolio Value: ${path['net_total_estate']:,.2f}")
        print(f"  - Cumulative Tax Liabilities:           ${path['lifetime_taxes_paid']:,.2f}")
        print(f"  - Calculated Multi-Year Suitability:     {path['suitability_score']:.2f} / 100\n")

       
if __name__ == "__main__":
    # 1. Walk dynamic hybrid combinations natively over your fixed horizon
    print("[INFO] Initializing dynamic hybrid Cartesian simulation trees over a 5-Year optimization window...")
    raw_pool, cached_sched = generate_all_balance_driven_combinations()
    
    # 2. Score, sort, and render the clean conformed top-10 overview grid
    completed_scoreboard = score_unrestricted_matrix(raw_pool)
        
    # 3. Clean Interactive Selection Prompt Loop
    while True:
        if not completed_scoreboard:
            break
        print("\n" + "-"*80)
        print("Commands: [Rank Number] = Inspect Ledger Details | 'q' = Quit")
        user_input = input("Select an option to inspect: ").strip()
            
        if user_input.lower() == 'q':
            print("[INFO] Exiting strategy optimization workspace.")
            break
        else: 
            try:
                target_rank = int(user_input)
                if 1 <= target_rank <= len(completed_scoreboard):
                    selected_record = completed_scoreboard[target_rank - 1]
                    rotation_list = selected_record["rotation"]
                    full_timeline_data = selected_record["simulation_data"]
                    
                    # Accumulate matrix summary grand totals
                    grand_totals = {
                        "taxes": 0.0, "health": 0.0, "base_inflow": 0.0, "taxable_income": 0.0,
                        "brokerage": 0.0, "roth": 0.0, "401k": 0.0, "conversions": 0.0,
                        "living_exp": 0.0, "required_income": 0.0, "brok_gains": 0.0
                    }
                    
                    for y_idx, y_row in enumerate(full_timeline_data):
                        y_from_brokerage = y_row.get("from_brokerage", 0.00)
                        y_from_roth = y_row.get("from_roth", 0.00)
                        y_from_401k_draw = y_row.get("from_401k", 0.00)
                        actual_annual_conversion = y_row.get("actual_conversion", 0.00)
                        
                        grand_totals["taxes"] += y_row.get("total_taxes", 0.00)
                        grand_totals["health"] += y_row.get("healthcare_cost", 0.00)
                        grand_totals["base_inflow"] += y_row.get("pension_ss_rent", 0.00)
                        grand_totals["brokerage"] += y_from_brokerage
                        grand_totals["roth"] += y_from_roth
                        grand_totals["401k"] += y_from_401k_draw
                        grand_totals["conversions"] += actual_annual_conversion
                        grand_totals["living_exp"] += y_row.get("living_expense", 0.00)
                        grand_totals["required_income"] += y_row.get("required_income", 0.00)
                        grand_totals["brok_gains"] += y_row.get("brokerage_gains", 0.00)

                    # Display the Interactive Sub-Menu Matrix Style Picker
                    print("\n[1] View Full Chronological Transaction Ledger")
                    print("[2] View Side-by-Side Brokerage vs. Roth Annual Balance Matrix")
                    view_choice = input("Select viewing matrix detail style (1 or 2): ").strip()
                    
                    if view_choice == "2":
                        print_dual_pool_ledger(selected_record, rotation_list)
                    else:
                        print("\n" + "="*255)
                        print(f" YEAR-BY-YEAR DETAIL DRAWDOWN LEDGER FOR RANK {target_rank} Pattern: {rotation_list} (Projections to Age 90)")
                        print("="*255)
                        print(f" {'#':<3} | {'Yr':<4} | {'Age (W/H)':<10} | {'Bracket':<7} | {'Brok Start':<14} | {'401k Start':<14} | {'Converted':<14} | {'Roth Start':<14} | {'Living Exp':<14} | {'Est Taxes':<12} | {'Health Cost':<12} | {'Inflow Base':<13} | {'Brok Yield':<12} | {'Req Income':<14} | {'From Broker':<13} | {'From Roth':<13} | {'From 401k':<14} | {'End Roth':<14}")
                        print("-"*255)
                        
                        for y_idx, y_row in enumerate(full_timeline_data):
                            yr_str = str(y_row.get("year"))[-2:]
                            age_str = f"{y_row.get('wife_age')}/{y_row.get('husband_age')}"
                            
                            y_from_401k = y_row.get("from_401k", 0.00)
                            h_age = y_row.get("husband_age", 46)
                            
                            # Safely flag active distribution rules concurrently
                            if h_age >= 75 and y_from_401k > 0.01:
                                suffix = " [RMD]"
                            elif (h_age >= 52 and h_age < 60) and y_from_401k > 0.01:
                                suffix = " [SEPP]"
                            else:
                                suffix = ""
                                
                            sb = f"${y_row.get('start_brokerage', 0.00):<13,.2f}"
                            st = f"${y_row.get('start_trad', 0.00):<13,.2f}"
                            sc = f"${y_row.get('actual_conversion', 0.00):<13,.2f}"
                            sr = f"${y_row.get('start_roth', 0.00):<13,.2f}"
                            le = f"${y_row.get('living_expense', 0.00):<13,.2f}"
                            ct = f"${y_row.get('total_taxes', 0.00):<11,.2f}"
                            hc = f"${y_row.get('healthcare_cost', 0.00):<11,.2f}"
                            inf = f"${y_row.get('pension_ss_rent', 0.00):<12,.2f}"
                            bg = f"${y_row.get('brokerage_gains', 0.00):<11,.2f}"
                            ri = f"${y_row.get('required_income', 0.00):<13,.2f}"
                            fb = f"${y_row.get('from_brokerage', 0.00):<12,.2f}"
                            fr = f"${y_row.get('from_roth', 0.00):<12,.2f}"
                            f4 = f"${y_from_401k:,.2f}{suffix}"
                            er = f"${y_row.get('end_roth', 0.00):<13,.2f}"
                            
                            print(f" {y_idx+1:<3} | {yr_str:<4} | {age_str:<10} | {y_row.get('active_bracket'):<7} | {sb} | {st} | {sc} | {sr} | {le} | {ct} | {hc} | {inf} | {bg} | {ri} | {fb} | {fr} | {f4:<14} | {er}")
                                  
                        print("-"*255)
                        print(f" {'TOTAL':<3} | {'-':<4} | {'-':<10} | {'-':<7} | {'-':<14} | {'-':<14} | ${grand_totals['conversions']:<13,.2f} | {'-':<14} | ${grand_totals['living_exp']:<13,.2f} | ${grand_totals['taxes']:<11,.2f} | ${grand_totals['health']:<11,.2f} | ${grand_totals['base_inflow']:<12,.2f} | ${grand_totals['brok_gains']:<11,.2f} | ${grand_totals['required_income']:<13,.2f} | ${grand_totals['brokerage']:<12,.2f} | ${grand_totals['roth']:<12,.2f} | ${grand_totals['401k']:<13,.2f} | {'-':<14}")
                        print("="*255)

                    # 4. Dossier compilation export check
                    export_input = input(f"\nWould you like to generate full custom Excel/PDF dossiers for Rank {target_rank}? (y/n): ").strip().lower()
                    if export_input == 'y':
                        try:
                            import report_generator
                            report_generator.generate_custom_dossiers(
                                target_rank,
                                selected_record,
                                full_timeline_data,
                                rotation_list,
                                grand_totals["taxes"],
                                grand_totals["health"],
                                grand_totals["base_inflow"],
                                grand_totals["conversions"],
                                grand_totals["brokerage"],
                                grand_totals["roth"],
                                grand_totals["401k"]
                            )
                            print(f"[SUCCESS] High-fidelity reporting packages secured for Rank {target_rank}.")
                        except Exception as e:
                            print(f"[ERROR] Dossier generator failed to run to completion natively: {e}")
                else:
                    print(f"[ERROR] Invalid choice. Enter a rank number between 1 and {len(completed_scoreboard)}.")
            except ValueError:
                print("[ERROR] Invalid command. Please type an integer rank or 'q' to quit.")

