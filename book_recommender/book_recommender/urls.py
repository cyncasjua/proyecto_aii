"""
URL configuration for book_recommender project.

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
from main import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.listado_libros, name='listado_libros'),
    path('cargar/', views.cargar_libros, name='cargar_libros'),
    path('search/', views.searcher, name='searcher'),
    path('libro/<int:libro_id>/', views.detalle_libro, name='detalle_libro'),
    path('recomendados/', views.recomendados_para_ti, name='recomendados_para_ti'),
    path('ver-mas-populares/', views.ver_mas_populares, name='ver_mas_populares'),
    path('buscar-por-categoria/', views.buscar_por_categoria, name='buscar_por_categoria'),
    path('libro/<int:libro_id>/favorito/', views.toggle_favorito, name='toggle_favorito'),
    path('favoritos/', views.favoritos_list, name='favoritos_list'),
     path('libro/<int:libro_id>/quiero-leer/', views.toggle_quiero_leer, name='toggle_quiero_leer'),
    path('libro/<int:libro_id>/leido/', views.toggle_leido, name='toggle_leido'),
    path('quiero-leer/', views.quiero_leer_list, name='quiero_leer_list'),
    path('leidos/', views.leido_list, name='leido_list'),
    path('accounts/', include('main.urls')),
]
