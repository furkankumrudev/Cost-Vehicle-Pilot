#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
require_python

SEGMENT="${SEGMENT:-general}"
CHECKPOINT="${CHECKPOINT:-data/runtime/daily_recent_checkpoint.json}"

echo "Pulling ${SEGMENT} listings from the last 24 hours..."
"$PYTHON" -m src.ingestion.recent_listing_scraper \
    --days 1 --filter-segments "$SEGMENT" --max-pages 0 --page-size 50 \
    --price-bands "$PRICE_BANDS" --delay-min 3 --delay-max 6 \
    --manual-wait-seconds 180 --max-old-pages 3 --max-stale-pages 0 \
    --max-repeated-pages 3 --stop-on-access \
    --checkpoint-path "$CHECKPOINT" "$@"

echo "Rebuilding cleaned analysis table..."
"$PYTHON" -m src.maintenance.clean_vehicle_data
