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
import logging

from dateutil import parser

from report.metrics.git import Git
from report.report import Report

def compute_metric(es_url, ds):

    start = parser.parse('2000-01-01')
    end = parser.parse('2020-01-01')

    metrics = Git.get_section_metrics()['overview']['activity_metrics']

    logging.debug("Computing metrics for %s: %s ", ds, metrics)

    for metric in metrics:
        es_index = Report.ds2index[Report.ds2class[ds]]
        ds = metric.ds.name
        m = metric(es_url, es_index, start=start, end=end)
        print("AGG: ", m.get_agg())
        print("TS: ", m.get_ts())
        print("Trend:", m.get_trend())

def get_params():
    parser = argparse.ArgumentParser(usage="usage: metrics2es.py [options]",
                                     description="Feed GrimoireLab Metrics into Elasticsearch")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-e', '--elastic-url', required=True, help="Elastic URL with the enriched indexes")
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

    es_url = args.elastic_url
    data_source = args.data_source

    compute_metric(es_url, data_source)
