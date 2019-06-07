import functools

from time import time

from django import forms

from prosoul.models import Attribute, Metric, QualityModel

from . import data_editor

SELECT_LINES = 20
MAX_ITEMS = 1000  # Implement pagination if there are more items


def perfdata(func):
    @functools.wraps(func)
    def decorator(self, *args, **kwargs):
        task_init = time()
        data = func(self, *args, **kwargs)
        print("%s: Total data collecting time ... %0.3f sec" %
              (self.__class__.__name__, time() - task_init))
        return data
    return decorator


class ProsoulEditorForm(forms.Form):

    select_widget = forms.Select(attrs={'size': SELECT_LINES, 'class': 'form-control'})
    attrs = {'size': SELECT_LINES, 'class': 'form-control', 'onclick': 'this.form.submit()'}
    select_widget_onclick = forms.Select(attrs=attrs)

    # Hidden widgets to store the state of the ProsoulEditorForm
    qmodel_state = forms.CharField(required=False, max_length=50, widget=forms.HiddenInput())
    goals_state = forms.CharField(required=False, max_length=50, widget=forms.HiddenInput())
    attributes_state = forms.CharField(required=False, max_length=50, widget=forms.HiddenInput())
    metrics_state = forms.CharField(required=False, max_length=50, widget=forms.HiddenInput())

    def is_empty_state(self):
        return self.state.is_empty() if self.state else True

    def __init__(self, *args, **kwargs):
        self.state = kwargs.pop('state') if 'state' in kwargs else None
        if self.state:
            if 'initial' in kwargs:
                kwargs['initial'].update(self.state.initial_state())
            else:
                kwargs['initial'] = self.state.initial_state()
        super(ProsoulEditorForm, self).__init__(*args, **kwargs)

        # The state includes the names of objects except for metrics
        # in which ids are included because there is no name
        self.state_fields = [self['qmodel_state'],
                             self['goals_state'],
                             self['attributes_state'],
                             self['metrics_state']
                             ]


class QualityModelForm(ProsoulEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(QualityModelForm, self).__init__(*args, **kwargs)

        qmodel_name = None
        if self.state and self.state.qmodel_id:
            qmodel_id = self.state.qmodel_id
            qmodel_name = QualityModel.objects.get(id=qmodel_id).name

        qm_attrs = {'class': 'form-control', 'placeholder': 'QualityModel name'}
        self.fields['qmodel_name'] = forms.CharField(label='QualityModel name',
                                                     max_length=100, initial=qmodel_name)
        self.fields['qmodel_name'].widget = forms.TextInput(attrs=qm_attrs)


class QualityModelsForm(ProsoulEditorForm):

    select_widget = forms.Select(attrs={'class': 'form-control', 'onclick': 'this.form.submit()'})

    @perfdata
    def __init__(self, *args, **kwargs):
        print(args, kwargs)

        super(QualityModelsForm, self).__init__(*args, **kwargs)

        choices = [('', '')]  # Initial empty choice

        for qmodel in data_editor.QualityModelsData(self.state).fetch():
            choices += ((qmodel.id, qmodel.name),)

        self.fields['id'] = forms.ChoiceField(label='QualityModels', required=True,
                                              widget=self.select_widget, choices=choices)


class GoalForm(ProsoulEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(GoalForm, self).__init__(*args, **kwargs)

        self.fields['goal_name'] = forms.CharField(label='Goal name', max_length=100)
        self.fields['goal_name'].widget = forms.TextInput(attrs={'class': 'form-control'})

        current_id = None
        if self.state and self.state.goals:
            current_id = self.state.goals[0]
        self.fields['current_id'] = forms.CharField(required=False, max_length=50,
                                                    widget=forms.HiddenInput(),
                                                    initial=current_id)


class GoalsForm(ProsoulEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(GoalsForm, self).__init__(*args, **kwargs)

        choices = ()

        for goal in data_editor.GoalsData(self.state).fetch():
            if (goal.id, goal.name) not in choices:
                choices += ((goal.id, goal.name),)

        choices = sorted(choices, key=lambda x: x[1])
        self.fields['id'] = forms.ChoiceField(label='Goals',
                                              widget=self.select_widget_onclick, choices=choices)


class AttributeForm(ProsoulEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(AttributeForm, self).__init__(*args, **kwargs)

        ds_attrs = {'class': 'form-control', 'placeholder': 'Attribute'}
        self.fields['attribute_name'] = forms.CharField(label='Attribute name', max_length=100)
        self.fields['attribute_name'].widget = forms.TextInput(attrs=ds_attrs)

        current_id = None
        if self.state and self.state.attributes:
            current_id = self.state.attributes[0]
        self.fields['current_id'] = forms.CharField(required=False, max_length=50,
                                                    widget=forms.HiddenInput(),
                                                    initial=current_id)
        choices = (('', ''),)

        widget = forms.Select(attrs={'class': 'form-control'})

        for attribute in data_editor.AttributesData(self.state).fetch():
            if (attribute.id, attribute.name) not in choices and \
               attribute.id != current_id:
                choices += ((attribute.id, attribute.name),)

        choices = sorted(choices, key=lambda x: x[1])

        self.fields['parent_id'] = forms.ChoiceField(label='Parent', required=False,
                                                     widget=widget, choices=choices)


class AttributesForm(ProsoulEditorForm):

    def list_choices(self):
        choices = ()

        for attribute in data_editor.AttributesData(self.state).fetch():
            if (attribute.id, attribute.name) not in choices:
                choices += ((attribute.id, attribute.name),)

        choices = sorted(choices, key=lambda x: x[1])

        return choices

    @perfdata
    def __init__(self, *args, **kwargs):
        super(AttributesForm, self).__init__(*args, **kwargs)

        self.fields['id'] = forms.ChoiceField(label='Attributes',
                                              widget=self.select_widget_onclick, choices=self.list_choices())


class MetricDataForm(ProsoulEditorForm):
    def __init__(self, *args, **kwargs):
        super(MetricDataForm, self).__init__(*args, **kwargs)

        ds_attrs = {'class': 'form-control', 'placeholder': 'Implementation'}
        self.fields['implementation'] = forms.CharField(label='Implementation', max_length=100)
        self.fields['implementation'].widget = forms.TextInput(attrs=ds_attrs)
        self.fields['params'] = forms.CharField(label='Params', required=False, max_length=100)
        params_sample = '{"filter": {"term": {"state": "closed"}}}'
        self.fields['params'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': params_sample})


class MetricsForm(ProsoulEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(MetricsForm, self).__init__(*args, **kwargs)

        choices = ()

        for metric in data_editor.MetricsData(self.state).fetch():
            choices += ((metric.id, metric),)
            if len(choices) > MAX_ITEMS:
                break

        self.fields['id'] = forms.ChoiceField(label='Metric',
                                              widget=self.select_widget_onclick, choices=choices)


class MetricForm(ProsoulEditorForm):
    # This implementation needs to be revisited and simplified

    @perfdata
    def __init__(self, *args, **kwargs):
        self.metric_id = None
        self.metric_orm = None

        # First state process in order to fill initial values
        kwargs['initial'] = {}
        self.state = kwargs.get('state') if 'state' in kwargs else None
        if self.state:
            kwargs['initial'] = self.state.initial_state()

        if self.state and self.state.metrics:
            self.metric_id = self.state.metrics[0]

        if self.state and self.state.attributes:
            attribute_orm = Attribute.objects.get(id=self.state.attributes[0])
            kwargs['initial'].update({
                'attributes': attribute_orm.id,
                'old_attribute_id': attribute_orm.id
            })

        if self.metric_id:
            try:
                metric_orm = Metric.objects.get(id=self.metric_id)
                kwargs['initial'].update({
                    'metric_id': self.metric_id,
                    'metric_name': metric_orm.name,
                    'metric_thresholds': metric_orm.thresholds,
                    'calculation_type': metric_orm.calculation_type
                })
                if metric_orm.data:
                    kwargs['initial'].update({'metrics_data': metric_orm.data.id})
            except Metric.DoesNotExist:
                print(self.__class__, "Received metric which does not exists", self.metric_id)
        super(MetricForm, self).__init__(*args, **kwargs)

        self.fields['metric_id'] = forms.CharField(label='metric_id', required=False, max_length=100)
        self.fields['metric_id'].widget = forms.HiddenInput()

        self.fields['metric_name'] = forms.CharField(label='name', max_length=100, required=True)
        self.fields['metric_name'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'metric name'})

        self.fields['metric_thresholds'] = forms.CharField(label='Thresholds', max_length=100, required=False)
        self.fields['metric_thresholds'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1,2,3,4,5'})

        choices = ()

        # Show only the attributes for this quality model
        for attr in data_editor.AttributesData(state=self.state).fetch():
            choices += ((attr.id, attr.name),)

        empty_choice = [('', '')]
        choices = empty_choice + sorted(choices, key=lambda x: x[1])

        self.widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['attributes'] = forms.ChoiceField(label='Attributes', required=True,
                                                      widget=self.widget, choices=choices)

        calculation_types = [('max', 'Max'),
                             ('min', 'Min'),
                             ('avg', 'Average'),
                             ('median', 'Median'),
                             ('sum', 'Sum'),
                             ('last', 'Last')]
        self.fields['calculation_type'] = forms.ChoiceField(label='Calculation Type', required=True,
                                                            widget=self.widget, choices=calculation_types)

        choices = ()

        for metric_data in data_editor.MetricsDataData(state=None).fetch():
            choices += ((metric_data.id, str(metric_data.implementation)),)

        empty_choice = [('', '')]
        choices = empty_choice + sorted(choices, key=lambda x: x[1])

        self.fields['metrics_data'] = forms.ChoiceField(label='Metrics Data', required=False,
                                                        widget=self.widget, choices=choices)

        self.fields['old_attribute_id'] = forms.CharField(label='old_attribute', max_length=100, required=False)
        self.fields['old_attribute_id'].widget = forms.HiddenInput(attrs={'class': 'form-control', 'readonly': 'True'})
