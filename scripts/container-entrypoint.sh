#!/bin/sh
set -eu

# SQLite relies on file locking that is not reliable on a Windows bind mount.
# Keep the source database read-only and copy it to the container filesystem.
if [ -n "${SOURCE_DB_PATH:-}" ] && [ -f "$SOURCE_DB_PATH" ]; then
    mkdir -p "$(dirname "$SQLITE_DB_PATH")"
    cp "$SOURCE_DB_PATH" "$SQLITE_DB_PATH"
fi

exec "$@"
