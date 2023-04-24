from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('recipes', RecipeViewSet, basename='recipes')
# router_v1.register('ingredients', views.IngredientsViewSet, basename='ingredients')
# router_v1.register('tags', views.TagViewSet, basename='tags')
# router_v1.register('users', views.UserViewSet, basename='users')


urlpatterns = [
    path('', include(router_v1.urls)),
    path(r'auth/', include('djoser.urls.authtoken'))
]




# users/set_password/
# users/me/
# api/auth/token/login/
# api/auth/token/logout/
# api/recipes/download_shopping_cart/
# api/recipes/{id}/favorite/
# api/users/subscriptions/ - мои подписки
# api/users/{id}/subscribe/ - подписаться на пользователя
# api/ingredients/