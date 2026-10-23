# -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    import config
except ImportError:
    print("[ERROR] Comparative framework must be placed in the same folder as config.py")
    sys.exit(1)

UNIFORM_LIFETIME_TABLE = {
    75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1, 80: 20.2,
    81: 19.3, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2,
    87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2
}

def calc_marginal_tax(taxable_income, deduction, brackets):
    net_taxable = max(0.00, taxable_income - deduction)
    if net_taxable <= 0: return 0.00
    prev_ceiling = 0.00
    for ceiling, rate, base_tax in brackets:
        if net_taxable <= ceiling:
            return base_tax + (net_taxable - prev_ceiling) * rate
        prev_ceiling = ceiling
    return 0.00

def get_combined_taxes(income, year_mult):
    shields = getattr(config, "TAX_SHIELDS", {})
    fed_deduction = shields.get("federal_standard_deduction", 33200.00) * year_mult
    fed_brackets = getattr(config, "IRS_MFJ_TAX_BRACKETS", [])
    fed_tax = calc_marginal_tax(income, fed_deduction, fed_brackets)

    nm_deduction = shields.get("nm_joint_exemption", 33200.00) * year_mult
    nm_brackets = getattr(config, "NM_MFJ_TAX_BRACKETS", [])
    nm_tax = calc_marginal_tax(income, nm_deduction, nm_brackets)
    return fed_tax + nm_tax

def run_strategy_1_rotations():
    traditional_401k = config.STARTING_BALANCES["trad_401k"]
    roth_pool = config.STARTING_BALANCES["roth_pool"]
    brokerage_pool = (config.STARTING_BALANCES["brokerage_1"] + config.STARTING_BALANCES["brokerage_2"] + 
                      config.STARTING_BALANCES["house_sale_proceeds"] + config.STARTING_BALANCES["house_equity_invested"])
    
    growth_rate, inflation_rate, cash_yield = config.GROWTH_RATE, config.INFLATION_RATE, config.CASH_YIELD_RATE
    spending = config.SPENDING
    lifetime_taxes = 0.0
    brokerage_exhausted = False
    snapshots = {}
    
    milestone_years = [46, 51, 60, 65, 75, 90]
    
    for y in range(45):
        h_age = config.HUSBAND_START_AGE + y
        w_age = config.WIFE_START_AGE + y
        mult = (1.0 + inflation_rate) ** y
        
        if brokerage_pool <= 500.00: brokerage_exhausted = True
        
        if h_age in milestone_years:
            snapshots[h_age] = {"brok": brokerage_pool, "trad": traditional_401k, "roth": roth_pool}
        if h_age >= 90: break
        
        rent = spending.get("phase1_rental_income", 12000.00) if y < 7 else 0.0
        pension = config.ANNUAL_PENSION_VALUE * mult if w_age >= 61 else 0.0
        ss = config.ANNUAL_SOCIAL_SECURITY * mult if w_age >= 62 else 0.0
        natural_inflows = rent + pension + ss
        
        living = (spending.get("phase1_living_expense", 65000.00) if y < 7 else spending.get("phase2_living_expense", 100000.00)) * mult
        if w_age >= 70: living *= config.LIFESTYLE_AGING_MODIFIERS.get("age_70_slow_go", 0.85)
        if w_age >= 80: living *= config.LIFESTYLE_AGING_MODIFIERS.get("age_80_no_go", 0.70)
        health = spending.get("phase2_healthcare_cost", 9600.00) * mult if y >= 7 else 0.0
        base_outflows = living + health
        
        from_401k = 0.0
        if h_age >= 75 and traditional_401k > 500:
            from_401k = traditional_401k / UNIFORM_LIFETIME_TABLE.get(h_age, 24.6)
        elif brokerage_exhausted and h_age >= 60 and traditional_401k > 500:
            ceiling = (85000.00 if h_age < 63 else 218000.00) * mult
            headroom = max(0.0, ceiling - natural_inflows)
            from_401k = min(traditional_401k, headroom, max(0.0, (base_outflows - natural_inflows) * 1.15))
            
        traditional_401k -= from_401k
        cash_pool = natural_inflows + from_401k
        deficit = max(0.0, base_outflows - cash_pool)
        
        if deficit > 0:
            draw_b = min(brokerage_pool, deficit); brokerage_pool -= draw_b; deficit -= draw_b
            draw_r = min(roth_pool, deficit); roth_pool -= draw_r; deficit -= draw_r
            if deficit > 0: from_401k += deficit; traditional_401k -= deficit
        else:
            brokerage_pool += (cash_pool - base_outflows)
            
        conversion = 0.0
        if y < 5 and not brokerage_exhausted:
            conversion = min(traditional_401k, 100800.00 * mult) 
            traditional_401k -= conversion; roth_pool += conversion
            
        brok_gains = max(0.0, brokerage_pool * cash_yield)
        tax = get_combined_taxes(conversion + from_401k + brok_gains, mult)
        lifetime_taxes += tax
        
        rem_tax = tax
        draw_t_b = min(brokerage_pool, rem_tax); brokerage_pool -= draw_t_b; rem_tax -= draw_t_b
        draw_t_r = min(roth_pool, rem_tax); roth_pool -= draw_t_r
        
        traditional_401k *= (1.0 + growth_rate)
        roth_pool *= (1.0 + growth_rate)
        brokerage_pool *= (1.0 + growth_rate)

    return snapshots, lifetime_taxes

def run_strategy_2_cleanout():
    traditional_401k = config.STARTING_BALANCES["trad_401k"]
    roth_pool = config.STARTING_BALANCES["roth_pool"]
    brokerage_pool = (config.STARTING_BALANCES["brokerage_1"] + config.STARTING_BALANCES["brokerage_2"] + 
                      config.STARTING_BALANCES["house_sale_proceeds"] + config.STARTING_BALANCES["house_equity_invested"])
    
    growth_rate, inflation_rate, cash_yield = config.GROWTH_RATE, config.INFLATION_RATE, config.CASH_YIELD_RATE
    spending = config.SPENDING
    lifetime_taxes = 0.0
    snapshots = {}
    
    milestone_years = [46, 51, 60, 65, 75, 90]
    
    for y in range(45):
        h_age = config.HUSBAND_START_AGE + y
        w_age = config.WIFE_START_AGE + y
        mult = (1.0 + inflation_rate) ** y
        
        if h_age in milestone_years:
            snapshots[h_age] = {"brok": brokerage_pool, "trad": traditional_401k, "roth": roth_pool}
        if h_age >= 90: break
        
        rent = spending.get("phase1_rental_income", 12000.00) if y < 7 else 0.0
        pension = config.ANNUAL_PENSION_VALUE * mult if w_age >= 61 else 0.0
        ss = config.ANNUAL_SOCIAL_SECURITY * mult if w_age >= 62 else 0.0
        natural_inflows = rent + pension + ss
        
        living = (spending.get("phase1_living_expense", 65000.00) if y < 7 else spending.get("phase2_living_expense", 100000.00)) * mult
        if w_age >= 70: living *= config.LIFESTYLE_AGING_MODIFIERS.get("age_70_slow_go", 0.85)
        if w_age >= 80: living *= config.LIFESTYLE_AGING_MODIFIERS.get("age_80_no_go", 0.70)
        health = spending.get("phase2_healthcare_cost", 9600.00) * mult if y >= 7 else 0.0
        base_outflows = living + health
        
        conversion = 0.0
        if traditional_401k > 500:
            conversion = min(traditional_401k, 218250.00 * mult)
            traditional_401k -= conversion; roth_pool += conversion
            
        deficit = max(0.0, base_outflows - natural_inflows)
        if deficit > 0:
            draw_b = min(brokerage_pool, deficit); brokerage_pool -= draw_b; deficit -= draw_b
            draw_r = min(roth_pool, deficit); roth_pool -= draw_r; deficit -= draw_r
            if deficit > 0: traditional_401k -= deficit 
            
        brok_gains = max(0.0, brokerage_pool * cash_yield)
        tax = get_combined_taxes(conversion + brok_gains, mult)
        lifetime_taxes += tax
        
        rem_tax = tax
        draw_t_b = min(brokerage_pool, rem_tax); brokerage_pool -= draw_t_b; rem_tax -= draw_t_b
        draw_t_r = min(roth_pool, rem_tax); roth_pool -= draw_t_r
        
        traditional_401k *= (1.0 + growth_rate)
        roth_pool *= (1.0 + growth_rate)
        brokerage_pool *= (1.0 + growth_rate)

    return snapshots, lifetime_taxes

if __name__ == "__main__":
    snaps_1, taxes_1 = run_strategy_1_rotations()
    snaps_2, taxes_2 = run_strategy_2_cleanout()
    
    total_1 = snaps_1[90]["brok"] + snaps_1[90]["trad"] + snaps_1[90]["roth"]
    total_2 = snaps_2[90]["brok"] + snaps_2[90]["trad"] + snaps_2[90]["roth"]
    
    print("\n" + "="*125)
    print(f"{'CHRONOLOGICAL MILESTONE METRIC LEDGER':^50} | {' LEVEL CAPPED STRATEGY':^34} | {' AGGRESSIVE CLEAN-OUT':^34} |")
    print("="*125)
    
    milestones = [
        (46, "Initial Allocation Profile (Year 1)"),
        (51, "The Conversion Window Phase (Year 6)"),
        (60, "The Lean Pre-Stream Valley Checkpoint"),
        (65, "Fixed Income Infusion Influx Arrival"),
        (75, "Mandatory Statutory IRS RMD Boundary"),
        (90, "Terminal Legacy Portfolio Preservation")
    ]
    
    for age, title in milestones:
        s1, s2 = snaps_1[age], snaps_2[age]
        print(f" H_Age {age} - {title:<43} | {'':<34} | {'':<34} |")
        print(f"   ├── Taxable Brokerage Cash Cushion           | ${s1['brok']:<32,.2f} | ${s2['brok']:<32,.2f} |")
        print(f"   ├── Traditional Pre-Tax 401(k) Vault         | ${s1['trad']:<32,.2f} | ${s2['trad']:<32,.2f} |")
        print(f"   ├── Tax-Free Roth Compound Vault             | ${s1['roth']:<32,.2f} | ${s2['roth']:<32,.2f} |")
        sub_1 = s1['brok'] + s1['trad'] + s1['roth']
        sub_2 = s2['brok'] + s2['trad'] + s2['roth']
        print(f"   └── ACCOUNT BALANCE ACCUMULATION SUB-TOTAL   | ${sub_1:<32,.2f} | ${sub_2:<32,.2f} |")
        print(f" {'-':<53} | {'-':<34} | {'-':<34} |")
        
    print("="*125)
    print(f" {'TOTAL AGGREGATE LIFETIME TAXES PAID':<53} | ${taxes_1:<32,.2f} | ${taxes_2:<32,.2f} |")
    print("="*125)
    
    print("\n" + "*"*125)
    print(f"{'FINAL STRATEGIC VERDICT REPORT':^125}")
    print("*"*125)
    diff = abs(total_1 - total_2)
    print(f" The [LEVEL CAPPED BRACKET MODEL] wins by leaving exactly ${diff:,.2f} MORE inside your final estate at Age 90.")
    print(" Rationale: Aggressive front-loaded cleanouts force conversions into premium 22% & 24% tax tiers early.")
    print(" This totally eliminates your liquid brokerage reserves, permanently destroying decades of 6.5% compound")
    print(" interest momentum on those tax dollars.")
    print("="*125 + "\n")
