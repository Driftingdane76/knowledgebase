from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/db', views.get_db, name='get_db'),
    path('api/search', views.search_pages, name='search_pages'),
    path('api/categories', views.categories, name='categories'),
    path('api/categories/<str:cat_id>', views.delete_category, name='delete_category'),
    path('api/pages', views.save_page, name='save_page'),
    path('api/pages/<str:page_id>', views.delete_page, name='delete_page'),
]
