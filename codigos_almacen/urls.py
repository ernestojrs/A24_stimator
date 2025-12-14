"""
URL configuration for codigos_almacen project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from codigos import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('codigos.urls')),  # Include the URLs from the codigos app
    #path('home/', include('codigos.urls')),
   # path('lista_codigos/', include('codigos.urls')),
    #path('codigo_form/', include('codigos.urls')),
   # path('eliminar_codigo/<int:codigo>/', include('codigos.urls')),
   # path('curso/', include('codigos.urls')),
]
