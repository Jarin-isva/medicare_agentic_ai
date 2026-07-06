@echo off
REM Start all MCP servers in background
REM save this as: start_all_servers.bat

echo ================================================
echo 🚀 Starting MediGuide MCP Servers
echo ================================================

REM Activate virtual environment
call .venv\Scripts\activate

REM Start servers in separate windows
echo.
echo Starting Medical KB Server (Port 8001)...
start "MCP Server 1: Medical KB" python mcp_servers/medical_kb.py

timeout /t 2

echo Starting Emergency Detector (Port 8002)...
start "MCP Server 2: Emergency Detector" python mcp_servers/emergency_detector.py

timeout /t 2

echo Starting Care Network (Port 8003)...
start "MCP Server 3: Care Network" python mcp_servers/care_network.py

timeout /t 2

echo.
echo ================================================
echo ✅ All servers started!
echo ================================================
echo.
echo Servers running on:
echo   Port 8001: Medical KB
echo   Port 8002: Emergency Detector
echo   Port 8003: Care Network
echo.
echo Leave these windows open. They will keep running
echo even if you close other windows.
echo.
pause