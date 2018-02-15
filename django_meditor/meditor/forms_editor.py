import functools

from time import time

from django import forms


from meditor.models import Attribute, Goal, Metric

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


class MeditorEditorForm(forms.Form):

    widget = forms.Select(attrs={'size': SELECT_LINES, 'class': 'form-control'})

    # Hidden widgets to store the state of the MeditorEditorForm
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
        super(MeditorEditorForm, self).__init__(*args, **kwargs)

        # The state includes the names of objects except for metrics
        # in which ids are included because there is no name
        self.state_fields = [self['qmodel_state'],
                             self['goals_state'],
                             self['attributes_state'],
                             self['metrics_state']
                             ]


class QualityModelForm(MeditorEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(QualityModelForm, self).__init__(*args, **kwargs)

        eco_attrs = {'class': 'form-control', 'placeholder': 'QualityModel name'}
        self.fields['qmodel_name'] = forms.CharField(label='QualityModel name', max_length=100)
        self.fields['qmodel_name'].widget = forms.TextInput(attrs=eco_attrs)


class QualityModelsForm(MeditorEditorForm):

    widget = forms.Select(attrs={'class': 'form-control', 'onclick': 'this.form.submit()'})

    @perfdata
    def __init__(self, *args, **kwargs):
        super(QualityModelsForm, self).__init__(*args, **kwargs)

        choices = [('', '')]  # Initial empty choice

        for eco in data_editor.QualityModelsData(self.state).fetch():
            choices += ((eco.name, eco.name),)

        self.fields['name'] = forms.ChoiceField(label='QualityModels', required=True,
                                                widget=self.widget, choices=choices)


class GoalForm(MeditorEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(GoalForm, self).__init__(*args, **kwargs)

        self.fields['goal_name'] = forms.CharField(label='Goal name', max_length=100)
        self.fields['goal_name'].widget = forms.TextInput(attrs={'class': 'form-control'})

        current_goal = None
        if self.state and self.state.goals:
            current_goal = self.state.goals[0]
        self.fields['current_name'] = forms.CharField(required=False, max_length=50,
                                                      widget=forms.HiddenInput(),
                                                      initial=current_goal)


class GoalsForm(MeditorEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(GoalsForm, self).__init__(*args, **kwargs)

        choices = ()

        for goal in data_editor.GoalsData(self.state).fetch():
            if (goal.name, goal.name) not in choices:
                choices += ((goal.name, goal.name),)

        choices = sorted(choices, key=lambda x: x[1])
        self.fields['name'] = forms.ChoiceField(label='Goals',
                                                widget=self.widget, choices=choices)


class AttributeForm(MeditorEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(AttributeForm, self).__init__(*args, **kwargs)

        ds_attrs = {'class': 'form-control', 'placeholder': 'Attribute'}
        self.fields['attribute_name'] = forms.CharField(label='Attribute name', max_length=100)
        self.fields['attribute_name'].widget = forms.TextInput(attrs=ds_attrs)


class AttributesForm(MeditorEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(AttributesForm, self).__init__(*args, **kwargs)

        choices = ()

        for attribute in data_editor.AttributesData(self.state).fetch():
            if (attribute.name, attribute.name) not in choices:
                choices += ((attribute.name, attribute.name),)

        choices = sorted(choices, key=lambda x: x[1])
        self.fields['name'] = forms.ChoiceField(label='Attributes',
                                                widget=self.widget, choices=choices)


class MetricsForm(MeditorEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(MetricsForm, self).__init__(*args, **kwargs)

        choices = ()

        for metric in data_editor.MetricsData(self.state).fetch():
            choices += ((metric.id, metric),)
            if len(choices) > MAX_ITEMS:
                break

        self.fields['id'] = forms.ChoiceField(label='Metric',
                                              widget=self.widget, choices=choices)


class MetricForm(MeditorEditorForm):

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
            attribute_orm = Attribute.objects.get(name=self.state.attributes[0])
            kwargs['initial'].update({
                'attributes': attribute_orm.name,
                'old_attribute': attribute_orm.name
            })

        if self.metric_id:
            try:
                metric_orm = Metric.objects.get(id=self.metric_id)
                kwargs['initial'].update({
                    'metric_id': self.metric_id,
                    'metric_name': metric_orm.name
                })
            except Metric.DoesNotExist:
                print(self.__class__, "Received metric which does not exists", self.metric_id)
        super(MetricForm, self).__init__(*args, **kwargs)

        self.fields['metric_id'] = forms.CharField(label='metric_id', required=False, max_length=100)
        self.fields['metric_id'].widget = forms.HiddenInput()

        self.fields['metric_name'] = forms.CharField(label='name', max_length=100, required=False)
        self.fields['metric_name'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'metric name'})

        choices = ()

        for ds in data_editor.AttributesData(state=None).fetch():
            choices += ((ds.name, ds.name),)

        empty_choice = [('', '')]
        choices = empty_choice + sorted(choices, key=lambda x: x[1])

        self.widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['attributes'] = forms.ChoiceField(label='Attributes', required=True,
                                                      widget=self.widget, choices=choices)

        self.fields['old_attribute'] = forms.CharField(label='old_attribute', max_length=100, required=False)
        self.fields['old_attribute'].widget = forms.HiddenInput(attrs={'class': 'form-control', 'readonly': 'True'})
