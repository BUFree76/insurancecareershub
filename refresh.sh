#!/usr/bin/env bash
# Daily refresh: rebuild jobs.json from SMA's live board (closed jobs drop off). If a host is configured later, add its deploy step below.
set -euo pipefail; cd "$(dirname "$0")"
python3 refresh_jobs.py
# Deploy (after host login), e.g. GitHub Pages: git add jobs.json && git commit -m "jobs refresh $(date +%F)" && git push
