#!/usr/bin/env bash
# Dev server launcher — restarts on crash, logs to tmp/dev_server.log
set -euo pipefail

mkdir -p tmp

echo "Starting dev server (Ctrl-C to stop)…"

while true; do
    {dev_server_command} 2>&1 | tee tmp/dev_server.log
    exit_code=${PIPESTATUS[0]}

    if [ "$exit_code" -eq 0 ]; then
        echo "Server exited cleanly."
        break
    fi

    echo "Server crashed (exit $exit_code). Restarting in 2 s…"
    sleep 2
done
