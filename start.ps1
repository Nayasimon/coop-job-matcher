param([switch]$Test, [int]$Port = 8501)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonCommand = Join-Path $projectRoot '.venv\Scripts\python.exe'
$oldPythonPath = $env:PYTHONPATH
Push-Location $projectRoot
try {
    $working = $false
    if (Test-Path -LiteralPath $pythonCommand) {
        try {
            & $pythonCommand -c 'import streamlit, anthropic, dotenv' 2>$null
            $working = $LASTEXITCODE -eq 0
        } catch { $working = $false }
    }
    if (-not $working) {
        $pythonCommand = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        $installedPackages = Join-Path $projectRoot '.venv\Lib\site-packages'
        if (-not (Test-Path -LiteralPath $pythonCommand) -or -not (Test-Path -LiteralPath $installedPackages)) {
            throw 'Python environment is unavailable. Follow the fresh setup steps in README.md.'
        }
        $env:PYTHONPATH = $installedPackages
        & $pythonCommand -c 'import streamlit, anthropic, dotenv'
        if ($LASTEXITCODE -ne 0) { throw 'Dependencies are unavailable. Follow README.md setup.' }
    }
    if ($Test) {
        & $pythonCommand -m unittest discover -s tests -v
    } else {
        & $pythonCommand -m streamlit run app.py --server.address 127.0.0.1 --server.port $Port --server.headless true --browser.gatherUsageStats false
    }
    $result = $LASTEXITCODE
} finally {
    $env:PYTHONPATH = $oldPythonPath
    Pop-Location
}
exit $result
