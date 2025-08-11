@echo off
chcp 1251 > nul
SET PYTHON=python
SET VENV_DIR=.venv
SET REQUIREMENTS=requirements.txt

:: Проверяем существование .venv
if exist "%VENV_DIR%\Scripts\activate" (
    echo Found environment
    call "%VENV_DIR%\Scripts\activate"
    
    :: Проверяем установленные зависимости
    %PYTHON% -m pip freeze | findstr /I /G:"%REQUIREMENTS%" > nul
    if %errorlevel% neq 0 (
        echo Setting up dependencies...
        %PYTHON% -m pip install -r %REQUIREMENTS%
    ) else (
        echo Dependencies installed
    )
) else (
    echo Creating environment...
    %PYTHON% -m venv %VENV_DIR%
    call "%VENV_DIR%\Scripts\activate"
    echo Setting up dependencies...
    %PYTHON% -m pip install -r %REQUIREMENTS%
)

:: Запуск бота
echo Starting bot...
%PYTHON% bot.py
pause