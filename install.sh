#!/bin/bash
set -e

useDocker=true

echo "Use neo4j docker instead of local neo4j server instance?"
select yn in "Yes" "No"; do
    case $yn in
        Yes|yes|Y|y ) break;;
        No|no|N|n   ) useDocker=false; break;;
    esac
done


echo "-> Step 1/3"
echo "Creating virtual environment in current folder..."
if [ -d venv ]; then
  echo "Virtual environment already existed skipping..."
else
  pip3 install virtualenv
  virtualenv venv
fi
source venv/bin/activate

echo
echo "-> Step 2/3"
echo "Install required packages..."
pip install -r requirements.txt
$useDocker && \
  pip install docker-compose


function wait-neo4j-start() {
    echo "Waiting for neo4j to start..."
    secs=10
    prefix="Browser will start in"
    suffix="seconds..."
    while [ $secs -gt 0 ]; do
       echo -ne "$prefix $secs $suffix\r"
       sleep 1
       : $((secs--))
    done
    echo
}

function start-docker() {
    rm -f ./.pass
    echo "Starting neo4j docker container..."
    echo "Warning: Data in this database will be erased once the container is removed!"
    echo "   This project if for demo only! **DO NOT** use this in production environment."
    docker-compose up -d
    echo "Use neo4j/<no password> to login when the borwser started."
    wait-neo4j-start
    echo "Bringing up the browser..."
    xdg-open "http://localhost:7474" &
    sleep 1
}

function start-local-neo4j() {
    echo -n Your local neo4j DB password:
    read -s password
    echo
    cat "$password" > ./.pass
    echo "Password saved to $(pwd)/.pass"
    echo "Please run 'neo4j' locally to start the database."
}

echo
echo "-> Step 3/3"
if $useDocker; then
  start-docker
else
  start-local-neo4j
fi

echo "Script finished successfully!"