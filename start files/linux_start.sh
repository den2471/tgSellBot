#!/bin/bash
PYTHON=python3
VENV_DIR=".venv"
REQUIREMENTS="requirements.txt"

cd ..

# Проверяем существование .venv
if [ -d "$VENV_DIR/bin" ]; then
    echo "Found environment"
    source "$VENV_DIR/bin/activate"
    
    # Проверяем установленные зависимости
    if ! $PYTHON -m pip freeze | grep -q -f "$REQUIREMENTS"; then
        echo "Setting up dependencies..."
        $PYTHON -m pip install -r "$REQUIREMENTS"
    else
        echo "Dependencies installed."
    fi
else
    echo "Creating environment..."
    $PYTHON -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "Setting up dependencies..."
    $PYTHON -m pip install -r "$REQUIREMENTS"
fi

# Запуск бота
echo "Starting bot..."
$PYTHON bot.py