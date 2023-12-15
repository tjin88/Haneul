from django.urls import path, re_path

from .views import MangaCreateView, MangaUpdateView, MangaSearchView, login_view, register_view, UserProfileReadingListView, update_reading_list, delete_book_from_reading_list, update_to_max_chapter, LightNovelCreateView, LightNovelUpdateView, LightNovelSearchView

urlpatterns = [
    path('api/manga/', MangaCreateView.as_view(), name='create_manga'),
    path('api/manga/<str:title>/', MangaUpdateView.as_view(), name='manga-update'),
    path('api/mangas/search', MangaSearchView.as_view(), name='manga-search'),
    path('api/login/', login_view, name='login'),
    path('api/register/', register_view, name='register'),
    re_path(r'^api/profiles/(?P<email>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/tracking_list/$', UserProfileReadingListView.as_view(), name='user-profile-reading-list'),
    path('api/profiles/update_reading_list/', update_reading_list, name='update-reading-list'),
    path('api/delete-book-from-reading-list/', delete_book_from_reading_list, name='delete-book-from-reading-list'),
    path('api/update-to-max-chapter/', update_to_max_chapter, name='update-to-max-chapter'),
    path('api/lightnovel/', LightNovelCreateView.as_view(), name='create_lightnovel'),
    path('api/lightnovel/<str:title>/', LightNovelUpdateView.as_view(), name='lightnovel-update'),
    path('api/lightnovel/search', LightNovelSearchView.as_view(), name='lightnovel-search'),
]

