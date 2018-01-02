#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Tool for getting metrics from GrimoireLab Report
#
# Copyright (C) 2016 Bitergia
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
# Author:
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#

import argparse
import hashlib
import logging

from dateutil import parser

from grimoire_elk.elk.elastic import ElasticSearch

from report.metrics.git import Git
from report.report import Report

# From perceval
def uuid(*args):
    """Generate a UUID based on the given parameters.

    The UUID will be the SHA1 of the concatenation of the values
    from the list. The separator bewteedn these values is ':'.
    Each value must be a non-empty string, otherwise, the function
    will raise an exception.

    :param *args: list of arguments used to generate the UUID

    :returns: a universal unique identifier

    :raises ValueError: when anyone of the values is not a string,
        is empty or `None`.
    """
    def check_value(v):
        if not isinstance(v, str):
            raise ValueError("%s value is not a string instance" % str(v))
        elif not v:
            raise ValueError("value cannot be None or empty")
        else:
            return v

    s = ':'.join(map(check_value, args))

    sha1 = hashlib.sha1(s.encode('utf-8', errors='surrogateescape'))
    uuid_sha1 = sha1.hexdigest()

    return uuid_sha1


def fetch_metric(es_url, ds):

    start = parser.parse('2000-01-01')
    end = parser.parse('2018-01-01')

    metrics = Git.get_section_metrics()['overview']['activity_metrics']

    logging.debug("Computing metrics for %s: %s ", ds, metrics)

    for metric in metrics:
        es_index = Report.ds2index[Report.ds2class[ds]]
        ds = metric.ds.name
        m = metric(es_url, es_index, start=start, end=end)
        # print("AGG: ", m.get_agg())
        metric_ts = m.get_ts()
        for i in range(0, len(metric_ts['date'])):
            metric_sample = {
                "metric_id": m.id,
                "metric_name": m.name,
                "metric_es_name": m.name,
                "metric_description": m.desc,
                "metric_data_source": m.ds.name,
                "metric_value": metric_ts['value'][i],
                "metric_sample_datetime": metric_ts['date'][i],
                "metric_implementation": str(m),
                "project": None
            }
            metric_sample['id'] = uuid(metric_sample['metric_id'], metric_sample['metric_sample_datetime'])

            yield(metric_sample)
            # print(metric_ts)
        # print("TS: ", m.get_ts())
        # print("Trend:", m.get_trend())

def get_params():
    parser = argparse.ArgumentParser(usage="usage: metrics2es.py [options]",
                                     description="Feed GrimoireLab Metrics into Elasticsearch")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-e', '--elastic-url', required=True, help="Elastic URL with the enriched indexes")
    parser.add_argument('--elastic-metrics-url',
                        help="Elastic URL to store the metrics if different from enriched indexes.")
    parser.add_argument('-d', '--data-source', required=True, help="Get metrics for data source")

    return parser.parse_args()

if __name__ == '__main__':

    args = get_params()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(message)s')
        logging.debug("Debug mode activated")
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    data_source = args.data_source
    index = "grimoirelab_metrics"

    elastic = ElasticSearch(args.elastic_url, index)
    if args.elastic_metrics_url:
        elastic = ElasticSearch(args.elastic_metrics_url, index)

    elastic.bulk_upload_sync(fetch_metric(args.elastic_url, data_source), "id")


    #for metric in fetch_metric(es_url, data_source):
    #    print(metric)
