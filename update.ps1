# update.ps1 - Downloads the latest app files from GitHub and updates local copies.
# Double-click or run from PowerShell: .\update.ps1
# Does NOT touch: .venv, batches, images, verified_counts, or any CSV files.

$ErrorActionPreference = "Stop"
$REPO   = "fruscitti/cells_counting"
$BRANCH = "main"
$BASE   = "https://raw.githubusercontent.com/$REPO/$BRANCH"

$FILES = @(
    "app.py",
    "icon.png",
    "analysis_core.py",
    "batch_manager.py",
    "main.py",
    "ui/__init__.py",
    "ui/batch_dialogs.py",
    "ui/image_utils.py",
    "ui/main_window.py",
    "ui/param_panel.py",
    "ui/scaled_image_label.py",
    "workers/__init__.py",
    "workers/analysis_worker.py",
    "workers/optimize_worker.py",
    "setup.bat",
    "run.bat",
    "update.ps1"
)

Write-Host ""
Write-Host "============================================="
Write-Host "  Cell Counter - Update"
Write-Host "============================================="
Write-Host ""
Write-Host "Downloading latest files from GitHub ($BRANCH)..."
Write-Host ""

$updated = 0
$failed  = 0

foreach ($file in $FILES) {
    $url    = "$BASE/$file"
    $dest   = Join-Path $PSScriptRoot $file

    # Make sure the directory exists
    $dir = Split-Path $dest
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
        Write-Host "  OK  $file"
        $updated++
    } catch {
        Write-Host "  SKIP  $file  (not found on remote — skipping)"
        $failed++
    }
}

Write-Host ""
Write-Host "============================================="
Write-Host "  Update complete: $updated file(s) updated"
if ($failed -gt 0) {
    Write-Host "  $failed file(s) not found on remote (skipped)"
}
Write-Host "  You can now run the app with run.bat"
Write-Host "============================================="
Write-Host ""

# Keep window open if double-clicked
if ($Host.Name -eq "ConsoleHost") {
    Write-Host "Press any key to close..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
