import functools

from time import time

from django import forms


from meditor.models import Goal, Metric

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


class BestiaryEditorForm(forms.Form):

    widget = forms.Select(attrs={'size': SELECT_LINES, 'class': 'form-control'})

    # Hidden widgets to store the state of the BestiaryEditorForm
    eco_name_state = forms.CharField(required=False, max_length=50, widget=forms.HiddenInput())
    projects_state = forms.CharField(required=False, max_length=50, widget=forms.HiddenInput())
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
        super(BestiaryEditorForm, self).__init__(*args, **kwargs)

        # The state includes the names of objects except for metrics
        # in which ids are included because there is no name
        self.state_fields = [self['eco_name_state'],
                             self['projects_state'],
                             self['attributes_state'],
                             self['metrics_state']
                             ]


class QualityModelForm(BestiaryEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(QualityModelForm, self).__init__(*args, **kwargs)

        eco_attrs = {'class': 'form-control', 'placeholder': 'QualityModel name'}
        self.fields['ecosystem_name'] = forms.CharField(label='QualityModel name', max_length=100)
        self.fields['ecosystem_name'].widget = forms.TextInput(attrs=eco_attrs)


class QualityModelsForm(BestiaryEditorForm):

    widget = forms.Select(attrs={'class': 'form-control', 'onclick': 'this.form.submit()'})

    @perfdata
    def __init__(self, *args, **kwargs):
        super(QualityModelsForm, self).__init__(*args, **kwargs)

        choices = [('', '')]  # Initial empty choice

        for eco in data_editor.QualityModelsData(self.state).fetch():
            choices += ((eco.name, eco.name),)

        self.fields['name'] = forms.ChoiceField(label='QualityModels', required=True,
                                                widget=self.widget, choices=choices)


class GoalForm(BestiaryEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(GoalForm, self).__init__(*args, **kwargs)

        self.fields['project_name'] = forms.CharField(label='Goal name', max_length=100)
        self.fields['project_name'].widget = forms.TextInput(attrs={'class': 'form-control'})


class GoalsForm(BestiaryEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(GoalsForm, self).__init__(*args, **kwargs)

        choices = ()

        for project in data_editor.GoalsData(self.state).fetch():
            if (project.name, project.name) not in choices:
                choices += ((project.name, project.name),)

        choices = sorted(choices, key=lambda x: x[1])
        self.fields['name'] = forms.ChoiceField(label='Goals',
                                                widget=self.widget, choices=choices)


class AttributeForm(BestiaryEditorForm):

    @perfdata
    def __init__(self, *args, **kwargs):
        super(AttributeForm, self).__init__(*args, **kwargs)

        ds_attrs = {'class': 'form-control', 'placeholder': 'Data source type'}
        self.fields['attribute_name'] = forms.CharField(label='Data source name', max_length=100)
        self.fields['attribute_name'].widget = forms.TextInput(attrs=ds_attrs)


class AttributesForm(BestiaryEditorForm):

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


class MetricsForm(BestiaryEditorForm):

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


class MetricForm(BestiaryEditorForm):

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

        if self.state and self.state.projects:
            project_orm = Goal.objects.get(name=self.state.projects[0])
            kwargs['initial'].update({
                'project': project_orm.name
            })

        if self.metric_id:
            try:
                metric_orm = Metric.objects.get(id=self.metric_id)
                kwargs['initial'].update({
                    'metric_id': self.metric_id,
                    'repository': metric_orm.repository.name,
                    'params': metric_orm.params
                })
            except Metric.DoesNotExist:
                print(self.__class__, "Received metric which does not exists", self.metric_id)
        super(MetricForm, self).__init__(*args, **kwargs)

        self.fields['metric_id'] = forms.CharField(label='metric_id', required=False, max_length=100)
        self.fields['metric_id'].widget = forms.HiddenInput()

        self.fields['repository'] = forms.CharField(label='repository', max_length=100, required=False)
        self.fields['repository'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL'})

        self.fields['params'] = forms.CharField(label='params', max_length=100, required=False)
        self.fields['params'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Params'})

        choices = ()

        for ds in data_editor.AttributesData(state=None).fetch():
            choices += ((ds.name, ds.name),)

        empty_choice = [('', '')]
        choices = empty_choice + sorted(choices, key=lambda x: x[1])

        self.widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['attribute'] = forms.ChoiceField(label='Data Source', required=True,
                                                       widget=self.widget, choices=choices)

        self.fields['project'] = forms.CharField(label='project', max_length=100, required=False)
        self.fields['project'].widget = forms.HiddenInput(attrs={'class': 'form-control', 'readonly': 'True'})
