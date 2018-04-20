import json

from os import listdir
from os.path import isfile, join


# PANELS_DIR = 'django_prosoul/prosoul/panels/'
PANELS_DIR = 'prosoul/panels/'


class VizTemplatesData():

    def fetch(self):
        """ Read available templates and return them """

        for tfilename in listdir(PANELS_DIR):
            if not isfile(join(PANELS_DIR, tfilename)):
                continue
            tfile = open(join(PANELS_DIR, tfilename))
            template = json.load(tfile)['dashboard']['value']['title']
            yield (join(PANELS_DIR, tfilename), template)
