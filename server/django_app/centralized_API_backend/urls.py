from django.urls import path
from .views import MangaCreateView, MangaUpdateView, login_view, register_view

urlpatterns = [
    path('api/manga/', MangaCreateView.as_view(), name='create_manga'),
    path('api/manga/<str:title>/', MangaUpdateView.as_view(), name='manga-update'),
    path('api/login/', login_view, name='login'),
    path('api/register/', register_view, name='register'),
]

