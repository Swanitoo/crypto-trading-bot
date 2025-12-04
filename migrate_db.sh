#!/bin/bash

# Script to migrate database using the virtual environment

# Activate virtual environment
source venv/bin/activate

# Run the migration script
python3 migrate_db.py
