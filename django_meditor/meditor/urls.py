from django.conf.urls import url
from django.views.generic import RedirectView


from . import views
from . import views_editor


urlpatterns_edit = [
    url(r'^editor$', views_editor.editor, name='editor'),
    url(r'^import$', views_editor.import_from_file),
    url(r'^export/qmodel=(?P<qmodel>[\w ]+)', views_editor.export_to_file),
    url(r'^export$', views_editor.export_to_file),
    url(r'^add_qmodel$', views_editor.QualityModelView.add_qmodel),
    url(r'^editor_select_qmodel$', views_editor.QualityModelView.select_qmodel),
    url(r'^add_goal$', views_editor.GoalView.add_goal),
    url(r'^remove_goal$', views_editor.GoalView.remove_goal),
    url(r'^select_goal$', views_editor.GoalView.select_goal),
    url(r'^update_goal$', views_editor.GoalView.update_goal),
    url(r'^add_attribute$', views_editor.AttributeView.add_attribute),
    url(r'^remove_attribute$', views_editor.AttributeView.remove_attribute),
    url(r'^select_attribute$', views_editor.AttributeView.select_attribute),
    url(r'^update_attribute$', views_editor.AttributeView.update_attribute),
    url(r'^add_metric$', views_editor.MetricView.add_metric),
    url(r'^remove_metric$', views_editor.MetricView.remove_metric),
    url(r'^select_metric$', views_editor.MetricView.select_metric),
    url(r'^update_metric$', views_editor.MetricView.update_metric),
    url(r'^add_metric_data$', views_editor.MetricDataView.add_metric_data)
]

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='viewer')),
    url(r'^viewer$', views.Viewer.viewer, name='viewer'),
    url(r'^visualize$', views.Visualize.visualize),
    url(r'^create_visualization$', views.Visualize.create),
    url(r'^assess$', views.Assess.assess)
]

urlpatterns += urlpatterns_edit
