from django.conf.urls import url
from django.views.generic import RedirectView


from . import views

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='viewer')),
    url(r'^viewer$', views.viewer, name='viewer'),
    url(r'^editor$', views.editor, name='editor')
]
