import json

from django.http import HttpResponse
from django.template import loader

from meditor.meditor_export import fetch_models, gl2viewer
from . import views_editor

def viewer(request):
    """ Basic Models Viewer just dumping the JSON of all models """
    models = fetch_models()
    if not models['qualityModels']:
        return views_editor.editor(request)
    model_selected = models['qualityModels'][0]['name']
    if request.method == 'GET' and 'qmodel_selected' in request.GET:
        model_selected = request.GET['qmodel_selected']
    viewer_data = gl2viewer(models, model_name=model_selected)
    context = {'qmodel_selected': model_selected,
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
