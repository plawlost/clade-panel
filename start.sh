#!/bin/bash

# Function to check if Conda is installed
check_conda_installed() {
    type conda >/dev/null 2>&1 || { echo >&2 "Conda is not installed."; return 1; }
}

# Install Conda if it is not installed
install_conda() {
    echo "Installing Miniconda..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p $HOME/miniconda
    export PATH="$HOME/miniconda/bin:$PATH"
    echo 'export PATH="$HOME/miniconda/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
    conda init bash
    echo "Miniconda installed."
}

# Check if Conda is installed, install if not
if ! check_conda_installed; then
    install_conda
fi

# Deactivate any active environments
conda deactivate

# Remove existing environment if it exists
conda remove --name clade_panel --all -y

# Create a new Conda environment
conda create --name clade_panel python=3.12.2 -y

# Activate the new environment
conda activate clade_panel

pip uninstall -r requirements.txt -y

conda install -c plotly plotly

pip install streamlit-autorefresh
# Install required Python packages from requirements.txt
pip install altair<5
pip install streamlit>=1.20.0
pip install -r requirements.txt -y

# Set up the database
python -c "
import sqlite3
conn = sqlite3.connect('clade_ai.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        email TEXT
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name TEXT,
        assigned_to TEXT,
        deadline DATETIME,
        status TEXT,
        description TEXT,
        priority TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        username TEXT,
        comment TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()
"

# Install system dependencies (if needed)
xcode-select --install

# Install additional Python packages (if needed)
pip install watchdog

# Run the Streamlit application
streamlit run main.py
