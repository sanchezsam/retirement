# -*- coding: utf-8 -*-
"""
MASTER RETIREMENT ROADMAP RUNWAY DRIVER ENGINE - SYSTEMWIDE PRODUCTION HUB
Natively executes your live optimize_rotations.py and optimize_hybrid.py files side-by-side.
Generates the core milestone matrix, year-by-year summary, and a detailed stacked row audit layout.
"""
import os
import sys

# Append local script directory path to guarantee seamless cross-imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    import config
    # CORE SYNC FIX: Aliases the files perfectly to align strategy labels with actual math logic
    import optimize_hybrid as optimize_rotations  # Hybrid file holds your capped SEPP logic
    import optimize_rotations as optimize_hybrid  # Rotations file holds your cleanout logic
except ImportError as err:
    print(f"[CRITICAL ERROR] Master Driver failed to resolve script dependencies: {err}")
    print("Please ensure this file is saved inside the same folder as config.py, optimize_rotations.py, and optimize_hybrid.py.")
    sys.exit(1)


def capture_strategy_snapshots(timeline_data):
    """
    Parses a full 44-year timeline and extracts account asset snapshots at landmark milestones.
    Synchronized precisely with the start-of-year baseline metrics returned by your files.
    """
    target_milestones = [46, 51, 60, 65, 75]
    snapshots = {}
    
    for row in timeline_data:
        h_age = row.get("husband_age")
        if h_age in target_milestones:
            snapshots[h_age] = {
                "brok": row.get("start_brokerage", 0.00),
                "trad": row.get("start_trad", 0.00),
                "roth": row.get("start_roth", 0.00),
                "tax": row.get("total_taxes", 0.00)
            }
            
    # Automatically extracts your true ending legacy values from the final calculated row
    if timeline_data:
        final_row = timeline_data[-1]
        snapshots[90] = {
            "brok": final_row.get("end_brokerage", 0.00),
            "trad": final_row.get("end_trad", 0.00),
            "roth": final_row.get("end_roth", 0.00),
            "tax": final_row.get("total_taxes", 0.00)
        }
        
    return snapshots
def execute_master_comparison():
    print("[INFO] Initializing Master Retirement Driver Engine...")
    print(f"[INFO] Syncing Central Parameters: Growth={config.GROWTH_RATE*100}%, Inflation={config.INFLATION_RATE*100}%")
    
    # 1. Natively execute Top Strategy Path from Level Capped Model
    #rotations_schedule = getattr(config, "DYNAMIC_BRACKET_SCHEDULE", [12, 12, 12, 12, 12])
    # 1. Walk dynamic Cartesian trees to capture fresh scored outcomes

    # 1. Walk dynamic Cartesian trees to capture fresh scored outcomes
    raw_rot_pool, _ = optimize_rotations.generate_all_balance_driven_combinations()
    
    # 2. Extract the sorted scoreboard arrays natively 
    # FIXED: Removed the secondary 'None' argument to match function signature perfectly
    sorted_rot = optimize_rotations.score_unrestricted_matrix(raw_rot_pool)
    
    # 3. Pull the conformed Rank 1 schedule and simulation data straight from keys
    top_record = sorted_rot[0]
    rotations_schedule = top_record["rotation"]
    rotations_timeline = top_record["simulation_data"]


    #rotations_timeline = optimize_rotations.run_financial_simulation(rotations_schedule)
    rotations_snapshots = capture_strategy_snapshots(rotations_timeline)
    rotations_lifetime_tax = sum(y.get("total_taxes", 0.00) for y in rotations_timeline)
    
    # 2. Natively execute Top Strategy Path from Aggressive Cleanout Model
    hybrid_schedule = [24, 24, 24, 24, 24]
    hybrid_timeline = optimize_hybrid.run_financial_simulation(hybrid_schedule)
    hybrid_snapshots = capture_strategy_snapshots(hybrid_timeline)
    hybrid_lifetime_tax = sum(y.get("total_taxes", 0.00) for y in hybrid_timeline)
    
    final_age = 90
    r_final = rotations_snapshots.get(final_age, {"brok": 0, "trad": 0, "roth": 0})
    h_final = hybrid_snapshots.get(final_age, {"brok": 0, "trad": 0, "roth": 0})
    
    total_estate_rotations = r_final["brok"] + r_final["trad"] + r_final["roth"]
    total_estate_hybrid = h_final["brok"] + h_final["trad"] + h_final["roth"]
    
    # =========================================================================
    # DISPLAY INDEX 1: SYSTEMWIDE CORE MILESTONE SUMMARY MATRIX
    # =========================================================================
    print("\n" + "="*145)
    print(f"{'MASTER DRIVER RETIREMENT PHILOSOPHY COMPARISON MATRIX (SYNCHRONIZED REALITY)':^145}")
    print("="*145)
    print(f" {'Chronological Lifecycle Checkpoint Profile':<45} | {' LEVEL CAPPED ROTATIONS STRATEGY':^45} | {' AGGRESSIVE FULL CLEAN-OUT STRATEGY':^45} |")
    print("-"*145)
    
    milestone_titles = [
        (46, "Initial Asset Base Allocation (Year 1)"),
        (51, "The Low-Income Conversion Phase (Year 6)"),
        (60, "The Lean Pre-Stream Cash Valley Milestone"),
        (65, "Fixed Pension & SS Stream Infusion Influx"),
        (75, "Mandatory Statutory IRS RMD Boundary Edge"),
        (90, "Terminal Legacy Estate Portfolio Value")
    ]
    
    for age, title in milestone_titles:
        r_snap = rotations_snapshots.get(age, {"brok": 0, "trad": 0, "roth": 0})
        h_snap = hybrid_snapshots.get(age, {"brok": 0, "trad": 0, "roth": 0})
        
        r_sub = r_snap["brok"] + r_snap["trad"] + r_snap["roth"]
        h_sub = h_snap["brok"] + h_snap["trad"] + h_snap["roth"]
        
        print(f" Husband Age {age} - {title:<45} | {'':<45} | {'':<45} |")
        print(f"   ├── Taxable Brokerage Cash Cushion           | ${r_snap['brok']:<42,.2f} | ${h_snap['brok']:<42,.2f} |")
        print(f"   ├── Traditional Pre-Tax 401(k) Asset Vault   | ${r_snap['trad']:<42,.2f} | ${h_snap['trad']:<42,.2f} |")
        print(f"   ├── Tax-Free Combined Roth Accumulation Vault| ${r_snap['roth']:<42,.2f} | ${h_snap['roth']:<42,.2f} |")
        print(f"   └── PORTFOLIO WEALTH ACCUMULATION SUB-TOTAL  | \033[1m${r_sub:<41,.2f}\033[0m | \033[1m${h_sub:<41,.2f}\033[0m |")
        print(f" {'-':<55} | {'-':<45} | {'-':<45} |")
        
    print("="*145)
    print(f" {'AGGREGATE TOTAL LIFETIME TAX LIABILITIES PAID':<55} | ${rotations_lifetime_tax:<42,.2f} | ${hybrid_lifetime_tax:<42,.2f} |")
    print("="*145)

    # =========================================================================
    # DISPLAY INDEX 2: COMPLETE YEAR-BY-YEAR CHRONOLOGICAL TRAJECTORY LEDGER
    # =========================================================================
    print("\n" + "="*145)
    print(f"{'COMPLETE CHRONOLOGICAL LIFECYCLE WEALTH TRAJECTORY LEDGER GAPS':^145}")
    print("="*145)
    print(f" {'Yr':<4} | {'H_Age':<5} | {' LEVEL CAPPED ROTATIONS MODEL VALUE':<34} | {' AGGRESSIVE FULL CLEAN-OUT VALUE':<34} | {' Net Annual Variance':<22} | {'Active Leader':<17} |")
    print("-"*145)
    
    max_years = min(len(rotations_timeline), len(hybrid_timeline))
    
    for idx in range(max_years):
        r_row = rotations_timeline[idx]
        h_row = hybrid_timeline[idx]
        
        h_age = r_row.get("husband_age", 46 + idx)
        yr = r_row.get("year", 2027 + idx)
        
        r_total = r_row.get("start_brokerage", 0.0) + r_row.get("start_trad", 0.0) + r_row.get("start_roth", 0.0)
        h_total = h_row.get("start_brokerage", 0.0) + h_row.get("start_trad", 0.0) + h_row.get("start_roth", 0.0)
        
        if h_age == 90 or idx == max_years - 1:
            r_total = r_row.get("end_brokerage", 0.0) + r_row.get("end_trad", 0.0) + r_row.get("end_roth", 0.0)
            h_total = h_row.get("end_brokerage", 0.0) + h_row.get("end_trad", 0.0) + h_row.get("end_roth", 0.0)
            
        variance = abs(r_total - h_total)
        
        if idx == 0:
            leader = "Symmetrical Match"
        elif r_total > h_total:
            leader = "Level Capped Leads"
        else:
            leader = "Clean-Out Leads"
            
        print(f" {str(yr)[-2:]:<4} | {h_age:<5} | ${r_total:<32,.2f} | ${h_total:<32,.2f} | ${variance:<20,.2f} | {leader:<17} |")
    print("="*145)

   
    # =========================================================================
    # DISPLAY INDEX 3: WIDESCREEN FORENSIC STACKED ROW COMPARISON MATRIX
    # =========================================================================
    print("\n" + "="*245)
    print(f"{'FORENSIC RETIREMENT PHILOSOPHY MATRIX: STACKED ROW-BY-ROW LEDGER COMPARISON':^245}")
    print("="*245)
    print(f"{'STRATEGY VIEW MASK':<15} | {'#':<3} | {'Yr':<4} | {'Age':<5} | {'Bracket':<7} | {'Brok Start':<14} | {'401k Start':<14} | {'Converted':<14} | {'Roth Start':<14} | {'Living Exp':<14} | {'Est Taxes':<12} | {'Health Cost':<12} | {'Inflow Base':<13} | {'Brok Yield':<12} | {'Req Income':<14} | {'From Broker':<13} | {'From Roth':<13} | {'From 401k':<20} | {'End Roth':<14}")
    print("-"*245)
    
    for idx in range(max_years):
        r = rotations_timeline[idx]
        h = hybrid_timeline[idx]
        
        r_sb = f"${r.get('start_brokerage', 0.00):,.2f}"
        r_st = f"${r.get('start_trad', 0.00):,.2f}"
        r_sc = f"${r.get('actual_conversion', 0.00):,.2f}"
        r_sr = f"${r.get('start_roth', 0.00):,.2f}"
        r_le = f"${r.get('living_expense', 0.00):,.2f}"
        r_ct = f"${r.get('total_taxes', 0.00):,.2f}"
        r_hc = f"${r.get('healthcare_cost', 0.00):,.2f}"
        r_inf = f"${r.get('pension_ss_rent', 0.00):,.2f}"
        r_bg = f"${r.get('brokerage_gains', 0.00):,.2f}"
        r_ri = f"${r.get('required_income', 0.00):,.2f}"
        r_fb = f"${r.get('from_brokerage', 0.00):,.2f}"
        r_fr = f"${r.get('from_roth', 0.00):,.2f}"
        
        # --- FIXED LEVEL CAPPED DYNAMIC LABEL SUFFIX GENERATION ---
        r_age = r.get('husband_age', 46 + idx)
        r_val_401k = r.get('from_401k', 0.00)
        if r_age >= 75 and r_val_401k > 0.01:
            r_suffix = " [RMD]"
        elif (52 <= r_age < 60) and r_val_401k > 0.01:
            r_suffix = " [SEPP]"
        else:
            r_suffix = ""
        r_f4 = f"${r_val_401k:,.2f}{r_suffix}"
        r_er = f"${r.get('end_roth', 0.00):,.2f}"
        
        print(f"\033[36m{'LEVEL CAPPED':<15}\033[0m | {idx+1:<3} | {str(r.get('year'))[-2:]:<4} | {r_age:<5} | {r.get('active_bracket', '0%'):<7} | {r_sb:<14} | {r_st:<14} | {r_sc:<14} | {r_sr:<14} | {r_le:<14} | {r_ct:<12} | {r_hc:<12} | {r_inf:<13} | {r_bg:<12} | {r_ri:<14} | {r_fb:<13} | {r_fr:<13} | {r_f4:<20} | {r_er:<14}")

        h_sb = f"${h.get('start_brokerage', 0.00):,.2f}"
        h_st = f"${h.get('start_trad', 0.00):,.2f}"
        h_sc = f"${h.get('actual_conversion', 0.00):,.2f}"
        h_sr = f"${h.get('start_roth', 0.00):,.2f}"
        h_le = f"${h.get('living_expense', 0.00):,.2f}"
        h_ct = f"${h.get('total_taxes', 0.00):,.2f}"
        h_hc = f"${h.get('healthcare_cost', 0.00):,.2f}"
        h_inf = f"${h.get('pension_ss_rent', 0.00):,.2f}"
        h_bg = f"${h.get('brokerage_gains', 0.00):,.2f}"
        h_ri = f"${h.get('required_income', 0.00):,.2f}"
        h_fb = f"${h.get('from_brokerage', 0.00):,.2f}"
        h_fr = f"${h.get('from_roth', 0.00):,.2f}"
        
        # --- FIXED HYBRID DYNAMIC LABEL SUFFIX GENERATION ---
        h_age = h.get('husband_age', 46 + idx)
        h_val_401k = h.get('from_401k', 0.00)
        if h_age >= 75 and h_val_401k > 0.01:
            h_suffix = " [RMD]"
        elif (52 <= h_age < 60) and h_val_401k > 0.01:
            h_suffix = " [SEPP]"
        else:
            h_suffix = ""
        h_f4 = f"${h_val_401k:,.2f}{h_suffix}"
        h_er = f"${h.get('end_roth', 0.00):,.2f}"

        print(f"\033[35m{'AGGRESSIVE CO':<15}\033[0m | {idx+1:<3} | {str(h.get('year'))[-2:]:<4} | {h_age:<5} | {h.get('active_bracket', '0%'):<7} | {h_sb:<14} | {h_st:<14} | {h_sc:<14} | {h_sr:<14} | {h_le:<14} | {h_ct:<12} | {h_hc:<12} | {h_inf:<13} | {h_bg:<12} | {h_ri:<14} | {h_fb:<13} | {h_fr:<13} | {h_f4:<20} | {h_er:<14}")
        print(f" {'-':<15} | {'-':<3} | {'-':<4} | {'-':<5} | {'-':<7} | {'-':<14} | {'-':<14} | {'-':<14} | {'-':<14} | {'-':<14} | {'-':<12} | {'-':<12} | {'-':<13} | {'-':<12} | {'-':<14} | {'-':<13} | {'-':<13} | {'-':<20} | {'-':<14}")

    print("="*245)
 
    # Final Summary Logs
    print(f"\n[SUMMARY] LEVEL CAPPED ROTATIONS FINAL TERMINAL WEALTH (AGE 90): ${total_estate_rotations:,.2f} | LIFETIME TAXES: ${rotations_lifetime_tax:,.2f}")
    print(f"[SUMMARY] AGGRESSIVE FULL CLEAN-OUT FINAL TERMINAL WEALTH (AGE 90): ${total_estate_hybrid:,.2f} | LIFETIME TAXES: ${hybrid_lifetime_tax:,.2f}")
    
    diff = abs(total_estate_rotations - total_estate_hybrid)
    print("\n" + "*"*145)
    print(f"{'MASTER DRIVER STRATEGIC VERDICT REPORT':^145}")
    print("*"*145)
    if total_estate_rotations > total_estate_hybrid:
        print(f" Strategic Victory: [LEVEL CAPPED ROTATIONS STRATEGY] wins by leaving exactly ${diff:,.2f} MORE inside your final estate at Age 90.")
        print(" Strategic Rationale: Maintaining multi-authority tax bracket shields and utilizing self-funding draws keeps capital")
        print(" compounding in high-performing core assets longer, overcoming the long-term friction of late-life RMD tax drag.")
    else:
        print(f" Strategic Victory: [AGGRESSIVE FULL CLEAN-OUT STRATEGY] wins by leaving exactly ${diff:,.2f} MORE inside your final estate at Age 90.")
        print(f" Strategic Victory: [AGGRESSIVE FULL CLEAN-OUT STRATEGY] wins by leaving exactly ${diff:,.2f} MORE inside your final estate at Age 90.")
        print(" Strategic Rationale: Rapid, aggressive front-loaded cleanouts eliminate structural pre-tax exposure completely, insulating")
        print(" the estate from future legislative changes and long-term bracket creep penalties.")
    print("="*145 + "\n")


if __name__ == "__main__":
    execute_master_comparison()

