===========================================================================
SDS Compliance Workbook — Automation Scripts
===========================================================================

PREREQUISITES
-------------
Python 3.9 or later
openpyxl  (pip install openpyxl)
pandas    (pip install pandas)   -- available for future use
No other third-party packages are required.


---------------------------------------------------------------------------
SCRIPT 1 — post_sharepoint_update.py
Flip OUTDATED rows to CURRENT after SharePoint / portal verification
---------------------------------------------------------------------------

PURPOSE
  Finds every row in "📂 SDS File Index" where:
    • Column G  = "OUTDATED"
    • Column H  is not blank
  For each matching row it:
    • Copies the portal date (H) into the file date (F)
    • Sets G  → "CURRENT"
    • Appends "Auto-flipped CURRENT YYYY-MM-DD" to the Notes column (I)
  Saves the workbook in-place. All formulas, formatting, and dropdown
  validation in other cells are preserved.

COMMAND (Windows Command Prompt or PowerShell)
  python post_sharepoint_update.py "C:\Users\edvigil\OneDrive\Lab Safety\SDS_Master_Reconciled_V10_ONEDRIVE.xlsx"

OUTPUT
  Prints a summary table:
    DOC#  |  Old Rev Date  |  New Rev Date  |  Product Name

NOTES
  • Run this AFTER you have confirmed portal dates in column H.
  • Back up the workbook before running for the first time.
  • Rows where G is already "CURRENT", or H is blank, are silently skipped.
  • Do NOT open the workbook in Excel while the script is running.


---------------------------------------------------------------------------
SCRIPT 2 — export_vendor_batches.py
Export UNVERIFIED rows as per-manufacturer Claude batch files
---------------------------------------------------------------------------

PURPOSE
  Reads every row in "📂 SDS File Index" where:
    • Column G  = "UNVERIFIED"  OR  G is blank
    • Column K  is not blank  (the pipe-delimited Claude prompt string)
  Groups those rows by Manufacturer (column D).
  Writes output files into a  claude_batches\  subfolder created next
  to the workbook.

OUTPUT FILES
  claude_batches\batch_<ManufacturerName>.txt   — one K-value per line
  claude_batches\batch_summary.txt              — sorted summary table

COMMAND (Windows Command Prompt or PowerShell)
  python export_vendor_batches.py "C:\Users\edvigil\OneDrive\Lab Safety\SDS_Master_Reconciled_V10_ONEDRIVE.xlsx"

WORKFLOW
  1. Run export_vendor_batches.py to generate the batch files.
  2. Open a batch_<Mfr>.txt file.
  3. Paste each line (the K-column prompt) into Claude in Chrome.
  4. Record the portal status and date back in columns G and H.
  5. When all rows for a manufacturer are resolved, run
     post_sharepoint_update.py to flip the OUTDATED ones to CURRENT.


---------------------------------------------------------------------------
TYPICAL WORKFLOW (end-to-end)
---------------------------------------------------------------------------

Step 1 — Export batches for vendor research
  python export_vendor_batches.py "C:\Users\edvigil\OneDrive\Lab Safety\SDS_Master_Reconciled_V10_ONEDRIVE.xlsx"

Step 2 — Research each vendor batch in Claude, update G and H in Excel

Step 3 — Flip verified rows to CURRENT
  python post_sharepoint_update.py "C:\Users\edvigil\OneDrive\Lab Safety\SDS_Master_Reconciled_V10_ONEDRIVE.xlsx"

Repeat Steps 1-3 as new SDS documents are added.


---------------------------------------------------------------------------
TROUBLESHOOTING
---------------------------------------------------------------------------

"sheet not found" error
  The sheet name contains a special emoji character.  Make sure the
  workbook has not been renamed.  Check with:
    python -c "import openpyxl; wb=openpyxl.load_workbook('path.xlsx'); print(wb.sheetnames)"

Script runs but changes 0 rows (post_sharepoint_update.py)
  Verify that column G cells contain exactly the text OUTDATED (no extra
  spaces) and that column H has a date value, not a formula error.

OneDrive sync conflict after saving
  Close the workbook in Excel before running either script, and allow
  OneDrive to finish syncing before running again.

===========================================================================
