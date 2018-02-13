from django.conf.urls import url
from django.views.generic import RedirectView


from . import views
from . import views_editor


urlpatterns_edit = [
    url(r'^editor$', views_editor.editor, name='editor'),
    url(r'^import/$', views_editor.import_from_file),
    url(r'^export/qmodel=(?P<qmodel>[\w ]+)', views_editor.export_to_file),
    url(r'^export/$', views_editor.export_to_file),
    url(r'^add_qmodel$', views_editor.add_qmodel),
    url(r'^editor_select_qmodel$', views_editor.editor_select_qmodel),
    url(r'^add_goal$', views_editor.add_goal),
    url(r'^remove_goal$', views_editor.remove_goal),
    url(r'^editor_select_goal$', views_editor.editor_select_goal),
    url(r'^add_attribute$', views_editor.add_attribute),
    url(r'^select_attribute$', views_editor.select_attribute),
    url(r'^add_metric$', views_editor.add_metric),
    url(r'^remove_metric$', views_editor.remove_metric),
    url(r'^select_metric$', views_editor.select_metric),
    url(r'^update_metric$', views_editor.update_metric)
]

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='viewer')),
    url(r'^viewer$', views.viewer, name='viewer'),
]

urlpatterns += urlpatterns_edit
