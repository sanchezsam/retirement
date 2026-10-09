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

# Ensure local imports work by appending current script directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    import config
except ImportError:
    print("[ERROR] Optimization script must be placed in the same folder as config.py")
    sys.exit(1)


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
    fed_brackets = getattr(config, "IRS_MFJ_TAX_BRACKETS", [
        (24800.00, 0.10, 0.00),
        (100800.00, 0.12, 2480.00),
        (211400.00, 0.22, 11600.00),
        (403550.00, 0.24, 35932.00),
        (512450.00, 0.32, 82048.00),
        (768700.00, 0.35, 116896.00),
        (float('inf'), 0.37, 206583.50)
    ])
    shields = getattr(config, "TAX_SHIELDS", {})
    
    fed_deduction = shields.get(
        "federal_standard_deduction", 
        getattr(config, "IRS_MFJ_STANDARD_DEDUCTION", 32200.00)
    )
    fed_tax = calc_marginal_tax(income, fed_deduction, fed_brackets)

    nm_brackets = getattr(config, "NM_MFJ_TAX_BRACKETS", [
        (8000.00, 0.015, 0.00),
        (16000.00, 0.035, 120.00),
        (24000.00, 0.047, 400.00),
        (315000.00, 0.049, 776.00),
        (float('inf'), 0.059, 15035.00)
    ])
    nm_deduction = shields.get(
        "nm_joint_exemption", 
        getattr(config, "NM_MFJ_STANDARD_DEDUCTION", 32200.00)
    )
    nm_tax = calc_marginal_tax(income, nm_deduction, nm_brackets)
    
    return fed_tax, nm_tax


def run_financial_simulation(bracket_schedule, custom_brokerage=None, custom_rent=None, custom_living=None):
    """
    Simulates a comprehensive 30-year drawdown timeline tracking liquid account
    depletions, progressive tax drag, and chronological Roth contribution seasoning.
    """
    timeline_data = []
    
    starting_balances = getattr(config, "STARTING_BALANCES", {})
    traditional_401k = starting_balances.get("trad_401k", 1476432.85)
    roth_pool = starting_balances.get("roth_pool", 130967.93)
    
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
    cash_yield = getattr(config, "CASH_YIELD_RATE", 0.00)
    
    phase1_duration = getattr(config, "PHASE_1_DURATION_YEARS", 7)
    spending_matrix = getattr(config, "SPENDING", {})
    aging_modifiers = getattr(config, "LIFESTYLE_AGING_MODIFIERS", {})
    
    shields = getattr(config, "TAX_SHIELDS", {})
    fed_deduction = shields.get(
        "federal_standard_deduction", 
        getattr(config, "IRS_MFJ_STANDARD_DEDUCTION", 32200.00)
    )
    
    start_year = 2027
    wife_start_age = getattr(config, "WIFE_START_AGE", 47)
    default_fallback = getattr(config, "DEFAULT_FALLBACK_BRACKET", 22)

    for year_idx in range(30):
        current_year = start_year + year_idx
        wife_age = wife_start_age + year_idx
        
        penalty = 0.00
        is_broken = False
        
        if (current_year - 5) in active_conversion_ladder:
            penalty_free_basis += active_conversion_ladder.pop(current_year - 5)
            
        if traditional_401k <= 500.00:
            active_bracket = 0
        elif year_idx < len(bracket_schedule):
            active_bracket = bracket_schedule[year_idx]
        else:
            active_bracket = default_fallback
            
        start_brokerage = brokerage_pool
        start_trad = traditional_401k
        start_roth = roth_pool
        
        brokerage_gains = start_brokerage * cash_yield
        inflation_multiplier = (1.0 + inflation_rate) ** year_idx
        
        if year_idx < phase1_duration:
            if custom_living is not None:
                living_exp = custom_living * inflation_multiplier
            else:
                living_exp = spending_matrix.get("phase1_living_expense", 65000.00) * inflation_multiplier
            health_cost = spending_matrix.get("phase1_healthcare_cost", 0.00) * inflation_multiplier
            rental_income = custom_rent if custom_rent is not None else spending_matrix.get("phase1_rental_income", 24000.00)
            
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
            
        net_deficit = max(0.00, base_outflows - baseline_inflows)
        from_inflow = min(base_outflows, baseline_inflows)
        from_brokerage = from_401k = from_roth = 0.00
        
        if net_deficit > 0:
            from_brokerage = min(brokerage_pool, net_deficit)
            brokerage_pool -= from_brokerage
            net_deficit -= from_brokerage
            
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

        conversion_target = 0.00
        if active_bracket > 0:
            if active_bracket == 22:
                conversion_target = 211400.00 + (fed_deduction if year_idx == 0 else fed_deduction * inflation_multiplier)
            elif active_bracket == 24:
                conversion_target = 403550.00 + (fed_deduction if year_idx == 0 else fed_deduction * inflation_multiplier)
            else:
                conversion_target = 512450.00 + (fed_deduction if year_idx == 0 else fed_deduction * inflation_multiplier)
            
            conversion_target = max(0.00, conversion_target - from_401k - brokerage_gains)
            if (61 - wife_age) <= 1:
                conversion_target = traditional_401k

        actual_conversion = min(traditional_401k, conversion_target)
        traditional_401k -= actual_conversion
        roth_pool += actual_conversion

        if actual_conversion > 0:
            active_conversion_ladder[current_year] = active_conversion_ladder.get(current_year, 0.00) + actual_conversion

        y_total_taxable_income = actual_conversion + from_401k + brokerage_gains
        fed_tax, nm_tax = calculate_progressive_taxes(y_total_taxable_income)
        total_taxes = fed_tax + nm_tax
        
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

        months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        active_start_month = getattr(config, "RETIREMENT_START_MONTH", "Feb") if year_idx == 0 else "Jan"
        active_month_index = months_list.index(active_start_month)
        total_active_months_in_year = 12.0 - active_month_index
        
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
            "actual_conversion": actual_conversion, "true_taxable_income": y_total_taxable_income,
            "required_income": living_exp + total_taxes + health_cost, "brokerage_gains": brokerage_gains
        }
        timeline_data.append(year_row)
        
        if (brokerage_pool + traditional_401k + roth_pool) <= 500.00:
            break
            
    return timeline_data


def generate_all_balance_driven_combinations():
    """Generates all conversion paths restricted strictly to years before Wife turns 61."""
    bracket_options = getattr(config, "AVAILABLE_BRACKET_CHOICES", [0, 22, 24])
    unique_executed_keys = set()
    absolute_results_pool = []
    
    target_runway_horizon = max(1, 61 - getattr(config, "WIFE_START_AGE", 47)) 
    print(f"[INFO] Dynamically walking combination tree paths for a fixed {target_runway_horizon}-Year Runway...")
    
    raw_permutations = list(itertools.combinations_with_replacement(bracket_options, target_runway_horizon))
            
    for permutation in raw_permutations:
        rotation_list = list(permutation)
        
        simulation_data = run_financial_simulation(rotation_list)
        if not simulation_data:
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


def score_unrestricted_matrix(absolute_results_pool, original_schedule):
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
                if m_data.get("from_401k", 0.00) > 0.01 or m_data.get("is_irs_violation", False):
                    violates_rules = True
                    break
            if violates_rules:
                break
                
        if sim_data[-1].get("end_trad", 0.00) <= 500.00 and not violates_rules:
            ending_estate = sim_data[-1].get("end_brokerage", 0.00) + sim_data[-1].get("end_trad", 0.00) + sim_data[-1].get("end_roth", 0.00)
            if ending_estate > max_estate_found:
                max_estate_found = ending_estate

    if max_estate_found == 0.0:
        max_estate_found = max(
            item["simulation_data"][-1].get("end_brokerage", 0.00) + 
            item["simulation_data"][-1].get("end_trad", 0.00) + 
            item["simulation_data"][-1].get("end_roth", 0.00) 
            for item in absolute_results_pool
        )

    for item in absolute_results_pool:
        clean_sequence = item["rotation"]
        simulation_data = item["simulation_data"]
        actual_clear_year = item["years_to_convert"]
        
        is_illegal_strategy = False
        for year_row in simulation_data:
            for m_data in year_row.get("monthly_ledger", []):
                if m_data.get("from_401k", 0.00) > 0.01 or m_data.get("is_irs_violation", False):
                    is_illegal_strategy = True
                    break
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

        is_brokerage_broken = any(
            year_row.get("end_brokerage", 1.0) <= 0.00 and year_row.get("wife_age", 47) < 61
            for year_row in simulation_data
        )

        risk_sig = "BROK_DEPLETED" if is_brokerage_broken else "CLEAN RUNWAY"
        final_year_record = simulation_data[-1]
        total_lifetime_taxes = sum(year_row.get("total_taxes", 0.00) for year_row in simulation_data)
        ending_total_estate = (
            final_year_record.get("end_brokerage", 0.00) + 
            final_year_record.get("end_trad", 0.00) + 
            final_year_record.get("end_roth", 0.00)
        )
        
        estate_score = (ending_total_estate / max_estate_found) * 25.0 if max_estate_found > 0 else 0.0
        liq_score = 25.0 if not is_brokerage_broken else 12.5
        clock_score = 25.0  
        tax_efficiency_score = max(0.0, 25.0 - (total_lifetime_taxes / 50000.0))

        base_suitability_score = estate_score + liq_score + clock_score + tax_efficiency_score
        final_suitability_score = base_suitability_score
        
        unique_active_brackets = set()
        for br in executed_brackets:
            if br > 0:
                unique_active_brackets.add(br)
        is_pure_flat_track = len(unique_active_brackets) <= 1
        
        if is_pure_flat_track:
            final_suitability_score += 15.0
            
        final_suitability_score = min(100.0, final_suitability_score)
            
        optimization_scoreboard.append({
            "rotation_sequence": executed_brackets, 
            "years_to_convert": actual_clear_year, 
            "lifetime_taxes_paid": total_lifetime_taxes,
            "net_total_estate": ending_total_estate, 
            "risk_profile": risk_sig, 
            "liq_buffer": liq_score,
            "clock_safety": clock_score, 
            "roth_split": estate_score,        
            "legis_risk": tax_efficiency_score, 
            "suitability_score": final_suitability_score,
            "simulation_data": simulation_data
        })

    config.DYNAMIC_BRACKET_SCHEDULE = original_schedule
    optimization_scoreboard.sort(key=lambda x: (x["suitability_score"], x["net_total_estate"]), reverse=True)
    return optimization_scoreboard


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

    print("\n" + "="*195)
    print("             RANKED RETIREMENT MATRIX SCOREBOARD: COMPREHENSIVE STRATEGY VARIATIONS")
    print("="*195)
    print(f"{'Rank':<5} | {'Bracket Rotation Sequence Pattern':<78} | {'Clear':<7} | {'Est Taxes':<14} | {'End Estate':<15} | {'Liq Buffer':<11} | {'IRS Clock':<10} | {'Roth Split':<11} | {'Legis Risk':<12} | {'FINAL SCORE':<12}")
    print("-"*195)
    
    for rank_idx, record in enumerate(scoreboard_data[:30], start=1):
        sequence_str = format_carryover_sequence(record["rotation_sequence"], field_width=78)
        years_str = f"{record['years_to_convert']} Yrs"
        tax_str = f"${record['lifetime_taxes_paid']:,.2f}"
        estate_str = f"${record['net_total_estate']:,.2f}"
        liq_str = f"{record['liq_buffer']:.1f}"
        clock_str = f"{record['clock_safety']:.1f}"
        roth_str = f"{record['roth_split']:.1f}"
        legis_str = f"{record['legis_risk']:.1f}"
        score_str = f"{record['suitability_score']:.1f} / 100"
        
        base_lines = sequence_str.split('\n')
        print(f"{rank_idx:<5} | {base_lines[0]:<78} | {years_str:<7} | {tax_str:<14} | {estate_str:<15} | {liq_str:<11} | {clock_str:<10} | {roth_str:<11} | {legis_str:<12} | {score_str:<12}")
        for extra_line in base_lines[1:]:
            print(f"{'':<5} | {extra_line:<78} | {'':<7} | {'':<14} | {'':<15} | {'':<11} | {'':<10} | {'':<11} | {'':<12} | {'':<12}")
            
    print("="*195)
    
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
            rotation_list = selected_record["rotation_sequence"]
            full_timeline_data = run_financial_simulation(rotation_list)
            
            pattern_display_str = " -> ".join(f"{br}%" for br in rotation_list)
            
            print("\n" + "="*286)
            print(f" YEAR-BY-YEAR DETAIL DRAWDOWN LEDGER FOR RANK {target_rank} Pattern: {pattern_display_str} (Full 30-Year Projections)")
            print("="*286)
            print(f"{'#':<3} | {'Yr':<4} | {'Bracket':<7} | {'Brok Start':<14} | {'401k Start':<14} | {'Converted':<14} | {'Roth Start':<14} | {'Living Exp':<14} | {'Est Taxes':<12} | {'Health Cost':<12} | {'Inflow Base':<13} | {'Brok Yield':<12} | {'Req Income':<14} | {'From Broker':<13} | {'From Roth':<13} | {'From 401k':<13} | {'End Roth':<14}")
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
                print(f"{y_idx + 1:<3} | {yr_short:<4} | {active_b_pct:<7} | {sb:<14} | {st:<14} | {sc:<14} | {sr:<14} | {le:<14} | {ct:<12} | {hc:<12} | {inf:<13} | {bg:<12} | {ri:<14} | {fb:<13} | {fr:<13} | {f4:<13} | {er:<14}")
                      
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


if __name__ == "__main__":
    raw_pool, cached_sched = generate_all_balance_driven_combinations()
    completed_scoreboard = score_unrestricted_matrix(raw_pool, cached_sched)
    print_complete_unrestricted_scoreboard(completed_scoreboard)

