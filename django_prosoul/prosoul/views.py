import json

from django import shortcuts
from django.http import HttpResponse
from django.template import loader

from prosoul.prosoul_export import fetch_models, gl2viewer
from prosoul.prosoul_assess import assess
from prosoul.prosoul_vis import build_dashboards
from prosoul.views_editor import editor
from prosoul.forms import AssessmentForm, VisualizationForm


class Viewer():
    @staticmethod
    def viewer(request):
        """ Basic Models Viewer just dumping the JSON of all models """
        models = fetch_models()
        if not models['qualityModels']:
            return editor(request)
        model_selected = models['qualityModels'][0]['name']
        if request.method == 'GET' and 'qmodel_selected' in request.GET:
            model_selected = request.GET['qmodel_selected']
        viewer_data = gl2viewer(models, model_name=model_selected)
        context = {'active_page': "viewer",
                   'qmodel_selected': model_selected,
                   'qmodels': models['qualityModels'],
                   'qm_data': viewer_data[0],
                   'qm_data_str': json.dumps(viewer_data[0]).replace('\"', '\\"'),
                   'attributes_data': viewer_data[1],
                   'attributes_data_str': json.dumps(viewer_data[1]).replace('\"', '\\"'),
                   'metrics_data': viewer_data[2],
                   'metrics_data_str': json.dumps(viewer_data[2]).replace('\"', '\\"')}

        template = loader.get_template('prosoul/viewer.html')

        render_index = template.render(context, request)

        return HttpResponse(render_index)


class Visualize():
    @staticmethod
    def visualize(request):
        template = loader.get_template('prosoul/visualize.html')
        context = {'active_page': "visualize", "vis_config_form": VisualizationForm()}
        render_index = template.render(context, request)
        return HttpResponse(render_index)

    @staticmethod
    def create(request):
        error = None
        if request.method == 'POST':
            form = VisualizationForm(request.POST)
            context = {'active_page': "visualize", "vis_config_form": form}
            if form.is_valid():
                qmodel_name = form.cleaned_data['quality_model']
                es_url = form.cleaned_data['es_url']
                kibana_url = form.cleaned_data['kibana_url']
                es_index = form.cleaned_data['es_index']
                attribute_template = form.cleaned_data['attribute_template']
                backend_metrics_data = form.cleaned_data['backend_metrics_data']

                # Time to execute the visualization creation
                try:
                    build_dashboards(es_url, es_index, attribute_template, qmodel_name,
                                     backend_metrics_data)
                except Exception as ex:
                    error = "Problem creating the visualization " + str(ex)

                context.update({"errors": error})
                if not error:
                    context.update({"kibana_url": kibana_url})
                return shortcuts.render(request, 'prosoul/visualize.html', context)
            else:
                context.update({"errors": form.errors})
                return shortcuts.render(request, 'prosoul/visualize.html', context)
        else:
            return shortcuts.render(request, 'prosoul/visualize.html', {"error": "Use GET method to send data"})


class Assessment():

    @staticmethod
    def assess(request):
        template = loader.get_template('prosoul/assessment.html')
        context = {'active_page': "assess", "assess_config_form": AssessmentForm()}
        render_index = template.render(context, request)
        return HttpResponse(render_index)

    def render_tables(assessment):
        """ Convert the JSON with the assessmet in an HTML table

        Sample format:

        {'Vitality': {'numberOfCommits': {'perceval': 2, 'GrimoireELK': 3},
                      'numberOfBugs':    {'perceval': 3, 'GrimoireELK': 3}},
         'Attention': {}}
        """

        projects_data = {}
        metrics = []

        for attribute in assessment:
            for metric in assessment[attribute]:
                metrics.append(metric)
                for project in assessment[attribute][metric]:
                    if project not in projects_data:
                        projects_data[project] = {}
                    if attribute not in projects_data[project]:
                        projects_data[project][attribute] = {}
                    projects_data[project][attribute][metric] = assessment[attribute][metric][project]

        metrics = list(set(metrics))
        # TODO: move this table rendering to Django templates
        tables = ""
        for project in projects_data:
            tables += "<h4>" + project + "</h4>"
            tables += "<table class='table'>"
            # Headers
            tables += "<thead><th scope='col'>Attribute</th>"
            for metric in metrics:
                tables += "<th>%s</th>" % metric
            tables += "</thead>"
            for attribute in projects_data[project]:
                # One row per atribute with its metrics
                tables += "<tr><th scope='row'>%s</td>" % attribute
                # Let's find the metrics to fill the metrics columns
                for metric_col in metrics:
                    metric_col_found = False
                    for metric in projects_data[project][attribute]:
                        if metric == metric_col:
                            tables += "<td>%s</td>" % projects_data[project][attribute][metric]
                            metric_col_found = True
                            break
                    if not metric_col_found:
                        tables += "<td></td>"
                tables += "</tr>"
            tables += "</table>"

        return tables

    @staticmethod
    def create(request):
        error = None
        if request.method == 'POST':
            form = AssessmentForm(request.POST)
            context = {'active_page': "assess", "assess_config_form": form}
            if form.is_valid():
                qmodel_name = form.cleaned_data['quality_model']
                es_url = form.cleaned_data['es_url']
                es_index = form.cleaned_data['es_index']
                backend_metrics_data = form.cleaned_data['backend_metrics_data']

                # Time to execute the assessment creation
                try:
                    assessment = assess(es_url, es_index, qmodel_name, backend_metrics_data)
                except Exception as ex:
                    error = "Problem creating the assessment " + str(ex)

                context.update({"errors": error})
                if not error:
                    assessment_table = Assessment.render_tables(assessment)
                    if assessment_table:
                        context.update({"assessment": Assessment.render_tables(assessment)})
                    else:
                        context.update({"errors": "Empty assessment. Review the form data."})
                return shortcuts.render(request, 'prosoul/assessment.html', context)
            else:
                context.update({"errors": form.errors})
                return shortcuts.render(request, 'prosoul/assessment.html', context)
        else:
            return shortcuts.render(request, 'prosoul/assessment.html', {"error": "Use POST method to send data"})
