#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Assess a Software Project based on Quality Models
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
# import json
import logging
import os

import requests

import django
# settings.configure()
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_prosoul.settings'
django.setup()

from prosoul.models import QualityModel

from prosoul.prosoul_utils import find_metric_name_field

THRESHOLDS = ["Very Poor", "Poor", "Fair", "Good", "Very Good"]
HEADERS_JSON = {"Content-Type": "application/json"}


def get_params():
    parser = argparse.ArgumentParser(usage="usage: mdashboard.py [options]",
                                     description="Create a Kibana Dashboard to show a Quality Model")
    parser.add_argument("-e", "--elastic-url", required=True,
                        help="Elasticsearch URL with the metrics")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-i', '--index', required='True', help='Index with the metrics')
    parser.add_argument('-m', '--model', required='True',
                        help='Model to be used to build the Dashboard')
    parser.add_argument('-b', '--backend-metrics-data', default='grimoirelab',
                        help='Backend metrics data to use (grimoirelab, ossmeter, ...)')

    return parser.parse_args()


def compute_metric_per_projects_grimoirelab(es_url, es_index, metric_field, metric_name):
    # Get the total aggregated value for a metrics in GrimoireLab
    # Elasticsearch index with metrics

    project_metrics = []
    es_query = """
    {
      "size": 0,
      "aggs": {
        "3": {
          "terms": {
            "field": "project"
          }
        }
      },
      "query": {
        "bool": {
          "must": [
            {
              "term": {
                "%s": "%s"
              }
            }
          ]
        }
      }
    }

    """ % (metric_field, metric_name)

    # logging.debug(json.dumps(json.loads(es_query), indent=True))

    res = requests.post(es_url + "/" + es_index + "/_search", data=es_query, headers=HEADERS_JSON)
    res.raise_for_status()

    project_buckets = res.json()["aggregations"]["3"]["buckets"]
    for pb in project_buckets:
        metric_value = pb["doc_count"]
        project_metrics.append({"project": pb['key'], "metric": metric_value})

    return project_metrics


def compute_metric_per_project_ossmeter(es_url, es_index, metric_field, metric_name):
    # Get the total aggregated value for a metric in the OSSMeter
    # Elasticsearch index with metrics
    project_metrics = []
    es_query = """
    {
      "size": 0,
      "query": {
        "bool": {
          "must": [
            {
              "term": {
                "%s": "%s"
              }
            }
          ]
        }
      },
      "aggs": {
        "3": {
          "terms": {
            "field": "project.keyword"
          },
          "aggs": {
            "2": {
              "max": {
                "field": "metric_es_value"
              }
            }
          }
        }
      }
    }
    """ % (metric_field, metric_name)

    # logging.debug(json.dumps(json.loads(es_query), indent=True))

    res = requests.post(es_url + "/" + es_index + "/_search", data=es_query, headers=HEADERS_JSON)
    res.raise_for_status()

    project_buckets = res.json()["aggregations"]["3"]["buckets"]
    for pb in project_buckets:
        metric_value = pb["2"]["value"]
        project_metrics.append({"project": pb['key'], "metric": metric_value})

    return project_metrics


def compute_metric_per_project(es_url, es_index, metric_data, backend_metrics_data):
    """ Compute the value of a metric for all projects available """
    metric_name = metric_data
    metric_per_project = None
    metric_field = find_metric_name_field(backend_metrics_data)
    if backend_metrics_data == "ossmeter":
        metric_per_project = compute_metric_per_project_ossmeter(es_url, es_index, metric_field, metric_name)
    elif backend_metrics_data == "grimoirelab":
        metric_per_project = compute_metric_per_projects_grimoirelab(es_url, es_index, metric_field, metric_name)

    return metric_per_project


def assess_attribute(es_url, es_index, attribute, backend_metrics_data):
    logging.debug('Doing the assessment for attribute: %s', attribute.name)
    # Collect all metrics that are included in the models
    metrics_with_data = []
    atribute_assessment = {}  # Includes the assessment for each metric per project

    for metric in attribute.metrics.all():
        # We need the metric values and the metric indicators
        if metric.data:
            metrics_with_data.append(metric)
        else:
            logging.debug("Can't find data for %s", metric.name)

    logging.debug("Metrics to be included: %s (%s attribute)", metrics_with_data, attribute.name)

    for metric in metrics_with_data:
        metric_data = metric.data.implementation
        atribute_assessment[metric_data] = {}
        metric_value = compute_metric_per_project(es_url, es_index, metric_data, backend_metrics_data)
        if metric_value:
            for project_metric in metric_value:
                pname = project_metric['project']
                pmetric = project_metric['metric']
                logging.debug("Project %s metric %s value %i", pname, metric_data, pmetric)
                logging.debug("Doing the assesment ...")
                if metric.thresholds:
                    score = 0
                    for threshold in metric.thresholds.split(","):
                        if project_metric['metric'] > float(threshold):
                            score += 1
                logging.debug("Score %s for %s: %i (%s)", project_metric['project'],
                              metric_data, score, THRESHOLDS[score - 1])
                atribute_assessment[metric_data][pname] = score
        else:
            logging.debug("Can't find value for for %s", metric)

    return atribute_assessment


def assess(es_url, es_index, model_name, backend_metrics_data):
    logging.debug('Building the assessment for projects ...')

    assessment = {}  # Includes the assessment for each attribute

    # Check that the model exists
    model_orm = None
    try:
        model_orm = QualityModel.objects.get(name=model_name)
    except QualityModel.DoesNotExist:
        logging.error('Can not find the metrics model %s', model_name)
        RuntimeError('Can not find the metrics model %s' + model_name)

    for goal in model_orm.goals.all():
        for attribute in goal.attributes.all():
            res = assess_attribute(es_url, es_index, attribute, backend_metrics_data)
            assessment[attribute.name] = res

    return assessment


if __name__ == '__main__':

    args = get_params()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
        logging.debug("Debug mode activated")
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    assessment = assess(args.elastic_url, args.index, args.model, args.backend_metrics_data)

    print(assessment)
