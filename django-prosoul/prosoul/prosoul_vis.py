#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Create a Kibana Dashboard to show a Quality Model
#
# Copyright (C) Bitergia
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

import requests

import django
# settings.configure()
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_prosoul.settings'
django.setup()

from prosoul.data import VizTemplatesData
from prosoul.models import QualityModel
from prosoul.prosoul_assess import assess
from prosoul.prosoul_utils import find_metric_name_field

from kidash.kidash import feed_dashboard

ES_HEADERS = {"Content-Type": "application/json", "kbn-xsrf": "true"}
ASSESS_PANEL = 'panels/scava-projects-radar.json'


def get_params():
    parser = argparse.ArgumentParser(usage="usage: prosoul_vis.py [options]",
                                     description="Create a Kibana Dashboard to show a Quality Model")
    parser.add_argument("-e", "--elastic-url", default="http://localhost:9200",
                        help="Elasticsearch URL with the metrics (http://localhost:9200 by default)")
    parser.add_argument("-k", "--kibana-url", default="http://localhost:5601",
                        help="Kibana URL (http://localhost:9200 by default)")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-i', '--index', required='True', help='Index with the metrics')
    parser.add_argument('-t', '--template-file', required=True,
                        help='Dashboard template file to be used')
    parser.add_argument('--template-assess-file', default=ASSESS_PANEL,
                        help='Dashboard template file to be used for assessment')
    parser.add_argument('-m', '--model', required='True',
                        help='Model to be used to build the Dashboard')
    parser.add_argument('-b', '--backend-metrics-data', default='scava-metrics',
                        help='Backend metrics data to use (Scava metrics, grimoirelab, ossmeter, ...)')

    return parser.parse_args()


def build_filters(metrics, metric_name):
    # Basic filter template to be updated
    template = """
    [{"$state": {"store": "appState"},
      "meta": {
        "alias": null,
        "disabled": false,
        "index": "ossmeter",
        "key": "%s",
        "negate": false,
        "params": ["numberOfDocuments", "numberOfBugs"],
        "type": "phrases",
        "value": "numberOfDocuments, numberOfBugs"},
        "query": {"bool": {"minimum_should_match": 1,
                  "should": [{"match_phrase": {"%s": "metric1"}},
                             {"match_phrase": {"%s": "metric2"}}]}}},
      {"query": {"match_all": {}}}]
      """ % (metric_name, metric_name, metric_name)

    filter_json = json.loads(template)

    filter_json[0]['meta']['params'] = metrics
    filter_json[0]['meta']['value'] = ", ".join(metrics)
    filter_should = []
    for metric in metrics:
        filter_should.append({'match_phrase': {metric_name: metric}})
    filter_json[0]['query']['bool']['should'] = filter_should

    return filter_json


def create_alias(es_url, es_index, es_alias):
    """
    Create an alias in Elasticsearch

    :param es_url: Elasticsearch URL
    :param es_index: name of the index
    :param es_alias: name of the alias to be created
    :return:
    """

    add_alias = """{
        "actions": [
            {
                "add": {
                    "index": "%s",
                    "alias": "%s"
                }
            }
        ]
    }""" % (es_index, es_alias)

    res = requests.post(es_url + "/_aliases",
                        headers=ES_HEADERS,
                        data=add_alias, verify=False)
    try:
        res.raise_for_status()
        logging.debug("Created alias %s for index %s" % (es_alias, es_index))
    except requests.exceptions.HTTPError:
        logging.error("Can not create the alias %s for index %s" % (es_alias, es_index))
        raise


def build_dashboard(es_url, kibana_url, es_index, template_filename, goal, attribute,
                    backend_metrics_data):
    """
    Build a Kibana dashboard using as template template_filename showing the data for
    an attribute in a goal from the quality model.

    :param es_url: Elasticsearch URL
    :param kibana_url: Kibana URL
    :param es_index: index with the metrics data
    :param template_filename: template to be used to create the dashboard
    :param goal: quality model goal to be included
    :param attribute: atribute in the goal to be included
    :param backend_metrics_data: metrics backend to be used for getting the data
    :return: a dict with the dashboard created
    """

    logging.debug('Building the dashboard for the attribute: %s (goal %s)', attribute, goal)

    # Check that the model and the template dashboard exists

    # Collect metrics to be included in this attribute
    metrics_data = []

    for metric in attribute.metrics.all():
        if metric.data:
            metrics_data.append(metric.data.implementation)
        else:
            logging.warning("The metric %s does not have data", metric.name)

    logging.debug("Metrics to be included: %s", metrics_data)

    # Upload the dashboard created from the template dashboard
    logging.debug("Uploading the template panel %s", template_filename)
    dashboard = VizTemplatesData.read_template(template_filename)

    # An alias is created from the index with the metrics to the template index
    index_pattern_name = dashboard['index_patterns'][0]['id']
    create_alias(es_url, es_index, index_pattern_name)

    # Add the filters to the template dashboard and export it to Kibana
    search_json = json.loads(dashboard['dashboard']['value']['kibanaSavedObjectMeta']['searchSourceJSON'])
    metric_name = find_metric_name_field(backend_metrics_data)
    search_json['filter'] = build_filters(metrics_data, metric_name)
    dashboard['dashboard']['value']['kibanaSavedObjectMeta']['searchSourceJSON'] = json.dumps(search_json)
    dashboard['dashboard']['value']['title'] = goal.name + "_" + attribute.name
    dashboard['dashboard']['id'] = goal.name + "_" + attribute.name

    feed_dashboard(dashboard, es_url, kibana_url)

    logging.info('Created the attribute dashboard %s', dashboard['dashboard']['value']['title'])

    return dashboard


def build_menu(es_url, qm_menu, assessment_menu):
    """
    Build the menu to access the quality model dashboards

    :param es_url: Elasticsearch URL
    :param qm_menu: dict with the quality model menu to be created
    :param assessment_menu: dict with the assessment menu
    :return:
    """

    logging.debug("Creating the menu for accessing %s" % qm_menu)

    # {'Product_Vitality': 'Product_Vitality', 'Community_Attention': 'Community_Attention'}
    #
    # must be converted to
    #
    # {
    #   "metadashboard" : {
    #     "Community": {
    #       "Attention": "Community_Attention"
    #     },
    #     "Product": {
    #       "Vitality": "Product_Vitality"
    #     }
    #   }
    # }

    kibana_menu = {"metadashboard": {}}
    for entry in qm_menu.keys():
        [goal, attribute] = entry.split("_")
        if goal not in kibana_menu["metadashboard"]:
            kibana_menu["metadashboard"][goal] = {}
        kibana_menu["metadashboard"][goal][attribute] = qm_menu[entry]

    # Add the assessment dashboard
    kibana_menu["metadashboard"].update(assessment_menu)

    # First step is to fix the .kibana mapping to avoid dynamic mapping for the menu
    menu_mapping = """
    {
        "properties": {
            "metadashboard" : {
              "type": "object",
              "dynamic": "true"
            }
        }
    } """

    res = requests.put(es_url + "/.kibana/_mapping/doc", headers=ES_HEADERS, verify=False,
                       data=menu_mapping)
    res.raise_for_status()

    # Upload the menu created
    res = requests.put(es_url + "/.kibana/doc/metadashboard", headers=ES_HEADERS, verify=False,
                       data=json.dumps(kibana_menu))
    res.raise_for_status()
    logging.debug("Menu created: %s" % json.dumps(kibana_menu, indent=True))


def build_dashboards(es_url, kibana_url, es_index, template_file, template_assess_file,
                     model_name, backend_metrics_data):
    """
    Create all the dashboards needed to viz a Quality Model

    :param es_url: Elasticsearch URL
    :param kibana_url: Kibana URL
    :param es_index: index in elasticsearch with the metrics data
    :param template_file: template file to be used for building the attribute dashboards
    :param template_assess_file: template file to be used for the assessment dashboard
    :param model_name: quality model to use
    :param backend_metrics_data: backend to use to collect the metrics data
    :return:
    """

    logging.debug('Building the dashboards for the model: %s', model_name)

    if not template_assess_file:
        template_assess_file = ASSESS_PANEL

    qm_menu = {}  # Kibana menu for accessing the Quality Model dashboards
    assess_menu = {}  # Kibana menu for accessing the assessment dashboard

    # Check that the model and the template dashboard exists
    model_orm = None
    try:
        model_orm = QualityModel.objects.get(name=model_name)
    except QualityModel.DoesNotExist:
        logging.error('Can not find the metrics model %s', model_name)
        raise RuntimeError("Can not find the metrics model " + model_name)

    # Build a new dashboard for each attribute in the quality model
    for goal in model_orm.goals.all():
        for attribute in goal.attributes.all():
            dash_json = build_dashboard(es_url, kibana_url, es_index, template_file, goal,
                                        attribute, backend_metrics_data)
            qm_menu[dash_json['dashboard']['value']['title']] = dash_json['dashboard']['id']

    # Project assessment is included also in the viz
    assess(es_url, es_index, model_name, backend_metrics_data)
    # Upload the radar viz to show the assessment
    assess_dash = VizTemplatesData.read_template(template_assess_file)
    feed_dashboard(assess_dash, es_url, kibana_url)
    assess_menu[assess_dash['dashboard']['value']['title']] = assess_dash['dashboard']['id']

    build_menu(es_url, qm_menu, assess_menu)


if __name__ == '__main__':

    args = get_params()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
        logging.debug("Debug mode activated")
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    build_dashboards(args.elastic_url, args.kibana_url, args.index,
                     args.template_file, args.template_assess_file,
                     args.model, args.backend_metrics_data)
