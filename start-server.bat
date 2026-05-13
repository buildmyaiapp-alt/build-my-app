@echo off
title Build My App - Preview Server
color 0A

echo.
echo  ==============================================
echo    Build My App  --  Preview Server
echo  ==============================================
echo.

:: ── Try Python (Windows usually has "python", not "python3") ──────────────────
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo  Starting with Python...
    echo.
    python start-server.py
    goto :done
)

:: ── Try python3 ───────────────────────────────────────────────────────────────
python3 --version >nul 2>&1
if %errorlevel% == 0 (
    echo  Starting with Python3...
    echo.
    python3 start-server.py
    goto :done
)

:: ── Try Node.js ───────────────────────────────────────────────────────────────
node --version >nul 2>&1
if %errorlevel% == 0 (
    echo  Starting with Node.js...
    echo.
    node server.js
    goto :done
)

:: ── Nothing installed ─────────────────────────────────────────────────────────
echo  ERROR: Python and Node.js are both not installed.
echo.
echo  Please install one of these (free, takes 2 minutes):
echo.
echo    Python:   https://www.python.org/downloads/
echo              -- click "Download Python" -- run installer
echo              -- CHECK the box "Add Python to PATH"  ^<-- IMPORTANT
echo.
echo    Node.js:  https://nodejs.org/
echo              -- click "LTS" version -- run installer
echo.
echo  After installing, close this window and double-click
echo  start-server.bat again.
echo.
pause
goto :end

:done
echo.
echo  Server stopped.
pause

:end
