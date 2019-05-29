#!/usr/bin/env python3
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
import csv
import dateutil
import json
import logging
import operator
import os

import requests

import django
# settings.configure()
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_prosoul.settings'
django.setup()

from grimoirelab_toolkit.datetime import (str_to_datetime)

import matplotlib.pyplot as plot

from elasticsearch import helpers, Elasticsearch

from prosoul.models import QualityModel
from prosoul.prosoul_utils import find_metric_name_field

ASSESSMENT_CSV_DIR_PATH = 'prosoul/static/prosoul/'
ASSESSMENT_CSV_FILE_NAME = 'assessment_csv.csv'
THRESHOLDS = ["Very Poor", "Poor", "Fair", "Good", "Very Good"]
HEADERS_JSON = {"Content-Type": "application/json"}
MAX_PROJECTS = 10000  # max number of projects to analyze
HTTPS_CHECK_CERT = False

SCORES = "_scores"
SCORE_QUARTERS = "_scores_by_quarters"
SCORES_QUARTER_TYPE = "quarter"
SCORES_ALL_TYPE = "all"


def get_params():
    parser = argparse.ArgumentParser(usage="usage: prosoul_assess.py [options]",
                                     description="Create a Kibana Dashboard to show a Quality Model")
    parser.add_argument("-e", "--elastic-url", required=True,
                        help="Elasticsearch URL with the metrics")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-i', '--index', required=True, help='Index with the metrics')
    parser.add_argument('-m', '--model', required=True,
                        help='Model to be used to build the Dashboard')
    parser.add_argument('-b', '--backend-metrics-data', default='grimoirelab',
                        help='Backend metrics data to use (grimoirelab, ossmeter, ...)')
    parser.add_argument('--from-date', default='1970-01-01',
                        help='Start date from which to compute the metrics (1970-01-01 by default)')
    parser.add_argument('--to-date', default='2100-01-01',
                        help='End date to compute the metrics (2100-01-01 by default)')
    parser.add_argument('--plot', action='store_true',
                        help='Show a plot with the metrics values')
    parser.add_argument('--csvfile', required=False,
                        help='Generate a CSV file with the scores of the assessment)')
    parser.add_argument('--attribute', help='Generate only the assessment for an attribute')

    return parser.parse_args()


def compute_metric_per_projects_grimoirelab(es_url, es_index, metric_field, metric_data, from_date, to_date):
    """
    In the current implementation the metrics supported are just counting metrics with
    an optional filtering defined in metric_params.

    :param es_url: Elasticsearch URL
    :param es_index: Elasticsearch index with the metrics
    :param metric_field: field to select the metrics data
    :param metric_data: data to compute the metric
    :param from_date: date from which to compute the metrics
    :return:
    """

    metric_name = metric_data.implementation
    metric_filter = ""  # filter needed to compute the metric
    metric_agg = ""  # aggregation needed to compute the metric
    agg_id = None  # id for the aggregation

    if metric_data.params:
        # In the params we can have filter or aggs
        params = json.loads(metric_data.params)
        # Build the filter if metric_params is defined
        if 'filter' in params:
            metric_filter = json.dumps(params['filter'])
        elif 'aggs' in params:
            agg_id = list(params['aggs'].keys())[0]
            metric_agg = json.dumps(params['aggs'])
            if metric_agg:
                metric_agg = ', "aggs": ' + metric_agg

    if from_date and to_date:
        from_date_iso = from_date
        to_date_iso = to_date
        filter_date = """
        {"range" :
            {
                "grimoire_creation_date" : {
                    "gte" : "%s",
                    "format": "yyyy-MM-dd"
                },
                "grimoire_creation_date" : {
                    "lte" : "%s",
                    "format": "yyyy-MM-dd"
                }
            }
        }
        """ % (from_date_iso, to_date_iso)
        metric_filter = metric_filter + "," + filter_date if metric_filter else filter_date

    if metric_filter:
        # Add a , to join this filter to the rest of filters
        metric_filter = ", " + metric_filter

    # Get the total aggregated value for a metrics in GrimoireLab
    project_metrics = []
    es_query = """
    {
      "size": 0,
      "aggs": {
        "3": {
          "terms": {
            "field": "project",
            "size": %i
          } %s
        }
      },
      "query": {
        "bool": {
          "must": [
            {
              "term": {
                "%s": "%s"
              }
            } %s
          ]
        }
      }
    }

    """ % (MAX_PROJECTS, metric_agg, metric_field, metric_name, metric_filter)

    logging.debug(json.dumps(json.loads(es_query), indent=True))

    res = requests.post(es_url + "/" + es_index + "/_search", data=es_query, verify=HTTPS_CHECK_CERT, headers=HEADERS_JSON)
    res.raise_for_status()

    project_buckets = res.json()["aggregations"]["3"]["buckets"]

    logging.info("Total projects found for %s: %i", metric_name, len(project_buckets))

    for pb in project_buckets:
        if not metric_agg:
            metric_value = pb["doc_count"]
            project_metrics.append({"project": pb['key'], "metric": metric_value})
        else:
            metric_value = pb[agg_id]['value']
            project_metrics.append({"project": pb['key'], "metric": metric_value})

    return project_metrics


def compute_metric_per_project_ossmeter(es_url, es_index, metric_field, metric_data, from_date, to_date):
    """
    Compute the non-normalized QM metric value for a given SCAVA metric (`metric_data`) stored in
    `es_url/es_index` between `from_date` and `to_date`. The value is the maximum of the SCAVA
    metric values in that given time range.

    :param es_url: URL of the ElasticSearch
    :param es_index: Metric index name (e.g., scava-metrics)
    :param metric_field: name of the metric field (e.g., metric_name)
    :param metric_data: name of the metric (e.g., commits, bugs)
    :param from_date: start date of the timeframe
    :param to_date: end date of the time frame
    """
    metric_name = metric_data.implementation
    calculation_type = metric_data.calculation_type

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
            },
            {
                "range": {
                    "datetime": {
                        "gte": "%s",
                        "format": "yyyy-MM-dd"
                    }
                }
            },
            {
                "range": {
                    "datetime": {
                        "lte": "%s",
                        "format": "yyyy-MM-dd"
                    }
                }
            }
          ]
        }
      },
      "aggs": {
        "3": {
          "terms": {
            "field": "project"
          },
    """ % (metric_field, metric_name, from_date, to_date)

    if calculation_type == 'median':
        es_query += """
            "aggs": {
                "2": {
                   "percentiles": {
                        "field": "metric_es_value",
                        "percents": [50]
                   }
                }
              }
            }
          }
        }"""
    elif calculation_type == 'last':
        es_query += """
            "aggs": {
                "2": {
                  "top_hits": {
                    "docvalue_fields": [
                      "metric_es_value"
                    ],
                    "_source": "metric_es_value",
                    "size": 1,
                    "sort": [
                      {
                        "datetime": {
                          "order": "desc"
                        }
                      }
                    ]
                  }
                }
              }
            }
        }
        }"""
    else:
        es_query += """
            "aggs": {
                "2": {
                  "%s": {
                    "field": "metric_es_value"
                  }
                }
              }
            }
          }
        }""" % calculation_type

    res = requests.post(es_url + "/" + es_index + "/_search", data=es_query, verify=HTTPS_CHECK_CERT, headers=HEADERS_JSON)
    res.raise_for_status()

    project_buckets = res.json()["aggregations"]["3"]["buckets"]
    for pb in project_buckets:
        if calculation_type == 'median':
            metric_value = pb["2"]["values"]['50.0']
        elif calculation_type == "last":
            metric_value = pb["2"]["hits"]["hits"][0]["fields"]["metric_es_value"][0]
        else:
            metric_value = pb["2"]["value"]
        project_metrics.append({"project": pb['key'], "metric": metric_value})

    return project_metrics


def compute_metric_per_project(es_url, es_index, metric_data, backend_metrics_data, from_date, to_date):
    """ Compute the value of a metric for all projects available """

    from_date_str = from_date.strftime('%Y-%m-%d')
    to_date_str = to_date.strftime('%Y-%m-%d')

    metric_per_project = None
    metric_field = find_metric_name_field(backend_metrics_data)
    if backend_metrics_data == "ossmeter":
        metric_per_project = compute_metric_per_project_ossmeter(es_url, es_index, metric_field, metric_data,
                                                                 from_date_str, to_date_str)
    elif backend_metrics_data == "grimoirelab":
        metric_per_project = compute_metric_per_projects_grimoirelab(es_url, es_index, metric_field, metric_data,
                                                                     from_date_str, to_date_str)
    elif backend_metrics_data == "scava-metrics":
        metric_per_project = compute_metric_per_project_ossmeter(es_url, es_index, metric_field, metric_data,
                                                                 from_date_str, to_date_str)

    return metric_per_project


def assess_attribute(es_url, es_index, attribute, backend_metrics_data, from_date, to_date):
    """
    Do the assessment for an attribute in the quality model. If a metric does not have thresholds,
    the score for it is 0.

    Given an attribute defined in the QM, all metrics are retrieved (i.e., QM metrics).
    Each QM metric value is the normalization on a 6-level threshold (i.e., 0-5) of the
    the maximum of the values of a given SCAVA metric between a `from_date` and `to_date`
    (see method `compute_metric_per_project`). The normalization is performed by comparing the
    maximum value obtained against each threshold level value (e.g., 20-40-60-80-100), if the
    value is greater than the threshold level value, the QM metric value is increased by one.

    :param es_url: Elasticsearch URL
    :param es_index: Index with the metrics data
    :param attribute: name of the attribute from which to compute the metrics
    :param backend_metrics_data: grimoirelab and ossmeter are the backend supported now
    :param from_date: initial date from which to compute the metrics
    :param from_date: end date from which to compute the metrics
    :return: a dict with metrics as keys and the projects score per each metric as value
    """
    logging.debug('Doing the assessment for attribute: %s', attribute.name)
    # Collect all metrics that are included in the models
    metrics_with_data = []
    atribute_assessment = {}  # Includes the assessment for each metric per project

    for metric in attribute.metrics.all():
        # We need the metric values and the metric indicators
        if metric.data:
            metric.data.calculation_type = metric.calculation_type
            metrics_with_data.append(metric)
        else:
            logging.debug("Can't find data for %s", metric.name)

    logging.debug("Metrics to be included: %s (%s attribute)", metrics_with_data, attribute.name)

    for metric in metrics_with_data:
        atribute_assessment[metric.data.implementation] = {}
        metric_value = compute_metric_per_project(es_url, es_index, metric.data, backend_metrics_data, from_date, to_date)
        if metric_value:
            for project_metric in metric_value:
                pname = project_metric['project']
                pmetric = project_metric['metric']
                logging.debug("Project %s metric %s value %i", pname, metric.data.implementation, pmetric)
                logging.debug("Doing the assessment ...")
                score = 0
                if metric.thresholds:
                    for threshold in metric.thresholds.split(","):
                        if project_metric['metric'] > float(threshold):
                            score += 1
                    threshold = score - 1 if score else 0
                    logging.debug("Score %s for %s: %i (%s)", project_metric['project'],
                                  metric.data.implementation, score, THRESHOLDS[threshold])
                if pname not in atribute_assessment[metric.data.implementation]:
                    atribute_assessment[metric.data.implementation][pname] = {}
                atribute_assessment[metric.data.implementation][pname]['score'] = score
                atribute_assessment[metric.data.implementation][pname]['raw_value'] = project_metric['metric']
                atribute_assessment[metric.data.implementation]['cal_type'] = metric.data.calculation_type
        else:
            logging.debug("Can't find value for for %s", metric)

    return atribute_assessment


def goals2projects(assessment):
    """
    Converts an goals assessment dict to a projects assessment dict

    :param assessment: the goal assessment dict
    :return: the project assessment dict
    """

    def check_project_dict(projects, project, goal, attr, metric):
        """ Check that the project dict has all the needed entries"""

        if project not in projects:
            project_dict = {}
        else:
            project_dict = projects[project]

        if goal not in project_dict:
            project_dict[goal] = {}

        if attr not in project_dict[goal]:
            project_dict[goal][attr] = {}

        if metric not in project_dict[goal][attr]:
            project_dict[goal][attr][metric] = {}

        return project_dict

    projects = {}

    for goal in assessment:
        for attr in assessment[goal]:
            for metric in assessment[goal][attr]:
                for project in assessment[goal][attr][metric]:
                    if project != 'cal_type':
                        projects[project] = check_project_dict(projects, project, goal, attr, metric)
                        projects[project][goal][attr][metric]['score'] = assessment[goal][attr][metric][project]['score']
                        projects[project][goal][attr][metric]['raw_value'] = assessment[goal][attr][metric][project][
                            'raw_value']
                        projects[project][goal][attr][metric]['cal_type'] = assessment[goal][attr][metric]['cal_type']

    return projects


def enrich_assessment(assessment):
    """
    Generate one item with a metric score for a project

    :param assessment: A dict with the results of the assessment
    :return:
    """
    for goal in assessment:
        for attr in assessment[goal]:
            for metric in assessment[goal][attr]:
                for project in assessment[goal][attr][metric]:
                    cal_type = assessment[goal][attr][metric]['cal_type']
                    if project != 'cal_type':
                        aitem = {
                            "goal": goal,
                            "attribute": attr,
                            "metric": metric,
                            "calculation_type": cal_type,
                            "project": project,
                            "score_" + metric: assessment[goal][attr][metric][project]['score'],
                            "score": assessment[goal][attr][metric][project]['score'],
                            "raw_value": assessment[goal][attr][metric][project]['raw_value']
                        }
                        yield aitem


def publish_assessment(es_url, scores_index, assessment, datetime_value, score_type=SCORES_ALL_TYPE):
    """
    Publish all the scores for the metrics in assessment in the
    target index: `es_index`+ '_scores' (e.g., scava-metrics_scores). Note
    that the target index is deleted and recreated every time, since the
    assessment is calculated on a given time span.

    An item in the target index is as the one below. It includes the name
    of the metric, attribute, goal, metric score normalized (i.e.,
    `score`, `score_Threads`) wrt the 6-level thresholds.

    {
        "_index" : "scava-metrics_scores",
        "_type" : "item",
        "_id" : "OtRLlmoBsN4hsIriFChp",
        "_score" : 1.0,
        "_source" : {
          "metric" : "Threads",
          "project" : "netty",
          "goal" : "activity",
          "score_Threads" : 5,
          "score" : 5,
          "attribute" : "interactions"
          "type": "all"/"quarter",
          "datetime": none/date
        }
      }

    :param es_url: URL for Elasticsearch
    :param scores_index: index in Elasticsearch
    :param assessment: dict with the assessment data
    :param datetime_value: start date of the quarter
    :param score_type: type of the score items (all or quarter)
    :return:
    """
    es_conn = Elasticsearch([es_url], timeout=100, verify_certs=HTTPS_CHECK_CERT)

    scores = []

    # Uploading info to the new ES
    for item in enrich_assessment(assessment):
        item['type'] = score_type
        item['datetime'] = datetime_value

        score = {
            "_index": scores_index,
            "_type": "item",
            "_source": item
        }
        scores.append(score)

    helpers.bulk(es_conn, scores)

    if es_conn.indices.exists(index=scores_index):
        es_conn.indices.refresh(index=scores_index)

    logging.info("Total scores published in %s: %i", scores_index, len(scores))

    return len(scores)


def __assess(es_url, es_index, model_name, backend_metrics_data, from_date, to_date, only_attribute=None):
    """
    Build the assessment for all projects

    :param es_url: Elasticsearch URL
    :param es_index: Elasticsearch index with the metrics data
    :param model_name: Quality model name
    :param backend_metrics_data: backend to be used for getting the metrics (ossmeter or grimoirelab)
    :param only_attribute: do the assessment only for this attribute
    :param from_date: date since which the metrics must be computed
    :param to_date: date until which the metrics must be computed
    :return: a dict with the assessment for all goals and attributes at projects level
    """
    assessment = {}  # Includes the assessment for each attribute

    # Check that the model exists
    model_orm = None
    try:
        model_orm = QualityModel.objects.get(name=model_name)
    except QualityModel.DoesNotExist:
        logging.error('Can not find the metrics model %s', model_name)
        RuntimeError('Can not find the metrics model %s' + model_name)

    for goal in model_orm.goals.all():
        assessment[goal.name] = {}
        for attribute in goal.attributes.all():
            if only_attribute and attribute.name != only_attribute:
                continue
            res = assess_attribute(es_url, es_index, attribute, backend_metrics_data, from_date, to_date)
            assessment[goal.name][attribute.name] = res

    logging.debug(json.dumps(assessment, indent=True))

    return assessment


def assess(es_url, es_index, model_name, backend_metrics_data, from_date, to_date, only_attribute=None):
    """
    Build the assessment for all projects from from-date to to-date and by quarters. The former is stored
    in scava-metrics_scores, the latter in scava-metrics_scores_by_quarters

    :param es_url: Elasticsearch URL
    :param es_index: Elasticsearch index with the metrics data
    :param model_name: Quality model name
    :param backend_metrics_data: backend to be used for getting the metrics (ossmeter or grimoirelab)
    :param only_attribute: do the assessment only for this attribute
    :param from_date: date since which the metrics must be computed
    :param to_date: date until which the metrics must be computed
    :return: a dict with the assessment for all goals and attributes at projects level
    """
    # delete the indexes, if they exist
    es_conn = Elasticsearch([es_url], timeout=100, verify_certs=HTTPS_CHECK_CERT)
    scores_index = es_index + SCORES
    scores_quarters_index = es_index + SCORE_QUARTERS

    if es_conn.indices.exists(index=scores_index):
        es_conn.indices.delete(index=scores_index)

    if es_conn.indices.exists(index=scores_quarters_index):
        es_conn.indices.delete(index=scores_quarters_index)

    # execute the assessment by quarter
    start_date = from_date

    while True:
        next_date = start_date + dateutil.relativedelta.relativedelta(months=+3)
        assessment = __assess(es_url, es_index, model_name, backend_metrics_data, start_date, next_date, only_attribute)
        publish_assessment(es_url, scores_quarters_index, assessment, start_date.isoformat(), score_type=SCORES_QUARTER_TYPE)

        if next_date > to_date:
            break

        start_date = next_date

    # execute the assessment over the full time frame
    assessment = __assess(es_url, es_index, model_name, backend_metrics_data, from_date, to_date, only_attribute)
    publish_assessment(es_url, scores_index, assessment, None, score_type=SCORES_ALL_TYPE)

    projects_data = goals2projects(assessment)
    dump_csv(projects_data)

    return assessment


def extract_metrics(qm_assessment):
    """
    Extract all metrics from a quality model assessment
    :param qm_assessment: a dict with the quality model assessment
    :return: a list with all the metrics
    """

    metrics = []

    for goal in qm_assessment:
        for attr in qm_assessment[goal]:
            for metric in qm_assessment[goal][attr]:
                metrics.append(qm_assessment[goal][attr][metric]['score'])

    return metrics


def build_project_big_number(project):
    """
    Get all metrics for a project and compute the average

    :param project: a dict with a project assessment
    :return: the average of all metrics
    """

    average = None
    metrics = []

    metrics = extract_metrics(project)
    average = sum(metrics) / len(metrics)
    average = round(average, 2)

    return average


def dump_csv(projects_data):
    """
    Dump the project metric scores to a CSV file

    :param csv_file: file in which to dump the projects metrics score data
    :param projects_data: dict with the projects metrics score
    :return:
    """

    fieldnames = ['project']
    # Get all score fields: we need to cross all projects to be sure all metrics are found
    for project in projects_data:
        for goal in projects_data[project]:
            for attr in projects_data[project][goal]:
                for metric in projects_data[project][goal][attr]:
                    if metric not in fieldnames:
                        fieldnames.append(metric)

    with open(ASSESSMENT_CSV_DIR_PATH + ASSESSMENT_CSV_FILE_NAME, 'w') as csvfile:  # Just use 'w' mode in 3.x
        csvwritter = csv.writer(csvfile)
        for project in projects_data:
            with open(ASSESSMENT_CSV_DIR_PATH + "assessment_csv_" + project + ".csv", 'w') as csvprojectfile:
                csvwritter_project = csv.writer(csvprojectfile)
                for goal in projects_data[project]:
                    for attr in projects_data[project][goal]:
                        for metric in projects_data[project][goal][attr]:
                            csvwritter.writerow([goal, attr, metric, project,
                                                 projects_data[project][goal][attr][metric]['cal_type'],
                                                 projects_data[project][goal][attr][metric]['raw_value'],
                                                 projects_data[project][goal][attr][metric]['score']])
                            csvwritter_project.writerow([goal, attr, metric, project,
                                                         projects_data[project][goal][attr][metric]['cal_type'],
                                                         projects_data[project][goal][attr][metric]['raw_value'],
                                                         projects_data[project][goal][attr][metric]['score']])


def build_report(assessment, kind):
    """

    :param assessment: dict with the goals assessment based on a quality model
    :param kind: kind of report to be built
    :param csv_file: export the metric scores to a CSV file
    :return: a dict with the report per each project
    """

    kinds = ['big_number']
    projects_report = {}

    if kind not in kinds:
        raise RuntimeError("Report kind not supported " + kind)

    if kind == 'big_number':
        # Average of all metrics
        projects_data = goals2projects(assessment)

        for project in projects_data:
            projects_report[project] = build_project_big_number(projects_data[project])

    return projects_report


def show_report(report_data, kind, plot_data=False):
    """

    Print in standard output a report based on report_data and kind

    :param report_data: a dict with the report data
    :param kind: kind of report in report_data
    :param plot_data: show a plot with the data
    :return:
    """

    kinds = ['big_number']
    plot_name = "Projects score"
    projects_report = {}

    if kind not in kinds:
        raise RuntimeError("Report kind not supported " + kind)

    sorted_report = sorted(report.items(), key=operator.itemgetter(1), reverse=True)
    for item in sorted_report:
        print(item)
    if plot_data:
        scores = [item[1] for item in sorted_report]
        x = range(0, len(scores))
        plot.plot(x, scores)
        plot.title(plot_name)
        plot.show()


if __name__ == '__main__':

    args = get_params()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
        logging.debug("Debug mode activated")
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    from_date = None if not args.from_date else str_to_datetime(args.from_date)
    to_date = None if not args.to_date else str_to_datetime(args.to_date)

    assessment = assess(args.elastic_url, args.index, args.model, args.backend_metrics_data,
                        from_date, to_date, args.attribute)
    report = build_report(assessment, "big_number")
    show_report(report, "big_number", args.plot)
