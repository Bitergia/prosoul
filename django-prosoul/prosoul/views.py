import csv
import json
import os

from django import shortcuts
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.template import loader
from django.views import View

from prosoul.prosoul_export import fetch_models, gl2viewer
from prosoul.prosoul_assess import assess
from prosoul.prosoul_vis import build_dashboards
from prosoul.forms import AssessmentForm, VisualizationForm, KIBANA_URL

ATTR_TEMPLATE = 'panels/templates/attribute-template.json'

ASSESSMENT_CSV_FILE_PATH = 'prosoul/static/prosoul/assessment_csv.csv'


class Viewer(View):

    http_method_names = ['get']

    def get(self, request):
        """ Basic Models Viewer just dumping the JSON of all models """
        models = fetch_models()
        if not models['qualityModels']:
            return shortcuts.redirect('prosoul:editor')
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


class Visualize(LoginRequiredMixin, View):

    http_method_names = ['get', 'post']

    def get(self, request):
        template = loader.get_template('prosoul/visualize.html')
        context = {'active_page': "visualize", "vis_config_form": VisualizationForm()}
        render_index = template.render(context, request)
        return HttpResponse(render_index)

    def post(self, request):
        error = None
        if request.method == 'POST':
            form = VisualizationForm(request.POST)
            context = {'active_page': "visualize", "vis_config_form": form}
            if form.is_valid():
                qmodel_name = form.cleaned_data['quality_model']
                es_url = form.cleaned_data['es_url']
                kibana_url = form.cleaned_data['kibana_url']
                es_index = form.cleaned_data['es_index']
                attribute_template = ATTR_TEMPLATE
                backend_metrics_data = form.cleaned_data['backend_metrics_data']
                from_date = form.cleaned_data['from_date']
                to_date = form.cleaned_data['to_date']

                # Time to execute the visualization creation
                try:
                    assess_template = None
                    build_dashboards(es_url, kibana_url, es_index, attribute_template, assess_template,
                                     qmodel_name, backend_metrics_data, from_date, to_date)
                except Exception as ex:
                    error = "Problem creating the visualizations " + str(ex)

                context.update({"errors": error})
                if not error:
                    context.update({"kibana_url": kibana_url})
                return shortcuts.render(request, 'prosoul/visualize.html', context)
            else:
                context.update({"errors": form.errors})
                return shortcuts.render(request, 'prosoul/visualize.html', context)
        else:
            return shortcuts.render(request, 'prosoul/visualize.html', {"error": "Use GET method to send data"})


class Assessment(LoginRequiredMixin, View):

    http_method_names = ['get', 'post']

    def get(self, request):
        template = loader.get_template('prosoul/assessment.html')
        context = {'active_page': "assess", "assess_config_form": AssessmentForm()}
        render_index = template.render(context, request)
        return HttpResponse(render_index)

    @staticmethod
    def render_attribute_table(metrics, goal, project, goal_p, csv_writter):
        table = "<table class='table'>"
        # Headers
        table += "<thead><th scope='col'>Attribute</th>"
        for metric in metrics:
            # Clean the metric name
            # "GitHubEnrich {\"filter\": {\"term\": {\"state\": \"closed\"}}}
            table += "<th>%s</th>" % metric

        table += "</thead>"
        for attribute in goal:
            # One row per atribute with its metrics
            table += "<tr><th scope='row'>%s</th>" % attribute
            # Let's find the metrics to fill the metrics columns
            for metric_col in metrics:
                metric_col_found = False
                for metric in goal[attribute]:
                    if metric == metric_col:
                        table += "<td>%s</td>" % goal[attribute][metric]
                        metric_col_found = True
                        csv_writter.writerow([goal_p, attribute, metric, project, goal[attribute][metric]])
                        break
                if not metric_col_found:
                    table += "<td>-</td>"
                    csv_writter.writerow([goal_p, attribute, metric, project, "-"])
            table += "</tr>"
        table += "</table>"

        return table

    def render_tables(assessment):
        """ Convert the JSON with the assessmet in an HTML table

        Sample format:

        {
         "Community": {
          "Attention": {
           "GitHubEnrich {\"filter\": {\"term\": {\"state\": \"closed\"}}}": {
            "perceval": 5,
            "GrimoireELK": 5
           }
          }
         },
         "Product": {
          "Vitality": {
           "GitHubEnrich": {
            "perceval": 2,
            "GrimoireELK": 2
           },
           "GitEnrich": {
            "perceval": 3,
            "GrimoireELK": 3
           }
          }
         }
        }
        """

        projects_data = {}
        metrics = []
        projects_list = []

        for goal in assessment:
            for attribute in assessment[goal]:
                for metric in assessment[goal][attribute]:
                    metrics.append(metric)
                    for project in assessment[goal][attribute][metric]:
                        if project not in projects_data:
                            projects_data[project] = {}
                        if goal not in projects_data[project]:
                            projects_data[project][goal] = {}
                        if attribute not in projects_data[project][goal]:
                            projects_data[project][goal][attribute] = {}
                        projects_data[project][goal][attribute][metric] = assessment[goal][attribute][metric][project]

        print(projects_data)

        metrics = list(set(metrics))
        # TODO: move this table rendering to Django templates
        tables = ""

        # Write to CSV
        with open(ASSESSMENT_CSV_FILE_PATH, 'w') as csvfile:  # Just use 'w' mode in 3.x
            csvwritter = csv.writer(csvfile)
            for project in projects_data:
                tables += "<h3>Project: " + project + "</h3>"
                projects_list.append(project)
                for goal in projects_data[project]:
                    tables += "<h5>Goal: " + goal + "</h5>"
                    tables += Assessment.render_attribute_table(metrics, projects_data[project][goal], project, goal,
                                                                csvwritter)

        return tables, projects_list

    def post(self, request):
        error = None
        form = AssessmentForm(request.POST)
        context = {'active_page': "assess", "assess_config_form": form, 'kibana_url': KIBANA_URL}
        if form.is_valid():
            qmodel_name = form.cleaned_data['quality_model']
            es_url = form.cleaned_data['es_url']
            es_index = form.cleaned_data['es_index']
            backend_metrics_data = form.cleaned_data['backend_metrics_data']
            from_date = form.cleaned_data['from_date']
            to_date = form.cleaned_data['to_date']

            # Time to execute the assessment creation
            try:
                assessment = assess(es_url, es_index, qmodel_name, backend_metrics_data, from_date, to_date)
            except Exception as ex:
                error = "Problem creating the assessment " + str(ex)

            context.update({"errors": error})
            if not error:
                (assessment_table, projects) = Assessment.render_tables(assessment)
                if assessment_table:
                    context.update({"assessment": assessment_table, "projects": projects,
                                    "assessment_raw": json.dumps(assessment)})
                else:
                    context.update({"errors": "Empty assessment. Review the form data."})
            return shortcuts.render(request, 'prosoul/assessment.html', context)
        else:
            context.update({"errors": form.errors})
            return shortcuts.render(request, 'prosoul/assessment.html', context)


def download_csv(request):
    file_path = ASSESSMENT_CSV_FILE_PATH
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404
