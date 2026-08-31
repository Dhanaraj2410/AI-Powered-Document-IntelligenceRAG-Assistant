from django.urls import path
from .views import (
    index_view, login_view, register_view, logout_view,
    dashboard_view, documents_list_view, collections_list_view, document_detail_view,
    chat_view, search_view, compare_view, conversations_list_view,
    bookmarks_view, analytics_view, evaluation_view, profile_view
)

urlpatterns = [
    path('', index_view, name='index'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('documents/', documents_list_view, name='documents'),
    path('collections/', collections_list_view, name='collections'),
    path('document/<int:doc_id>/', document_detail_view, name='document-detail'),
    path('chat/', chat_view, name='chat'),
    path('search/', search_view, name='search'),
    path('compare/', compare_view, name='compare'),
    path('conversations/', conversations_list_view, name='conversations'),
    path('bookmarks/', bookmarks_view, name='bookmarks'),
    path('analytics/', analytics_view, name='analytics'),
    path('evaluation/', evaluation_view, name='evaluation'),
    path('profile/', profile_view, name='profile'),
]
