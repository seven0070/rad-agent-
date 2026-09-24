# build-desktop-release.ps1
# ---------------------------------------------------------------------------
# Single entry point for a shippable Windows desktop package.
#
#   sidecar freeze (rad + rad-backend, MSVC triple)
#     -> assert binaries are real (> 1 KB, not 0-byte stubs)
#     -> tauri build (MSVC override on desktop/src-tauri)
#     -> assert MSI/NSIS bundles exist and postdate this run
#     -> print sizes + installer paths
#
# Same contract as CI (.github/workflows/release-desktop.yml).
#
# Usage (repo root or anywhere):
#   powershell -ExecutionPolicy Bypass -File scripts\build-desktop-release.ps1
#   ... -SkipSidecar     # reuse existing binaries (still asserts size)
#   ... -SkipTauri       # sidecar only
#
# Exit non-zero on any failure. Requires: Python 3.10+, Node 20 + desktop
# deps already present (do NOT npm install on Google Drive paths), Rust MSVC
# toolchain. Both sidecar freezes use isolated clean venvs (host site-packages
# may carry torch/matplotlib and OOM PyInstaller): rad-backend via
# python -m sidecar.build, rad CLI via scripts/build-sidecar.ps1.
# ---------------------------------------------------------------------------

[CmdletBinding()]
param(
    [switch]$SkipSidecar,
    [switch]$SkipTauri,
    [string]$Triple = 'x86_64-pc-windows-msvc',
    [int]$MinSidecarBytes = 1024,
    [long]$MinInstallerBytes = 524288
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$binDir   = Join-Path $repoRoot 'desktop\src-tauri\binaries'
$srcTauri = Join-Path $repoRoot 'desktop\src-tauri'
$desktop  = Join-Path $repoRoot 'desktop'
$started  = Get-Date

function Write-Step([string]$msg) { Write-Host "[release] $msg" }

function Assert-File {
    param([string]$Path, [long]$MinBytes, [string]$What)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$What missing: $Path"
    }
    $len = (Get-Item -LiteralPath $Path).Length
    if ($len -lt $MinBytes) {
        throw "$What too small ($len bytes < $MinBytes): $Path (0-byte stub or failed freeze?)"
    }
    Write-Step ("OK  {0}: {1} ({2:N0} bytes)" -f $What, (Split-Path -Leaf $Path), $len)
    return $len
}

function Invoke-Checked {
    param([string]$FilePath, [string[]]$Arguments, [string]$WorkDir)
    $prev = $null
    if ($WorkDir) { $prev = Get-Location; Set-Location -LiteralPath $WorkDir }
    try {
        Write-Step "RUN $FilePath $($Arguments -join ' ')"
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed (exit $LASTEXITCODE): $FilePath $($Arguments -join ' ')"
        }
    } finally {
        if ($prev) { Set-Location $prev }
    }
}

Write-Step "Repo:  $repoRoot"
Write-Step "Triple: $Triple"
Write-Step "Started: $($started.ToString('s'))"

# --- 1. Sidecars -------------------------------------------------------------
$radSidecar     = Join-Path $binDir ("rad-{0}.exe" -f $Triple)
$backendSidecar = Join-Path $binDir ("rad-backend-{0}.exe" -f $Triple)

if (-not $SkipSidecar) {
    # rad-backend: python -m sidecar.build (isolated venv + PyInstaller)
    Invoke-Checked -FilePath 'python' -Arguments @(
        '-m', 'sidecar.build',
        '--triple', $Triple,
        '--verbose'
    ) -WorkDir $repoRoot

    # rad CLI: isolated venv + PyInstaller onefile (same path CI used)
    Invoke-Checked -FilePath 'powershell' -Arguments @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', (Join-Path $repoRoot 'scripts\build-sidecar.ps1')
    ) -WorkDir $repoRoot
} else {
    Write-Step "SkipSidecar: reusing existing binaries"
}

$radLen     = Assert-File -Path $radSidecar     -MinBytes $MinSidecarBytes -What 'rad CLI sidecar'
$backendLen = Assert-File -Path $backendSidecar -MinBytes $MinSidecarBytes -What 'rad-backend sidecar'

# Smoke: frozen backend answers --help (serve/health contract)
Write-Step "Smoke: $backendSidecar --help"
$smoke = & $backendSidecar --help 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) { throw "sidecar --help failed (exit $LASTEXITCODE): $smoke" }
foreach ($word in @('serve', 'health')) {
    if ($smoke -notmatch [regex]::Escape($word)) {
        throw "sidecar --help missing subcommand '$word': $smoke"
    }
}
Write-Step "Smoke OK"

if ($SkipTauri) {
    Write-Step "SkipTauri: done after sidecar stage"
    exit 0
}

# --- 2. Pin MSVC for src-tauri (gnu windres dies on the space in 'My Drive') --
Write-Step "rustup override -> stable-x86_64-pc-windows-msvc (src-tauri)"
Invoke-Checked -FilePath 'rustup' -Arguments @(
    'override', 'set', 'stable-x86_64-pc-windows-msvc'
) -WorkDir $srcTauri

# --- 3. Frontend deps (must already exist on Google Drive; never npm install) --
if (-not (Test-Path -LiteralPath (Join-Path $desktop 'node_modules\@tauri-apps\cli'))) {
    throw "desktop\node_modules missing @tauri-apps/cli. Run npm ci once on a non-Google-Drive path, or restore node_modules."
}
if (-not (Test-Path -LiteralPath (Join-Path $desktop 'package-lock.json'))) {
    Write-Step "WARN: package-lock.json missing (npm ci in CI may fail)"
}

# --- 4. tauri build (beforeBuildCommand runs npm run build) ------------------
Write-Step "tauri build (packages externalBin sidecars into MSI + NSIS)"
Invoke-Checked -FilePath 'npm' -Arguments @('run', 'tauri', 'build') -WorkDir $desktop

# --- 5. Assert installers are fresh and non-trivial --------------------------
$bundleRoot = Join-Path $srcTauri 'target\release\bundle'
$msis  = @(Get-ChildItem -Path $bundleRoot -Recurse -Filter '*.msi' -ErrorAction SilentlyContinue)
$nsis  = @(Get-ChildItem -Path $bundleRoot -Recurse -Filter '*-setup.exe' -ErrorAction SilentlyContinue)
$all   = @($msis) + @($nsis)
if ($all.Count -eq 0) {
    throw "No MSI/NSIS installers under $bundleRoot"
}

$fail = $false
foreach ($f in $all) {
    $len = Assert-File -Path $f.FullName -MinBytes $MinInstallerBytes -What 'installer'
    if ($f.LastWriteTime -lt $started) {
        Write-Step "STALE  $($f.Name) timestamp $($f.LastWriteTime.ToString('s')) < run start $($started.ToString('s'))"
        $fail = $true
    } else {
        Write-Step "Fresh $($f.Name) ($($f.LastWriteTime.ToString('s')))"
    }
}

# Embedded shell must match the just-built release exe (catches stale bundles)
$shell = Join-Path $srcTauri 'target\release\rad-desktop.exe'
if (Test-Path -LiteralPath $shell) {
    $shellItem = Get-Item -LiteralPath $shell
    if ($shellItem.LastWriteTime -lt $started) {
        Write-Step "STALE shell rad-desktop.exe $($shellItem.LastWriteTime.ToString('s')) - tauri may not have relinked"
        $fail = $true
    }
    Write-Step ("Shell: rad-desktop.exe {0:N0} bytes, {1}" -f $shellItem.Length, $shellItem.LastWriteTime.ToString('s'))
}
if ($fail) { throw "Installer staleness check failed - delete target/release/bundle and rebuild" }

# --- 6. Summary ---------------------------------------------------------------
Write-Output ''
Write-Output '========== desktop release summary =========='
Write-Output ("sidecar rad        : {0:N0} bytes  {1}" -f $radLen, $radSidecar)
Write-Output ("sidecar rad-backend: {0:N0} bytes  {1}" -f $backendLen, $backendSidecar)
foreach ($f in $all | Sort-Object LastWriteTime) {
    $mb = [math]::Round($f.Length / 1MB, 2)
    Write-Output ("installer          : {0,8:N2} MB  {1}" -f $mb, $f.FullName)
}
Write-Output ("elapsed            : {0:n1}s" -f ((Get-Date) - $started).TotalSeconds)
Write-Output '============================================='
exit 0
