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
    parser.add_argument('--format', default='grimoirelab',
                        help="Import file format (default grimoirelab)")

    return parser.parse_args()


def fetch_model(model_name):
    """ Fetch a data model from Meditor and convert it to JSON """

    def fetch_goal(goal_orm):
        goal_json = {"name": goal_orm.name, "attributes": [], "subgoals": []}

        for attribute_orm in goal_orm.attributes.all():
            attribute_json = {"name": attribute_orm.name,
                              "description": attribute_orm.description,
                              "metrics": [],
                              "factoids": []}

            for metric_orm in attribute_orm.metrics.all():
                data_source_type_name = None
                if metric_orm.data_source_type:
                    data_source_type_name = metric_orm.data_source_type.name

                metric_json = {
                    "name": metric_orm.name,
                    "data_source_type": data_source_type_name,
                    "mclass": metric_orm.mclass

                }
                attribute_json['metrics'].append(metric_json)

            for factoid_orm in attribute_orm.factoids.all():
                data_source_type_name = None
                if factoid_orm.data_source_type:
                    data_source_type_name = factoid_orm.data_source_type.name

                factoid_json = {
                    "name": factoid_orm.name,
                    "data_source_type": data_source_type_name

                }
                attribute_json['factoids'].append(factoid_json)


            goal_json['attributes'].append(attribute_json)

        for subgoal_orm in goal_orm.subgoals.all():
            subgoal_json = fetch_goal(subgoal_orm)
            goal_json['subgoals'].append(subgoal_json)

        return goal_json


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

        goal_json = fetch_goal(goal_orm)


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


def gl2ossmeter(gl_models_json, model_name=None):
    """ Convert a GrimoireLab JSON quality model to OSSMeter format """

    def goal2qa(goal):
        qaspect = {"qualityAspects": [], "name": goal['name'], "attributes": []}

        for attribute in goal['attributes']:
            qa_attribute = {"name": attribute['name'],
                            "description": attribute['description'],
                            "metrics": [],
                            "factoids": []
                           }
            for metric in attribute['metrics']:
                qa_attribute['metrics'].append(metric['name'])
            for factoid in attribute['factoids']:
                qa_attribute['factoids'].append(factoid['name'])

            qaspect["attributes"].append(qa_attribute)

        if 'subgoals' in goal:
            for subgoal in goal['subgoals']:
                subqaspect = goal2qa(subgoal)
                qaspect['qualityAspects'].append(subqaspect)

        return qaspect


    ossmodel_json = {"qualityModel": {"qualityAspects": []}}
    gl_model_json = {}

    gl_models_json = gl_models_json['qualityModels']

    if not model_name:
        gl_model_json = gl_models_json[0]
    else:
        for model in gl_models_json:
            if gl_models_json['name'] == model_name:
                gl_model_json = model
                break
        if not gl_model_json:
            logging.error("Can not find model %s to export", model_name)
            raise RuntimeError("Can not find model %s to export" % model_name)

    ossmodel_json["qualityModel"]['name'] = gl_model_json['name']

    for goal in gl_model_json['goals']:
        qualityAspect = goal2qa(goal)
        ossmodel_json['qualityModel']['qualityAspects'].append(qualityAspect)

    return ossmodel_json


def show_report(models_json):

    def report_goal(goal, nattributes, nmetrics, nfactoids, ngoals):
        for attribute in goal['attributes']:
            nattributes += 1
            nmetrics += len(attribute['metrics'])
            nfactoids += len(attribute['factoids'])

        if 'subgoals' in goal:
            for subgoal in goal['subgoals']:
                ngoals += 1
                (nattributes, nmetrics, nfactoids, ngoals) = \
                    report_goal(subgoal, nattributes, nmetrics, nfactoids, ngoals)

        return (nattributes, nmetrics, nfactoids, ngoals)

    nmodels = 0
    ngoals = 0
    nattributes = 0
    nmetrics = 0
    nfactoids = 0

    for model in models_json['qualityModels']:
        nmodels += 1
        for goal in model['goals']:
            ngoals += 1
            (nattributes, nmetrics, nfactoids, ngoals) = \
                report_goal(goal, nattributes, nmetrics, nfactoids, ngoals)

    print("Models:", nmodels)
    print("Goals:", ngoals)
    print("Attributes:", nattributes)
    print("Metrics:", nmetrics)
    print("Factoids:", nfactoids)


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
                models_json = fetch_models(args.model)
            else:
                logging.info("Exporting all models to file %s", args.file)
                models_json = fetch_models()

            show_report(models_json)

            if args.format == 'ossmeter':
                models_json = gl2ossmeter(models_json)

            json.dump(models_json, fmodel, indent=True, sort_keys=True)
        except Exception:
            os.remove(args.file)
            raise

    logging.debug("Total exporting time ... %.2f sec", time() - task_init)
