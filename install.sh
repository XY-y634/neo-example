#!/bin/bash
set -e

echo "-> Step 0/3"
echo "Setting up parameters..."

useDocker=true
echo "Use neo4j docker instead of local neo4j server instance?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) break;;
        No  ) useDocker=false; break;;
    esac
done

if $useDocker; then
    openBrowser=false
    echo "Open browser after docker started?"
    select yn in "Yes" "No"; do
        case $yn in
            Yes ) openBrowser=true; break;;
            No  ) break;;
        esac
    done
fi

echo "Neo4j password (username 'neo4j')."
echo "Leave it to blank (press ENTER) equals disable Neo4j auth."
echo -n "Password: "
read -s password
echo
echo "$password" > ./.neo_pass
echo "Password saved to $(pwd)/.neo_pass"


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
    echo "Starting neo4j docker container..."
    echo "Warning: Data in this database will be erased once the container is removed!"
    echo "   This project if for demo only! **DO NOT** use this in production environment."
    [[ -z $password ]] && neoAuth="none" || neoAuth="neo4j/$password"
    echo "Starting Neo4j with AUTH: $neoAuth"
    # Don't show err msg and don't quit
    docker-compose down 2> /dev/null || true
    NEO4J_AUTH=$neoAuth docker-compose up -d
    if $openBrowser; then
        wait-neo4j-start
        echo "Bringing up the browser..."
        xdg-open "http://localhost:7474" &
        sleep 1
    fi
}

function start-local-neo4j() {
    echo "Please run 'neo4j' locally to start the database."
}

echo
echo "-> Step 3/3"
if $useDocker; then
  start-docker
else
  start-local-neo4j
fi

