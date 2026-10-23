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
    """Calculates the true empirical Break-Even Tax Rate (BETR) against a zero-conversion baseline."""
    zero_bracket_schedule = [0] * len(bracket_schedule)
    control_timeline = run_financial_simulation(
        zero_bracket_schedule, 
        custom_brokerage=custom_brokerage, 
        custom_rent=custom_rent, 
        custom_living=custom_living
    )
    if not control_timeline:
        return 0.00
        
    control_final = control_timeline[-1]
    control_net_estate = (
        control_final.get("end_brokerage", 0.00) +
        control_final.get("end_trad", 0.00) +
        control_final.get("end_roth", 0.00)
    )
    
    active_timeline = run_financial_simulation(
        bracket_schedule,
        custom_brokerage=custom_brokerage,
        custom_rent=custom_rent,
        custom_living=custom_living
    )
    total_converted = sum(y.get("actual_conversion", 0.00) for y in active_timeline)
    if total_converted <= 0 or strategy_net_estate <= control_net_estate:
        return 0.00
        
    strategy_lifetime_taxes = sum(y.get("total_taxes", 0.00) for y in active_timeline)
    control_lifetime_taxes = sum(y.get("total_taxes", 0.00) for y in control_timeline)
    tax_saved_delta = max(0.00, control_lifetime_taxes - strategy_lifetime_taxes)
    
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
    
    fed_deduction = shields.get("federal_standard_deduction", getattr(config, "IRS_MFJ_STANDARD_DEDUCTION", 32200.00))
    fed_tax = calc_marginal_tax(income, fed_deduction, fed_brackets)

    nm_brackets = getattr(config, "NM_MFJ_TAX_BRACKETS", [])
    nm_deduction = shields.get("nm_joint_exemption", getattr(config, "NM_MFJ_STANDARD_DEDUCTION", 32200.00))
    nm_tax = calc_marginal_tax(income, nm_deduction, nm_brackets)
    
    return fed_tax, nm_tax


def run_financial_simulation(bracket_schedule, custom_brokerage=None, custom_rent=None, custom_living=None):
    """Simulates a 30-year drawdown lifecycle timeline incorporating dynamic SEPP cash-flow triggers."""
    timeline_data = []
    
    starting_balances = getattr(config, "STARTING_BALANCES", {})
    traditional_401k = starting_balances.get("trad_401k", 0.00)
    roth_pool = starting_balances.get("roth_pool", 0.00)
    
    # Capture initial brokerage pool exactly once
    if custom_brokerage is not None:
        brokerage_pool = custom_brokerage
    else:
        brokerage_pool = (
            starting_balances.get("brokerage_1", 0.00) +
            starting_balances.get("brokerage_2", 0.00) +
            starting_balances.get("house_sale_proceeds", 0.00) +
            starting_balances.get("house_equity_invested", 0.00)
        )
        if brokerage_pool <= 0.01:
            brokerage_pool = getattr(config, "TOTAL_INITIAL_BROKERAGE", 436986.29)
        
    growth_rate = getattr(config, "GROWTH_RATE", 0.065)
    inflation_rate = getattr(config, "INFLATION_RATE", 0.03)
    cash_yield = getattr(config, "CASH_YIELD_RATE", 0.035)
    
    phase1_duration = getattr(config, "PHASE_1_DURATION_YEARS", 7)
    spending_matrix = getattr(config, "SPENDING", {})
    aging_modifiers = getattr(config, "LIFESTYLE_AGING_MODIFIERS", {})
    
    shields = getattr(config, "TAX_SHIELDS", {})
    fed_deduction = shields.get("federal_standard_deduction", getattr(config, "IRS_MFJ_STANDARD_DEDUCTION", 33200.00))
    sepp_rate_floor = getattr(config, "SEPP_INTEREST_RATE", 0.05)
    
    start_year = getattr(config, "START_YEAR", 2027)
    wife_start_age = getattr(config, "WIFE_START_AGE", 47)
    husband_start_age = getattr(config, "HUSBAND_START_AGE", 46)
    default_fallback = getattr(config, "DEFAULT_FALLBACK_BRACKET", 22)
    start_month = getattr(config, "RETIREMENT_START_MONTH", "Feb")

    sepp_active = False
    sepp_annual_amount = 0.00
    trigger_sepp_next_year = False
    sepp_years_served = 0
    sepp_label_tag = ""
    
    # Permanent tracking flag for empty brokerage cushion
    brokerage_was_exhausted = False
    months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for year_idx in range(60):
        current_year = start_year + year_idx
        wife_age = wife_start_age + year_idx
        husband_age = husband_start_age + year_idx
        
        # --- 1. IRS AGE 59.5 CIRCUIT BREAKER (ALIGNED TO HUSBAND AGE) ---
        if husband_age >= 59.5:
            # Only turn off if we have ALSO met the 5-year mandatory tracking timeline
            if sepp_years_served >= 5:
                sepp_active = False
                trigger_sepp_next_year = False
                sepp_annual_amount = 0.00
                sepp_label_tag = ""
            else:
                sepp_years_served += 1
                
        # --- 2. ACTIVE SEPP TIMEKEEPER ---
        elif sepp_active:
            # Keep counting years. Under 59.5, we NEVER turn it off early, 
            # even if sepp_years_served passes 5, because we haven't hit 59.5 yet!
            sepp_years_served += 1

        # --- 2. JUST-IN-TIME SEPP INITIALIZATION ---
        if trigger_sepp_next_year and not sepp_active and husband_age < 59.5:
            sepp_annual_amount = calculate_sepp_amortization(traditional_401k, husband_age, rate=sepp_rate_floor)
            sepp_active = True
            trigger_sepp_next_year = False
            sepp_years_served = 1
            sepp_label_tag = " [SEPP]"

        # Capture prior row starting points
        start_brokerage = brokerage_pool
        start_trad = traditional_401k
        start_roth = roth_pool

        # --- 3. PERMANENT LOCKOUT LOGIC INJECTION ---
        if start_brokerage <= 500.00 or brokerage_pool <= 500.00:
            brokerage_was_exhausted = True

        if brokerage_was_exhausted:
            active_bracket = 0  # Hard stop: never convert again
        elif traditional_401k <= 500.00 or sepp_active or trigger_sepp_next_year:
            active_bracket = 0
        elif year_idx < len(bracket_schedule):
            active_bracket = bracket_schedule[year_idx]
        else:
            active_bracket = default_fallback

        brokerage_gains = start_brokerage * cash_yield
        inflation_multiplier = (1.0 + inflation_rate) ** year_idx
        # --- 1. CASH INFLOW & LIFESTYLE OUTFLOW PROFILES ---
        natural_inflows = 0.00
        if year_idx < phase1_duration:
            natural_inflows += custom_rent if custom_rent is not None else spending_matrix.get("phase1_rental_income", 12000.00)
        if wife_age >= 61:
            natural_inflows += getattr(config, "ANNUAL_PENSION_VALUE", 35250.00) * inflation_multiplier
        if wife_age >= 62:
            natural_inflows += getattr(config, "ANNUAL_SOCIAL_SECURITY", 100000.00) * inflation_multiplier

        if year_idx < phase1_duration:
            living_exp = custom_living * inflation_multiplier if custom_living is not None else spending_matrix.get("phase1_living_expense", 65000.00) * inflation_multiplier
            health_cost = 0.00  
        else:
            living_exp = spending_matrix.get("phase2_living_expense", 100000.00) * inflation_multiplier
            if wife_age >= 80:
                living_exp *= aging_modifiers.get("age_80_no_go", 0.70)
            elif wife_age >= 70:
                living_exp *= aging_modifiers.get("age_70_slow_go", 0.85)
            health_cost = spending_matrix.get("phase2_healthcare_cost", 9600.00) * inflation_multiplier

        base_outflows = living_exp + health_cost

        # --- 2. PHASE 5: REQUIRED MINIMUM DISTRIBUTIONS (AGE 75+) ---
        rmd_distribution = 0.00
        rmd_label_tag = ""
        if husband_age >= 75:
            if traditional_401k > 500.00:
                rmd_factor = UNIFORM_LIFETIME_TABLE.get(int(husband_age), 24.6)
                rmd_distribution = traditional_401k / rmd_factor
                rmd_label_tag = " [RMD]"
            else:
                rmd_label_tag = " [RMD-$0]"

        # --- 3. POST-SEPP BRACKET-FILLING DRAWDOWN WATERFALL ---
        conversion_target = 0.00
        post_sepp_bracket_withdrawal = 0.00
        from_401k = 0.00
        label_suffix = ""
        
        if sepp_active:
            from_401k = min(traditional_401k, sepp_annual_amount)
            traditional_401k -= from_401k
            label_suffix = sepp_label_tag
        elif rmd_distribution > 0:
            from_401k = min(traditional_401k, rmd_distribution)
            traditional_401k -= from_401k
            label_suffix = rmd_label_tag
        elif brokerage_was_exhausted and husband_age >= 59.5 and traditional_401k > 500.00:
            existing_magi_base = natural_inflows + brokerage_gains
            
            if husband_age < 63.0:
                aca_magi_ceiling = getattr(config, "TAX_SHIELDS", {}).get("aca_magi_ceiling", 85000.00)
                target_ceiling = aca_magi_ceiling * inflation_multiplier
            else:
                base_irmaa_cliff = 218000.00
                target_ceiling = base_irmaa_cliff * inflation_multiplier
            
            headroom_before_insurance_spike = max(0.00, target_ceiling - existing_magi_base)
            if headroom_before_insurance_spike > 0:
                estimated_bracket_fill = base_outflows - natural_inflows
                estimated_tax_markup = 1.15 
                grossed_up_draw_target = estimated_bracket_fill * estimated_tax_markup
                post_sepp_bracket_withdrawal = min(traditional_401k, headroom_before_insurance_spike, max(0.00, grossed_up_draw_target))
                traditional_401k -= post_sepp_bracket_withdrawal
                from_401k += post_sepp_bracket_withdrawal
        elif "RMD" in rmd_label_tag:
            label_suffix = rmd_label_tag
        # --- 1. LIQUID DEFICIT CASCADING ENGINE ---
        available_cash_pool = natural_inflows + from_401k
        net_deficit = max(0.00, base_outflows - available_cash_pool)
        from_brokerage = from_roth = 0.00

        if net_deficit > 0:
            from_brokerage = min(brokerage_pool, net_deficit)
            brokerage_pool -= from_brokerage
            net_deficit -= from_brokerage

        if net_deficit > 0:
            if not sepp_active and husband_age < 59.5:
                trigger_sepp_next_year = True
            from_roth = min(roth_pool, net_deficit)
            roth_pool -= from_roth
            net_deficit -= from_roth

        if net_deficit > 0 and traditional_401k > 0:
            extra_draw = min(traditional_401k, net_deficit)
            traditional_401k -= extra_draw
            net_deficit -= extra_draw
            from_401k += extra_draw

        if available_cash_pool > base_outflows:
            surplus = available_cash_pool - base_outflows
            brokerage_pool += surplus

        # --- 2. EXECUTE INTENTIONAL ROTH CONVERSIONS ---
        if active_bracket > 0 and not brokerage_was_exhausted:
            fed_brackets = getattr(config, "IRS_MFJ_TAX_BRACKETS", [])
            target_rate = float(active_bracket) / 100.0
            base_ceiling = 0.00
            for ceiling, rate, _ in fed_brackets:
                if abs(rate - target_rate) < 0.001:
                    base_ceiling = ceiling
                    break
            deduction_factor = fed_deduction * inflation_multiplier
            gross_bracket_ceiling = base_ceiling + deduction_factor
            conversion_target = max(0.00, gross_bracket_ceiling - from_401k - brokerage_gains)
            actual_conversion = min(traditional_401k, conversion_target)
        else:
            actual_conversion = 0.00

        traditional_401k -= actual_conversion
        roth_pool += actual_conversion

        # --- 3. PROGRESSIVE MULTI-AUTHORITY TAX RESOLUTION ---
        y_total_taxable_income = actual_conversion + from_401k + brokerage_gains
        fed_tax, nm_tax = calculate_progressive_taxes(y_total_taxable_income)
        total_taxes = fed_tax + nm_tax
        
        remaining_tax = total_taxes
        if remaining_tax > 0:
            tax_from_brok = min(brokerage_pool, remaining_tax)
            brokerage_pool -= tax_from_brok
            remaining_tax -= tax_from_brok
            from_brokerage += tax_from_brok
        if remaining_tax > 0:
            tax_from_roth = min(roth_pool, remaining_tax)
            roth_pool -= tax_from_roth
            remaining_tax -= tax_from_roth
            from_roth += tax_from_roth

        traditional_401k *= (1.0 + growth_rate)
        roth_pool *= (1.0 + growth_rate)
        brokerage_pool *= (1.0 + growth_rate)

        # --- 4. DATA MATRIX PACKING & LEDGER SPLITS ---
        monthly_ledger = []
        active_months = months_list if year_idx > 0 else months_list[months_list.index(start_month):]
        num_active = len(active_months)
        
        for m in months_list:
            if m in active_months:
                monthly_ledger.append({
                    "month": m, "from_inflow": round(natural_inflows / num_active, 2),
                    "from_brokerage": round(from_brokerage / num_active, 2),
                    "from_roth": round(from_roth / num_active, 2),
                    "from_401k": round(from_401k / num_active, 2),
                    "health_draw": round(health_cost / num_active, 2)
                })
            else:
                monthly_ledger.append({
                    "month": m, "from_inflow": 0.00, "from_brokerage": 0.00, 
                    "from_roth": 0.00, "from_401k": 0.00, "health_draw": 0.00
                })

        # Safely establish missing string markers to prevent NameError compilation crashes
        safeguard_label = ""
        if "rmd_label_tag" in locals() and rmd_label_tag:
            safeguard_label = rmd_label_tag
        elif "sepp_label_tag" in locals() and sepp_label_tag:
            safeguard_label = sepp_label_tag

        year_row = {
            "year": current_year, "wife_age": wife_age, "husband_age": husband_age,
            "active_bracket": f"{active_bracket}%" if active_bracket > 0 else "0%",
            "start_brokerage": start_brokerage, "start_trad": start_trad, "actual_conversion": actual_conversion,
            "start_roth": start_roth, "living_expense": living_exp, "total_taxes": total_taxes,
            "fed_tax": fed_tax, "nm_tax": nm_tax, "true_taxable_income": y_total_taxable_income,
            "rmd_amount": rmd_distribution, "healthcare_cost": health_cost, "pension_ss_rent": natural_inflows,
            "brokerage_gains": brokerage_gains, "required_income": living_exp + total_taxes + health_cost,
            "from_brokerage": from_brokerage, "from_roth": from_roth, "from_401k": from_401k,
            "label_suffix": safeguard_label, "end_roth": roth_pool, "end_brokerage": brokerage_pool,
            "end_trad": traditional_401k, "monthly_ledger": monthly_ledger
        }
        timeline_data.append(year_row)

        # OVERRIDE THE PREMATURE BALANCES BREAK SWITCH WITH A REPAIRED AGE CEILING CONSTRAINT
        if husband_age >= 90:
            break

    return timeline_data


def generate_all_balance_driven_combinations():
    """Generates all initial conversion path configurations via Cartesian product matching."""
    bracket_options = getattr(config, "AVAILABLE_BRACKET_CHOICES", [0, 12, 22, 24])
    unique_keys = set()
    results_pool = []
    
    target_horizon = getattr(config, "RUNWAY_HORIZON_YEARS", 5)
    print(f"[INFO] Initializing dynamic hybrid Cartesian simulation trees over a {target_horizon}-Year optimization window...")
    
    raw_permutations = list(itertools.product(bracket_options, repeat=target_horizon))
    for permutation in raw_permutations:
        rotation_list = list(permutation)
        sim_data = run_financial_simulation(rotation_list)
        if not sim_data:
            continue
            
        years_to_clear = sum(1 for y in sim_data if y.get("start_trad", 0.00) > 500.00 and "[SEPP]" not in y.get("label_suffix", ""))
        seq_key = str(rotation_list)
        if seq_key in unique_keys:
            continue
        unique_keys.add(seq_key)
        
        results_pool.append({
            "rotation": rotation_list,
            "years_to_convert": years_to_clear if years_to_clear > 0 else 1,
            "simulation_data": sim_data
        })
    return results_pool, getattr(config, "DYNAMIC_BRACKET_SCHEDULE", [])


def score_unrestricted_matrix(results_pool):
    """Ranks and scores survival trajectories using conformed weighted priority dimensions."""
    scoreboard = []
    if not results_pool:
        return scoreboard

    max_estate = max(
        r["simulation_data"][-1]["end_brokerage"] + r["simulation_data"][-1]["end_trad"] + r["simulation_data"][-1]["end_roth"]
        for r in results_pool
    )
    
    weights = getattr(config, "OPTIMIZATION_WEIGHTS", {"estate_value": 30.0, "liquidity_buffer": 20.0, "clock_safety": 20.0, "lifetime_tax_drag": 15.0, "tax_volatility": 15.0})
    
    for item in results_pool:
        rotation = item["rotation"]
        sim_data = item["simulation_data"]
        final_row = sim_data[-1]
        
        ending_estate = final_row["end_brokerage"] + final_row["end_trad"] + final_row["end_roth"]
        total_taxes = sum(y["total_taxes"] for y in sim_data)
        
        is_brok_depleted = any(y["end_brokerage"] <= 0.00 and y["wife_age"] < 61 for y in sim_data)
        
        estate_score = (ending_estate / max_estate) * weights.get("estate_value", 30.0) if max_estate > 0 else 0.0
        liq_score = weights.get("liquidity_buffer", 20.0) if not is_brok_depleted else (weights.get("liquidity_buffer", 20.0) * 0.5)
        clock_score = weights.get("clock_safety", 20.0)
        tax_efficiency = max(0.0, weights.get("lifetime_tax_drag", 15.0) - (total_taxes / 50000.0))
        
        max_single_tax = max(y["total_taxes"] for y in sim_data)
        tax_ceiling = getattr(config, "MAX_ALLOWED_SINGLE_YEAR_TAX", 150000.00)
        volatility_score = 0.0 if max_single_tax > tax_ceiling else max(0.0, weights.get("tax_volatility", 15.0) * (1.0 - (max_single_tax / tax_ceiling)))
        
        switches = sum(1 for i in range(len(rotation)-1) if rotation[i] != rotation[i+1])
        friction = switches * 0.25
        
        final_score = max(0.0, min(100.0, estate_score + liq_score + clock_score + tax_efficiency + volatility_score - friction))
        empirical_betr = calculate_empirical_betr(ending_estate, rotation)
        
        scoreboard.append({
            "rotation_sequence": rotation, "years_to_convert": item["years_to_convert"],
            "lifetime_taxes_paid": total_taxes, "net_total_estate": ending_estate,
            "empirical_betr": empirical_betr, "liq_buffer": liq_score, "clock_safety": clock_score,
            "roth_split": estate_score, "legis_risk": tax_efficiency, "suitability_score": final_score,
            "simulation_data": sim_data
        })
        
    scoreboard.sort(key=lambda x: (x["suitability_score"], x["net_total_estate"]), reverse=True)
    return scoreboard


def print_complete_unrestricted_scoreboard(scoreboard_data):
    """Prints the comprehensive ranked hybrid multi-strategy benchmark leaderboard."""
    print("\n" + "="*190)
    print("             RANKED RETIREMENT MATRIX SCOREBOARD: COMPREHENSIVE STRATEGY VARIATIONS")
    print("="*190)
    print(f"{'Rank':<5} | {'Bracket Rotation Sequence Pattern':<55} | {'Clear':<7} | {'Est Taxes':<14} | {'End Estate':<15} | {'BETR Hurdle':<11} | {'Liq Buffer':<11} | {'IRS Clock':<10} | {'Roth Split':<11} | {'Legis Risk':<12} | {'FINAL SCORE':<12}")
    print("-"*190)
    
    for idx, r in enumerate(scoreboard_data[:30], start=1):
        seq_str = " -> ".join(f"{b}%" for b in r["rotation_sequence"])
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

        # Clean string layout conversions matching the exact column header sizes
        sb = f"${r.get('start_brokerage', 0.00):,.2f}"
        st = f"${r.get('start_trad', 0.00):,.2f}"
        sc = f"${r.get('actual_conversion', 0.00):,.2f}"
        sr = f"${r.get('start_roth', 0.00):,.2f}"
        le = f"${r.get('living_expense', 0.00):,.2f}"
        ct = f"${r.get('total_taxes', 0.00):,.2f}"
        hc = f"${r.get('healthcare_cost', 0.00):,.2f}"
        inf = f"${r.get('pension_ss_rent', 0.00):,.2f}"
        bg = f"${r.get('brokerage_gains', 0.00):,.2f}"
        ri = f"${r.get('required_income', 0.00):,.2f}"
        fb = f"${r.get('from_brokerage', 0.00):,.2f}"
        fr = f"${r.get('from_roth', 0.00):,.2f}"
        er = f"${r.get('end_roth', 0.00):,.2f}"

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
    # 1. Generate combinations and compute scoreboard rankings
    raw_pool, cached_sched = generate_all_balance_driven_combinations()
    completed_scoreboard = score_unrestricted_matrix(raw_pool)
    print_complete_unrestricted_scoreboard(completed_scoreboard)
        
    while True:
        if not completed_scoreboard:
            break
        print("\n" + "-"*80)
        print("Commands: [Rank Number] = Inspect Ledger Details | 'q' = Quit")
        user_input = input("Select an option: ").strip()
            
        if user_input.lower() == 'q':
            break
        else: 
            try:
                target_rank = int(user_input)
                if 1 <= target_rank <= len(completed_scoreboard):
                    selected_record = completed_scoreboard[target_rank - 1]
                    rotation_list = selected_record["rotation_sequence"]
                    full_timeline_data = run_financial_simulation(rotation_list)
                    
                    # --- FIXED: ELEVATED SUMMARY CALCULATOR PREVENTS NAMING ERRORS ---
                    grand_totals = {
                        "taxes": 0.0, "health": 0.0, "base_inflow": 0.0, "taxable_income": 0.0,
                        "brokerage": 0.0, "roth": 0.0, "401k": 0.0, "conversions": 0.0,
                        "living_exp": 0.0, "required_income": 0.0, "brok_gains": 0.0
                    }
                    
                    for y_idx, y_row in enumerate(full_timeline_data):
                        y_from_brokerage = sum(m.get("from_brokerage", 0.00) for m in y_row.get("monthly_ledger", []))
                        y_from_roth = sum(m.get("from_roth", 0.00) for m in y_row.get("monthly_ledger", []))
                        y_from_401k = sum(m.get("from_401k", 0.00) for m in y_row.get("monthly_ledger", []))
                        actual_annual_conversion = y_row.get("actual_conversion", 0.00)
                        
                        grand_totals["taxes"] += y_row.get("total_taxes", 0.00)
                        grand_totals["health"] += y_row.get("healthcare_cost", 0.00)
                        grand_totals["base_inflow"] += y_row.get("pension_ss_rent", 0.00)
                        grand_totals["brokerage"] += y_from_brokerage
                        grand_totals["roth"] += y_from_roth
                        grand_totals["401k"] += y_from_401k
                        grand_totals["conversions"] += actual_annual_conversion
                        grand_totals["living_exp"] += y_row.get("living_expense", 0.00)
                        grand_totals["required_income"] += y_row.get("required_income", 0.00)
                        grand_totals["brok_gains"] += y_row.get("brokerage_gains", 0.00)

                    # 2. Display the Interactive Sub-Menu Matrix Style Picker
                    print("\n[1] View Full Chronological Transaction Ledger")
                    print("[2] View Side-by-Side Brokerage vs. Roth Annual Balance Matrix")
                    view_choice = input("Select viewing matrix detail style (1 or 2): ").strip()
                    
                    if view_choice == "2":
                        print_dual_pool_ledger(selected_record, rotation_list)
                    else:
                        pattern_display_str = " -> ".join(f"{br}%" for br in rotation_list)
                        
                        print("\n" + "="*300)
                        print(f" YEAR-BY-YEAR DETAIL DRAWDOWN LEDGER FOR RANK {target_rank} Pattern: {pattern_display_str} (Projections to Age 90)")
                        print("="*300)
                        print(f"{'#':<3} | {'Yr':<4} | {'H_Age':<5} | {'Bracket':<7} | {'Brok Start':<14} | {'401k Start':<14} | {'Converted':<14} | {'Roth Start':<14} | {'Living Exp':<14} | {'Est Taxes':<12} | {'Health Cost':<12} | {'Inflow Base':<13} | {'Brok Yield':<12} | {'Req Income':<14} | {'From Broker':<13} | {'From Roth':<13} | {'From 401k':<22} | {'End Roth':<14}")
                        print("-"*300)
                        
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
                            y_req_income = y_row.get("required_income", 0.00)
                            y_brok_gains = y_row.get("brokerage_gains", 0.00)
                            
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
                            
                            label_tag = y_row.get("label_suffix", "")
                            f4 = f"${y_from_401k:,.2f}{label_tag}"
                            er = f"${y_row.get('end_roth', 0.00):,.2f}"
                            
                            yr_short = str(y_row.get('year', 2027))[-2:]
                            h_age = y_row.get("husband_age", 46 + y_idx)
                            
                            print(f"{y_idx + 1:<3} | {yr_short:<4} | {h_age:<5} | {active_b_pct:<7} | {sb:<14} | {st:<14} | {sc:<14} | {sr:<14} | {le:<14} | {ct:<12} | {hc:<12} | {inf:<13} | {bg:<12} | {ri:<14} | {fb:<13} | {fr:<13} | {f4:<22} | {er:<14}")
                                  
                        print("-"*300)
                        print(f"{'TOTALS':<10} | {'-':<4} | {'-':<5} | {'-':<7} | {'-':<14} | {'-':<14} | ${grand_totals['conversions']:<12,.2f} | {'-':<14} | ${grand_totals['living_exp']:<12,.2f} | ${grand_totals['taxes']:<11,.2f} | ${grand_totals['health']:<11,.2f} | ${grand_totals['base_inflow']:<12,.2f} | ${grand_totals['brok_gains']:<11,.2f} | ${grand_totals['required_income']:<13,.2f} | ${grand_totals['brokerage']:<12,.2f} | ${grand_totals['roth']:<12,.2f} | ${grand_totals['401k']:<21,.2f} | {'-':<14}")
                        print("="*300)

                    # 3. File compilation hook trigger check
                    export_input = input(f"\nWould you like to generate full custom Excel/PDF dossiers for Rank {target_rank}? (y/n): ").strip().lower()
                    if export_input == 'y':
                        try:
                            # Auto-detect filename based on what is in your folder
                            report_gen_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gen_excel.py")
                            if not os.path.exists(report_gen_path):
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
                            print(f"[ERROR] Could not load or execute report document generation hooks: {err}")
                else:
                    print(f"[ERROR] Please select a rank between 1 and {len(completed_scoreboard)}")
            except ValueError:
                print("[ERROR] Invalid numeric character parsed.")

