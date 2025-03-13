#!/bin/bash

# Cek apakah Laravel Echo Server sedang berjalan
if pgrep -x "uvicorn" > /dev/null
then
    echo "uvicorn sudah berjalan"
else
    echo "Uvicorn server berhenti. Memulai kembali..."
    sudo -u me bash -c "source /var/www/be/venv/bin/activate && cd /var/www/be && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
fi
