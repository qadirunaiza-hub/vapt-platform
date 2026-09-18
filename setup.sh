#!/usr/bin/env bash
set -euo pipefail

echo "=== VAPT Platform Setup ==="

# Copy env file
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[+] .env created from template. Edit it before production use."
fi

# Generate a random SECRET_KEY
SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s|change-me-in-production-use-openssl-rand-hex-32|${SECRET}|" .env
echo "[+] SECRET_KEY generated."

# Pull scanner images (optional, will be pulled on first use)
echo "[*] Pulling scanner Docker images (may take a while)…"
docker pull ghcr.io/zaproxy/zaproxy:stable || echo "[!] ZAP pull skipped"
docker pull aquasec/trivy:latest || echo "[!] Trivy pull skipped"

echo "[+] Building and starting services…"
docker compose up --build -d

echo ""
echo "=== VAPT Platform is starting ==="
echo "  Frontend:  http://localhost:3000"
echo "  API docs:  http://localhost:8000/api/docs"
echo "  API base:  http://localhost:8000/api/v1"
echo ""
echo "First-time setup: register an account at http://localhost:3000"
echo "Then add authorized targets and start scanning."
