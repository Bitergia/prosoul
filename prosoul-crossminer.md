# Using prosoul in CROSSMINER

### Start Prosoul, Elasticsearch and Kibiter using docker


```
(acs@dellx) (master *% u=) ~/devel/prosoul/docker $ docker-compose up -d
Creating docker_prosoul_1
Creating docker_elasticsearch_1
Creating docker_kibiter_1
```
### Load  CROSSMINER Metrics Data

Following [the CROSSMINER guide](https://github.com/crossminer/crossminer/tree/dev/web-dashboards/ossmeter-metrics#ossmeter-metrics-dashboard):

```
(acs@dellx) ~/devel/crossminer $ git clone https://github.com/crossminer/crossminer
(acs@dellx) ~ $ sudo rm -rf  ~/oss-data/
(acs@dellx) ~ $ tar xfz devel/crossminer/crossminer/web-dashboards/data/mongo-ossmeter-dump.tgz
(acs@dellx) ~ $ docker-compose -f devel/crossminer/crossminer/web-dashboards/docker/ossmeter.yml up -d oss-db
(acs@dellx) ~ $ mongorestore dump
(acs@dellx) ~ $ rm -rf dump
(acs@dellx) ~ $ devel/crossminer/crossminer/web-dashboards/ossmeter-metrics/mongo2es.py -g -e http://localhost:9200 -i ossmeter --project perceval
(acs@dellx) ~ $ devel/crossminer/crossminer/web-dashboards/ossmeter-metrics/mongo2es.py -g -e http://localhost:9200 -i ossmeter --project GrimoireELK
```

### Load Kibana templates for Attributes and for CROSSMINER metrics dashboards
```
(acs@dellx) ~ $ kidash -e http://localhost:9200 --import ~/devel/crossminer/crossminer/web-dashboards/ossmeter-metrics/panels/ossmeter-metrics.json
(acs@dellx) ~ $ kidash -e http://localhost:9200 --import ~/devel/prosoul/django_prosoul/prosoul/panels/attribute-template.json
```

### Configure Quality Model for Viz and Assessment using Prosoul

The process is shown in [this video](https://raw.githubusercontent.com/Bitergia/prosoul/master/prosoul-viz-assess.webm).

* Import the [Developer Quality Model](https://github.com/Bitergia/prosoul/blob/master/django_prosoul/prosoul/data/developer_model.json) (DQM) using prosoul web editor
* Configure the data and thresholds for DQM metrics using prosoul web editor
 * Add the ossmeter metrics data: numberOfBugs, numberOfCommits, numberOfResolvedClosedBugs (pending the bugs without attention)
 * 0,10,100,500,1000: thresholds for numberOfBugs, numberOfResolvedClosedBugs
 * 0,100,1000,5000,10000: thresholds for numberOfCommits
* Create the DQM visualization using prosoul web
* Create the DQM assessment using prosoul web
