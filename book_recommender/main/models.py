
from django.db import models

class OpinionLibro(models.Model):
    libro = models.ForeignKey('Libro', on_delete=models.CASCADE, related_name='opiniones')
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} sobre {self.libro.titulo}: {self.texto[:30]}..."

class QuieroLeerLibro(models.Model):
    libro = models.ForeignKey('Libro', on_delete=models.CASCADE)
    usuario = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    fecha = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('usuario', 'libro'), ('session_key', 'libro'))

    def __str__(self):
        if self.usuario:
            return f"{self.usuario.username} - {self.libro.titulo} (Quiero leer)"
        return f"Session {self.session_key} - {self.libro.titulo} (Quiero leer)"

class LeidoLibro(models.Model):
    libro = models.ForeignKey('Libro', on_delete=models.CASCADE)
    usuario = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    fecha = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('usuario', 'libro'), ('session_key', 'libro'))

    def __str__(self):
        if self.usuario:
            return f"{self.usuario.username} - {self.libro.titulo} (Leído)"
        return f"Session {self.session_key} - {self.libro.titulo} (Leído)"


class FavoritoLibro(models.Model):
    libro = models.ForeignKey('Libro', on_delete=models.CASCADE)
    usuario = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    fecha = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('usuario', 'libro'), ('session_key', 'libro'))

    def __str__(self):
        if self.usuario:
            return f"{self.usuario.username} - {self.libro.titulo} (Favorito)"
        return f"Session {self.session_key} - {self.libro.titulo} (Favorito)"

class Libro(models.Model):
    titulo = models.CharField(max_length=255)
    precio = models.CharField(max_length=20)
    disponibilidad = models.CharField(max_length=50)
    categoria = models.CharField(max_length=100)
    rating = models.CharField(max_length=20)
    imagen_url = models.URLField(max_length=300)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.titulo} - {self.categoria}"


class PuntuacionLibro(models.Model):
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    puntuacion = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    fecha = models.DateTimeField(auto_now=True)
    usuario = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        unique_together = (('usuario', 'libro'), ('session_key', 'libro'))

    def __str__(self):
        if self.usuario:
            return f"{self.usuario.username} - {self.libro.titulo}: {self.puntuacion} estrellas"
        return f"Session {self.session_key} - {self.libro.titulo}: {self.puntuacion} estrellas"
