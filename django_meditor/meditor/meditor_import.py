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

from time import time

import django
# settings.configure()
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_meditor.settings'
django.setup()

from meditor.models import Attribute, DataSourceType, Goal, Metric, MetricsModel

from meditor.meditor_export import show_report

def get_params():
    parser = argparse.ArgumentParser(usage="usage: meditor_import.py [options]",
                                     description="Import Metrics Models in Meditor")
    parser.add_argument('-g', '--debug', action='store_true')
    parser.add_argument("-f", "--file", required=True,
                        help="File path from which to load the Metrics Models")
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

    for model in models_json:
        mparams = {"name": model}
        model_orm = add(MetricsModel, **mparams)

        for goal in models_json[model]:
            gparams = {"name": goal}
            goal_orm = add(Goal, **gparams)
            model_orm.goals.add(goal_orm)

            for attribute in models_json[model][goal]:
                aparams = {"name": attribute}
                attribute_orm = add(Attribute, **aparams)
                goal_orm.attributes.add(attribute_orm)

                for metric in models_json[model][goal][attribute]:
                    dsparams = {"name": metric[1]}
                    data_source_orm = add(DataSourceType, **dsparams)
                    metparams = {"name": metric[0],
                                 "data_source_type": data_source_orm}
                    metric_orm = add(Metric, **metparams)
                    attribute_orm.metrics.add(metric_orm)

                attribute_orm.save()

            goal_orm.save()

        model_orm.save()


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
        models_json = json.load(fmodel)
        feed_models(models_json)

    show_report(models_json)

    logging.debug("Total importing time ... %.2f sec", time() - task_init)
