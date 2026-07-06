$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$appFile = Join-Path $projectRoot "app.py"

if (-not (Test-Path $pythonExe)) {
    throw "Virtual environment was not found at $pythonExe"
}

& $pythonExe -m streamlit run $appFile --server.headless true
