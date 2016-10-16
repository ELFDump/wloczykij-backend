from django.conf.urls import url, include
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from wloczykij import settings
from . import views, views_login

router = DefaultRouter()
router.register(r'token', views_login.LoginToken, base_name='token')
router.register(r'me', views.CurrentUserView, base_name='me')
router.register(r'users', views.UserViewSet)
router.register(r'places', views.PlaceViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include('rest_framework.urls')),
    url(r'^login/(?P<provider>(\w|-)+)/$', views_login.LoginRedirect.as_view(), name='allaccess-login'),
    url(r'^logincallback/(?P<provider>(\w|-)+)/$', views_login.LoginCallback.as_view(), name='allaccess-callback'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
