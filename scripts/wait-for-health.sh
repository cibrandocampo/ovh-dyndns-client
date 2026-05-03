#!/usr/bin/env sh
# Block until http://localhost:8000/health responds 200, or fail after $1
# seconds (default 30). Used by the project-root Makefile's `screenshots`
# target to gate the capture step on the API being ready.
set -u

URL="http://localhost:8000/health"
TIMEOUT="${1:-30}"

i=0
until curl -sf "$URL" > /dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge "$TIMEOUT" ]; then
        echo "timeout waiting for $URL after ${TIMEOUT}s" >&2
        exit 1
    fi
    sleep 1
done
echo "ready"
