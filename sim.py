# -*- coding: utf-8 -*-
"""
RETIREMENT RUNWAY SENSITIVITY ANALYSIS SYSTEM - STANDALONE ENGINE
File: sim.py
Description: Manages self-contained financial projections, progressive tax models,
             and automated binary searches for minimal principal thresholds.
Features: Renders Scenario 1 and Scenario 2 metrics simultaneously on boot.
          Prompts for scenario selection upfront before generating the combinations tree.
          Evaluates the strategy variations scoreboard specific to that scenario's cash flows.
          Enforces a flat 0% asset yield drag on non-retirement brokerage capital.
          Displays the complete matrix scoreboard of different tax bracket percentage 
          options before prompting for line-by-line inspection.
Budget Lockout Engine: Initial brokerage capital is strictly locked to your config limits 
                       defined dynamically as the sum of Base Cash + House Proceeds.
                       Cash on hand is treated as an immutable constant that cannot increase;
                       the portfolio can only expand via house sale proceeds adjustments.
                       Scenario 1 and Scenario 2 strictly use their respective solved minimum 
                       house sale proceeds in-memory to guarantee distinct scenario benchmarks.
Loophole Repair: Strictly audits tax liabilities drawn from the Roth pool against the 5-year clock calendar.
Completely standalone and independent with zero cross-imports from other strategy optimization modules.
"""
import os
import sys
import itertools
import importlib.util

# Ensure local directory takes precedence in path lookups
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    import config
except ImportError:
    print("[ERROR] Simulation script must be placed in the same folder as config.py")
    sys.exit(1)


def calc_marginal_tax(taxable_income, deduction, brackets):
    """Core mathematical engine for standard marginal tax brackets."""
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
    nm_deduction = shields.get("nm_joint_exemption", getattr(config, "NM_MFJ_STANDARD_DEDUCTION", 32200.00))
    nm_tax = calc_marginal_tax(income, nm_deduction, nm_brackets)
    return fed_tax, nm_tax


def run_financial_simulation(bracket_schedule, custom_brokerage=None, custom_rent=None, custom_living=None):
    """
    30-Year Financial Simulation Matrix. Fully resolves cash distributions, 
    tax-drag ordering, and annual investment/cash market compounding.
    Allows dynamic overrides for multi-variable sensitivity analysis.
    """
    timeline_data = []
    
    starting_balances = getattr(config, "STARTING_BALANCES", {})
    traditional_401k = starting_balances.get("trad_401k", 1476432.85)
    roth_pool = starting_balances.get("roth_pool", 130967.93)
    
    # IRS CHRONOLOGICAL BASIS LADDER INITIALIZATION
    penalty_free_basis = starting_balances.get("roth_pool", 130967.93)
    active_conversion_ladder = {}
    
    if custom_brokerage is not None:
        brokerage_pool = custom_brokerage
    else:
        base_cash = getattr(config, "BASE_CASH", 71000.00)
        total_brok_config = getattr(config, "TOTAL_INITIAL_BROKERAGE", 436986.29)
        house_proceeds = getattr(config, "HOUSE_PROCEEDS", total_brok_config - base_cash)
        brokerage_pool = base_cash + house_proceeds
    
    growth_rate = getattr(config, "GROWTH_RATE", 0.06)
    inflation_rate = getattr(config, "INFLATION_RATE", 0.03)
    
    # Cash yield rate set to 0% for brokerage assets to eliminate interest accumulation
    cash_yield = 0.00 
    
    phase1_duration = getattr(config, "PHASE_1_DURATION_YEARS", 7)
    spending_matrix = getattr(config, "SPENDING", {})
    aging_modifiers = getattr(config, "LIFESTYLE_AGING_MODIFIERS", {})
    
    start_year = 2027
    wife_start_age = getattr(config, "WIFE_START_AGE", 47)
    default_fallback = getattr(config, "DEFAULT_FALLBACK_BRACKET", 22)

    for year_idx in range(30):
        current_year = start_year + year_idx
        wife_age = wife_start_age + year_idx
        
        penalty = 0.00
        is_broken = False
        
        # IRS Clock Seasoning: Move matured conversions into penalty-free basis
        target_seasoning_year = current_year - 5
        if target_seasoning_year in active_conversion_ladder:
            penalty_free_basis += active_conversion_ladder.pop(target_seasoning_year)
            
        if traditional_401k <= 500.00:
            active_bracket = 0
        elif year_idx < len(bracket_schedule):
            active_bracket = bracket_schedule[year_idx]
        else:
            active_bracket = default_fallback
            
        start_brokerage = brokerage_pool
        start_trad = traditional_401k
        start_roth = roth_pool
        
        # Brokerage gains evaluate to exactly 0.00 due to flat non-increasing configuration
        brokerage_gains = start_brokerage * cash_yield
        
        remaining_runway_years = max(1, 61 - wife_age)
        inflation_multiplier = (1.0 + inflation_rate) ** year_idx
        
        if year_idx < phase1_duration:
            if custom_living is not None:
                living_exp = custom_living * inflation_multiplier
            else:
                living_exp = spending_matrix.get("phase1_living_expense", 65000.00) * inflation_multiplier
            health_cost = spending_matrix.get("phase1_healthcare_cost", 0.00) * inflation_multiplier
            if custom_rent is not None:
                rental_income = custom_rent
            else:
                rental_income = spending_matrix.get("phase1_rental_income", 24000.00)
            base_outflows = living_exp + health_cost
            baseline_inflows = rental_income
        else:
            living_exp = spending_matrix.get("phase2_living_expense", 100000.00) * inflation_multiplier
            health_cost = spending_matrix.get("phase2_healthcare_cost", 9600.00) * inflation_multiplier
            
            if wife_age >= 80:
                living_exp *= aging_modifiers.get("age_80_no_go", 0.70)
            elif wife_age >= 70:
                living_exp *= aging_modifiers.get("age_70_slow_go", 0.85)
                
            base_outflows = living_exp + health_cost
            baseline_inflows = 0.00
            
        if wife_age >= 61:
            baseline_inflows += getattr(config, "ANNUAL_PENSION_VALUE", 35250.00) * inflation_multiplier
        if wife_age >= 62:
            baseline_inflows += getattr(config, "ANNUAL_SOCIAL_SECURITY", 100000.00) * inflation_multiplier
            
        # Resolve Living Deficits and Distributions Chronologically
        net_deficit = max(0.00, base_outflows - baseline_inflows)
        from_inflow = min(base_outflows, baseline_inflows)
        from_brokerage = from_401k = from_roth = 0.00
        
        if net_deficit > 0:
            from_brokerage = min(brokerage_pool, net_deficit)
            brokerage_pool -= from_brokerage
            net_deficit -= from_brokerage
            
        # Chronological Outflow Basis Drawdown Processor
        if net_deficit > 0:
            from_roth = min(roth_pool, net_deficit)
            roth_pool -= from_roth
            net_deficit -= from_roth
            
            roth_draw_remaining = from_roth
            if penalty_free_basis > 0:
                basis_drawn = min(roth_draw_remaining, penalty_free_basis)
                penalty_free_basis -= basis_drawn
                roth_draw_remaining -= basis_drawn
                
            if roth_draw_remaining > 0 and wife_age < 59.5:
                for conv_year in sorted(active_conversion_ladder.keys()):
                    if roth_draw_remaining <= 0:
                        break
                    unseasoned_pool = active_conversion_ladder[conv_year]
                    if unseasoned_pool > 0:
                        ladder_drawn = min(roth_draw_remaining, unseasoned_pool)
                        active_conversion_ladder[conv_year] -= ladder_drawn
                        roth_draw_remaining -= ladder_drawn
                        is_broken = True
                        penalty += ladder_drawn * 0.10
                
                if penalty > 0:
                    roth_pool -= penalty
            
        if net_deficit > 0 and traditional_401k > 0:
            from_401k = min(traditional_401k, net_deficit)
            traditional_401k -= from_401k
            net_deficit -= from_401k

        # Determine Conversion Target
        conversion_target = 0.00
        if active_bracket > 0:
            if active_bracket == 22:
                conversion_target = 244600.00  
            elif active_bracket == 24:
                conversion_target = 436750.00  
            else:
                conversion_target = 545650.00
            
            # Headroom calculations clear smoothly with zeroed brokerage interest gains
            conversion_target = max(0.00, conversion_target - from_401k - brokerage_gains)
            
            if remaining_runway_years <= 1:
                conversion_target = traditional_401k

        actual_conversion = min(traditional_401k, conversion_target)
        traditional_401k -= actual_conversion
        roth_pool += actual_conversion

        if actual_conversion > 0:
            active_conversion_ladder[current_year] = active_conversion_ladder.get(current_year, 0.00) + actual_conversion

        # Compile progressive tax calculations with flat asset yields
        y_total_taxable_income = actual_conversion + from_401k + brokerage_gains
        fed_tax, nm_tax = calculate_progressive_taxes(y_total_taxable_income)
        total_taxes = fed_tax + nm_tax
        
        # Pay conversion taxes from Brokerage, fallback to Roth if dry
        remaining_tax_to_pay = total_taxes
        tax_from_brokerage = 0.0
        tax_from_roth = 0.0
        if remaining_tax_to_pay > 0:
            tax_from_brokerage = min(brokerage_pool, remaining_tax_to_pay)
            brokerage_pool -= tax_from_brokerage
            remaining_tax_to_pay -= tax_from_brokerage
            
        if remaining_tax_to_pay > 0:
            tax_from_roth = min(roth_pool, remaining_tax_to_pay)
            roth_pool -= tax_from_roth
            remaining_tax_to_pay -= tax_from_roth
            
            # --- LOOPHOLE REPAIR: AUDIT TAX LIABILITIES AGAINST THE 5-YEAR LADDER WINDOWS ---
            tax_draw_remaining = tax_from_roth
            if penalty_free_basis > 0:
                basis_drawn = min(tax_draw_remaining, penalty_free_basis)
                penalty_free_basis -= basis_drawn
                tax_draw_remaining -= basis_drawn
                
            if tax_draw_remaining > 0 and wife_age < 59.5:
                tax_penalty = 0.00
                for conv_year in sorted(active_conversion_ladder.keys()):
                    if tax_draw_remaining <= 0:
                        break
                    unseasoned_pool = active_conversion_ladder[conv_year]
                    if unseasoned_pool > 0:
                        ladder_drawn = min(tax_draw_remaining, unseasoned_pool)
                        active_conversion_ladder[conv_year] -= ladder_drawn
                        tax_draw_remaining -= ladder_drawn
                        is_broken = True
                        tax_penalty += ladder_drawn * 0.10
                
                if tax_penalty > 0:
                    penalty += tax_penalty
                    roth_pool -= tax_penalty

        # Build ledger segments chronologically
        months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        active_start_month = getattr(config, "RETIREMENT_START_MONTH", "Feb") if year_idx == 0 else "Jan"
        active_month_index = months_list.index(active_start_month)
        total_active_months_in_year = 12.0 - active_month_index
        
        # Identify how many valid voucher payment windows fall within this year's active track
        active_vouchers = [m for m in months_list[active_month_index:] if m in ["Jan", "Apr", "Jun", "Sep"]]
        total_vouchers_this_year = len(active_vouchers) if active_vouchers else 4

        monthly_ledger = []
        for m_idx, m_name in enumerate(months_list):
            if m_idx < active_month_index:
                monthly_ledger.append({
                    "month": m_name, "from_inflow": 0.00, "from_brokerage": 0.00, "from_roth": 0.00, "from_401k": 0.00,
                    "is_irs_violation": False, "penalty_paid": 0.00
                })
            else:
                m_inflow = from_inflow / total_active_months_in_year
                m_brokerage = from_brokerage / total_active_months_in_year
                m_roth = from_roth / total_active_months_in_year
                m_401k = from_401k / total_active_months_in_year
                
                if m_name in active_vouchers:
                    m_brokerage += tax_from_brokerage / total_vouchers_this_year
                    m_roth += tax_from_roth / total_vouchers_this_year

                monthly_ledger.append({
                    "month": m_name, "from_inflow": m_inflow, "from_brokerage": m_brokerage,
                    "from_roth": m_roth, "from_401k": m_401k,
                    "is_irs_violation": is_broken if m_name == active_start_month and penalty > 0 else False,
                    "penalty_paid": penalty if m_name == active_start_month and penalty > 0 else 0.00
                })

        # Brokerage pool remains completely flat with 0% compounding applied
        brokerage_pool *= 1.00
        traditional_401k *= (1.0 + growth_rate)
        roth_pool *= (1.0 + growth_rate)
        
        penalty_free_basis *= (1.0 + growth_rate)
        for c_yr in active_conversion_ladder:
            active_conversion_ladder[c_yr] *= (1.0 + growth_rate)
        
        year_row = {
            "year": current_year, "wife_age": wife_age,
            "husband_age": getattr(config, "HUSBAND_START_AGE", 46) + year_idx,
            "month": active_start_month,
            "start_brokerage": start_brokerage, "start_trad": start_trad, "start_roth": start_roth,
            "end_brokerage": brokerage_pool, "end_trad": traditional_401k, "end_roth": roth_pool, 
            "fed_tax": fed_tax, "nm_tax": nm_tax, "total_taxes": total_taxes, "living_expense": living_exp,
            "healthcare_cost": health_cost, "pension_ss_rent": from_inflow, "monthly_ledger": monthly_ledger,
            "actual_conversion": actual_conversion,
            "true_taxable_income": y_total_taxable_income,
            "required_income": living_exp + total_taxes + health_cost,
            "brokerage_gains": brokerage_gains
        }
        timeline_data.append(year_row)
        
        total_remaining_assets = brokerage_pool + traditional_401k + roth_pool
        if total_remaining_assets <= 1.00:
            break
            
    return timeline_data


def execute_sensitivity_analysis_solvers(optimal_rotation, custom_living=None):
    """Calculates minimal house proceed requirements while holding base cash fixed."""
    print("="*95)
    print("        EXECUTING RE-VERIFIED SENSITIVITY SOLVER SIMULATION DATA LAYOUT")
    print("="*95)
    
    base_cash_global = getattr(config, "BASE_CASH", 71000.00)
    spending_matrix = getattr(config, "SPENDING", {})
    config_rent = spending_matrix.get("phase1_rental_income", 24000.00)
    base_rent_scen1 = max(24000.00, config_rent)
    
    # --- SCENARIO 1 SOLVER: RENT ACTIVE, SOLVE FOR REFERENCE HOUSE FLOOR ---
    low_h1, high_h1 = 0.0, 3000000.0
    min_house_needed_1 = high_h1
    for _ in range(35):
        mid_h1 = (low_h1 + high_h1) / 2.0
        total_brok = base_cash_global + mid_h1
        sim_data = run_financial_simulation(optimal_rotation, custom_brokerage=total_brok, custom_rent=base_rent_scen1, custom_living=custom_living)
        
        success = True
        for y_row in sim_data:
            if (y_row.get("end_brokerage", 0.0) + y_row.get("end_trad", 0.0) + y_row.get("end_roth", 0.0)) <= 500.00:
                success = False
            for m_data in y_row.get("monthly_ledger", []):
                if m_data.get("penalty_paid", 0.00) > 0.01 or m_data.get("from_401k", 0.00) > 0.01:
                    success = False
        if success:
            min_house_needed_1 = mid_h1
            high_h1 = mid_h1
        else:
            low_h1 = mid_h1
            
    print(f"Scenario 1: Active Flat Rental Inflow = ${base_rent_scen1:,.2f}/Yr, Fixed Base Cash = ${base_cash_global:,.2f}")
    print(f"  ├── Implied Minimum House Sale Proceeds Required   : ${min_house_needed_1:,.2f}")
    print(f"  └── Resulting Total Initial Brokerage Pool         : ${base_cash_global + min_house_needed_1:,.2f}")
    
    # --- SCENARIO 2 SOLVER: RENT AT $0.00, SOLVE FOR REQUIRED HOUSE FLOOR ---
    low_h2, high_h2 = 0.0, 3000000.0
    min_house_needed_2 = high_h2
    for _ in range(35):
        mid_h2 = (low_h2 + high_h2) / 2.0
        total_brok = base_cash_global + mid_h2
        sim_data = run_financial_simulation(optimal_rotation, custom_brokerage=total_brok, custom_rent=0.00, custom_living=custom_living)
        
        success = True
        for y_row in sim_data:
            if (y_row.get("end_brokerage", 0.0) + y_row.get("end_trad", 0.0) + y_row.get("end_roth", 0.0)) <= 500.00:
                success = False
            for m_data in y_row.get("monthly_ledger", []):
                if m_data.get("penalty_paid", 0.00) > 0.01 or m_data.get("from_401k", 0.00) > 0.01:
                    success = False
        if success:
            min_house_needed_2 = mid_h2
            high_h2 = mid_h2
        else:
            low_h2 = mid_h2
            
    print(f"\nScenario 2: Dead Rental Stream (Rent = $0.00), Fixed Base Cash = ${base_cash_global:,.2f}")
    print(f"  ├── Implied Minimum House Sale Proceeds Required   : ${min_house_needed_2:,.2f}")
    print(f"  └── Resulting Total Initial Brokerage Pool         : ${base_cash_global + min_house_needed_2:,.2f}")
    print("="*95)
    return min_house_needed_1, min_house_needed_2


def generate_all_balance_driven_combinations(custom_brokerage, custom_rent, custom_living):
    """Generates all conversion paths restricted strictly to years before Wife turns 61."""
    bracket_options = getattr(config, "AVAILABLE_BRACKET_CHOICES", [0, 22, 24])
    unique_executed_keys = set()
    absolute_results_pool = []
    
    target_runway_horizon = max(1, 61 - getattr(config, "WIFE_START_AGE", 47)) 
    raw_permutations = list(itertools.combinations_with_replacement(bracket_options, target_runway_horizon))
            
    for permutation in raw_permutations:
        rotation_list = list(permutation)
        
        simulation_data = run_financial_simulation(rotation_list, custom_brokerage=custom_brokerage, custom_rent=custom_rent, custom_living=custom_living)
        if not simulation_data or len(simulation_data) == 0:
            continue
            
        years_to_clear = 0
        for year_row in simulation_data:
            if year_row.get("start_trad", 0.00) > 500.00:
                years_to_clear += 1
                
        full_executed_pattern = [br for br in rotation_list]
        seq_key = str(full_executed_pattern)
        
        if seq_key in unique_executed_keys:
            continue
        unique_executed_keys.add(seq_key)
        
        absolute_results_pool.append({
            "rotation": full_executed_pattern,
            "years_to_convert": years_to_clear if years_to_clear > 0 else 1,
            "simulation_data": simulation_data
        })
            
    return absolute_results_pool, getattr(config, "DYNAMIC_BRACKET_SCHEDULE", [])


def score_unrestricted_matrix(absolute_results_pool, original_schedule, custom_brokerage, custom_rent, custom_living):
    """Disqualifies strategies with ordinary 401k draws or IRS penalties. Ranks by Ending Estate."""
    optimization_scoreboard = []
    if not absolute_results_pool:
        return optimization_scoreboard

    seen_execution_patterns = set()
    max_estate_found = 0.0
    for item in absolute_results_pool:
        sim_data = item["simulation_data"]
        violates_rules = False
        for year_row in sim_data:
            for m_data in year_row.get("monthly_ledger", []):
                if m_data.get("from_401k", 0.00) > 0.01 or m_data.get("penalty_paid", 0.00) > 0.01:
                    violates_rules = True
            if violates_rules:
                break
        if sim_data[-1].get("end_trad", 0.00) <= 500.00 and not violates_rules:
            ending_estate = sim_data[-1].get("end_brokerage", 0.00) + sim_data[-1].get("end_trad", 0.00) + sim_data[-1].get("end_roth", 0.00)
            if ending_estate > max_estate_found:
                max_estate_found = ending_estate

    if max_estate_found == 0.0:
        max_estate_found = max(item["simulation_data"][-1].get("end_brokerage", 0.00) + 
                               item["simulation_data"][-1].get("end_trad", 0.00) + 
                               item["simulation_data"][-1].get("end_roth", 0.00) 
                               for item in absolute_results_pool)

    for item in absolute_results_pool:
        clean_sequence = item["rotation"]
        simulation_data = item["simulation_data"]
        actual_clear_year = item["years_to_convert"]
        
        is_illegal_strategy = False
        for year_row in simulation_data:
            for m_data in year_row.get("monthly_ledger", []):
                if m_data.get("from_401k", 0.00) > 0.01 or m_data.get("penalty_paid", 0.00) > 0.01:
                    is_illegal_strategy = True
            if is_illegal_strategy:
                break
        if is_illegal_strategy:
            continue
            
        executed_brackets = []
        for y_idx, y_row in enumerate(simulation_data):
            if y_idx < len(clean_sequence):
                if y_row.get("start_trad", 0.00) <= 500.00:
                    executed_brackets.append(0)
                else:
                    executed_brackets.append(clean_sequence[y_idx])
        
        while len(executed_brackets) > 1 and executed_brackets[-1] == 0:
            executed_brackets.pop()
            
        seq_key = str(executed_brackets)
        if seq_key in seen_execution_patterns:
            continue
        seen_execution_patterns.add(seq_key)

        is_brokerage_broken = False
        for year_row in simulation_data:
            if year_row.get("end_brokerage", 1.0) <= 0.00 and year_row.get("wife_age", 47) < 61:
                is_brokerage_broken = True

        risk_sig = "BROK_DEPLETED" if is_brokerage_broken else "CLEAN RUNWAY"
        final_year_record = simulation_data[-1]
        total_lifetime_taxes = sum(year_row.get("total_taxes", 0.00) for year_row in simulation_data)
        ending_total_estate = final_year_record.get("end_brokerage", 0.00) + final_year_record.get("end_trad", 0.00) + final_year_record.get("end_roth", 0.00)
        
        estate_score = (ending_total_estate / max_estate_found) * 25.0 if max_estate_found > 0 else 0.0
        liq_score = 25.0 if not is_brokerage_broken else 12.5
        clock_score = 25.0  
        tax_efficiency_score = max(0.0, 25.0 - (total_lifetime_taxes / 50000.0))

        base_suitability_score = estate_score + liq_score + clock_score + tax_efficiency_score
        final_suitability_score = base_suitability_score
        if len(set([b for br in executed_brackets if (b := br) > 0])) <= 1:
            final_suitability_score += 15.0
        final_suitability_score = min(100.0, final_suitability_score)
            
        optimization_scoreboard.append({
            "rotation_sequence": executed_brackets, "years_to_convert": actual_clear_year, 
            "lifetime_taxes_paid": total_lifetime_taxes, "net_total_estate": ending_total_estate, 
            "risk_profile": risk_sig, "liq_buffer": liq_score, "clock_safety": clock_score, 
            "roth_split": estate_score, "legis_risk": tax_efficiency_score, "suitability_score": final_suitability_score,
            "simulation_data": simulation_data
        })

    config.DYNAMIC_BRACKET_SCHEDULE = original_schedule
    optimization_scoreboard.sort(key=lambda x: (x["suitability_score"], x["net_total_estate"]), reverse=True)
    return optimization_scoreboard


if __name__ == "__main__":
    spending_matrix = getattr(config, "SPENDING", {})
    config_rent = spending_matrix.get("phase1_rental_income", 24000.00)
    custom_living = spending_matrix.get("phase1_living_expense", 65000.00)
    base_cash_global = getattr(config, "BASE_CASH", 71000.00)
    
    if hasattr(config, "TOTAL_INITIAL_BROKERAGE"):
        total_brok_config = config.TOTAL_INITIAL_BROKERAGE
        house_proceeds_global = getattr(config, "HOUSE_PROCEEDS", total_brok_config - base_cash_global)
    else:
        house_proceeds_global = getattr(config, "HOUSE_PROCEEDS", 300000.00)
        total_brok_config = base_cash_global + house_proceeds_global
        
    # 1. Output simultaneous dual-sensitivity statistics immediately on boot
    min_house_1, min_house_2 = execute_sensitivity_analysis_solvers([22, 22, 22, 22, 22, 22, 22, 22], custom_living=custom_living)
    
    # 2. Prompt for scenario context selection upfront
    print("\n" + "="*95)
    print("        SCENARIO OPTIMIZATION CHOICE CONTEXT MENU")
    print("="*95)
    print("1. Optimize Scenario 1 (Preserve Active Rental Inflow from config)")
    print("2. Optimize Scenario 2 (Force Rental Inflow down to $0.00 for life)")
    print("="*95)
    
    while True:
        scenario_choice = input("Select context scenario to run optimization (1-2): ").strip()
        if scenario_choice in ["1", "2"]:
            break
        print("[ERROR] Invalid choice. Please enter 1 or 2.")
        
    if scenario_choice == "1":
        custom_rent = max(24000.00, config_rent)
        # --- FIXED ALIGNMENT RECONCILIATION: Initialize exactly at the solved scenario bedrock floor ---
        selected_house_proceeds = min_house_1
        custom_brokerage_selected = base_cash_global + selected_house_proceeds
        scen_title = f"SCENARIO 1 (RENT ACTIVE AT ${custom_rent:,.2f}/YR | BROKERAGE SET TO MINIMUM SHORTFALL BEDROCK: ${custom_brokerage_selected:,.2f} [Base Cash: ${base_cash_global:,.2f} LOCKED + House Sale Floor: ${selected_house_proceeds:,.2f}])"
    else:
        custom_rent = 0.00
        # --- FIXED ALIGNMENT RECONCILIATION: Initialize exactly at the solved scenario bedrock floor ---
        selected_house_proceeds = min_house_2
        custom_brokerage_selected = base_cash_global + selected_house_proceeds
        scen_title = f"SCENARIO 2 (DEAD RENTAL STREAM | BROKERAGE SET TO MINIMUM SHORTFALL BEDROCK: ${custom_brokerage_selected:,.2f} [Base Cash: ${base_cash_global:,.2f} LOCKED + House Sale Floor: ${selected_house_proceeds:,.2f}])"

    # 3. Generate percentage options scoreboard tailored to selected scenario constraints
    while True:
        raw_pool, cached_sched = generate_all_balance_driven_combinations(
            custom_brokerage=custom_brokerage_selected, custom_rent=custom_rent, custom_living=custom_living
        )
        completed_scoreboard = score_unrestricted_matrix(
            raw_pool, cached_sched, custom_brokerage=custom_brokerage_selected, custom_rent=custom_rent, custom_living=custom_living
        )
        
        if completed_scoreboard:
            break
            
        print("\n" + "="*95)
        print(f" [ALERT] Your current config.py values will not get the job done safely under {scen_title}!")
        print("  Since you cannot add more money into the plan, you must scale down spending targets.")
        print("="*95 + "\n")
        
        user_expense_input = input(f"Enter a reduced Phase 1 annual living expense value to test (Current: ${custom_living:,.2f}) or 'q' to quit: ").strip()
        if user_expense_input.lower() == 'q':
            sys.exit(0)
        try:
            val = float(user_expense_input)
            if val <= 0:
                print("[ERROR] Lifestyle expense target must be a positive number.")
                continue
            custom_living = val
        except ValueError:
            print("[ERROR] Invalid numeric entry.")

    # 4. Display percentage options scoreboard specifically generated for your scenario choice
    print("\n" + "="*175)
    print(f"             RANKED RETIREMENT MATRIX SCOREBOARD FOR {scen_title}")
    print("="*175)
    print(f"{'Rank':<5} | {'Bracket Rotation Sequence Pattern':<60} | {'Clear':<7} | {'Est Taxes':<14} | {'End Estate':<16} | {'Liq Buffer':<11} | {'IRS Clock':<10} | {'Roth Split':<11} | {'Legis Risk':<11} | {'FINAL SCORE'}")
    print("-"*175)
    for idx, s_row in enumerate(completed_scoreboard):
        rank = idx + 1
        pat_str = " -> ".join(f"{br}%" for br in s_row["rotation_sequence"])
        clear_str = f"{s_row['years_to_convert']} Yrs"
        tax_str = f"${s_row['lifetime_taxes_paid']:,.2f}"
        estate_str = f"${s_row['net_total_estate']:,.2f}"
        liq = f"{s_row['liq_buffer']:.1f}"
        clock = f"{s_row['clock_safety']:.1f}"
        roth = f"{s_row['roth_split']:.1f}"
        legis = f"{s_row['legis_risk']:.1f}"
        score = f"{s_row['suitability_score']:.1f} / 100"
        print(f"{rank:<5} | {pat_str:<60} | {clear_str:<7} | {tax_str:<14} | {estate_str:<16} | {liq:<11} | {clock:<10} | {roth:<11} | {legis:<11} | {score}")
    print("="*175)

    while True:
        if len(completed_scoreboard) == 0:
            print("[ERROR] Failed to compile viable baseline strategies even with fallback overrides.")
            break
        print("\n" + "-"*115)
        user_input = input("Select target strategy rank to inspect year-by-year details (or type 'q' to quit): ").strip()
        if user_input.lower() == 'q': 
            break
            
        try:
            target_rank = int(user_input)
            if target_rank < 1 or target_rank > len(completed_scoreboard): 
                continue
                
            selected_record = completed_scoreboard[target_rank - 1]
            rotation_list = selected_record["rotation_sequence"]
            
            full_timeline_data = run_financial_simulation(rotation_list, custom_brokerage=custom_brokerage_selected, custom_rent=custom_rent, custom_living=custom_living)
            pattern_display_str = " -> ".join(f"{br}%" for br in rotation_list)
            
            print("\n" + "="*286)
            print(f" YEAR-BY-YEAR DETAIL DRAWDOWN LEDGER FOR RANK {target_rank} ({scen_title}) Pattern: {pattern_display_str}")
            print("="*286)
            print(f"{'#':<3} | {'Yr':<4} | {'Bracket':<7} | {'Brok Start':<14} | {'401k Start':<14} | {'Converted':<14} | {'Roth Start':<14} | {'Living Exp':<14} | {'Est Taxes':<12} | {'Health Cost':<12} | {'Inflow Base':<13} | {'Brok Yield':<12} | {'Req Income':<14} | {'From Broker':<13} | {'From Roth':<13} | {'From 401k':<13} | {'End Roth':<14}")
            print("-"*286)
            
            grand_total_taxes = grand_total_health = grand_total_base_inflow = grand_total_taxable_income = grand_total_brokerage = grand_total_roth = grand_total_401k = grand_total_conversions = grand_total_living_exp = grand_total_required_income = grand_total_brok_gains = 0.0
            
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
                
                grand_total_taxes += combined_taxes
                grand_total_health += y_row.get("healthcare_cost", 0.00)
                grand_total_base_inflow += y_row.get("pension_ss_rent", 0.00)
                grand_total_brokerage += y_from_brokerage
                grand_total_roth += y_from_roth
                grand_total_401k += y_from_401k
                grand_total_conversions += actual_annual_conversion
                grand_total_taxable_income += y_total_taxable_income
                grand_total_living_exp += y_row.get("living_expense", 0.00)
                grand_total_required_income += y_req_income
                grand_total_brok_gains += y_brok_gains
                
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
                print(f"{y_idx + 1:<3} | {yr_short:<4} | {active_b_pct:<7} | {sb:<14} | {st:<14} | {sc:<14} | {sr:<14} | {le:<14} | {ct:<12} | {hc:<12} | {inf:<13} | {bg:<12} | {ri:<14} | {fb:<13} | {fr:<13} | {f4:<13} | {er:<14}")
                      
            print("-"*286)
            print(f"{'TOTALS':<10} | {'-':<7} | {'-':<14} | {'-':<14} | ${grand_total_conversions:<12,.2f} | {'-':<14} | ${grand_total_living_exp:<12,.2f} | ${grand_total_taxes:<11,.2f} | ${grand_total_health:<11,.2f} | ${grand_total_base_inflow:<12,.2f} | ${grand_total_brok_gains:<11,.2f} | ${grand_total_required_income:<13,.2f} | ${grand_total_brokerage:<12,.2f} | ${grand_total_roth:<12,.2f} | ${grand_total_401k:<12,.2f} | {'-':<14}")
            print("="*286)
            
            export_input = input(f"\nWould you like to generate full custom Excel/PDF files for Rank {target_rank}? (y/n): ").strip().lower()
            if export_input == 'y':
                try:
                    import importlib.util
                    report_gen_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "report_generator.py")
                    spec = importlib.util.spec_from_file_location("report_generator", report_gen_path)
                    report_generator = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(report_generator)
                    
                    report_generator.generate_custom_dossiers(
                        target_rank, selected_record, full_timeline_data, rotation_list,
                        grand_total_taxes, grand_total_health, grand_total_base_inflow, grand_total_conversions,
                        grand_total_brokerage, grand_total_roth, grand_total_401k
                    )
                except Exception as err:
                    print(f"[ERROR] Could not load or run report_generator.py: {err}")
            
        except (ValueError, KeyError, IndexError) as err:
            print(f"[ERROR] Selection visualization error: {err}")

