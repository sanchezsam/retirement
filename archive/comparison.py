# -*- coding: utf-8 -*-
"""
RETIREMENT RUNWAY MATRIX CONVERSION OPTIMIZER - STAGE 1
Algorithmically evaluates all 8 sequence permutations for a precise 4-year window.
"""
import os
import sys
import itertools

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    import config
    import run_new
except ImportError:
    print("[ERROR] Optimization script must be placed in the same folder as config.py and run_new.py")
    sys.exit(1)

print("[INFO] Initializing Exact 4-Year Fixed Permutation Scoring System...")
def generate_exact_four_year_variations():
    """ Explicitly builds all 8 permutations of 22% and 24% over a 4-year horizon window """
    bracket_options = 
    target_horizon_years = 4  # FORCES THE ENGINE TO USE EXACTLY YOUR 4-YEAR FRAMEWORK
    
    # Generate complete binary structural tracks (2^4 = 8 unique combinations)
    raw_permutations = list(itertools.product(bracket_options, repeat=target_horizon_years))
    target_variations = [list(p) for p in raw_permutations]
    
    print(f"[INFO] Target Horizon Window Size: {target_horizon_years} Years.")
    print(f"[INFO] Isolated exactly {len(target_variations)} unique sequence permutations.")
    
    optimization_scoreboard = []
    original_schedule = getattr(config, "DYNAMIC_BRACKET_SCHEDULE", [])
    return target_variations, optimization_scoreboard, original_schedule, target_horizon_years
def score_four_year_schedules(target_variations, optimization_scoreboard, original_schedule):
    """ Passes each of the 8 patterns through your full chronological math cascade model """
    for idx, rotation_list in enumerate(target_variations, start=1):
        config.DYNAMIC_BRACKET_SCHEDULE = rotation_list
        simulation_data = run_new.run_financial_simulation(target_bracket="schedule")
        
        years_to_deplete_401k = 44
        is_brokerage_broken = False
        is_roth_penalty_hit = False
        
        for year_row in simulation_data:
            if year_row["end_trad"] <= 0.01 and years_to_deplete_401k == 44:
                years_to_deplete_401k = year_row["year"]
            if year_row["end_brokerage"] <= 0.01 and year_row["wife_age"] < 61:
                is_brokerage_broken = True
            for m_data in year_row["monthly_ledger"]:
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
        total_lifetime_taxes = sum(year_row["total_taxes"] for year_row in simulation_data)
        ending_total_estate = final_year_record["end_brokerage"] + final_year_record["end_trad"] + final_year_record["end_roth"]
        
        optimization_scoreboard.append({
            "rotation_sequence": rotation_list,
            "years_to_convert": years_to_deplete_401k,
            "lifetime_taxes_paid": total_lifetime_taxes,
            "net_total_estate": ending_total_estate,
            "risk_profile": risk_sig
        })
        
    config.DYNAMIC_BRACKET_SCHEDULE = original_schedule
    optimization_scoreboard.sort(key=lambda x: x["net_total_estate"], reverse=True)
    return optimization_scoreboard
def print_ranked_horizon_results(scoreboard_data, window_size):
    """ Outputs the complete comparison grid for all 8 sequence variations side-by-side """
    print("\n" + "="*112)
    print(f"             RANKED SCOREBOARD: ALL {len(scoreboard_data)} STRATEGY VARIATIONS FOR THE EXACT {window_size}-YEAR HORIZON")
    print("="*112)
    print(f"{'Rank':<5} | {'Bracket Rotation Sequence Pattern':<28} | {'Years to Clear':<15} | {'Lifetime Taxes':<14} | {'Ending Net Estate':<18} | {'Liquidity Risk Code':<16}")
    print("-"*112)
    
    for rank_idx, record in enumerate(scoreboard_data, start=1):
        sequence_str = " -> ".join(f"{pct}%" for pct in record["rotation_sequence"])
        years_str = f"{record['years_to_convert']} Years"
        tax_str = f"${record['lifetime_taxes_paid']:,.2f}"
        estate_str = f"${record['net_total_estate']:,.2f}"
        risk_str = record["risk_profile"]
        
        print(f"{rank_idx:<5} | {sequence_str:<28} | {years_str:<15} | {tax_str:<14} | {estate_str:<18} | {risk_str:<16}")
    print("="*112)
    
    winning_rotation = scoreboard_data["rotation_sequence"]
    print(f"\n[OPTIMAL MATCHED RUNWAY]: Update your config.py array to match: {winning_rotation}\n")

if __name__ == "__main__":
    variants, scoreboard, cached_sched, window = generate_exact_four_year_variations()
    completed_scoreboard = score_four_year_schedules(variants, scoreboard, cached_sched)
    print_ranked_horizon_results(completed_scoreboard, window)

