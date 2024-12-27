from django.urls import path
from .views import get_route
urlpatterns = [ path('', get_route, name='get-route'), ]