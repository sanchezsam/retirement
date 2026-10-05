# -*- coding: utf-8 -*-
"""
INDENTATION RECONCILIATION ENGINE FOR RETIREMENT ENGINE
Reads surroundings to mirror exact spacing structures.
"""
import os

def apply_precise_indent_patch():
    source_filename = "run_all.py"
    output_filename = "run_new.py"
    
    if not os.path.exists(source_filename):
        print(f"[ERROR] Source file '{source_filename}' not found.")
        return

    with open(source_filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print("[INFO] Scanning core file for precise line matching patterns...")
    
    target_idx = -1
    detected_spaces = ""
    
    # Locate the target bracket calculation line and capture its exact indentation profile
    for idx, line in enumerate(lines):
        if "bracket_ceiling = 416100.00 if target_bracket == 24 else 233250.00" in line:
            target_idx = idx
            # Capture whatever exact character string (spaces/tabs) started this line
            detected_spaces = line[:line.find("bracket_ceiling")]
            break

    if target_idx == -1:
        print("[ERROR] Could not find the original static bracket_ceiling definition line.")
        return

    print(f"[INFO] Detected exact spacing profile: {len(detected_spaces)} characters deep.")

    # Build the insertion using the exact spaces match from your file layout
    # Build the insertion using the exact spaces match from your file layout
    new_block = [
        f"{detected_spaces}if target_bracket == \"schedule\":\n",
        f"{detected_spaces}    schedule_list = getattr(config, \"DYNAMIC_BRACKET_SCHEDULE\", [])\n",
        f"{detected_spaces}    active_percentage = schedule_list[year - 1] if year <= len(schedule_list) else getattr(config, \"DEFAULT_FALLBACK_BRACKET\", 22)\n",
        f"{detected_spaces}else:\n",
        f"{detected_spaces}    active_percentage = target_bracket\n\n",
        f"{detected_spaces}bracket_ceiling = 416100.00 if active_percentage == 24 else 233250.00\n"
    ]

    # Swap the single static line for our dynamically aligned indentation block
    lines[target_idx] = "".join(new_block)

    # Apply the openpyxl tuple auto-fit patch cleanly
    for idx, line in enumerate(lines):
        if "col_letter = get_column_letter(col_cells.column)" in line:
            fit_spaces = line[:line.find("col_letter")]
            lines[idx] = (
                f"{fit_spaces}first_cell_obj = col_cells\n"
                f"{fit_spaces}col_letter = get_column_letter(first_cell_obj.column)\n"
            )

    # Expand Dashboard Headers
    old_headers = 'dash_headers = ["Strategic Performance Parameter", "22% Smoothed Strategy", "24% Sprint Strategy"]'
    new_headers = 'dash_headers = ["Strategic Performance Parameter", "22% Strategy", "24% Strategy", "Custom Scheduled Strategy"]'
    for idx, line in enumerate(lines):
        if old_headers in line:
            lines[idx] = line.replace(old_headers, new_headers)

    # Remap Main Loop Execution Switches
    new_main_loop = (
        'if __name__ == "__main__":\n'
        '    args = parse_command_arguments()\n'
        '    strategies = {22: "Ledger - 22 Strategy", 24: "Ledger - 24 Strategy", "schedule": "Ledger - Custom Schedule"}\n'
        '    all_data = {}\n'
        '    for strategy_key in strategies.keys():\n'
        '        all_data[strategy_key] = run_financial_simulation(strategy_key)\n'
        '        compile_synchronized_pdf(all_data[strategy_key], strategy_key)\n'
        '    compile_synchronized_excel(all_data)\n'
        '    print("[SUCCESS] All strategies compiled perfectly into run_new.py!")\n'
    )

    for idx, line in enumerate(lines):
        if 'if __name__ == "__main__":' in line:
            lines[idx:] = [new_main_loop]
            break

    # Write out the cleanly reconciled framework file
    with open(output_filename, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"[SUCCESS] Layout indents structurally synchronized into '{output_filename}'!")

if __name__ == "__main__":
    apply_precise_indent_patch()

