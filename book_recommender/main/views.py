from main.models import QuieroLeerLibro, LeidoLibro, FavoritoLibro, Libro, PuntuacionLibro, OpinionLibro
from django.http import JsonResponse
from django.urls import reverse
from django.db import models
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from main.populateDB import populateDB
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser
from .whoosh_index import INDEX_DIR
from main.recommendations import recomendar_libros
import random
from django.db.models import Count
from django.contrib.auth.decorators import login_required


@login_required(login_url='/accounts/login/')
def buscar_por_categoria(request):
    categorias = Libro.objects.values_list('categoria', flat=True).distinct().order_by('categoria')
    categoria = request.GET.get('categoria', '')
    libros = []
    if categoria:
        libros = Libro.objects.filter(categoria=categoria)
    return render(request, "buscar_por_categoria.html", {"categorias": categorias, "libros": libros, "categoria_seleccionada": categoria})

@login_required(login_url='/accounts/login/')
def ver_mas_populares(request):
    populares_full = list(Libro.objects.filter(rating__iexact='five'))
    paginator = Paginator(populares_full, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "ver_mas_populares.html", {"populares": page_obj.object_list, "page_obj": page_obj})

@login_required(login_url='/accounts/login/')
def recomendados_para_ti(request):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    usuario = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
    if usuario:
        puntuados = PuntuacionLibro.objects.filter(usuario=usuario, puntuacion__gte=4)
    else:
        puntuados = PuntuacionLibro.objects.filter(session_key=session_key, puntuacion__gte=4)

    similares = []
    for p in puntuados:
        recs = recomendar_libros(p.libro.id, top_n=5)
        if not recs:
            recs = recomendar_libros(p.libro.id, top_n=10)
        similares.extend(recs)
    vistos = set()
    libros = []
    for libro in similares:
        if libro.id not in vistos:
            libros.append(libro)
            vistos.add(libro.id)
    random.shuffle(libros)

    paginator = Paginator(libros, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if not page_obj.object_list and libros:
        page_obj = paginator.get_page(1)
    primer_id = page_obj.object_list[0].id if page_obj.object_list else 0

    return render(request, "recomendados_para_ti.html", {
        "libros": page_obj.object_list,
        "primer_id": primer_id,
        "page_obj": page_obj
    })

@login_required(login_url='/accounts/login/')
def listado_libros(request):
    libros_list = Libro.objects.all()
    paginator = Paginator(libros_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    usuario = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
    if usuario:
        puntuados = PuntuacionLibro.objects.filter(usuario=usuario, puntuacion__gte=4)
    else:
        puntuados = PuntuacionLibro.objects.filter(session_key=session_key, puntuacion__gte=4)

    similares = []
    for p in puntuados:
        recs = recomendar_libros(p.libro.id, top_n=5)
        if not recs:
            recs = recomendar_libros(p.libro.id, top_n=10)
        similares.extend(recs)
    vistos = set()
    recomendados = []
    for libro in similares:
        if libro.id not in vistos and libro not in [p.libro for p in puntuados]:
            recomendados.append(libro)
            vistos.add(libro.id)
    random.shuffle(recomendados)
    recomendados = recomendados[:5]
    primer_id = recomendados[0].id if recomendados else 0

    populares_full = list(Libro.objects.filter(rating__iexact='five'))
    random.shuffle(populares_full)
    populares_top5 = populares_full[:5]
    categorias = Libro.objects.values_list('categoria', flat=True).distinct().order_by('categoria')
    categoria = request.GET.get('categoria', '')
    if categoria:
        libros_list = Libro.objects.filter(categoria=categoria)
    else:
        libros_list = Libro.objects.all()
    paginator = Paginator(libros_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    quiero_leer_ids = set()
    leido_ids = set()
    if usuario:
        quiero_leer_ids = set(QuieroLeerLibro.objects.filter(usuario=usuario, libro__in=page_obj.object_list).values_list('libro_id', flat=True))
        leido_ids = set(LeidoLibro.objects.filter(usuario=usuario, libro__in=page_obj.object_list).values_list('libro_id', flat=True))
    else:
        quiero_leer_ids = set(QuieroLeerLibro.objects.filter(session_key=session_key, libro__in=page_obj.object_list).values_list('libro_id', flat=True))
        leido_ids = set(LeidoLibro.objects.filter(session_key=session_key, libro__in=page_obj.object_list).values_list('libro_id', flat=True))
    return render(request, "listado_libros.html", {
        "page_obj": page_obj,
        "libros": page_obj.object_list,
        "recomendados": recomendados,
        "primer_id": primer_id,
        "populares": populares_top5,
        "populares_total": len(populares_full),
        "categorias": categorias,
        "categoria_seleccionada": categoria,
        "quiero_leer_ids": quiero_leer_ids,
        "leido_ids": leido_ids
    })


@login_required(login_url='/accounts/login/')
def cargar_libros(request):
    success = populateDB()
    if success:
        message = "Base de datos cargada correctamente."
    else:
        message = "Error al cargar la base de datos."
    return render(request, "cargar_libros.html", {"message": message})

@login_required(login_url='/accounts/login/')
def searcher(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        ix = open_dir(INDEX_DIR)
        parser = MultifieldParser(["titulo", "categoria"], schema=ix.schema)
        q = parser.parse(query)

        with ix.searcher() as searcher:
            whoosh_results = searcher.search(q, limit=None)
            for r in whoosh_results:
                try:
                    libro = Libro.objects.get(id=r['id'])
                    results.append(libro)
                except Libro.DoesNotExist:
                    # Skip if the book does not exist in the database
                    continue

    return render(request, "searcher.html", {
        "query": query,
        "libros": results
    })

@login_required(login_url='/accounts/login/')
def detalle_libro(request, libro_id):
    libro = Libro.objects.get(id=libro_id)
    mensaje = None
    puntuacion_usuario = None
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key
    usuario = request.user if request.user.is_authenticated else None
    if usuario:
        puntuacion_obj = PuntuacionLibro.objects.filter(usuario=usuario, libro=libro).first()
    else:
        puntuacion_obj = PuntuacionLibro.objects.filter(session_key=session_key, libro=libro).first()
    if puntuacion_obj:
        puntuacion_usuario = puntuacion_obj.puntuacion

    opiniones = OpinionLibro.objects.filter(libro=libro).order_by('-fecha')
    if request.method == "POST":
        if 'puntuacion' in request.POST:
            puntuacion = int(request.POST.get("puntuacion"))
            if usuario:
                obj, created = PuntuacionLibro.objects.update_or_create(
                    usuario=usuario, libro=libro,
                    defaults={"puntuacion": puntuacion}
                )
            else:
                obj, created = PuntuacionLibro.objects.update_or_create(
                    session_key=session_key, libro=libro,
                    defaults={"puntuacion": puntuacion}
                )
            mensaje = "¡Puntuación guardada!"
            puntuacion_usuario = puntuacion
        elif 'opinion' in request.POST:
            texto = request.POST.get('opinion', '').strip()
            if texto and usuario:
                OpinionLibro.objects.create(libro=libro, usuario=usuario, texto=texto)
                mensaje = "¡Opinión guardada!"
            return redirect('detalle_libro', libro_id=libro.id)

    recomendaciones = recomendar_libros(libro.id, top_n=5)
    usuario = request.user if request.user.is_authenticated else None
    if usuario:
        puntuados = PuntuacionLibro.objects.filter(usuario=usuario, puntuacion__gte=4)
    else:
        puntuados = PuntuacionLibro.objects.filter(session_key=session_key, puntuacion__gte=4)
    puntuados_libros = set(p.libro for p in puntuados)
    recomendaciones_filtradas = [lib for lib in recomendaciones if lib not in puntuados_libros]
    if not recomendaciones_filtradas:
        recomendaciones_filtradas = recomendaciones
    return render(request, "detalle_libro.html", {
        "libro": libro,
        "recomendaciones": recomendaciones_filtradas,
        "mensaje": mensaje,
        "puntuacion_usuario": puntuacion_usuario,
        "opiniones": opiniones,
    })


@login_required(login_url='/accounts/login/')
def toggle_quiero_leer(request, libro_id):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key
    libro = Libro.objects.get(id=libro_id)
    usuario = request.user if request.user.is_authenticated else None
    if request.method == "POST":
        obj, created = QuieroLeerLibro.objects.get_or_create(
            libro=libro,
            usuario=usuario if usuario else None,
            session_key=None if usuario else session_key
        )
        if not created:
            obj.delete()
            return JsonResponse({'quiero_leer': False})
        return JsonResponse({'quiero_leer': True})
    else:
        existe = QuieroLeerLibro.objects.filter(
            libro=libro,
            usuario=usuario if usuario else None,
            session_key=None if usuario else session_key
        ).exists()
        return JsonResponse({'quiero_leer': existe})

@login_required(login_url='/accounts/login/')
def toggle_leido(request, libro_id):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key
    libro = Libro.objects.get(id=libro_id)
    usuario = request.user if request.user.is_authenticated else None
    if request.method == "POST":
        obj, created = LeidoLibro.objects.get_or_create(
            libro=libro,
            usuario=usuario if usuario else None,
            session_key=None if usuario else session_key
        )
        if not created:
            obj.delete()
            return JsonResponse({'leido': False})
        return JsonResponse({'leido': True})
    else:
        existe = LeidoLibro.objects.filter(
            libro=libro,
            usuario=usuario if usuario else None,
            session_key=None if usuario else session_key
        ).exists()
        return JsonResponse({'leido': existe})

@login_required(login_url='/accounts/login/')
def quiero_leer_list(request):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key
    usuario = request.user if request.user.is_authenticated else None
    if usuario:
        quiero_leer = QuieroLeerLibro.objects.filter(usuario=usuario)
    else:
        quiero_leer = QuieroLeerLibro.objects.filter(session_key=session_key)
    libros = [f.libro for f in quiero_leer]
    paginator = Paginator(libros, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "quiero_leer_list.html", {"libros": page_obj.object_list, "page_obj": page_obj})

@login_required(login_url='/accounts/login/')
def leido_list(request):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key
    usuario = request.user if request.user.is_authenticated else None
    if usuario:
        leidos = LeidoLibro.objects.filter(usuario=usuario)
    else:
        leidos = LeidoLibro.objects.filter(session_key=session_key)
    libros = [f.libro for f in leidos]
    paginator = Paginator(libros, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "leido_list.html", {"libros": page_obj.object_list, "page_obj": page_obj})


@login_required(login_url='/accounts/login/')
def toggle_favorito(request, libro_id):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key
    libro = Libro.objects.get(id=libro_id)
    usuario = request.user if request.user.is_authenticated else None
    if request.method == "POST":
        favorito, created = FavoritoLibro.objects.get_or_create(
            libro=libro,
            usuario=usuario if usuario else None,
            session_key=None if usuario else session_key
        )
        if not created:
            favorito.delete()
            return JsonResponse({'favorito': False})
        return JsonResponse({'favorito': True})
    else:
        existe = FavoritoLibro.objects.filter(
            libro=libro,
            usuario=usuario if usuario else None,
            session_key=None if usuario else session_key
        ).exists()
        return JsonResponse({'favorito': existe})

@login_required(login_url='/accounts/login/')
def favoritos_list(request):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key
    usuario = request.user if request.user.is_authenticated else None
    if usuario:
        favoritos = FavoritoLibro.objects.filter(usuario=usuario)
    else:
        favoritos = FavoritoLibro.objects.filter(session_key=session_key)
    libros = [f.libro for f in favoritos]
    paginator = Paginator(libros, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "favoritos_list.html", {"libros": page_obj.object_list, "page_obj": page_obj})

