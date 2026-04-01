#!/usr/bin/env bash
# Salir si ocurre un error
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Recolectar archivos estáticos (CSS/JS/Imágenes)
python manage.py collectstatic --no-input

# Aplicar migraciones a la nueva base de datos PostgreSQL
python manage.py migrate