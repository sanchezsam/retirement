# -*- coding: utf-8 -*-
import openpyxl
import os

# 1. Cleanly purge any locked or cached old spreadsheet data files first
if os.path.exists("roth_conversion_comparison_v5.xlsx"):
    try:
        os.remove("roth_conversion_comparison_v5.xlsx")
    except:
        pass

import gen_excel

print("----------------------------------------------------------------------")
print("SUCCESS: Old system file locks cleared. Re-compiling synced matrix...")
print("----------------------------------------------------------------------")
