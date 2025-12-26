@echo off
REM Admin Dashboard Launcher for Windows
REM This script starts the local-only admin dashboard at http://127.0.0.1:5000

setlocal enabledelayedexpansion

echo.
echo 🎬 Movies Recommendation - Admin Dashboard Launcher
echo ==================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "admin\app.py" (
    echo ❌ Please run this script from the MoviesRecommendation root directory
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "admin\.venv" (
    echo 📦 Creating virtual environment...
    python -m venv admin\.venv
    echo ✓ Virtual environment created
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call admin\.venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo 📥 Installing dependencies...
python -m pip install -q --upgrade pip
pip install -q -r admin\requirements.txt
echo ✓ Dependencies installed

REM Check for Excel file
if not exist "movies_master.xlsx" (
    echo.
    echo ⚠️  Warning: movies_master.xlsx not found in project root
    echo    The admin dashboard expects this file to exist.
    echo.
)

REM Check for data files
if not exist "data" (
    echo ⚠️  Warning: 'data' directory not found. Some features may not work.
)

echo.
echo ==================================================
echo ✅ Setup complete! Starting admin dashboard...
echo.
echo 📍 Local access: http://127.0.0.1:5000
echo 🔐 Not publicly accessible (local network only)
echo.
echo 💡 Features:
echo    • Edit movies_master.xlsx in web UI
echo    • Filter by status, language, region, completeness
echo    • Run enrichment pipeline
echo    • Generate and preview JSON
echo    • Manage backups
echo    • Publish to S3 (optional)
echo.
echo Press Ctrl+C to stop the server
echo ==================================================
echo.

REM Run Flask app
cd admin
python app.py

pause
