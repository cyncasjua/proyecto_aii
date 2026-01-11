from django.contrib import admin
from .models import Libro, FavoritoLibro, QuieroLeerLibro, LeidoLibro, OpinionLibro

admin.site.register(Libro)
admin.site.register(FavoritoLibro)
admin.site.register(QuieroLeerLibro)
admin.site.register(LeidoLibro)
admin.site.register(OpinionLibro)    

