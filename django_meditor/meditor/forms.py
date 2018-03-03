from django import forms
from django.core.validators import URLValidator

from . import data_editor
from meditor.meditor_utils import BACKEND_METRICS_DATA

CROSSMINER_URL = 'https://crossminer.biterg.io'
CROSSMINER_METRICS_INDEX = 'ossmeter'


class VisualizationForm(forms.Form):
    """ A form to collect the params needed to build a quality model visualization """

    # Temporal default values to make easier the config process
    KIBANA_URL = CROSSMINER_URL
    ELASTIC_URL = CROSSMINER_URL + '/data'
    INDEX_DATA = CROSSMINER_METRICS_INDEX
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
        # self.fields['quality_model'].widget = forms.Select()
        self.fields['es_url'] = forms.CharField(label='Elasticsearch URL', max_length=100, widget=widget)
        self.fields['es_url'].validators = [URLValidator()]
        self.fields['kibana_url'] = forms.CharField(label='Kibana URL', max_length=100, widget=widget)
        self.fields['kibana_url'].validators = [URLValidator()]
        self.fields['es_index'] = forms.CharField(label='Index with metrics data', max_length=100, widget=widget)
        self.fields['attribute_template'] = forms.CharField(label='Attribute template', max_length=100, widget=widget)


class AssessmentForm(forms.Form):
    """ A form to collect the params needed to build an assessment of projects """

    # Temporal default values to make easier the config process
    ELASTIC_URL = CROSSMINER_URL + '/data'
    INDEX_DATA = CROSSMINER_METRICS_INDEX

    def __init__(self, *args, **kwargs):
        kwargs['initial'] = {"es_url": self.ELASTIC_URL,
                             "es_index": self.INDEX_DATA}

        super(AssessmentForm, self).__init__(*args, **kwargs)

        es_attrs = {'class': 'form-control'}
        widget = forms.TextInput(attrs=es_attrs)
        widget_select = forms.Select(attrs=es_attrs)

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
        self.fields['es_url'].validators = [URLValidator()]
        self.fields['es_index'] = forms.CharField(label='Index with metrics data', max_length=100, widget=widget)
