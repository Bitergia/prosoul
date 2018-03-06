# Change to the directory in which you have cloned 
# https://github.com/chaoss/grimoirelab-elk
# https://github.com/chaoss/grimoirelab-kidash
GIT_CLONES_DIR='/home/acs/devel/'

# P2O="p2o.py"
P2O="$GIT_CLONES_DIR/GrimoireELK/utils/p2o.py"
# KIDASH='kidash'
KIDASH_PYTHONPATH="$GIT_CLONES_DIR/grimoirelab-kidash:$GIT_CLONES_DIR/GrimoireELK"
KIDASH="$GIT_CLONES_DIR/grimoirelab-kidash/bin/kidash"
ES="http://localhost:9200"

# init.sh <github api token>
if [ -z "$1" ]
  then
    echo "init.sh <GITHUB_API_TOKEN>"
    exit
fi

echo "Loading the metrics data"
mysqladmin -u root create prosoul_sh
$P2O --enrich --db-sortinghat prosoul_sh --json-projects-map projects.json --index git-raw --index-enrich git git https://github.com/chaoss/grimoirelab-elk.git
$P2O --enrich --db-sortinghat prosoul_sh --json-projects-map projects.json --index git-raw --index-enrich git git https://github.com/chaoss/perceval.git
$P2O --enrich --db-sortinghat prosoul_sh --json-projects-map projects.json --index github-raw --index-enrich github_issues github chaoss perceval -t $1
$P2O --enrich --db-sortinghat prosoul_sh --json-projects-map projects.json --index github-raw --index-enrich github_issues github chaoss grimoirelab-elk -t $1

echo "Generating grimoirelab alias"
curl -XPOST -H "Content-Type: application/json" $ES/_aliases -d '
  {
  "actions" : [
                  {"add" : { "index" : "git",
                         "alias" : "grimoirelab" }},
                  {"add" : { "index" : "github_issues",
                         "alias" : "grimoirelab" }}
              ]
  }
'

echo "Loading the Visualization Templates"
export PYTHONPATH=$KIDASH_PYTHONPATH
$KIDASH --import git.json
$KIDASH --import github_issues.json
$KIDASH --import ../../django_prosoul/prosoul/panels/attribute-template-grimoirelab.json

echo "Loading the Quality Model"
PYTHONPATH=../../django_prosoul ../../django_prosoul/prosoul/prosoul_import.py -f ../../django_prosoul/prosoul/data/developer_model.json

