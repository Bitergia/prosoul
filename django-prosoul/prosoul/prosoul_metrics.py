#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ProSoul Metrics Manager Tool
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
import logging
import os
from statistics import mean, median, stdev

import matplotlib.pyplot as plot

import django
# settings.configure()
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_prosoul.settings'
django.setup()

from prosoul.models import QualityModel
from prosoul.prosoul_assess import compute_metric_per_project


def get_params():
    parser = argparse.ArgumentParser(usage="usage: mdashboard.py [options]",
                                     description="Create a Kibana Dashboard to show a Quality Model")
    parser.add_argument("-e", "--elastic-url", required=True,
                        help="Elasticsearch URL with the metrics")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-i', '--index', required=True, help='Index with the metrics')
    parser.add_argument('-m', '--model', required=True,
                        help='Model to be used to build the Dashboard')
    parser.add_argument('-b', '--backend-metrics-data', default='grimoirelab',
                        help='Backend metrics data to use (grimoirelab, ossmeter, ...)')
    parser.add_argument('-l', '--list', action='store_true', help='List available metrics')
    parser.add_argument('--metrics', nargs='*', help='Metrics names to be computed')
    parser.add_argument('--plot', action='store_true',
                        help='Show a plot with the metrics values (use it with --metric option)')

    return parser.parse_args()


def compute_metrics(names, es_url, es_index, model_name, backend_metrics_data):
    """
    Compute the value for a list of metrics
    :param names: list with the names of the metrics to be computed
    :return: a dict with the metric name as key and the metric values as value
    """

    metrics_values = {}

    for name in names:
        metrics_values[name] = compute_metric(name, es_url, es_index, model_name, backend_metrics_data)

    return metrics_values


def compute_metric(name, es_url, es_index, model_name, backend_metrics_data):
    """
    Compute the value for a metric

    :param name: name of the metric to be computed
    :param es_url: Elasticsearch URL
    :param es_index: index with the metrics data
    :param model_name: quality model name to be used
    :param backend_metrics_data: backend used to collect the metrics data
    :return: a list with the metric value per project
    """

    metrics = list_metrics(es_url, es_index, model_name, backend_metrics_data)
    metrics_name = [str(metric) for metric in metrics]

    # Check that the metric exists
    if name not in metrics_name:
        raise RuntimeError("metric %s not found (available %s)" % (name, metrics_name))

    # Check that the metric has data
    metric = None
    for m in metrics:
        if str(m) == name:
            metric = m
            break

    if not metric.data:
        raise RuntimeError("metric %s has no data" % name)

    # Time to compute the metric
    metric_value = compute_metric_per_project(es_url, es_index, metric.data, backend_metrics_data)

    return metric_value


def list_metrics(es_url, es_index, model_name, backend_metrics_data):
    """
    List available metrics

    :param es_url: Elasticsearch URL
    :param es_index: index with the metrics data
    :param model_name: quality model name to be used
    :param backend_metrics_data: backend used to collect the metrics data
    :return: a list with the metrics available

    """

    logging.debug("Listing the metrics available")

    metrics = []

    # Check that the model exists
    model_orm = None
    try:
        model_orm = QualityModel.objects.get(name=model_name)
    except QualityModel.DoesNotExist:
        RuntimeError('Can not find the metrics model %s' + model_name)

    for goal in model_orm.goals.all():
        for attribute in goal.attributes.all():
            for metric in attribute.metrics.all():
                metrics.append(metric)

    return metrics


def show_metric_stats(name, metric_project_values, plot_data=False):
    """
    Show a report in standard output about the values of a metric in all projects

    :param name: name of the metric to be plotted
    :param metric_value: dict with the value of the metric per each project
    :param plot_data: show a plot with the data
    :return:
    """

    metrics = []

    print("Total number of projects for %s: %i" % (name, len(metric_project_values)))
    for project in metric_project_values:
        metrics.append(project['metric'])

    if not metrics:
        return

    # Show the max, min, median, mean and standard deviation of the metric
    print("Max:", max(metrics), "Min:", min(metrics), "Mean:", round(mean(metrics), 2),
          "Median:", round(median(metrics), 2), "Stdev:", round(stdev(metrics), 2))

    if plot_data:
        # Plot the metrics
        x = range(0, len(metrics))
        plot.plot(x, metrics)
        plot.title(name)
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

    if args.list:
        metrics = list_metrics(args.elastic_url, args.index, args.model, args.backend_metrics_data)
        print(metrics)
    elif args.metrics:
        metrics_value = compute_metrics(args.metrics, args.elastic_url, args.index, args.model, args.backend_metrics_data)
        for name, metric_value in metrics_value.items():
            show_metric_stats(name, metric_value, plot_data=args.plot)
