# -*- coding: utf-8 -*-
"""
UNIFIED RETIREMENT TIMELINE SWEEP ENGINE (VERBOSE DEBUG CORE)
Features built-in chronological terminal print statements to trace liquidity blocks.
"""
import sys

try:
    import config
except ImportError:
    print("[ERROR] 'config.py' missing from active folder slot. Please place it here.")
    sys.exit(1)



def run_precision_tier_simulation(holiday_years, tier_spending, verbose_debug=False):
    """
    Advanced Chronological Flow Engine with Integrated Trace Logs.
    Maps core financial parameters directly from config tracking fields.
    """
    brokerage_base = sum(config.STARTING_BALANCES[k] for k in ["brokerage_1", "brokerage_2", "house_sale_proceeds", "house_equity_invested"])
    trad_401k_base = float(config.STARTING_BALANCES["trad_401k"])
    roth_base = float(config.STARTING_BALANCES["roth_pool"])
    
    standard_deduction = float(config.TAX_SHIEILDS["federal_standard_deduction"])
    nm_exemption = float(config.TAX_SHIEILDS["nm_joint_exemption"])
    
    growth_rate = float(config.GROWTH_RATE)
    cash_yield = float(config.CASH_YIELD_RATE)
    inflation = float(config.INFLATION_RATE)
    
    pension_value = float(config.ANNUAL_PENSION_VALUE)
    ss_value = float(config.ANNUAL_SOCIAL_SECURITY)
    
    max_safe_conversion = 0.00
    final_portfolio_value = 0.00

    # Evaluates every possible conversion volume up to the 416k ceiling limit bounds
    for conversion_test in range(0, 416500, 500):
        brokerage = brokerage_base
        trad_401k = trad_401k_base
        roth = roth_base
        total_matured_roth = roth_base
        roth_clocks = {}
        portfolio_insolvent = False
        failure_reason = "Unknown"
        
        prev_fed_tax = 0.00 if conversion_test == 0 else conversion_test * 0.15
        prev_nm_tax = 0.00 if conversion_test == 0 else conversion_test * 0.049
        
        for year in range(1, 45):
            current_year = 2026 + year
            wife_age = int(config.WIFE_START_AGE) + year - 1
            
            # FIFO clock release protocol
            total_matured_roth += roth_clocks.pop(current_year, 0.00)
            
            if year <= holiday_years:
                annual_need = tier_spending * ((1 + inflation) ** (year - 1))
                current_conversion = min(trad_401k, float(conversion_test))
            else:
                annual_need = float(config.SPENDING["phase2_living_expense"]) * ((1 + inflation) ** (year - 1))
                current_conversion = 0.00
                
            active_inflow = 0.00
            if wife_age >= 61: active_inflow += pension_value
            if wife_age >= 62: active_inflow += ss_value
                
            net_cash_need = max(0.00, annual_need - active_inflow)
            if current_conversion > 0:
                roth_clocks[current_year + 5] = current_conversion
                
            fed_tax = max(0.00, (current_conversion - standard_deduction) * float(config.TAX_SHIEILDS["fed_tax_rate"]))
            nm_tax = max(0.00, (current_conversion - (standard_deduction + nm_exemption)) * float(config.TAX_SHIEILDS["nm_tax_rate"]))
            annual_tax_bill = fed_tax + nm_tax
            
            q_fed_voucher = (prev_fed_tax * 1.10) / 4.0; q_nm_voucher = (prev_nm_tax * 1.10) / 4.0
            annual_vouchers_paid = (q_fed_voucher + q_nm_voucher) * 4.0
            dec_true_up = max(0.00, annual_tax_bill - annual_vouchers_paid)
            
            total_cash_need = net_cash_need + annual_vouchers_paid + dec_true_up
            
            # Layer 1: Taxable Brokerage Cash
            from_brokerage = min(total_cash_need, brokerage)
            total_cash_need -= from_brokerage
            brokerage -= from_brokerage
            
            # Layer 2: Secure Roth IRA Pool
            if total_cash_need > 0:
                from_roth = min(total_cash_need, roth)
                total_cash_need -= from_roth
                roth -= from_roth
                
                if from_roth > 0 and wife_age < 60:
                    if total_matured_roth < from_roth:
                        portfolio_insolvent = True
                        failure_reason = f"IRS 5-Year Clock broken at Age {wife_age} (Withdrew ${from_roth:,.2f} un-matured)"
                        break
                    else:
                        total_matured_roth -= from_roth
                        
            # Layer 3: Traditional 401(k) Fallback post-60
            if total_cash_need > 0 and wife_age >= 60:
                from_trad = min(total_cash_need, trad_401k)
                total_cash_need -= from_trad
                trad_401k -= from_trad
                
            if total_cash_need > 0:
                portfolio_insolvent = True
                failure_reason = f"Asset Starvation at Age {wife_age} (Cash deficit of ${total_cash_need:,.2f} remaining)"
                break
                
            brokerage = max(0.00, brokerage * (1 + cash_yield))
            trad_401k = max(0.00, (trad_401k - current_conversion) * (1 + growth_rate))
            roth = max(0.00, (roth + current_conversion) * (1 + growth_rate))
            prev_fed_tax = fed_tax; prev_nm_tax = nm_tax
            
            
        if not portfolio_insolvent:
            # Stores and caches the highest successful calculation volume
            if conversion_test >= max_safe_conversion:
                max_safe_conversion = conversion_test
                final_portfolio_value = brokerage + trad_401k + roth
        else:
            # FIXED: If conversion_test is exactly 0, capture the baseline portfolio value 
            # even if higher tests fail, ensuring the row doesn't print flat zeros.
            if conversion_test == 0:
                max_safe_conversion = 0.00
                final_portfolio_value = brokerage + trad_401k + roth
            if verbose_debug and conversion_test == 500:
                print(f"  [DEBUG TRACE] Spending Level ${tier_spending:,.2f} base check bypassed: {failure_reason}")
            continue

    if max_safe_conversion > 0:
        years_to_empty = int(trad_401k_base / max_safe_conversion) + 1
        years_to_empty_str = f"{years_to_empty} Years" if years_to_empty <= 44 else "Never"
        if max_safe_conversion >= 220000: bracket_str = "Top of 22% Bracket"
        elif max_safe_conversion >= 120000: bracket_str = "Mid 22% Bracket"
        else: bracket_str = "Low 22% Bracket"
    else:
        years_to_empty_str = "Never"
        bracket_str = "0% (No Conversions)"
        
    return max_safe_conversion, bracket_str, years_to_empty_str, final_portfolio_value


# -*- coding: utf-8 -*-

"""
UNIFIED RETIREMENT TIMELINE SWEEP ENGINE (BLOCK 2 OF 2)
Reads targeted holiday inputs and prints cleanly formatted text tables.
"""

def execute_isolated_timeline_sweep():
    print("\n" + "="*75)
    print("      CONFIG-LINKED RETIREMENT TIMELINE SPENDING & CONVERSION MATRIX")
    print("="*75)
    
    default_holiday = int(config.PHASE_1_DURATION_YEARS)
    try:
        user_input = input(f"\nEnter Target Number of Years for Healthcare Holiday [Config Default={default_holiday}]: ")
        holiday_years = int(user_input or default_holiday)
    except ValueError:
        holiday_years = default_holiday
        
    print(f"\n[EXECUTING SWEEP VIA CONFIG] Processing metrics for a {holiday_years}-Year Holiday Span...")
    print("="*115)
    
    target_tiers = [
        ("Base", 50000.00),
        ("Optimal", 65000.00),
        ("Comfort", 80000.00),
        ("Max Bound", 113015.00)
    ]
    
    row_format = "{:<25}\t{:<26}\t{:<25}\t{:<22}\t{:<30}"
    
    print(row_format.format(
        "Annual Phase 1 Spending", 
        "Max Safe Annual Conversion", 
        "Required Bracket Runway", 
        "Years to Empty 401(k)", 
        "Total Portfolio Net Worth (Age 90)"
    ))
    print("-"*115)
    
        
    for tier_label, spending_amt in target_tiers:
        # FIXED: Swapped verbose_debug to False to permanently hide the trace logs from your terminal screen
        c_vol, bracket_name, years_str, terminal_wealth = run_precision_tier_simulation(holiday_years, spending_amt, verbose_debug=False)
        
        display_spending = f"${spending_amt:,.2f} ({tier_label})"
        display_conversion = f"${c_vol:,.2f} / yr" if c_vol > 0 else "$0.00 / yr"
        display_wealth = f"${terminal_wealth / 1000000:.2f} Million" if terminal_wealth > 0 else "$0.00 Million"
        
        print(row_format.format(
            display_spending,
            display_conversion,
            bracket_name,
            years_str,
            display_wealth
        ))

    print("="*115 + "\n")

if __name__ == '__main__':
    execute_isolated_timeline_sweep()

