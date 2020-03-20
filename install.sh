echo "-> Step 1/3"
echo "Creating virtual environment in current folder..."
virtualenv venv
./venv/bin/activate

echo
echo "-> Step 2/3"
echo "Install required packages..."
pip install -r requirements.txt

function start-docker() {
    echo "Starting neo4j docker container..."
    echo "Warning: Data in this database will be erased once the container is removed!"
    echo "   This project if for demo only! **DO NOT** use this in production environment."
    docker-compose up -d
}

function start-local-neo4j() {
    echo "Please run 'neo4j' locally to start the database."
}

echo
echo "-> Step 3/3"
echo "Use neo4j docker instead of local neo4j server instance?"
echo "- Yes(recommended) / No"
echo "Please input: "
select yn in "Yes" "No" "yes" "no", "y", "n", "Y", "N"; do
    case $yn in
        Yes|yes|Y|y ) start-docker; break;;
        No|no|N|n   ) break;;
    esac
done

echo "Script finished successfully!"