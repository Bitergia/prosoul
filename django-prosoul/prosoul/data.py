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
