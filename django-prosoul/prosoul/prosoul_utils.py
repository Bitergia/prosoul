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

# Supported backends for providing the data for metrics in the quality models
BACKEND_METRICS_DATA = ['scava-metrics', 'grimoirelab', 'ossmeter']


def find_metric_name_field(backend_metrics_data):
    """ Find the field with the metric name for a given backend for metrics """

    if backend_metrics_data not in BACKEND_METRICS_DATA:
        raise RuntimeError('Backend for metrics data not supported: ' + backend_metrics_data)

    if backend_metrics_data == 'grimoirelab':
        metric_name = 'metadata__gelk_backend_name'
    elif backend_metrics_data == 'ossmeter':
        metric_name = 'metric_es_name'
    elif backend_metrics_data == 'scava-metrics':
        metric_name = 'metric_name'

    return metric_name
