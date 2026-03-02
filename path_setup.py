# path_setup.py (в корне проекта, рядом с main.py)
"""Настройка путей для импортов"""

import sys
import os

# Добавляем корневую папку проекта в sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"✅ Добавлен путь: {PROJECT_ROOT}")

# Добавляем все подпапки с __init__.py
for root, dirs, files in os.walk(PROJECT_ROOT):
    if '__init__.py' in files and root not in sys.path:
        sys.path.insert(0, root)
        print(f"✅ Добавлен путь: {root}")