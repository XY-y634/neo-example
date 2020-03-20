#!/bin/bash
set -e

./install.sh

read -p "Press ENTER when neo4j instance in started..."
echo

python -m src

echo "Run './clean.sh' to remove Neo4j configs and DB completely!"
#./clean.sh
echo "Bye!"