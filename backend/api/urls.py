from django.urls import include, path
from rest_framework.routers import DefaultRouter

app_name = 'api'

# router_v1 = DefaultRouter()
# router_v1.register('recipes', views.RecipeViewSet, basename='recipes')
# router_v1.register('ingredients', views.IngredientsViewSet, basename='ingredients')
# router_v1.register('tags', views.TagViewSet, basename='tags')

urlpatterns = [
    # path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken'))
    # path('users/set_password', UserPass.as_view({'post':'set_password'})),
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