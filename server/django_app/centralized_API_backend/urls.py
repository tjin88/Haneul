from django.urls import path
from .views import MangaCreateView, MangaUpdateView

urlpatterns = [
    path('api/manga/', MangaCreateView.as_view(), name='create_manga'),
    path('api/manga/<str:title>/', MangaUpdateView.as_view(), name='manga-update'),
]

