#!/bin/bash
PYTHON=python3
VENV_DIR=".venv"
REQUIREMENTS="requirements.txt"

apt-get update
pip install --upgrade pip
apt install git -y

echo "Checking updates"
git init
git branch -D origin
git remote add origin https://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@github.com/den2471/tgSellBot
git fetch --all
git reset --hard origin/master
git pull origin main
exit

# Проверяем существование .venv
if [ -d "$VENV_DIR/bin" ]; then
    echo "Found environment"
    source "$VENV_DIR/bin/activate"
    
    # Проверяем установленные зависимости
    if ! $PYTHON -m pip freeze | grep -q -f "$REQUIREMENTS"; then
        echo "Setting up dependencies..."
        $PYTHON -m pip install -r "$REQUIREMENTS"
        apt-get install -y \
            libgl1 \
            libglib2.0-0 \
            libsm6 \
            libxrender1 \
            libxext6
    else
        echo "Dependencies installed."
    fi
else
    echo "Creating environment..."
    $PYTHON -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "Setting up dependencies..."
    $PYTHON -m pip install -r "$REQUIREMENTS"
    RUN apt-get install -y \
            libgl1 \
            libglib2.0-0 \
            libsm6 \
            libxrender1 \
            libxext6
fi

# Запуск бота
echo "Starting bot..."
$PYTHON bot.py