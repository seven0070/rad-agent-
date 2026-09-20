# build-sidecar.ps1
# ---------------------------------------------------------------------------
# Builds the `rad` CLI as a PyInstaller onefile console executable and installs
# it where Tauri's externalBin (`binaries/rad` in desktop/src-tauri/
# tauri.conf.json) expects it for Windows x64:
#
#   desktop/src-tauri/binaries/rad-x86_64-pc-windows-msvc.exe
#
# Config note (Tauri integration contract):
#   The PyInstaller onefile console app IS the rad CLI itself. Tauri invokes
#   the sidecar directly by path -- it must NOT be called with `-m`/`--module`.
#
# Requirements:
#   - Python 3.10+ reachable via `py -3.12`, `py -3.11`, `py -3.10`, or a
#     plain `python` fallback.
#   - Network access to PyPI (pip installs package + PyInstaller into an
#     isolated venv).
#
# Usage:
#   powershell -File scripts/build-sidecar.ps1
#
# Exit code is non-zero on any failure ($ErrorActionPreference = 'Stop').
# ---------------------------------------------------------------------------

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$binDir   = Join-Path $repoRoot 'desktop\src-tauri\binaries'
$outName  = 'rad-x86_64-pc-windows-msvc.exe'
$outPath  = Join-Path $binDir $outName

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

Write-Output "[sidecar] Repo root: $repoRoot"
Write-Output "[sidecar] Target:    $outPath"

# --- 1. Locate Python 3.10+ --------------------------------------------------
$candidates = @(
    @{ Exe = 'py';     Args = @('-3.12') },
    @{ Exe = 'py';     Args = @('-3.11') },
    @{ Exe = 'py';     Args = @('-3.10') },
    @{ Exe = 'python'; Args = @() }
)

$pythonExe   = $null
$pythonArgv  = @()

foreach ($c in $candidates) {
    $probe = & $c.Exe $c.Args @('-c', 'import sys; print("%d.%d" % sys.version_info[:2])') 2>$null
    if ($LASTEXITCODE -eq 0 -and $probe) {
        $verText = ($probe | Select-Object -Last 1)
        try {
            $ver = [version]$verText
        } catch {
            $ver = $null
        }
        if ($ver -and $ver.Major -eq 3 -and $ver.Minor -ge 10) {
            $pythonExe  = $c.Exe
            $pythonArgv = $c.Args
            Write-Output "[sidecar] Python $verText via $pythonExe $($pythonArgv -join ' ')"
            break
        }
    }
}

if (-not $pythonExe) {
    throw "Python 3.10+ not found. Tried: py -3.12, py -3.11, py -3.10, python."
}

# --- 2. Clean venv + build under $env:TEMP ------------------------------------
$tmpRoot = Join-Path $env:TEMP ("rad-sidecar-" + [guid]::NewGuid().ToString('N'))
$venvDir = Join-Path $tmpRoot 'venv'
$distDir = Join-Path $tmpRoot 'dist'

try {
    New-Item -ItemType Directory -Path $tmpRoot | Out-Null
    Write-Output "[sidecar] Temp build dir: $tmpRoot"

    Write-Output "[sidecar] Creating clean venv"
    Invoke-Checked $pythonExe ($pythonArgv + @('-m', 'venv', $venvDir))

    $venvPython = Join-Path $venvDir 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "venv python not found: $venvPython"
    }

    # Install editable package with dev extras from the repo root, then
    # PyInstaller into the isolated venv. PyInstaller is deliberately not part
    # of the runtime/dev dependency set (rad stays dependency-free).
    Push-Location $repoRoot
    try {
        Write-Output "[sidecar] pip install (venv): -U pip, -e '.[dev]', pyinstaller"
        Invoke-Checked $venvPython @('-m', 'pip', 'install', '--upgrade', 'pip')
        Invoke-Checked $venvPython @('-m', 'pip', 'install', '-e', '.[dev]')
        Invoke-Checked $venvPython @('-m', 'pip', 'install', 'pyinstaller')
    } finally {
        Pop-Location
    }

    Write-Output "[sidecar] PyInstaller onefile build (console app = the rad CLI)"
    Invoke-Checked $venvPython @(
        '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        '--onefile',
        '--name', 'rad',
        '--collect-all', 'rad',
        '--collect-submodules', 'rad',
        '--distpath', $distDir,
        '--specpath', $tmpRoot,
        (Join-Path $repoRoot 'rad\__main__.py')
    )

    $builtExe = Join-Path $distDir 'rad.exe'
    if (-not (Test-Path -LiteralPath $builtExe)) {
        throw "PyInstaller output not found: $builtExe"
    }

    # --- 3. Install into the Tauri externalBin directory ----------------------
    if (-not (Test-Path -LiteralPath $binDir)) {
        New-Item -ItemType Directory -Path $binDir | Out-Null
    }
    Copy-Item -LiteralPath $builtExe -Destination $outPath -Force

    $sizeBytes = (Get-Item -LiteralPath $outPath).Length
    $sizeMb    = [math]::Round($sizeBytes / 1MB, 2)
    Write-Output "[sidecar] OK: $outPath ($sizeMb MB)"
    Write-Output "[sidecar] Smoke: $outPath"
    Write-Output "[sidecar] Tauri calls the sidecar directly (no -m / --module)."
}
finally {
    if (Test-Path -LiteralPath $tmpRoot) {
        Remove-Item -LiteralPath $tmpRoot -Recurse -Force
        Write-Output "[sidecar] Cleaned temp build dir $tmpRoot"
    }
}