from django.conf.urls import include, url
from django.views.generic import RedirectView

from rest_framework import routers

from . import views
from prosoul.views_editor import AttributeView, EditorView, GoalView, MetricView, MetricDataView, QualityModelView
from prosoul.views_editor import import_from_file, export_to_file

from prosoul.rest import AttributeViewSet, DataSourceTypeViewSet, FactoidViewSet, GoalViewSet
from prosoul.rest import MetricViewSet, MetricDataViewSet, QualityModelViewSet

app_name = 'prosoul'

urlpatterns_edit = [
    url(r'^editor$', EditorView.as_view(), name='editor'),
    url(r'^import$', import_from_file),
    url(r'^export/qmodel=(?P<qmodel>[\w ]+)', export_to_file),
    url(r'^export$', export_to_file),
    url(r'^add_qmodel$', QualityModelView.as_view(action=QualityModelView.add_qmodel)),
    url(r'^remove_qmodel$', QualityModelView.as_view(action=QualityModelView.remove_qmodel)),
    url(r'^select_qmodel$', QualityModelView.as_view(action=QualityModelView.select_qmodel)),
    url(r'^update_qmodel$', QualityModelView.as_view(action=QualityModelView.update_qmodel)),
    url(r'^add_goal$', GoalView.as_view(action=GoalView.add_goal)),
    url(r'^remove_goal$', GoalView.as_view(action=GoalView.remove_goal)),
    url(r'^select_goal$', GoalView.as_view(action=GoalView.select_goal)),
    url(r'^update_goal$', GoalView.as_view(action=GoalView.update_goal)),
    url(r'^add_attribute$', AttributeView.as_view(action=AttributeView.add_attribute)),
    url(r'^remove_attribute$', AttributeView.as_view(action=AttributeView.remove_attribute)),
    url(r'^select_attribute$', AttributeView.as_view(action=AttributeView.select_attribute)),
    url(r'^update_attribute$', AttributeView.as_view(action=AttributeView.update_attribute)),
    url(r'^add_metric$', MetricView.as_view(action=MetricView.add_metric)),
    url(r'^remove_metric$', MetricView.as_view(action=MetricView.remove_metric)),
    url(r'^select_metric$', MetricView.as_view(action=MetricView.select_metric)),
    url(r'^update_metric$', MetricView.as_view(action=MetricView.update_metric)),
    url(r'^add_metric_data$', MetricDataView.as_view(action=MetricDataView.add_metric_data))
]

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='viewer')),
    url(r'^viewer$', views.Viewer.as_view(), name='viewer'),
    url(r'^visualize$', views.Visualize.as_view(), name='viz'),
    url(r'^create_visualization$', views.Visualize.as_view()),
    url(r'^assess$', views.Assessment.as_view(), name='assess'),
    url(r'^create_assessment$', views.Assessment.as_view())
]

urlpatterns += urlpatterns_edit

#############
# REST routes support

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'attributes', AttributeViewSet)
router.register(r'factoid', FactoidViewSet)
router.register(r'goal', GoalViewSet)
router.register(r'datasourcetype', DataSourceTypeViewSet)
router.register(r'metric', MetricViewSet)
router.register(r'metricdata', MetricDataViewSet)
router.register(r'qualitymodels', QualityModelViewSet)
#############

urlpatterns += [url(r'^api/', include(router.urls))]
