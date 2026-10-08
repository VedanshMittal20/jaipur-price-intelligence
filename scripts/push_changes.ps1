$ErrorActionPreference = "Stop"

Set-Location -Path "c:\Users\vedan\Documents\antigravity\clever-hubble"

Write-Host "Running tests..."
pytest -q tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed! Aborting push."
    exit $LASTEXITCODE
}

Write-Host "Staging changes..."
git add .

$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "No changes to commit."
    exit 0
}

Write-Host "Committing changes..."
git commit -m "chore(audit): daily health audit, enhancements, and a11y improvements"

Write-Host "Pushing to remote..."
git push origin main

Write-Host "Daily automated push complete!"
