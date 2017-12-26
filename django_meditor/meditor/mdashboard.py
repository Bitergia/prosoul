#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Create a Kibana Dashboard to show a Quality Model
#
# Copyright (C) 2017 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#

import argparse
import json
import logging
import os
import sys


from time import time

import requests

import django
# settings.configure()
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_meditor.settings'
django.setup()

from meditor.models import MetricsModel

from grimoire_elk.panels import search_dashboards, fetch_dashboard, feed_dashboard


def get_params():
    parser = argparse.ArgumentParser(usage="usage: mdashboard.py [options]",
                                     description="Create a Kibana Dashboard to show a Quality Model")
    parser.add_argument("-e", "--elastic-url", required=True,
                        help="Elasticsearch URL with the metrics")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-i', '--index', required='True', help='Index with the metrics')
    parser.add_argument('-t', '--template', required='True', help='Dashboard template to be used')
    parser.add_argument('-m', '--model', required='True',
                        help='Model to be used to build the Dashboard')

    return parser.parse_args()

def find_dash_id(es_url, dash_name):
    dash_id = None

    for dashboard in search_dashboards(es_url):
        if dashboard['title'] == dash_name:
            dash_id = dashboard['_id']
            logging.debug('Template dashboard found %s (%s)', dash_name, dash_id)
            break

    return dash_id


def build_filters(metrics, index):
    # Basic filter template to be updated
    template = """
    [{"$state": {"store": "appState"},
      "meta": {
        "alias": null,
        "disabled": false,
        "index": "ossmeter",
        "key": "metric_es_name.keyword",
        "negate": false,
        "params": ["numberOfDocuments", "numberOfBugs"],
        "type": "phrases",
        "value": "numberOfDocuments, numberOfBugs"},
        "query": {"bool": {"minimum_should_match": 1,
                  "should": [{"match_phrase": {"metric_es_name.keyword": "numberOfDocuments"}},
                             {"match_phrase": {"metric_es_name.keyword": "numberOfBugs"}}]}}},
      {"query": {"match_all": {}}}]
      """

    filter_json = json.loads(template)

    filter_json[0]['meta']['index'] = index
    filter_json[0]['meta']['params'] = metrics
    filter_json[0]['meta']['value'] = ", ".join(metrics)
    filter_should = []
    for metric in metrics:
        filter_should.append({'match_phrase': {'metric_es_name.keyword': metric}})
    filter_json[0]['query']['bool']['should'] = filter_should

    return filter_json



def build_dashboard(es_url, es_index, template_dashboard, model_name):
    logging.debug('Building the dashboard ... %s')

    # Check that the model and the template dashboard exists
    model_orm = None
    try:
        metric_params = {"name": model_name}
        model_orm = MetricsModel.objects.get(**metric_params)
    except MetricsModel.DoesNotExist:
        logging.error('Can not find the metrics model %s', model_name)
        sys.exit(1)

    # Collect all metrics that are included in the models
    metrics = []
    for goal in model_orm.goals.all():
        for attribute in goal.attributes.all():
            for metric in attribute.metrics.all():
                metrics.append(metric.name)

    logging.debug("Metrics to be included: %s", metrics)

    # Get the dashboard template to add to it the metric filters
    template_dashboard_id = find_dash_id(es_url, template_dashboard)
    if not template_dashboard_id:
        logging.error('Can not find the template dashboard %s', template_dashboard)
        sys.exit(1)

    # Add the filters to the template dashboard and export it to Kibana
    dashboard = fetch_dashboard(es_url, template_dashboard_id)
    search_json = json.loads(dashboard['dashboard']['value']['kibanaSavedObjectMeta']['searchSourceJSON'])
    search_json['filter'] = build_filters(metrics, es_index)
    dashboard['dashboard']['value']['kibanaSavedObjectMeta']['searchSourceJSON'] = json.dumps(search_json)
    dashboard['dashboard']['value']['title'] = dashboard['dashboard']['value']['title'] + "_" + model_name
    dashboard['dashboard']['id'] = dashboard['dashboard']['id'] + "_" + model_name


    feed_dashboard(dashboard, es_url)

    logging.info('Created Metrics Model dashboard %s', dashboard['dashboard']['value']['title'])



if __name__ == '__main__':

    args = get_params()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
        logging.debug("Debug mode activated")
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    dashboard_json = build_dashboard(args.elastic_url, args.index,
                                     args.template, args.model)
