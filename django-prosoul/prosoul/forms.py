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
#   David Moreno <dmoreno@bitergia.com>
#
#

import os

from django import forms

from . import data
from . import data_editor
from prosoul.prosoul_utils import BACKEND_METRICS_DATA

from grimoirelab_toolkit.datetime import (str_to_datetime)

# Fetch URLs by env variables from docker or define it with "localhost" by default
ES_URL = str(os.getenv('ES_URL', 'https://admin:admin@localhost:9200'))
KIBANA_URL = str(os.getenv('KIBITER_URL', 'http://localhost:80'))
METRICS_INDEX = 'scava-metrics'


class VisualizationForm(forms.Form):
    """ A form to collect the params needed to build a quality model visualization """

    # Temporal default values to make easier the config process
    KIBANA_URL = KIBANA_URL
    ELASTIC_URL = ES_URL
    INDEX_DATA = METRICS_INDEX
    ATTRIBUTE_TEMPLATE = 'AttributeTemplate'

    def __init__(self, *args, **kwargs):
        kwargs['initial'] = {"es_url": self.ELASTIC_URL,
                             "kibana_url": self.KIBANA_URL,
                             "es_index": self.INDEX_DATA,
                             "attribute_template": self.ATTRIBUTE_TEMPLATE}

        super(VisualizationForm, self).__init__(*args, **kwargs)

        es_attrs = {'class': 'form-control'}
        widget = forms.TextInput(attrs=es_attrs)
        widget_select = forms.Select(attrs=es_attrs)
        widget_date_from = forms.SelectDateWidget(attrs=es_attrs, years=range(1970, 2101))
        widget_date_to = forms.SelectDateWidget(attrs=es_attrs, years=range(1970, 2101))

        qmodels = [('', '')]  # Initial empty choice
        for qmodel in data_editor.QualityModelsData().fetch():
            qmodels += ((qmodel.name, qmodel.name),)

        self.fields['quality_model'] = forms.ChoiceField(label='Quality Model', required=True,
                                                         widget=widget_select, choices=qmodels)

        templates = []
        for template_tuple in data.VizTemplatesData().fetch():
            templates += (template_tuple,)

        self.fields['attribute_template'] = forms.ChoiceField(label='Attribute Template', required=True,
                                                              widget=widget_select, choices=templates)

        backends = []
        for backend in BACKEND_METRICS_DATA:
            backends += ((backend, backend),)

        self.fields['backend_metrics_data'] = forms.ChoiceField(label='Backend for metrics data', required=True,
                                                                widget=widget_select, choices=backends)
        # self.fields['quality_model'].widget = forms.Select()
        self.fields['es_url'] = forms.CharField(label='Elasticsearch URL', max_length=100, widget=widget)
        self.fields['kibana_url'] = forms.CharField(label='Kibana URL', max_length=100, widget=widget)
        self.fields['es_index'] = forms.CharField(label='Index with metrics data', max_length=100, widget=widget)
        self.fields['from_date'] = forms.DateField(label='From date', widget=widget_date_from)
        self.fields['to_date'] = forms.DateField(label='To date', widget=widget_date_to, initial=str_to_datetime(
            "2100-01-01"))


class AssessmentForm(forms.Form):
    """ A form to collect the params needed to build an assessment of projects """

    # Temporal default values to make easier the config process
    ELASTIC_URL = ES_URL
    INDEX_DATA = METRICS_INDEX

    def __init__(self, *args, **kwargs):
        kwargs['initial'] = {"es_url": self.ELASTIC_URL,
                             "es_index": self.INDEX_DATA}

        super(AssessmentForm, self).__init__(*args, **kwargs)

        es_attrs = {'class': 'form-control'}
        widget = forms.TextInput(attrs=es_attrs)
        widget_select = forms.Select(attrs=es_attrs)
        widget_date_from = forms.SelectDateWidget(attrs=es_attrs, years=range(1970, 2101))
        widget_date_to = forms.SelectDateWidget(attrs=es_attrs, years=range(1970, 2101))

        qmodels = [('', '')]  # Initial empty choice

        for qmodel in data_editor.QualityModelsData().fetch():
            qmodels += ((qmodel.name, qmodel.name),)

        self.fields['quality_model'] = forms.ChoiceField(label='Quality Model', required=True,
                                                         widget=widget_select, choices=qmodels)

        backends = []
        for backend in BACKEND_METRICS_DATA:
            backends += ((backend, backend),)

        self.fields['backend_metrics_data'] = forms.ChoiceField(label='Backend for metrics data', required=True,
                                                                widget=widget_select, choices=backends)
        self.fields['es_url'] = forms.CharField(label='Elasticsearch URL', max_length=100, widget=widget)
        self.fields['es_index'] = forms.CharField(label='Index with metrics data', max_length=100, widget=widget)
        self.fields['from_date'] = forms.DateField(label='From date', widget=widget_date_from)
        self.fields['to_date'] = forms.DateField(label='To date', widget=widget_date_to, initial=str_to_datetime(
            "2100-01-01"))
