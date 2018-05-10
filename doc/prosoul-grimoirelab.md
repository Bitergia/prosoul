# Using prosoul with GrimoireLab

### Start Prosoul, Elasticsearch and Kibiter using docker

```
(acs@dellx) (master *% u=) ~/devel/prosoul/docker $ docker-compose up -d
Creating docker_prosoul_1
Creating docker_elasticsearch_1
Creating docker_kibiter_1
```

### Load  GrimoireLab Metrics Data

You need a GitHub API token in order to load GitHub data from GrimoireLab projects.

With the `prosoul/tests/grimoirelab/init.sh` script the data for projects is collected,
and the quality model for doing the assessment and visualization is loaded.

```
acs@~/devel/prosoul/tests/grimoirelab $ ./init.sh <github-api-token>
```

Once the script execution has finished, you have in Elasticsearch the projects data needed for
doing the assessment and visualization of them using ProSoul.

### Import the QualityModel

* Import the [Developer Quality Model](https://github.com/Bitergia/prosoul/blob/master/django_prosoul/prosoul/data/developer_model.json) using prosoul web editor

### Create the Visualization and Assessment using ProSoul web interface

Use the Visualize and Assess link in Prosoul web interface to generate them. 

In the web forms use:

* Elasticsearch URL: http://172.17.0.1:9200
* Kibana URL: http://172.17.0.1:5601
* Index with metrics data: grimoirelab
* Atribute Template: AttributeTemplateGrimoireLab