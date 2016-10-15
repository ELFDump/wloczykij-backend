from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
import rest_framework.authtoken.views
from . import views, views_login

router = DefaultRouter()
router.register(r'me', views.CurrentUserView, base_name='me')
router.register(r'users', views.UserViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include('rest_framework.urls')),
    url(r'^login/(?P<provider>(\w|-)+)/$', views_login.LoginRedirect.as_view(), name='allaccess-login'),
    url(r'^logincallback/(?P<provider>(\w|-)+)/$', views_login.LoginCallback.as_view(), name='allaccess-callback'),
    url(r'^token/?(?P<provider>(\w|-)*)/$', views_login.LoginToken.as_view(), name='gettoken-login')
]
