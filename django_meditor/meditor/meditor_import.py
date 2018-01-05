#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Import Metrics Models in Meditor
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

from django.test import TestCase

from meditor.models import Attribute, DataSourceType, Factoid, Goal, Metric, QualityModel

from meditor.meditor_export import fetch_models, gl2ossmeter, show_report

def get_params():
    parser = argparse.ArgumentParser(usage="usage: meditor_import.py [options]",
                                     description="Import Metrics Models in Meditor")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument("-f", "--file", required=True,
                        help="File path from which to load the Metrics Models")
    parser.add_argument('--format', default='grimoirelab',
                        help="Import file format (default grimoirelab)")
    parser.add_argument('-c', '--check', action='store_true',
                        help='Export the data and compare it with the imported')


    return parser.parse_args()


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


def feed_models(models_json):

    def feed_attribute(attribute):
        aparams = {"name": attribute['name']}
        if 'description' in attribute:
            aparams["description"] = attribute['description']
        attribute_orm = add(Attribute, **aparams)

        for subattribute in attribute['subattributes']:
            subattribute_orm = feed_attribute(subattribute)
            attribute_orm.subattributes.add(subattribute_orm)

        for metric in attribute['metrics']:
            data_source_orm = None
            if 'data_source_type' in metric and metric['data_source_type']:
                dsparams = {"name": metric['data_source_type']}
                data_source_orm = add(DataSourceType, **dsparams)
            metparams = {"name": metric['name'],
                         "data_source_type": data_source_orm}
            metric_orm = add(Metric, **metparams)
            attribute_orm.metrics.add(metric_orm)

        for factoid in attribute['factoids']:
            data_source_orm = None
            if 'data_source_type' in factoid and factoid['data_source_type']:
                dsparams = {"name": factoid['data_source_type']}
                data_source_orm = add(DataSourceType, **dsparams)
            fparams = {"name": factoid['name'],
                       "data_source_type": data_source_orm}
            factoid_orm = add(Factoid, **fparams)
            attribute_orm.factoids.add(factoid_orm)

        attribute_orm.save()

        return attribute_orm


    def feed_goal(goal):
        gparams = {"name": goal['name']}
        goal_orm = add(Goal, **gparams)

        for subgoal in goal['subgoals']:
            subgoal_orm = feed_goal(subgoal)
            goal_orm.subgoals.add(subgoal_orm)

        for attribute in goal['attributes']:
            attribute_orm = feed_attribute(attribute)
            goal_orm.attributes.add(attribute_orm)

        goal_orm.save()

        return goal_orm


    for model in models_json['qualityModels']:
        mparams = {"name": model['name']}
        if 'version' in model:
            mparams["version"] = model['version']
        model_orm = add(QualityModel, **mparams)

        for goal in model['goals']:
            goal_orm = feed_goal(goal)
            model_orm.goals.add(goal_orm)

        model_orm.save()

def alambic2gl(model_json):
    """ Convert a JSON from Alambic format to GrimoireLab """

    def build_attribute(attribute):
        """ The same attribute concept than in GrimoireLab """
        attribute_json = {"name": attribute['mnemo'], "subattributes": [],
                          "metrics": [], "factoids": []}
        for child in attribute['children']:
            if child['type'] == 'attribute':
                attribute_json['subattributes'].append(build_attribute(child))
            elif child['type'] == 'metric':
                metric_json = {"name": child['mnemo']}
                attribute_json['metrics'].append(metric_json)

        return attribute_json

    def build_goal(child):
        """ The first level attribute is a Goal in GrimoireLab """
        goal_json = {"name": child['mnemo'], "attributes": [],
                     "subgoals": []}

        for attribute in child['children']:
            # All all attributes with subattributes until metrics are reached
            attribute_json = build_attribute(attribute)
            goal_json["attributes"].append(attribute_json)

        return goal_json


    logging.debug('Converting from Alambic to GrimoireLab quality model')

    grimoirelab_json = {"qualityModels": []}

    gl_model_json = {"name": model_json["name"], "goals": [],
                     "version": model_json["version"]}

    for child in model_json['children']:
        # In alambic all are attributes
        # Convert the first level attribute to a goal
        goal_json = build_goal(child)

        gl_model_json["goals"].append(goal_json)

    grimoirelab_json["qualityModels"].append(gl_model_json)

    print(json.dumps(grimoirelab_json, indent=True))

    return grimoirelab_json


def ossmeter2gl(model_json):
    """ Convert a JSON from OSSMeter format to GrimoireLab """

    def build_goal(qualityAspect):
        # A qualityAspect is a Goal in GrimoireLab
        goal_json = {"name": qualityAspect['name'], "attributes": [],
                     "subgoals": []}

        for attribute_om in qualityAspect['attributes']:
            attribute_json = {"name": attribute_om['name'],
                              "description": attribute_om['description'],
                              "metrics": [], "factoids": []}
            for metric_om in attribute_om['metrics']:
                metrics_json = {"name": metric_om}
                attribute_json['metrics'].append(metrics_json)
            for factoid_om in attribute_om['factoids']:
                factoid_json = {"name": factoid_om}
                attribute_json['factoids'].append(factoid_json)

            goal_json["attributes"].append(attribute_json)

        if 'qualityAspects' in qualityAspect:
            for subqualityAspect in qualityAspect['qualityAspects']:
                subgoal_json = build_goal(subqualityAspect)
                goal_json["subgoals"].append(subgoal_json)

        return goal_json


    logging.debug('Converting from OSSMeter to GrimoireLab quality model')

    grimoirelab_json = {"qualityModels": []}

    model_json = model_json['qualityModel']

    gl_model_json = {"name": model_json["name"], "goals": []}

    for qualityAspect in model_json['qualityAspects']:
        goal_json = build_goal(qualityAspect)

        gl_model_json["goals"].append(goal_json)


    grimoirelab_json["qualityModels"].append(gl_model_json)

    return grimoirelab_json


def convert_to_grimoirelab(format_, model_json):
    """ Convert a json from supported format_ to grimoirelab format """

    grimoirelab_json = {}

    if format_ not in ['alambic', 'grimoirelab', 'ossmeter']:
        grimoirelab_json = models_json

    if format_ == 'grimoirelab':
        return models_json
    elif format_ == 'ossmeter':
        grimoirelab_json = ossmeter2gl(model_json)
    elif format_ == 'alambic':
        grimoirelab_json = alambic2gl(model_json)
    else:
        logging.error("Quality Model format not supported %s", format_)
        sys.exit(1)

    return grimoirelab_json


def compare_models(models_json, format_=None):
    # The MEditor database must only contains the models imported
    exported_models_json = fetch_models()
    if format_ == 'ossmeter':
        exported_models_json = gl2ossmeter(exported_models_json)
    test = TestCase()
    test.maxDiff = None
    test.assertDictEqual(models_json, exported_models_json)
    logging.info("Check completed")


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

    logging.info("Importing models from file %s", args.file)
    with open(args.file) as fmodel:
        import_models_json = json.load(fmodel)
        models_json = import_models_json
        if args.format != "grimoirelab":
            models_json = convert_to_grimoirelab(args.format, import_models_json)
        feed_models(models_json)

        show_report(models_json)

        logging.debug("Total importing time ... %.2f sec", time() - task_init)

        if args.check:
            logging.info('Checking data ...')
            compare_models(import_models_json, "ossmeter")
