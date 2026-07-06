@echo off
setlocal

set ROOT=%~dp0.. 
set ROOT=%ROOT:~0,-1%
cd /d "%ROOT%"

set PYTHON_EXE=.venv\Scripts\python.exe
set PORT=8002
set HEALTH_URL=http://localhost:%PORT%/health

echo ==========================================
echo 🏥 Starting MCP Servers
echo ==========================================
echo.
echo 🚀 Starting Medical Knowledge Base Server on port %PORT%...
start "MedicalKB" /B "%PYTHON_EXE%" mcp_servers\medical_kb.py

for /L %%i in (1,1,20) do (
    curl.exe -s %HEALTH_URL% >nul 2>&1
    if not errorlevel 1 goto started
    timeout /t 1 /nobreak >nul
)

:started
echo ✅ Medical Knowledge Base Server is running

echo.
echo ==========================================
echo ✅ MCP Servers started successfully
echo ==========================================
echo.
echo Available endpoints:
echo    - %HEALTH_URL%
echo    - http://localhost:%PORT%/tools/find_diseases
echo.
echo Press Ctrl+C to stop the server.

:wait_loop
ping 127.0.0.1 -n 2 >nul
goto wait_loop