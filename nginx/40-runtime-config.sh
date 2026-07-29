#!/bin/sh
set -eu

api_base_url="${API_BASE_URL:-http://backend:8000/api/v1}"
escaped_api_base_url="$(printf '%s' "$api_base_url" | sed 's/\\/\\\\/g; s/"/\\"/g')"

printf 'window.__APP_CONFIG__ = Object.freeze({ API_BASE_URL: "%s" });\n' \
  "$escaped_api_base_url" > /tmp/runtime-config.js
