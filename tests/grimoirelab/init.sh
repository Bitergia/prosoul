# init.sh <github api token>
if [ -z "$1" ]
  then
    echo "init.sh <GITHUB_API_TOKEN>"
fi
mysqladmin -u root create meditor_sh
p2o.py --enrich --db-sortinghat meditor_sh --json-projects-map projects.json --index git-raw --index-enrich git git https://github.com/chaoss/grimoirelab-elk.git
p2o.py --enrich --db-sortinghat meditor_sh --json-projects-map projects.json --index git-raw --index-enrich git git https://github.com/chaoss/perceval.git
p2o.py --enrich --db-sortinghat meditor_sh --json-projects-map projects.json --index github-raw --index-enrich github_issues github chaoss perceval -t $1
p2o.py --enrich --db-sortinghat meditor_sh --json-projects-map projects.json --index github-raw --index-enrich github_issues github chaoss grimoirelab-elk -t $1
kidash --import git.json
kidash --import github_issues.json
kidash --import ../../django_meditor/meditor/panels/attribute-template-grimoirelab.json
