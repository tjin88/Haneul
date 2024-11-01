from django.urls import path, re_path
from .views import HomeNovelUnloggedGetView, HomeNovelLoggedGetView, AllNovelGetGenres, AllNovelSearchView, login_view, register_view, UserProfileReadingListView, update_reading_list, delete_book_from_reading_list, update_to_max_chapter, BookDetailsView, AllNovelBrowseView, update_reading, update_user_profile, csrf_token_view

urlpatterns = [
    path('api/home-novels/unlogged', HomeNovelUnloggedGetView.as_view(), name='get_home_carousel_novels'),
    path('api/home-novels/logged', HomeNovelLoggedGetView.as_view(), name='get_all_home_novels'),
    path('api/genres/', AllNovelGetGenres.as_view(), name='get_all_genres'),
    path('api/book-details/<str:title>/', BookDetailsView.as_view(), name='book-details'),
    path('api/all-novels/search', AllNovelSearchView.as_view(), name='search_all_novels'),
    path('api/all-novels/browse', AllNovelBrowseView.as_view(), name='browse_all_novels'),
    path('api/update-reading', update_reading, name='update_reading'),
    path('api/login/', login_view, name='login'),
    path('api/register/', register_view, name='register'),
    path('api/update_user_profile/', update_user_profile, name='update_user_profile'),
    re_path(r'^api/profiles/(?P<email>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/tracking_list/$', UserProfileReadingListView.as_view(), name='user-profile-reading-list'),
    path('api/profiles/update_reading_list/', update_reading_list, name='update-reading-list'),
    path('api/delete-book-from-reading-list/', delete_book_from_reading_list, name='delete-book-from-reading-list'),
    path('api/update-to-max-chapter/', update_to_max_chapter, name='update-to-max-chapter'),
    path('api/csrf-token/', csrf_token_view, name='csrf-token'),
]
