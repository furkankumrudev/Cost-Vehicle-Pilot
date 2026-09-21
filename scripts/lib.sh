#!/usr/bin/env bash
# Shared helpers for the POSIX entry points. Sourced, never executed directly.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Git Bash on Windows uses the same .venv with a different layout.
if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
else
    PYTHON=""
fi

require_python() {
    if [ -z "$PYTHON" ]; then
        echo "Sanal ortam bulunamadi. Once README'deki kurulum adimlarini tamamlayin." >&2
        exit 1
    fi
}

require_web_deps() {
    if [ ! -d "web/node_modules" ]; then
        echo "Web bagimliliklari bulunamadi. Once web klasorunde npm ci calistirin." >&2
        exit 1
    fi
}

# Bands keep each search page small enough for the ingestion layer to paginate.
PRICE_BANDS="0-100000,100001-200000,200001-300000,300001-400000,400001-500000,500001-600000,600001-700000,700001-800000,800001-900000,900001-1000000,1000001-1100000,1100001-1200000,1200001-1300000,1300001-1400000,1400001-1500000,1500001-1600000,1600001-1700000,1700001-1800000,1800001-1900000,1900001-2000000,2000001-2250000,2250001-2500000,2500001-2750000,2750001-3000000,3000001-3250000,3250001-3500000,3500001-3750000,3750001-4000000,4000001-4250000,4250001-4500000,4500001-4750000,4750001-5000000,5000001-6000000,6000001-7500000,7500001-10000000,10000001-15000000,15000001+"
