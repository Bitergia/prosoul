#!/usr/bin/env python3
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
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_prosoul.settings'
django.setup()

from prosoul.models import QualityModel


def get_params():
    parser = argparse.ArgumentParser(usage="usage: prosoul_export.py [options]",
                                     description="Export a Metrics Model to a file")
    parser.add_argument("-f", "--file", required=True,
                        help="File path in which to export the Metrics Models")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument('-m', '--model', help='Model to be exported. If not provided all models will be exported.')
    parser.add_argument('--format', default='grimoirelab',
                        help="Import file format (default grimoirelab)")

    return parser.parse_args()


def fetch_model(model_name):
    """ Fetch a data model from Prosoul and convert it to JSON """

    def fetch_attribute(attribute_orm):
        attribute_json = {"name": attribute_orm.name,
                          "description": attribute_orm.description,
                          "metrics": [],
                          "factoids": [],
                          "subattributes": []}

        for metric_orm in attribute_orm.metrics.all():
            data_source_type_name = None
            if metric_orm.data_source_type:
                data_source_type_name = metric_orm.data_source_type.name
            metric_data_implementation = None
            metric_data_params = None
            if metric_orm.data:
                metric_data_implementation = metric_orm.data.implementation
                metric_data_params = metric_orm.data.params

            metric_json = {
                "name": metric_orm.name,
                "description": metric_orm.description,
                "data_implementation": metric_data_implementation,
                "data_params": metric_data_params,
                "data_source_type": data_source_type_name,
                "thresholds": metric_orm.thresholds
            }
            attribute_json['metrics'].append(metric_json)

        for factoid_orm in attribute_orm.factoids.all():
            data_source_type_name = None
            if factoid_orm.data_source_type:
                data_source_type_name = factoid_orm.data_source_type.name

            factoid_json = {
                "name": factoid_orm.name,
                "description": factoid_orm.description,
                "data_source_type": data_source_type_name

            }
            attribute_json['factoids'].append(factoid_json)

        for subattribute_orm in attribute_orm.subattributes.all():
            attribute_json['subattributes'].append(fetch_attribute(subattribute_orm))

        return attribute_json

    def fetch_goal(goal_orm):
        goal_json = {"name": goal_orm.name, "description": goal_orm.description,
                     "attributes": [], "subgoals": []}

        for attribute_orm in goal_orm.attributes.all():
            goal_json['attributes'].append(fetch_attribute(attribute_orm))

        for subgoal_orm in goal_orm.subgoals.all():
            goal_json['subgoals'].append(fetch_goal(subgoal_orm))

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


def select_model(gl_models_json, model_name=None):
    """ Select a model from the list of avaialble models by model_name """

    gl_model_json = None

    gl_models_json = gl_models_json['qualityModels']

    if not model_name:
        gl_model_json = gl_models_json[0]
    else:
        for model in gl_models_json:
            if model['name'] == model_name:
                gl_model_json = model
                break
        if not gl_model_json:
            logging.error("Can not find model %s to export", model_name)
            raise RuntimeError("Can not find model %s to export" % model_name)

    return gl_model_json


def gl2viewer(gl_models_json, model_name=None):
    """ Convert a GrimoireLab JSON quality model to Alambic Viewer format """

    def extract_attributes(alambic_children):
        attributes = {}
        for child in alambic_children:
            if child['type'] == 'attribute':
                attributes[child['mnemo']] = {
                    "description": child['description'],
                    "mnemo": child['mnemo'],
                    "name": child['mnemo']
                }
                if 'children' in child:
                    attributes.update(extract_attributes(child['children']))

        return attributes

    def extract_metrics(alambic_children):
        metrics = {}
        for child in alambic_children:
            if child['type'] == 'metric':
                metrics[child['mnemo']] = {
                    "description": child['description'],
                    "mnemo": child['mnemo'],
                    "name": child['mnemo']
                }
            if 'children' in child and child['children']:
                metrics.update(extract_metrics(child['children']))

        return metrics

    viewer_json = {}
    alambic_json = gl2alambic(gl_models_json, model_name=model_name, description=True)

    attributes_json = {"children": extract_attributes(alambic_json['children'])}
    metrics_json = {"children": extract_metrics(alambic_json['children'])}

    viewer_json = [alambic_json]
    viewer_json.append(attributes_json)
    viewer_json.append(metrics_json)

    return viewer_json


def gl2alambic(gl_models_json, model_name=None, viewer=False):
    """
    Convert a GrimoireLab JSON quality model to Alambic format.
    Alambic format does not include name an description fields in its items,
    but these fields are needed for the Alambic web quality model viewer,
    so they are added if the model is going to be used in the quality model viewer.
    A bit hacky, but there is not a formal definition of the format, and in
    the quality model used as reference for Alambic, name and description
    do not exists.

    :param gl_models_json: Models in GrimoireLab format
    :param model_name: model to be converted (alambic only supports one)
    :param viewer: add extra fields needed by Alambic viewer
    :return: a dict with the model in alambic format
    """

    def attribute2child(attribute, viewer=False):
        """ Convert an Alambic child to an attribute """
        al_attribute = {"active": "true", "type": "attribute",
                        "mnemo": attribute['name'],
                        "children": []}
        if viewer:
            al_attribute["description"] = attribute['description']
            al_attribute["name"] = attribute['name']

        for metric in attribute['metrics']:
            al_metric = {"active": "true", "type": "metric",
                         "mnemo": metric['name']}
            if viewer:
                al_metric["description"] = metric['description']
                al_metric["name"] = metric['name']

            al_attribute['children'].append(al_metric)

        if 'subattributes' in attribute:
            for subattribute in attribute['subattributes']:
                al_attribute['children'].append(attribute2child(subattribute, viewer))

        return al_attribute

    def goal2atributte(goal, viewer=False):
        """ In Alambic goals are first level attributes """

        goal_attribute = {"active": "true", "type": "attribute",
                          "mnemo": goal['name'], "children": []}
        if viewer:
            goal_attribute["description"] = goal['description']
            goal_attribute["name"] = goal['name']

        for attribute in goal['attributes']:
            goal_attribute["children"].append(attribute2child(attribute, description))

        if 'subgoals' in goal:
            for subgoal in goal['subgoals']:
                goal_attribute["children"].append(goal2atributte(subgoal, description))

        return goal_attribute

    alambic_json = {"name": "", "version": "", "children": []}
    gl_model_json = select_model(gl_models_json, model_name)

    alambic_json['name'] = gl_model_json['name']
    alambic_json['version'] = '0.1'  # Version exported

    for goal in gl_model_json['goals']:
        alambic_child = goal2atributte(goal, description)
        alambic_json['children'].append(alambic_child)

    return alambic_json


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
    gl_model_json = select_model(gl_models_json, model_name)

    ossmodel_json["qualityModel"]['name'] = gl_model_json['name']

    for goal in gl_model_json['goals']:
        qualityAspect = goal2qa(goal)
        ossmodel_json['qualityModel']['qualityAspects'].append(qualityAspect)

    return ossmodel_json


def show_report(models_json):

    def report_attribute(attribute, nattributes, nmetrics, nfactoids):
        nmetrics += len(attribute['metrics'])
        if 'factoids' in attribute:
            nfactoids += len(attribute['factoids'])

        if 'subattributes' in attribute:
            for subattribute in attribute['subattributes']:
                nattributes += 1
                (nattributes, nmetrics, nfactoids) = \
                    report_attribute(subattribute, nattributes, nmetrics, nfactoids)
        return (nattributes, nmetrics, nfactoids)

    def report_goal(goal, nattributes, nmetrics, nfactoids, ngoals):
        for attribute in goal['attributes']:
            nattributes += 1
            (nattributes, nmetrics, nfactoids) = \
                report_attribute(attribute, nattributes, nmetrics, nfactoids)

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
            elif args.format == 'alambic':
                models_json = gl2alambic(models_json)
            elif args.format == 'viewer':
                models_json = gl2viewer(models_json)
            elif args.format == 'grimoirelab':
                models_json = models_json
            else:
                raise RuntimeError('Export format not supported ' + args.format)

            if args.format != 'viewer':
                json.dump(models_json, fmodel, indent=True)
            else:
                json.dump(models_json[0], fmodel, indent=True)
                logging.info('Generating extra files for attributes and metrics')
                # attributes_full.json
                attributes_file = os.path.join(os.path.dirname(fmodel.name), "attributes_full.json")
                with open(attributes_file, "w") as fattrs:
                    json.dump(models_json[1], fattrs, indent=True)
                # metrics_full.json
                metrics_file = os.path.join(os.path.dirname(fmodel.name), "metrics_full.json")
                with open(metrics_file, "w") as fmetrics:
                    json.dump(models_json[2], fmetrics, indent=True)

        except Exception:
            os.remove(args.file)
            raise

    logging.debug("Total exporting time ... %.2f sec", time() - task_init)
