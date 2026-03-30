# Quick Task 260330-eto: Fix Batch Management Issues - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Task Boundary

Fix three batch management bugs in the cell counter web app:
1. Cell counts not restored when opening a saved batch (File/Cell Count table appears empty)
2. Save Batch asks for a name even when a batch is already open — should overwrite in-place
3. Grand total cell count across all batch images not displayed

</domain>

<decisions>
## Implementation Decisions

### Total Count Display
- Add a "Total" summary row at the bottom of the File/Cell Count table, summing all images

### Save Batch Trigger
- When a batch is already open (has a current batch name), Save Batch should silently overwrite/update without prompting for a name
- After saving, show a brief toast/status confirmation message ("Batch saved") for 2-3 seconds

### Claude's Discretion
- Implementation details for how batch state is read/restored from manifest.json
- Exact styling of the Total row and toast message

</decisions>

<specifics>
## Specific Ideas

- The File/Cell Count table is currently empty after opening a batch — root cause likely in how manifest.json cell_count values are loaded into the UI table
- The title bar already shows the batch name (e.g. "Cell Counter — batch3"), so the app tracks current batch state somewhere
- Save Batch should check if a current batch name exists; if yes, update manifest in-place; if no, prompt for name as usual

</specifics>
