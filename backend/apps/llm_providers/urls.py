from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'providers', views.LLMProviderViewSet)
router.register(r'models', views.LLMModelViewSet)

app_name = 'llm_providers'

urlpatterns = [
    path('', include(router.urls)),
]
