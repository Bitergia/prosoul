import json

from django.http import HttpResponse
from meditor.meditor_export import fetch_all_models

def index(request):
    """ Basic Models Viewer just dumping the JSON of all models """
    render_index = "<h1>Metrics Model Viewer</h1>"
    model = fetch_all_models()
    render_index += "<pre>"+json.dumps(model, indent=True, sort_keys=True)+"</pre>"
    return HttpResponse(render_index)
