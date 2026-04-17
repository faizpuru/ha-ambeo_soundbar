#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/.."
apt-get update && apt-get install -y sqlite3 ffmpeg
git config --global --add safe.directory "${PWD}"
python3 -m pip install --requirement dev-requirements.txt
pre-commit install
