from django.urls import path, re_path

from .views import HomeNovelGetView, AllNovelGetView, AllNovelSearchView, AsuraScansCreateView, AsuraScansUpdateView, AsuraScansSearchView, login_view, register_view, UserProfileReadingListView, update_reading_list, delete_book_from_reading_list, update_to_max_chapter, LightNovelPubCreateView, LightNovelPubUpdateView, LightNovelPubSearchView, BookDetailsView, AllNovelBrowseView

urlpatterns = [
    path('api/home-novels/', HomeNovelGetView.as_view(), name='get_all_novels'),

    # TODO: Might need to change this to include light novel vs Manga, or source? Not sure
    path('api/book-details/<str:title>/', BookDetailsView.as_view(), name='book-details'),

    path('api/all-novels/', AllNovelGetView.as_view(), name='get_all_novels'),
    path('api/all-novels/search', AllNovelSearchView.as_view(), name='search_all_novels'),
    path('api/all-novels/browse', AllNovelBrowseView.as_view(), name='browse_all_novels'),



    path('api/asurascans/', AsuraScansCreateView.as_view(), name='create_manga'),
    path('api/asurascans/<str:title>/', AsuraScansUpdateView.as_view(), name='manga-update'),
    # path('api/manga/search', AsuraScansSearchView.as_view(), name='manga-search'),
    # path('api/lightnovel/', LightNovelPubCreateView.as_view(), name='create_lightnovel'),
    # path('api/lightnovel/<str:title>/', LightNovelPubUpdateView.as_view(), name='lightnovel-update'),
    # path('api/lightnovel/search', LightNovelPubSearchView.as_view(), name='lightnovel-search'),

    path('api/login/', login_view, name='login'),
    path('api/register/', register_view, name='register'),
    re_path(r'^api/profiles/(?P<email>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/tracking_list/$', UserProfileReadingListView.as_view(), name='user-profile-reading-list'),
    path('api/profiles/update_reading_list/', update_reading_list, name='update-reading-list'),
    path('api/delete-book-from-reading-list/', delete_book_from_reading_list, name='delete-book-from-reading-list'),
    path('api/update-to-max-chapter/', update_to_max_chapter, name='update-to-max-chapter'),
]

