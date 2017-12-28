#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Export a Metrics Model to a file
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

import django
# settings.configure()
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_meditor.settings'
django.setup()

from meditor.models import QualityModel


def get_params():
    parser = argparse.ArgumentParser(usage="usage: meditor_export.py [options]",
                                     description="Export a Metrics Model to a file")
    parser.add_argument("-f", "--file", required=True,
                        help="File path in which to export the Metrics Models")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-m', '--model', help='Model to be exported. If not provided all models will be exported.')

    return parser.parse_args()


def fetch_model(model_name):
    """ Fetch a data model from Meditor and convert it to JSON """

    model_json = {}

    logging.debug("Fetch the model %s", model_name)

    try:
        model_orm = QualityModel.objects.get(name=model_name)
        model_json['name'] = model_orm.name
        model_json['goals'] = []
    except QualityModel.DoesNotExist:
        logging.error('Can not find model %s', model_name)
        raise

    for goal_orm in model_orm.goals.all():
        goal_json = {"name": goal_orm.name, "attributes": []}

        for attribute_orm in goal_orm.attributes.all():
            attribute_json = {"name": attribute_orm.name,
                              "description": attribute_orm.description,
                              "metrics": []}

            for metric in attribute_orm.metrics.all():
                metric_json = {
                    "name": metric.name,
                    "data_source_type": metric.data_source_type.name,
                    "mclass": metric.mclass

                }
                attribute_json['metrics'].append(metric_json)

            goal_json['attributes'].append(attribute_json)

        model_json['goals'].append(goal_json)

    return model_json


def fetch_models(model_name=None):
    models_json = {"qualityModels": []}

    if model_name:
        models_json["qualityModels"].append(fetch_model(model_name))
    else:
        models = QualityModel.objects.all()
        for model in models:
            models_json["qualityModels"].append(fetch_model(model.name))

    return models_json


def show_report(models_json):
    nmodels = 0
    ngoals = 0
    nattributes = 0
    nmetrics = 0

    for model in models_json['qualityModels']:
        nmodels += 1
        for goal in model['goals']:
            ngoals += 1
            for attribute in goal['attributes']:
                nattributes += 1
                nmetrics += len(attribute['metrics'])

    print("Models:", nmodels)
    print("Goals:", ngoals)
    print("Attributes:", nattributes)
    print("Metrics:", nmetrics)


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

    if os.path.isfile(args.file):
        logging.info("%s exists. Remove it before running.", args.file)
        sys.exit(0)

    with open(args.file, "w") as fmodel:
        try:
            if args.model:
                logging.info("Exporting model %s to file %s", args.model, args.file)
                model_json = fetch_models(args.model)
            else:
                logging.info("Exporting all models to file %s", args.file)
                model_json = fetch_models()

            json.dump(model_json, fmodel, indent=True, sort_keys=True)
            show_report(model_json)
        except Exception:
            os.remove(args.file)

    logging.debug("Total exporting time ... %.2f sec", time() - task_init)
