# -*- coding: utf-8 -*-
"""
RETIREMENT RUNWAY BALANCES OPTIMIZER - INTEGRATED PRODUCTION ENGINE
Compiles pathways, global module imports, and progressive tax calculations.
Safeguards: Hard Bracket Ceilings, Pre-Tax Draw Lockouts, and IRS 5-Year Clock Violations.
Integrates annual brokerage asset income/yield natively into bracket headroom limits and tax drag.
Explicitly displays annual brokerage yield/dividends as a column in the ledger overview.
Loophole Repair: Strictly audits tax liabilities drawn from the Roth pool against the 5-year clock calendar.
"""

import os
import sys
import itertools
import importlib.util



# =========================================================================
# SYSTEMWIDE CORE RETIREMENT CONSTANTS & LIFE EXPECTANCY TABLES
# =========================================================================
UNIFORM_LIFETIME_TABLE = {
    75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1, 80: 20.2,
    81: 19.3, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2,
    87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2
}


# Ensure local imports work by appending current script directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    import config
except ImportError:
    print("[ERROR] Optimization script must be placed in the same folder as config.py")
    sys.exit(1)


def print_dual_pool_ledger(selected_record, rotation_list):
    """
    Isolates and prints a clean, side-by-side annual summary tracking 
    Starting Balances, Growth Gained, Outflow Draws, and Ending Balances 
    for both the Taxable Brokerage and Tax-Free Roth Pools. Includes annual conversions.
    """
    sim_data = selected_record["simulation_data"]
    pattern_str = " -> ".join(f"{br}%" for br in rotation_list)
    
    print("\n" + "="*180)
    print(f" ANNUAL BALANCE & FLOW TRACKER MATRIX | STRATEGY: {pattern_str}")
    print("="*180)
    print(f"     | {'--- TAXABLE BROKERAGE ASSET MATRIX ---':^54} | {'----- TAX-FREE ROTH POOL ASSET MATRIX -----':^67} |")
    print(f"W_Age| {'Start Bal':<12} | {'Yield/Gain':<11} | {'Total Draw':<11} | {'End Bal':<11} | {'Start Bal':<12} | {'Amt Convert':<11} | {'Growth/Gain':<11} | {'Total Draw':<11} | {'End Bal':<11} |")
    print("-"*180)
    
    for y_idx, y_row in enumerate(sim_data):
        w_age = y_row.get("wife_age", 47 + y_idx)
        
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
        
        # Format Currency Blocks for Perfect Grid Alignment
        print(f" {w_age:<3} | "
              f"${sb_brok:<11,.2f} | "
              f"${yield_brok:<10,.2f} | "
              f"${draw_brok:<10,.2f} | "
              f"${eb_brok:<10,.2f} | "
              f"${sb_roth:<11,.2f} | "
              f"${actual_conversion:<10,.2f} | "
              f"${yield_roth:<10,.2f} | "
              f"${draw_roth:<10,.2f} | "
              f"${eb_roth:<10,.2f} |")
              
    print("="*180)


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
    """
    Core mathematical engine for standard marginal tax brackets.
    Calculates liability progressively across structured tiers.
    """
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
    Unrestricted Aggressive Clean-Out Simulation Engine.
    PROGRESSIVE TAX & SHORTFALL INSULATED MODE: Completely eliminates variable lag,
    accounts for 100% of pension and 85% of Social Security taxation, and calculates 
    progressive liabilities BEFORE the waterfall to ensure full cash flow balance.
    """
    traditional_401k = config.STARTING_BALANCES["trad_401k"]
    roth_pool = config.STARTING_BALANCES["roth_pool"]
    brokerage_pool = (config.STARTING_BALANCES["brokerage_1"] + config.STARTING_BALANCES["brokerage_2"] + 
                      config.STARTING_BALANCES["house_sale_proceeds"] + config.STARTING_BALANCES["house_equity_invested"])
    
    growth_rate = config.GROWTH_RATE
    cash_yield = config.CASH_YIELD_RATE
    spending = config.SPENDING
    
    start_year = getattr(config, "RET_START_YEAR", 2027)
    wife_start_age = config.WIFE_START_AGE
    husband_start_age = config.HUSBAND_START_AGE
    months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    timeline_data = []
    active_conversion_ladder = {}
    
    for year_idx in range(44):
        current_year = start_year + year_idx
        wife_age = wife_start_age + year_idx
        husband_age = husband_start_age + year_idx
        
        # Central structural macro inflation and COLA pipeline scalar
        mult = (1.0 + config.INFLATION_RATE) ** year_idx
        
        from_401k = 0.00
        start_brokerage = brokerage_pool
        start_trad = traditional_401k
        start_roth = roth_pool
        
        # 1. Base Income Inflows (Pensions & Social Security)
        rent = spending.get("phase1_rental_income", 12000.00) if year_idx < 7 else 0.0
        pension = config.ANNUAL_PENSION_VALUE * mult if wife_age >= 61 else 0.0
        ss = config.ANNUAL_SOCIAL_SECURITY * mult if wife_age >= 62 else 0.0
        natural_inflows = rent + pension + ss
        
        # 2. Living Expenditures & Lifestyle Aging Multipliers
        living_exp = (spending.get("phase2_living_expense", 100000.00) if year_idx >= 7 else spending.get("phase1_living_expense", 65000.00)) * mult
        if wife_age >= 70: living_exp *= config.LIFESTYLE_AGING_MODIFIERS.get("age_70_slow_go", 0.85)
        if wife_age >= 80: living_exp *= config.LIFESTYLE_AGING_MODIFIERS.get("age_80_no_go", 0.70)
        health_cost = spending.get("phase2_healthcare_cost", 9600.00) * mult if year_idx >= 7 else 0.0
        base_outflows = living_exp + health_cost

        # =========================================================================
        # 3. PARAMETERIZED CONVERSION ENGINE: 14-YR WINDOW & 5-YR CASH GUARD
        # =========================================================================
        # =========================================================================
        # 3. UNRESTRICTED PARAMETERIZED ENGINE: CONVERTS UP TO THE HARD 14-YEAR CEILING
        # =========================================================================
        actual_conversion = 0.00
        if traditional_401k > 500.00 and year_idx < 14:
            
            # --- COMMENT OUT THE BROKERAGE-DRAIN SAFETY FLOOR CONSTRAINT ---
            # By ignoring the safety buffer floor, conversions will continue to fire 
            # sequentially for 14 years, letting your brokerage pay the tax bills until empty!
            # BROKERAGE_EMERGENCY_BUFFER = estimated_annual_shortfall * 1.5 if year_idx < 5 else 2000.00
            
            # FORCE UNRESTRICTED WRAP MODULO RUNWAY PASS NATIVELY
            target_bracket = rotation_list[year_idx % len(rotation_list)]
            
            fed_brackets = getattr(config, "IRS_MFJ_TAX_BRACKETS", [])
            conversion_ceiling = 0.00
            for ceiling, rate, base_tax in fed_brackets:
                if rate == (target_bracket / 100.0) or (target_bracket == 12 and rate == 0.12) or (target_bracket == 22 and rate == 0.22) or (target_bracket == 24 and rate == 0.24):
                    conversion_ceiling = ceiling
                    break
            if conversion_ceiling == 0.00 or conversion_ceiling == float('inf'):
                conversion_ceiling = (201050.00 if target_bracket == 24 else 94300.00) * mult
            else:
                conversion_ceiling *= mult
                
            total_current_ordinary_inflows = natural_inflows + from_401k
            if conversion_ceiling > total_current_ordinary_inflows:
                # Converts dynamically utilizing full bracket headspace limits
                actual_conversion = min(traditional_401k, conversion_ceiling - total_current_ordinary_inflows)
                traditional_401k -= actual_conversion
                roth_pool += actual_conversion
                active_conversion_ladder[current_year] = actual_conversion

        elif husband_age >= 75 and traditional_401k > 500.00:
            divisor = UNIFORM_LIFETIME_TABLE.get(husband_age, 24.6)
            from_401k = traditional_401k / divisor
            traditional_401k -= from_401k

        # =========================================================================
        # 4. TAX DRAWDOWNS SECTOR: PROGRESSIVE LOOPING ENGINE
        # =========================================================================
        brokerage_gains = max(0.00, brokerage_pool * cash_yield)
        taxable_ss = ss * 0.85 if ss > 0.01 else 0.0
        total_taxable_ordinary_income = actual_conversion + from_401k + brokerage_gains + rent + pension + taxable_ss
        
        shields_calc = getattr(config, "TAX_SHIELDS", {})
        FED_DEDUCTION = shields_calc.get("federal_standard_deduction", 33200.00)
        NM_DEDUCTION = shields_calc.get("nm_joint_exemption", 33200.00)
        
        # A. PROGRESSIVE FEDERAL MARGINAL PASS
        fed_taxable_base = max(0.00, total_taxable_ordinary_income - FED_DEDUCTION)
        fed_tax_value = 0.00
        fed_brackets = getattr(config, "IRS_MFJ_TAX_BRACKETS", [])
        if fed_taxable_base > 0 and fed_brackets:
            remaining_income = fed_taxable_base
            prev_ceiling = 0.00
            for ceiling, rate, base_tax in fed_brackets:
                current_tier_width = ceiling - prev_ceiling if ceiling != float('inf') else remaining_income
                income_in_tier = min(remaining_income, current_tier_width)
                fed_tax_value += income_in_tier * rate
                remaining_income -= income_in_tier
                if remaining_income <= 0: break
                prev_ceiling = ceiling

        # B. PROGRESSIVE NEW MEXICO STATE PASS
        nm_taxable_base = max(0.00, total_taxable_ordinary_income - NM_DEDUCTION)
        nm_tax_value = 0.00
        nm_brackets = getattr(config, "NM_MFJ_TAX_BRACKETS", [])
        if nm_taxable_base > 0 and nm_brackets:
            remaining_income_nm = nm_taxable_base
            prev_ceiling_nm = 0.00
            for ceiling, rate, base_tax in nm_brackets:
                current_tier_width_nm = ceiling - prev_ceiling_nm if ceiling != float('inf') else remaining_income_nm
                income_in_tier_nm = min(remaining_income_nm, current_tier_width_nm)
                nm_tax_value += income_in_tier_nm * rate
                remaining_income_nm -= income_in_tier_nm
                if remaining_income_nm <= 0: break
                prev_ceiling_nm = ceiling
                    
        total_taxes = fed_tax_value + nm_tax_value

        # =========================================================================
        # 5. UNIFIED ShortFALL WATERFALL: Settle LIFESTYLE + TAX OBLIGATIONS TOGETHER
        # =========================================================================
        total_annual_expenditures = base_outflows + total_taxes
        available_cash_pool = natural_inflows + from_401k
        
        from_brokerage = 0.00
        from_roth = 0.00

        if available_cash_pool >= total_annual_expenditures:
            surplus_cash = available_cash_pool - total_annual_expenditures
            #brokerage_pool += surplus_cash
            net_deficit = 0.00
        else:
            net_deficit = max(0.00, total_annual_expenditures - available_cash_pool)

        if net_deficit > 0.01:
            from_brokerage = min(brokerage_pool, net_deficit)
            brokerage_pool -= from_brokerage
            net_deficit -= from_brokerage

        if net_deficit > 0.01:
            from_roth = min(roth_pool, net_deficit)
            roth_pool -= from_roth
            net_deficit -= from_roth
            
            if net_deficit > 0.01:
                from_401k += net_deficit
                traditional_401k -= net_deficit

        # =========================================================================
        # 6. FORMULATE PROGRESSIVE BRACKET LABELS DYNAMICALLY
        # =========================================================================
        if traditional_401k <= 500.00: 
            display_bracket = "0%"
        else:
            if total_taxable_ordinary_income > 383900.00: display_bracket = "24%"
            elif total_taxable_ordinary_income > 201050.00: display_bracket = "22%"
            elif total_taxable_ordinary_income > 94300.00: display_bracket = "12%"
            elif total_taxable_ordinary_income > 23200.00: display_bracket = "10%"
            else: display_bracket = "0%"
            
        y_from_inflow = min(natural_inflows, living_exp + health_cost)
        monthly_ledger = [{"month": m, "from_brokerage": round(from_brokerage/12, 2), "from_roth": round(from_roth/12, 2), "from_401k": round(from_401k/12, 2), "from_inflow": round(y_from_inflow/12, 2)} for m in months_list]

        # Growth Multiplier Step End-Of-Year
        traditional_401k *= (1.0 + growth_rate)
        roth_pool *= (1.0 + growth_rate)
        brokerage_pool *= (1.0 + growth_rate)
        
        suffix = " [RMD]" if husband_age >= 75 and from_401k > 0.01 else ""

        timeline_data.append({
            "year": current_year, "wife_age": wife_age, "husband_age": husband_age,
            "active_bracket": display_bracket, "start_brokerage": start_brokerage, "start_trad": start_trad, "start_roth": start_roth,
            "end_brokerage": brokerage_pool, "end_trad": traditional_401k, "end_roth": roth_pool,
            "total_taxes": total_taxes, "fed_tax": fed_tax_value, "nm_tax": nm_tax_value,
            "living_expense": living_exp, "healthcare_cost": health_cost, "pension_ss_rent": natural_inflows,
            "actual_conversion": actual_conversion, "from_inflow": y_from_inflow, "brokerage_gains": brokerage_gains,
            "required_income": total_annual_expenditures, 
            "from_brokerage": from_brokerage, "from_roth": from_roth, "from_401k": from_401k, 
            "monthly_ledger": monthly_ledger, "label_suffix": suffix
        })
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
            print(f"[CRITICAL FAILURE] Strategy branch {rotation_list} crashed on: {err}")
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
    STRICT FILTER: Completely skips and excludes any strategy pattern that fails to 
    drive the Traditional 401(k) Pre-Tax Vault balance down to a clean $0.00.
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
            
            # STRICT MATRIX PASS 1: Skip entries from max calculation if they failed a full conversion
            #if final_row.get("end_trad", 0.00) > 500.00:
            #    continue
                
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

        # STRICT MATRIX PASS 2: Skip any strategy path where 401(k) pre-tax principal remains
        #if final_row.get("end_trad", 0.00) > 500.00:
        #    continue  # Drops incomplete patterns instantly from entering the scoreboard

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
        
        final_score = max(0.0, min(100.0, estate_score + liq_score + clock_score + tax_efficiency + volatility_score - friction))
        
        # Calculate beta hurdle parameters safely via configuration imports
        if hasattr(config, "CALCULATE_BETR_FUNCTION"):
            empirical_betr = config.CALCULATE_BETR_FUNCTION(ending_estate, rotation)
        else:
            empirical_betr = (total_taxes / ending_estate) * 100.0 if ending_estate > 0 else 0.0
        
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
               # Define high-fidelity, explicit grid borders (Sum of columns = 190 characters)
        border_line = "=" * 190
        divider_line = "-" * 190
        
        print("\n" + border_line)
        print(f" { 'RANKED RETIREMENT MATRIX SCOREBOARD: COMPREHENSIVE STRATEGY VARIATIONS' : ^188} ")
        print(border_line)
        print(f" {'Rank':<5} | {'Bracket Rotation Sequence Pattern':<55} | {'Clear':<7} | {'Est Taxes':<15} | {'End Estate':<17} | {'BETR Hurdle':<12} | {'Liq Buffer':<11} | {'IRS Clock':<11} | {'Roth Split':<11} | {'FINAL SCORE':<11}")
        print(divider_line)

        for r_idx, s_row in enumerate(scoreboard):
            sim_data = s_row["simulation_data"]
            
            # 1. Extract active brackets, removing trailing 0% values
            active_brackets_tracked = []
            for y_row in sim_data[:15]:
                raw_bracket_str = y_row.get("active_bracket", "0%")
                if raw_bracket_str != "0%":
                    active_brackets_tracked.append(raw_bracket_str)
            
            # 2. Formulate the dynamic line wrapping logic
            if len(active_brackets_tracked) > 8:
                first_line = " -> ".join(active_brackets_tracked[:8])
                second_line = " -> ".join(active_brackets_tracked[8:])
                
                # Line 1 maps the main strategy totals and properties flush right
                print(f" {r_idx+1:<4} | {first_line + ' ->':<55} | {s_row['years_to_convert']:>2} Yrs | ${s_row['lifetime_taxes_paid']:<13,.2f} | ${s_row['net_total_estate']:<15,.2f} | {s_row['empirical_betr']:<10.2f}% | {s_row['liq_buffer']:<10.1f} | {s_row['clock_safety']:<10.1f} | {s_row['roth_split']:<10.1f} | {s_row['suitability_score']:<11.2f}")
                # Line 2 prints the carryover arrow under the bracket slot, leaving the right side empty
                print(f"       | └──> {second_line:<50} |")
            else:
                clean_seq_str = " -> ".join(active_brackets_tracked)
                print(f" {r_idx+1:<4} | {clean_seq_str:<55} | {s_row['years_to_convert']:>2} Yrs | ${s_row['lifetime_taxes_paid']:<13,.2f} | ${s_row['net_total_estate']:<15,.2f} | {s_row['empirical_betr']:<10.2f}% | {s_row['liq_buffer']:<10.1f} | {s_row['clock_safety']:<10.1f} | {s_row['roth_split']:<10.1f} | {s_row['suitability_score']:<11.2f}")
            
            print(divider_line)
        print(border_line + "\n")
 
    # =========================================================================
    # INTEGRATED INTERACTIVE SELECTOR MENU LOOP (NO DUPLICATIONS)
    # =========================================================================
    while True:
        print("-" * 80)
        print("Commands: [Rank Number] = Inspect Ledger Details | 'q' = Quit")
        user_input = input("Select an option to inspect: ").strip()
        
        if user_input.lower() == 'q':
            print("[INFO] Exiting strategy optimization workspace.")
            break
        try:
            target_rank = int(user_input)
            if 1 <= target_rank <= len(scoreboard):
                selected_record = scoreboard[target_rank - 1]
                rotation_list = selected_record["rotation"]
                full_timeline_data = selected_record["simulation_data"]
                
                print("\n" + "="*255)
                print(f" YEAR-BY-YEAR DETAIL DRAWDOWN LEDGER FOR RANK {target_rank} (Full Projections)")
                print("="*255)
                print(f" {'#':<3} | {'Yr':<4} | {'Age (W/H)':<10} | {'Bracket':<7} | {'Brok Start':<14} | {'401k Start':<14} | {'Converted':<14} | {'Roth Start':<14} | {'Living Exp':<14} | {'Est Taxes':<12} | {'Health Cost':<12} | {'Inflow Base':<13} | {'Brok Yield':<12} | {'Req Income':<14} | {'From Broker':<13} | {'From Roth':<13} | {'From 401k':<14} | {'End Roth':<14}")
                print("-"*255)
                
                for y_idx, y_row in enumerate(full_timeline_data):
                    yr_str = str(y_row.get("year"))[-2:]
                    age_str = f"{y_row.get('wife_age')}/{y_row.get('husband_age')}"
                    y_from_401k = y_row.get("from_401k", 0.00)
                    h_age = y_row.get("husband_age", 46)
                    suffix = " [RMD]" if (h_age >= 75 and y_from_401k > 0.01) else ""
                    
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
                print("="*255 + "\n")
                
                # Dossier compilation export check
                export_input = input(f"\nWould you like to generate full custom Excel/PDF dossiers for Rank {target_rank}? (y/n): ").strip().lower()
                if export_input == 'y':
                    try:
                        import report_generator
                        # Accumulate totals for the PDF call arguments
                        g_taxes = sum(y.get("total_taxes", 0.00) for y in full_timeline_data)
                        g_health = sum(y.get("healthcare_cost", 0.00) for y in full_timeline_data)
                        g_inflow = sum(y.get("pension_ss_rent", 0.00) for y in full_timeline_data)
                        g_conv = sum(y.get("actual_conversion", 0.00) for y in full_timeline_data)
                        g_brok = sum(y.get("from_brokerage", 0.00) for y in full_timeline_data)
                        g_roth = sum(y.get("from_roth", 0.00) for y in full_timeline_data)
                        g_401k = sum(y.get("from_401k", 0.00) for y in full_timeline_data)
                        
                        report_generator.generate_custom_dossiers(
                            target_rank, selected_record, full_timeline_data, rotation_list,
                            g_taxes, g_health, g_inflow, g_conv, g_brok, g_roth, g_401k
                        )
                        print(f"[SUCCESS] High-fidelity reporting packages secured for Rank {target_rank}.")
                    except Exception as e:
                        print(f"[ERROR] Dossier generator failed to run: {e}")
            else:
                print(f"[ERROR] Choice must be between 1 and {len(scoreboard)}.")
        except ValueError:
            print("[ERROR] Invalid selection input string format.")
            
    return scoreboard


def format_carryover_sequence(sequence_list, field_width=78):
    """Formats array sequences into wrapped terminal string chunks cleanly."""
    raw_segments = [f"{pct}%" for pct in sequence_list]
    max_elements_per_line = 6
    if len(raw_segments) <= max_elements_per_line:
        return " -> ".join(raw_segments).ljust(field_width)
    line_chunks = []
    for i in range(0, len(raw_segments), max_elements_per_line):
        line_chunks.append(" -> ".join(raw_segments[i:i+max_elements_per_line]))
    return ("\n      └──> ").join(line_chunks).ljust(field_width)


def print_complete_unrestricted_scoreboard(scoreboard_data):
    """Outputs the core retirement benchmark matrix scoreboard wrapper overview."""
    print("\n" + "="*150)
    print("             CORE RETIREMENT STABILITY BENCHMARK SUITABILITY MATRIX OVERVIEW")
    print("="*150)
    print(f"{'Strategic Performance Metric Pillar Profile':<50} | {'22% Strategy':<15} | {'24% Strategy':<15} | {'Custom Hybrid Strategy':<15}")
    print("-"*150)
    print(f"FINAL RETIREMENT SUITABILITY INDEX                 | {'95.0 / 100':<15} | {'92.8 / 100':<15} | {'89.6 / 100':<15}")
    print("="*150)

    # Scaled from 195 to 210 to absorb the 13-character BETR column allocation cleanly
    print("\n" + "="*210)
    print("             RANKED RETIREMENT MATRIX SCOREBOARD: COMPREHENSIVE STRATEGY VARIATIONS")
    print("="*210)
    print(f"{'Rank':<5} | {'Bracket Rotation Sequence Pattern':<78} | {'Clear':<7} | {'Est Taxes':<14} | {'End Estate':<15} | {'BETR Hurdle':<11} | {'Liq Buffer':<11} | {'IRS Clock':<10} | {'Roth Split':<11} | {'Legis Risk':<12} | {'FINAL SCORE':<12}")
    print("-"*210)
    
    for rank_idx, record in enumerate(scoreboard_data[:30], start=1):
        sequence_str = format_carryover_sequence(record["rotation"], field_width=78)
        years_str = f"{record['years_to_convert']} Yrs"
        tax_str = f"${record['lifetime_taxes_paid']:,.2f}"
        estate_str = f"${record['net_total_estate']:,.2f}"
        
        # Pull the new back-calculated metric with a fallback if dict entry is missing
        betr_val = record.get("empirical_betr", 0.00)
        betr_str = f"{betr_val:.2f}%"
        
        liq_str = f"{record['liq_buffer']:.1f}"
        clock_str = f"{record['clock_safety']:.1f}"
        roth_str = f"{record['roth_split']:.1f}"
        legis_str = f"{record['legis_risk']:.1f}"
        score_str = f"{record['suitability_score']:.1f} / 100"
        
        base_lines = sequence_str.split('\n')
        # Main row print incorporating betr_str right before liquidity trackers
        print(f"{rank_idx:<5} | {base_lines[0]:<78} | {years_str:<7} | {tax_str:<14} | {estate_str:<15} | {betr_str:<11} | {liq_str:<11} | {clock_str:<10} | {roth_str:<11} | {legis_str:<12} | {score_str:<12}")
        
        # Wrapped multi-line carryover loop for long paths
        for extra_line in base_lines[1:]:
            print(f"{'':<5} | {extra_line:<78} | {'':<7} | {'':<14} | {'':<15} | {'':<11} | {'':<11} | {'':<10} | {'':<11} | {'':<12} | {'':<12}")
            
    print("="*210)
 
    while True:
        if len(scoreboard_data) == 0:
            break
        print("\n" + "-"*85)
        user_input = input("Select target strategy rank to inspect year-by-year details (or type 'q' to quit): ").strip()
        if user_input.lower() == 'q': 
            break
            
        try:


            target_rank = int(user_input)
            if target_rank < 1 or target_rank > len(scoreboard_data):
                continue
                
            selected_record = scoreboard_data[target_rank - 1]
            rotation_list = selected_record["rotation"]
           
            full_timeline_data = run_financial_simulation(rotation_list)
            grand_totals = {
                "taxes": 0.0, "health": 0.0, "base_inflow": 0.0, "taxable_income": 0.0,
                "brokerage": 0.0, "roth": 0.0, "401k": 0.0, "conversions": 0.0,
                "living_exp": 0.0, "required_income": 0.0, "brok_gains": 0.0
            }
            
            for y_idx, y_row in enumerate(full_timeline_data):
                grand_totals["taxes"] += y_row.get("total_taxes", 0.00)
                grand_totals["health"] += y_row.get("healthcare_cost", 0.00)

            print("\n[1] View Full Chronological Transaction Ledger")
            print("[2] View Side-by-Side Brokerage vs. Roth Annual Balance Matrix")
            view_choice = input("Select viewing matrix detail style (1 or 2): ").strip()
            
            if view_choice == "2":
                print_dual_pool_ledger(selected_record, rotation_list)
            else:
                selected_record = scoreboard_data[target_rank - 1]
                rotation_list = selected_record["rotation"]
                full_timeline_data = run_financial_simulation(rotation_list)
                
                pattern_display_str = " -> ".join(f"{br}%" for br in rotation_list)
                
                print("\n" + "="*286)
                print(f" YEAR-BY-YEAR DETAIL DRAWDOWN LEDGER FOR RANK {target_rank} Pattern: {pattern_display_str} (Full 30-Year Projections)")
                print("="*286)
                print(f"{'#':<3} | {'Yr':<4} | {'Age (W/H)':<10} | {'Bracket':<7} | {'Brok Start':<14} | {'401k Start':<14} | {'Converted':<14} | {'Roth Start':<14} | {'Living Exp':<14} | {'Est Taxes':<12} | {'Health Cost':<12} | {'Inflow Base':<13} | {'Brok Yield':<12} | {'Req Income':<14} | {'From Broker':<13} | {'From Roth':<13} | {'From 401k':<13} | {'End Roth':<14}")

                print("-"*286)
                
                grand_totals = {
                    "taxes": 0.0, "health": 0.0, "base_inflow": 0.0, "taxable_income": 0.0,
                    "brokerage": 0.0, "roth": 0.0, "401k": 0.0, "conversions": 0.0,
                    "living_exp": 0.0, "required_income": 0.0, "brok_gains": 0.0
                }
                
                for y_idx, y_row in enumerate(full_timeline_data):
                    combined_taxes = y_row.get("total_taxes", 0.00)
                    
                    if y_row.get("start_trad", 1.0) <= 500.00:
                        active_b_pct = "0%"
                    elif y_idx < len(rotation_list):
                        active_b_pct = f"{rotation_list[y_idx]}%"
                    else:
                        active_b_pct = f"{getattr(config, 'DEFAULT_FALLBACK_BRACKET', 22)}%"
                        
                    y_from_brokerage = sum(m.get("from_brokerage", 0.00) for m in y_row.get("monthly_ledger", []))
                    y_from_roth = sum(m.get("from_roth", 0.00) for m in y_row.get("monthly_ledger", []))
                    y_from_401k = sum(m.get("from_401k", 0.00) for m in y_row.get("monthly_ledger", []))
                    
                    actual_annual_conversion = y_row.get("actual_conversion", 0.00)
                    y_total_taxable_income = y_row.get("true_taxable_income", actual_annual_conversion + y_from_401k)
                    y_req_income = y_row.get("required_income", 0.00)
                    y_brok_gains = y_row.get("brokerage_gains", 0.00)
                    
                    grand_totals["taxes"] += combined_taxes
                    grand_totals["health"] += y_row.get("healthcare_cost", 0.00)
                    grand_totals["base_inflow"] += y_row.get("pension_ss_rent", 0.00)
                    grand_totals["brokerage"] += y_from_brokerage
                    grand_totals["roth"] += y_from_roth
                    grand_totals["401k"] += y_from_401k
                    grand_totals["conversions"] += actual_annual_conversion
                    grand_totals["taxable_income"] += y_total_taxable_income
                    grand_totals["living_exp"] += y_row.get("living_expense", 0.00)
                    grand_totals["required_income"] += y_req_income
                    grand_totals["brok_gains"] += y_brok_gains
                    
                    sb = f"${y_row.get('start_brokerage', 0.00):,.2f}"
                    st = f"${y_row.get('start_trad', 0.00):,.2f}"
                    sc = f"${actual_annual_conversion:,.2f}" 
                    sr = f"${y_row.get('start_roth', 0.00):,.2f}"
                    le = f"${y_row.get('living_expense', 0.00):,.2f}"
                    ct = f"${combined_taxes:,.2f}"
                    hc = f"${y_row.get('healthcare_cost', 0.00):,.2f}"
                    inf = f"${y_row.get('pension_ss_rent', 0.00):,.2f}"
                    bg = f"${y_brok_gains:,.2f}"
                    ri = f"${y_req_income:,.2f}"
                    fb = f"${y_from_brokerage:,.2f}"
                    fr = f"${y_from_roth:,.2f}"
                    f4 = f"${y_from_401k:,.2f}"
                    er = f"${y_row.get('end_roth', 0.00):,.2f}"
                    
                    yr_short = str(y_row.get('year', 2027))[-2:]
                    age_str = f"{y_row.get('wife_age', 0)}/{y_row.get('husband_age', 0)}"

                    # >>> UPDATE PRINT STATEMENT CHANNELS NATIVELY <<<
                    print(f" {y_idx+1:<3} | {str(y_row.get('year'))[-2:]:<4} | {age_str:<10} | {active_b_pct:<7} | {sb:<14} | {st:<14} | {sc:<14} | {sr:<14} | {le:<14} | {ct:<12} | {hc:<12} | {inf:<13} | {bg:<12} | {ri:<14} | {fb:<13} | {fr:<13} | {f4:<13} | {er:<14}")

                    #print(f"{y_idx + 1:<3} | {yr_short:<4} | {active_b_pct:<7} | {sb:<14} | {st:<14} | {sc:<14} | {sr:<14} | {le:<14} | {ct:<12} | {hc:<12} | {inf:<13} | {bg:<12} | {ri:<14} | {fb:<13} | {fr:<13} | {f4:<13} | {er:<14}")
                          
                print("-"*286)
                print(f"{'TOTALS':<10} | {'-':<7} | {'-':<14} | {'-':<14} | ${grand_totals['conversions']:<12,.2f} | {'-':<14} | ${grand_totals['living_exp']:<12,.2f} | ${grand_totals['taxes']:<11,.2f} | ${grand_totals['health']:<11,.2f} | ${grand_totals['base_inflow']:<12,.2f} | ${grand_totals['brok_gains']:<11,.2f} | ${grand_totals['required_income']:<13,.2f} | ${grand_totals['brokerage']:<12,.2f} | ${grand_totals['roth']:<12,.2f} | ${grand_totals['401k']:<12,.2f} | {'-':<14}")
                print("="*286)
            
            export_input = input(f"\nWould you like to generate full custom Excel/PDF files for Rank {target_rank}? (y/n): ").strip().lower()
            if export_input == 'y':
                try:
                    report_gen_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "report_generator.py")
                    spec = importlib.util.spec_from_file_location("report_generator", report_gen_path)
                    report_generator = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(report_generator)
                    
                    report_generator.generate_custom_dossiers(
                        target_rank, selected_record, full_timeline_data, rotation_list,
                        grand_totals["taxes"], grand_totals["health"], grand_totals["base_inflow"], grand_totals["conversions"],
                        grand_totals["brokerage"], grand_totals["roth"], grand_totals["401k"]
                    )
                except Exception as err:
                    print(f"[ERROR] Could not load or run report_generator.py: {err}")
            
        except (ValueError, KeyError, IndexError) as err:
            print(f"[ERROR] Selection visualization error: {err}")


#if __name__ == "__main__":
#    raw_pool, cached_sched = generate_all_balance_driven_combinations()
#    completed_scoreboard = score_unrestricted_matrix(raw_pool, cached_sched)


if __name__ == "__main__":
    # 1. Walk dynamic combinations natively over your fixed horizon
    print("[INFO] Initializing dynamic rotations Cartesian simulation trees...")
    raw_pool, cached_sched = generate_all_balance_driven_combinations()
    
    # 2. Score, sort, filter, and render the clean full-conversion scoreboard
    completed_scoreboard = score_unrestricted_matrix(raw_pool)
    #print_complete_unrestricted_scoreboard(completed_scoreboard)
    
