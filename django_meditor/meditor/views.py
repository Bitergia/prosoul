import json

from django import shortcuts
from django.http import HttpResponse
from django.template import loader

from meditor.meditor_export import fetch_models, gl2viewer
from . import views_editor
from . import forms
from . import meditor_vis

class Viewer():
    @staticmethod
    def viewer(request):
        """ Basic Models Viewer just dumping the JSON of all models """
        models = fetch_models()
        if not models['qualityModels']:
            return views_editor.editor(request)
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

        template = loader.get_template('meditor/viewer.html')

        render_index = template.render(context, request)

        return HttpResponse(render_index)

class Visualize():
    @staticmethod
    def visualize(request):
        template = loader.get_template('meditor/visualize.html')
        context = {'active_page': "visualize", "vis_config_form": forms.VisualizationForm()}
        render_index = template.render(context, request)
        return HttpResponse(render_index)

    @staticmethod
    def create(request):
        error = None
        if request.method == 'POST':
            form = forms.VisualizationForm(request.POST)
            context = {'active_page': "visualize", "vis_config_form": form}
            if form.is_valid():
                qmodel_name = form.cleaned_data['quality_model']
                es_url = form.cleaned_data['es_url']
                kibana_url = form.cleaned_data['kibana_url']
                es_index = form.cleaned_data['es_index']
                attribute_template = form.cleaned_data['attribute_template']

                # Time to execute the visualization creation
                try:
                    meditor_vis.build_dashboards(es_url, es_index, attribute_template, qmodel_name)
                except Exception as ex:
                    error = "Problem creating the visualization " + str(ex)

                context.update({"errors": error})
                if not error:
                    context.update({"kibana_url": kibana_url})
                return shortcuts.render(request, 'meditor/visualize.html', context)
            else:
                context.update({"errors": form.errors})
                return shortcuts.render(request, 'meditor/visualize.html', context)
        else:
            return shortcuts.render(request, 'meditor/visualize.html', {"error": "Use GET method to send data"})


class Assess():

    @staticmethod
    def assess(request):
        template = loader.get_template('meditor/assess.html')
        context = {'active_page': "assess"}
        render_index = template.render(context, request)
        return HttpResponse(render_index)
