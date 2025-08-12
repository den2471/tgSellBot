@echo off
chcp 65001 > nul
SET PYTHON=python
SET VENV_DIR=.venv
SET REQUIREMENTS=requirements.txt

echo Checking updates
start updateWin.bat

:: Check for Python
where %PYTHON% >nul 2>&1
if not %errorlevel% == 0 (
    echo Error: Python not found in PATH!
    pause
    exit /b 1
)

:: Check for requirements.txt
if not exist "%REQUIREMENTS%" (
    echo Error: %REQUIREMENTS% not found!
    pause
    exit /b 1
)

:: Clean old virtual environment if it exists
if exist "%VENV_DIR%" (
    echo Cleaning old virtual environment...
    rmdir /s /q "%VENV_DIR%"
)

:: Create fresh virtual environment
echo Creating fresh virtual environment...
%PYTHON% -m venv "%VENV_DIR%"
if not %errorlevel% == 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate environment
call "%VENV_DIR%\Scripts\activate.bat"
if not %errorlevel% == 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Check Python in virtual environment
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Error: Python not found in virtual environment
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_DIR%\Scripts\python.exe" -m pip install -r "%REQUIREMENTS%"

:: Start bot
echo Starting bot...
"%VENV_DIR%\Scripts\python.exe" bot.py
pause