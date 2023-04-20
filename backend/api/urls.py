from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import home

app_name = 'api'

# router_v1 = DefaultRouter()
# router_v1.register('recipes', views.RecipeViewSet, basename='recipes')
# router_v1.register('ingredients', views.IngredientsViewSet, basename='ingredients')
# router_v1.register('tags', views.TagViewSet, basename='tags')
# router_v1.register('users', views.UserViewSet, basename='users')

urlpatterns = [
    # path('', include(router_v1.urls)),
    path('', home, name='home'),
    path('auth/', include('djoser.urls.authtoken'))
]
