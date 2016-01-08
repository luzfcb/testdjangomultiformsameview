from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$',
        views.PessoaList.as_view(),
        name='list'
        ),
    url(r'^create/$',
        views.PessoaCreate.as_view(),
        name='create'
        ),
    url(r'^detail/(?P<pk>\d+)/$',
        views.PessoaDetail.as_view(),
        name='detail'
        ),
    url(r'^update/(?P<pk>\d+)/$',
        views.PessoaUpdate.as_view(),
        name='update'
        ),

]
