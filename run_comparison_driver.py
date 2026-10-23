# -*- coding: utf-8 -*-
"""
MASTER RETIREMENT ROADMAP RUNWAY DRIVER ENGINE - INTEGRATED MODULE ENGINE
Natively executes your live optimize_rotations.py and optimize_hybrid.py files.
Extracts penny-accurate timeline data matching your true file structures corner-to-corner.
"""
import os
import sys

# Append local script directory path to guarantee seamless cross-imports
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# --- CHANGE THIS SECTION AT THE TOP OF RUN_COMPARISON_DRIVER.PY ---
try:
    import config
    
    # >>> FLIP THESE TWO LINES CORNER-TO-CORNER TO ALIGN THE LABELS <<<
    import optimize_hybrid as optimize_rotations  # Hybrid holds your capped SEPP logic
    import optimize_rotations as optimize_hybrid  # Rotations holds your cleanout logic

except ImportError as err:

    print(f"[CRITICAL ERROR] Master Driver failed to resolve script dependencies: {err}")
    print("Please ensure this file is saved inside the same folder as config.py, optimize_rotations.py, and optimize_hybrid.py.")
    sys.exit(1)


def capture_accurate_snapshots(timeline_data):
    """
    Parses your live 44-year timeline arrays and extracts snapshot metrics.
    Synchronized corner-to-corner with your conformed sub-script dictionary keys.
    """
    target_milestones = [46, 51, 60, 65, 75, 90]
    snapshots = {}
    
    for row in timeline_data:
        h_age = row.get("husband_age")
        if h_age in target_milestones:
            # Fix tracking synchronization by capturing live start and end keys cleanly
            snapshots[h_age] = {
                "brok": row.get("start_brokerage", row.get("end_brokerage", 0.00)),
                "trad": row.get("start_trad", row.get("end_trad", 0.00)),
                "roth": row.get("start_roth", row.get("end_roth", 0.00)),
                "tax": row.get("total_taxes", 0.00)
            }
            
    # Tail-end override to lock down your absolute terminal Age 90 legacy state
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
    
    # 1. Natively execute your true Level Capped model from optimize_rotations.py
    rotations_schedule = getattr(config, "DYNAMIC_BRACKET_SCHEDULE", [12, 12, 12, 12, 12])
    rotations_timeline = optimize_rotations.run_financial_simulation(rotations_schedule)
    rotations_snapshots = capture_accurate_snapshots(rotations_timeline)
    rotations_lifetime_tax = sum(y.get("total_taxes", 0.00) for y in rotations_timeline)
    
    # 2. Natively execute your true Aggressive Cleanout model from optimize_hybrid.py
    hybrid_schedule = [22, 22, 22, 22, 22] # Matches your live Rank 1 pattern
    hybrid_timeline = optimize_hybrid.run_financial_simulation(hybrid_schedule)
    hybrid_snapshots = capture_accurate_snapshots(hybrid_timeline)
    hybrid_lifetime_tax = sum(y.get("total_taxes", 0.00) for y in hybrid_timeline)
    
    final_age = 90
    r_final = rotations_snapshots.get(final_age, {"brok": 0, "trad": 0, "roth": 0})
    h_final = hybrid_snapshots.get(final_age, {"brok": 0, "trad": 0, "roth": 0})
    
    total_estate_rotations = r_final["brok"] + r_final["trad"] + r_final["roth"]
    total_estate_hybrid = h_final["brok"] + h_final["trad"] + h_final["roth"]
    
    # =========================================================================
    # SYSTEMWIDE WIDESCREEN TERMINAL COMPARISON LEDGER MATRIX
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
    
    print("\n" + "*"*145)
    print(f"{'MASTER DRIVER STRATEGIC VERDICT REPORT':^145}")
    print("*"*145)
    
    diff = abs(total_estate_rotations - total_estate_hybrid)
    if total_estate_rotations > total_estate_hybrid:
        print(f" Strategic Victory: [LEVEL CAPPED ROTATIONS STRATEGY] wins by saving exactly ${diff:,.2f} MORE inside your final estate at Age 90.")
    else:
        print(f" Strategic Victory: [AGGRESSIVE FULL CLEAN-OUT STRATEGY] wins by leaving exactly ${diff:,.2f} MORE inside your final estate at Age 90.")
    print("="*145 + "\n")


if __name__ == "__main__":
    execute_master_comparison()

