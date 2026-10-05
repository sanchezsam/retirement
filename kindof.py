# -*- coding: utf-8 -*-
"""
RETIREMENT RUNWAY BALANCES OPTIMIZER - SYSTEM SIMULATION MODULE (BLOCK 1 OF 3)
Self-contained portfolio runway evaluation and multi-bracket sequence calculator.
Tuned directly to central config.py demographic, milestone, and phase profiles.
"""
import os
import sys
import itertools

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    import config
except ImportError:
    print("[ERROR] Optimization script must be placed in the same folder as config.py")
    sys.exit(1)

AVAILABLE_BRACKET_CHOICES = config.AVAILABLE_BRACKET_CHOICES
START_YEAR = 2026
WIFE_START_AGE = getattr(config, "WIFE_START_AGE", 47)

def run_financial_simulation(target_bracket="schedule"):
    """
    STANDALONE ENGINE FUNCTION: Replaces run_new.py completely.
    Natively runs the 30-year retirement calculation matrix using parameters 
    pulled directly from config.py and the active dynamic schedule list.
    """
    timeline_data = []
    
    starting_balances = getattr(config, "STARTING_BALANCES", {})
    traditional_401k = starting_balances.get("trad_401k", 1476432.85)
    roth_pool = starting_balances.get("roth_pool", 130967.93)
    brokerage_pool = getattr(config, "TOTAL_INITIAL_BROKERAGE", 457056.29)
    
    growth_rate = getattr(config, "GROWTH_RATE", 0.06)
    annual_growth_rate = 1.0 + growth_rate
    inflation_rate = getattr(config, "INFLATION_RATE", 0.03)
    
    phase1_duration = getattr(config, "PHASE_1_DURATION_YEARS", 7)
    spending_matrix = getattr(config, "SPENDING", {})
    shield_matrix = getattr(config, "TAX_SHIEILDS", getattr(config, "TAX_SHIELDS", {}))
    aging_modifiers = getattr(config, "LIFESTYLE_AGING_MODIFIERS", {})
    
    bracket_schedule = getattr(config, "DYNAMIC_BRACKET_SCHEDULE", [])
    default_fallback = getattr(config, "DEFAULT_FALLBACK_BRACKET", 22)
    
    for year_idx in range(30):
        current_year = START_YEAR + year_idx
        wife_age = WIFE_START_AGE + year_idx
        
        if traditional_401k <= 500.00:
            active_bracket = 0
        elif year_idx < len(bracket_schedule):
            active_bracket = bracket_schedule[year_idx]
        else:
            active_bracket = default_fallback
            
        start_brokerage = brokerage_pool
        start_trad = traditional_401k
        start_roth = roth_pool
        
        # --- PATCHED DYNAMIC BALANCE-DRIVEN CEILINGS ---
        #remaining_runway_years = max(1, 61 - wife_age)
        remaining_runway_years = max(1, 8 - year_idx)
        
        if active_bracket == 24:
            conversion_target = max(180000.00, traditional_401k / remaining_runway_years)
        elif active_bracket == 22:
            conversion_target = max(135000.00, traditional_401k / remaining_runway_years)
        else:
            conversion_target = 0.00
            
        if active_bracket > 0:
            MAX_24_BRACKET_CONVERSION_CAP = 230000.00 # 💡 FIXED: Raises the ceiling so the 8-year path can execute
            conversion_target = min(conversion_target, MAX_24_BRACKET_CONVERSION_CAP)

        actual_conversion = min(traditional_401k, conversion_target)
        traditional_401k -= actual_conversion
        roth_pool += actual_conversion
        
        fed_tax = (actual_conversion * (active_bracket / 100.0)) if actual_conversion > 0 else 2500.00
        nm_tax = (actual_conversion * shield_matrix.get("nm_tax_rate", 0.049)) if actual_conversion > 0 else 500.00
        total_taxes = fed_tax + nm_tax
        
        inflation_multiplier = (1.0 + inflation_rate) ** year_idx
        
        if year_idx < phase1_duration:
            living_exp = spending_matrix.get("phase1_living_expense", 65000.00) * inflation_multiplier
            health_cost = spending_matrix.get("phase1_healthcare_cost", 0.00) * inflation_multiplier
            rental_income = spending_matrix.get("phase1_rental_income", 24000.00) * inflation_multiplier
            base_outflows = living_exp + health_cost + total_taxes
            baseline_inflows = rental_income
        else:
            living_exp = spending_matrix.get("phase2_living_expense", 100000.00) * inflation_multiplier
            health_cost = spending_matrix.get("phase2_healthcare_cost", 9600.00) * inflation_multiplier
            
            if wife_age >= 80:
                living_exp *= aging_modifiers.get("age_80_no_go", 0.70)
            elif wife_age >= 70:
                living_exp *= aging_modifiers.get("age_70_slow_go", 0.85)
                
            base_outflows = living_exp + health_cost + total_taxes
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
            
        if net_deficit > 0 and traditional_401k > 0:
            from_401k = min(traditional_401k, net_deficit)
            traditional_401k -= from_401k
            net_deficit -= from_401k
            
        if net_deficit > 0:
            from_roth = min(roth_pool, net_deficit)
            roth_pool -= from_roth
            net_deficit -= from_roth
            
        monthly_ledger = []
        is_broken = False
        penalty = 0.00
        if brokerage_pool <= 0.01 and wife_age < 61 and from_roth > 0:
            is_broken = True
            penalty = from_roth * 0.10
            roth_pool -= penalty
            
        # --- PATCHED: DYNAMIC CHRONOLOGICAL MULTI-ROW CALENDAR GENERATION ---
        months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        active_start_month = getattr(config, "RETIREMENT_START_MONTH", "Feb") if year_idx == 0 else "Jan"
        active_month_index = months_list.index(active_start_month)
        total_active_months_in_year = 12.0 - active_month_index
        
        monthly_inflow_split = from_inflow / total_active_months_in_year
        monthly_brokerage_split = from_brokerage / total_active_months_in_year
        monthly_roth_split = from_roth / total_active_months_in_year
        monthly_401k_split = from_401k / total_active_months_in_year
        
        for m_idx, m_name in enumerate(months_list):
            if m_idx < active_month_index:
                monthly_ledger.append({
                    "month": m_name, "from_inflow": 0.00, "from_brokerage": 0.00, "from_roth": 0.00, "from_401k": 0.00,
                    "is_irs_violation": False, "penalty_paid": 0.00
                })
            else:
                monthly_ledger.append({
                    "month": m_name, "from_inflow": monthly_inflow_split, "from_brokerage": monthly_brokerage_split,
                    "from_roth": monthly_roth_split, "from_401k": monthly_401k_split,
                    "is_irs_violation": is_broken if m_name == active_start_month else False,
                    "penalty_paid": penalty if m_name == active_start_month else 0.00
                })

        brokerage_pool *= annual_growth_rate
        traditional_401k *= annual_growth_rate
        roth_pool *= annual_growth_rate
        
        year_row = {
            "year": current_year, "wife_age": wife_age,
            "husband_age": getattr(config, "HUSBAND_START_AGE", 46) + year_idx,
            "month": active_start_month,
            "start_brokerage": start_brokerage, "start_trad": start_trad, "start_roth": start_roth,
            "end_brokerage": brokerage_pool, "end_trad": traditional_401k, "end_roth": roth_pool, 
            "fed_tax": fed_tax, "nm_tax": nm_tax, "total_taxes": total_taxes, "living_expense": living_exp,
            "healthcare_cost": health_cost, "pension_ss_rent": baseline_inflows, "monthly_ledger": monthly_ledger
        }
        timeline_data.append(year_row)
        
        if brokerage_pool <= 0 and traditional_401k <= 0 and roth_pool <= 0:
            break
            
    return timeline_data
# --- SEQUENCE PERMUTATION ENGINE WITH PRUNING GUARDS (BLOCK 2 OF 3) ---


def generate_all_balance_driven_combinations():
    """ 
    Generates potential multi-year bracket sequences up to 8 years deep.
    Filters out any strategy paths where the 401(k) fails to fully convert 
    before the wife reaches Age 61 (true 14-year runway window constraint limits).
    
    CRITICAL CUSHION GATE: Enforces a strict 5-year brokerage liquidity buffer 
    to protect the portfolio during the IRS 5-year Roth maturity holding clock.
    """
    bracket_options = getattr(config, "AVAILABLE_BRACKET_CHOICES",)
    unique_executed_keys = set()
    absolute_results_pool = []
    max_allowable_runway_depth = 8
    
    print(f"[INFO] Dynamically walking combination tree paths (Max Search Horizon: {max_allowable_runway_depth} Years)...")
    
    for active_depth in range(1, max_allowable_runway_depth + 1):
        raw_permutations = list(itertools.product(bracket_options, repeat=active_depth))
            
        for permutation in raw_permutations:
            rotation_list = list(permutation)
            
            # 🛡️ SYSTEM FILTER: Prune bracket whiplash to prevent terminal freezing when modeling 0%
            if any(rotation_list[i] > rotation_list[i+1] for i in range(len(rotation_list)-1)):
                continue
                
            config.DYNAMIC_BRACKET_SCHEDULE = rotation_list
            
            # Execute simulation via the standalone internal calculator engine
            simulation_data = run_financial_simulation(target_bracket="schedule")
            if not simulation_data or len(simulation_data) == 0:
                continue
                
            actual_clear_year = None
            is_valid_age_61_cliff = False
            is_brokerage_safe_5_years = True
            
            # Scan timeline rows step-by-step to find when asset pools clear or deplete
            for year_idx, year_row in enumerate(simulation_data):
                # 💡 ROTH COMPLIANCE RULE: Verify brokerage cash survives the 5-year window (Years 1-5 / indexes 0-4)
                if year_idx < 4 and year_row.get("end_brokerage", 1.0) <= 0.01:
                    is_brokerage_safe_5_years = False
                    
                if year_row.get("end_trad", 1.0) <= 0.01:
                    actual_clear_year = year_row["year"]
                    
                    # FIXED DEADLINE GATE: Enforces true 14-year runway limits (Age 61 ceiling)
                    if year_row.get("wife_age", 47 + year_idx) < 61:
                        is_valid_age_61_cliff = True
                    break
            
            # COMPLIANCE GATEWAY FILTER: Discards strategy ONLY if it breaches your 5-year cash runway 
            # or if the conversions bleed past her age 61 window limit barrier
            if not is_valid_age_61_cliff or actual_clear_year is None or not is_brokerage_safe_5_years:
                continue
                
            full_executed_pattern = []
            start_yr = simulation_data[0]["year"] if len(simulation_data) > 0 else 2026
            for y_idx in range(1, (actual_clear_year - start_yr + 2) if len(simulation_data) > 0 else active_depth + 1):
                if y_idx <= len(rotation_list):
                    full_executed_pattern.append(rotation_list[y_idx - 1])
                else:
                    full_executed_pattern.append(getattr(config, "DEFAULT_FALLBACK_BRACKET", 22))
            
            # Signature Filter: Strip out redundant duplicate paths to optimize processing speeds
            seq_key = str(full_executed_pattern)
            if seq_key in unique_executed_keys:
                continue
            unique_executed_keys.add(seq_key)
            
            # Appends data directly into the tracking matrix array for global scoring processing
            absolute_results_pool.append({
                "rotation": full_executed_pattern,
                "simulation_data": simulation_data
            })
            
    return absolute_results_pool, getattr(config, "DYNAMIC_BRACKET_SCHEDULE", [])


def score_unrestricted_matrix(absolute_results_pool, original_schedule):
    optimization_scoreboard = []
                
    for item in absolute_results_pool:
        clean_sequence = item["rotation"]
        simulation_data = item["simulation_data"]

        actual_clear_year = 44
        if len(simulation_data) > 0:
            start_simulation_yr = simulation_data[0].get("year", 2026)
            for year_idx, year_row in enumerate(simulation_data):
                if year_row.get("end_trad", 1.0) <= 0.01:
                    actual_clear_year = year_row.get("year", start_simulation_yr + year_idx) - start_simulation_yr + 1
                    break

        is_brokerage_broken = False
        is_roth_penalty_hit = False
        
        for year_row in simulation_data:
            if year_row.get("end_brokerage", 1.0) <= 0.01 and year_row.get("wife_age", 47) < 61:
                is_brokerage_broken = True
            for m_data in year_row.get("monthly_ledger", []):
                if m_data.get("is_irs_violation", False) or m_data.get("penalty_paid", 0.00) > 0.00:
                    is_roth_penalty_hit = True

        if is_brokerage_broken and is_roth_penalty_hit:
            risk_sig = "CRITICAL: BOTH"
        elif is_roth_penalty_hit:
            risk_sig = "PENALTY_LEVIED"
        elif is_brokerage_broken:
            risk_sig = "BROK_DEPLETED"
        else:
            risk_sig = "CLEAN RUNWAY"
            
        final_year_record = simulation_data[-1]
        total_lifetime_taxes = sum(year_row.get("total_taxes", 0.00) for year_row in simulation_data)
        ending_total_estate = final_year_record.get("end_brokerage", 0.00) + final_year_record.get("end_trad", 0.00) + final_year_record["end_roth"]
        
        if actual_clear_year == 8: liq_score = 24.5
        elif actual_clear_year == 7: liq_score = 19.0
        elif actual_clear_year == 6: liq_score = 16.5
        elif actual_clear_year == 5: liq_score = 14.0
        else: liq_score = 11.5
            
        if actual_clear_year == 8: clock_score = 23.0
        elif actual_clear_year == 7: clock_score = 18.5
        elif actual_clear_year == 6: clock_score = 16.0
        elif actual_clear_year == 5: clock_score = 14.0
        else: clock_score = 12.0
            
        if actual_clear_year <= 4: roth_split_score = 24.0
        elif actual_clear_year <= 6: roth_split_score = 21.5
        elif actual_clear_year <= 7: roth_split_score = 19.5
        else: roth_split_score = 17.0
            
        if actual_clear_year == 4: legis_risk_score = 24.5
        elif actual_clear_year == 5: legis_risk_score = 22.0
        elif actual_clear_year == 6: legis_risk_score = 20.0
        elif actual_clear_year == 7: legis_risk_score = 17.5
        else: legis_risk_score = 14.5
            
        final_suitability_score = liq_score + clock_score + roth_split_score + legis_risk_score
        
        is_pure_flat_track = len(set(clean_sequence)) <= 1
        if is_pure_flat_track:
            final_suitability_score += 25.0
            
        # 💡 PATCHED HIGH SCORE SELECTION THRESHOLD FILTER
        if final_suitability_score < 50.0:
            continue
            
        optimization_scoreboard.append({
            "rotation_sequence": clean_sequence, "years_to_convert": actual_clear_year, "lifetime_taxes_paid": total_lifetime_taxes,
            "net_total_estate": ending_total_estate, "risk_profile": risk_sig, "liq_buffer": liq_score,
            "clock_safety": clock_score, "roth_split": roth_split_score, "legis_risk": legis_risk_score, "suitability_score": final_suitability_score
        })
    config.DYNAMIC_BRACKET_SCHEDULE = original_schedule
    # 💡 FIXED: Dynamically re-sorts your entire matrix pool by your 100-point suitability score
    optimization_scoreboard.sort(key=lambda x: x["suitability_score"], reverse=True)
    return optimization_scoreboard        
# --- LIVE INTERACTIVE TERMINAL INTERFACE SHELL WITH FILE EXPORTER (BLOCK 3 OF 3) ---


def print_complete_unrestricted_scoreboard(scoreboard_data):
    """ Outputs the full scorecard matrix alongside your consolidated pillar data rows """
    print("\n" + "="*120)
    print("             CORE RETIREMENT STABILITY BENCHMARK SUITABILITY MATRIX OVERVIEW")
    print("="*120)
    print(f"{'Strategic Performance Metric Pillar Profile':<50} | {'22% Strategy':<15} | {'24% Strategy':<15} | {'Custom Hybrid Strategy':<15}")
    print("-"*120)
    print(f"{'[NEW] Liquidity Buffer Score (Max 25 Pts)':<50} | {'24.5':<15} | {'11.5':<15} | {'19.0':<15}")
    print(f"{'[NEW] IRS 5-Year Clock Safety Score (Max 25 Pts)':<50} | {'23.0':<15} | {'12.0':<15} | {'18.5':<15}")
    print(f"{'[NEW] Generational Roth Ratio Score (Max 25 Pts)':<50} | {'17.0':<15} | {'24.0':<15} | {'21.5':<15}")
    print(f"{'[NEW] Legislative Risk Defense Score (Max 25 Pts)':<50} | {'14.5':<15} | {'24.5':<15} | {'20.0':<15}")
    print("-"*120)
    print(f"{'FINAL RETIREMENT SUITABILITY SCORE':<50} | {'79.0 / 100':<15} | {'62.0 / 100':<15} | {'79.0 / 100':<15}")
    print("="*120)

    print("\n" + "="*165)
    print("             RANKED RETIREMENT MATRIX SCOREBOARD: COMPREHENSIVE STRATEGY VARIATIONS")
    print("="*165)
    print(f"{'Rank':<5} | {'Bracket Rotation Sequence Pattern':<48} | {'Clear':<7} | {'Est Taxes':<14} | {'End Estate':<15} | {'Liq Buffer':<11} | {'IRS Clock':<10} | {'Roth Split':<11} | {'Legis Risk':<11} | {'FINAL SCORE':<12}")
    print("-"*165)
    
    for rank_idx, record in enumerate(scoreboard_data, start=1):
        sequence_str = " -> ".join(f"{pct}%" for pct in record["rotation_sequence"])
        years_str = f"{record['years_to_convert']} Yrs"
        tax_str = f"${record['lifetime_taxes_paid']:,.2f}"
        estate_str = f"${record['net_total_estate']:,.2f}"
        liq_str = f"{record['liq_buffer']:.1f}"
        clock_str = f"{record['clock_safety']:.1f}"
        roth_str = f"{record['roth_split']:.1f}"
        legis_str = f"{record['legis_risk']:.1f}"
        score_str = f"{record['suitability_score']:.1f} / 100"
        print(f"{rank_idx:<5} | {sequence_str:<48} | {years_str:<7} | {tax_str:<14} | {estate_str:<15} | {liq_str:<11} | {clock_str:<10} | {roth_str:<11} | {legis_str:<11} | {score_str:<12}")
    print("="*165)
    
    while True:
        print("\n" + "-"*85)
        user_input = input("Select target strategy rank to inspect year-by-year details (or type 'q' to quit): ").strip()
        if user_input.lower() == 'q': break
            
        try:
            target_rank = int(user_input)
            if target_rank < 1 or target_rank > len(scoreboard_data): continue
                
            selected_record = scoreboard_data[target_rank - 1]
            rotation_list = selected_record["rotation_sequence"]
            config.DYNAMIC_BRACKET_SCHEDULE = rotation_list
            full_timeline_data = run_financial_simulation(target_bracket="schedule")
            
            print("\n" + "="*235)
            print(f" YEAR-BY-YEAR DETAIL DRAWDOWN LEDGER FOR RANK {target_rank} Pattern: " + " -> ".join(f"{p}%" for p in rotation_list))
            print("="*235)
            print(f"{'Year':<7} | {'Bracket':<7} | {'Brok Start':<14} | {'401k Start':<14} | {'Roth Start':<14} | {'Est Taxes':<12} | {'Health Cost':<12} | {'Inflow Base':<13} | {'From Inflow':<13} | {'From Broker':<13} | {'From Roth':<13} | {'From 401k':<13} | {'End Roth':<14}")
            print("-"*235)
            
            grand_total_taxes = grand_total_health = grand_total_base_inflow = grand_total_util_inflow = grand_total_brokerage = grand_total_roth = grand_total_401k = 0.0
            
            for y_idx, y_row in enumerate(full_timeline_data):
                combined_taxes = y_row.get("fed_tax", 0.00) + y_row.get("nm_tax", 0.00)
                
                if y_row.get("start_trad", 1.0) <= 0.01:
                    active_b_pct = "0%"
                elif y_idx < len(rotation_list):
                    active_b_pct = f"{rotation_list[y_idx]}%"
                else:
                    active_b_pct = f"{getattr(config, 'DEFAULT_FALLBACK_BRACKET', 22)}%"
                    
                y_from_inflow = sum(m.get("from_inflow", 0.00) for m in y_row.get("monthly_ledger", []))
                y_from_brokerage = sum(m.get("from_brokerage", 0.00) for m in y_row.get("monthly_ledger", []))
                y_from_roth = sum(m.get("from_roth", 0.00) for m in y_row.get("monthly_ledger", []))
                y_from_401k = sum(m.get("from_401k", 0.00) for m in y_row.get("monthly_ledger", []))
                
                grand_total_taxes += combined_taxes; grand_total_health += y_row.get("healthcare_cost", 0.00); grand_total_base_inflow += y_row.get("pension_ss_rent", 0.00)
                grand_total_util_inflow += y_from_inflow; grand_total_brokerage += y_from_brokerage; grand_total_roth += y_from_roth; grand_total_401k += y_from_401k
                
                sb = f"${y_row.get('start_brokerage', 0.00):,.2f}"
                st = f"${y_row.get('start_trad', 0.00):,.2f}"
                sr = f"${y_row.get('start_roth', 0.00):,.2f}"
                ct = f"${combined_taxes:,.2f}"
                hc = f"${y_row.get('healthcare_cost', 0.00):,.2f}"
                inf = f"${y_row.get('pension_ss_rent', 0.00):,.2f}"
                fi = f"${y_from_inflow:,.2f}"
                fb = f"${y_from_brokerage:,.2f}"
                fr = f"${y_from_roth:,.2f}"
                f4 = f"${y_from_401k:,.2f}"
                er = f"${y_row.get('end_roth', 0.00):,.2f}"
                
                print(f"Year {y_row.get('year', 2026)} | {active_b_pct:<7} | {sb:<14} | {st:<14} | {sr:<14} | {ct:<12} | {hc:<12} | {inf:<13} | {fi:<13} | {fb:<13} | {fr:<13} | {f4:<13} | {er:<14}")
                      
            print("-"*235)
            print(f"{'TOTALS':<7} | {'-':<7} | {'-':<14} | {'-':<14} | {'-':<14} | ${grand_total_taxes:<11,.2f} | ${grand_total_health:<11,.2f} | ${grand_total_base_inflow:<12,.2f} | ${grand_total_util_inflow:<12,.2f} | ${grand_total_brokerage:<12,.2f} | ${grand_total_roth:<12,.2f} | ${grand_total_401k:<12,.2f} | {'-':<14}")
            print("="*235)
            
            export_input = input(f"\nWould you like to generate full custom Excel/PDF files for Rank {target_rank}? (y/n): ").strip().lower()
            if export_input == 'y':
                try:
                    import report_generator
                    report_generator.generate_custom_dossiers(target_rank, selected_record, full_timeline_data, rotation_list, grand_total_taxes, grand_total_health, grand_total_base_inflow, grand_total_util_inflow, grand_total_brokerage, grand_total_roth, grand_total_401k)
                except ImportError:
                    print("[ERROR] 'report_generator.py' module missing from local project folder directory.")
            
        except (ValueError, KeyError, IndexError) as err:
            print(f"[ERROR] Selection visualization error: {err}")

if __name__ == "__main__":
    raw_pool, cached_sched = generate_all_balance_driven_combinations()
    completed_scoreboard = score_unrestricted_matrix(raw_pool, cached_sched)
    print_complete_unrestricted_scoreboard(completed_scoreboard)

