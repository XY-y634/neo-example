#!/bin/bash
set -e

source venv/bin/activate

echo "Shutting down docker container..."
docker-compose down 2> /dev/null || true
rm -f ./.neo_pass
