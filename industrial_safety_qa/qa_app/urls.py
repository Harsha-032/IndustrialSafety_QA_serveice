from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('ask/', views.ask, name='ask'),
    path('api/ask/', views.ask_api, name='ask_api'),
    path('initialize/', views.initialize_system, name='initialize'),
    path('diagnostic/', views.diagnostic, name='diagnostic'),
    path('check-pdfs/', views.check_pdfs, name='check_pdfs'),
]