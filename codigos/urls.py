from django.urls import path
from . import views

# Define your URL patterns here/ lista de urls
urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),
    path('codigos/', views.codigo_form_view, name='codigo_form'),
    path('lista_codigos/', views.lista_codigos_view, name='lista_codigos'),
    path('eliminar_codigo/<int:codigo>/', views.eliminar_codigo_view, name='eliminar_codigo'),
    path('brigadas/', views.brigadas_view, name='brigadas'),
    
    # path('curso/', views.curso, name='curso'),
]
# codigos/urls.py