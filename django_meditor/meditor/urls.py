from django.conf.urls import url
from django.views.generic import RedirectView


from . import views
from . import views_editor

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='viewer')),
    url(r'^viewer$', views.viewer, name='viewer'),
    url(r'^editor$', views_editor.editor, name='editor')
]
