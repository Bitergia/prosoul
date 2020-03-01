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
#
#

import json
import logging
import os.path

import pkg_resources

PANELS_DIR = 'panels/templates'


class VizTemplatesData():

    def fetch(self):
        """
        Read available panel templates and return them

        :return: dict with the path to the template as key  and its content as value
        """

        # The template files could be located inside the pip package
        templates = pkg_resources.resource_listdir(__name__, PANELS_DIR)

        for tfilename in templates:
            if not tfilename.endswith(".json"):
                continue
            resource_path = '/'.join((PANELS_DIR, tfilename))
            if pkg_resources.resource_isdir(__name__, resource_path):
                continue
            tstring = pkg_resources.resource_string(__name__, resource_path).decode("utf-8")
            template = json.loads(tstring)['dashboard']['value']['title']
            yield (resource_path, template)

    @classmethod
    def read_template(self, tpath):
        """
        Read the contents of a template file trying to read it from the file system
        and if fails, as a resource inside a pip package.

        :param tpath: path to the template file/resource
        :return: a dict with the contents of the template
        """
        if os.path.isfile(tpath):
            template_file = open(tpath, "r")
            dashboard = json.load(template_file)
            template_file.close()
        else:
            logging.debug("Template file not found. Trying to load it from the pip package.")
            tstring = pkg_resources.resource_string(__name__, tpath).decode("utf-8")
            logging.debug("Template loaded from the pip package")
            dashboard = json.loads(tstring)

        return dashboard
