#!/bin/bash
# start.sh - Script de inicio para Render (free tier)
# Se ejecuta DESPUES del deploy, cuando la BD ya esta disponible

set -e  # Salir si hay error

echo "=== Iniciando aplicacion ==="

# 1. Ejecutar migraciones (idempotente, seguro en cada inicio)
echo "--- Aplicando migraciones ---"
python manage.py migrate --noinput

# 2. Crear superadmin de plataforma (idempotente: verifica si existe por email)
# SIN gimnasio asignado - gestiona toda la plataforma
echo "--- Verificando/Creando superadmin de plataforma ---"
python manage.py create_superadmin --force || echo "[WARN] create_superadmin falló (ver logs arriba), continuando..."

# 3. Crear admin de gimnasio (idempotente: verifica si existe por email)
# CON gimnasio asignado - gestiona un gimnasio especifico
echo "--- Verificando/Creando admin de gimnasio ---"
python manage.py create_production_admin --force || echo "[WARN] create_production_admin falló (ver logs arriba), continuando..."

# 4. Collectstatic (idempotente)
echo "--- Recopilando estaticos ---"
python manage.py collectstatic --noinput || true

# 5. Iniciar servidor
echo "--- Iniciando Gunicorn ---"
exec gunicorn gimnasio.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120