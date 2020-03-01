#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Bitergia
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#   Valerio Cosentino <valcos@bitergia.com>
#
#

import argparse
import logging
import os


from time import time

import requests

import django
# settings.configure()
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_prosoul.settings'
django.setup()

from prosoul.models import DataSourceType, Metric


def get_params():
    parser = argparse.ArgumentParser(usage="usage: metrics_import.py [options]",
                                     description="Load CROSSMINER metrics definition in Prosoul")
    parser.add_argument("-e", "--elastic-url", required=True,
                        help="Elasticsearch URL with the metrics")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-i', '--index', required='True', help='Index with the metrics')

    return parser.parse_args()


def search_agg():
    query = """
    {
      "query": {
        "bool": {
          "must": []
        }
      },
      "size": 0,
      "aggs": {
        "2": {
          "terms": {
            "field": "metric_class",
            "size": 10000,
            "order": {
              "_count": "desc"
            }
          },
          "aggs": {
            "3": {
              "terms": {
                "field": "metric_name",
                "size": 10000,
                "order": {
                  "_count": "desc"
                }
              },
              "aggs": {
                "4": {
                  "terms": {
                    "field": "metric_name",
                    "size": 10000,
                    "order": {
                      "_count": "desc"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    return query


def process_agg(res):
    metrics = {}

    for data_source in res.json()["aggregations"]["2"]["buckets"]:
        if data_source['key'] not in metrics:
            metrics[data_source['key']] = {}

        for metric_class in data_source["3"]["buckets"]:
            if metric_class['key'] not in metrics[data_source['key']]:
                metrics[data_source['key']][metric_class['key']] = []

            for metric_name in metric_class["4"]["buckets"]:
                if len(metric_name['key'].split(":")) > 4:
                    # Bad metrics: 12:18:43:11:000_bugsConsidered
                    continue
                metrics[data_source['key']][metric_class['key']].append(metric_name['key'])

    return metrics


def add(cls_orm, **params):
    """ Add an object if it does not exists """

    obj_orm = None

    try:
        obj_orm = cls_orm.objects.get(**params)
        # logging.debug('Already exists %s: %s', cls_orm.__name__, params)
    except cls_orm.DoesNotExist:
        obj_orm = cls_orm(**params)
        try:
            obj_orm.save()
            logging.debug('Added %s: %s', cls_orm.__name__, params)
        except django.db.utils.IntegrityError as ex:
            logging.error("Can't add %s: %s", cls_orm.__name__, params)
            logging.error(ex)

    return obj_orm


def load_metrics(es_url, index):

    search_url = es_url + "/" + index + "/_search"

    res = requests.post(search_url, data=search_agg())

    metrics = process_agg(res)

    ndata_sources = 0
    nmetrics = 0

    for data_source in metrics:
        pparams = {"name": data_source}
        data_source_orm = add(DataSourceType, **pparams)

        ndata_sources += 1

        for metric_class in metrics[data_source]:
            metric_params = {"mclass": metric_class, "data_source_type": data_source_orm}
            for metric in metrics[data_source][metric_class]:
                metric_params["name"] = metric
                add(Metric, **metric_params)

                nmetrics += 1

        data_source_orm.save()

    return nmetrics


if __name__ == '__main__':

    task_init = time()

    args = get_params()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
        logging.debug("Debug mode activated")
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    nmetrics = load_metrics(args.elastic_url, args.index)

    logging.debug("Total loading time ... %.2f sec", time() - task_init)
    print("Metrics loaded", nmetrics)
