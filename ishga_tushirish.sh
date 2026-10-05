#!/bin/sh
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt -q
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
python dastur.py
